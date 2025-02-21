import frappe

@frappe.whitelist(allow_guest=True, methods=("GET",))
def mark_email_as_seen(recipient_email: str, reference_name: str, reference_doctype: str, communication_name: str | None = None):  
	from werkzeug.wrappers import Response
	frappe.request.after_response.add(lambda: _mark_email_as_opened(recipient_email, reference_name, reference_doctype, communication_name))
	pixel = b"GIF89a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"

	response = Response()
	response.mimetype = "image/gif"
	response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	response.headers["Expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
	response.data = pixel
	return response

def _mark_email_as_opened(recipient_email, reference_name, reference_doctype, communication_name):
	try:
		update_communication(recipient_email, communication_name)
		if reference_doctype == "Email Campaign":
			update_email_campaign(recipient_email, reference_name)

	except Exception as e:
		frappe.log_error(f"Failed to mark email as seen: {str(e)}", "Email Tracking")
		
def update_communication(recipient_email, communication_name):
	from frappe.utils import now_datetime

	current_time = now_datetime()
	formatted_time = current_time.strftime("%d-%m-%Y %I:%M %p")
	doc = frappe.get_doc('Communication', communication_name)
	child_entry = next((child for child in doc.all_emails if child.email == recipient_email), None)
	
	if child_entry:
		frappe.db.set_value("Email Insights", child_entry.name, "opened", child_entry.opened + 1, update_modified=False)
		frappe.db.set_value("Email Insights", child_entry.name, "opened_at", child_entry.opened_at + '\n' + formatted_time, update_modified=False)
	else:
		new_row = {
            "doctype": "Email Insights",
            "parent": communication_name,
            "parentfield": "all_emails",
            "parenttype": "Communication",
            "email": recipient_email,
            "opened": 1,
            "opened_at": formatted_time
        }
		child_doc = frappe.get_doc(new_row)
		child_doc.insert(ignore_permissions=True)
	frappe.db.commit()

def update_email_campaign(recipient_email, reference_name):
	from frappe.utils import now_datetime

	current_time = now_datetime()
	formatted_time = current_time.strftime("%d-%m-%Y %I:%M %p")
	doc = frappe.get_doc('Email Campaign', reference_name)
	child_entry = next((child for child in doc.all_emails if child.email == recipient_email), None)
	
	if child_entry:
		frappe.db.set_value("Email Insights", child_entry.name, "opened", child_entry.opened + 1, update_modified=False)
		frappe.db.set_value("Email Insights", child_entry.name, "opened_at", child_entry.opened_at + '\n' + formatted_time, update_modified=False)
	else:
		new_row = {
            "doctype": "Email Insights",
            "parent": reference_name,
            "parentfield": "all_emails",
            "parenttype": "Email Campaign",
            "email": recipient_email,
            "opened": 1,
            "opened_at": formatted_time
        }
		child_doc = frappe.get_doc(new_row)
		child_doc.insert(ignore_permissions=True)
	frappe.db.commit()