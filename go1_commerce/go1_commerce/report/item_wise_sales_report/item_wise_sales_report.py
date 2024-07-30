# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

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
	conditions =""
	if filters.get('business'):
		conditions += ' and o.business = "{0}"'.format(filters.get('business'))
	if filters.get('from_date'):
		conditions+=' and o.order_date>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		conditions+=' and o.order_date<="%s"' % filters.get('to_date')
	data = frappe.db.sql('''select o.name, o.order_date, i.item, i.item_name, o.customer, o.customer_name, o.customer_email, o.phone, i.price, i.quantity from 
	`tabOrder` o inner join `tabOrder Item` i on i.parent=o.name where o.docstatus = 1 and o.payment_status = 'Paid' {condition} group by o.name order by o.name desc'''.format(condition=conditions), as_list=1)
	return data

