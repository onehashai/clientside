import json
import frappe
@frappe.whitelist()
def create_new_user(*args, **kwargs):
    email = kwargs["email"] 
    password = kwargs["password"]
    firstname = kwargs["firstname"]
    lastname = kwargs["lastname"]
    print(email,password,firstname,lastname)
    user = frappe.db.get("User", {"email": email})
    if user:
        if user.enabled:
            return 0, "Already Registered"
        else:
            return 0,"Registered but disabled"
    user = frappe.get_doc({
        "doctype": "User",
        "first_name": firstname,
        "last_name":lastname,
        "email": email,
        "send_welcome_email":0,
        "new_password":password,
        "enabled":1
        
    })
    user.flags.ignore_permissions = True
    user.flags.ignore_password_policy = True
    user.insert()
    adminUser = frappe.get_doc("User","Administrator")
    roles_to_add = []
    for role in adminUser.roles:
        print(role.role)
        roles_to_add.append(role.role)
    user.add_roles(*roles_to_add)
    return "User Created Successfully"
    