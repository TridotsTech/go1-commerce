# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate,nowdate,date_diff,add_to_date
from datetime import datetime, timedelta
from frappe.query_builder import DocType, Order

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [
		_("Order Id") + ":Link/Order:200",
		_("Order Date") + ":Data: 250",]
	columns += [	
		_("Customer") + ":Data:250",
		_("Earnings") + ":Currency:200"
	]
	return columns

def get_data(filters):
    Order = DocType('Order')
    Business = DocType('Business')

    query = frappe.qb.from_(Order)
    query = query.left_join(Business).on(Order.business == Business.name)
    conditions = []
    if filters.get('from_date'):
        conditions.append(Order.order_date >= filters.get('from_date'))
    if filters.get('to_date'):
        conditions.append(Order.order_date <= filters.get('to_date'))
    query = query.select(
        Order.name,
        Order.order_date,
        Order.customer_name,
        Order.total_driver_charges
    ).where(
        (Order.driver == frappe.session.user) &
        (Order.docstatus == 1) &
        *conditions
    ).orderby(Order.creation, order=Order.desc)
    data = query.run(as_list=True)
    return data