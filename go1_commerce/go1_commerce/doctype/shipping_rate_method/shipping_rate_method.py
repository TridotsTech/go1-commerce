# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class ShippingRateMethod(Document):
	def validate(self):
		if not self.title:
			self.title = self.shipping_rate_method
		if self.is_active:
			if self.shipping_rate_method == 'Shipping By Distance' or \
						self.shipping_rate_method == 'Shipping By Distance and Total':
				maps =frappe.get_single('Google Settings')
				if not maps.api_key:
					frappe.throw(frappe._('Please provide google map client key to make {0} as default').format(self.name))
				if not maps.enable:
					frappe.throw(frappe._('Please enable google maps'))
		
	def on_update(self):		
		if self.is_active:
			filts = {'name':('!=',self.name),'is_active':1}
			active = frappe.db.get_all('Shipping Rate Method',filters=filts)
			if active:
				for item in active:
					frappe.db.set_value('Shipping Rate Method', item.name, 'is_active', 0)