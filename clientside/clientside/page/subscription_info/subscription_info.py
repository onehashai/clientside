import frappe
from frappe.utils.password import decrypt
from clientside.clientside.page.onehash_backups.onehash_backups import schedule_files_backup
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

def get_active_users():
    try:
        active_users_list = frappe.get_all("User", fields=['name', 'email', 'user_type', 'enabled'])
        customer_email = frappe.conf.get('customer_email')
        if customer_email.endswith("@onehash.ai"):
            active_users = sum(
                    1 for user in active_users_list 
                    if user.get("enabled") 
                    and user["name"] not in ['Administrator', 'Guest']
                )
        else:
            active_users = sum(
                    1 for user in active_users_list 
                    if user.get("enabled") 
                    and not user["email"].endswith("@onehash.ai") 
                    and user["name"] not in ['Administrator', 'Guest']
                )
        return active_users
    except Exception as e:
        print(f"Error Counting Active Users: {e}")
        return 0

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

def get_subscription_info():
    return {
        "users": get_active_users(),
        "emails": get_number_of_emails_sent(),
        "database_size": format_bytes(get_database_size_of_site()[1][1]),
        "files_size": format_bytes(get_total_files_size()),
        "backup_size": format_bytes(get_backup_size_of_site()),
        "license_limit": int(frappe.conf.min_license),
        "email_limit": int(frappe.conf.max_email),
        "storage_limit": format_bytes(int(frappe.conf.max_storage) * 1024 * 1024 * 1024),
        "customer_id": frappe.conf.customer_id,
        "subscription_id": frappe.conf.subscription_id,
        "plan_name": frappe.conf.plan_name,
        "licenses": int(frappe.conf.subscription_quantity)
    }

@frappe.whitelist()
def licenses():
    return {
        "licenses": int(frappe.conf.subscription_quantity),
        "license_limit": int(frappe.conf.min_license)
    }

def get_context(context):
    frappe.only_for("OneHash Manager")

    subscription_info = get_subscription_info()
    return {"subscription_info": subscription_info}

@frappe.whitelist()
def delete_site():
    cmd="bench --site {} execute bettersaas.api.delete_site --args {}".format(
            frappe.conf.admin_url, frappe.local.site
        )
    frappe.utils.execute_in_shell(cmd)