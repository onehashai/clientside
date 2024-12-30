import click
import frappe
import sys
import requests
from frappe.commands import  pass_context
from frappe.exceptions import SiteNotSpecifiedError

def is_stock_site(admin_site, local_site):
    req = requests.get(
            "http://"
            + admin_site
            + "/api/method/bettersaas.bettersaas.doctype.saas_stock_sites.saas_stock_sites.is_stock_site?site="
            + local_site
        ).json()
    if req["message"]:
        return True
    else:
        return False
    
    
@click.command("saas-sites-backup")
@pass_context
def saas_sites_backup(context):
    from clientside.clientside.page.onehash_backups.onehash_backups import schedule_files_backup

    exit_code = 0
    for site in context.sites:
        try:
            frappe.init(site=site)
            frappe.connect()
            if site == frappe.conf.get("admin_url"):
                continue
            if is_stock_site(frappe.conf.get("admin_url"), site):
                continue
            schedule_files_backup(site)
        except Exception:
            click.secho(
                f"Backup failed for Site {site}. Database or site_config.json may be corrupted",
                fg="red",
            )
            exit_code = 1
            continue
        click.secho(
			"Backup for Site {} has been successfully completed".format(
				site
			),
			fg="green",
		)
        frappe.destroy()

    if not context.sites:
        raise SiteNotSpecifiedError

    sys.exit(exit_code)

commands = [
 saas_sites_backup
]
