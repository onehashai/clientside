frappe.pages["usage-info"].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Usage Info"),
    single_column: true,
  });
  $(frappe.render_template("usage_info")).appendTo(
    page.body.addClass("no-border")
  );
  $("head").append(
    '<link rel="stylesheet" href="/assets/clientside/css/loading-bar.min.css" type="text/css" />'
  );
  $("head").append(
    '<link rel="stylesheet" href="/assets/clientside/css/usage_info.css" type="text/css" />'
  );
  $("head").append(
    '<script src="/assets/clientside/css/loading-bar.min.js"></script>'
  );
};
