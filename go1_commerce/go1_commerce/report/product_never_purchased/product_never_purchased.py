# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.query_builder import DocType

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = products_never_purchased(filters)
	return columns, data


def get_columns():
	return[
			"Product Id" + ":Link/Product:120",
			"Product Name" + ":Data:250"
		]

def products_never_purchased(filters):	
	try:
		Product = DocType('Product')
		OrderItem = DocType('Order Item')
		subquery = (
			frappe.qb.from_(OrderItem)
			.select(OrderItem.item)
			.where(OrderItem.parenttype == 'Orders')
		)
		products_query = (
			frappe.qb.from_(Product)
			.select(Product.name, Product.item)
			.where(
				(Product.is_active == 1) &
				(Product.status == 'Approved') &
				(Product.name.isin(subquery))
			)
		)
		results = products_query.run(as_list=True)
		return results
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.report.products_never_purchased")
