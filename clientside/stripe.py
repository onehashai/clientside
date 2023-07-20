import stripe
import frappe
import datetime
# price IDS
@frappe.whitelist(allow_guest=True)
def hasActiveSubscription(*args,**kwargs):
    print("checking whether has active subscription")
    print(kwargs)
    invalidate_cache = True if "invalidate_cache" in kwargs else False
    site = kwargs.get("site",frappe.local.site)
    print("hasAc",site)
    frappe.utils.execute_in_shell("bench --site {} clear-cache".format(site))
    frappe.utils.execute_in_shell("bench --site {} clear-website-cache".format(site))
    country = frappe.get_site_config(site_path=site)["country"]
    customer_id = frappe.get_site_config(site_path=site)["customer_id"]
    print("country",country)
    stripe_manager = StripeSubscriptionManager(country=country)
    
    if invalidate_cache or (not frappe.conf.has_subscription):
        print("rechecking subscription")
        hasSubscription = "yes" if   stripe_manager.has_valid_site_subscription(customer_id)  else "no"
        print("hasSubscription",hasSubscription)
        command = "bench --site {} set-config has_subscription {}".format(site,hasSubscription)
        print("command",command)
        frappe.utils.execute_in_shell(command)
    return True if frappe.conf.has_subscription == "yes" else False
    
def get_room(customer_id):    
    try:
        print("customer_id",customer_id)
        site = frappe.db.get_list('SaaS sites', filters={'cus_id': customer_id},fields=["site_name"],ignore_permissions=True)[0]["site_name"]
        return f"{site}:website"
    except Exception as e:
        print("error",e)
def get_site(customer_id):
    print("getting site")
    return frappe.db.get_list('SaaS sites', filters={'cus_id': customer_id},fields=["site_name"],ignore_permissions=True)[0]["site_name"]

class StripeSubscriptionManager():
    def __init__(self,country=""):
        self.api_key = frappe.conf.STRIPE_SECRET_KEY
        self.endpoint_secret = frappe.conf.STRIPE_ENDPOINT_SECRET
        print("we have",country)
        if country:
            self.region = country
        else:
            self.region = frappe.conf.country or "US"
        print("region",self.region)
        if(self.region == "IN"):
            print("setting stripe key to IN")
            self.api_key = frappe.conf.STRIPE_SECRET_KEY_IN
            
            self.endpoint_secret = frappe.conf.STRIPE_ENDPOINT_SECRET_IN
        self.plan_to_product_id = frappe.conf.stripe_prices["US"]["products"]
        self.onehas_subscription_product_ids = ["prod_OE6JgL1X5whRBm","prod_ODy9z0LH7AwXD6","prod_OF3nxhfb3JpKeR"]
        self.trial_price_id = frappe.conf.stripe_prices["US"]["trial_price_id"]
        self.trial_product = "ONEHASH_PRO"

        if(self.region == "IN"):
            self.plan_to_product_id = frappe.conf.stripe_prices["IN"]["products"]
            self.trial_price_id = frappe.conf.stripe_prices["IN"]["trial_price_id"]
        self.onehas_subscription_product_ids = [x for x in self.plan_to_product_id.values()]
        stripe.api_key = self.api_key
        print("setting stripe api key",stripe.api_key)
    def getSession(self,session_id,expand=[]):
        return stripe.checkout.Session.retrieve(session_id,expand=expand)
    def create_customer(self, site_name,email,fname,lname,phone):
        return stripe.Customer.create(email=email,metadata={"full name": fname + " " + lname},name = site_name,phone = phone)
    def get_current_onehash_price(self,customer_id):
        subscription = self.get_onehash_subscription(frappe.conf.customer_id)
        print(subscription)
        return subscription["plan"]["id"]
    def end_trial(self,customer_id):
        # cancel the subcription of customer which is on trial
        print(self.api_key)
        # print all customers
        alls = stripe.Customer.list()
        # print customer ids 
        for customer in alls:
            print(customer["id"])
        subscriptions = stripe.Subscription.list(customer=customer_id)
        for subscription in subscriptions:
            if subscription["status"] == "trialing":
                stripe.Subscription.delete(subscription["id"])
    def start_free_trial_of_site(self,customer_id):
        return stripe.Subscription.create(customer=customer_id,items=[{"price": self.trial_price_id}],payment_settings={"save_default_payment_method": "on_subscription"},trial_settings={"end_behavior": {"missing_payment_method": "pause"}},metadata={"plan":"ONEHASH_PRO"},trial_period_days=14)
    def has_valid_site_subscription(self,cus_id):

        return self.get_onehash_subscription(cus_id) != "NONE"
    def create_new_purchase_session(self,customer_id,price_id,subdomain):
        success_url = "http://" + subdomain + "."+(frappe.conf.domain if frappe.conf.domain !="localhost" else frappe.conf.domain+":8000") +"/plans?payment_success=True"
        session = stripe.checkout.Session.create(
            success_url=success_url,
            mode="subscription",
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                    
                }],
            client_reference_id = subdomain,
            customer = customer_id,
            metadata={"del_trial":True},
        )
        return session.url

    
   # def create_checkout_session(self,customer_id,plan,success_url,cancel_url):
    def get_customer_details(self,customer_id):
        customer = stripe.Customer.retrieve(customer_id,expand=["subscriptions"])
        return customer
    def get_current_onehash_product_id(self,customer_id):
        customer = self.get_customer_details(customer_id)
        product_id = None
        for subscription in customer["subscriptions"]["data"]:
            if subscription["status"] in ["active","trialing"] and subscription["plan"]["product"] and subscription["plan"]["product"] in self.onehas_subscription_product_ids:
                product_id = subscription["plan"]["product"]
                break
        return product_id
    def get_current_onehash_product(self,customer_id):
        subscriptions = stripe.Subscription.list(customer=customer_id)
        product = None
        for subscription in subscriptions["data"]:
            print(subscription["status"],subscription["id"])
            if subscription["status"] in ["active","trialing"] and subscription["plan"]["product"] and subscription["plan"]["product"] in self.onehas_subscription_product_ids:
                product = subscription["plan"]["product"]
                break
        return stripe.Product.retrieve(product)
    def hadle_subscription_deleted(self,event):
        hasActiveSubscription(invalidate_cache=True,site=get_site(event["data"]["object"]["customer"]))
    def has_valid_subscription_v2(self,customer_id,plan):
        # if plan == "ONEHASH" 
        # check if the customer has any product in subscription which product id starts with ONEHASH
        # if yes then return true else false
        if not customer_id:
            return False
        customer = self.get_customer_details(customer_id)
        if "subscriptions" not in customer:
            return False
        if plan == "ONEHASH":
            for subscription in customer["subscriptions"]["data"]:
                if subscription["status"] in ["active","trialing"] and subscription["plan"]["product"] and subscription["plan"]["product"] in self.onehas_subscription_product_ids:
                    return True
            return False
        else :
            for subscription in customer["subscriptions"]["data"]:
                if subscription["status"] in ["active","trialing"] and subscription["plan"]["product"] and subscription["plan"]["product"] == self.plan_to_product_id[plan]:
                    return True
            return False
    def get_onehash_subscription(self,customer_id):
        if not customer_id:
            return "NONE"
        subscriptions = stripe.Subscription.list(customer=customer_id)
        for subscription in subscriptions["data"]:
            if subscription["status"] in ["active","trialing"] and subscription["plan"]["product"] and subscription["plan"]["product"] in self.onehas_subscription_product_ids:
                return subscription
        return "NONE"
    def cancel_onehash_subscription(self,customer_id):
        current_sub = self.get_onehash_subscription(customer_id)
        if current_sub != "NONE":
            stripe.Subscription.delete(current_sub["id"])
        
    def upgrade_subscription(self,customer_id,new_price_id,subdomain):
        # this will upgrade the subscription to new price id and try to charge the customer immediately
        subscription = self.get_onehash_subscription(customer_id)
        # check is customer has any pending invoice if yes then return "PENDING_INVOICE"
        # check is customer has any pending update if yes then return "PENDING_UPDATE"
        # check is customer has any unpaid invoice if yes then return "UNPAID_INVOICE"
        # check is customer has no payment method if yes then return "NO_PAYMENT_METHOD"
        customer = self.get_customer_details(customer_id)
        invoices = stripe.Invoice.list(customer=customer_id)
        for invoice in invoices['data']:
            if invoice["status"] != "paid" and invoice["status"] != "void":
                return "PENDING_INVOICE"
        customer_payment_methods = stripe.PaymentMethod.list(customer=customer_id,type="card")
        
        if  len(customer_payment_methods["data"]) == 0 :
            return "NO_PAYMENT_METHOD"
        # remove any pending update
        if  customer["subscriptions"]["data"][0]["pending_update"] :
            return "PENDING_UPDATE"
       
        try:
            print("updating subscription..")
            response = stripe.Subscription.modify(
                    subscription.id,
                    payment_behavior='pending_if_incomplete',
                    proration_behavior='always_invoice',
                    items=[{
                        'id': subscription['items']['data'][0].id,
                        'price': new_price_id,
                    }],
                   
                    )
            
        except Exception as e:
            print(e)
            return "TECHNICAL_ERROR"
       # print("response",response)
        if("pending_update" in response and response["pending_update"] ):
            # error in payment
            print("there are updates pending,might require payment action")
            return "PENDING_UPDATE"
           
        else :
            # success
            return "SUCCESS"
    def handle_payment_intent_failed(self,event):
        customer_id = event["data"]["object"]["customer"]
        hasActiveSubscription(invalidate_cache=True,site=get_site(event["data"]["object"]["customer"]))
        print("payment failed")
        frappe.publish_realtime("payment_failed",room=get_room(customer_id))
    def handle_payment_intent_action_required(self,event):
        print(self.region,self.api_key)
     #   payment_intent_id = "pi_1NUkv1CwmuPVDwVySsT5gUDX"
        payment_intent_id = event["data"]["object"]["payment_intent"]
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        client_secret = payment_intent["client_secret"]
        frappe.publish_realtime("requires_payment_action",message={"client_secret":client_secret},room=get_room(event["data"]["object"]["customer"]))
            # after 3 minute check if payment is done , if not dome then void this transaction
        from threading import Timer
        invoice_id = event["data"]["object"]["id"]
        def void_payment(invoice_id):
            print("voidng invoice")
            payment_intent = stripe.PaymentIntent.retrieve(invoice_id)
            if payment_intent["status"] == "requires_payment_action":
                stripe.Invoice.void_invoice(invoice_id)
        t = Timer(30*60, void_payment,(invoice_id))
        t.start()    
    def handle_subscription_updated(self,event):
        hasActiveSubscription(invalidate_cache=True,site=get_site(event["data"]["object"]["customer"]))
    def handle_checkout_session_completed(self,event):
        session_metadata = event["data"]["object"]["metadata"]
        customer_id  = event["data"]["object"]["customer"]
        print("session metadata",self.api_key)
        print("api key",stripe.api_key)
        print("checkout session completed")
        print("for customer",customer_id)
        if "del_trial" in session_metadata and session_metadata["del_trial"] == "True":
            print("ending trial")
            self.end_trial(customer_id)
    def get_product(self,product_id):
        return stripe.Product.retrieve(product_id)
    def handle_invoice_failed(self,event):
        hasActiveSubscription(invalidate_cache=True,site=get_site(event["data"]["object"]["customer"]))
    def handle_invoice_paid(self,event):
        customer_id = event["data"]["object"]["customer"]
        sub_id = event["data"]["object"]["subscription"]
        subscription = stripe.Subscription.retrieve(sub_id,expand=["latest_invoice"])
        product_id = subscription["items"]["data"][0]["price"]["product"]
        price_id = subscription["items"]["data"][0]["price"]["id"]
        # invoice paid
        print("INVOICE PAID>>>>>>")
        if product_id in self.onehas_subscription_product_ids :
            site_name = frappe.get_list("SaaS sites",filters={"cus_id":customer_id},fields=["site_name"],ignore_permissions=True)[0]["site_name"]
            
            if price_id != frappe.conf.price_id :
                # end tria
                # fetch the site_name from the database - saved payment intent id
                print("updating onehash subscription for site",site_name)
                fulfilOneHashUpdate(self.onehas_subscription_product_ids,product_id,price_id,site_name)
                # call payment success on that site
            command = "bench --site {} set-config has_subscription {}".format(site_name,"yes")
            frappe.utils.execute_in_shell(command)
            print("payment success")
            frappe.publish_realtime("payment_success",room=get_room(customer_id))
            
    
        

def test2():
    hasActiveSubscription(invalidate_cache=True,site="dlwkef.localhost")
    
    
def fulfilOneHashUpdate(pids,product_id,price_id,site_name):
    # pass the checkout session 
    if product_id in pids:
            # handle onehash subscription
        product = stripe.Product.retrieve(product_id)
        user_limit = 10
        plan_name = ""
        if product.name == "OneHash Pro":
                user_limit = 100000
                plan_name = "ONEHASH_PRO"   
        elif product.name == "OneHash Starter":
                user_limit = 10
                plan_name = "ONEHASH_STARTER"
        else :
                user_limit = 30
                plan_name = "ONEHASH_PLUS"
        command_to_set_limit = "bench --site {site_name} set-config  max_users {user_limit}".format(site_name=site_name,user_limit=user_limit)
        command_to_set_plan = "bench --site {site_name} set-config  plan {plan}".format(site_name=site_name,plan=plan_name)
        command_to_set_price_id = "bench --site {site_name} set-config  price_id {price_id}".format(site_name=site_name,price_id=price_id)
        frappe.utils.execute_in_shell(command_to_set_limit)
        frappe.utils.execute_in_shell(command_to_set_plan)
        frappe.utils.execute_in_shell(command_to_set_price_id)
        
# unit testing to do.

    
# test if new signups are being made - site has a trial subscription and  correspnding user limits are being setpayment_intent = stripe.PaymentIntent.retrieve(payment_intent_id) 