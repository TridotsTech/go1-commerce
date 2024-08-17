# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import date, timedelta, datetime
from frappe.query_builder import DocType, Count

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		_("Customer Name") + ":Data:200",
		_("Customer Email") + ":Data: 250",
		_("No.Of Orders Placed") + ":Int:200",
	]



def get_data(filters):
	Order = DocType('Order')
	conditions = []
	if filters.get('from_date'):
		conditions.append(Order.order_date >= filters.get('from_date'))
	if filters.get('to_date'):
		conditions.append(Order.order_date <= filters.get('to_date'))
	query = (
		frappe.qb.from_(Order)
		.select(
			Order.customer_name,
			Order.customer_email,
			Count('*').as_('count')
		)
		.where(
			(Order.docstatus == 1) &
			(Order.status != 'Cancelled') &
			(Order.restaurant_status != 'Declined') &
			*conditions
		)
		.groupby(Order.customer_name, Order.customer_email)
		.orderby(Count('*'), order="Order.desc")
	)
	
	results = query.run(as_dict=True)
	return results