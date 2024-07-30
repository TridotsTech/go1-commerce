# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns=get_columns()
	data=order_report(filters)
	order_result = get_orders(filters)
	orders = []
	if order_result:
		for item in order_result:
			orders.append(item)
	chart = get_chart_data(orders,data, filters)
	return columns, data, None, chart

def get_columns():
	return[
		"Order ID" + ":Link/Order:150",
		"Order Status" + ":Data:120",
		"Payment Status" + ":Data:120",
		"Customer Name" + ":Data:120",
		"Order Date" + ":Date:120",
		"Total Amount" + ":Currency:120"
	]
	
def order_report(filters):
	condition = ' and o.order_date = "{0}"'.format(filters.get('date'))

	vendor_order = frappe.db.sql('''select o.name, o.status, o.payment_status, concat(o.first_name,' ' ,o.last_name), 
	 o.order_date, o.total_amount from `tabOrder` o inner join `tabOrder Delivery Slot` od on od.order=o.name where o.docstatus=1 {condition} '''.format(condition=condition), as_list=1)
	return vendor_order

def get_orders(filters):
	condition = ' and o.order_date = "{0}"'.format(filters.get('date'))
	vendor_order = frappe.db.sql('''select o.name from `tabOrder` o inner join `tabOrder Delivery Slot` od on od.order=o.name where o.docstatus=1 {condition} '''.format(condition=condition), as_list=1)
	return vendor_order

def get_chart_data(orders,data, filters):
	condition = ' and o.order_date = "{0}"'.format(filters.get('date'))
	if not orders:
		orders = []
	datasets = []
	for item in orders:
		if item:
			vendor_order = frappe.db.sql('''select o.total_amount from `tabOrder` o inner join `tabOrder Delivery Slot` od on od.order=o.name where o.docstatus=1 and o.name=%s {condition}'''.format(condition=condition),(item[0]), as_list=1)
			datasets.append(vendor_order[0][0])
	chart = {
		"data": {
			'labels': orders,
			'datasets': [{'name': 'Order','values': datasets}]
		}
	}
	chart["type"] = "line"
	return chart

