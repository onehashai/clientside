frappe.ui.form.on('Notification', {

	refresh: function (frm) {
		frm.events.setup_whatsapp_template(frm);
	},

	channel: function (frm) {
		frm.events.setup_whatsapp_template(frm);
	},

	whatsapp_template: function (frm) {
		frm.doc.message = ""
		refresh_field("message")
		frm.events.setup_whatsapp_template(frm);
	},

	map_fields: function (frm) {
		let counter = 0
		let context = {}
		let contact_dict = {};
		var meta = frappe.get_meta(frm.doc.document_type)
		meta.fields.forEach((e) => { if (e.options == "Phone" || e.fieldname == "contact_phone" || e.fieldname == "contact_mobile") { contact_dict[e.fieldname] = e.label } })
		let doc_field_list = [{
			"value": "Attachment",
			"description": "Attach a file"
		}]
		if (frappe.model.can_print(null, cur_frm) && !meta.issingle) {
			doc_field_list.push({
				"value": "Print Format",
				"description": "Print Format"
			})
		}
		let data_link_dict = {}
		meta.fields.forEach((e) => { if (e.fieldtype == "Data" || e.fieldtype == "Link") { data_link_dict[e.fieldname] = e.label } })

		let new_dict = {}
		for (const [key, value] of Object.entries(data_link_dict)) {
			new_dict["value"] = value
			new_dict["description"] = key
			
			doc_field_list.push(new_dict)
			new_dict = {}
		}
		
		var d = new frappe.ui.Dialog({
			'fields': [
				{ 'label': __("Content"), 'fieldname': 'content', 'fieldtype': 'HTML' },

			],
			primary_action: function (values) {

				if (frm.doc.message != "" && frm.doc.message != "Add your message here"){
					frappe.confirm('This will overwrite the message. Are you sure you want to proceed?',
						() => {
							// action to perform if Yes is selected
							frm.doc.message = JSON.stringify(context)
							refresh_field("message")
							for (const [k, value] of Object.entries(context)) {
								frm.doc.whatsapp_parameter.forEach((f) =>{
									if(f.parameter == k){
										f.value = value
									}
								})
							}
							frm.refresh_fields("whatsapp_parameter");
							frm.dirty()
							d.hide()
						}, () => {
							// action to perform if No is selected
						})
				} 
				
			},
			primary_action_label: __("Map"),
			no_submit_on_enter: true,
			size: 'large',
			minimizable: true,
			title: ("Map Fields"),
		});

		if(frm.doc.whatsapp_template){
			frappe.db.get_doc("WhatsApp Template", frm.doc.whatsapp_template)
				.then((data) => {
					counter += 1
					if (counter == 1) {
						cur_frm.broadcast_name = data.broadcast_name
						// document.getElementsByClassName("modal-body ui-front").forEach((e) => 
						// 	{ e.addEventListener("click", function () { verify(cur_frm.dialog_d, cur_frm.dialog_context, cur_frm.dialog_data, cur_frm.dialog_header_html, cur_frm.data_dict); }); })
						const elements = document.getElementsByClassName("modal-body ui-front");
						const elementArray = Array.from(elements);
						
						elementArray.forEach((e) => {
						  e.addEventListener("click", function () {
						    verify(cur_frm.dialog_d, cur_frm.dialog_context, cur_frm.dialog_data, cur_frm.dialog_header_html, cur_frm.data_dict);
						  });
						});

						cur_frm.fields_list = data.whatsapp_map
						let option_list = ["Attachment"]
						if (frappe.model.can_print(null, cur_frm) && !meta.issingle) {
							option_list.push("Print Format")
						}
						data.whatsapp_map.forEach((e) => {
							if (e.location == "header") {

								d.make_field({
									"fieldtype": "Select",
									"label": e.field_name,
									"fieldname": e.field_name,
									"options": option_list,
									"reqd": 1
								})
							} else {
								d.make_field({
									"fieldtype": "MultiSelect",
									"label": e.field_name,
									"fieldname": e.field_name,
									"reqd": 1
								})

							}
							// make attach field for every field
							d.make_field({
								"label": __("Attachment"),
								"fieldtype": "Attach",
								"fieldname": e.field_name + "_attachment",
								"hidden": true
							})
							
							d.get_field(e.field_name + "_attachment").refresh()

							// make print_format field for every field
							d.make_field({
								"label": __("Select Print Format"),
								"fieldtype": "Select",
								"fieldname": e.field_name + "_print_format",
								"options": frappe.meta.get_print_formats(meta.name),
								"hidden": true
							});
							d.get_field(e.field_name + "_print_format").refresh()

							d.get_field(e.field_name).refresh();
							context[e.field_name] = "";

							if (e.location != "header") {
								d.get_field(e.field_name).set_data(doc_field_list)
							}

							d.fields_dict[e.field_name].input.onchange = function () {
								if (this.value && this.value.replace(", ", "") == "Attachment") {
									d.get_field(e.field_name + "_attachment").df.hidden = false
									d.get_field(e.field_name + "_attachment").value = ""
									d.get_field(e.field_name + "_attachment").refresh()

									d.get_field(e.field_name + "_print_format").df.hidden = true
									d.get_field(e.field_name + "_print_format").refresh()
									cur_frm.dialog_context[e.field_name] = ""
								}
								else if (this.value && this.value.replace(", ", "") == "Print Format") {
									d.get_field(e.field_name + "_attachment").df.hidden = true
									d.get_field(e.field_name + "_attachment").refresh()

									d.get_field(e.field_name + "_print_format").df.hidden = false
									d.get_field(e.field_name + "_print_format").refresh()
									cur_frm.dialog_context[e.field_name] = ""
								} else {
									d.get_field(e.field_name + "_attachment").df.hidden = true
									d.get_field(e.field_name + "_attachment").refresh()

									d.get_field(e.field_name + "_print_format").df.hidden = true
									d.get_field(e.field_name + "_print_format").refresh()
								}

								verify(cur_frm.dialog_d, cur_frm.dialog_context, cur_frm.dialog_data, cur_frm.dialog_header_html, cur_frm.data_dict)

							}

						})
						let header_html = "";
						if (!["text", "", undefined, null].includes(data.header_type)) {
							header_html = data.header_type.charAt(0).toUpperCase() + data.header_type.slice(1) + ` Attachment: <a href="` + data.header_link + `">` + data.header_link + `</a><br><br>`

						}
						$(d.get_field('content').wrapper).html(
							`<div class="card mb-3 h-100"><div class="card-body">` + header_html + data.message_body + `<br><br></div></div>`
						);

						cur_frm.dialog_d = d
						cur_frm.dialog_context = context
						cur_frm.dialog_data = data
						cur_frm.dialog_header_html = header_html
						cur_frm.data_dict = data_link_dict
					}
				});
		}

		d.show();
		d.get_primary_btn()[0].disabled = true

	},

	setup_whatsapp_template: function (frm) {
		let template = '';
		let total_html = "";
		if (frm.doc.channel === 'WhatsApp') {

			if (frm.doc.whatsapp_template != undefined) {
				frappe.db.get_doc("WhatsApp Template", frm.doc.whatsapp_template)
					.then((data) => {
						frm.fields_list = data.whatsapp_map
						if (frm.doc.message == "" || frm.doc.message == "Add your message here") {
							let param_html = ""
							if (data.whatsapp_map.length > 0) {
								param_html = `{`
								data.whatsapp_map.forEach((e) => {
									let check = false
									param_html += `"` + e.field_name + `": "", `
									if(cur_frm.is_new() != 1){
									frm.doc.whatsapp_parameter.forEach((f) =>{
										if(f.parameter == e.field_name){
											check = true
										}
									})
								}
									if(check == false){
										var childTable = cur_frm.add_child("whatsapp_parameter");
										childTable.parameter= e.field_name
										cur_frm.refresh_fields("whatsapp_parameter");
									}
								})
								param_html = param_html.slice(0,-2)
								param_html += `}`
								frm.doc.message = param_html
								refresh_field("message")
								frm.dirty()
							}

						}
						let header_html = "";

						if (data.header_type != 'text' && data.header_type != '') {

							header_html = `Attachment: <a href="` + data.header_link + `">` + data.header_link + `</a><br><br>`

						}

						total_html = '<div class="card mb-3 h-100"><div class="card-body">' + header_html + data.message_body + '<br><br></div></div>'
						template = '<h5 style="display: inline-block">Warning:</h5><br>Only Use Pre-Approved WhatsApp Template. Message should be a dictionary of parameters and values for the selected template.<h5>Message Example:</h5><pre>{"file_url":"https://www.onehash.ai/files/demo.pdf", "name": "{{ doc.name }}" }</pre><pre>Put "print_format" to attach Print Format of document. Also enable and select Print Format in Print Settings below.</pre>';
						if (template) {
							frm.set_df_property('message_examples', 'options', template);
						}

					})
			}
		}
	}
});

function verify(d, context, data, header_html, data_dict) {
	for (const [key, value] of Object.entries(context)) {
		if ((d.get_field(key).input.value).replace(", ", "") == "Attachment") {
			if (d.get_field(key + "_attachment").value == null || d.get_field(key + "_attachment").value.length == 0) {
				return
			}
			else if(d.get_field(key + "_attachment").value && d.get_field(key + "_attachment").value.includes("/private/")){
				d.get_field(key + "_attachment").value = ""
				d.get_field(key + "_attachment").refresh()
				frappe.msgprint("Attachment File can't be Private")
			}
			else if (d.get_field(key + "_attachment").value && d.get_field(key + "_attachment").value.includes("https://")) {
				context[key] = (d.get_field(key + "_attachment").value)
			} else {
				context[key] = ("https://" + frappe.boot.sitename + d.get_field(key + "_attachment").value)
			}
		}else if ((d.get_field(key).input.value).replace(", ", "") == "Print Format") {
			frappe.call({
				method: "wati.users.get_attach_link",
				args: { "doc": { "doctype": cur_frm.doc.doctype, "docname": cur_frm.doc.name }, "print_format": d.get_field(key + "_print_format").value },
				callback: (r) => {
					context[key] = r.message
				}
			})
		}
		else {
			context[key] = (d.get_field(key).input.value).replace(", ", "");
			for (const [k, value] of Object.entries(data_dict)) {
				if((d.get_field(key).input.value).replace(", ", "") == value){
					context[key] = 	"{{ doc." + k + " }}"
				}
			}
	}
}
	$(d.get_field('content').wrapper).html(
		`<div class="card mb-3 h-100"><div class="card-body">` + frappe.render(header_html, context) + frappe.render(data.message_body, context) + `<br><br></div></div>`
	);
	d.get_primary_btn()[0].disabled = false
}
