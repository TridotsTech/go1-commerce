# -*- coding: utf-8 -*-
# Copyright (c) 2021, Tridots Tech and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType

class ShipmentBag(Document):
	def on_update(self):
		from go1_commerce.go1_commerce.api\
			import calculate_shipment_charges
		total_amount = calculate_shipment_charges(self.name)
		self.total_shipping_charges = total_amount
		ShipmentBag = DocType('Shipment Bag')
		query = frappe.qb.update(ShipmentBag).set(
			ShipmentBag.total_shipping_charges, total_amount
		).where(ShipmentBag.name == name)
		query.run()
		frappe.db.commit()