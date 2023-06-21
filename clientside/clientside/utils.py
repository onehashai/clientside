import json
import frappe
import requests
import os
from setup_app.setup_app.doctype.saas_sites.saas_sites import (
    checkEmailFormatWithRegex,
    check_password_strength,
)
from frappe.geo.country_info import get_country_timezone_info
from frappe.desk.doctype.workspace.workspace import update_page


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


def changeERPNames():
    update_page("ERPNext Settings", "OneHash Settings", "setting", "", 1)
    update_page("ERPNext Integrations", "OneHash Integrations", "setting", "", 1)


@frappe.whitelist()
def createUserOnTargetSite(*args, **kwargs):
    email = kwargs["email"]
    password = kwargs["password"]
    firstname = kwargs["firstname"]
    lastname = kwargs["lastname"]
    company_name = kwargs["company_name"]
    country = kwargs["country"]
    print("input", email, password, firstname, lastname, company_name, country)
    if not checkEmailFormatWithRegex(email):
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
    from frappe.utils.data import now_datetime
    from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

    print(frappe.db.a_row_exists("Company"))
    if True:
        current_year = now_datetime().year

        country_info = get_country_timezone_info()["country_info"][country]
        print(country_info)
        setup_complete(
            {
                "currency": country_info["currency"],
                "full_name": firstname + " " + lastname,
                "first_name": firstname,
                "last_name": lastname,
                "email": email,
                "password": password,
                "company_name": company_name,
                "timezone": country_info["timezones"][0],
                "country": country,
                "fy_start_date": f"{current_year}-01-01",
                "fy_end_date": f"{current_year}-12-31",
                "language": "english",
                "chart_of_accounts": "Standard",
            }
        )
    changeERPNames()
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


@frappe.whitelist()
def getNumberOfUsers():
    return frappe.db.count("User")


@frappe.whitelist()
def getNumberOfEmailSent():
    return frappe.db.count(
        "Communication",
        {"communication_type": "Communication", "sent_or_received": "Sent"},
    )


@frappe.whitelist()
def getDataBaseSizeOfSite():
    # return frappe.db.sql(
    #     "SELECT pg_database_size('" + frappe.conf.db_name + "');", as_dict=True
    # )[0].pg_database_size
    return frappe.db.sql(
        "SELECT table_schema "
        + frappe.conf.db_name
        + ", SUM(data_length + index_length) / (1024 * 1024) 'Database Size in MB' FROM information_schema.TABLES GROUP BY table_schema;"
    )


def checkDiskSize(path):
    # this finds the disk size of a folder named site in the /sites folderx
    import subprocess

    return subprocess.check_output(["du", "-hs", path]).decode("utf-8").split("\t")[0]


def convertToMB(sizeInStringWithPrefix):
    if sizeInStringWithPrefix == "0":
        return 0
    print("converting to MB", sizeInStringWithPrefix)
    prefix = sizeInStringWithPrefix[-1]
    if prefix == "M":
        return float(sizeInStringWithPrefix[:-1])
    elif prefix == "G":
        return float(sizeInStringWithPrefix[:-1]) * 1024
    elif prefix == "K":
        return float(sizeInStringWithPrefix[:-1]) / 1024
    return 0


@frappe.whitelist()
def getUsage():
    site = frappe.conf.site_name

    return {
        "users": getNumberOfUsers(),
        "emails": getNumberOfEmailSent(),
        "storage": {
            "database_size": str(getDataBaseSizeOfSite()[1][1]) + "M",
            "site_size": checkDiskSize("./" + site),
            "backup_size": checkDiskSize("./" + site + "/private/backups"),
        },
    }


def alertForUpgrade():
    frappe.msgprint("alertForUpgrade")
    user_limit = frappe.conf.max_users if frappe.conf.max_users else 1000
    email_limit = frappe.conf.max_email_limit if frappe.conf.max_email_limit else 1000
    storage_limit = frappe.conf.max_storage if frappe.conf.max_storage else 1000
    usage = getUsage()
    print(user_limit, email_limit, storage_limit, usage)
    alerMessage = ""
    if (
        int(usage["users"]) >= int(user_limit)
        or int(usage["emails"]) >= int(email_limit)
        or convertToMB(usage["storage"]["site_size"])
        + convertToMB(usage["storage"]["database_size"])
        >= int(storage_limit)
    ):
        alerMessage = "You have reached the maximum limit of your plan, please upgrade your plan to continue using the system. Your site backups and imports have been blocked"
    return alerMessage


@frappe.whitelist()
def getDecryptedPassword(*args, **kwargs):
    print("getDecryptedPassword", kwargs)
    return getDecryptedPassword(kwargs["password"])


def getInstalledApps(site):
    import subprocess

    output = (
        subprocess.check_output(
            " bench --site {} list-apps --format text".format(site),
            shell=True,
        )
        .decode("utf-8")
        .split("\n")
    )
    output = [x for x in output if x != ""]
    return output


@frappe.whitelist()
def installApp(app):
    frappe.utils.execute_in_shell(
        "bench --site {} install-app {}".format(frappe.local.site, app)
    )


@frappe.whitelist()
def installApps(*args, **kwargs):
    installedApps = getInstalledApps(frappe.local.site)
    apps_to_install = kwargs["apps"][1:-1].split(",")
    print(apps_to_install)
    for app in apps_to_install:
        if app not in installedApps:
            installApp(app)
    return "OK"
