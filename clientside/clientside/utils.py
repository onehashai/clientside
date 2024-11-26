import frappe
import requests
import json
import os
import subprocess
import boto3
from clientside.stripe import StripeSubscriptionManager
from frappe.utils import validate_email_address
# from frappe_s3_attachment.controller import get_total_file_sizes
from frappe.core.doctype.user.user import test_password_strength
from frappe.integrations.offsite_backup_utils import (
    generate_files_backup,
    get_latest_backup_file,
    validate_file_size,
)
from frappe.core.doctype.user.user import get_system_users
from frappe.geo.country_info import get_country_timezone_info
from frappe.desk.doctype.workspace.workspace import update_page
from rq.timeouts import JobTimeoutException

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

def change_erp_to_onehash():
    try:
        update_page("ERPNext Settings", "OneHash Settings", "setting", "", 0)
    except:
        print(
            "error updating page",
            "ERPNext Settings",
            "OneHash Settings",
            "setting",
            "",
            1,
        )
    try:
        update_page(
            "ERPNext Integrations", "OneHash Integrations", "integration", "", 0
        )
    except:
        print(
            "error updating page",
            "ERPNext Integrations",
            "OneHash Integrations",
            "integration",
            "",
            1,
        )

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
    frappe.delete_doc_if_exists("Page", "welcome-to-erpnext", force=1)
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
    return {"status": "OK"}

@frappe.whitelist()
def get_number_of_users():
    return frappe.db.count("User")

@frappe.whitelist()
def get_number_of_emails_sent():
    return frappe.db.count(
        "Communication",
        {"communication_type": "Communication", "sent_or_received": "Sent"},
    )

@frappe.whitelist()
def get_database_size_of_site():
    return frappe.db.sql(
        "SELECT table_schema "
        + frappe.conf.db_name
        + ", SUM(data_length + index_length)  'Database Size in B' FROM information_schema.TABLES GROUP BY table_schema;"
    )

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

def get_number_of_emails_sent(sender=frappe.conf.email):
    return frappe.conf.onehash_mail_usage or 0

def get_backup_size_of_site():
    url = (
        "http://"
        + frappe.conf.admin_url
        + "/api/method/bettersaas.bettersaas.doctype.saas_sites.saas_sites.get_site_backup_size?site_name="
        + frappe.local.site
    )
    resp = requests.get(url)
    print("backup size", resp.json()["message"])
    return resp.json()["message"]

@frappe.whitelist(allow_guest=True)
def get_usage():
    import datetime

    site = frappe.local.site
    subscription = StripeSubscriptionManager()
    sub = subscription.get_onehash_subscription(frappe.conf.customer_id)
    if sub != "NONE":
        start_date = datetime.datetime.fromtimestamp(sub["current_period_start"])
        end_date = datetime.datetime.fromtimestamp(sub["current_period_end"])

        days_left = (end_date - datetime.datetime.now()).days
        total_days = (end_date - start_date).days
        current_product = subscription.get_current_onehash_product(
            frappe.conf.customer_id
        )
    else:
        days_left = 0
        total_days = 0
        current_product = {
            "name": "NO_PRODUCT",
        }
    return {
        "users": len(get_system_users()),
        "emails": get_number_of_emails_sent(),
        "days_left": days_left,
        "total_days": total_days,
        "plan": current_product["name"],
        "storage": {
            "database_size": get_database_size_of_site()[1][1],
            # "site_size": get_total_file_sizes(),
            "backup_size": get_backup_size_of_site(),
        },
        "user_limit": frappe.conf.max_users,
        "email_limit": frappe.conf.max_email,
        "storage_limit": int(frappe.conf.max_storage) * 1024 * 1024 * 1024,
        "stripe_conf": get_site_stripe_config(),
    }

def get_installed_apps(site):
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
def install_app(app):
    frappe.utils.execute_in_shell(
        "bench --site {} install-app {}".format(frappe.local.site, app)
    )

@frappe.whitelist()
def install_apps(*args, **kwargs):
    installed_apps = get_installed_apps(frappe.local.site)
    apps_to_install = kwargs["apps"][1:-1].split(",")
    for app in apps_to_install:
        if app not in installed_apps:
            install_app(app)
    return "OK"

def post_install():
    change_erp_to_onehash()
    add_options()

def create_zip_with_files(zip_file_path, files_to_zip):
    import zipfile

    """
    Create a zip file containing the specified files.

    Parameters:
        - zip_file_path (str): The path of the output zip file.
        - files_to_zip (list): An array of file paths to include in the zip.

    Returns:
        - None
    """
    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_zip:
            zipf.write(file_path, os.path.basename(file_path))

@frappe.whitelist()
def take_backups_s3(retry_count=0, is_manual=0, backup_limit=3, site=frappe.local.site):
    try:
        validate_file_size()
        backup_to_s3(is_manual=is_manual, backup_limit=backup_limit, site=site)
    except JobTimeoutException:
        if retry_count < 2:
            take_backups_s3(
                retry_count=retry_count + 1,
                is_manual=is_manual,
                backup_limit=backup_limit,
                site=site,
            )
    except Exception:
        print(frappe.get_traceback())

def backup_to_s3(is_manual=0, backup_limit=3, site=frappe.local.site):
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

    backup_size = check_disk_size("./" + site + "/private/backups")
    folder = os.path.basename(db_filename)[:15] + "/"
    to_upload_config = []
    to_upload_config.append([db_filename, folder])
    to_upload_config.append([site_config, folder])

    if backup_files:
        if private_files:
            to_upload_config.append([private_files, folder])

        if files_filename:
            to_upload_config.append([files_filename, folder])
    server_keys = [x[0] for x in to_upload_config]
    site_config_util = frappe.get_site_config(site_path=site)
    limit = int(site_config_util["max_storage"]) * 1024
    current_usage = (
        # get_total_file_sizes()
        get_database_size_of_site()[1][1]
        + get_backup_size_of_site()
    )
    if current_usage > convert_to_bytes(str(limit) + "G"):
        frappe.throw("Storage Limit Exceeded")
        for x in server_keys:
            os.remove(x)
    replaced_site_name = site.replace(".", "_")
    target_zip_file_name = (
        to_upload_config[0][1][:-1] + "-" + replaced_site_name + ".zip"
    )
    on_server_zip_key = site + "/private/" + target_zip_file_name
    create_zip_with_files(on_server_zip_key, server_keys)
    aws_key = "site_backups/" + site + "/" + target_zip_file_name
    try:
        conn.upload_file(on_server_zip_key, bucket, aws_key)
    except Exception as e:
        print("Error uploading files to s3", e)
    command = "bench --site {} execute bettersaas.bettersaas.doctype.saas_sites.saas_sites.insert_backup_record --args \"'{}','{}','{}','{}'\"".format(
        frappe.conf.admin_subdomain + "." + frappe.conf.domain,
        site,
        backup_size,
        "onehash/" + aws_key,
        is_manual,
    )
    try:
        frappe.utils.execute_in_shell(command)
        command_1 = "bench --site {} execute bettersaas.bettersaas.doctype.saas_sites.saas_sites.delete_old_backups --args \"'{}','{}'\"".format(
            frappe.conf.admin_subdomain + "." + frappe.conf.domain,
            backup_limit,
            site,
            is_manual,
        )
        frappe.utils.execute_in_shell(command_1)
        for key in server_keys:
            os.remove(key)
        os.remove(on_server_zip_key)
    except Exception as e:
        print(e)
    frappe.utils.execute_in_shell(
        "bench --site {} set-config backup_in_progress no".format(site)
    )

@frappe.whitelist(allow_guest=True)
def get_all_apps():
    url = "http://{site_name}/api/method/bettersaas.bettersaas.doctype.available_apps.available_apps.get_apps".format(
        site_name=frappe.conf.admin_url
    )
    try:
        site_apps = [x["app_name"] for x in frappe.utils.get_installed_apps_info()]
        res = json.loads(requests.get(url).text)
        apps_to_return = []
        for app in res["message"]:
            if app["app_name"] == "whitelabel":
                continue

            if app["app_name"] in site_apps:
                app["installed"] = "true"
            else:
                app["installed"] = "false"
            apps_to_return.append(app)
        return apps_to_return
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return e

@frappe.whitelist()
def install_app(*args, **kwrgs):
    arr = []
    for key, value in kwrgs.items():
        arr.append((key, value))
    app_name = arr[0][1]
    site_name = frappe.local.site
    frappe.utils.execute_in_shell(
        "bench --site {s_name} install-app {app_name}".format(
            s_name=site_name, app_name=app_name
        )
    )
    return "Success"

@frappe.whitelist()
def uninstall_app(*args, **kwrgs):
    arr = []
    for key, value in kwrgs.items():
        arr.append((key, value))
    app_name = arr[0][1]
    site_name = frappe.local.site
    frappe.utils.execute_in_shell(
        "bench --site {s_name} uninstall-app {a_name} --yes --no-backup".format(
            s_name=site_name, a_name=app_name
        )
    )
    return "Success"

@frappe.whitelist()
def delete_site_from_server():
    frappe.utils.execute_in_shell(
        "bench drop-site {site} --root-password {db_root_password} --force --no-backup".format(
            site=frappe.local.site, db_root_password=frappe.conf.root_password
        )
    )

@frappe.whitelist()
def verify_custom_domain(new_domain):
    current_domains = []
    for key in frappe.conf.domains:
        if type(key) == dict:
            current_domains.append(key["domain"])
        else:
            current_domains.append(key)
    if new_domain in current_domains:
        return ["VERIFIED", new_domain]
    parts = new_domain.split(".")
    if len(parts) < 2:
        return ["INVALID_DOMAIN_FORMAT", ""]
    if len(parts) == 2:
        new_domain = "www." + new_domain
    command = "dig {} CNAME +short".format(new_domain)
    try:
        import time

        cname = frappe.utils.execute_in_shell(command)[1].decode("utf-8").strip()[:-1]
        if cname == frappe.local.site and new_domain != frappe.local.site:
            command = "bench setup nginx --yes"
            frappe.utils.execute_in_shell(command)
            command = "echo {} | sudo -S service nginx reload"
            frappe.utils.execute_in_shell(command)
            command = "bench setup add-domain {} --site {}".format(
                new_domain, frappe.local.site
            )
            frappe.utils.execute_in_shell(command)
            command = "echo {} | sudo -S certbot certonly --nginx -d {}".format(
                frappe.conf.root_password, new_domain
            )
            resp = frappe.utils.execute_in_shell(command)
            frappe.msgprint("SSL certificate added" + str(resp))
            new_domains = frappe.conf.domains
            new_domains.append(
                new_domain
                # {
                #     "ssl_certificate": "/etc/letsencrypt/live/{}/fullchain.pem".format(
                #         new_domain
                #     ),
                #     "ssl_certificate_key": "/etc/letsencrypt/live/{}/privkey.pem".format(
                #         new_domain
                #     ),
                #     "domain": new_domain,
                # }
            )
            frappe.installer.update_site_config("domains", new_domains, validate=True)
            # after adding the domain, reload nginx after 4 seconds async task
            time.sleep(4)
            frappe.utils.execute_in_shell("bench setup nginx --yes")
            frappe.utils.execute_in_shell(
                "echo {} | sudo -S service nginx reload".format(
                    frappe.conf.root_password
                )
            )
        if new_domain == frappe.local.site:
            return ["ALREADY_REGISTERED", cname]
        return ["INVALID_RECORD", cname]
    except Exception as e:
        print(e)
        return ["INVALID_DOMAIN", ""]

@frappe.whitelist(allow_guest=True)
def create_new_purchase_session(*args, **kwargs):
    stripe = StripeSubscriptionManager()
    resp = stripe.create_new_purchase_session(
        frappe.conf.customer_id, kwargs["price_id"], frappe.local.site.split(".")[0]
    )
    return {"url": resp}

@frappe.whitelist(allow_guest=True)
def upgrade_onehash_plan(*args, **kwargs):
    stripe = StripeSubscriptionManager(country=frappe.conf.country or "US")
    res = stripe.upgrade_subscription(
        frappe.conf.customer_id, kwargs["price_id"], frappe.local.site.split(".")[0]
    )
    if res != "SUCCESS" and res != "PENDING_UPDATE":
        frappe.publish_realtime(
            "upgrade_failed",
            room=f"{frappe.local.site}:website",
            message={"reason": res},
        )
    elif res == "SUCCESS":
        frappe.publish_realtime(
            "upgrade_succeeded",
            room=f"{frappe.local.site}:website",
            message={"reason": res},
        )
    return {"url": "response"}

@frappe.whitelist(allow_guest=True)
def get_site_stripe_config():
    country = frappe.conf.country or "US"
    if country == "IN":
        return {
            "publishable_key": frappe.conf.publishable_key_in,
            "customer_portal": frappe.conf.customer_portal_in,
            "country": frappe.conf.country,
            "pricing": frappe.conf.stripe_prices["IN"]["prices"],
        }
    else:
        return {
            "publishable_key": frappe.conf.publishable_key,
            "customer_portal": frappe.conf.customer_portal,
            "country": frappe.conf.country,
            "pricing": frappe.conf.stripe_prices["US"]["prices"],
        }

@frappe.whitelist(allow_guest=True)
def has_role_to_manage_onehash_payments():
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    if "OneHash Manager" in user_roles:
        return True
    return False

def add_options():
    navbar_settings = frappe.get_single("Navbar Settings")
    navbar_settings.append(
        "settings_dropdown",
        {
            "item_label": "Usage Info",
            "item_type": "Action",
            "action": "frappe.set_route('Form','Usage-Info')",
            "is_standard": 1,
            "idx": 5,
        },
    )
    navbar_settings.append(
        "settings_dropdown",
        {
            "item_label": "Marketplace",
            "item_type": "Action",
            "action": "frappe.set_route('Form','market-place')",
            "is_standard": 1,
            "idx": 6,
        },
    )
    navbar_settings.append(
        "settings_dropdown",
        {
            "item_label": "Background Jobs",
            "item_type": "Action",
            "action": "frappe.set_route('Form','background_jobs')",
            "is_standard": 1,
            "idx": 7,
        },
    )
    navbar_settings.save()

def update_last_active():
    time = frappe.utils.now_datetime().strftime("%Y-%m-%d")
    command = "bench --site {site} set-config last_active '{time}'".format(
        site=frappe.local.site, time=time
    )
    frappe.utils.execute_in_shell(command)

@frappe.whitelist()
def schedule_files_backup():
    frappe.conf.backup_in_progress = "no"
    if frappe.conf.backup_in_progress and frappe.conf.backup_in_progress == "yes":
        frappe.throw("Backup is already in progress")
    frappe.utils.execute_in_shell(
        "bench --site {} set-config backup_in_progress yes".format(frappe.local.site)
    )
    backup_limit = frappe.db.get_single_value("System Settings", "backup_limit")
    frappe.enqueue(
        "clientside.clientside.utils.take_backups_s3",
        is_manual=1,
        backup_limit=backup_limit,
        queue="long",
        now=1,
    )

def make_object_public(bucket_name, object_name):
    conn = boto3.client(
        "s3",
        aws_access_key_id=frappe.conf.aws_access_key_id,
        aws_secret_access_key=frappe.conf.aws_secret_access_key,
    )
    conn.put_object_acl(ACL="public-read", Bucket=bucket_name, Key=object_name)

@frappe.whitelist(allow_guest=True)
def get_download_link(s3key):
    from botocore.client import Config

    bucket_name = frappe.conf.aws_bucket_name
    if not frappe._dev_server:
        s3key.replace("/onehash", "")
    make_object_public(bucket_name, s3key)
    conn = boto3.client(
        "s3",
        aws_access_key_id=frappe.conf.aws_access_key_id,
        aws_secret_access_key=frappe.conf.aws_secret_access_key,
        config=Config(signature_version="s3v4", region_name="ap-south-1"),
    )
    url = conn.generate_presigned_url(
        "get_object", Params={"Bucket": bucket_name, "Key": s3key}, ExpiresIn=3600
    )
    return url

@frappe.whitelist()
def get_backups():
    r = requests.get(
        "http://"
        + frappe.conf.admin_url
        + "/api/method/bettersaas.bettersaas.doctype.saas_site_backups.saas_site_backups.get_backups?site="
        + frappe.local.site
    ).json()
    return r["message"]
