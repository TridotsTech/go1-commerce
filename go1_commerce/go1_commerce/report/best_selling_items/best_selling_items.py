# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = best_selling(filters)
	return columns, data

def get_columns():
	
	return[
			"Product Id" + ":Link/Product:180",
			"Product Name" + ":Data:200",
			"SKU" + ":Data:200",
			"Sold Qty" + ":Int:180"
		]

def best_selling(filters):	
	condition=''
	if filters.get('from_date'):
		condition+=' and O.order_date>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		condition+=' and O.order_date<="%s"' % filters.get('to_date')
	if filters.get('business'):
		condition+=' and O.business ="%s"' % filters.get('business')
	
	return frappe.db.sql('''select p.name,p.item,p.sku,sum(o.quantity) as qty from `tabProduct` p left join `tabOrder Item` o on o.item=p.name and o.parenttype="Order" left join `tabOrder` O on o.parent=O.name where O.payment_status = 'Paid' {condition}  group by p.name having sum(o.quantity)>0 order by qty desc'''.format(condition=condition))

def get_items():	
	
	return frappe.db.sql('''select p.name from `tabProduct` p left join `tabOrder Item` o on o.item=p.name and o.parenttype="Order"  group by p.name having sum(o.quantity)>0 ''')

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
			
			total_order= frappe.db.sql('''select sum(o.quantity) as qty from `tabProduct` p left join `tabOrder Item` o on o.item=p.name and o.parenttype="Order"  where p.name=%s group by p.name having sum(o.quantity)>0 order by qty desc''',(item[0]))

				
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
