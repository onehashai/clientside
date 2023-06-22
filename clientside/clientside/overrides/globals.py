import frappe
import json

from frappe.client import save
from frappe.desk.form.save import savedocs
from frappe.core.doctype.user.user import get_system_users


def isUserCreationAllowed(doc):
    print(doc)
    print(len(get_system_users()), int(frappe.conf.max_users))
    if (
        json.loads(doc)["doctype"] == "User"
        and json.loads(doc)["user_type"] == "System User"
        and len(get_system_users()) >= int(frappe.conf.max_users)
    ):
        frappe.throw("You have exhasuted your System user creation limit")


@frappe.whitelist(methods=["POST", "PUT"])
def saveOverride(doc):
    # isUserCreationAllowed(doc)
    return save(doc)


@frappe.whitelist()
def savedocsoverride(doc, action):
    # isUserCreationAllowed(doc)
    return savedocs(doc, action)
