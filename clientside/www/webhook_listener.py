import frappe
import json

@frappe.whitelist(allow_guest=True)
def webhook_listener():
    try:
        raw_data = frappe.request.get_data(as_text=True)
        print("Received raw data:", raw_data)

        if raw_data:
            data = json.loads(raw_data)
            print("Parsed data:", data)

            if isinstance(data, dict):
                sender = data.get('waId')
                content = data.get('text')

                if sender is not None and content is not None:
                    create_lead(sender, content)
                    return {'status': 'success'}
                else:
                    frappe.log_error("Missing sender or content in webhook data")
                    return {'error': 'Missing sender or content'}
            else:
                frappe.log_error("Invalid data format in webhook")
                return {'error': 'Invalid data format'}
        else:
            frappe.log_error("Empty data received in webhook")
            return {'error': 'Empty data'}
    except Exception as e:
        frappe.log_error(f"Webhook Error: {str(e)}")
        return {'error': str(e)}

def create_lead(sender, content):
    if str(content)=='Interested':
        lead = frappe.get_doc({
            'doctype': 'Lead',
            'first_name': 'WhatsApp Message',
            'phone':sender,
            'last_name':content
        })
        lead.insert(ignore_permissions=True)
