import frappe
from frappe import _
from frappe.core.doctype.system_settings.system_settings import SystemSettings

class SystemSettingsOverride(SystemSettings):
    def validate_backup_limit(self):
        if not self.backup_limit or self.backup_limit != 10:
            frappe.msgprint(_("Number of backups must be ten."), alert=True)
            self.backup_limit = 10
