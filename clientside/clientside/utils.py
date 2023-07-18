import frappe
import requests

import subprocess
import os
from frappe.utils import cstr
from frappe.core.doctype.user.user import test_password_strength
import boto3
from frappe.integrations.offsite_backup_utils import (
    generate_files_backup,
    get_latest_backup_file,
    validate_file_size,
)
from clientside.stripe import StripeSubscriptionManager
from frappe.core.doctype.user.user import get_system_users
from rq.timeouts import JobTimeoutException
from frappe.geo.country_info import get_country_timezone_info
from frappe.desk.doctype.workspace.workspace import update_page

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
def checkEmailFormatWithRegex(email):
    import re

    regex = "^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$"
    if re.search(regex, email):
        return True
    else:
        return False

def changeERPNames():
    try:
        update_page("ERPNext Settings", "OneHash Settings", "setting", "", 1)
    except:
        print("error updating page", "ERPNext Settings", "OneHash Settings", "setting", "", 1)
    try:
        update_page("ERPNext Integrations", "OneHash Integrations", "integration", "", 1)
    except:
        print("error updating page", "ERPNext Integrations", "OneHash Integrations", "integration", "", 1)

@frappe.whitelist(allow_guest=True)
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
    # get the newly created user and add the role  "OneHash Manager"
    # print 
  #  changeERPNames()
    user = frappe.get_doc("User", email)
    user.add_roles("OneHash Manager")
    user.save(ignore_permissions=True)
    frappe.utils.execute_in_shell("bench --site {} clear-cache".format(frappe.local.site))
    frappe.utils.execute_in_shell("bench --site {} clear-website-cache".format(frappe.local.site))
    
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
    return frappe.db.sql(
        "SELECT table_schema "
        + frappe.conf.db_name
        + ", SUM(data_length + index_length) / (1024 * 1024) 'Database Size in MB' FROM information_schema.TABLES GROUP BY table_schema;"
    )


def checkDiskSize(path):
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
def get_number_of_emails_sent(sender = frappe.conf.email):
    return frappe.conf.onehash_mail_usage or 0
@frappe.whitelist(allow_guest=True)
def getUsage():
    import requests
    url = "http://"+frappe.conf.admin_url+ "/api/method/bettersaas.bettersaas.doctype.saas_sites.saas_sites.get_site_backup_size?sitename=" + frappe.local.site
    resp = requests.get(url)
    import datetime
    site = frappe.local.site
    subscription = StripeSubscriptionManager()
    sub = subscription.get_onehash_subscription(frappe.conf.customer_id)
    if(sub != "NONE"):
        start_date = datetime.datetime.fromtimestamp(sub["current_period_start"])
        end_date = datetime.datetime.fromtimestamp(sub["current_period_end"])
    
        days_left = (end_date - datetime.datetime.now()).days
        total_days = (end_date - start_date).days
        current_product = subscription.get_current_onehash_product(frappe.conf.customer_id)
    else :
        days_left = 0
        total_days = 0
        current_product = {
            "name":"NO_PRODUCT",
        }
    return {
        "users": len(get_system_users()),
        "emails": get_number_of_emails_sent(),
        "days_left": days_left,
        "total_days": total_days,
        "plan": current_product["name"],
        "storage": {
            "database_size": str(getDataBaseSizeOfSite()[1][1]) + "M",
            "site_size": str(0.0045 + convertToMB(checkDiskSize("./" + site + "/public")) + convertToMB(checkDiskSize("./" + site + "/private/files")) ) + "M",
            "backup_size": str(resp.json()["message"]) + "M",
        },
        "user_limit":frappe.conf.max_users,
        "email_limit":frappe.conf.max_email,
        "storage_limit":str(frappe.conf.max_space) + 'G',
        "stripe_conf": getSiteStripeConfig()
    }

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
    createRole("OneHash Manager")
    changeERPNames()
    add_usage_info() 
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
    upload_keys = [ os.path.join(x[1],os.path.basename(x[0]))  for x in to_upload_config]
    print("uploading files to s3",len(to_upload_config))
    backup_size = checkDiskSize("./" + frappe.local.site + "/private/backups")
    command = "bench --site {} execute bettersaas.bettersaas.doctype.saas_sites.saas_sites.insert_backup_record --args \"'{}','{}','{}','{}','{}','{}'\"".format(
        frappe.conf.admin_subdomain + "." + frappe.conf.domain,upload_keys[0],upload_keys[2],upload_keys[3],upload_keys[1] ,frappe.local.site,backup_size)
    try:
        p =frappe.utils.execute_in_shell(command)
        print(p)
    except Exception as e:
        print(e)
    for file in to_upload_config:
        import threading

       # t = threading.Timer(120.0, os.remove, args=[file[0]])
       # t.start()
        upload_file_to_s3(file[0], file[1], conn, bucket)


def upload_file_to_s3(filename, folder, conn, bucket):
    destpath = os.path.join(folder, os.path.basename(filename))
    try:
        conn.upload_file(filename, bucket, "site_backups/"+ frappe.local.site + "/" + destpath)  # Requires PutObject permission
        
        # delete the file after uploading
        os.remove(filename)
        
    except Exception as e:
        frappe.log_error()
        print("Error uploading: %s" % (e))
    return True
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
    admin_url = frappe.conf.admin_url
    url = 'http://{s_name}/api/method/bettersaas.bettersaas.doctype.available_apps.available_apps.get_apps'.format(s_name = admin_url)
    try:
        site_name=frappe.local.site
        site_apps = subprocess.check_output('bench --site {s_name} list-apps'.format(s_name =site_name),shell=True).decode('utf-8').split('\n')
        res = json.loads(requests.get(url).text)
        for app in res['message']:
            if app['app_name'] in site_apps:
                app['installed']='true'
            else:
                app['installed']='false'

        return res['message']
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return e





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

@frappe.whitelist()
def install_app(*args,**kwrgs):
    arr=[]
    for key,value in kwrgs.items():
        arr.append((key,value))
    app_name = arr[0][1]
    site_name = frappe.local.site
    if app_name == 'india_compliance':
        os.system('bench --site {s_name} install-app india_compliance'.format(s_name=site_name))
    elif app_name =='posawesome':
        os.system('bench --site {s_name} install-app posawesome'.format(s_name=site_name))
    elif app_name == 'whitelabel':
        os.system('bench --site {s_name} install-app whitelabel'.format(s_name=site_name))
    else:
        return "Failure"
    return 'Success'
    


@frappe.whitelist()
def uninstall_app(*args,**kwrgs):
    arr=[]
    for key,value in kwrgs.items():
        arr.append((key,value))
    app_name = arr[0][1]
    site_name = frappe.local.site
    check = os.system('bench --site {s_name} uninstall-app {a_name} --yes --no-backup'.format(s_name = site_name,a_name=app_name))  
    if check:
        return 'Success'
    else:
        return 'Failure'

@frappe.whitelist()
def verify_custom_domain(new_domain):
    if new_domain in frappe.conf.domains :
        return ["VERIFIED",new_domain]
    parts = new_domain.split(".")
    if len(parts) < 2:
        return ["INVALID_DOMAIN_FORMAT",""]
    if len(parts) == 2:
        new_domain = "www." + new_domain
    command = "dig {} CNAME +short".format(new_domain)
    try:
        cname = frappe.utils.execute_in_shell(command)[1].decode("utf-8").strip()[:-1]
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


@frappe.whitelist(allow_guest=True)
def createNewPurchaseSession(*args, **kwargs):
    stripe = StripeSubscriptionManager()
    resp =  stripe.create_new_purchase_session(frappe.conf.customer_id,kwargs["price_id"],frappe.local.site.split(".")[0])
    return {"url":resp}
@frappe.whitelist(allow_guest=True)
def upgradeOneHashPlan(*args, **kwargs):
    stripe = StripeSubscriptionManager(country=frappe.conf.country or "US")
    res = stripe.upgrade_subscription(frappe.conf.customer_id,kwargs["price_id"],frappe.local.site.split(".")[0])
    if res != "SUCCESS" and res!="PENDING_UPDATE":
        print("upgrade failed")
        frappe.publish_realtime("upgrade_failed",room=f"{frappe.local.site}:website",message={"reason":res})
    elif res == "SUCCESS":
        frappe.publish_realtime("upgrade_succeeded",room=f"{frappe.local.site}:website",message={"reason":res})
    return {"url":"response"}
@frappe.whitelist(allow_guest=True)
def getSiteStripeConfig():
    country = frappe.conf.country or "US"
    if country == "IN":
        return {
            "publishable_key":frappe.conf.publishable_key_in,
            "customer_portal":frappe.conf.customer_portal_in,
            "country":frappe.conf.country,
            "pricing":{
                        "ONEHASH_PRO":{
                            "monthly":{
                                "price_id":"price_1NTJIZCwmuPVDwVyrKuQqnUY",
                                "price":"16,250",
                            },
                            "yearly":{
                                "price_id":"price_1NTJIZCwmuPVDwVyGNdlnJsl",
                                "price":"195,000"
                            }
                            
                        },
                        "ONEHASH_STARTER":{
                            "monthly":{
                                "price_id":"price_1NTJGHCwmuPVDwVyLgzRNKRI",
                                "price":"5,500",
                            },
                            "yearly":{
                                "price_id":"price_1NTJFOCwmuPVDwVyqPnGUQ6L",
                                "price":"48,000"
                            }
                            
                        },
                        "ONEHASH_PLUS":{
                            "monthly":{
                                "price_id":"price_1NTJHECwmuPVDwVywGmFiC0m",
                                "price":"10,300",
                            },
                            "yearly":{
                                "price_id":"price_1NTJHECwmuPVDwVyplRDnjow",
                                "price":"96,000"
                            }
                        }
            }
        }
    else :
        return {
            "publishable_key":frappe.conf.publishable_key,
            "customer_portal":frappe.conf.customer_portal,
            "country":frappe.conf.country,
            "pricing":{
                "ONEHASH_PRO":{
                        "monthly":{
                            "price_id":"price_1NTKzuEwPMdYWOIL1UBnXt9r",
                            "price":"649",
                        },
                        "yearly":{
                            "price_id":"price_1NTKzREwPMdYWOILklDKorqG",
                            "price":"6,588"
                        }
                    },
                "ONEHASH_STARTER":{
                    "monthly":{
                        "price_id":"price_1NTKs4EwPMdYWOILQ8TBJ5Mi",
                        "price":"129",
                    },
                    "yearly":{
                        "price_id":"price_1NTKxvEwPMdYWOILymCB3hWr",
                        "price":"1,188"
                    }
    
                },
                "ONEHASH_PLUS":{
                    "monthly":{
                        "price_id":"price_1NTKs4EwPMdYWOILQ8TBJ5Mi",
                        "price":"299"
                    },
                    "yearly":{
                        "price_id":"price_1NTKypEwPMdYWOILdybQnp2W",
                        "price":"2,988"
                    }
                }
        }
        }
        
# expire cache value  after 24 hr

@frappe.whitelist(allow_guest=True)
def hasRoleToManageOnehashPayments():
    # check if user has role "OneHash Manager"
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    print(user_roles)
    if "OneHash Manager" in user_roles:
        return True
    return False
    
def createRole(role_name):
    print("creating role " + role_name)
    role = frappe.get_doc({
        "doctype":"Role",
        "role_name":role_name,
        "desk_access":1,
    })
    role.insert(ignore_permissions=True)
    return role.name

    
# errors 

def add_usage_info():
    navbar_settings = frappe.get_single("Navbar Settings")
    # if frappe.db.exists("Navbar Item", {"item_label": "Usage Infooo"}):
    #     return
 

    navbar_settings.append(
		"settings_dropdown",
		{
			"item_label": "Usage Infooo",
			"item_type": "Action",
			"action": "frappe.set_route('Form','Usage Info')",
			"is_standard": 1,
			"idx": 5,
		},
	)
    navbar_settings.save()
