import frappe
from frappe.utils import getdate, nowdate,add_days

@frappe.whitelist()
def create_data_import(document_type):
	doc = frappe.new_doc('Data Import')
	doc.reference_doctype = document_type
	doc.skip_errors = 1
	doc.no_email = 1
	doc.save(ignore_permissions=True)
	return doc

# by gopi on 13/6/24

def on_update_shopping_cart(doc, method):
	try:
		if doc.cart_type == "Shopping Cart":
			enable_campaign = frappe.db.get_value('Email Campaign Settings', None, 'enable_campaign')
			if enable_campaign:
				if doc.items and doc.naming_series != 'GC- ':
					check_campaign = frappe.db.sql('''
										select name from `tabEmail Campaign` where email_campaign_for = "Shopping Cart" 
											and recipient = %(recipient)s and (status = "In Progress" OR status = "Scheduled") ''',{'recipient': doc.name}, as_dict=1)
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

# def on_update_shopping_cart(doc, method):
# 	try:
# 		enable_campaign = frappe.db.get_value('Email Campaign Settings', None, 'enable_campaign')
# 		if enable_campaign:
# 			if doc.items and doc.naming_series != 'GC- ':
# 				date = min([x.creation for x in doc.items])
# 				check_campaign = frappe.db.sql('''select name from `tabEmail Campaign` where email_campaign_for = "Shopping Cart" and recipient = %(recipient)s and end_date >= %(date)s''',{'date': getdate(date), 'recipient': doc.name}, as_dict=1)
# 				if not check_campaign:
# 					campaign = frappe.db.get_value('Email Campaign Settings', None, 'shopping_cart')
# 					if campaign:
# 						create_email_campaign(campaign, 'Shopping Cart', doc.name)
# 	except Exception:
# 		frappe.log_error(message = frappe.get_traceback(), title = "Error in on_update_shopping_cart")

# end

def after_insert_email_group(doc, method):
	enable_campaign = frappe.db.get_value('Email Campaign Settings', None, 'enable_campaign')
	if enable_campaign:
		campaign = None
		if frappe.db.get_value("Email Group",doc.name,"business"):
			business = frappe.db.get_value("Email Group",doc.name,"business")
			campaigns = frappe.db.get_all("Business Campaign",filters={"parent":'Email Campaign Settings',"business":business},fields=['campaign'])
			if campaigns:
				campaign = campaigns[0].campaign
		else:
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
