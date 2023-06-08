import json
import frappe
from setup_app.setup_app.doctype.saas_sites.saas_sites import (
    checkEmailFormatWithRegex,
    check_password_strength,
)


@frappe.whitelist()
def create_new_user(*args, **kwargs):
    email = kwargs["email"]
    password = kwargs["password"]
    firstname = kwargs["firstname"]
    lastname = kwargs["lastname"]
    print(email, password, firstname, lastname)
    if not checkEmailFormatWithRegex(email):
        return "INVALID_EMAIL_FORMAT"
    passwordResult = check_password_strength(
        password=password, first_name=firstname, last_name=lastname, email=email
    )
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

    try:
        user = frappe.db.get("User", {"email": email})
        if user:
            if user.enabled:
                return "EMAIL_ALREADY_REGISTERED"
            else:
                return "EMAIL_ALREADY_REGISTERED_BUT_DISABLED"
        user = frappe.get_doc(
            {
                "doctype": "User",
                "first_name": firstname,
                "last_name": lastname,
                "full_name": firstname + " " + lastname,
                "email": email,
                "send_welcome_email": 0,
                "new_password": password,
                "enabled": 1,
            }
        )
        user.flags.ignore_permissions = True
        user.flags.ignore_password_policy = True
        user.insert()
        adminUser = frappe.get_doc("User", "Administrator")
        roles_to_add = []
        for role in adminUser.roles:
            print(role.role)
            roles_to_add.append(role.role)
        user.add_roles(*roles_to_add)
    except Exception as e:
        print(e)
        return e
    return {
        "status": "OK",
        "roles_added": roles_to_add,
        "password_policy": passwordResult["feedback"][
            "password_policy_validation_passed"
        ],
    }


@frappe.whitelist()
def testSomethingRandom(*args, **kwargs):
    email = kwargs["email"]
    password = kwargs["password"]
    firstname = kwargs["firstname"]
    lastname = kwargs["lastname"]
    frappe.clear_cache()
    from frappe.utils.data import now_datetime
    from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

    print(frappe.db.a_row_exists("Company"))
    if True:
        print("heree")
        current_year = now_datetime().year
        setup_complete(
            {
                "currency": "USD",
                "full_name": firstname + " " + lastname,
                "first_name": firstname,
                "last_name": lastname,
                "email": email,
                "password": password,
                "company_name": "Wind Power LLC",
                "timezone": "America/New_York",
                "company_abbr": "WP",
                "industry": "Manufacturing",
                "country": "United States",
                "fy_start_date": f"{current_year}-01-01",
                "fy_end_date": f"{current_year}-12-31",
                "language": "english",
                "company_tagline": "Testing",
                "chart_of_accounts": "Standard",
            }
        )
    return {
        "status": "OK",
    }


def InsertFiscalYear():
    print("Inserting Fiscal Year")
    try:
        fiscalYear = frappe.get_doc(
            {
                "doctype": "Fiscal Year",
                "year": "2021",
                "year_start_date": "2021-01-01",
                "year_end_date": "2021-12-31",
            }
        )
        fiscalYear.flags.ignore_permissions = True
        fiscalYear.insert()
    except Exception as e:
        print(e)
        return e
    return {
        "status": "OK",
    }


def InsertCompany():
    print("Inserting Company")
    try:
        company = frappe.get_doc(
            {
                "doctype": "Company",
                "abbr": "All",
                "company_name": "All",
                "default_currency": "USD",
                "country": "United States",
            }
        )
        company.flags.ignore_permissions = True
        company.insert()
    except Exception as e:
        print(e)
        return e
    return {
        "status": "OK",
    }


def insertDefaultCountryCurrencyAndTimeZones():
    print("Inserting Country")
    try:
        country = frappe.get_doc(
            {
                "doctype": "Country",
                "country_name": "United States",
                "code": "US",
                "date_format": "mm-dd-yyyy",
                "time_format": "HH:mm:ss",
                "default_currency": "USD",
                "number_format": "#,###.##",
                "timezones": "America/Chicago",
            }
        )
        country.flags.ignore_permissions = True
        country.insert()
    except Exception as e:
        print(e)
        return e
    return {
        "status": "OK",
    }


def post_install():
    print("Post Install")
    InsertFiscalYear()
    InsertCompany()
    insertDefaultCountryCurrencyAndTimeZones()
    return {
        "status": "OK",
    }
