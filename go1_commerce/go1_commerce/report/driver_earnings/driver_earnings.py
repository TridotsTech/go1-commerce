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
	if "Admin" in frappe.get_roles(frappe.session.user) or "System Manager" in frappe.get_roles(frappe.session.user):
		conditions = ''
		if filters.get('driver'):
			conditions += ' and o.driver = "%s"' % filters.get('driver')
		if filters.get('from_date'):
			conditions+=' and o.order_date>="%s"' % filters.get('from_date')
		if filters.get('to_date'):
			conditions+=' and o.order_date<="%s"' % filters.get('to_date')
		data = frappe.db.sql('''select o.name,o.order_date, d.driver_name, o.driver, d.driver_phone, o.total_driver_charges from 
				`tabOrder` o inner join `tabDrivers` d on d.name = o.driver where o.driver is not null and o.docstatus=1 {condition} '''.format(condition=conditions),as_list=1)
		return data
	if "Driver" in frappe.get_roles(frappe.session.user):
		conditions = ''
		if filters.get('from_date'):
			conditions+=' and O.order_date>="{0}"'.format(filters.get('from_date'))
		if filters.get('to_date'):
			conditions+=' and O.order_date<="{0}"'.format(filters.get('to_date'))
		data = frappe.db.sql(''' select O.name,O.order_date,O.customer_name,O.total_driver_charges from `tabOrder` O inner join `tabBusiness` B on B.name=O.business where O.driver = %(driver)s and O.docstatus = 1 and O.order_date>=%(from_date)s and O.order_date<=%(to_date)s order by O.creation desc''',{'driver':frappe.session.user,'conditions':conditions,"from_date":filters.get('from_date'),"to_date":filters.get('to_date')},as_list=1)
		return data
	