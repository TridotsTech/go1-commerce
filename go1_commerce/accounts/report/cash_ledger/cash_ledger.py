# Copyright (c) 2023, Tridots Tech and contributors
# For license information, please see license.txt

# import frappe

import frappe
from frappe.query_builder import DocType, Field

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return[
			
			"Cash Collection Date" + ":Date:200",
			"Cash Approval Date" + ":Date:200",
			"Customer" + ":Link/Customers:120",
			"Customer Name" + ":Data:120",
			"Against" + ":Data",
			"Against Reference" + ":Data",
			"Order ID" + ":Data",
			"Amount" + ":Currency:80"

		]

def get_data(filters):
	PaymentEntry = DocType('Payment Entry')
	PaymentReference = DocType('Payment Reference')
	Customers = DocType('Customers')
	query = (
		frappe.qb.from_(PaymentEntry).as_('tm')
		.inner_join(PaymentReference).as_('tt').on('tm.name = tt.parent')
		.inner_join(Customers).as_('cs').on('cs.name = tm.party')
		.select(
			Field('""').as_('cash_collection_date'),
			PaymentEntry.modified.as_('cash_approval_date'),
			PaymentEntry.party.as_('customer'),
			Customers.first_name.as_('customer_name'),
			PaymentReference.reference_doctype.as_('against'),
			PaymentReference.reference_name.as_('against_reference'),
			PaymentReference.reference_name.as_('order_id'),
			PaymentEntry.paid_amount.as_('amount')
		)
		.where(PaymentEntry.mode_of_payment == 'Cash')
		.where(PaymentReference.reference_doctype != 'Wallet Transaction')
		.where(PaymentEntry.docstatus == 1)
		.where(PaymentEntry.payment_type == 'Receive')
	)

	if filters.get('from_date'):
		query = query.where(PaymentEntry.modified >= filters.get('from_date'))
	if filters.get('to_date'):
		query = query.where(PaymentEntry.modified <= filters.get('to_date'))

	query = query.orderby(PaymentEntry.creation, order=Order.desc)

	ret_data = query.run(as_dict=True)
	for x in ret_data:
		if x.against=="Sales Invoice":
			x.order_id = frappe.db.get_value("Sales Invoice",x.against_reference,"reference")
		order_delivery = frappe.db.get_all("Order Delivery Slot",filters={"order":x.order_id},fields=['order_date'])
		if order_delivery:
			x.cash_collection_date = order_delivery[0].order_date
		else:
			x.cash_collection_date = frappe.db.get_value("Order",x.order_id,"order_date")
	return ret_data
