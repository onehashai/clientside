@frappe.whitelist()
def schedule_files_backup(user_email):
	from frappe.utils.background_jobs import enqueue, get_jobs

	queued_jobs = get_jobs(site=frappe.local.site, queue="long")
	method = "frappe.desk.page.backups.backups.backup_files_and_notify_user"

	if method not in queued_jobs[frappe.local.site]:
		enqueue(
			"frappe.desk.page.backups.backups.backup_files_and_notify_user",
			queue="long",
			user_email=user_email,
		)
		frappe.msgprint(_("Queued for backup. You will receive an email with the download link"))
	else:
		frappe.msgprint(
			_("Backup job is already queued. You will receive an email with the download link")
		)