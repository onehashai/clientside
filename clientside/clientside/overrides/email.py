import frappe

@frappe.whitelist(allow_guest=True, methods=("GET",))
def mark_email_as_seen(recipient_email: str, reference_name: str, reference_doctype: str, communication_name: str | None = None):  
	from werkzeug.wrappers import Response
	frappe.request.after_response.add(lambda: _mark_email_as_opened(recipient_email, reference_name, reference_doctype, communication_name))
	pixel = b"GIF89a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"

	response = Response()
	response.mimetype = "image/gif"
	response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	response.headers["Expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
	response.data = pixel
	return response

def _mark_email_as_opened(recipient_email, reference_name, reference_doctype, communication_name):
	try:
		update_communication(recipient_email, communication_name)
		if reference_doctype == "Email Campaign":
			update_email_campaign(recipient_email, reference_name)

	except Exception as e:
		frappe.log_error(f"Failed to mark email as seen: {str(e)}", "Email Tracking")
		
def update_communication(recipient_email, communication_name):
	from frappe.utils import now_datetime

	current_time = now_datetime()
	formatted_time = current_time.strftime("%d-%m-%Y %I:%M %p")
	doc = frappe.get_doc('Communication', communication_name)
	child_entry = next((child for child in doc.all_emails if child.email == recipient_email), None)
	
	if child_entry:
		frappe.db.set_value("Email Insights", child_entry.name, "opened", child_entry.opened + 1, update_modified=False)
		frappe.db.set_value("Email Insights", child_entry.name, "opened_at", child_entry.opened_at + '\n' + formatted_time, update_modified=False)
	else:
		new_row = {
            "doctype": "Email Insights",
            "parent": communication_name,
            "parentfield": "all_emails",
            "parenttype": "Communication",
            "email": recipient_email,
            "opened": 1,
            "opened_at": formatted_time
        }
		child_doc = frappe.get_doc(new_row)
		child_doc.insert(ignore_permissions=True)
	frappe.db.commit()

def update_email_campaign(recipient_email, reference_name):
	from frappe.utils import now_datetime

	current_time = now_datetime()
	formatted_time = current_time.strftime("%d-%m-%Y %I:%M %p")
	doc = frappe.get_doc('Email Campaign', reference_name)
	child_entry = next((child for child in doc.all_emails if child.email == recipient_email), None)
	
	if child_entry:
		frappe.db.set_value("Email Insights", child_entry.name, "opened", child_entry.opened + 1, update_modified=False)
		frappe.db.set_value("Email Insights", child_entry.name, "opened_at", child_entry.opened_at + '\n' + formatted_time, update_modified=False)
	else:
		new_row = {
            "doctype": "Email Insights",
            "parent": reference_name,
            "parentfield": "all_emails",
            "parenttype": "Email Campaign",
            "email": recipient_email,
            "opened": 1,
            "opened_at": formatted_time
        }
		child_doc = frappe.get_doc(new_row)
		child_doc.insert(ignore_permissions=True)
	frappe.db.commit()

@frappe.whitelist()
def make(
	doctype=None,
	name=None,
	content=None,
	subject=None,
	sent_or_received="Sent",
	sender=None,
	sender_full_name=None,
	recipients=None,
	communication_medium="Email",
	send_email=False,
	print_html=None,
	print_format=None,
	attachments=None,
	send_me_a_copy=False,
	cc=None,
	bcc=None,
	read_receipt=None,
	print_letterhead=True,
	email_template=None,
	communication_type=None,
	send_after=None,
	print_language=None,
	now=False,
	**kwargs,
) -> dict[str, str]:
    """Make a new communication. Checks for email permissions for specified Document.

	:param doctype: Reference DocType.
	:param name: Reference Document name.
	:param content: Communication body.
	:param subject: Communication subject.
	:param sent_or_received: Sent or Received (default **Sent**).
	:param sender: Communcation sender (default current user).
	:param recipients: Communication recipients as list.
	:param communication_medium: Medium of communication (default **Email**).
	:param send_email: Send via email (default **False**).
	:param print_html: HTML Print format to be sent as attachment.
	:param print_format: Print Format name of parent document to be sent as attachment.
	:param attachments: List of File names or dicts with keys "fname" and "fcontent"
	:param send_me_a_copy: Send a copy to the sender (default **False**).
	:param email_template: Template which is used to compose mail .
	:param send_after: Send after the given datetime.
	"""
    from frappe.utils import cint

    if kwargs:
        from frappe.utils.commands import warn

        warn(
			f"Options {kwargs} used in frappe.core.doctype.communication.email.make "
			"are deprecated or unsupported",
			category=DeprecationWarning,
		)

    if doctype and name and not frappe.has_permission(doctype=doctype, ptype="email", doc=name):
        raise frappe.PermissionError(f"You are not allowed to send emails related to: {doctype} {name}")

    return _make(
		doctype=doctype,
		name=name,
		content=content,
		subject=subject,
		sent_or_received=sent_or_received,
		sender=sender,
		sender_full_name=sender_full_name,
		recipients=recipients,
		communication_medium=communication_medium,
		send_email=send_email,
		print_html=print_html,
		print_format=print_format,
		attachments=attachments,
		send_me_a_copy=cint(send_me_a_copy),
		cc=cc,
		bcc=bcc,
		read_receipt=cint(read_receipt),
		print_letterhead=print_letterhead,
		email_template=email_template,
		communication_type=communication_type,
		add_signature=False,
		send_after=send_after,
		print_language=print_language,
		now=now,
	)

def _make(
	doctype=None,
	name=None,
	content=None,
	subject=None,
	sent_or_received="Sent",
	sender=None,
	sender_full_name=None,
	recipients=None,
	communication_medium="Email",
	send_email=False,
	print_html=None,
	print_format=None,
	attachments=None,
	send_me_a_copy=False,
	cc=None,
	bcc=None,
	read_receipt=None,
	print_letterhead=True,
	email_template=None,
	communication_type=None,
	add_signature=True,
	send_after=None,
	print_language=None,
	now=False,
) -> dict[str, str]:
    """Internal method to make a new communication that ignores Permission checks."""

    from frappe.email.email_body import get_message_id
    from frappe.utils import cint, get_formatted_email, get_string_between, list_to_str

    sender = sender or get_formatted_email(frappe.session.user)
    recipients = list_to_str(recipients) if isinstance(recipients, list) else recipients
    cc = list_to_str(cc) if isinstance(cc, list) else cc
    bcc = list_to_str(bcc) if isinstance(bcc, list) else bcc

    comm = frappe.get_doc(
        {
			"doctype": "Communication",
			"subject": subject,
			"content": content,
			"sender": sender,
			"sender_full_name": sender_full_name,
			"recipients": recipients,
			"cc": cc or None,
			"bcc": bcc or None,
			"communication_medium": communication_medium,
			"sent_or_received": sent_or_received,
			"reference_doctype": doctype,
			"reference_name": name,
			"email_template": email_template,
			"message_id": get_string_between("<", get_message_id(), ">"),
			"read_receipt": read_receipt,
			"has_attachment": 1 if attachments else 0,
			"communication_type": communication_type,
			"send_after": send_after,
		}
	)
    comm.flags.skip_add_signature = not add_signature
    comm.insert(ignore_permissions=True)

    if attachments:
        if isinstance(attachments, str):
            import json
            attachments = json.loads(attachments)
        add_attachments(comm.name, attachments)

    if cint(send_email):
        if not comm.get_outgoing_email_account():
            from frappe import _
            frappe.throw(
				_(
					"Unable to send mail because of a missing email account. Please setup default Email Account from Settings > Email Account"
				),
				exc=frappe.OutgoingEmailError,
			)

        comm.send_email(
			print_html=print_html,
			print_format=print_format,
			send_me_a_copy=send_me_a_copy,
			print_letterhead=print_letterhead,
			print_language=print_language,
			now=now,
		)

    emails_not_sent_to = comm.exclude_emails_list(include_sender=send_me_a_copy)

    return {"name": comm.name, "emails_not_sent_to": ", ".join(emails_not_sent_to)}


def add_attachments(name, attachments):
    """Add attachments to the given Communication

    :param name: Communication name
    :param attachments: File names or dicts with keys "fname" and "fcontent"
    """
    for a in attachments:
        if isinstance(a, str):
            attach = frappe.db.get_value(
                "File", {"name": a}, ["file_url", "is_private", "file_size"], as_dict=1
            )
            file_args = {
                "file_url": attach.file_url,
                "file_size": attach.file_size,
                "is_private": attach.is_private,
            }
        elif isinstance(a, dict) and "fcontent" in a and "fname" in a:
            file_args = {
                "file_name": a["fname"],
                "content": a["fcontent"],
                "is_private": 1,
            }
        else:
            continue

        file_args.update(
            {
                "attached_to_doctype": "Communication",
                "attached_to_name": name,
                "folder": "Home/Attachments",
            }
        )

        _file = frappe.new_doc("File")
        _file.update(file_args)
        _file.save(ignore_permissions=True)

