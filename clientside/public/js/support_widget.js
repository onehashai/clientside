frappe.ready(() => {
  const baseUrl = frappe.boot.chat_widget_base_url;
  const token = frappe.boot.chat_widget_token;
  if (!token || !baseUrl) return;

  (function(d, t) {
    var BASE_URL = baseUrl;
    var g = d.createElement(t), s = d.getElementsByTagName(t)[0];
    g.src = BASE_URL + "/packs/js/sdk.js";
    g.defer = true;
    g.async = true;
    s.parentNode.insertBefore(g, s);
    g.onload = function() {
      window.chatwootSDK.run({
        websiteToken: token,
        baseUrl: BASE_URL
      });
    };
  })(document, "script");
});