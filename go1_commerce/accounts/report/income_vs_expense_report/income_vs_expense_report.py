# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

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
	condition = ' and year(posting_date) = "%s"' % filters.get('year')
	
	income_entries = frappe.db.sql('''select monthname(posting_date) as month, sum(paid_amount) as amount from `tabPayment Entry` where docstatus = 1 and payment_type = "Receive" {} group by monthname(posting_date)'''.format(condition), as_dict=1)
	expense_entries = frappe.db.sql('''select monthname(posting_date) as month, sum(paid_amount) as amount from `tabPayment Entry` where docstatus = 1 and payment_type = "Pay" {} group by monthname(posting_date)'''.format(condition), as_dict=1)
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
	year_list = frappe.db.sql_list('''select distinct year(posting_date) from `tabPayment Entry` order by posting_date desc''')
	return year_list