import frappe
from clientside.clientside.utils import get_database_size_of_site, get_total_files_size, get_backup_size_of_site

def site_stripe_config():
    country = frappe.conf.country or "US"
    if country == "IN":
        return {
            "customer_portal": frappe.conf.customer_portal_in,
        }
    else:
        return {
            "customer_portal": frappe.conf.customer_portal,
        }

def get_number_of_emails_sent():
    return frappe.conf.onehash_mail_usage or 0

def get_all_users():
    users =  frappe.db.count('User')
    return users-2

def format_bytes(bytes, decimals=2):
    if bytes == 0:
        return "0 Bytes"
    k = 1024
    dm = decimals if decimals > 0 else 0
    sizes = ["Bytes", "KB", "MB", "GB", "TB"]
    i = 0
    while i < len(sizes) - 1 and bytes >= k:
        bytes /= k  
        i += 1 
    result = round(bytes, dm)
    return f"{result} {sizes[i]}" 

@frappe.whitelist()
def get_usage():
    return {
        "users": get_all_users(),
        "emails": get_number_of_emails_sent(),
        "database_size": format_bytes(get_database_size_of_site()[1][1]),
        "files_size": format_bytes(get_total_files_size()),
        "backup_size": format_bytes(get_backup_size_of_site()),
        "user_limit": frappe.conf.max_users,
        "email_limit": frappe.conf.max_email,
        "storage_limit": format_bytes(int(frappe.conf.max_storage) * 1024 * 1024 * 1024),
        "customer_id": frappe.conf.customer_id,
        "plan_name": frappe.conf.plan_name
    }

@frappe.whitelist()
def get_context(context):
    usage_info = get_usage()
    return {"usage_info": usage_info}

