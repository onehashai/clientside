import frappe
def get_context(context):
    context.update({
        "subdomain": frappe.local.site.split(".")[0],
        "customer_email": frappe.conf.customer_email,
    })