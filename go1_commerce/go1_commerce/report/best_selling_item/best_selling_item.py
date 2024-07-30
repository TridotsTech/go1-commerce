# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = best_selling(filters)
	items = []
	item_data = get_items()
	if item_data:
		for item in item_data:
			items.append(item)
	chart = get_chart_data(items,data)
	return columns, data, None , chart


def get_columns():
	return[
			"Product Id" + ":Link/Product:120",
			"Product Name" + ":Data:120",
			"Sold Qty" + ":Int:120"
		]

def best_selling(filters):	
	return frappe.db.sql('''select p.name,p.item,sum(o.quantity) as qty from `tabProduct` p left join `tabOrder Item` o on o.item=p.name and o.parenttype="Order"  group by p.name having sum(o.quantity)>0 order by qty desc''')

def get_items():	
	return frappe.db.sql('''select p.name from `tabProduct` p left join `tabOrder Item` o on o.item=p.name and o.parenttype="Order"  group by p.name having sum(o.quantity)>0 order by p.name desc''')

@frappe.whitelist(allow_guest=True)
def check_domain(domain_name):
	try:
		from frappe.core.doctype.domain_settings.domain_settings import get_active_domains
		domains_list=get_active_domains()
		domains=frappe.cache().hget('domains','domain_constants')
		if not domains:
			domains=get_domains_data()
		if domains[domain_name] in domains_list:
			return True
		return False
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.api.check_domain")


def get_chart_data(items,data):
	
	if not items:
		items = []
	datasets = []
	for item in items:
		if item:
			
			query = 'select ifnull(sum(o.quantity), 0) as qty from `tabProduct` p left join `tabOrder Item` o on o.item=p.name and o.parenttype="Order" where p.name="{item}"'.format(item =item[0])
			
			total_order = frappe.db.sql('''{query}'''.format(query=query),as_list=1)
			
			if total_order:
				data = total_order[0][0]
			else:
				data = []
			datasets.append(data)
	
	chart = {
		"data": {
			'labels': items,
			'datasets': [{'name': 'Qty','values': datasets}]
		}
	}
	chart["type"] = "line"
	return chart
