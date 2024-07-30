# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class CustomerAddress(Document):
	def validate(self):
		maps = frappe.get_single('Google Settings')
		address = ''
		if maps.enable:	
			if self.address:
				address += self.address+','
			if self.city:
				address += self.city + ','
			if self.state:
				address += self.state + ' '
			if self.zipcode:
				address += str(self.zipcode)		
			validate_geo_location(self, address)

@frappe.whitelist()
def validate_geo_location(self,address):
	try:
		if not self.latitude or not self.longitude:				
			from go1_commerce.go1_commerce.api\
				import get_geolocation
			location_data=get_geolocation(address)
			if location_data:
				self.latitude=location_data['latitude']
				self.longitude=location_data['longitude']
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.customer_address.validate_geo_location") 
	