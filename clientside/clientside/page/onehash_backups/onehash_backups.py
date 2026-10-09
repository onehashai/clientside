import frappe


@frappe.whitelist()
def get_context(context):
	frappe.local.flags.redirect_location = "/app/backups"
	raise frappe.Redirect
