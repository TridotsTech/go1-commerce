app_name = "go1_commerce"
app_title = "Go1 Commerce"
app_publisher = "Tridotstech PVT LTD"
app_description = "Go1 Commerce is an Open Source eCommerce portal built on frappe framework."
app_email = "info@tridotstech.com"
app_license = "mit"
required_apps = ['builder']

app_logo_url = "/assets/go1_commerce/images/go1_commerce_logo.svg"

website_context = {
	"favicon": "/assets/go1_commerce/images/go1favicon.svg",
	"splash_image": "/assets/go1_commerce/images/go1_commerce_logo.svg",
}

boot_session = "go1_commerce.go1_commerce.v2.common.boot_session"

# website permission
has_website_permission = {
	'Customers':'go1_commerce.go1_commerce.v2.common.customer_web_permission'
}

after_install = "go1_commerce.go1_commerce.after_install.after_install"
# on login
on_session_creation = "go1_commerce.go1_commerce.v2.common.login_customer"

app_include_css = [
	"/assets/go1_commerce/css/console.css",
	"/assets/go1_commerce/css/ui/uploader.css",
]
app_include_js = [
    "/assets/go1_commerce/js/ui/dialog_popup.js",
     "/assets/go1_commerce/js/default_methods.js",
     "/assets/go1_commerce/js/option.js",
	"/assets/go1_commerce/js/console.js",
	"/assets/go1_commerce/js/getting_started.js",
	"assets/go1_commerce/js/ui/product_func_class.js",
	"assets/go1_commerce/js/quick_entry/return_quick_entry.js",
]
doctype_js = {
    "Web Form" : "public/js/ui/editor/web_form.js"
    }

page_js = {
	"products-bulk-update": [
		"public/plugins/datatable/sortable.min.js",
		"public/plugins/datatable/clusterize.min.js",
		"public/plugins/datatable/frappe-datatable.min.js",
		"public/js/uppy.min.js",
		"public/js/lightgallery.js"
	]
}


has_website_permission = {
	"Customers": "go1_commerce.go1_commerce.doctype.customers.customers.has_website_permission"
}

override_doctype_class = {
	'File': 'go1_commerce.go1_commerce.override.CustomFile',
	'PageSection': 'go1_commerce.go1_commerce.override.PageSection',
	'Builder Page':'go1_commerce.go1_commerce.doctype.override_doctype.builder_page.BuilderPage'
}


doc_events = {
	"User": {
		"after_insert": "go1_commerce.go1_commerce.doctype.customers.customers.generate_keys"
	},
	"Newsletter": {
		"autoname": "go1_commerce.utils.setup.autoname_newsletter"
	},
	
	"Order": {
		"on_submit": "go1_commerce.go1_commerce.v2.whoosh.update_order_item"
	},
	"Google Settings": {
		"validate": "go1_commerce.utils.setup.validate_google_settings"
	},
	"Help Article": {
		"validate": "go1_commerce.go1_commerce.v2.common.create_help_article_json"
	},
		"Order Settings": {
		"on_update": "go1_commerce.go1_commerce.v2.common.generate_all_website_settings_json_doc"
	},
	"Catalog Settings": {
		"on_update": "go1_commerce.go1_commerce.v2.common.generate_all_website_settings_json_doc"
	},
	"Market Place Settings": {
		"on_update": "go1_commerce.go1_commerce.v2.common.generate_all_website_settings_json_doc"
	},
	"Shopping Cart Settings": {
		"on_update": "go1_commerce.go1_commerce.v2.common.generate_all_website_settings_json_doc"
	},
	"Product Category": {
		"on_update": "go1_commerce.go1_commerce.v2.common.generate_all_website_settings_json_doc"
	},
	"Media Settings": {
		"on_update": "go1_commerce.go1_commerce.v2.common.generate_all_website_settings_json_doc"
	},
	"Header Component": {
		"on_update": "go1_commerce.go1_commerce.v2.common.generate_all_website_settings_json_doc"
	},
	"Footer Component": {
		"on_update": "go1_commerce.go1_commerce.v2.common.generate_all_website_settings_json_doc"
	},
	"Menu": {
		"on_update": "go1_commerce.go1_commerce.v2.common.generate_all_website_settings_json_doc"
	},
	"Version":{
		"after_insert":"go1_commerce.go1_commerce.v2.orders.update_stoke"
	},
	"Builder Page":{
		"on_update":"go1_commerce.go1_commerce.v2.builder_page.update_global_script"
	}
}

# Scheduled Tasks
# ---------------
scheduler_events = {
	"all": [
		"go1_commerce.accounts.api.release_lockedin_amount"
	],
	"monthly": [
		"go1_commerce.utils.setup.clear_logs"	
	],
	"cron": {
		"* * * * *": [
			"frappe.email.queue.flush",
		],
		"0 1 * * *": [
			"go1_commerce.go1_commerce.doctype.customers.customers.delete_guest_customers",
		],
		"30 12 1 * *":[
			"go1_commerce.utils.setup.clear_api_log"
		]
	}
}

fixtures = [
	{
		"doctype": "Custom Script",
		"filters": [
			["name", "in", (
				"Newsletter-Client"
			)]
		]
	},
	{
		"doctype": "Custom Field",
		"filters": [
			["name", "in", (
				"Country-enabled",
				"Country-phone_number_code",
				"Country-validate_zipcode",
				"Country-zipcode_validation_policy",
				"Country-min_zipcode_length",
				"Country-max_zipcode_length",
				"Notification-allow_user_modify",
				"Email Group Member-business",
				"Google Settings-restrict_to_countries",
				"Google Settings-countries",
				"Google Settings-default_address",
				"Google Settings-latitude",
				"Google Settings-longitude",
				"Google Settings-marker_icon",
				"Help Article-doctype_name",
				"Help Article-domain_name",
				"Email Group-business",
				"Builder Settings-custom_server_script",

			)]
		]
	}
]

# Set default Role-updateby siva
# -------
default_roles = [
	{'role': 'Customer', 'doctype':'Customers'},
]
override_whitelisted_methods = {
    "frappe.client.validate_link": "go1_commerce.utils.utils.validate_link",
    "frappe.desk.form.linked_with.cancel_all_linked_docs": "go1_commerce.utils.utils.cancel_all_linked_docs"
    
}

auto_cancel_exempted_doctypes = ["Order"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/go1_commerce/css/go1_commerce.css"
# app_include_js = "/assets/go1_commerce/js/go1_commerce.js"

# include js, css files in header of web template
# web_include_css = "/assets/go1_commerce/css/go1_commerce.css"
# web_include_js = "/assets/go1_commerce/js/go1_commerce.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "go1_commerce/public/scss/website"

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

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "go1_commerce/public/icons.svg"

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
# 	"methods": "go1_commerce.utils.jinja_methods",
# 	"filters": "go1_commerce.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "go1_commerce.install.before_install"
# after_install = "go1_commerce.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "go1_commerce.uninstall.before_uninstall"
# after_uninstall = "go1_commerce.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "go1_commerce.utils.before_app_install"
# after_app_install = "go1_commerce.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "go1_commerce.utils.before_app_uninstall"
# after_app_uninstall = "go1_commerce.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "go1_commerce.notifications.get_notification_config"

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
# 		"go1_commerce.tasks.all"
# 	],
# 	"daily": [
# 		"go1_commerce.tasks.daily"
# 	],
# 	"hourly": [
# 		"go1_commerce.tasks.hourly"
# 	],
# 	"weekly": [
# 		"go1_commerce.tasks.weekly"
# 	],
# 	"monthly": [
# 		"go1_commerce.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "go1_commerce.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "go1_commerce.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "go1_commerce.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["go1_commerce.utils.before_request"]
# after_request = ["go1_commerce.utils.after_request"]

# Job Events
# ----------
# before_job = ["go1_commerce.utils.before_job"]
# after_job = ["go1_commerce.utils.after_job"]

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
# 	"go1_commerce.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

