# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data
def get_columns(filters):
	columns =  [
		_("Order Id") + ":Link/Order:120",
		_("Order Date") + ":Date:120",
		_("Shipping Method") + ":Data:120",
		_("Payment Status") + ":Data:120",
		_("Payment Method") + ":Data:120",
		]

	columns.append(_("Customer Name") + ":Data:180")
	columns.append(_("Customer Email") + ":Data:180")
	columns.append(_("Customer Phone") + ":Data:180")
	columns.append(_("Order Total") + ":Currency:120")
	return columns

def get_data(filters):
	conditions = ' and o.ship_date = "{0}"'.format(filters.get('date'))
	
	query = 'select o.name, o.order_date,o.shipping_method_name,o.payment_status, o.payment_method_name,o.customer_name,o.customer_email,o.phone,'
	query += 'o.total_amount from `tabOrder` o inner join `tabShipping Method` SM on SM.name=o.shipping_method where o.docstatus = 1 and SM.is_deliverable=0 and SM.show_in_website=1 {condition}'
	data = frappe.db.sql(query.format(condition=conditions), as_list=1)
	return data

def get_orders(filters):
	conditions = ' and o.ship_date = "{0}"'.format(filters.get('date'))
		
	query = 'select o.name from `tabOrder` o where o.docstatus = 1 {condition}'
	data = frappe.db.sql(query.format(condition=conditions), as_list=1)
	return data

def get_chart_data(orders,data, filters):
	if not orders:
		orders = []
	datasets = []
	for item in orders:
		if item:
			conditions = ' and o.order_date = "{0}"'.format(filters.get('date'))
				
			query = 'select o.total_amount from `tabOrder` o where o.docstatus = 1 and o.name=%s {condition}'
			data = frappe.db.sql(query.format(condition=conditions), (item[0]), as_list=1)
			datasets.append(data[0][0])
	chart = {
		"data": {
			'labels': orders,
			'datasets': [{'name': 'Order','values': datasets}]
		}
	}
	chart["type"] = "line"
	return chart

@frappe.whitelist()
def get_shipping_methods(doctype,txt,searchfield,start,page_len,filters):
	try:	
		query='SELECT name, shipping_method_name from `tabShipping Method` where is_deliverable=0 and show_in_website=1 order by display_order'
		results=frappe.db.sql('''{query}'''.format(query=query))
		return results
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.report.daily_sales_report.daily_sales_report.get_shipping_methods") 
