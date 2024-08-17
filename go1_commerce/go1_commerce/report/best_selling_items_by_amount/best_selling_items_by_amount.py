# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.query_builder import DocType, Field, Order
from frappe.query_builder.functions import Sum

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = best_selling(filters)
	return columns, data

def get_columns():
	
	return[
			"Product Id" + ":Link/Product:150",
			"Product Name" + ":Data:200",
			"Amount" + ":Currency:180"
		]

def best_selling(filters):	
	product = DocType("Product")
	order_item = DocType("Order Item")
	order = DocType("Order")
	query = (
		frappe.qb.from_(product)
		.left_join(order_item) 
		.on((order_item.item == product.name) & (order_item.parenttype == "Order"))
		.left_join(order) 
		.on((order_item.parent == order.name))
		.select(
			product.name,
			product.item,
			Sum(order_item.amount).as_("amt")
		)
		.where(order.payment_status == 'Paid')
	)
	if filters.get('from_date'):
		query = query.where(order.order_date >= filters.get('from_date'))
	if filters.get('to_date'):
		query = query.where(order.order_date <= filters.get('to_date'))
	query = (
		query.groupby(product.name)
		.having(Sum(order_item.amount) > 0)
		.orderby(Sum(order_item.amount), order=Order.desc)
	)
	return query.run(as_dict=True)

def get_items():	
	product = DocType("Product")
	order_item = DocType("Order Item")
	query = (
		frappe.qb.from_(product)
		.left_join(order_item)
		.on((order_item.item == product.name) & (order_item.parenttype == "Order"))
		.select(product.name)
		.groupby(product.name)
		.having(Sum(order_item.amount) > 0)
	)
	return query.run(as_dict=True)

def get_chart_data(items,data):
	
	if not items:
		items = []
	datasets = []
	for item in items:
		if item:
			
			product = DocType("Product")
			order_item = DocType("Order Item")
			query = (
				frappe.qb.from_(product)
				.left_join(order_item)
				.on((order_item.item == product.name) & (order_item.parenttype == "Order"))
				.select(Sum(order_item.amount).as_("amt"))
				.where(product.name == item_name)
				.groupby(product.name)
				.having(Sum(order_item.amount) > 0)
				.orderby(Sum(order_item.amount),order=Order.desc)
			)
			total_order = query.run(as_list=True)
			if total_order:
				data = total_order[0][0]
			else:
				data = []
			datasets.append(data)
	
	chart = {
		"data": {
			'labels': items,
			'datasets': [{'name': 'Qty','values': datasets}]
		}
	}
	chart["type"] = "line"
	return chart
