$(document).ready(function () {
  const baseUrl = frappe.boot.chat_widget_base_url;
  const token = frappe.boot.chat_widget_token;
  const disabled = frappe.boot.chat_widget_disabled;
  if (!token || !baseUrl) return;
  if (disabled) return;

  window.$crisp = [];
  window.CRISP_WEBSITE_ID = token;
  (function (d) {
    s = d.createElement("script");
    s.src = baseUrl;
    s.async = 1;
    d.getElementsByTagName("head")[0].appendChild(s);
  })(document);
});
