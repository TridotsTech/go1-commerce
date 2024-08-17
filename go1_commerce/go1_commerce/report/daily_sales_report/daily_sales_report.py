# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.query_builder import DocType

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data
def get_columns(filters):
	columns =  [
		_("Order Id") + ":Link/Order:120",
		_("Order Date") + ":Date:120",
		_("Order Status") + ":Data:120",
		_("Payment Status") + ":Data:120",
		_("Payment Method") + ":Data:120",
		]
	columns.append(_("Customer Name") + ":Data:180")
	columns.append(_("Customer Email") + ":Data:180")
	columns.append(_("Customer Phone") + ":Data:180")
	columns.append(_("Order Total") + ":Currency:120")
	return columns

def get_data(filters):
	Order = DocType("Order")
	date_condition = Order.order_date == filters.get('date')
	query = (
		frappe.qb.from_(Order)
		.select(
			Order.name,
			Order.order_date,
			Order.status,
			Order.payment_status,
			Order.payment_method_name,
			Order.customer_name,
			Order.customer_email,
			Order.phone,
			Order.total_amount
		)
		.where(
			(Order.docstatus == 1) &
			date_condition
		)
	)
	data = query.run(as_list=True)
	return data

def get_orders(filters):
	Order = DocType("Order")
	date_condition = Order.order_date == filters.get('date')
	query = (
		frappe.qb.from_(Order)
		.select(Order.name)
		.where(
			(Order.docstatus == 1) &
			date_condition
		)
	)
	data = query.run(as_list=True)
	return data

def get_chart_data(orders,data, filters):
	if not orders:
		orders = []
	datasets = []
	Order = DocType("Order")
	for item in orders:
		if item:
			date_condition = Order.order_date == filters.get('date')
			query = (
				frappe.qb.from_(Order)
				.select(Order.total_amount)
				.where(
					(Order.docstatus == 1) &
					(Order.name == item[0]) &
					date_condition
				)
			)
			data = query.run(as_list=True)
			if data:
				datasets.append(data[0][0])
	chart = {
		"data": {
			'labels': orders,
			'datasets': [{'name': 'Order','values': datasets}]
		}
	}
	chart["type"] = "line"
	return chart

