# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = products_never_purchased(filters)
	return columns, data


def get_columns():
	return[
			"Product Id" + ":Link/Product:120",
			"Product Name" + ":Data:250"
		]

def products_never_purchased(filters):	
	try:
		products1 = frappe.db.sql('''select item from `tabOrder Item` where parenttype = "Order" group by item''',as_dict = 1)
		return frappe.db.sql('''select p.name, p.item from `tabProduct` p where p.is_active=1 and p.status='Approved' and p.name not in (select item from `tabOrder Item` where parenttype = "Orders") ''', as_list = 1)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.report.products_never_purchased")


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
