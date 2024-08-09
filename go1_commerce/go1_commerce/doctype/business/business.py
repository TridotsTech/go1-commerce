# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe,string, random
from frappe.website.website_generator import WebsiteGenerator
from go1_commerce.utils.setup import get_settings

class Business(WebsiteGenerator):
	def validate(self):
		self.lft = ""
		self.rgt = ""
		self.validate_email_type(self.email)
		address=''
		maps = frappe.get_single('Google Settings')
		if maps.enable:	
			if self.address:
				address += self.address+','
			if self.city:
				address += self.city + ','
			if self.state:
				address += self.state + ' '
			if self.zipcode:
				address += self.zipcode		
			validate_geo_location(self, address)
		if self.phone and len(str(self.phone)) > 0:
			self.validate_phone()


	def on_update(self):
		if frappe.db.get_all("Business",{"email":self.get('email'),"name": ("!=", self.name)}):
			frappe.throw(frappe._('Email is already registered.'))
		if frappe.db.get_all("Business",{"phone":self.get('phone'),"name": ("!=", self.name)}):
			frappe.throw(frappe._('Mobile Number is already registered.'))
		if self.set_new_password:
			self.new_password = self.set_new_password
			frappe.db.set_value('Business', self.name, 'new_password', self.set_new_password)	
			su = frappe.db.get_all("Shop User",filters={"email":self.email})
			s_user= frappe.get_doc("Shop User",su[0].name)
			s_user.first_name = self.first_name
			s_user.last_name = self.last_name
			s_user.email = self.email
			s_user.restaurant = self.name
			s_user.role = 'Vendor'
			s_user.mobile_no = self.phone
			s_user.set_new_password = self.new_password
			s_user.new_password = self.new_password
			s_user.save(ignore_permissions=True)


	def validate_phone(self):
		if self.phone == self.alternate_mobile_number:
			frappe.throw(frappe._('Phone Number and Alternate Mobile Number are same'))
		if not self.phone.isnumeric():
			frappe.throw(frappe._('Mobile Number must contain only numbers'))
		if self.alternate_mobile_number:
			if not self.alternate_mobile_number.isnumeric():
				frappe.throw(frappe._('Alternate Mobile Number must contain only numbers'))
		order_settings = get_settings('Order Settings')

		import re
		res = re.search('(?=.*\d)[\d]', str(self.phone))
		if not res:
			frappe.throw(frappe._('Phone number must contain only numbers'))
		if order_settings.enable_phone_validation:
			if len(str(self.phone)) < int(order_settings.min_phone_length):
				frappe.throw(frappe._('Mobile number should be minimum of {0} digits').\
				 											format(order_settings.min_phone_length))
			if len(str(self.phone)) > int(order_settings.max_phone_length):
				frappe.throw(frappe._('Mobile number should be maximum of {0} digits').\
				 											format(order_settings.max_phone_length))


	def validate_email_type(self, email):
		from frappe.utils import validate_email_address
		validate_email_address(email.strip(), True)


	def id_generator(self,size=4, chars=string.ascii_uppercase):
		return ''.join(random.choice(chars) for _ in range(size))

	
def get_all_weekdays():
	Group = frappe.db.get_all('Week Day',fields=['name','day'],order_by='displayorder asc')
	return Group 

def validate_geo_location(self,address):
	try:
		if not self.latitude or not self.longitude:				
			from go1_commerce.go1_commerce.\
															utils.google_maps import get_geolocation
			location_data=get_geolocation(address)
			if location_data:
				self.latitude=location_data['latitude']
				self.longitude=location_data['longitude']
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.business.validate_geo_location") 
	

