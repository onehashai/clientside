import frappe
from frappe.email.doctype.email_queue.email_queue import SendMailContext
from frappe.email.smtp import SMTPServer

EMAIL_FROM = "digital@onehash.ai"
EMAIL_SERVER_HOST = "smtp.gmail.com"
EMAIL_SERVER_PORT = 465
EMAIL_SERVER_USER = "digital@onehash.ai"
# You will need to provision an App Password.
# @see https://support.google.com/accounts/answer/185833
EMAIL_SERVER_PASSWORD = "fmdaswylcmpsimna"
can_send_email_from_default_admin_email_address = True


def send(self, sender, recipient, msg):
    print("send() override")
    # this function checks if  the sender has permission to send email from the default admin email address
    # if not, it will send the email from the default email account from set on frappe
    # this is useful when you have a multi-tenant setup and you want to send emails from the default admin email address
    # but you don't want to give the user permission to send emails from the default admin email address
    # implementation
    smtp_server_instance = None
    if can_send_email_from_default_admin_email_address:
        admin_smtp_server = EMAIL_SERVER_HOST
        admin_smtp_port = EMAIL_SERVER_PORT
        admin_smtp_login = EMAIL_SERVER_USER
        admin_smtp_password = EMAIL_SERVER_PASSWORD
        admin_smtp_server_instance = SMTPServer(
            server=admin_smtp_server,
            port=admin_smtp_port,
            use_ssl=0,
            use_tls=1,
            login=admin_smtp_login,
            password=admin_smtp_password,
        )
        smtp_server_instance = admin_smtp_server_instance
    with SendMailContext(self, False, smtp_server_instance) as ctx:
        if not frappe.flags.in_test:
            ctx.smtp_session.sendmail(
                from_addr=self.sender, to_addrs=recipient, msg=msg
            )
            ctx.add_to_sent_list(recipient)


from frappe.core.doctype.communication.communication import Communication

can_send_emails = False
