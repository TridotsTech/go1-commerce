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
	chart = get_chart_data(filters)
	return columns, data, None, chart

def get_columns():
	return [
		_("Date") + ":Data:120",
		_("Total Orders") + ":Int:120",
		_("Total Sales") + ":Currency:120",
		_("Payment Method") + ":Data:120",
	]

def get_data(filters):
	conditions = ' and year(o.order_date) = "{0}" and monthname(o.order_date) = "{1}"'.format(filters.get('year'), filters.get('month'))
	if filters.get('from_date'):
		conditions+=' and o.order_date>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		conditions+=' and o.order_date<="%s"' % filters.get('to_date')
	data = frappe.db.sql('''select o.order_date, count(o.name), sum(o.total_amount), o.payment_method_name from 
	`tabOrder` o where o.docstatus = 1 and o.payment_status = 'Paid' {condition} group by o.order_date'''.format(condition=conditions), as_list=1)
	return data

def days_cur_month(filters):
	from datetime import date, timedelta
	long_month_name = filters.get('month')
	datetime_object = datetime.strptime(long_month_name, "%B")
	month_number = datetime_object.month
	import calendar
	year = str(filters.get('year'))
	month = int(month_number)
	num_days = calendar.monthrange(year, month)[1]
	days = [datetime.date(year, month, day) for day in range(1, num_days+1)]
	return days

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
		"colors": ['#428b46', '#ffa3ef', 'light-blue']
	}

def get_chart_data_source(filters):
	conditions = ' and year(o.order_date) = "{0}" and monthname(o.order_date) = "{1}"'.format(filters.get('year'), filters.get('month'))
	data = frappe.db.sql('''select o.order_date, sum(o.total_amount) from 
		`tabOrder` o where o.docstatus = 1 {condition} group by o.order_date'''.format(condition=conditions), as_list=1)
	return data
