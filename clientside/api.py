import frappe


def update_workspaces():
    onehash_workspaces = frappe.get_all(
        "Workspace",
        filters={"name": ("in", ["OneHash Integrations", "OneHash Settings"])},
        fields=[
            "name",
            "title",
            "icon",
            "indicator_color",
            "parent_page as parent",
            "public",
        ],
    )

    erpnext_workspaces = frappe.get_all(
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

    if onehash_workspaces and erpnext_workspaces:
        for workspace in erpnext_workspaces:
            frappe.delete_doc("Workspace", workspace["name"], force=True)
            frappe.db.commit()

    update_workspace_shortcuts()


def update_workspace_shortcuts():
    workspace_shortcuts = frappe.get_all(
        "Workspace Shortcut", fields=["name", "label", "url"]
    )

    workspace_shortcuts_to_remove = []
    for shortcut in workspace_shortcuts:
        if shortcut["url"] and (
            shortcut["url"].startswith("https://frappe")
            or shortcut["url"].startswith("https://erpnext")
        ):
            workspace_shortcuts_to_remove.append(shortcut)
        elif shortcut["label"] == "Browse Apps":
            workspace_shortcuts_to_remove.append(shortcut)

    if workspace_shortcuts_to_remove:
        for shortcut in workspace_shortcuts_to_remove:
            frappe.delete_doc("Workspace Shortcut", shortcut["name"])
            frappe.db.commit()
    else:
        print("No workspace shortcut to update.")


def disable_legacy_backup_jobs():
    """Stop obsolete custom and off-site backup jobs on tenant sites."""
    patterns = (
        "%onehash_backups%",
        "%s3_backup_settings%",
        "%google_drive%backup%",
        "%dropbox_settings%backup%",
    )
    conditions = " OR ".join(["method LIKE %s"] * len(patterns))
    frappe.db.sql(
        f"UPDATE `tabScheduled Job Type` SET stopped = 1 WHERE {conditions}",  # nosec B608
        patterns,
    )
