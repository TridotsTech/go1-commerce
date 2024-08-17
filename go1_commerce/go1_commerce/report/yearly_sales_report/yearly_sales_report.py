# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Sum, MonthName, StrToDate

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
		conditions &= frappe.qb.functions.Year(Order.creation) == filters.get('year')
	if filters.get('from_date'):
		conditions &= Order.order_date >= filters.get('from_date')
	if filters.get('to_date'):
		conditions &= Order.order_date <= filters.get('to_date')
	query = (
		frappe.qb.from_(Order)
		.select(
			MonthName(Order.order_date),
			Count(Order.name),
			Sum(Order.total_amount),
			Order.payment_method_name
		)
		.where(conditions)
		.groupby(MonthName(Order.order_date))
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
	months = frappe.qb.from_(
		frappe.qb.union_all(
			*(frappe.qb.select(frappe.qb.terms.Literal(i).as_('month')) for i in range(1, 13))
		).as_('m')
	)
	conditions = (Order.docstatus == 1)
	if filters.get('year'):
		conditions &= frappe.qb.functions.Year(Order.creation) == filters.get('year')
	query = (
		months.left_join(Order)
		.on(frappe.qb.functions.Month(Order.order_date) == months.month)
		.select(
			MonthName(StrToDate(months.month, '%m')),
			Sum(Order.total_amount)
		)
		.where(conditions)
		.groupby(months.month)
	)
	data = query.run(as_list=True)
	return data