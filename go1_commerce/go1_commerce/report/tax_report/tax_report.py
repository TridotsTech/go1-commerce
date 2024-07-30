# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = tax_report()
	items = []
	item_data = get_vendors()
	if item_data:
		for item in item_data:
			items.append(item)
	chart = get_chart_data(items,data)
	return columns, data, None , chart

def get_columns():
	return[
		"Vendor Id" + ":Data:120",
		"Vendor Name" + ":Data:120",
		"Total Amount" + ":Currency:120",
		"Total Tax Amount" + ":Currency:120",
		"Orders" + ":Int:140"
	]

def tax_report():
	
	result=frappe.db.sql('''select b.name,b.restaurant_name,
		sum(v.total_amount) as sales, sum(v.total_tax_amount) as tax, count(p.name) as count from `tabBusiness` b 
	 	left join `tabVendor Orders` p on p.business=b.name left join `tabVendor Orders` v on v.business=b.name group by b.name''')
	return result

def get_vendors():
	
	result=frappe.db.sql('''select name, restaurant_name from `tabBusiness`''')
	return result

def get_chart_data(items,data):
	if not items:
		items = []
	datasets = []
	for item in items:
		if item:
			total_order=frappe.db.sql('''select sum(v.total_tax_amount) as tax from `tabBusiness` b 
	 	left join `tabVendor Orders` p on p.business=b.name left join `tabVendor Orders` v on v.business=b.name where b.name=%s group by b.name''',(item[0]))
			
			if total_order:
				data = total_order[0][0]
			else:
				data = []
			datasets.append(data)
	
	chart = {
		"data": {
			'labels': items,
			'datasets': [{'name': 'Tax','values': datasets}]
		}
	}
	chart["type"] = "line"
	return chart
