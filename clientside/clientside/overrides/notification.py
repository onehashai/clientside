import frappe
from frappe.email.doctype.notification.notification import Notification


class NotificationOverride(Notification):
    def validate(self):
        if self.channel == "WhatsApp":
            hooks = frappe.get_hooks("whatsapp_notification_validate")
            for hook in hooks:
                frappe.get_attr(hook)(self)
        super().validate()

    def send(self, doc):
        if self.channel == "WhatsApp":
            hooks = frappe.get_hooks("whatsapp_notification_send")
            for hook in hooks:
                frappe.get_attr(hook)(self, doc)
        super().send(doc)
