# Copyright (c) 2023, Tridots Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder import DocType, Field

def execute(filters=None):
	columns, data = get_columns(),get_data(filters)
	return columns, data

def get_columns():
	col__ = []
	col__.append(_("Customer Id")+":Link/Customers:200")
	col__.append(_("Customer Name")+":Data:200")
	col__.append(_("Customer Email")+":Data:250")
	col__.append(_("Customer Phone No")+":Phone:200")
	col__.append(_("Total Order Count")+":Data:200")
	col__.append(_("Total Amount")+":Currency:120")
	

	return col__

def get_data(filters):
	Customer = DocType('Customer')
	Order = DocType('Order')
	query = (
		frappe.qb.from_(Customer)
		.select(
			Customer.name,
			Customer.full_name,
			Customer.email,
			Customer.phone,
			frappe.qb.from_(Order)
			.select(frappe.qb.fn.Count(Order.name))
			.where(Order.customer == Customer.name)
			.where(Order.docstatus == 1)
			.as_("total_order_count"),
			frappe.qb.from_(Order)
			.select(frappe.qb.fn.Sum(Order.total_amount))
			.where(Order.customer == Customer.name)
			.where(Order.docstatus == 1)
			.as_("total_amount")
		)
		.where(Customer.customer_status == 'Approved')
	)
	if filters.get('from_date'):
		query = query.where(frappe.qb.from_(Order).select(frappe.qb.fn.Min(Order.order_date)) >= filters.get('from_date'))

	if filters.get('to_date'):
		query = query.where(frappe.qb.from_(Order).select(frappe.qb.fn.Max(Order.order_date)) <= filters.get('to_date'))

	query = query.groupby(
		Customer.name,
		Customer.full_name,
		Customer.email,
		Customer.phone
	)

	result = query.run(as_list=True)
	return result