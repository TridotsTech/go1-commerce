# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = products_report()
	return columns, data

def get_columns():
	return[
		"Vendor Name" + ":Link/Business:120",
		"Product" + ":Data:120",	
		"Quantity" + ":Int:120"
	]

def products_report():
	report = frappe.db.sql('''select  p.restaurant ,p.item, count(o.name) as qty from `tabProduct` p left join `tabOrder Item` o on o.item=p.name and o.parenttype="Order" group by p.name''', as_list = 1)	
	return report