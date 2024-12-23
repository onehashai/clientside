import frappe
from frappe.desk.doctype.workspace.workspace import update_page

def after_install():
    create_role("OneHash Manager")
    change_erp_to_onehash()
    update_navbar_settings()

def create_role(role_name):
    role = frappe.get_doc(
        {
            "doctype": "Role",
            "role_name": role_name,
            "desk_access": 1,
        }
    )
    role.insert(ignore_permissions=True)
    return role.name

def change_erp_to_onehash():
    try:
        update_page("ERPNext Settings", "OneHash Settings", "setting", "" , "", 0)
    except Exception as e:
        print("Error updating ERPNext Settings Page", e)

    try:
        update_page("ERPNext Integrations", "OneHash Integrations", "integration", "", "", 0)
    except Exception as e:
        print("Error updating ERPNext Integrations Page", e)

def update_navbar_settings():
    navbar_settings = frappe.get_single("Navbar Settings")
    
    for navbar_item in navbar_settings.settings_dropdown[3:]:
        navbar_item.idx = navbar_item.idx + 2
          
    navbar_settings.append(
        "settings_dropdown",
        {
            "item_label": "Usage Info",
            "item_type": "Action",
            "action": "frappe.set_route('Form','Subscription Info')",
            "is_standard": 1,
            "idx": 4,
        },
    )
    navbar_settings.append(
        "settings_dropdown",
        {
            "item_label": "Marketplace",
            "item_type": "Action",
            "action": "frappe.set_route('Form','Market Place')",
            "is_standard": 1,
            "idx": 5,
        },
    )
    navbar_settings.save()