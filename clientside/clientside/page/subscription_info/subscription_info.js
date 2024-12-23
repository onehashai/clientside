frappe.pages['subscription-info'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Subscription Info',
		single_column: true
	});

	$(frappe.render_template("subscription_info")).appendTo(page.body.addClass("no-border"));
}

function open_customer_portal() {
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

function manage_licenses() {
	const customer_id = document.getElementById('manage-licenses').dataset.customerId;
	const subscription_id = document.getElementById('manage-licenses').dataset.subscriptionId;
	frappe.call({
		method: "clientside.stripe.payment_method_present",
		args: {
			customer_id: customer_id
		},
		callback: function (r) {
			if (r.message){
				let licenses
				frappe.call({
					method: "clientside.clientside.page.subscription_info.subscription_info.licenses",
					callback: function (r) {
						licenses = r.message.licenses;
						let dialog = new frappe.ui.Dialog({
							title: 'Manage Licenses',
							fields: [
								{
									label:"Licenses",
									fieldname: "licenses",
									fieldtype: "Data",
									default: licenses,
									reqd: 1,
									onchange: function () {
										if (this.value < r.message.license_limit){
											dialog.set_df_property(
												"licenses",
												"description",
												`Your account can't have fewer than ${r.message.license_limit} licenses. If you need any assistance, please email <b>support@onehash.ai</b>`
											);
											dialog.set_df_property("proration", "options","<p></p>");
										} else if (this.value == r.message.licenses) {
											dialog.set_df_property("licenses","description","");
											dialog.set_df_property("proration", "options","<p></p>");
										} else {
											dialog.set_df_property(
												"licenses",
												"description",
												""
											);
											frappe.call({
												method: "clientside.stripe.calculate_proration",
												args: {
													customer_id: customer_id,
													subscription_id: subscription_id,
													quantity: this.value
												},
												callback: function (r) {
													let options = `<table class="table"">
																		<tr>
																			<td class="flex-row">
																				<div class="left">
																					<span><strong>${r.message.plan_name}</strong>(x${r.message.quantity})</span><br>
																					<span class="small-text">${r.message.unit_price} each per ${r.message.interval}</span>
																				</div>
																				<div class="right">
																					<span>${r.message.subscription_amount}</span>
																				</div>
																			</td>
																			<td class="flex-row">
																				<div class="left">
																					<span>What you'll pay starting</span><br>
																					<span class="small-text">${r.message.next_billing_start_date}</span>
																				</div>
																				<div class="right">
																					<span>${r.message.subscription_amount}</span>
																				</div>
																			</td>
																			<td class="flex-row">
																				<div class="left">
																					<span>Amount due today</span><br>
																				</div>
																				<div class="right">
																					<span><strong>${r.message.amount_due_today}</strong></span>
																				</div>
																			</td>
																		</tr>
																	</table>`;
													dialog.set_df_property("proration", "options", options);
												}
											})
										}
									}
								},
								{
									fieldtype: "HTML",
									fieldname: "proration",
									options: "",
									read_only: 1,
								}
							],
							size: 'small',
							primary_action_label: 'Submit',
							primary_action(values) {
								console.log(values);
								if (values.licenses < r.message.license_limit){
									frappe.msgprint({
										title: __("Error"),
										message: __(`Your account can't have fewer than ${r.message.license_limit} licenses. If you need any assistance, please email <b>support@onehash.ai</b>`),
										indicator: "red",
									});
								} else if(values.licenses == r.message.licenses){
									frappe.msgprint({
										title: __("Notification"),
										message: __('The quantity of licenses stays the same.'),
										indicator: "green",
									});
								} else{
									frappe.confirm('Are you sure you want to proceed?',
										() => {
											frappe.call({
												method: "clientside.stripe.update_subscription_quantity",
												args: {
													subscription_id: subscription_id,
													quantity: values.licenses
												},
												callback: function (r) {
													frappe.show_alert({
														message:__('Thank you. The number of licenses on your account has been updated and the modifications will take effect shortly.'),
														indicator:'green'
													});
												}
											})
										}, () => {
											// action to perform if No is selected
										})
								}
								dialog.hide();
							}
						})
						dialog.show();
					},
				})
			} else{ 
				frappe.msgprint({
					title: __("Error"),
					message: __("No Payment method found. To add a payment method, please visit the <b><a onclick='open_customer_portal()'>Billing Portal</a></b>."),
					indicator: "red",
				});
			}
		}
	})
}


function contact_us() {
	window.location.href = "mailto:support@onehash.ai";
}

function delete_site() {
	frappe.confirm(__("This will delete your site permanently. Are you sure you want to proceed?"), function() {
		frappe.call({
			method: "clientside.clientside.page.subscription_info.subscription_info.delete_site",
			callback: function (r) {
			},
		});
	})
}