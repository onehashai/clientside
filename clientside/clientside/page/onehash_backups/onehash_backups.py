import datetime
import os

import frappe
from frappe.utils import cint, convert_utc_to_system_timezone, get_site_path


@frappe.whitelist()
def get_context(context):
	frappe.only_for("System Manager")
	backup_path = get_site_path("private", "backups")
	limit = cint(frappe.db.get_singles_value("System Settings", "backup_limit")) or 7
	files = [
		path
		for path in (os.path.join(backup_path, name) for name in os.listdir(backup_path))
		if os.path.isfile(path) and path.endswith("sql.gz")
	]
	files.sort(key=os.path.getmtime, reverse=True)
	return {"files": [_backup_details(path) for path in files[:limit]]}


def _backup_details(path):
	modified = convert_utc_to_system_timezone(
		datetime.datetime.utcfromtimestamp(os.path.getmtime(path))
	).strftime("%a %b %d %H:%M %Y")
	size = os.path.getsize(path)
	formatted_size = f"{size / 1048576:.1f}M" if size > 1048576 else f"{size / 1024:.1f}K"
	return (f"/backups/{os.path.basename(path)}", modified, "-enc" in os.path.basename(path), formatted_size)
