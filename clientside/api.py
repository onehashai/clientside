import frappe
def boot_session(boot):
    boot.customer_portal = frappe.conf.customer_portal