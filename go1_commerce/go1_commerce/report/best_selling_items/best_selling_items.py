# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.query_builder import DocType,  Order
from frappe.query_builder.functions import  Sum

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = best_selling(filters)
	return columns, data

def get_columns():
	
	return[
			"Product Id" + ":Link/Product:180",
			"Product Name" + ":Data:200",
			"SKU" + ":Data:200",
			"Sold Qty" + ":Int:180"
		]

def best_selling(filters):	
	Product = DocType("Product")
	OrderItem = DocType("Order Item")
	Orders = DocType("Order")
	query = (
		frappe.qb.from_(Product)
		.left_join(OrderItem).on(OrderItem.item == Product.name)
		.left_join(Orders).on(Orders.name == OrderItem.parent)
		.select(
			Product.name,
			Product.item,
			Product.sku,
			Sum(OrderItem.quantity).as_('qty')
		)
		.where(Orders.payment_status == "Paid")
	)
	
	if filters.get('from_date'):
		query = query.where(Orders.order_date >= filters.get('from_date'))
	if filters.get('to_date'):
		query = query.where(Orders.order_date <= filters.get('to_date'))
	query = query.groupby(Product.name)
	query = query.having(Sum(OrderItem.quantity) > 0)
	query = query.orderby(Sum(OrderItem.quantity), order=Order.desc)
	return query.run(as_dict=True)

def get_items():
	Product = DocType("Product")
	OrderItem = DocType("Order Item")	
	query = (
		frappe.qb.from_(Product)
		.left_join(OrderItem).on((OrderItem.item == Product.name )&(OrderItem.parenttype == "Order"))
		.select(Product.name)
		.groupby(Product.name)
		.having(Sum(OrderItem.quantity) > 0)
	)
	result = query.run(as_dict=True)
	return result

def get_chart_data(items,data):
	
	if not items:
		items = []
	datasets = []
	for item in items:
		if item:
			Product = DocType("Product")
			OrderItem = DocType("Order Item")
			query = (
				frappe.qb.from_(Product)
				.left_join(OrderItem).on((OrderItem.item == Product.name )&(OrderItem.parenttype == "Order"))
				.select(Sum('tabOrder Item.quantity').as_('qty'))
				.where(Product.name == item[0])
				.groupby(Product.name)
				.having(Sum(OrderItem.quantity) > 0)
				.orderby(Sum(OrderItem.quantity), order=Order.desc)
			)
			total_order = query.run(as_dict=True)
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
