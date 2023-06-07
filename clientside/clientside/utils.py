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


def post_install():
    print("Post Install")
    InsertFiscalYear()
    InsertCompany()
    return {
        "status": "OK",
    }
