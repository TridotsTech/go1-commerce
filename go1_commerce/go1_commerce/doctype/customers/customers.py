# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.utils import nowdate
from frappe import _
from frappe.utils.password import update_password as _update_password
from frappe.model.naming import make_autoname
from frappe.utils.nestedset import NestedSet
from go1_commerce.utils.setup import get_settings, get_settings_value


class Customers(NestedSet):
	nsm_parent_field = 'parent_level'
	nsm_oldparent_field = 'old_parent'

	def autoname(self):
		self.name = make_autoname(self.naming_series+'.#####', doc=self)

	def validate(self):
		if self.user_id:
			if self.disable==1:
				val = 0
			else:
				val = 1
			udoc = frappe.get_doc("User",self.user_id)
			if self.first_name:
				udoc.first_name = self.first_name
			else:
				udoc.first_name = "Hello"
			udoc.enabled = val
			udoc.save(ignore_permissions=True)
			userdoc = frappe.get_doc('User', self.user_id)
			userdoc.set("roles", [])
			check_customer = next((x for x in self.customer_role if x.role == 'Customer'), None)
			if not check_customer:
				self.append('customer_role', {'role': 'Customer'})
			for role in self.customer_role:
				userdoc.append("roles", {"role": role.role})
			userdoc.save(ignore_permissions=True)
		if not self.parent_doctype and self.naming_series != "GC-":
			self.parent_doctype = "Customers"
		self.check_address_phone_pwd()
	
	def check_address_phone_pwd(self):
		if self.naming_series != 'GC-':
			mob_filters = [['phone', '=', self.phone], ['name', '!=', self.name], 
				  ['naming_series', '!=', 'GC-']]
			check_mobile_number = frappe.db.get_all('Customers', filters=mob_filters)
			if check_mobile_number and self.phone and self.phone!="":
				frappe.throw(frappe._('Mobile number already registered.'))
		firstname = ""
		if self.last_name:
			lastname = self.last_name
		if self.first_name:
			firstname = self.first_name
		if not self.full_name:
			self.full_name = firstname
		else:
			if not (self.full_name == firstname):
				self.full_name = firstname
		self.validate_address()
		if self.phone in ['null', 'undefined']:
			self.phone = None
		if self.phone and len(str(self.phone)) > 0:
			self.validate_phone()
		if self.set_new_password:
			self.validate_pwd()


	def on_update(self):
		try:
			if self.naming_series != 'GC-':
				self.set_customer_email()
				self.update_user_and_password()
				
			if self.allow_multiple_address == 0:
				self.update_customer_address()
		except Exception:
			from go1_commerce.utils.utils import other_exception
			other_exception("customers on_update")

	def update_user_and_password(self):
		
		if self.customer_role and len(self.customer_role)>0:
			cart = frappe.db.get_all('Shopping Cart', filters={'customer': self.name})
			if cart:
				for ct in cart:
					doc = frappe.get_doc("Shopping Cart", ct.name)
					doc.save()


	def set_customer_email(self):
		if self.parent_level:
			self.old_parent = self.parent_level
			frappe.db.set_value('Customers', self.name, 'old_parent', self.parent_level)	
		if not self.new_password and not self.set_new_password:
			import string
			import random
			pwd = str(''.join(random.choices(string.ascii_uppercase + string.digits, k=8)))
			self.set_new_password = pwd
		if self.set_new_password:
			self.new_password = self.set_new_password
			frappe.db.set_value('Customers', self.name, 'new_password', self.set_new_password)	
		if not self.email:
			catalog_settings = get_settings('Catalog Settings')
			self.email = self.phone+"@"+catalog_settings.site_name+".com"
			frappe.db.set_value('Customers', self.name, 'email', self.email)
			frappe.db.commit()
		if not self.user_id:
			if self.email:
				email = self.email
				d = frappe.db.sql("""SELECT name 
									FROM `tabUser` 
         							WHERE email=%(email)s""",{'email':email})
				if not d:					
					user = insert_user(self)
					if user:
						if self.set_new_password:
							newupdate = update_password(new_password = self.new_password, 
														old_password = None,user = email)								
							frappe.db.set_value('Customers',self.name,'set_new_password','')
		elif self.user_id:
			s = frappe.db.get_all("User", fields=["full_name","email","mobile_no"] , 
					filters={"email": self.user_id},limit_page_length = 1)
			if s:
				self.user_id = update_user(self)
				if self.new_password:
					keys = frappe.db.get_all("User", fields = ["reset_password_key"] , 
						filters = {"email": self.user_id},limit_page_length = 1)
					if keys:
						update_password(new_password = self.new_password, 
							key = keys[0].reset_password_key, old_password = None,user = self.user_id)
						frappe.db.set_value('Customers',self.name,'set_new_password','')


	def update_customer_address(self):
		check_addr = frappe.db.get_all("Customer Address",
							filters={"address":self.address,
									"city":self.city,
									"state":self.state,
									"country":self.country,
									"zipcode":self.zipcode,
									"parent":self.name})
		if not check_addr and self.address and self.city and self.state and self.zipcode:
			c_addr = frappe.new_doc("Customer Address")
			c_addr.first_name = self.first_name
			c_addr.last_name = self.last_name
			c_addr.address = self.address
			c_addr.city = self.city
			c_addr.state = self.state
			c_addr.country = self.country
			c_addr.zipcode = self.zipcode
			c_addr.landmark = self.landmark
			c_addr.latitude = self.latitude
			c_addr.longitude = self.longitude
			c_addr.phone = self.phone
			c_addr.is_default = 1
			c_addr.parent = self.name
			c_addr.parentfield = "table_6"
			c_addr.parenttype = "Customers"
			c_addr.save(ignore_permissions=True)
			frappe.db.commit()

	def validate_address(self):
		if self.table_6:
			self.validate_geolocation()

	def validate_geolocation(self):
		enable_map = get_settings_value('Order Settings', 'enable_map')
		if enable_map:
			for item in self.table_6:
				if not item.latitude or not item.longitude:
					from go1_commerce.go1_commerce.\
						utils.google_maps import get_geolocation
					address = item.address + ', '+ item.city
					address += (' ' + item.state) if item.state else ''
					address += ' ' + item.country + ' - ' + item.zipcode
					location_data = get_geolocation(address)
					item.latitude = location_data['latitude']
					item.longitude = location_data['longitude']

	def validate_establishment_year(self):
		import re
		res = re.search('(?=.*\d)[\d]', str(self.establishment_year))
		if not res:
			frappe.throw(frappe._('Establishment Year must contain only numbers'))
		if not len(str(self.establishment_year))==4:
			frappe.throw(frappe._('Establishment Year should be 4 digits'))
	def validate_phone(self):
		if self.phone == self.alternate_phone:
			frappe.throw(frappe._('Phone Number and Alternate Phone Number are same'))
		if not str(self.phone).isnumeric():
			frappe.throw(frappe._('Phone Number must contain only numbers'))
		if self.alternate_phone and not str(self.alternate_phone).isnumeric():
			frappe.throw(frappe._('Alternate Phone must contain only numbers'))
		order_settings = get_settings('Order Settings')
		import re
		res = re.search('(?=.*\d)[\d]', str(self.phone))
		if not res:
			frappe.throw(frappe._('Phone number must contain only numbers'))
		if order_settings.enable_phone_validation:
			if len(str(self.phone)) < int(order_settings.min_phone_length):
				frappe.throw(frappe._('Phone number should be minimum of {0} digits').format(order_settings.min_phone_length))
			if len(str(self.phone)) > int(order_settings.max_phone_length):
				frappe.throw(frappe._('Phone number should be maximum of {0} digits').format(order_settings.max_phone_length))
			
   
	def validate_pwd(self):
		order_settings = get_settings('Order Settings')
		'''updated str() in self.set_new_password-by sivaranjani(Jan, 13, 20)'''
		# if order_settings and order_settings.phone_req==0 and order_settings.login_with_password==0:
		if len(str(self.set_new_password)) < int(order_settings.min_password_length):
			frappe.throw(frappe._('Password must contain {0} digits').format(order_settings.min_password_length))

	
def update_user(self):	
	frappe.db.set_value("User", self.user_id , "first_name", self.first_name)
	frappe.db.set_value("User", self.user_id , "gender", self.gender)
	frappe.db.set_value("User", self.user_id , "mobile_no", self.phone)
	frappe.db.set_value("User", self.user_id ,"last_name", self.last_name)
	name=self.first_name
	if self.last_name: name=name+' '+self.last_name
	frappe.db.set_value("User", self.user_id ,"full_name", name)
	user_id = self.user_id
	if self.email and self.user_id.lower() != self.email.lower():
		check_email=frappe.db.get_all('User',filters={'name':self.email})
		if check_email:
			frappe.throw("E-Mail ID Already Registered")
		else:
			try:
				frappe.rename_doc("User", self.user_id, self.email, ignore_if_exists=True)
				self.user_id = self.email
				frappe.db.set_value('Customers',self.name,'user_id',self.email)
			except Exception as e:
				self.user_id = user_id		
			
	add_arole(self, self.user_id)
	return self.user_id


@frappe.whitelist()
def add_arole(self, email=None):
	if not email:
		email = self.email	
	role = frappe.db.get_all('Has Role',fields=['*'],filters={'parent':email,'role':'Customer'})
	if not role:
		result = frappe.get_doc({
			"doctype": "Has Role",
			"name": nowdate(),
			"parent": email,
			"parentfield": "roles",
			"parenttype": "User",
			"role": "Customer"
			}).insert(ignore_permissions = True)


@frappe.whitelist(allow_guest=True)
def insert_user(self):
	from frappe.utils import random_string
	key = random_string(32)
	email = self.email
	phone = self.phone
	first_name = "Hello"
	last_name=""
	if self.first_name:
		first_name = self.first_name
	if self.last_name:
		last_name = self.last_name
	result = frappe.new_doc("User")
	result.email = email
	result.first_name = first_name
	result.last_name = last_name
	result.mobile_no = phone
	result.send_welcome_email = 0
	result.reset_password_key = key
	result.gender = self.gender
	result.simultaneous_sessions = 4
	result.append("roles", {"role": "Customer"})
	result.insert(ignore_permissions=True)
	frappe.db.set_value('Customers',self.name,'user_id',result.name)
	frappe.db.commit()
	return result

@frappe.whitelist(allow_guest=True)
def update_password(new_password, logout_all_sessions=0, key=None, old_password=None,user=None):
	try:
		if not user: user= frappe.session.user
		if not key:
			from frappe.utils import random_string
			key = random_string(32)		
			frappe.db.set_value('User', user, 'reset_password_key', key)
		res = _get_user_for_update_password(key, old_password)
		if res.get('message'):
			return res['message']
		else:
			user = res['user']
		_update_password(user, new_password, logout_all_sessions=int(logout_all_sessions))
		user_doc, redirect_url = reset_user_data(user)
		redirect_to = frappe.cache().hget('redirect_after_login', user)
		if redirect_to:
			redirect_url = redirect_to
			frappe.cache().hdel('redirect_after_login', user)
		if user_doc.user_type == "System User":
			return "/desk"
		else:
			return redirect_url if redirect_url else "/"
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.customers.update_password") 
	
def _get_user_for_update_password(key, old_password):
	try:
		if key:
			user = frappe.db.get_value("User", {"reset_password_key": key})
			if not user:
				return {
					'message': _("Cannot Update: Incorrect / Expired Link.")
				}
		elif old_password:
			frappe.local.login_manager.check_password(frappe.session.user, old_password)
			user = frappe.session.user
		else:
			return

		return {
			'user': user
		}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.customers._get_user_for_update_password") 

def reset_user_data(user):
	try:
		user_doc = frappe.get_doc("User", user)
		redirect_url = user_doc.redirect_url
		user_doc.reset_password_key = ''
		user_doc.redirect_url = ''
		user_doc.save(ignore_permissions=True)
		return user_doc, redirect_url
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.customers.reset_user_data") 

@frappe.whitelist(allow_guest=True)
def check_location(self):
	try:
		if self.table_6:
			for item in self.table_6:
				if not item.lattitude and not item.longitude:
					from go1_commerce.go1_commerce.\
														utils.google_maps import get_geolocation
					location_data=get_geolocation(item.address)
					item.latitude=location_data['latitude']
					item.longitude=location_data['longitude']
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.customers.check_location") 

@frappe.whitelist(allow_guest=True)
def update_checkout_guest_customer(first_name, email, phone,address_data=None):
	try:
		customers = frappe.db.get_all("Customers",filters={"email":email})
		customer = None
		frappe.local.cookie_manager.set_cookie('guest_customer_name', first_name)
		frappe.local.cookie_manager.set_cookie('guest_customer_phone', phone)
		if customers:
			customer = frappe.get_doc("Customers",customers[0])
		else:
			customer = frappe.new_doc("Customers")
			customer.first_name = first_name
			customer.email = email
			customer.phone = phone
			from frappe.utils import random_string
			password_new = "G#" + random_string(8) + "k12"
			customer.new_password = password_new
			customer.set_new_password = password_new
			customer.append('customer_role', {'role': 'Customer'})
			customer.save(ignore_permissions=True)
		if customer:
			return update_address_data(address_data)
		return {"status":"failed"}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'update_guest_customer_data')

def update_address_data(first_name, email, phone,address_data=None):
	if address_data:
		addr = json.loads(address_data)
		if not frappe.db.get_all("Customer Address",
						   filters={"parent":customer.name,"latitude":addr.get('latitude'),
				  					"longitude":addr.get('latitude')}):
			customer = frappe.get_doc("Customers",customer.name)
			customer.append('table_6', {
										'address': addr.get('address'),
										'city': addr.get('city'),
										'state': addr.get('state'),
										'country': addr.get('country'),
										'zipcode': addr.get('pincode'),
										'landmark': addr.get('landmark'),
										'address_type': addr.get('address_type'),
										'door_no': addr.get('door_no'),
										'unit_number': addr.get('unit_number'),
										'latitude': addr.get('latitude'),
										'longitude': addr.get('longitude'),
										'first_name': first_name,
										'email': email,
										'phone': phone
										})
			customer.save(ignore_permissions=True)
	frappe.local.cookie_manager.set_cookie('customer_id', customer.name)
	frappe.local.login_manager.user = customer.email
	frappe.local.login_manager.post_login()
	guest_customer = frappe.request.cookies.get('guest_customer')
	from go1_commerce.go1_commerce.v2.customer \
				import move_cart_items
	move_cart_items(customer.name, guest_customer)
	return {"status":"success"}

def get_random_string(length):
	import random
	import string
	letters = string.ascii_lowercase
	result_str = ''.join(random.choice(letters) for i in range(length))
	return result_str

@frappe.whitelist(allow_guest=True)
def update_guest_customer_data(customer_id, first_name, email, phone, address_data=None):
	try:
		customer = frappe.get_doc('Customers', customer_id)
		customer.first_name = first_name
		customer.email = email
		customer.phone = phone
		if address_data:
			addr = json.loads(address_data)
			allow = True
			for item in customer.table_6:
				if item.latitude == addr.get('latitude') and item.longitude == addr.get('longitude'):
					allow = False
					break
				elif item.address == addr.get('address') and \
							item.city == addr.get('city') and item.state == addr.get('state') and \
							item.country == addr.get('country') and addr.get('pincode') == item.zipcode:
					allow = True
					break
			if allow:
				customer.append('table_6', {'address': addr.get('address'),
											'city': addr.get('city'),
											'state': addr.get('state'),
											'country': addr.get('country'),
											'zipcode': addr.get('pincode'),
											'landmark': addr.get('landmark'),
											'address_type': addr.get('address_type'),
											'door_no': addr.get('door_no'),
											'unit_number': addr.get('unit_number'),
											'latitude': addr.get('latitude'),
											'longitude': addr.get('longitude'),
											'first_name': first_name,
											'email': email,
											'phone': phone })
		customer.save(ignore_permissions=True)
		return customer
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'update_guest_customer_data')

@frappe.whitelist()
def delete_guest_customers():
	from frappe.utils import add_days, getdate, nowdate
	check_date = add_days(getdate(nowdate()), 7)
	customers_list = frappe.db.sql( """	SELECT name 
										FROM `tabCustomers` 
										WHERE NOT EXISTS (
											SELECT name 
											FROM `tabOrder` 
											WHERE customer = `tabCustomers`.name) 
										AND naming_series = "GC-" 
										AND creation < %(date)s
									""", {'date': check_date}, as_dict=1)
	if customers_list:
		for item in customers_list:
			deviceid = frappe.db.get_value('App Alert Device', {"document":"Customers", "user":item.name})
			if deviceid and frappe.db.exists("App Alert Device", deviceid):
				device = frappe.get_doc('App Alert Device', deviceid)
				device.delete()
			customer = frappe.get_doc('Customers', item.name)
			cart = frappe.db.get_all('Shopping Cart', filters={'customer': item.name})
			if cart:
				for c in cart:
					if "Drip Marketing" in frappe.get_installed_apps():
						if frappe.db.exists("Email Campaign", 
						  			{"email_campaign_for": "Shopping Cart", "recipient":c.name}):
							camp=frappe.db.get_value("Email Campaign", 
								{"email_campaign_for": "Shopping Cart", "recipient":c.name}, "name")
							camp_info = frappe.get_doc('Email Campaign', camp)
							camp_info.delete()
					cart_info = frappe.get_doc('Shopping Cart', c.name)
					cart_info.delete()
			customer.delete()

@frappe.whitelist()
def get_children(doctype, parent=None, is_root=False, is_tree=False):
	filters = []
	fields = ['name as value', 'full_name as title', 'full_name', 'last_name', 
		   		'phone', 'email', "is_group as expandable", "parent_level"]
	if is_root:
		parent = ''
	if parent:
		filters.append(['parent_level', '=', parent])
	else:
		filters.append(['parent_level', '=', ''])
	customers = frappe.get_list(doctype, fields=fields,
		filters=filters, order_by='name')
	return customers


def generate_keys(doc, method):
	user_details = frappe.get_doc("User", doc.name)
	api_secret = frappe.generate_hash(length=15)
	if not user_details.api_key:
		api_key = frappe.generate_hash(length=15)
		user_details.api_key = api_key
	user_details.api_secret = api_secret
	user_details.save(ignore_permissions=True)

def has_website_permission(doc, ptype, user, verbose=False):
	if not user: user = frappe.session.user	
	if doc.user_id == user:
		return True
	return False

@frappe.whitelist()
def add_customer_withparent(data, parent):
	data = json.loads(data)
	new_doc = frappe.new_doc('Customers')
	if frappe.db.get_value("Customers",parent,"name"):
		new_doc.parent_doctype ="Customers"
		new_doc.parent_level= parent if parent!="All Customers" else ""
	new_doc.first_name = data['first_name']
	new_doc.last_name = data['last_name']
	new_doc.phone = data['phone']
	new_doc.email = data['email']
	new_doc.is_group = data['is_group']
	new_doc.flags.ignore_permissions=True
	new_doc.insert()
	return new_doc


def update_custom_preference_check(order_info,customer_info,item):
	if item.reference_document == 'Cuisine':
		check_preference('Cuisine', '', 'Order', customer_info)
	elif item.reference_document == 'Product Category':
		item_names = ','.join(['"' + x.item + '"' for x in order_info.order_item])
		if order_info.order_item[0].order_item_type == 'Product':
			category_list = frappe.db.sql(	""" SELECT DISTINCT category 
												FROM `tabProduct Category Mapping` 
												WHERE parent IN ({0})
											""".format(item_names), as_dict=1)
			if category_list:
				for cat in category_list:
					check_preference('Product Category', cat.category, 'Order', customer_info)
	elif item.reference_document == 'Product Brand':
		item_names = ','.join(['"' + x.item + '"' for x in order_info.order_item])
		if order_info.order_item[0].order_item_type == 'Product':
			brand_list = frappe.db.sql(	""" SELECT DISTINCT band 
											FROM `tabProduct Brand Mapping` 
											WHERE parent IN ({0})
										""".format(item_names), as_dict=1)
			if brand_list:
				for br in brand_list:
					check_preference('Product Brand', br.brand, 'Order', customer_info)

def update_customer_preference_from_order(order_id):
	settings = frappe.get_single('Customer Preference Settings')
	if settings.enable_log and settings.preferences:
		order_info = frappe.get_doc('Order', order_id)
		customer_info = frappe.get_doc('Customers', order_info.customer)
		for item in settings.preferences:
			update_custom_preference_check(order_info,customer_info,item)
		for item in settings.preferences:
			check_records = frappe.db.sql( 	"""	SELECT name, modified 
												FROM `tabCustomer Preference` 
												WHERE parent = %(parent)s 
												AND reference_doctype = %(doctype)s 
												AND preference_type = %(pre_type)s 
												ORDER BY modified DESC
											""", {'pre_type': item.based_on, 'doctype': item.reference_document, 
												'parent': customer_info.name}, as_dict=1)

			if len(check_records) > int(item.no_of_records):
				delete_list = check_records[int(item.no_of_records):]
				frappe.db.sql(	""" DELETE FROM `tabCustomer Preference` 
									WHERE name IN ({0})
								""".format(','.join(['"' + x.name + '"' for x in delete_list])))
			

def check_preference(reference_doctype, reference_name, preference_type, customer_info):
	check_val = next((x for x in customer_info.customer_preference \
				   if (x.reference_doctype == reference_doctype and x.reference_name == reference_name \
		   								and x.preference_type == preference_type)), None)
	if check_val:
		frappe.db.set_value('Customer Preference', check_val.name, 'count', check_val.count + 1)
	else:
		res = frappe.get_doc({
								'doctype': 'Customer Preference',
								'reference_doctype': reference_doctype,
								'reference_name': reference_name,
								'count': 1,
								'preference_type': preference_type,
								'parenttype': 'Customers',
								'parent': customer_info.name,
								'parentfield': 'customer_preference'
							}).insert(ignore_permissions=True)

def get_custom_query(user):
	if not user: user = frappe.session.user
	if "System Manager" in frappe.get_roles(user):
		return '''(`tabCustomers`.naming_series <> "GC-")'''

	return "(`tabCustomers`.naming_series!='GC-' and (email!='Administrator' or email is NULL) \
			and (email not in(select parent from `tabHas Role` where parenttype='User' \
			and (role='Admin' or role='System Manager')) or email is NULL))"

@frappe.whitelist()
def get_all_roles(include=None):
	""" get the roles set in the  """
	filters={}
	filters['disabled'] = 0
	if include:
		filters["name"]= ("in", include)
	roles = frappe.get_all("Role",
		fields=["*"], filters=filters, distinct=True)
	active_roles = [row.get("name") for row in roles]
	return active_roles

@frappe.whitelist()
def make_customers_dashboard(name):
	try:
		data = get_order_count(name)
		today_orders_count = data[0]
		all_count = data[1]
		source = data[2]
		catalog_settings = get_settings('Catalog Settings')
		currency = frappe.db.get_all('Currency',fields=["*"], 
							 filters={"name":catalog_settings.default_currency},limit_page_length=1)
		if currency:
			rupee = currency[0].symbol
		else:
			rupee = "₹"
		return {
      			'today_orders_count':today_orders_count,
         		'all_count':all_count,
				'currency':rupee,
		  		'source':source
				}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.customers.make_customers_dashboard")

def get_order_count(name):
	dt = 'Order'
	today_order_list = frappe.db.sql("""SELECT name
										FROM `tab{dt}`  
										WHERE customer = %(name)s 
										AND DATE(`creation`) = CURDATE() 
										AND naming_series != "SUB-ORD-" 
									""".format(dt=dt), {'name': name}, as_dict=1)
	all_order_list = frappe.db.sql("""	SELECT name 
										FROM `tab{dt}` s 
										WHERE s.customer = %(name)s 
										AND naming_series != "SUB-ORD-" 
									""".format(dt=dt), {'name': name}, as_dict=1)
	source=None
	wallet = frappe.get_single("Wallet Settings")
	if wallet.enable_customer_wallet==1:
		source = frappe.db.sql("""	SELECT name, user_type, current_wallet_amount, total_wallet_amount 
									FROM `tabWallet` 
									WHERE user = %(user)s
								""", {'user': name}, as_dict=1)
		if source:
			source = source
	today_orders_count = len(today_order_list)
	all_count = len(all_order_list)
	return [today_orders_count,all_count,source]

@frappe.whitelist()
def get_customer_orders(customer_id):
	condition = ''
	dt = 'Order'
	order_detail=frappe.db.sql("""	SELECT name, total_amount, payment_method_name, 
										payment_status, order_date, status 
									FROM `tab{dt}` 
									WHERE customer = %(customer_id)s 
									AND naming_series != "SUB-ORD-" {cond} 
									ORDER BY creation 
									LIMIT 10
								""".format(dt=dt, cond=condition), {'customer_id': customer_id}, as_dict=1)
	catalog_settings = get_settings('Catalog Settings')
	currency=frappe.db.get_all('Currency',fields=["*"], 
							filters={"name":catalog_settings.default_currency},limit_page_length=1)
	if currency:
		rupee=currency[0].symbol
	else:
		rupee = "₹"
	return {
     		'order_detail':order_detail,
       		'currency':rupee
			}

@frappe.whitelist()
def get_order_settings():
	order_settings = get_settings('Order Settings')
	return order_settings
@frappe.whitelist()
def impersonate_customer(customer_id):
	frappe.local.cookie_manager.set_cookie('impersonate_customer', "1")
	frappe.local.cookie_manager.set_cookie('impersonate_old_customer', frappe.session.user)
	customer_info = frappe.get_doc("Customers",customer_id)
	if customer_info.new_password:
		frappe.local.login_manager.authenticate(customer_info.email, customer_info.new_password)
		frappe.local.login_manager.post_login()
	else:
		catalog_settings = get_settings('Catalog Settings')
		from datetime import date
		todays_date = date.today()
		new_password = "#"+((catalog_settings.site_name.replace(" ","").lower())[0:5])+"Y"+\
																str(todays_date.year)+"#"
		customer_info.set_new_password = new_password
		customer_info.save(ignore_permissions=True)
		frappe.local.login_manager.authenticate(customer_info.email, new_password)
		frappe.local.login_manager.post_login()
	frappe.local.cookie_manager.set_cookie('customer_id', customer_id)
	return "success"

@frappe.whitelist(allow_guest=True)
def impersonate_customer_logout(user):
	frappe.local.cookie_manager.delete_cookie(["impersonate_old_customer","impersonate_customer"])
	frappe.local.login_manager.user = user
	frappe.local.login_manager.post_login()
	return "success"

@frappe.whitelist()
def get_sales_executives(route):
	return frappe.db.sql("""SELECT group_concat(SE.se_name) AS names 
							FROM `tabRoute SE` SE 
							INNER JOIN `tabRoute` R ON R.name = SE.parent 
							WHERE R.name = %(route)s 
								AND SE.status = 'Active'
						""", {"route": route}, as_dict = 1)