import frappe
from clientside.stripe import StripeSubscriptionManager
def get_context(context):
   
    stripe_subscription_manager = StripeSubscriptionManager()
    print("customer id",frappe.conf.customer_id)
    onehash_sub = stripe_subscription_manager.get_onehash_subscription(frappe.conf.customer_id)
  #  print("onehash_sub",onehash_sub)
    if onehash_sub == "NONE":
        isTrial = False
        current_product = "prod_OF3nxfb3JpKeR"
        current_price="NONE"
    else :
        current_product = stripe_subscription_manager.get_current_onehash_product(frappe.conf.customer_id)
        isTrial = onehash_sub["status"] == "trialing"
        current_price = stripe_subscription_manager.get_current_onehash_price(frappe.conf.customer_id)
        print(onehash_sub["plan"]["product"])
        current_product = stripe_subscription_manager.plan_id_to_product()[onehash_sub["plan"]["product"]]
        
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