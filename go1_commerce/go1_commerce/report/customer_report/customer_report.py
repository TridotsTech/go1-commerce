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
	columns = [
		_("Id") + ":Link/Customers:120",
		_("Customer Name") + ":Data: 200",
		_("Customer Email") + ":Data:200",
		_("Customer Phone") + ":Data:120"]
	if "loyalty" in frappe.get_installed_apps():
		columns += [
		_("Loyalty Points") + ":Data:140"
		]
	columns += [
		_("Creation Date") + ":Data:200",
		_("Social Media Source") + ":Data:150",
		]
	
	return columns

def get_data(filters):
	conditions = ''
	if filters.get('from_date'):
		conditions+=' and CAST(c.creation AS DATE)>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		conditions+=' and CAST(c.creation AS DATE)<="%s"' % filters.get('to_date')
	loyalty_join_query = ''
	loyalty_columns_query = ''
	if "loyalty" in frappe.get_installed_apps():
		loyalty_columns_query = ',ifnull(sum(LP.loyalty_points),0) as total_points'
		loyalty_join_query = ' left join `tabLoyalty Point Entry` LP on LP.customer=c.name and LP.party_type="Customers"'
	data = frappe.db.sql('''select c.name, c.full_name, c.email, c.phone {loyalty_columns_query}, CAST(c.creation AS DATE), group_concat(s.provider) from 
		`tabCustomers` c left join `tabUser Social Login` s on s.parent = c.user_id and s.provider != 'frappe' {loyalty_join_query} 
		where c.name != '' and c.naming_series != 'GC-' {condition} group by c.name order by c.creation desc'''.format(condition=conditions,loyalty_columns_query=loyalty_columns_query,loyalty_join_query=loyalty_join_query), as_list=1)
	return data
