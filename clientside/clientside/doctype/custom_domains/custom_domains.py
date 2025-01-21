# Copyright (c) 2023, OneHash and contributors
# For license information, please see license.txt

import frappe
import time
import subprocess
import re
from frappe.utils import execute_in_shell
from frappe.model.document import Document

def check_cname_record(domain):
    try:
        command = f"dig +short CNAME {domain}"
        result = subprocess.check_output(command, shell=True).decode('utf-8').strip()
        c_names = result.split("\n")
        for cname in c_names:
            cname = cname.strip('.')
            if cname == frappe.local.site:
                return True
        return False
    except subprocess.CalledProcessError as e:
        return False
    except Exception as e:
        return False

def generate_custom_domain_cert(domain):
    current_domains = []
    for key in frappe.conf.domains:
        if type(key) == dict:
            current_domains.append(key["domain"])
        else:
            current_domains.append(key)
    if domain in current_domains:
        return False, "Already Verified"
    
    try:
        cert_command = "echo {} | sudo -S certbot certonly --nginx -d {} --email {} --agree-tos --non-interactive".format(
            frappe.conf.root_password, domain, "support@onehash.ai"
        )
        process = subprocess.run(cert_command, capture_output=True, text=True)

        if process.returncode != 0:
            return False, "SSL certificate generation failed"

        command = "bench setup add-domain {} --site {} --ssl-certificate {} --ssl-certificate-key {}".format(
            domain, frappe.local.site, f"/etc/letsencrypt/live/{domain}/fullchain.pem", f"/etc/letsencrypt/live/{domain}/privkey.pem"
        )
        execute_in_shell(command)
        # after adding the domain, reload nginx after 4 seconds async task
        time.sleep(4)
        execute_in_shell("bench setup nginx --yes")
        execute_in_shell(
            "echo {} | sudo -S service nginx reload".format(
                frappe.conf.root_password
            )
        )
        return True, f"Domain is valid and properly pointed to {frappe.local.site}"
    except Exception as e:
        print(e)
        return False, f"Failed to generate certificate for custom domain"
    
@frappe.whitelist()
def verify_custom_domain(domain):
    if not domain:
        return False, "Domain is empty."
    
    domain_pattern = r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'
    if not re.match(domain_pattern, domain):
        return False, "Domain is not in a proper format or does not contain a subdomain."
    
    parts = domain.split('.')
    if len(parts) < 3:
        return False, "Domain does not have a subdomain. Please provide a fully qualified domain (e.g., sub.example.com)."
    
    if check_cname_record(domain):
        generate_custom_domain_cert(domain)
    else:
        return False, f"No CNAME record pointing to {frappe.local.site} found"
    
    
class CustomDomains(Document):
	pass
