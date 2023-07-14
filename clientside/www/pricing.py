import frappe
from whitelabel.api import StripeSubscriptionManager
def get_context(context):
    plan_id_to_product = {
        "prod_OFovQrq6UPfouo":"ONEHASH_PLUS",
        "prod_OFowmBYUz738j9":"ONEHASH_PRO",
        "prod_OFotftDB5owt2r":"ONEHASH_STARTER"
    }
    stripe_subscription_manager = StripeSubscriptionManager()
    onehash_sub = stripe_subscription_manager.get_onehash_subscription(frappe.conf.customer_id)
    if onehash_sub == "NONE":
        isTrial = False
        current_product = "prod_OF3nxfb3JpKeR"
        current_price="NONE"
    else :
        current_product = stripe_subscription_manager.get_current_onehash_product(frappe.conf.customer_id)
        isTrial = onehash_sub["status"] == "trialing"
        current_price = stripe_subscription_manager.get_current_onehash_price(frappe.conf.customer_id)
        
        current_product = plan_id_to_product[onehash_sub["plan"]["product"]]
        
   # print(onehash_sub)
    context.update({
        "subdomain": frappe.local.site.split(".")[0],
        "customer_email": frappe.conf.customer_email,
        "current_product": current_product,
        "isTrial": isTrial,
        "current_price_id": current_price if current_price else "NONE",
        "has_subscription": onehash_sub != "NONE"
    })
    
# scenario 1 : user is on trial and cliks on one of available