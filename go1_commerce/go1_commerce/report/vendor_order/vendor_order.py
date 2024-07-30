# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, items, data = [], [], []
	columns=get_columns()
	data=vendororder_report(filters)
	item_data = get_vendors(filters)
	if item_data:
		for item in item_data:
			items.append(item)
	chart = get_chart_data(items,data, filters)
	return columns, data, None , chart

def get_columns():
	return[
		"Order ID" + ":Link/Vendor Orders:150",
		"Order Date" + ":Date:120",
		"Order Status" + ":Data:120",
		"Payment Status" + ":Data:120",
		"Customer Name" + ":Data:120",
		"Customer Email" + ":Data:120",
		"Customer Phone" + ":Data:120",
		"Total Amount" + ":Currency:120",
		"Order From" + ":Data:120",
	]
	
def vendororder_report(filters):
	condition=''
	if filters.get('from_date'):
		condition+=' and order_date>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		condition+=' and order_date<="%s"' % filters.get('to_date')
	if filters.get('status'):
		condition+=' and status="%s"' % filters.get('status')
	if filters.get('payment_status'):
		condition+=' and payment_status="%s"' % filters.get('payment_status') 
	
	if "Vendor" in frappe.get_roles(frappe.session.user):
		shop_user=frappe.db.get_all('Shop User',filters={'name':frappe.session.user},fields=['name','restaurant'])
		if shop_user and shop_user[0].restaurant:
			condition+=' and business="%s"' % shop_user[0].restaurant
	vendor_order = frappe.db.sql('''select name,order_date, status, payment_status, concat(first_name,' ' ,last_name),customer_email,phone, 
	  total_amount,order_from from `tabVendor Orders` where docstatus=1 {condition} '''.format(condition=condition), as_list=1)
	return vendor_order

def get_vendors(filters):
	condition=''
	if filters.get('from_date'):
		condition+=' and order_date>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		condition+=' and order_date<="%s"' % filters.get('to_date')
	if filters.get('status'):
		condition+=' and status="%s"' % filters.get('status')
	if filters.get('payment_status'):
		condition+=' and payment_status="%s"' % filters.get('payment_status') 
	result=frappe.db.sql('''select order_date from `tabVendor Orders` where docstatus=1 {condition} '''.format(condition=condition), as_list=1)
	return result

def get_chart_data(items,data, filters):
	condition=''
	if filters.get('status'):
		condition+=' and status="%s"' % filters.get('status')
	if filters.get('payment_status'):
		condition+=' and payment_status="%s"' % filters.get('payment_status') 
	if not items:
		items = []
	datasets = []
	for item in items:
		if item:
			if "Vendor" in frappe.get_roles(frappe.session.user):
				shop_user=frappe.db.get_all('Shop User',filters={'name':frappe.session.user},fields=['name','restaurant'])
				if shop_user and shop_user[0].restaurant:
					condition+=' and business="%s"' % shop_user[0].restaurant
			total_order = frappe.db.sql('''select sum(total_amount) as amount from `tabVendor Orders` where docstatus=1 and order_date=%s {condition} '''.format(condition=condition), (item[0]), as_list=1)
			if total_order:
				data = total_order[0][0]
			else:
				data = []
			datasets.append(data)
	
	chart = {
		"data": {
			'labels': items,
			'datasets': [{'name': 'Orders','values': datasets}]
		}
	}
	chart["type"] = "line"
	return chart
