# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.query_builder import DocType, Order

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data
	

def get_columns():
	columns = [_("Order ID") + ":Data:150",]
	columns += [	
		_("Order Date") + ":Date:90",
		_("Item ID") + ":Data:140",
		_("Item Name") + ":Data:180",
		_("Customer ID") + ":Data:120",
		_("Customer Name") + ":Data:120",
		_("Customer Email") + ":Data:180", 
		_("Customer Phone") + ":Data:100",
		_("Price") + ":Currency:140",
		_("Quantity") + ":Int:140"
	]
	return columns

def get_data(filters):
	Orders = DocType('Order')
	OrderItem = DocType('Order Item')

	query = frappe.qb.from_(Orders)
	query = query.inner_join(OrderItem).on(Orders.name == OrderItem.parent)

	conditions = []
	
	

	query = query.select(
		Orders.name,
		Orders.order_date,
		OrderItem.item,
		OrderItem.item_name,
		Orders.customer,
		Orders.customer_name,
		Orders.customer_email,
		Orders.phone,
		OrderItem.price,
		OrderItem.quantity
	).where(
		(Orders.docstatus == 1) &
		(Orders.payment_status == 'Paid')
	)
	if filters.get('from_date'):
		query.where(Orders.order_date >= filters.get('from_date'))
	if filters.get('to_date'):
		query.where(Orders.order_date <= filters.get('to_date'))
	query.groupby(Orders.name).orderby(Orders.name, order=Order.desc)
	data = query.run(as_list=True)
	return data

