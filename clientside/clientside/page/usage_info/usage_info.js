frappe.pages['usage-info'].on_page_load = async function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Usage Info',
		single_column: true
	});
	$(frappe.render_template("usage_info")).appendTo(
		page.body.addClass("no-border")
	  );
	$("#loading").show();
	$("#content").hide();
	const res = await fetch("/api/method/clientside.clientside.utils.get_usage");
	const { message } = await res.json();
	console.log(message);
	$("#loading").hide();
	$("#content").show();
	init(message);
}