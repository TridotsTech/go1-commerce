# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.query_builder import DocType, Order

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data
def get_columns(filters):
	columns =  [
		_("Order Id") + ":Link/Order:120",
		_("Order Date") + ":Date:120",
		_("Shipping Method") + ":Data:120",
		_("Payment Status") + ":Data:120",
		_("Payment Method") + ":Data:120",
		]

	columns.append(_("Customer Name") + ":Data:180")
	columns.append(_("Customer Email") + ":Data:180")
	columns.append(_("Customer Phone") + ":Data:180")
	columns.append(_("Order Total") + ":Currency:120")
	return columns

def get_data(filters):
	Orders = DocType('Order')
	ShippingMethod = DocType('Shipping Method')
	conditions = []
	if filters.get('date'):
		conditions.append(Orders.ship_date == filters.get('date'))
	
	query = frappe.qb.from_(Orders)
	query = query.inner_join(ShippingMethod).on(Orders.shipping_method == ShippingMethod.name)
	query = query.select(
		Orders.name,
		Orders.order_date,
		Orders.shipping_method_name,
		Orders.payment_status,
		Orders.payment_method_name,
		Orders.customer_name,
		Orders.customer_email,
		Orders.phone,
		Orders.total_amount
	).where(
		(Orders.docstatus == 1) &
		(ShippingMethod.is_deliverable == 0) &
		(ShippingMethod.show_in_website == 1) &
		*conditions
	)
	data = query.run(as_list=True)
	return data

def get_orders(filters):
	Orders = DocType('Order')
	conditions = []
	if filters.get('date'):
		conditions.append(Orders.ship_date == filters.get('date'))
	
	query = frappe.qb.from_(Orders)
	query = query.select(Orders.name).where(
		(Orders.docstatus == 1) &
		*conditions
	)
	data = query.run(as_list=True)
	return data

def get_chart_data(orders,data, filters):
	if not orders:
		return []

	Order = DocType('Order')

	datasets = []
	for item in orders:
		if item:
			conditions = []
			if filters.get('date'):
				conditions.append(Order.order_date == filters.get('date'))
			
			query = frappe.qb.from_(Order).select(Order.total_amount).where(
				(Order.docstatus == 1) &
				(Order.name == item[0]) &
				*conditions
			)
			
			result = query.run(as_list=True)
			if result:
				datasets.append(result[0][0])
	
	chart = {
		"data": {
			'labels': orders,
			'datasets': [{'name': 'Order','values': datasets}]
		}
	}
	chart["type"] = "line"
	return chart

@frappe.whitelist()
def get_shipping_methods(doctype,txt,searchfield,start,page_len,filters):
	try:	
		query = frappe.qb.from_('tabShipping Method')
			.select('name', 'shipping_method_name')
			.where(
				(frappe.qb.Field('is_deliverable') == 0) &
				(frappe.qb.Field('show_in_website') == 1)
			)
			.orderby('display_order')
		results = query.run(as_dict=True)
		return results
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.report.daily_sales_report.daily_sales_report.get_shipping_methods") 
