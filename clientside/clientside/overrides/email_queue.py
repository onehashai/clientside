import quopri
import requests
import urllib.parse
from email.parser import Parser
from email.policy import SMTP

import frappe
from frappe import _, safe_encode
from frappe.email.smtp import SMTPServer
from frappe.utils import (
	cint,
	get_hook_method,
	get_url,
)
from frappe.database.database import savepoint
from frappe.email.email_body import add_attachment
from frappe.email.queue import get_unsubcribed_url
from frappe.utils.verified_command import get_signed_params
from frappe.email.doctype.email_queue.email_queue import EmailQueue
from frappe.model.document import Document

class SendMailContext:
	def __init__(
		self,
		queue_doc: Document,
		smtp_server_instance: SMTPServer = None,
	):
		self.queue_doc: EmailQueue = queue_doc
		self.smtp_server: SMTPServer = smtp_server_instance
		self.sent_to_atleast_one_recipient = any(
			rec.recipient for rec in self.queue_doc.recipients if rec.is_mail_sent()
		)
		self.email_account_doc = None

	def fetch_smtp_server(self):
		self.email_account_doc = self.queue_doc.get_email_account(raise_error=True)
		if not self.smtp_server:
			self.smtp_server = self.email_account_doc.get_smtp_server()

	def __enter__(self):
		self.queue_doc.update_status(status="Sending", commit=True)
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		if exc_type:
			update_fields = {"error": frappe.get_traceback()}
			if self.queue_doc.retry < get_email_retry_limit():
				update_fields.update(
					{
						"status": "Partially Sent" if self.sent_to_atleast_one_recipient else "Not Sent",
						"retry": self.queue_doc.retry + 1,
					}
				)
			else:
				update_fields.update({"status": "Error"})
				self.notify_failed_email()
		else:
			update_fields = {"status": "Sent"}

		self.queue_doc.update_status(**update_fields, commit=True)

	@savepoint(catch=Exception)
	def notify_failed_email(self):
		# Parse the email body to extract the subject
		subject = Parser(policy=SMTP).parsestr(self.queue_doc.message)["Subject"]

		# Construct the notification
		notification = frappe.new_doc("Notification Log")
		notification.for_user = self.queue_doc.owner
		notification.set("type", "Alert")
		notification.from_user = self.queue_doc.owner
		notification.document_type = self.queue_doc.doctype
		notification.document_name = self.queue_doc.name
		notification.subject = _("Failed to send email with subject:") + f" {subject}"
		notification.insert()

	def update_recipient_status_to_sent(self, recipient):
		self.sent_to_atleast_one_recipient = True
		recipient.update_db(status="Sent", commit=True)

	def get_message_object(self, message):
		return Parser(policy=SMTP).parsestr(message)

	def message_placeholder(self, placeholder_key):
		# sourcery skip: avoid-builtin-shadow
		map = {
			"tracker": "<!--email_open_check-->",
			"unsubscribe_url": "<!--unsubscribe_url-->",
			"cc": "<!--cc_message-->",
			"recipient": "<!--recipient-->",
		}
		return map.get(placeholder_key)

	def build_message(self, recipient_email) -> bytes:
		"""Build message specific to the recipient."""
		message = self.queue_doc.message

		if not message:
			return ""

		message = message.replace(self.message_placeholder("tracker"), self.get_tracker_str(recipient_email))
		message = message.replace(
			self.message_placeholder("unsubscribe_url"), self.get_unsubscribe_str(recipient_email)
		)
		message = message.replace(self.message_placeholder("cc"), self.get_receivers_str())
		message = message.replace(
			self.message_placeholder("recipient"), self.get_recipient_str(recipient_email)
		)
		message = self.include_attachments(message)
		return message

	def get_tracker_str(self, recipient_email) -> str:
		tracker_url=""
		params = {
			"recipient_email": recipient_email,
			"reference_name": self.queue_doc.reference_name,
			"reference_doctype": self.queue_doc.reference_doctype,
			"communication_name": self.queue_doc.communication,
		}
		if self.queue_doc.communication:
			tracker_url = f"{get_url()}/api/method/frappe.core.doctype.communication.email.mark_email_as_seen?{get_signed_params(params)}"

		elif self.queue_doc.reference_doctype == "Newsletter":
			tracker_url = f"{get_url()}/api/method/frappe.email.doctype.newsletter.newsletter.newsletter_email_read?{get_signed_params(params)}"

		if tracker_url:
			tracker_url_html = f'<img src="{tracker_url}"/>'
			return quopri.encodestring(tracker_url_html.encode()).decode()

		return ""

	def get_unsubscribe_str(self, recipient_email: str) -> str:
		unsubscribe_url = ""

		if self.queue_doc.add_unsubscribe_link and self.queue_doc.reference_doctype:
			unsubscribe_url = get_unsubcribed_url(
				reference_doctype=self.queue_doc.reference_doctype,
				reference_name=self.queue_doc.reference_name,
				email=recipient_email,
				unsubscribe_method=self.queue_doc.unsubscribe_method,
				unsubscribe_params=self.queue_doc.unsubscribe_param,
			)

		return quopri.encodestring(unsubscribe_url.encode()).decode()

	def get_receivers_str(self):
		message = ""
		if self.queue_doc.expose_recipients == "footer":
			to_str = ", ".join(self.queue_doc.to)
			cc_str = ", ".join(self.queue_doc.cc)
			message = f"This email was sent to {to_str}"
			message = f"{message} and copied to {cc_str}" if cc_str else message
		return message

	def get_recipient_str(self, recipient_email):
		return recipient_email if self.queue_doc.expose_recipients != "header" else ""

	def include_attachments(self, message):
		message_obj = self.get_message_object(message)
		attachments = self.queue_doc.attachments_list

		for attachment in attachments:
			if attachment.get("fcontent"):
				continue

			file_filters = {}
			if attachment.get("fid"):
				file_filters["name"] = attachment.get("fid")
			elif attachment.get("file_url"):
				file_filters["file_url"] = attachment.get("file_url")

			if file_filters:
				_file = frappe.get_doc("File", file_filters)
				if _file.file_url.startswith(("http://", "https://")):
					if "frappe_s3_attachment.controller.generate_file" in _file.file_url:
						site_base_url = frappe.utils.get_url()
						parsed_url = urllib.parse.urlparse(_file.file_url)
						query_params = urllib.parse.parse_qs(parsed_url.query)
						content_hash = query_params.get("key", [None])[0]
						file_name = query_params.get("file_name", [None])[0]
						signed_url_request = f"{site_base_url}/api/method/frappe_s3_attachment.controller.generate_signed_url?key={content_hash}&file_name={file_name}"
						response = requests.get(signed_url_request)
						
						if response.status_code == 200:
							signed_url = response.json().get("message")
							response = requests.get(signed_url, stream=True)
							if response.status_code == 200:
								fcontent = response.content
							else:
								frappe.throw(f"Failed to fetch file from signed URL (Status: {response.status_code})")
					else:
						response = requests.get(_file.file_url, stream=True)
					if response.status_code == 200:
						fcontent = response.content 
					else:
						frappe.throw(f"Failed to fetch file from {_file.file_url} (Status: {response.status_code})")
				else:
					fcontent = _file.get_content()

				attachment.update({"fname": _file.file_name, "fcontent": fcontent, "parent": message_obj})
				attachment.pop("fid", None)
				attachment.pop("file_url", None)
				add_attachment(**attachment)
				
			elif attachment.get("print_format_attachment") == 1:
				attachment.pop("print_format_attachment", None)
				print_format_file = frappe.attach_print(**attachment)
				self._store_file(print_format_file["fname"], print_format_file["fcontent"])
				print_format_file.update({"parent": message_obj})
				add_attachment(**print_format_file)

		return safe_encode(message_obj.as_string())

	def _store_file(self, file_name, content):
		if not frappe.get_system_settings("store_attached_pdf_document"):
			return

		file_data = frappe._dict(file_name=file_name, is_private=1)

		# Store on communication if available, else email queue doc
		if self.queue_doc.communication:
			file_data.attached_to_doctype = "Communication"
			file_data.attached_to_name = self.queue_doc.communication
		else:
			file_data.attached_to_doctype = self.queue_doc.doctype
			file_data.attached_to_name = self.queue_doc.name

		if frappe.db.exists("File", file_data):
			return

		file = frappe.new_doc("File", **file_data)
		file.content = content
		file.insert()

class EmailQueueOverride(EmailQueue):
    def send(self, smtp_server_instance: SMTPServer = None):
        """Send emails to recipients."""
        if not self.can_send_now():
            return

        with SendMailContext(self, smtp_server_instance) as ctx:
            ctx.fetch_smtp_server()
            message = None
            for recipient in self.recipients:
                if recipient.is_mail_sent():
                    continue

                message = ctx.build_message(recipient.recipient)
                if method := get_hook_method("override_email_send"):
                    method(self, self.sender, recipient.recipient, message)
                else:
                    if not frappe.flags.in_test or frappe.flags.testing_email:
                        ctx.smtp_server.session.sendmail(
                            from_addr=self.sender,
                            to_addrs=recipient.recipient,
                            msg=message.decode("utf-8").encode(),
                        )

                ctx.update_recipient_status_to_sent(recipient)

            if frappe.flags.in_test and not frappe.flags.testing_email:
                frappe.flags.sent_mail = message
                return

            if ctx.email_account_doc.append_emails_to_sent_folder:
                ctx.email_account_doc.append_email_to_sent_folder(message)
				
def get_email_retry_limit():
	return cint(frappe.db.get_system_setting("email_retry_limit")) or 3