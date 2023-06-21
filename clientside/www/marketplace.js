// redirect to login if user is not logged in
window.onload = function () {
  console.log(frappe.is_user_logged_in());
  if (!frappe.is_user_logged_in()) {
    window.location.href = "/login";
  }
};
document.getElementById("installApp").addEventListener("click", installApp);

function installApp() {
  console.log("installing app");
  const to_install = ["India Compliance"];
  frappe.call({
    method: "clientside.clientside.utils.installApps",
    args: {
      site_name: frappe.get_cookie("site_name"),
      apps: to_install,
    },
    callback: function (r) {
      console.log(r);
    },
  });
}
