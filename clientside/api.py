import frappe
def boot_session(boot):
    print(frappe.conf.customer_portal)
    boot.customer_portal = frappe.conf.customer_portal