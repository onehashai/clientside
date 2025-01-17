import frappe
import json
import requests
from frappe import _
from clientside.clientside.overrides.communication import can_send_from_onehash_email_account
from frappe.core.doctype.communication.communication import Communication
from frappe.email.doctype.email_queue.email_queue import send_now as clientside_send_now
from frappe.client import save as clientside_save
from frappe.desk.form.save import savedocs as clientside_savedocs
from clientside.clientside.page.subscription_info.subscription_info import get_active_users

def user_creation_allowed():
    site_config = frappe.get_site_config(site_path=frappe.local.site)
    req = requests.get(
        "http://"
        + frappe.conf.admin_url
        + "/api/method/bettersaas.bettersaas.doctype.saas_sites.saas_sites.user_contacted?site_name="
        + frappe.local.site
    ).json()
    active_users = get_active_users()
    if site_config["country"]=="IN":
        if active_users>=15 and site_config["license_limit"]==15:
            if req["message"]:
                return True 
            else:
                return False
    else:
        if active_users>=10 and site_config["license_limit"]==10:
            if req["message"]:
                return True 
            else:
                return False
    return True

@frappe.whitelist(methods=["POST", "PUT"])
def save(doc):
    doc_data = json.loads(doc)
    if doc_data.get("doctype") == "User":
        if user_creation_allowed():
            return clientside_save(doc)
        else:
            frappe.throw(_("The user limit for your current plan has been reached. Kindly get in touch with <b>support@onehash.ai</b> to upgrade."))
    return clientside_save(doc)

@frappe.whitelist()
def savedocs(doc, action):
    doc_data = json.loads(doc)
    if doc_data.get("doctype") == "User" and 'new-user' in doc_data.get("name", ""):
        if user_creation_allowed():
            return clientside_savedocs(doc, action)
        else:
            frappe.throw(_("The user limit for your current plan has been reached. Kindly get in touch with <b>support@onehash.ai</b> to upgrade."))
    return clientside_savedocs(doc, action)

@frappe.whitelist()
def send_now(name):
    email_account = Communication().get_outgoing_email_account()
    if email_account.as_dict().login_id == frappe.conf.get("mail_login"):
        if can_send_from_onehash_email_account():
            current_usage = int(frappe.conf.get("onehash_mail_usage") or 0)
            command = "bench --site {} set-config onehash_mail_usage {}".format(
                frappe.local.site, int(current_usage) + 1
            )
            frappe.utils.execute_in_shell(command)
            clientside_send_now(name)
        else:
            frappe.throw(
                _(
                    "Please set up your own Email account to send emails"
                ),
                exc=frappe.OutgoingEmailError,
            )
    else:
        clientside_send_now(name)

@frappe.whitelist()
def schedule_files_backup():
    frappe.msgprint("This page is not available in this version of OneHash CRM. Please visit OneHash Backups page")
    