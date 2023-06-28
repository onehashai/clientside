frappe.pages["usage-info"].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Usage Info"),
    single_column: true,
  });
  $(frappe.render_template("usage_info")).appendTo(
    page.body.addClass("no-border")
  );

  var forEach = function (array, callback, scope) {
    for (var i = 0; i < array.length; i++) {
      callback.call(scope, i, array[i]);
    }
  };
  var max = -219.99078369140625;
  forEach(document.querySelectorAll(".iprogress"), function (index, value) {
    console.log(value);
    percent = value.getAttribute("data-progress");
    value
      .querySelector(".fill")
      .setAttribute(
        "style",
        "stroke-dashoffset: " + ((100 - percent) / 100) * max
      );
    value.querySelector(".value").innerHTML = percent + "%";
  });
};
