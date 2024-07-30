# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import date, timedelta, datetime

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
	conditions = ''
	if filters.get('from_date'):
		conditions+=' and O.order_date>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		conditions+=' and O.order_date<="%s"' % filters.get('to_date')
	data = frappe.db.sql('''select O.customer_name,O.customer_email,COUNT(*) as count FROM `tabOrder` O WHERE docstatus=1 and status<>"Cancelled" and restaurant_status<>"Declined" {condition} group by O.customer_name,O.customer_email ORDER BY count DESC'''.format(condition=conditions), as_list=1)
	return data


