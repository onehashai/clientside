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
    domains_config = frappe.get_site_config(site_path=frappe.local.site).get("domains")
    for item in domains_config:
        if isinstance(item, str):
            if item == domain:
                return False, "Domain already Verified"
        elif isinstance(item, dict):
            d = item.get("domain")
            if d == domain:
                return False, "Domain already Verified"
            
    try:
        cert_command = "sudo certbot certonly --nginx -d {} --email {} --agree-tos --non-interactive".format(
            domain, "support@onehash.ai"
        )

        process = subprocess.run(cert_command, capture_output=True, text=True, shell=True)
        if process.returncode != 0:
            return False, f"Certificate generation failed: {process.stderr}"

        command = "bench setup add-domain {} --site {} --ssl-certificate {} --ssl-certificate-key {}".format(
            domain, frappe.local.site, f"/etc/letsencrypt/live/{domain}/fullchain.pem", f"/etc/letsencrypt/live/{domain}/privkey.pem"
        )
        execute_in_shell(command)
        # after adding the domain, reload nginx after 4 seconds async task
        time.sleep(4)
        execute_in_shell("bench setup nginx --yes")
        execute_in_shell("sudo service nginx reload")
        return True, f"Domain pointed to {frappe.local.site}"
    except Exception as e:
        print(e)
        return False, f"Failed to generate certificate: {e}"
    
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
        return generate_custom_domain_cert(domain)
    else:
        return False, f"No CNAME record pointing to {frappe.local.site} found"
    
class CustomDomains(Document):
	pass
