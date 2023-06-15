import frappe
from frappe.website.utils import is_signup_disabled
from frappe import _
from clientside.clientside.utils import getNumberOfEmailSent
from frappe.core.doctype.communication.email import _make
from frappe.utils import escape_html, cint


def sendEmail(*args, **kwargs):
    print("hqkejdjwefiwen")
    frappe.msgprint("This is a custom message from the clientside app.")
    return False


# MAKE EMAIL
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
    attachments="[]",
    send_me_a_copy=False,
    cc=None,
    bcc=None,
    read_receipt=None,
    print_letterhead=True,
    email_template=None,
    communication_type=None,
    **kwargs,
):
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
    :param attachments: List of attachments as list of files or JSON string.
    :param send_me_a_copy: Send a copy to the sender (default **False**).
    :param email_template: Template which is used to compose mail .
    """
    print("sending ........")
    if frappe.conf.max_email_limit and int(frappe.conf.max_email_limit) < int(
        getNumberOfEmailSent()
    ):
        frappe.throw(
            "You have exceeded the maximum number of emails allowed on your site , please contact your system manager to support for further information"
        )
    if kwargs:
        from frappe.utils.commands import warn

        warn(
            f"Options {kwargs} used in frappe.core.doctype.communication.email.make "
            "are deprecated or unsupported",
            category=DeprecationWarning,
        )

    if (
        doctype
        and name
        and not frappe.has_permission(doctype=doctype, ptype="email", doc=name)
    ):
        raise frappe.PermissionError(
            f"You are not allowed to send emails related to: {doctype} {name}"
        )

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
    )
