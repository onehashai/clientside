import frappe
import json

from frappe.client import save
from frappe.desk.form.save import savedocs

@frappe.whitelist(methods=["POST", "PUT"])
def save_method(doc):
    return save(doc)

@frappe.whitelist()
def save_docs(doc, action):
    return savedocs(doc, action)