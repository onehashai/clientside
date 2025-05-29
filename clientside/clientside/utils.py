import frappe
import json
import os
import subprocess
import requests
from frappe.utils import validate_email_address
from frappe.core.doctype.user.user import test_password_strength
from frappe.geo.country_info import get_country_timezone_info
from clientside.stripe import StripeSubscriptionManager

@frappe.whitelist(allow_guest=True)
def check_password_strength(*args, **kwargs):
    passphrase = kwargs["password"]
    first_name = kwargs["first_name"]
    last_name = kwargs["last_name"]
    email = kwargs["email"]
    user_data = (first_name, "", last_name, email, "")
    if "'" in passphrase or '"' in passphrase:
        return {
            "feedback": {
                "password_policy_validation_passed": False,
                "suggestions": ["Password should not contain ' or \""],
            }
        }
    return test_password_strength(passphrase, user_data=user_data)

def get_fy(country):
    from datetime import datetime
    from frappe.utils import getdate, today, now_datetime

    year = now_datetime().year
    current_date = datetime.now().date()
    if country in ["Antigua and Barbuda","Barbados","Belize","Botswana","Brunei Darussalam","Canada","Swaziland","India","Jamaica","Japan","Kuwait","Lesotho","Namibia","New Zealand","Qatar","Saint Lucia","Singapore","South Africa"]:
        fy_start_date = getdate(f"{year}-04-01")
        if current_date < fy_start_date:
            return {
                "fy_start_date": f"{year-1}-04-01",
                "fy_end_date": f"{year}-03-31"
            }
        else:
            return {
                "fy_start_date": f"{year}-04-01",
                "fy_end_date": f"{year+1}-03-31"
            }
    elif country in ["Australia","Bahamas","Bangladesh","Bhutan","Cameroon","Dominica","Egypt","Kenya","Malawi","Mauritius","Nauru","Pakistan","Tonga","Uganda","United of Republic of Tanzania"]:
        fy_start_date = getdate(f"{year}-07-01")
        if current_date < fy_start_date:
            return {
                "fy_start_date": f"{year-1}-07-01",
                "fy_end_date": f"{year}-06-30"
            }
        else:
            return {
                "fy_start_date": f"{year}-07-01",
                "fy_end_date": f"{year+1}-06-30"
            }
    elif country in ["Haiti","Lao People's Democratic Republic","Marshall Islands","Micronesia","Myanmar","Palau","Thailand","Trinidad and Tobago","United States"]:
        fy_start_date = getdate(f"{year}-10-01")
        if current_date < fy_start_date:
            return {
                "fy_start_date": f"{year-1}-10-01",
                "fy_end_date": f"{year}-09-30"
            }
        else:
            return {
                "fy_start_date": f"{year}-10-01",
                "fy_end_date": f"{year+1}-09-30"
            }
    elif country in ["Nepal"]:
        fy_start_date = getdate(f"{year}-07-16")
        if current_date < fy_start_date:
            return {
                "fy_start_date": f"{year-1}-07-16",
                "fy_end_date": f"{year}-07-15"
            }
        else:
            return {
                "fy_start_date": f"{year}-07-16",
                "fy_end_date": f"{year+1}-07-15"
            }
    elif country in ["Afghanistan"]:
        fy_start_date = getdate(f"{year}-12-21")
        if current_date < fy_start_date:
            return {
                "fy_start_date": f"{year-1}-12-21",
                "fy_end_date": f"{year}-12-20"
            }
        else:
            return {
                "fy_start_date": f"{year}-12-21",
                "fy_end_date": f"{year+1}-12-20"
            }
    elif country in ["Iran"]:
        fy_start_date = getdate(f"{year}-03-21")
        if current_date < fy_start_date:
            return {
                "fy_start_date": f"{year-1}-03-21",
                "fy_end_date": f"{year}-03-20"
            }
        else:
            return {
                "fy_start_date": f"{year}-03-21",
                "fy_end_date": f"{year+1}-03-20"
            }
    elif country in ["United Kingdom"]:
        fy_start_date = getdate(f"{year}-04-06")
        if current_date < fy_start_date:
            return {
                "fy_start_date": f"{year-1}-04-06",
                "fy_end_date": f"{year}-04-05"
            }
        else:
            return {
                "fy_start_date": f"{year}-04-06",
                "fy_end_date": f"{year+1}-04-05"
            }
    elif country in ["Ethiopia"]:
        fy_start_date = getdate(f"{year}-08-08")
        if current_date < fy_start_date:
            return {
                "fy_start_date": f"{year-1}-08-08",
                "fy_end_date": f"{year}-08-07"
            }
        else:
            return {
                "fy_start_date": f"{year}-08-08",
                "fy_end_date": f"{year+1}-08-07"
            }
    elif country in ["Samoa"]:
        fy_start_date = getdate(f"{year}-06-01")
        if current_date < fy_start_date:
            return {
                "fy_start_date": f"{year-1}-06-01",
                "fy_end_date": f"{year}-05-31"
            }
        else:
            return {
                "fy_start_date": f"{year}-06-01",
                "fy_end_date": f"{year+1}-05-31"
            }
    else: 
        return {
            "fy_start_date": f"{year}-01-01",
            "fy_end_date": f"{year}-12-31"
        }

@frappe.whitelist(allow_guest=True)
def create_user_on_target_site(*args, **kwargs):
    from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "country_currency.json"
    )
    file = open(file_path, "r")
    f = json.loads(file.read())
    email = kwargs["email"]
    password = kwargs["password"]
    firstname = kwargs["firstname"]
    lastname = kwargs["lastname"]
    company_name = kwargs["company_name"]
    country = kwargs["country"]
    if validate_email_address(email) == '':
        return "INVALID_EMAIL_FORMAT"
    if (
        check_password_strength(
            password=password, first_name=firstname, last_name=lastname, email=email
        )["feedback"]["password_policy_validation_passed"]
        == False
    ):
        return "PASSWORD_NOT_STRONG"
    if not firstname:
        return "FIRST_NAME_NOT_PROVIDED"
    if not lastname:
        return "LAST_NAME_NOT_PROVIDED"
    frappe.clear_cache()
    fy = get_fy(f[country]["common"])
    setup_complete(
        {
            "currency": f[country]["currency"],
            "full_name": firstname + " " + lastname,
            "first_name": firstname,
            "last_name": lastname,
            "email": email,
            "password": password,
            "company_name": company_name,
            "timezone": get_country_timezone_info()["country_info"][
                f[country]["common"]
            ]["timezones"][0],
            "country": f[country]["common"],
            "fy_start_date": fy["fy_start_date"],
            "fy_end_date": fy["fy_end_date"],
            "language": "english",
            "chart_of_accounts": "Standard",
        }
    )
    user = frappe.get_doc("User", email)
    user.add_roles("OneHash Manager")
    user.save(ignore_permissions=True)
    remove_erpnext_workspace()
    frappe.utils.execute_in_shell(
        "bench --site {} clear-cache".format(frappe.local.site)
    )
    frappe.utils.execute_in_shell(
        "bench --site {} clear-website-cache".format(frappe.local.site)
    )
    subscription_manager = StripeSubscriptionManager(country)
    customer = subscription_manager.create_customer(frappe.local.site, email, firstname, lastname)
    subscription_manager.create_subscription(customer.id, country, frappe.local.site)
    update_lead_status(email)
    return {"status": "OK"}

def remove_erpnext_workspace():
    workspaces_to_remove = frappe.get_all(
		"Workspace",
		filters={"name": ("in", ["ERPNext Integrations", "ERPNext Settings"])},
		fields=["name", "title", "icon", "indicator_color", "parent_page as parent", "public"],
	)
    for workspace in workspaces_to_remove:
        frappe.delete_doc("Workspace", workspace["name"], force=True)
        frappe.db.commit()
        
def update_lead_status(email):
    cmd="bench --site {} execute bettersaas.api.update_lead_status --args {}".format(
            frappe.conf.admin_url, email
        )
    frappe.utils.execute_in_shell(cmd)

@frappe.whitelist()
def get_number_of_users():
    return frappe.db.count("User")

@frappe.whitelist()
def get_backup_size_of_site():
    url = (
        "http://"
        + frappe.conf.admin_url
        + "/api/method/bettersaas.bettersaas.doctype.saas_sites.saas_sites.get_site_backup_size?site_name="
        + frappe.local.site
    )
    resp = requests.get(url)
    return resp.json()["message"]

@frappe.whitelist()
def get_database_size_of_site():
    return frappe.db.sql(
        "SELECT table_schema "
        + frappe.conf.db_name
        + ", SUM(data_length + index_length)  'Database Size in B' FROM information_schema.TABLES GROUP BY table_schema;"
    )

@frappe.whitelist()
def get_total_files_size():
    return frappe.qb.sum("File", "file_size")

def check_disk_size(path):
    return subprocess.check_output(["du", "-hs", path]).decode("utf-8").split("\t")[0]

def convert_to_bytes(size):
    if size == "0":
        return 0
    prefix = size[-1]
    if prefix == "G":
        return float(size[:-1]) * 1024 * 1024 * 1024
    if prefix == "M":
        return float(size[:-1]) * 1024 * 1024
    if prefix == "K":
        return float(size[:-1]) * 1024
    return float(size)

def create_user_in_user_details(doc, method):
    user_obj = {
        "site_name": frappe.local.site,
        "email": doc.name,
        "firstname": doc.first_name,
        "lastname": doc.last_name,
        "user_type": doc.user_type,
        "enabled": doc.enabled,
        "last_active": doc.last_active,
    }
    try:
        url = f"http://{frappe.conf.admin_url}/api/method/bettersaas.bettersaas.doctype.saas_sites.saas_sites.create_user_entry_in_saas_site"
        cookies = {"sid": get_login_sid()}
        requests.post(url, json=user_obj, cookies=cookies)
        return
    except Exception as e:
        print(f"Error creating entry in bettersaas: {str(e)}")

def update_user_in_user_details(doc, method):
    user_obj = {
        "site_name": frappe.local.site,
        "email": doc.name,
        "firstname": doc.first_name,
        "lastname": doc.last_name,
        "user_type": doc.user_type,
        "enabled": doc.enabled,
        "last_active": doc.last_active,
    }
    try:
        url = f"https://{frappe.conf.admin_url}/api/method/bettersaas.bettersaas.doctype.saas_sites.saas_sites.update_user_entry_in_saas_site"
        cookies = {"sid": get_login_sid()}
        requests.post(url, json=user_obj, cookies=cookies)
        return
    except Exception as e:
        print(f"Error updating entry in bettersaas: {str(e)}")

def delete_user_in_user_details(doc, method):
    user_obj = {
        "site_name": frappe.local.site,
        "email": doc.name,
    }
    try:
        url = f"http://{frappe.conf.admin_url}/api/method/bettersaas.bettersaas.doctype.saas_sites.saas_sites.delete_user_entry_in_saas_site"
        cookies = {"sid": get_login_sid()}
        requests.post(url, json=user_obj, cookies=cookies)
        return
    except Exception as e:
        print(f"Error deleting entry in bettersaas: {str(e)}")

def get_login_sid():
    admin_site_name = frappe.conf.admin_url
    admin_password = frappe.conf.administrator_password
    response = requests.post(
            f"https://{admin_site_name}/api/method/login",
            data={"usr": "Administrator", "pwd": admin_password},
        )
    sid = response.cookies.get("sid")
    if sid:
        return sid

    