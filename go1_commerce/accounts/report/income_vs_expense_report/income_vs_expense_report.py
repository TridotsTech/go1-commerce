# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.query_builder import DocType, Field, functions as fn

month_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	return columns, data, None, chart

def get_columns():
	return [
		{
			"fieldname": "month",
			"fieldtype": "Data",
			"label": _("Month"),
			"width": 120
		},
		{
			"fieldname": "income_amount",
			"fieldtype": "Currency",
			"label": _("Income Amount"),
			"width": 150
		},
		{
			"fieldname": "expense_amount",
			"fieldtype": "Currency",
			"label": _("Expense Amount"),
			"width": 150
		},
		{
			"fieldname": "balance_amount",
			"fieldtype": "Currency",
			"label": _("Balance Amount"),
			"width": 150
		}
	]

def get_data(filters):
	data = []
	
	income_entries = get_payment_entries(filters, "Receive")
	expense_entries = get_payment_entries(filters, "Pay")
	for item in month_list:
		income, expense, balance = 0, 0, 0
		check_income = next((x for x in income_entries if x.month == item), None)
		check_expense = next((x for x in expense_entries if x.month == item), None)
		if check_income:
			income = float(check_income.amount or 0)
		if check_expense:
			expense = float(check_expense.amount or 0)
		balance = income - expense
		data.append([item, income, expense, balance])
	return data

def get_payment_entries(filters, payment_type):
	PaymentEntry = DocType('Payment Entry')
	query = (
		frappe.qb.from_(PaymentEntry)
		.select(
			fn.monthname(PaymentEntry.posting_date).as_('month'),
			fn.sum(PaymentEntry.paid_amount).as_('amount')
		)
		.where(PaymentEntry.docstatus == 1)
		.where(PaymentEntry.payment_type == payment_type)
	)
	if filters.get('year'):
		query.where(
			Function('YEAR', 'posting_date') == filters.get('year')
		)
	query = query.groupby(fn.monthname(PaymentEntry.posting_date))
	result = query.run(as_dict=True)
	return result



def get_chart(data):
	income_list = [x[1] for x in data]
	expense_list = [x[2] for x in data]
	datasets = [
		{
			"title": "Income",
			"name": "Income",
			"values": income_list
		},
		{
			"title": "Expense",
			"name": "Expense",
			"values": expense_list
		}
	]

	return {
		"data": {
			"labels": month_list,
			"datasets": datasets
		},
		"type": "bar"
	}

@frappe.whitelist()
def get_year_list():
	year_list_query = (
	    frappe.qb.from_("tabPayment Entry")
	    .select(Function('YEAR', 'posting_date'))
	    .distinct()
	    .orderby(Function('YEAR', 'posting_date').desc())
	)
	year_list = year_list_query.run(as_dict=True)
	year_list = [row['YEAR(posting_date)'] for row in year_list]
	return year_list