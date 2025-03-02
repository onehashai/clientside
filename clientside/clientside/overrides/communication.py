import frappe
from frappe import _
from frappe.core.doctype.communication.communication import Communication

def can_send_from_onehash_email_account():
    current_usage = frappe.conf.get("onehash_mail_usage") or "0"
    max_email = frappe.conf.get("max_email") or "10"
    if int(current_usage) >= int(max_email):
        return False
    else:
        return True
    
class CommunicationOverride(Communication):
    def get_outgoing_email_account(self):
        email_account = super().get_outgoing_email_account()
        if email_account.as_dict().login_id == frappe.conf.get("mail_login"):
            if can_send_from_onehash_email_account():
                current_usage = frappe.conf.get("onehash_mail_usage") or "0"
                command = f'bench --site {frappe.local.site} set-config onehash_mail_usage "{int(current_usage) + 1}"'
                frappe.utils.execute_in_shell(command)
                return email_account
            else:
                frappe.throw(
                    _(
                        "Please set up your own Email account to send emails"
                    ),
                    exc=frappe.OutgoingEmailError,
                )
        else:
            return email_account
