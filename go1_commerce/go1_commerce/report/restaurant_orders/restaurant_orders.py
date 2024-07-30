# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	columns, data = [], []
	if not filters: filters={}
	columns=get_columns()
	data=get_values(filters)
	status_result = get_status()
	status = []
	if status_result:
		for item in status_result:
			status.append(item)
	chart = get_chart_data(status,data, filters)
	return columns, data, None, chart

def get_columns():
	columns = [
		_("Order Id") + ":Data:120",
		_("Order Date") + ":Date:120"				
	]
	if "Admin" in frappe.get_roles(frappe.session.user) or "Super Admin" in frappe.get_roles(frappe.session.user):
		columns += [ 
			_("Business") + ":Link/Business:120",
			_("Business Name") + ":Data:120"
		]
	columns += [
		_("Order Status") + ":Data:120",
		_("Payment Status") + ":Data:120",
		_("Customer Name") + ":Data:120",
		_("Sub Total") + ":Currency:120",
		_("Shipping Charges") + ":Currency:120",
		_("Tax Amount") + ":Currency:120",
		_("Total Amount") + ":Currency:120",
		_("Total Amount For Vendor") + ":Currency:170"
	]
	return columns

def get_values(filters):
	conditions = get_conditions(filters)
	if "Admin" in frappe.get_roles(frappe.session.user) or "Super Admin" in frappe.get_roles(frappe.session.user):
		customer_order = frappe.db.sql('''select o.name, o.order_date, o.business,(select restaurant_name from `tabBusiness` where name=o.business) as business_name, o.status, o.payment_status, ifnull((concat(o.first_name,' ' ,o.last_name)),o.first_name) as full_name, 
			 o.order_subtotal,o.shipping_charges,o.total_tax_amount,o.total_amount, o.total_amount_for_vendor from 
			`tabOrder` o where o.naming_series !="SUB-ORD-" and o.docstatus=1 o.naming_series !="SUB-ORD-" '''.format(condition=conditions),as_list=1)
	else:
		if "Vendor" in frappe.get_roles(frappe.session.user):
			permission=frappe.db.sql('''select group_concat(concat('"',for_value,'"')) as business from `tabUser Permission` where user=%s and allow="Business"''',(frappe.session.user),as_dict=1)
			if permission and permission[0].business:
				conditions +=' and o.business in ({business})'.format(business=permission[0].business)
			else:
				frappe.throw(_('No {0} is mapped for your login.').format(_("Business")))
		customer_order = frappe.db.sql('''select o.name, o.order_date, o.status, o.payment_status, ifnull((concat(o.first_name,' ' ,o.last_name)),o.first_name) as full_name, 
			 o.order_subtotal,o.shipping_charges,o.total_tax_amount,o.total_amount, o.total_amount_for_vendor from 
			`tabOrder` o where o.naming_series !="SUB-ORD-" and o.docstatus=1 {condition} '''.format(condition=conditions),as_list=1)
	return customer_order

def get_conditions(filters):
	conditions=''
	if filters.get('from_date'):
		conditions+=' and o.order_date>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		conditions+=' and o.order_date<="%s"' % filters.get('to_date')
	if filters.get('status'):
		conditions+=' and o.status="%s"' % filters.get('status')
	if filters.get('payment_status'):
		conditions+=' and o.payment_status="%s"' % filters.get('payment_status') 
	return conditions
	

@frappe.whitelist(allow_guest=True)
def check_domain(domain_name):
	try:
		from frappe.core.doctype.domain_settings.domain_settings import get_active_domains
		domains_list=get_active_domains()
		domains=frappe.cache().hget('domains','domain_constants')
		if not domains:
			domains=get_domains_data()
		if domains[domain_name] in domains_list:
			return True
		return False
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.api.check_domain")

def get_status():
	return frappe.db.sql("""select name from `tabOrder Status` where domain_based = 0 order by display_order asc""" , as_list=1)

def get_chart_data(status,data, filters):
	conditions = get_conditions(filters)
	if not status:
		status = []
	datasets = []
	for item in status:
		if item:
			if "Admin" in frappe.get_roles(frappe.session.user) or "Super Admin" in frappe.get_roles(frappe.session.user):
				total_order = frappe.db.sql('''select sum(o.total_amount) from 
					`tabOrder` o where o.naming_series !="SUB-ORD-" and o.docstatus=1 o.naming_series !="SUB-ORD-" and o.status = %s'''.format(condition=conditions), (item[0]),as_list=1)
			else:
				if "Vendor" in frappe.get_roles(frappe.session.user):
					permission=frappe.db.sql('''select group_concat(concat('"',for_value,'"')) as business from `tabUser Permission` where user=%s and allow="Business" and o.status = %s''',(frappe.session.user, item[0]),as_dict=1)
					if permission and permission[0].business:
						conditions +=' and o.business in ({business})'.format(business=permission[0].business)
					
				total_order = frappe.db.sql('''select sum(o.total_amount) from 
					`tabOrder` o where o.naming_series !="SUB-ORD-" and o.status = %s and o.docstatus=1 {condition} '''.format(condition=conditions), (item[0]),as_list=1)
			datasets.append(total_order[0][0])
	chart = {
		"data": {
			'labels': status,
			'datasets': [{'name': 'Orders','values': datasets}]
		}
	}
	chart["type"] = "line"
	return chart
