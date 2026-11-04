import frappe
import json
import requests
from frappe import _
from clientside.clientside.overrides.communication import (
    can_send_from_onehash_email_account,
)
from frappe.core.doctype.communication.communication import Communication
from frappe.email.doctype.email_queue.email_queue import send_now as clientside_send_now
from frappe.client import save as clientside_save
from frappe.desk.form.save import savedocs as clientside_savedocs
from clientside.clientside.page.subscription_info.subscription_info import (
    get_active_users,
)
from clientside.clientside.access_control import reject_restricted_doctype_payload


def user_creation_allowed(user=None):
    site_config = frappe.get_site_config(site_path=frappe.local.site)
    active_users = get_active_users([user]) if user else get_active_users()
    next_user_count = active_users + 1
    free_allowance = int(site_config.get("min_license") or 0)
    purchased_quantity = int(site_config.get("subscription_quantity") or 0)
    if (
        next_user_count <= free_allowance
        or next_user_count <= purchased_quantity
    ):
        return True

    req = requests.get(
        "http://"
        + frappe.conf.admin_url
        + "/api/method/bettersaas.bettersaas.doctype.saas_sites.saas_sites.user_contacted?site_name="
        + frappe.local.site
    ).json()
    return bool(req["message"])


@frappe.whitelist(methods=["POST", "PUT"])
def save(doc):
    reject_restricted_doctype_payload(doc)
    doc_data = json.loads(doc)
    if doc_data.get("doctype") == "User" and doc_data.get("enabled"):
        if user_creation_allowed(doc_data.get("name")):
            return clientside_save(doc)
        else:
            frappe.throw(
                _(
                    "The user limit for your current plan has been reached. Kindly get in touch with <b>support@onehash.ai</b> to upgrade."
                )
            )
    return clientside_save(doc)


@frappe.whitelist()
def savedocs(doc, action):
    reject_restricted_doctype_payload(doc)
    doc_data = json.loads(doc)
    if doc_data.get("doctype") == "User" and doc_data.get("enabled"):
        if user_creation_allowed(doc_data.get("name")):
            return clientside_savedocs(doc, action)
        else:
            frappe.throw(
                _(
                    "The user limit for your current plan has been reached. Kindly get in touch with <b>support@onehash.ai</b> to upgrade."
                )
            )
    return clientside_savedocs(doc, action)


@frappe.whitelist()
def schedule_files_backup():
    frappe.msgprint(
        "This page is not available in this version of OneHash CRM. Please visit OneHash Backups page"
    )
