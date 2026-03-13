import frappe


def extend_bootinfo(bootinfo):
    from frappe.utils import today, getdate, add_days

    today_date = getdate(today())

    subscription_ends_on = frappe.conf.subscription_ends_on
    subscription_status = frappe.conf.subscription_status
    invoice_due_date = frappe.conf.invoice_due_date

    expiry_date = getdate(invoice_due_date or subscription_ends_on)
    bootinfo.subscription_expired = False

    if subscription_status in [
        "unpaid",
        "canceled",
        "incomplete",
        "incomplete_expired",
        "paused",
    ]:
        bootinfo.subscription_expired = True

    elif subscription_status in ["past_due", "trialing"]:
        if expiry_date:
            if subscription_status != "trialing" and today_date > add_days(
                expiry_date, 5
            ):
                bootinfo.subscription_expired = True

    bootinfo.chat_widget_base_url = frappe.conf.chat_widget_base_url
    bootinfo.chat_widget_token = frappe.conf.chat_widget_token
    bootinfo.chat_widget_disabled = frappe.conf.chat_widget_disabled
