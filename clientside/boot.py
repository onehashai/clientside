import frappe


def get_config_date(*keys):
    for key in keys:
        value = frappe.conf.get(key)
        if value and value != "None":
            return value


def extend_bootinfo(bootinfo):
    from frappe.utils import today, getdate, add_days

    today_date = getdate(today())

    subscription_status = frappe.conf.subscription_status
    site_expiry_date = get_config_date("site_expiry_date")
    fallback_expiry_date = get_config_date("invoice_due_date", "subscription_ends_on")

    expiry_date = getdate(site_expiry_date or fallback_expiry_date)
    if not site_expiry_date and expiry_date:
        expiry_date = add_days(expiry_date, 5)
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
            if today_date > expiry_date:
                bootinfo.subscription_expired = True

    bootinfo.chat_widget_base_url = frappe.conf.chat_widget_base_url
    bootinfo.chat_widget_token = frappe.conf.chat_widget_token
    bootinfo.chat_widget_disabled = frappe.conf.chat_widget_disabled
