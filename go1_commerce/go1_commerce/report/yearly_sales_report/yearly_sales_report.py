# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	chart = get_chart_data(filters)
	return columns, data, None, chart

def get_columns(filters):
	return [
		_("Business") + ":Link/Business:120",
		_("Business Name") + ":Data: 150",
		_("Month") + ":Data:120",
		_("Total Orders") + ":Int:120",
		_("Total Sales") + ":Currency:120",
		_("Payment Method") + ":Data:120",
	]

def get_data(filters):
	conditions = ''
	conditions = ' and year(o.creation) = "{0}"'.format(filters.get('year'))
	if filters.get('from_date'):
		conditions+=' and o.order_date>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		conditions+=' and o.order_date<="%s"' % filters.get('to_date')
	query = '''select 
	monthname(o.order_date), count(o.name), sum(o.total_amount), o.payment_method_name from `tabOrder` o where o.docstatus = 1 and o.payment_status = 'Paid' {condition}
	group by monthname(o.order_date), o.business order by o.creation'''.format(condition=conditions)
	data = frappe.db.sql(query, as_list=1)
	return data

def get_chart_data(filters):
	labels = datasets = []
	data = get_chart_data_source(filters)
	labels = [x[0] for x in data]
	value = [x[1] for x in data]
	datasets.append({
		"title": "Sales",
		"values": value
		})
	return {
		"data": {
			'labels': labels,
			'datasets': datasets
		},
		"type": "bar",
		"colors": ['red']
	}

def get_chart_data_source(filters):
	conditions = ' and year(o.creation) = "{0}"'.format(filters.get('year'))
	query = '''select monthname(str_to_date(m.month,'%m')), 
		sum(o.total_amount), sum(o.commission_amt) from (select 1 as month union select 2 as month 
		union select 3 as month union select 4 as month union select 5 as month union select 6 as month 
		union select 7 as month union select 8 as month union select 9 as month union select 10 as month 
		union select 11 as month union select 12 as month) m left join `tabOrder` o on 
		m.month = month(o.order_date) and o.docstatus = 1 {condition}
		group by m.month'''.format(condition=conditions)
	data = frappe.db.sql(query, as_list=1)
	return data
