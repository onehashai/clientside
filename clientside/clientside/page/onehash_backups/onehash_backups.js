frappe.pages["onehash-backups"].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("OneHash backups"),
    single_column: true,
  });

  page.add_inner_button(__("Set Number of Backups"), function () {
    frappe.set_route("Form", "System Settings");
  });

  page.add_inner_button(__("Schedule a backup now"), function () {
    frappe.call({
      method: "clientside.clientside.utils.schedule_files_backup",
      args: { user_email: frappe.session.user_email },
    });
    frappe.msgprint({
      title: __("Backup Scheduled"),
      message: __(
        "Backup scheduled successfully. Please visit this page after some time to view or download the backup."
      ),
      indicator: "green",
    });
  });

  frappe.breadcrumbs.add("Setup");

  $(frappe.render_template("oh_backup")).appendTo(
    page.body.addClass("no-border")
  );
  init();
};

async function init() {
  // working
  const { message } = await fetch(
    "/api/method/clientside.clientside.utils.getBackups"
  ).then((r) => r.json());
  message.forEach((backup) => {
    const backup_card_html = `<div class="frappe-card m-3" style="flex-basis: 342px">
								<div class="card-body">
									<p><strong>Backup Date:</strong> ${new Date(backup.creation).toDateString()}</p>
									<p><strong>Backup Time:</strong> ${backup.time}</p>
									<p><strong>Backup Size:</strong> ${backup.backup_size}M</p>
									<button data-key=${backup.site_files} class="btn btn-primary download"
									>Download Backup</button
									>
								</div>
							</div>`;

    document.getElementById("backup_box").innerHTML += backup_card_html;
  });
  document.querySelectorAll(".download").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      let key = e.target.dataset.key;
      if (!window.dev_server) key = key.replace("onehash/", "");
      const { message } = await fetch(
        `/api/method/clientside.clientside.utils.get_download_link?s3key=${key}`
      ).then((r) => r.json());
      window.open(message, "_blank");
    });
  });
}
