import frappe

def extend_bootinfo(bootinfo):
    from frappe.utils import today, getdate, add_days

    subscription_ends_on = frappe.conf.subscription_ends_on

    if subscription_ends_on:
        if getdate(today()) > add_days(getdate(subscription_ends_on), 5):
            bootinfo.subscription_expired = True

    bootinfo.chat_widget_base_url = frappe.conf.chat_widget_base_url
    bootinfo.chat_widget_token = frappe.conf.chat_widget_token