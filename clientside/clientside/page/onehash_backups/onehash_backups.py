import frappe
from frappe.desk.page.backups.backups import get_context as get_local_backup_context


@frappe.whitelist()
def get_context(context):
	frappe.only_for("System Manager")
	return get_local_backup_context(context)
