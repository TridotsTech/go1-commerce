# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = shop_report()
	items = []
	item_data = get_vendors()
	if item_data:
		for item in item_data:
			items.append(item)
	chart = get_chart_data(items,data)
	return columns, data, None , chart

def get_columns():
	return[
		"Vendor Id" + ":Link/Business:120",
		"Vendor Name" + ":Data:120",
		"Total Products" + ":Int:120",
		"Sales Amount" + ":Currency:120",
		"Commission Amount" + ":Currency:140"
	]
	
def shop_report():
	result=frappe.db.sql('''select b.name,b.restaurant_name,count(p.name) as products_count,
		sum(v.total_amount) as sales,sum(v.commission_amt) as commission from `tabBusiness` b 
	 	left join `tabProduct` p on p.restaurant=b.name left join `tabVendor Orders` v on v.business=b.name group by b.name''')
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
			total_order=frappe.db.sql('''select sum(v.total_amount) as sales from `tabBusiness` b 
	 	left join `tabProduct` p on p.restaurant=b.name left join `tabVendor Orders` v on v.business=b.name and b.name=%s group by b.name''',(item[0]))
			if total_order:
				data = total_order[0][0]
			else:
				data = []
			datasets.append(data)
	
	chart = {
		"data": {
			'labels': items,
			'datasets': [{'name': 'Sales Amount','values': datasets}]
		}
	}
	chart["type"] = "line"
	return chart
