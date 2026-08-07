frappe.pages["onehash-backups"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Download Backups"),
		single_column: true,
	});

	page.add_inner_button(__("Download Files Backup"), function () {
		frappe.call({
			method: "frappe.desk.page.backups.backups.schedule_files_backup",
			args: { user_email: frappe.session.user_email },
		});
	});

	page.add_inner_button(__("Get Backup Encryption Key"), function () {
		frappe.verify_password(function () {
			frappe.call({
				method: "frappe.utils.backups.get_backup_encryption_key",
				callback: function (r) {
					frappe.msgprint({
						title: __("Backup Encryption Key"),
						message: __(r.message),
						indicator: "blue",
					});
				},
			});
		});
	});

	frappe.breadcrumbs.add("Setup");
	$(frappe.render_template("onehash_backups")).appendTo(page.body.addClass("no-border"));
};
