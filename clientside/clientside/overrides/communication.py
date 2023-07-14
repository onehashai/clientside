from frappe.core.doctype.communication.communication import Communication
import frappe
from frappe import _


def checkIfUserCanSendEmailsFromOneHashEmailAccount():
    current_usage = int(frappe.conf.get("onehash_mail_usage") or 0)
    print("current_usage", current_usage)
    if current_usage >= int(frappe.conf.get("max_email")) or 0:
        return False
    else:
        return True


class CommunicationOverride(Communication):
    def get_outgoing_email_account(self):
        can_send_from_admin_email_account = (
            checkIfUserCanSendEmailsFromOneHashEmailAccount()
        )

        if can_send_from_admin_email_account:
            print("send from default account")
            email_account = super().get_outgoing_email_account()
            if email_account.as_dict().login_id == frappe.conf.get("mail_login"):
                current_usage = int(frappe.conf.get("onehash_mail_usage") or 0)
                command = "bench --site {} set-config onehash_mail_usage {}".format(
                    frappe.local.site, int(current_usage) + 1
                )
                frappe.utils.execute_in_shell(command)

            return email_account
        else:
            # check if user has Email account set
            comm = super().get_outgoing_email_account()
            if comm.as_dict().login_id == frappe.conf.get("mail_login"):
                frappe.throw(
                    _(
                        "Please set up your own Email account to send emails"
                    ),
                    exc=frappe.OutgoingEmailError,
                )
