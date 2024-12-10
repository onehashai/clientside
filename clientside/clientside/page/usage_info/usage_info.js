frappe.pages['usage-info'].on_page_load = async function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Usage Info',
		single_column: true
	});

	$(frappe.render_template("usage_info")).appendTo(page.body.addClass("no-border"));
}

async function open_customer_portal() {
	const customer_id = document.getElementById('customer-portal').dataset.customerId;
	const return_url = window.location.href; 

	frappe.call({
		method: "clientside.stripe.create_billing_portal_session",
		args: {
		  customer_id: customer_id,
		  return_url: return_url,
		},
		callback: function (response) {
		  if (response.message && response.message.url) {
			window.open(response.message.url, "_blank", "noopener,noreferrer");
		  } else {
			frappe.msgprint({
			  title: __("Error"),
			  message: __("Failed to create billing portal session."),
			  indicator: "red",
			});
		  }
		},
		error: function (err) {
		  frappe.msgprint({
			title: __("Error"),
			message: __("An error occurred while opening the billing portal."),
			indicator: "red",
		  });
		},
	  });
}