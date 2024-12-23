# Copyright (c) 2023, OneHash and contributors
# For license information, please see license.txt

import frappe
import time
from frappe.model.document import Document

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
class CustomDomains(Document):
	pass
