import frappe
import json
from frappe import _
from frappe.client import save, delete
from frappe.desk.form.save import savedocs
from clientside.stripe import update_subscription_quantity
from clientside.clientside.page.usage_info.usage_info import get_usage

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

def user_creation_allowed():
    usage = get_usage()
    if usage["plan_name"] == "CRM Starter" or usage["plan_name"] == "ERP Starter":
        if usage["users"] >= 10 and usage["users"] < 15: 
            update_subscription_quantity(usage["users"])
            return True
        elif (usage["users"] >= 15):
            return False
        return True

@frappe.whitelist(methods=["POST", "PUT"])
def save_method(doc):
    doc_data = json.loads(doc)
    if doc_data.get("doctype") == "User":
        if user_creation_allowed():
            return save(doc)
        else:
            frappe.throw(_("The user limit for your current plan has been reached. Kindly get in touch with <b>support@onehash.ai</b> to upgrade."))

    else:
        return save(doc)

@frappe.whitelist()
def save_docs(doc, action):
    doc_data = json.loads(doc)
    if doc_data.get("doctype") == "User" and 'new-user' in doc_data.get("name", "") :
        if user_creation_allowed():
            return savedocs(doc, action)
        else:
            frappe.throw(_("The user limit for your current plan has been reached. Kindly get in touch with <b>support@onehash.ai</b> to upgrade."))
    else:
        return savedocs(doc, action)

# TODO
@frappe.whitelist(methods=["DELETE", "POST"])
def delete_method(doctype, name):
    logger.info(doctype)
    logger.info(name)
    return delete(doctype, name)

@frappe.whitelist()
def schedule_files_backup():
    frappe.msgprint("This page is not available in this version of OneHash CRM. Please visit OneHash Backups page")