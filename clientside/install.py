import frappe
from frappe.utils import strip_html
from frappe.utils.html_utils import unescape_html
from frappe.desk.doctype.workspace.workspace import update_page


def after_install():
    create_role("OneHash Manager")
    update_workspace_title()
    hide_integrations()
    update_navbar_settings()
    add_custom_fields_to_communication()
    add_custom_fields_to_email_campaign()
    update_notification_channels()


def create_role(role_name):
    role = frappe.get_doc(
        {
            "doctype": "Role",
            "role_name": role_name,
            "desk_access": 1,
        }
    )
    role.insert(ignore_permissions=True)
    frappe.db.commit()
    return role.name


def update_workspace_title():
    workspaces_to_update = frappe.get_all(
        "Workspace",
        filters={"name": ("in", ["ERPNext Integrations", "ERPNext Settings"])},
        fields=[
            "name",
            "title",
            "icon",
            "indicator_color",
            "parent_page as parent",
            "public",
        ],
    )
    for workspace in workspaces_to_update:
        title = strip_html(unescape_html(workspace.title))
        updated_title = title.replace("ERPNext", "OneHash")
        if title == updated_title:
            continue

        workspace.title = updated_title
        try:
            update_page(**workspace)
            frappe.db.commit()

        except Exception:
            frappe.db.rollback()


def hide_integrations():
    workspaces_to_update = frappe.get_all(
        "Workspace",
        filters={"name": "Integrations"},
        fields=["name", "is_hidden"],
    )
    if workspaces_to_update:
        workspace = workspaces_to_update[0]
        if workspace["is_hidden"] == 0:
            frappe.db.set_value("Workspace", workspace["name"], "is_hidden", 1)
            frappe.db.commit()
        else:
            print(f"Workspace '{workspace['name']}' is already hidden.")
    else:
        print("Workspace 'Integrations' not found.")


def update_navbar_settings():
    navbar_settings = frappe.get_single("Navbar Settings")

    for navbar_item in navbar_settings.settings_dropdown[3:]:
        navbar_item.idx = navbar_item.idx + 2

    navbar_settings.append(
        "settings_dropdown",
        {
            "item_label": "Subscription Info",
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

    label = frappe.get_all("Navbar Item", filters={"item_label": "Apps"}, fields=["*"])
    if label:
        frappe.db.set_value("Navbar Item", label[0]["name"], "hidden", 1)
        frappe.db.commit()


def add_custom_fields_to_communication():
    custom_fields = [
        {
            "label": "Email Insights",
            "fieldname": "email_insights",
            "fieldtype": "Tab Break",
            "insert_after": "feedback_request",
        },
        {
            "label": "Overview",
            "fieldname": "overview",
            "fieldtype": "Section Break",
            "insert_after": "email_insights",
        },
        {
            "label": "All Emails",
            "fieldname": "all_emails",
            "fieldtype": "Table",
            "insert_after": "overview",
            "options": "Email Insights",
        },
    ]

    for field in custom_fields:
        if not frappe.db.exists(
            "Custom Field", {"dt": "Communication", "fieldname": field["fieldname"]}
        ):
            new_field = frappe.get_doc(
                {"doctype": "Custom Field", "dt": "Communication", **field}
            )
            new_field.insert()
            frappe.db.commit()


def add_custom_fields_to_email_campaign():
    custom_fields = [
        {
            "label": "Email Insights",
            "fieldname": "email_insights",
            "fieldtype": "Tab Break",
            "insert_after": "status",
        },
        {
            "label": "Overview",
            "fieldname": "overview",
            "fieldtype": "Section Break",
            "insert_after": "email_insights",
        },
        {
            "label": "All Emails",
            "fieldname": "all_emails",
            "fieldtype": "Table",
            "insert_after": "overview",
            "options": "Email Insights",
        },
    ]

    for field in custom_fields:
        if not frappe.db.exists(
            "Custom Field", {"dt": "Email Campaign", "fieldname": field["fieldname"]}
        ):
            new_field = frappe.get_doc(
                {"doctype": "Custom Field", "dt": "Email Campaign", **field}
            )
            new_field.insert()
            frappe.db.commit()


def update_notification_channels():
    field = frappe.db.get_list(
        "DocField", ["*"], {"parent": "Notification", "fieldname": "channel"}
    )[0]
    options = (field.options or "").split("\n")
    if "WhatsApp" not in options:
        options.append("WhatsApp")
        frappe.db.set_value("DocField", field.name, "options", "\n".join(options))
        frappe.db.commit()


def add_custom_fields_to_notification():
    custom_fields = [
        {
            "depends_on": 'eval:doc.channel=="WhatsApp"',
            "fieldname": "custom_whatsapp_app",
            "fieldtype": "Select",
            "insert_after": "channel",
            "label": "WhatsApp App",
            "mandatory_depends_on": 'eval:doc.channel=="WhatsApp"',
            "module": "Clientside",
            "options": "",
        }
    ]
    for field in custom_fields:
        if not frappe.db.exists(
            "Custom Field", {"dt": "Notification", "fieldname": field["fieldname"]}
        ):
            new_field = frappe.get_doc(
                {"doctype": "Custom Field", "dt": "Notification", **field}
            )
            new_field.insert()
            frappe.db.commit()
