import frappe
from frappe.utils import getdate, nowdate,add_days
from frappe.query_builder import DocType

@frappe.whitelist()
def create_data_import(document_type):
	doc = frappe.new_doc('Data Import')
	doc.reference_doctype = document_type
	doc.import_type = "Insert New Records"
	doc.skip_errors = 1
	doc.no_email = 1
	doc.save(ignore_permissions=True)
	return doc

def on_update_shopping_cart(doc, method):
	try:
		if doc.cart_type == "Shopping Cart":
			enable_campaign = frappe.db.get_value('Email Campaign Settings', None, 'enable_campaign')
			if enable_campaign:
				if doc.items and doc.naming_series != 'GC- ':
					EmailCampaign = DocType('Email Campaign')
					check_campaign = frappe.qb.select(EmailCampaign.name).from_(EmailCampaign) \
						.where(
							(EmailCampaign.email_campaign_for == "Shopping Cart") &
							(EmailCampaign.recipient == recipient) &
							((EmailCampaign.status == "In Progress") | (EmailCampaign.status == "Scheduled"))
						).run(as_dict=True)
					
					if not check_campaign:
						campaign = frappe.db.get_value('Email Campaign Settings', None, 'shopping_cart')
						if campaign:
							insert_email_campaign(campaign, 'Shopping Cart', doc.name)
	except Exception:
		frappe.log_error(message = frappe.get_traceback(), title = "Error in on_update_shopping_cart")

def insert_email_campaign(campaign, email_campaign_for, recipient):
	campaign = frappe.get_doc("Campaign", campaign)
	for entry in campaign.get("campaign_schedules"):
		scheduled_date = getdate(nowdate())
		end_date = None
		if entry.get('send_after_days'):
			scheduled_date = add_days(getdate(nowdate()), entry.get('send_after_days'))
		if entry.get('no_of_times'):
			end_date = add_days(getdate(nowdate()), entry.get('no_of_times'))
		doc = frappe.new_doc('Email Campaign')
		doc.campaign = campaign
		doc.email_campaign_for = email_campaign_for
		doc.campaign_for = email_campaign_for
		doc.recipient = recipient
		doc.start_date = scheduled_date
		if end_date:
			doc.end_date = end_date
		if scheduled_date == getdate(nowdate()):
			doc.status = "In Progress"
		else:
			doc.status = "Scheduled"
		doc.email_template = entry.get("email_template")
		doc.campign_id = entry.name
		doc.save(ignore_permissions=True)

def after_insert_email_group(doc, method):
	enable_campaign = frappe.db.get_value('Email Campaign Settings', None, 'enable_campaign')
	if enable_campaign:
		campaign = frappe.db.get_value('Email Campaign Settings', None, 'email_group')
		if campaign:
			create_email_campaign(campaign, 'Email Group', doc.name)

def create_email_campaign(campaign, email_campaign_for, recipient):
	check_records = frappe.db.get_all('Email Campaign', filters={'email_campaign_for': email_campaign_for, 'recipient': recipient, 'status': 'In Progress'})
	if check_records:
		for item in check_records:
			ref_doc = frappe.get_doc('Email Campaign', item.name)
			ref_doc.save(ignore_permissions=True)
	doc = frappe.new_doc('Email Campaign')
	doc.campaign = campaign
	doc.email_campaign_for = email_campaign_for
	doc.campaign_for = email_campaign_for
	doc.recipient = recipient
	doc.start_date = getdate(nowdate())
	doc.save(ignore_permissions=True)

@frappe.whitelist(allow_guest=True)
def get_builder_page_data(page_title= None):
	filters={}
	if page_title:
		filters["page_title"]= page_title
	doc = frappe.db.get_all("Builder Page",fields = ["published","page_name","route",
													"dynamic_route","blocks","page_data_script","preview","page_title"],
													filters=filters)
	for i in doc:
		client_scripts = frappe.db.get_all("Builder Page Client Script",fields = ["builder_script"], filters = {"parent":i.page_name})
		i["client_scripts"] = client_scripts
		i['doctype']="Builder Page"
	return doc
 
 
@frappe.whitelist(allow_guest=True)
def get_all_data(doctype = None, docname=None):
	filters={}
	if doctype:
		if docname:
			filters["name"]= docname
		doc = frappe.db.get_all(doctype,fields = ["*"],filters=filters)
		return doc
 
 
@frappe.whitelist(allow_guest=True)
def get_builder_component_data(component_name = None, component_id= None):
	filters={}
	if component_name:
		filters["component_name"] = component_name
	if component_id:
		filters["component_id"] = component_id
	doc = frappe.db.get_all("Builder Component",fields = ["component_name","block","component_id"],
							filters=filters)
	for x in doc:
		x['doctype']='Builder Component'
	return doc
 
@frappe.whitelist(allow_guest=True)
def get_builder_script_data(name = None):
	filters={}
	if name:
		filters["name"] = name
	doc = frappe.db.get_all("Builder Client Script",fields = ["name","script_type","script","public_url"],
						 filters=filters)
	for x in doc:
		x['doctype']='Builder Client Script'
	return doc
 
@frappe.whitelist(allow_guest=True)
def get_builder_settings_data():
	doc = frappe.get_doc("Builder Settings","Builder Settings",fields = ["script","script_public_url","style","custom_server_script","style_public_url"])
	return doc
 
@frappe.whitelist(allow_guest=True)
def update_builder_page_data_script(doc_name, data_script = None):
	doc = frappe.get_doc("Builder Page", doc_name)
	doc.page_data_script = data_script
	doc.save(ignore_permissions = True)
 
