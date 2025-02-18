import frappe

def clientside_patch():
    onehash_workspaces = frappe.get_all(
		"Workspace",
		filters={"name": ("in", ["OneHash Integrations", "OneHash Settings"])},
		fields=["name", "title", "icon", "indicator_color", "parent_page as parent", "public"],
	)

    erpnext_workspaces = frappe.get_all(
		"Workspace",
		filters={"name": ("in", ["ERPNext Integrations", "ERPNext Settings"])},
		fields=["name", "title", "icon", "indicator_color", "parent_page as parent", "public"],
	)

    if onehash_workspaces and erpnext_workspaces:
        for workspace in erpnext_workspaces:
            frappe.delete_doc("Workspace", workspace["name"], force=True)
            frappe.db.commit()
