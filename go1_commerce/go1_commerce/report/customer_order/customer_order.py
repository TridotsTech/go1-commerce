# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.query_builder import DocType, Field

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
	Order = DocType('Order')
	query = (
		frappe.qb.from_(Order)
		.select(
			Order.name,
			Order.order_date,
			Order.status,
			Order.payment_status,
			(Order.first_name + ' ' + Order.last_name).as_('customer_name'),
			Order.customer_email,
			Order.phone,
			Order.total_amount,
			Order.order_from
		)
		.where(Order.naming_series != "SUB-ORD-")
		.where(Order.docstatus == 1)
	)
	if filters.get('from_date'):
		query = query.where(Order.order_date >= filters.get('from_date'))

	if filters.get('to_date'):
		query = query.where(Order.order_date <= filters.get('to_date'))

	if filters.get('status'):
		query = query.where(Order.status == filters.get('status'))

	if filters.get('payment_status'):
		query = query.where(Order.payment_status == filters.get('payment_status'))

	if filters.get('order_from'):
		query = query.where(Order.order_from == filters.get('order_from'))
	customer_order = query.run(as_list=True)
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
	Order = DocType('Order')
	query = (
		frappe.qb.from_(Order)
		.select(
			Order.order_date,
			Order.total_amount
		)
		.where(Order.naming_series != "SUB-ORD-")
		.where(Order.docstatus == 1)
	)
	if filters.get('from_date'):
		query = query.where(Order.order_date >= filters.get('from_date'))

	if filters.get('to_date'):
		query = query.where(Order.order_date <= filters.get('to_date'))

	if filters.get('status'):
		query = query.where(Order.status == filters.get('status'))

	if filters.get('payment_status'):
		query = query.where(Order.payment_status == filters.get('payment_status'))

	if filters.get('order_from'):
		query = query.where(Order.order_from == filters.get('order_from'))
	customer_order = query.run(as_list=True)
	return customer_order



