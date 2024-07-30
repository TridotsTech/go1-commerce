# Copyright (c) 2023, Tridots Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns, data = get_columns(),get_data(filters)
	return columns, data

def get_columns():
	col__ = []
	col__.append(_("Customer Id")+":Link/Customers:200")
	col__.append(_("Customer Name")+":Data:200")
	col__.append(_("Customer Email")+":Data:250")
	col__.append(_("Customer Phone No")+":Phone:200")
	col__.append(_("Total Order Count")+":Data:200")
	col__.append(_("Total Amount")+":Currency:120")
	

	return col__

def get_data(filters):
	condition = ''
	if filters.get('from_date'):
		condition += f" AND ORD.order_date >= '{filters.get('from_date')}' "
	if filters.get('to_date'):
		condition += f" AND ORD.order_date <= '{filters.get('to_date')}' "

	query = frappe.db.sql("""
							SELECT C.name,C.full_name ,
							C.email, C.phone,
							(SELECT COUNT(ORD.name) FROM `tabOrder` ORD WHERE ORD.customer = C.name AND ORD.docstatus = 1)AS total_order_count,
							(SELECT SUM(ORD.total_amount) FROM `tabOrder` ORD WHERE ORD.customer = C.name AND ORD.docstatus = 1)AS total_amount

							FROM `tabCustomers` C
							WHERE C.customer_status = 'Approved' {conditions}
							GROUP BY C.name,C.full_name,C.email, C.phone
						""".format(conditions=condition), as_list=1)
	return query