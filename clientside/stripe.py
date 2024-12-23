import stripe
import frappe
import locale
import datetime
from frappe import _

def get_products(country):
    products_list = []
    if country == "IN":
        products = frappe.conf.get("stripe_prices",{}).get("IN", {}).get("products",{})
        product_id_crm = products.get("ONEHASH_CRM",{})['product_id']
        product_id_erp = products.get("ONEHASH_ERP",{})['product_id']
        price_ids_crm = [products.get("ONEHASH_CRM",{}).get("prices", {}).get("monthly",{})['price_id'],products.get("ONEHASH_CRM",{}).get("prices", {}).get("yearly",{})['price_id']]
        price_ids_erp = [products.get("ONEHASH_ERP",{}).get("prices", {}).get("monthly",{})['price_id'],products.get("ONEHASH_ERP",{}).get("prices", {}).get("yearly",{})['price_id']]
        products_list.extend([
            {
                "product": product_id_crm,
                "prices": price_ids_crm
            },
            {
                "product": product_id_erp,
                "prices": price_ids_erp
            }
        ])
    else:
        products = frappe.conf.get("stripe_prices",{}).get("US", {}).get("products",{})
        product_id_crm = products.get("ONEHASH_CRM",{})['product_id']
        product_id_erp = products.get("ONEHASH_ERP",{})['product_id']
        price_ids_crm = [products.get("ONEHASH_CRM",{}).get("prices", {}).get("monthly",{})['price_id'],products.get("ONEHASH_CRM",{}).get("prices", {}).get("yearly",{})['price_id']]
        price_ids_erp = [products.get("ONEHASH_ERP",{}).get("prices", {}).get("monthly",{})['price_id'],products.get("ONEHASH_ERP",{}).get("prices", {}).get("yearly",{})['price_id']]
        products_list.extend([
            {
                "product": product_id_crm,
                "prices": price_ids_crm
            },
            {
                "product": product_id_erp,
                "prices": price_ids_erp
            }
        ])
    return products_list

@frappe.whitelist()
def create_billing_portal_session(customer_id, return_url):
    country = frappe.conf.country
    stripe.api_version = frappe.conf.stripe_api_version
    if country == 'IN':
        stripe.api_key = frappe.conf.stripe_secret_key_in
    else:
        stripe.api_key = frappe.conf.stripe_secret_key

    try:
        configuration = stripe.billing_portal.Configuration.create(
            business_profile={
                "headline": "OneHash, Inc. partners with Stripe for simplified billing"
            },
            features={
                "subscription_update": {
                    "default_allowed_updates": ["price", "promotion_code"],
                    "enabled": True,
                    "proration_behavior": "always_invoice",
                    "products": get_products(country)
                },
                "customer_update": {
                    "enabled": True,
                    "allowed_updates": ["name", "email", "address"]
                },
                "payment_method_update": {
                    "enabled": True
                },
                "subscription_cancel": {
                    "enabled": True,
                    "mode": "at_period_end",
                    'cancellation_reason': {
                        "enabled": True,
                        "options": ["too_expensive", "missing_features", "switched_service", "unused", "other"]
                    }
                },
                "subscription_pause": {
                    "enabled": False
                },
                "invoice_history": {
                    "enabled": True
                }
            }
        )
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
            configuration= configuration.id
        )
        return {"url": session.url}
    except Exception as e:
        frappe.throw(_(f"Unable to create a billing portal session: {e})"))

@frappe.whitelist()
def payment_method_present(customer_id):
    country = frappe.conf.country
    stripe.api_version = frappe.conf.stripe_api_version
    if country == 'IN':
        stripe.api_key = frappe.conf.stripe_secret_key_in
    else:
        stripe.api_key = frappe.conf.stripe_secret_key

    data = stripe.Customer.list_payment_methods(
        customer=customer_id,
        limit=3,
    )
    if data["data"]:
        return True
    else:
        return False
    
@frappe.whitelist()
def calculate_proration(customer_id, subscription_id, quantity):
    country = frappe.conf.country
    stripe.api_version = frappe.conf.stripe_api_version
    if country == 'IN':
        stripe.api_key = frappe.conf.stripe_secret_key_in
    else:
        stripe.api_key = frappe.conf.stripe_secret_key

    subscription = stripe.Subscription.retrieve(subscription_id)
    unit_price = subscription['items']['data'][0]['price']['unit_amount']/100
    currency = subscription['items']['data'][0]['price']['currency']
    interval = subscription['items']['data'][0]['price']['recurring']['interval']
    next_billing_start_date = datetime.datetime.utcfromtimestamp(subscription['current_period_end']).strftime('%d %B %Y')

    if currency == 'usd':
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    elif currency == 'inr':
        locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')
    else:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

    formatted_unit_price = locale.currency(unit_price, grouping=True)
    subscription_amount = unit_price * int(quantity)
    formatted_subscription_amount = locale.currency(subscription_amount, grouping=True)

    items=[{
        'id': subscription['items']['data'][0].id,
        'price': subscription['items']['data'][0]['price']['id'],
        'quantity': quantity
    }]

    invoice = stripe.Invoice.upcoming(
        customer=customer_id,
        subscription=subscription_id,
        subscription_details={"items": items, "proration_behavior": "always_invoice"}
    )
    formatted_amount_due = locale.currency(invoice['amount_due'] / 100, grouping=True)
    return {
        'plan_name': frappe.conf.plan_name.replace('_', ' '),
        'quantity': quantity,
        'unit_price': formatted_unit_price,
        'interval': interval,
        'subscription_amount': formatted_subscription_amount,
        'next_billing_start_date': next_billing_start_date,
        'amount_due_today': formatted_amount_due,
    }

@frappe.whitelist()
def update_subscription_quantity(subscription_id, quantity):
    country = frappe.conf.country
    stripe.api_version = frappe.conf.stripe_api_version
    if country == 'IN':
        stripe.api_key = frappe.conf.stripe_secret_key_in
    else:
        stripe.api_key = frappe.conf.stripe_secret_key

    subscription = stripe.Subscription.retrieve(subscription_id)
    items=[{
        'id': subscription['items']['data'][0].id,
        'price': subscription['items']['data'][0]['price']['id'],
        'quantity': quantity
    }]
    return stripe.Subscription.modify(
        subscription_id,
        items=items,
        proration_behavior="always_invoice"
    )

class StripeSubscriptionManager:
    def __init__(self, country=""):
        self.region = country or frappe.conf.get("country", "US")
        if self.region == "IN":
            self.api_key = frappe.conf.stripe_secret_key_in
            self.endpoint_secret = frappe.conf.stripe_endpoint_secret_in
            self.trial_price_id = frappe.conf.get("stripe_prices",{}).get("IN", {}).get("products",{}).get("ONEHASH_ERP", {}).get("prices", {}).get("monthly", {})['price_id']
        else:
            self.api_key = frappe.conf.stripe_secret_key 
            self.endpoint_secret = frappe.conf.stripe_endpoint_secret
            self.trial_price_id = frappe.conf.get("stripe_prices",{}).get("US", {}).get("products",{}).get("ONEHASH_ERP", {}).get("prices", {}).get("monthly", {})['price_id']
        stripe.api_key = self.api_key
        stripe.api_version = frappe.conf.stripe_api_version

    def create_customer(self, site_name, email, fname, lname):
        return stripe.Customer.create(
            email=email,
            name=f"{fname} {lname}",
            metadata={"site_name": site_name},
        )

    def create_subscription(self, customer_id, country, site_name):
        quantity = 15 if country == "IN" else 10
        return stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": self.trial_price_id, "quantity": quantity}],
            payment_settings={"save_default_payment_method": "on_subscription"},
            metadata={"site_name": site_name},
            trial_settings={"end_behavior": {"missing_payment_method": "pause"}},
            trial_period_days=30,
        )
