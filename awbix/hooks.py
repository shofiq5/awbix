app_name = "awbix"
app_title = "AWBix"
app_publisher = "Shofiq"
app_description = "Cargo System"
app_email = "shofiq5@gmail.com"
app_license = "epl-2.0"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "awbix",
# 		"logo": "/assets/awbix/logo.png",
# 		"title": "AWBix",
# 		"route": "/awbix",
# 		"has_permission": "awbix.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "awbix.bundle.css"
# app_include_js = "awbix.bundle.js"

# include js, css files in header of web template
# web_include_css = "/assets/awbix/css/awbix.css"
# web_include_js = "/assets/awbix/js/awbix.js"

# Portal pages — injected via portal_base.html using include_style / include_script
# (not using web_include_* to avoid loading portal assets on non-portal pages)

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "awbix/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_list_js = {"EDX Message Stage": "edx/doctype/edx_message_stage/edx_message_stage.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "awbix/public/icons.svg"

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
# 	"methods": "awbix.utils.jinja_methods",
# 	"filters": "awbix.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "awbix.install.before_install"
# after_install = "awbix.install.after_install"

# EDX: seed/refresh message definitions (idempotent) after every migrate
after_migrate = ["awbix.edx.install.after_migrate"]

# Uninstallation
# ------------

# before_uninstall = "awbix.uninstall.before_uninstall"
# after_uninstall = "awbix.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "awbix.utils.before_app_install"
# after_app_install = "awbix.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "awbix.utils.before_app_uninstall"
# after_app_uninstall = "awbix.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "awbix.notifications.get_notification_config"

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

# scheduler_events = {
# 	"all": [
# 		"awbix.tasks.all"
# 	],
# 	"daily": [
# 		"awbix.tasks.daily"
# 	],
# 	"hourly": [
# 		"awbix.tasks.hourly"
# 	],
# 	"weekly": [
# 		"awbix.tasks.weekly"
# 	],
# 	"monthly": [
# 		"awbix.tasks.monthly"
# 	],
# }

# EDX messaging engine — poll inbound transports, dispatch outbound, retry failures.
# poll_inbound_connections / dispatch_outbound_queue are no-ops until EDX Connection
# exists (M4); they self-guard so this is safe to enable now.
scheduler_events = {
	"cron": {
		"*/2 * * * *": ["awbix.edx.engine.pipeline.poll_inbound_connections"],
		"*/1 * * * *": ["awbix.edx.engine.pipeline.dispatch_outbound_queue"],
	},
	"all": ["awbix.edx.engine.pipeline.retry_failed"],
	# Project: re-check active tasks and surface likely-done ones for human review.
	"daily": ["awbix.project.completion.detect_completed_tasks"],
}

# Testing
# -------

# before_tests = "awbix.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "awbix.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "awbix.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["awbix.utils.before_request"]
# after_request = ["awbix.utils.after_request"]

# Job Events
# ----------
# before_job = ["awbix.utils.before_job"]
# after_job = ["awbix.utils.after_job"]

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
# 	"awbix.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Fixtures
# ---------
# Export DocTypes as fixtures (master/reference data), excluding transactional logs
fixtures = [
	"OCI Information Identifier",
	"Accounting Information Identifier",
	"Measurement Unit Code",
	"Airport",
	"Airline",
	"Charge Code",
	"Customs Information Identifier",
	"ULD Type",
	"Service Code",
	"Volume Code",
	"Rate Class Code",
	"Special Handling Code",
	"Other Charge Code",
	"Participant Identifier",
	"Party",
	"Party Contact",
	"Shipment",
	"Shipment FSU",
	"Shipment FSU Status Record",
	"EDX Connection",
	"EDX Message Definition",
	"EDX Message Issue",
	"EDX Message Routing",
	"EDX Message Stage",
	"EDX Delivery",
	"EDX Verify Row",
]

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

