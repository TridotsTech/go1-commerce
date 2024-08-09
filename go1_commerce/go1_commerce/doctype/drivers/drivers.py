# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from go1_commerce.go1_commerce.doctype.customers.customers import update_password
from frappe.utils import nowdate
from go1_commerce.utils.setup import get_settings

class Drivers(Document):
	def validate(self):
		if self.get('__islocal'):
			check_drivers = frappe.db.get_all('User', filters = {'name': self.driver_email})
			if check_drivers:
				user_role=frappe.db.get_all('Has Role',
											filters = {'parent':self.driver_email,'role':'Driver'})
				if not user_role:
					add_arole(self,'Driver')
				else:
					frappe.throw(frappe._('E-Mail ID already registered.'))
		if self.driver_phone:
			self.validate_phone()
		if self.set_new_password:
			self.validate_pwd()
		self.validate_status_change()

	def validate_status_change(self):
		prev_status = frappe.db.get_value('Drivers', self.name, 'working_status')
		if self.working_status == 'Available' and prev_status == 'On Duty':
			check_orders_list = frappe.db.sql('''SELECT name 
												FROM `tabOrder` 
												WHERE driver = %(driver)s 
													AND status NOT IN ("Completed", "Cancelled")
											''', {'driver': self.name}, as_dict = 1)
			if check_orders_list:
				frappe.throw(frappe._('Status cannot be changed to Available.'))
		

	def validate_phone(self):
		import re
		res = re.search('(?=.*\d)[\d]', str(self.driver_phone))
		if not res:
			frappe.throw(frappe._('Phone number must contain only numbers'))
		order_settings = get_settings('Order Settings')
		if order_settings.enable_phone_validation:
			if len(str(self.driver_phone)) != int(order_settings.max_phone_length):
				frappe.throw(frappe._('Phone Number must contain {0} digits').format(
																		order_settings.max_phone_length
																	))

	def validate_pwd(self):
		order_settings = get_settings('Order Settings')
		if len(self.set_new_password) < int(order_settings.min_password_length):
			frappe.throw(frappe._('Password must contain {0} digits').format(
																	order_settings.min_password_length
																))
		from go1_commerce.go1_commerce.\
			doctype.order_settings.order_settings import validate_password
		validate_password(self.set_new_password)

	def on_update(self):	
		if self.driver_status == 'Offline':
			self.working_status = "Unavailable"
		if self.set_new_password:
			self.new_password = self.set_new_password
		if self.driver_email:
			s = frappe.db.get_all("User", 
								fields = ["full_name","email","mobile_no"] , 
								filters = {"email": self.driver_email},
								limit_page_length = 1)
			if s:				
				update_user(self)
				if self.set_new_password:
					update_password(new_password=self.new_password,user=self.name)
					frappe.db.set_value('Drivers', self.name, 'set_new_password','')
			else:					
				d = frappe.db.sql("""SELECT name 
									FROM `tabUser` 
									WHERE email = %(email)s
								""",{'email':self.driver_email})
				if d:
					user_role=frappe.db.get_all('Has Role',
									filters = {'parent':self.driver_email,'role':'Driver'}) 							
					if not user_role:
						add_arole(self,'Driver')
					else:
						frappe.throw("Email id already registered")
				else:					
					user = insert_user(self)
					if user:
						if self.new_password:
							newupdate = update_password(
														new_password = self.new_password, 
														old_password = None,
														user = self.driver_email
													)								
							frappe.db.set_value('Drivers', self.name, 'set_new_password','')
		frappe.publish_realtime('check_active_drivers', {
															'name': self.name, 
															'driver_status': self.driver_status, 
															'working_status': self.working_status
														})
def update_user(self):	
	add_arole(self,'Driver')
		

def add_arole(self,role):	
	user_role = frappe.db.get_all('Has Role', filters = {'parent':self.driver_email,'role':role})
	if not user_role:
		result = frappe.get_doc({
									"doctype": "Has Role",
									"name": nowdate(),
									"parent": self.driver_email,
									"parentfield": "roles",
									"parenttype": "User",
									"role": role
								}).insert()
		
def insert_user(self):	
	result = frappe.get_doc({
								"doctype": "User",
								"email": self.driver_email,
								"first_name": self.driver_name,
								"mobile_no": self.driver_phone,
								"send_welcome_email": 0,
								"gender": self.gender,
								"birth_date": self.birth_date,
								"location": self.location
							}).insert(ignore_permissions = True)
	add_arole(self,'Driver')
	return result		


def get_shipping_manager():
	shipping_info = ''
	installed_apps = frappe.db.sql(''' SELECT * 
										FROM `tabModule Def` 
										WHERE app_name = 'shipping_providers'
									''', as_dict = True)
	if len(installed_apps) > 0:
		user = frappe.session.user
		if "Shipping Manager" in frappe.get_roles(user):
			shipping_provider = frappe.db.get_all('Shipping Provider',
													filters = {'email':user},
													fields = ['name'])
			if shipping_provider:
				shipping_info = shipping_provider[0].name
	return shipping_info

def get_query_condition(user):
	installed_apps = frappe.db.sql(''' SELECT * 
										FROM `tabModule Def` 
										WHERE app_name = 'shipping_providers'
									''', as_dict = True)
	if len(installed_apps) > 0:
		if not user: user = frappe.session.user
		if "Shipping Manager" in frappe.get_roles(user):
			shipping_provider = frappe.db.get_all('Shipping Provider',
													filters = {'email':user},
													fields = ['name'])
			if shipping_provider:
				return "(`tabDrivers`.shipping_provider='{0}'  )".format(
																			shipping_provider[0].name
																		)

def has_permission(doc, user):
	installed_apps = frappe.db.sql(''' SELECT * 
										FROM `tabModule Def` 
										WHERE app_name = 'shipping_providers'
									''', as_dict = True)
	if len(installed_apps) > 0:
		if not user: user = frappe.session.user
		if "Shipping Manager" in frappe.get_roles(user):
			shipping_provider = frappe.db.get_all('Shipping Provider',
                                         filters = {'email':user},
                                         fields = ['name'])
			if shipping_provider:
				if doc.shipping_provider == shipping_provider[0].name:
					return True
				else:
					return False


