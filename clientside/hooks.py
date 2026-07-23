from . import __version__ as app_version
import clientside

app_name = "clientside"
app_title = "Clientside"
app_publisher = "OneHash"
app_description = "An app to handle customer facing view"
app_email = "support@onehash.ai"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = ""
app_include_js = [
    "clientside.bundle.js",
    "assets/clientside/js/check_subscription.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/clientside/css/clientside.css"
# web_include_js = "/assets/clientside/js/clientside.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "clientside/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"/": "public/js/file.js"}


# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

after_migrate = [
    "clientside.api.update_workspaces",
    "clientside.install.apply_enterprise_defaults",
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "clientside.utils.jinja_methods",
# 	"filters": "clientside.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "clientside.install.before_install"
after_install = "clientside.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "clientside.uninstall.before_uninstall"
# after_uninstall = "clientside.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "clientside.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
permission_query_conditions = {
    "Server Script": "clientside.clientside.access_control.deny_script_control_query_conditions",
    "Client Script": "clientside.clientside.access_control.deny_script_control_query_conditions",
    "System Console": "clientside.clientside.access_control.deny_script_control_query_conditions",
}

# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }
has_permission = {
    "Server Script": "clientside.clientside.access_control.has_script_control_permission",
    "Client Script": "clientside.clientside.access_control.has_script_control_permission",
    "System Console": "clientside.clientside.access_control.has_script_control_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    "Communication": "clientside.clientside.overrides.communication.CommunicationOverride",
    "System Settings": "clientside.clientside.overrides.system_settings.SystemSettingsOverride",
    "Email Queue": "clientside.clientside.overrides.email_queue.EmailQueueOverride",
    "Notification": "clientside.clientside.overrides.notification.NotificationOverride",
}
# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "User": {
        "after_insert": "clientside.clientside.utils.create_user_in_user_details",
        "on_update": "clientside.clientside.utils.update_user_in_user_details",
        "after_delete": "clientside.clientside.utils.delete_user_in_user_details",
    }
}

# Scheduled Tasks
# ---------------
scheduler_events = {}

# Testing
# -------

# before_tests = "clientside.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "frappe.client.save": "clientside.clientside.overrides.globals.save",
    "frappe.desk.form.save.savedocs": "clientside.clientside.overrides.globals.savedocs",
    "frappe.desk.doctype.system_console.system_console.execute_code": "clientside.clientside.access_control.execute_system_console_code",
    "frappe.desk.doctype.system_console.system_console.show_processlist": "clientside.clientside.access_control.show_system_console_processlist",
    "frappe.core.doctype.communication.email.mark_email_as_seen": "clientside.clientside.overrides.email.mark_email_as_seen",
    "frappe.core.doctype.communication.email.make": "clientside.clientside.overrides.email.make",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "clientside.task.get_dashboard_data"
# }
boot_session = "clientside.boot.extend_bootinfo"
# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]
# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication"]

# Request Events
# ----------------
before_request = ["clientside.platform_rate_limit.enforce_api_rate_limit"]
# after_request = ["clientside.utils.after_request"]

# Job Events
# ----------
# before_job = ["clientside.utils.before_job"]
# after_job = ["clientside.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]
website_redirects = []
# Authentication and authorization
# --------------------------------
# on_session_creation = "clientside.clientside.utils.alertForUpgrade"
