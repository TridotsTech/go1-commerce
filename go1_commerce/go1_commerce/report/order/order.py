# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns=get_columns()
	data=vendororder_report(filters)
	return columns, data

def get_columns():
	return[
		"Order ID" + ":Link/Vendor Orders:150",
		"Order Status" + ":Data:120",
		"Payment Status" + ":Data:120",
		"Customer Name" + ":Data:120",
		"Order Date" + ":Date:120",
		"Total Amount" + ":Currency:120"
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
	vendor_order = frappe.db.sql('''select name, status, payment_status, concat(first_name,' ' ,last_name), 
	 order_date, total_amount from `tabVendor Orders` where docstatus=1 {condition} '''.format(condition=condition), as_list=1)
	return vendor_order
