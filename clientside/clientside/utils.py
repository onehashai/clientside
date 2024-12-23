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

@frappe.whitelist(allow_guest=True)
def create_user_on_target_site(*args, **kwargs):
    from frappe.utils.data import now_datetime
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
    current_year = now_datetime().year
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
            "fy_start_date": f"{current_year}-04-01",
            "fy_end_date": f"{current_year+1}-03-31",
            "language": "english",
            "chart_of_accounts": "Standard",
        }
    )
    user = frappe.get_doc("User", email)
    user.add_roles("OneHash Manager")
    user.save(ignore_permissions=True)
    frappe.utils.execute_in_shell(
        "bench --site {} clear-cache".format(frappe.local.site)
    )
    frappe.utils.execute_in_shell(
        "bench --site {} clear-website-cache".format(frappe.local.site)
    )
    subscription_manager = StripeSubscriptionManager(country)
    customer = subscription_manager.create_customer(frappe.local.site, email, firstname, lastname)
    subscription_manager.create_subscription(customer.id, country, frappe.local.site)
    return {"status": "OK"}

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
    files = frappe.db.get_list('File', fields=['file_size'])
    total_size = sum(file['file_size'] for file in files if file['file_size'] is not None)
    return total_size

def check_disk_size(path):
    return subprocess.check_output(["du", "-hs", path]).decode("utf-8").split("\t")[0]

def convert_to_bytes(sizeInStringWithPrefix):
    if sizeInStringWithPrefix == "0":
        return 0
    prefix = sizeInStringWithPrefix[-1]
    if prefix == "G":
        return float(sizeInStringWithPrefix[:-1]) * 1024 * 1024 * 1024
    if prefix == "M":
        return float(sizeInStringWithPrefix[:-1]) * 1024 * 1024
    if prefix == "K":
        return float(sizeInStringWithPrefix[:-1]) * 1024
    return float(sizeInStringWithPrefix)