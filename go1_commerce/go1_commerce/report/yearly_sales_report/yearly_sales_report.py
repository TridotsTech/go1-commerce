# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.query_builder import DocType, Field
from frappe.query_builder.functions import Count, Sum
from frappe.query_builder.functions import Function

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	chart = get_chart_data(filters)
	return columns, data, None, chart

def get_columns(filters):
	return [
		_("Month") + ":Data:120",
		_("Total Orders") + ":Int:120",
		_("Total Sales") + ":Currency:120",
		_("Payment Method") + ":Data:120",
	]

def get_data(filters):
	Order = DocType('Order')
	conditions = (Order.docstatus == 1) & (Order.payment_status == 'Paid')
	if filters.get('year'):
		conditions &= Function('YEAR', Order.order_date).as_('years')
	if filters.get('from_date'):
		conditions &= Order.order_date >= filters.get('from_date')
	if filters.get('to_date'):
		conditions &= Order.order_date <= filters.get('to_date')
	query = (
		frappe.qb.from_(Order)
		.select(
			Function('MONTHNAME', Order.order_date).as_('month'),
			Count(Order.name),
			Sum(Order.total_amount),
			Order.payment_method_name
		)
		.where(conditions)
		.groupby(Function('MONTHNAME',Order.order_date))
		.orderby(Order.creation)
	)
	data = query.run(as_list=True)
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
	Order = DocType('Order')
	months_query = ' UNION ALL '.join(f"SELECT {i} AS month" for i in range(1, 13))
	months_table = f'({months_query}) AS months'
	conditions = (Order.docstatus == 1)
	if filters.get('year'):
		conditions &= Function('YEAR', Order.order_date) == filters.get('year')
	query = (
		frappe.qb.from_(months_table)
		.left_join(Order)
		.on(Function('MONTH', Order.order_date) == Field('months.month'))
		.select(
			Function('MONTHNAME', Function('STR_TO_DATE', Field('months.month'), '%m')).as_('month_name'),
			Sum(Order.total_amount).as_('total_amount')
		)
		.where(conditions)
		.groupby(Field('months.month'))
	)
	data = query.run(as_list=True)
	return data