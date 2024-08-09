# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
from go1_commerce.accounts.api import make_payment as _make_payment
from go1_commerce.go1_commerce.v2.orders import get_today_date

class Shipment(Document):
	def on_update_after_submit(self):
		if self.status == 'Delivered':
			frappe.db.set_value('Shipment', self.name, 'delivered_date', get_today_date(replace=True))
			products = []
			for item in self.items:
				products.append({'product': item.item, 'orderid': self.document_name})


def make_payment(name):
	doc = frappe.get_doc('Shipment', name)
	order = frappe.get_doc(doc.document_type, doc.document_name)
	if order.payment_status != 'Paid':
		order_id = order.name if doc.document_type == 'Order' else order.order_reference
		res = _make_payment(order=order_id, mode_of_payment=order.payment_type, amount=doc.order_total)
		if res:
			if doc.document_type == 'Vendor Orders':
				order.payment_status = 'Paid' if order.total_amount == doc.order_total else 'Partially Paid'
				order.save(ignore_permissions=True)
			frappe.db.set_value('Shipment', name, 'payment_status', 'Paid')
	else:
		frappe.db.set_value('Shipment', name, 'payment_status', 'Paid')
	return {'status': 'Success'}
