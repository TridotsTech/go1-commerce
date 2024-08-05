# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	if not filters: filters={}
	columns=get_columns()
	data=customer_report(filters)
	chart = get_chart_data(filters)
	return columns, data, None, chart

def get_columns():
	columns = [
		"Order Number" + ":Link/Order:120",
		"Order Date" + ":Date:120",
		"Order Status" + ":Data:120",
		"Payment Status" + ":Data:120",
		"Customer Name" + ":Data:120",
		"Customer Email" + ":Data:120",
		"Customer Phone" + ":Data:120",
		
		"Total Amount" + ":Currency:120",
		"Order From" + ":Data:120",
		
	]
	
	return columns
	
def customer_report(filters):
	condition=''
	if filters.get('from_date'):
		condition+=' and order_date>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		condition+=' and order_date<="%s"' % filters.get('to_date')
	if filters.get('status'):
		condition+=' and status="%s"' % filters.get('status')
	if filters.get('payment_status'):
		condition+=' and payment_status="%s"' % filters.get('payment_status') 
	if filters.get('order_from'):
		condition+=' and order_from="%s"' % filters.get('order_from') 
	customer_order = frappe.db.sql('''select name, order_date,status, payment_status, concat(first_name,' ' ,last_name), 
		 customer_email,phone,total_amount,order_from from 
		`tabOrder` where naming_series !="SUB-ORD-" and docstatus=1 {condition} '''.format(condition=condition),as_list=1)
	return customer_order

def get_chart_data(filters):
	labels = datasets = []
	data = get_chart_data_source(filters)
	labels = [x[0] for x in data]
	value = [x[1] for x in data]
	datasets.append({
		"title": "Order",
		"values": value
		})
	return {
		"data": {
			'labels': labels,
			'datasets': datasets
		},
		"type": "line"
	}

def get_chart_data_source(filters):
	condition=''
	if filters.get('from_date'):
		condition+=' and order_date>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		condition+=' and order_date<="%s"' % filters.get('to_date')
	if filters.get('status'):
		condition+=' and status="%s"' % filters.get('status')
	if filters.get('payment_status'):
		condition+=' and payment_status="%s"' % filters.get('payment_status') 
	if filters.get('order_from'):
		condition+=' and order_from="%s"' % filters.get('order_from') 
	customer_order = frappe.db.sql('''select order_date,total_amount from 
		`tabOrder` where naming_series !="SUB-ORD-" and docstatus=1 {condition} '''.format(condition=condition),as_list=1)
	
	return customer_order



