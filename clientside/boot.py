import frappe


def get_config_date(*keys):
    for key in keys:
        value = frappe.conf.get(key)
        if value and value != "None":
            return value


def get_config_bool(key):
    return frappe.conf.get(key) in (1, "1", True, "true", "True", "yes", "Yes")


def extend_bootinfo(bootinfo):
    from frappe.utils import add_days, cint, getdate, today

    today_date = getdate(today())

    bootinfo.subscription_expired = False
    if not get_config_bool("skip_subscription_expiry"):
        subscription_status = frappe.conf.subscription_status
        site_expiry_date = get_config_date("site_expiry_date")
        fallback_expiry_date = get_config_date(
            "invoice_due_date", "subscription_ends_on"
        )

        expiry_date = getdate(site_expiry_date or fallback_expiry_date)
        if not site_expiry_date and expiry_date:
            expiry_date = add_days(
                expiry_date,
                cint(frappe.conf.get("subscription_expiry_grace_days", 5)),
            )

        if subscription_status in [
            "canceled",
            "incomplete",
            "incomplete_expired",
            "paused",
        ]:
            bootinfo.subscription_expired = True

        elif subscription_status in ["past_due", "trialing", "unpaid"]:
            if expiry_date:
                if today_date > expiry_date:
                    bootinfo.subscription_expired = True

    bootinfo.chat_widget_base_url = frappe.conf.chat_widget_base_url
    bootinfo.chat_widget_token = frappe.conf.chat_widget_token
    bootinfo.chat_widget_disabled = frappe.conf.chat_widget_disabled
