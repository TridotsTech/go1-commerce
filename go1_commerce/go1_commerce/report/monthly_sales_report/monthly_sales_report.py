# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import date, timedelta, datetime
from frappe.query_builder import DocType, Field

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
	Order = DocType('tabOrder')
	query = frappe.qb.from_(Order) 
		.select(
			Order.order_date,
			frappe.qb.fn.Count(Order.name).as_('count'),
			frappe.qb.fn.Sum(Order.total_amount).as_('total_amount'),
			Order.payment_method_name
		) 
		.where(
			(Order.docstatus == 1) &
			(Order.payment_status == 'Paid') &
			(frappe.qb.fn.Year(Order.order_date) == filters.get('year')) &
			(frappe.qb.fn.MonthName(Order.order_date) == filters.get('month'))
		)
	if filters.get('from_date'):
		query = query.where(Order.order_date >= filters.get('from_date'))
	if filters.get('to_date'):
		query = query.where(Order.order_date <= filters.get('to_date'))
	data = query.groupby(Order.order_date).run(as_dict=True)
	
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
    Order = DocType('tabOrder')
    query = frappe.qb.from_(Order) 
        .select(
            Order.order_date,
            frappe.qb.fn.Sum(Order.total_amount).as_('total_amount')
        ) 
        .where(
            (Order.docstatus == 1) &
            (frappe.qb.fn.Year(Order.order_date) == filters.get('year')) &
            (frappe.qb.fn.MonthName(Order.order_date) == filters.get('month'))
        )
    
    data = query.groupby(Order.order_date).run(as_dict=True)
    
    return data
