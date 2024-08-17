# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Concat

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
	Order = DocType('Order')
	OrderDeliverySlot = DocType('Order Delivery Slot')
	date_filter = filters.get('date')
	query = (
		frappe.qb.from_(Order)
		.inner_join(OrderDeliverySlot).on(Order.name == OrderDeliverySlot.order)
		.select(
			Order.name,
			Order.status,
			Order.payment_status,
			(Order.first_name + ' ' + Order.last_name).as_('full_name'),
			Order.order_date,
			Order.total_amount
		)
		.where(Order.docstatus == 1)
	)
	if date_filter:
		query = query.where(Order.order_date == date_filter)
	vendor_order = query.run(as_list=True)
	return vendor_order

def get_orders(filters):
	Order = DocType('Order')
	OrderDeliverySlot = DocType('Order Delivery Slot')
	date_filter = filters.get('date')
	query = (
		frappe.qb.from_(Order)
		.inner_join(OrderDeliverySlot).on(Order.name == OrderDeliverySlot.order)
		.select(Order.name)
		.where(Order.docstatus == 1)
	)
	if date_filter:
		query = query.where(Order.order_date == date_filter)
	vendor_order = query.run(as_list=True)
	return vendor_order
	
def order_report(filters):
	Order = DocType("Order")
	OrderDeliverySlot = DocType("Order Delivery Slot")
	date_condition = (Order.order_date == filters.get('date'))
	query = (
		frappe.qb.from_(Order)
		.join(OrderDeliverySlot)
		.on(Order.name == OrderDeliverySlot.order)
		.select(
			Order.name,
			Order.status,
			Order.payment_status,
			Concat(Order.first_name, " ", Order.last_name).as_("customer_name"),
			Order.order_date,
			Order.total_amount
		)
		.where(
			(Order.docstatus == 1) &
			date_condition
		)
	)
	
	vendor_order = query.run(as_list=True)
	return vendor_order

def get_orders(filters):
	Order = DocType("Order")
	OrderDeliverySlot = DocType("Order Delivery Slot")
	date_condition = (Order.order_date == filters.get('date'))
	query = (
		frappe.qb.from_(Order)
		.join(OrderDeliverySlot)
		.on(Order.name == OrderDeliverySlot.order)
		.select(Order.name)
		.where(
			(Order.docstatus == 1) &
			date_condition
		)
	)
	vendor_order = query.run(as_list=True)
	return vendor_order

def get_chart_data(orders,data, filters):
	Order = DocType("Order")
	OrderDeliverySlot = DocType("Order Delivery Slot")
	date_condition = (Order.order_date == filters.get('date'))
	
	datasets = []
	
	if not orders:
		orders = []

	for item in orders:
		if item:
			query = (
				frappe.qb.from_(Order)
				.join(OrderDeliverySlot)
				.on(Order.name == OrderDeliverySlot.order)
				.select(Order.total_amount)
				.where(
					(Order.docstatus == 1) &
					(Order.name == item[0]) &
					date_condition
				)
			)
			vendor_order = query.run(as_list=True)
			if vendor_order:
				datasets.append(vendor_order[0][0])
	chart = {
		"data": {
			'labels': orders,
			'datasets': [{'name': 'Order','values': datasets}]
		}
	}
	chart["type"] = "line"
	return chart

