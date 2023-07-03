import json
import frappe
import requests
import subprocess
import os
from frappe.utils import cstr
from frappe.core.doctype.user.user import test_password_strength
from frappe.utils import cint
from frappe.utils.background_jobs import enqueue
import boto3


@frappe.whitelist(allow_guest=True)
def check_password_strength(*args, **kwargs):
    print("ljewfhe", kwargs)
    print("check password strength called")
    print(kwargs)
    passphrase = kwargs["password"]
    first_name = kwargs["first_name"]
    last_name = kwargs["last_name"]
    email = kwargs["email"]
    print(passphrase, first_name, last_name, email)
    user_data = (first_name, "", last_name, email, "")
    if "'" in passphrase or '"' in passphrase:
        return {
            "feedback": {
                "password_policy_validation_passed": False,
                "suggestions": ["Password should not contain ' or \""],
            }
        }
    return test_password_strength(passphrase, user_data=user_data)


from frappe.geo.country_info import get_country_timezone_info
from frappe.desk.doctype.workspace.workspace import update_page


def checkEmailFormatWithRegex(email):
    import re

    regex = "^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$"
    if re.search(regex, email):
        return True
    else:
        return False


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
    update_page("ERPNext Integrations", "OneHash Integrations", "integration", "", 1)


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

    frappe.delete_doc_if_exists("Page", "welcome-to-erpnext", force=1)
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
from frappe.core.doctype.user.user import get_system_users
def get_number_of_emails_sent(sender = frappe.conf.email):
    return frappe.db.count(
        "Email Queue",
        { "sender": sender},
    )
@frappe.whitelist()
def getUsage():
    import datetime
    site = frappe.conf.site_name
    print(frappe.conf.expiry_date)
    expiry_date = frappe.utils.get_datetime(frappe.conf.expiry_date).date()
    print(expiry_date, datetime.date.today())
    days_left = (expiry_date - datetime.date.today()).days
    start_date = None
    if frappe.conf.last_purchase_date:
        start_date = frappe.utils.get_datetime(frappe.conf.last_purchase_date).date()
    else :
        start_date = frappe.utils.get_datetime(frappe.conf.creation_date).date()
    total_days = (expiry_date - start_date).days
    return {
        "start_date": start_date,
        "expiry_date": expiry_date,
        "users": len(get_system_users()),
        "emails": get_number_of_emails_sent(),
        "days_left": days_left,
        "total_days": total_days,
        "storage": {
            "database_size": str(getDataBaseSizeOfSite()[1][1]) + "M",
            "site_size": str(0.0045 + convertToMB(checkDiskSize("./" + site + "/public")) + convertToMB(checkDiskSize("./" + site + "/private/files")) ) + "M",
            "backup_size": checkDiskSize("./" + site + "/private/backups"),
        },
        "user_limit":frappe.conf.max_users,
        "email_limit":frappe.conf.max_email,
        "storage_limit":str(frappe.conf.max_space) + 'G',
    }


def alertForUpgrade():
    # frappe.msgprint("alertForUpgrade")
    pass


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


def post_install():
    changeERPNames()


from frappe.integrations.offsite_backup_utils import (
    generate_files_backup,
    get_latest_backup_file,
    send_email,
    validate_file_size,
)

from rq.timeouts import JobTimeoutException


@frappe.whitelist()
def take_backups_s3(retry_count=0):
    try:
        validate_file_size()
        backup_to_s3()
    except JobTimeoutException:
        if retry_count < 2:
            take_backups_s3(retry_count=retry_count + 1)

    except Exception:
        print(frappe.get_traceback())


def backup_to_s3():
    from frappe.utils import get_backups_path
    from frappe.utils.backups import new_backup

    bucket = frappe.conf.aws_bucket_name
    backup_files = True

    conn = boto3.client(
        "s3",
        aws_access_key_id=frappe.conf.aws_access_key_id,
        aws_secret_access_key=frappe.conf.aws_secret_access_key,
        endpoint_url=frappe.conf.endpoint_url,
    )

    if frappe.flags.create_new_backup:
        backup = new_backup(
            ignore_files=False,
            backup_path_db=None,
            backup_path_files=None,
            backup_path_private_files=None,
            force=True,
        )
        print(
            backup.backup_path_db,
            backup.backup_path_files,
            backup.backup_path_private_files,
            backup.backup_path_conf,
        )
        print(get_backups_path())
        db_filename = os.path.join(
            get_backups_path(), os.path.basename(backup.backup_path_db)
        )
        site_config = os.path.join(
            get_backups_path(), os.path.basename(backup.backup_path_conf)
        )
        if backup_files:
            files_filename = os.path.join(
                get_backups_path(), os.path.basename(backup.backup_path_files)
            )
            private_files = os.path.join(
                get_backups_path(), os.path.basename(backup.backup_path_private_files)
            )
    else:
        if backup_files:
            (
                db_filename,
                site_config,
                files_filename,
                private_files,
            ) = get_latest_backup_file(with_files=backup_files)

            if not files_filename or not private_files:
                generate_files_backup()
                (
                    db_filename,
                    site_config,
                    files_filename,
                    private_files,
                ) = get_latest_backup_file(with_files=backup_files)

        else:
            db_filename, site_config = get_latest_backup_file()

    folder = os.path.basename(db_filename)[:15] + "/"
    print("folder name in s3", folder)
    # for adding datetime to folder name
    print(
        db_filename,
        folder,
    )
    to_upload_config = []
    to_upload_config.append([db_filename, folder])
    to_upload_config.append([site_config, folder])

    # TODO: delete the files after uploading
    # call function on site fresh.localhost to save details of backup

    if backup_files:
        if private_files:
            to_upload_config.append([private_files, folder])

        if files_filename:
            to_upload_config.append([files_filename, folder])
    for file in to_upload_config:
        import threading

        t = threading.Timer(120.0, os.remove, args=[file[0]])
        t.start()
        upload_file_to_s3(file[0], file[1], conn, bucket)


def upload_file_to_s3(filename, folder, conn, bucket):
    destpath = os.path.join(folder, os.path.basename(filename))
    command = "bench --site {} execute bettersaas.bettersaas.doctype.saas_sites.saas_sites.insert_backup_record --args \"'{}','{}','{}'\"".format(
        frappe.conf.admin_subdomain + "." + frappe.conf.domain,
        filename[2:],
        destpath,
        frappe.local.site,
    )
    print("file name", filename)
    try:
        conn.upload_file(filename, bucket, destpath)  # Requires PutObject permission
        frappe.utils.execute_in_shell(command)
    except Exception as e:
        frappe.log_error()
        print("Error uploading: %s" % (e))


# @frappe.whitelist()
# def download_backup( bucket="onehash", filename="", destpath):
#     conn = boto3.client(
#         "s3",
#         aws_access_key_id=frappe.conf.aws_access_key_id,
#         aws_secret_access_key=frappe.conf.aws_secret_access_key,
#         endpoint_url=frappe.conf.endpoint_url,
#     )
#     conn.download_file(bucket, filename, destpath)

@frappe.whitelist()
def delete_site_from_server():
    import requests
    import time
    command = "bench drop-site {} --db-root-password {}".format(frappe.local.site, frappe.conf.db_pass)
    os.system(command)
    time.sleep(3)
    return "OK"


@frappe.whitelist(allow_guest=True)
def get_all_apps():
    site_name = cstr(frappe.local.site)
    all_apps = frappe.db.get_list('Available Apps',fields=['*'])
    site_apps = subprocess.check_output('bench --site {s_name} list-apps'.format(s_name = site_name),shell=True).decode('utf-8').split('\n')
    for app in all_apps:
        if app.app_name in site_apps:
            app['installed']='true'
        else:
            app['installed']='false'

    return all_apps

@frappe.whitelist(allow_guest=True)
def install_app(*args,**kwrgs):
    arr=[]
    for key,value in kwrgs.items():
        arr.append((key,value))
    app_name = arr[0][1]
    site_name = cstr(frappe.local.site)
    if app_name == 'india_compliance':
        os.system('bench --site {s_name} install-app india_compliance'.format(s_name=site_name))
    elif app_name =='posawesome':
        os.system('bench --site {s_name} install-app posawesome'.format(s_name=site_name))
    else:
        return "Failure"
    return 'Success'
    

@frappe.whitelist(allow_guest=True)
def uninstall_app(*args,**kwrgs):
    arr=[]
    for key,value in kwrgs.items():
        arr.append((key,value))
    app_name = arr[0][1]
    site_name = cstr(frappe.local.site) 
    check = os.system('bench --site {s_name} uninstall-app {a_name} --yes --no-backup'.format(s_name = site_name,a_name=app_name))  
    if check:
        return 'Success'
    else:
        return 'Failure'




@frappe.whitelist()
def verify_custom_domain(new_domain):
    ## if domain does not have www then add it
    if new_domain in frappe.conf.domains :
        return ["VERIFIED",new_domain]
    parts = new_domain.split(".")
    if len(parts) < 2:
        return ["INVALID_DOMAIN_FORMAT",""]
    if len(parts) == 2:
        new_domain = "www." + new_domain
    print("checking for",new_domain)
    command = "dig {} CNAME +short".format(new_domain)
    try:
        cname = frappe.utils.execute_in_shell(command)[1].decode("utf-8").strip()[:-1]
        print("cname", cname)
        if cname == frappe.local.site and new_domain != frappe.local.site :
            command = "bench setup add-domain {} --site {}".format( new_domain, frappe.local.site)
            frappe.utils.execute_in_shell(command)
            frappe.utils.execute_in_shell("bench setup nginx --yes")
            frappe.utils.execute_in_shell("echo {} | sudo -S service nginx reload".format(frappe.conf.root_password))
            return ["VERIFIED",cname]
        if new_domain == frappe.local.site:
            return ["ALREADY_REGISTERED",cname]
        return ["INVALID_RECORD",cname]
            
    except Exception as e:
        print(e)
        return[ "INVALID_DOMAIN",""]
    
