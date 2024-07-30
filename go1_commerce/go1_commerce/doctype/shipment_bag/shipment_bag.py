# -*- coding: utf-8 -*-
# Copyright (c) 2021, Tridots Tech and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ShipmentBag(Document):
	def on_update(self):
		from go1_commerce.go1_commerce.api\
			import calculate_shipment_charges
		total_amount = calculate_shipment_charges(self.name)
		self.total_shipping_charges = total_amount
		frappe.db.sql(f""" 	UPDATE 
								`tabShipment Bag` 
							set total_shipping_charges = '{total_amount}' 
							WHERE name='{self.name}' """)
		frappe.db.commit()