import frappe

def extend_bootinfo(bootinfo):
    from frappe.utils import today, getdate, add_days

    subscription_ends_on = frappe.conf.subscription_ends_on
    subscription_status = frappe.conf.subscription_status

    bootinfo.subscription_expired = False

    if subscription_status in ["unpaid", "canceled", "incomplete", "incomplete_expired", "paused"]:
        bootinfo.subscription_expired = True


    elif subscription_status in ["past_due", "trialing"]:
        if subscription_ends_on:
            today_date = getdate(today())
            expiry_date = getdate(subscription_ends_on)

            if subscription_status != "trialing" and today_date > add_days(expiry_date, 5):
                bootinfo.subscription_expired = True

    bootinfo.chat_widget_base_url = frappe.conf.chat_widget_base_url
    bootinfo.chat_widget_token = frappe.conf.chat_widget_token
    bootinfo.chat_widget_disabled = frappe.conf.chat_widget_disabled
