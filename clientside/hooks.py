from . import __version__ as app_version

app_name = "clientside"
app_title = "Clientside"
app_publisher = "OneHash"
app_description = "An app to handle customer facing view"
app_email = "digital@onehash.ai"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/clientside/css/clientside.css"
# app_include_js = "/assets/clientside/js/clientside.js"

# include js, css files in header of web template
# web_include_css = "/assets/clientside/css/clientside.css"
# web_include_js = "/assets/clientside/js/clientside.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "clientside/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

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
after_install = "clientside.clientside.utils.post_install"
import frappe


def tps():
    frappe.db.set_default("desktop:home_page", "workspace")
    frappe.db.set_single_value("System Settings", "setup_complete", 1)
    frappe.db.set_single_value("System Settings", "enable_onboarding", 1)


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
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
    "cron": {
        "* * * *": ["clientside.clientside.utils.pri"],
    }
}

# Testing
# -------

# before_tests = "clientside.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "frappe.frappe.core.doctype.user.user.sign_up": "clientside.clientside.overrides.sign_up",
    "frappe.core.doctype.communication.email.make": "clientside.clientside.overrides.make",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "clientside.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["clientside.utils.before_request"]
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

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"clientside.auth.validate"
# ]

doc_events = {
    "User": {
        # will run before a ToDo record is inserted into database
        "before_insert": "clientside.clientside.utils.check_user",
    },
}
override_email_send = "clientside.clientside.overrides.sendEmail"
