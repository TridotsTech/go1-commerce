# -*- coding: utf-8 -*-
# Copyright (c) 2021, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from go1_commerce.go1_commerce.doctype.customers.customers \
    import update_password
from frappe.utils import nowdate
from go1_commerce.utils.setup import get_settings


class ZoneUser(Document):
	def validate(self):
		if self.get('__islocal'):
			check_users = frappe.db.get_all('User', filters={'name': self.email})
			if check_users:
				frappe.throw(frappe._('E-Mail ID already registered.'))
		if self.phone_number:
			self.validate_phone()
		if self.set_new_password:
			self.validate_pwd()

	def validate_phone(self):
		if not self.phone_number.isnumeric():
			frappe.throw(frappe._('Phone Number must contain only numbers'))
		import re
		res = re.search('(?=.*\d)[\d]', str(self.phone_number))
		if not res:
			frappe.throw(frappe._('Phone number must contain only numbers'))
		order_settings = get_settings('Order Settings')
		if order_settings.enable_phone_validation:
			if len(str(self.phone_number)) != int(order_settings.max_phone_length):
				frappe.throw(frappe._('Phone Number must contain {0} digits').\
										format(order_settings.max_phone_length))

	def validate_pwd(self):
		order_settings = get_settings('Order Settings')
		if len(self.set_new_password) < int(order_settings.min_password_length):
			frappe.throw(frappe._('Password must contain {0} digits').format(order_settings.min_password_length))
		from go1_commerce.go1_commerce.doctype.order_settings.\
			order_settings import validate_password
		validate_password(self.set_new_password)

	def on_update(self):
		if self.set_new_password:
			self.new_password = self.set_new_password
		if self.email:
			s = frappe.db.get_all("User", fields=["full_name","email","mobile_no"] , 
										filters={"email": self.email},limit_page_length=1)
			if s:				
				update_user(self)
				if self.set_new_password:
					update_password(new_password=self.new_password,user=self.name)
					frappe.db.set_value('Zone User', self.name, 'set_new_password','')
			else:					
				d = frappe.db.sql(	"""	SELECT name 
										FROM `tabUser` 
										WHERE email=%(email)s
									""", {'email': self.email})
				if d: 							
					frappe.throw("Email id already registered")
				else:					
					user = insert_user(self)
					if user:
						if self.new_password:
							newupdate = update_password(new_password=self.new_password, old_password=None,
                                   						user=self.email)								
							frappe.db.set_value('Zone User', self.name, 'set_new_password','')
	
def update_user(self):	
	frappe.db.set_value("User", self.email , "first_name", self.full_name)
	frappe.db.set_value("User", self.email , "mobile_no", self.phone_number)
	add_arole(self,'Zone Manager')
		

@frappe.whitelist()
def add_arole(self,role):	
	user_role=frappe.db.get_all('Has Role',filters={'parent':self.email,'role':role})
	if not user_role:
		result = frappe.get_doc({"doctype": "Has Role",
								"name": nowdate(),
								"parent": self.email,
								"parentfield": "roles",
								"parenttype": "User",
								"role": role
								}).insert()


@frappe.whitelist(allow_guest=True)
def insert_user(self):	
	result= frappe.get_doc({
		"doctype": "User","email": self.email,"first_name": self.full_name,
		"mobile_no": self.phone_number,"send_welcome_email": 0
	}).insert(ignore_permissions=True)
	add_arole(self,'Zone Manager')
	return result