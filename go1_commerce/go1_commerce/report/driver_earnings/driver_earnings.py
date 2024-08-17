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
	if "Admin" in frappe.get_roles(frappe.session.user) or "System Manager" in frappe.get_roles(frappe.session.user):
		return [
			_("Order Id") + ":Link/Order:200",
			_("Order Date") + ":Date",
			_("Driver Name") + ":Data: 250",
			_("Driver Email") + ":Data:250",
			_("Driver Phone") + ":Data:200",
			_("Earnings") + ":Currency:200"
		]
	if "Driver" in frappe.get_roles(frappe.session.user):
		columns = [
			_("Order Id") + ":Link/Order:200",
			_("Order Date") + ":Data: 250",]
		columns += [	
			_("Customer") + ":Data:250",
			_("Earnings") + ":Currency:200"
		]
		return columns

def get_data(filters):
    roles = frappe.get_roles(frappe.session.user)
    
    Order = DocType('Order')
    Drivers = DocType('Drivers')
    Business = DocType('Business')

    query = frappe.qb.from_(Order)
    conditions = []

    if "Admin" in roles or "System Manager" in roles:
        query = query.left_join(Drivers).on(Order.driver == Drivers.name)
        if filters.get('driver'):
            conditions.append(Order.driver == filters.get('driver'))
        if filters.get('from_date'):
            conditions.append(Order.order_date >= filters.get('from_date'))
        if filters.get('to_date'):
            conditions.append(Order.order_date <= filters.get('to_date'))
        query = query.select(
            Order.name,
            Order.order_date,
            Drivers.driver_name,
            Order.driver,
            Drivers.driver_phone,
            Order.total_driver_charges
        ).where(
            (Order.driver.isnotnull()) &
            (Order.docstatus == 1) &
            *conditions
        )
        
    elif "Driver" in roles:
        query = query.left_join(Business).on(Business.name == Order.business)
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
	