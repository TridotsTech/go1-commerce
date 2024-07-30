# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json, os, string, random
from frappe.website.website_generator import WebsiteGenerator
from frappe.utils.nestedset import NestedSet
from frappe import _, scrub
from urllib.parse import unquote
from frappe.utils import now, getdate
from frappe.utils.momentjs import get_all_timezones
from frappe.core.doctype.domain_settings.domain_settings import get_active_domains
from datetime import datetime, date
from go1_commerce.utils.setup import get_settings_value_from_domain, get_settings_from_domain
# from go1_commerce.go1_commerce.api import check_domain
from go1_commerce.go1_commerce.doctype.data_creation_report.data_creation_report import create_data_report, update_data_report

class Business(WebsiteGenerator, NestedSet):
	nsm_parent_field = 'parent_business'
	def autoname(self):
		# to override autoname of WebsiteGenerator
		from frappe.model.naming import make_autoname
		if self.parent_business:
			self.naming_series = frappe.db.get_value('Business', self.parent_business, 'abbr')
		self.name = make_autoname(self.naming_series + '.#####', doc=self)

	def validate(self):
		self.lft = ""
		self.rgt = ""
		self.validate_email_type(self.contact_email)
		# validate_zip(self.zip_code)
		# if not self.abbr:
		restaurant_name = self.restaurant_name.replace('(','').replace(')','')
		name_parts = restaurant_name.split()
		if self.get('__islocal') or not self.abbr:
			abbr = ''.join([c[0] for c in name_parts]).upper()	
			check_abbr = frappe.db.sql('''select name,abbr from `tabBusiness` where abbr=%(abbr)s''',{'abbr':abbr},as_dict=1)
			car=self.id_generator()
			if len(check_abbr)>0:
				self.abbr=abbr+car+str(len(check_abbr))
			else:
				self.abbr=abbr
			self.abbr = self.abbr.replace('&', '')
		if not self.route:
			route=self.scrub(self.restaurant_name+'-'+self.abbr)
			# if check_domain('restaurant'):
			# 	route = 'restaurant/' + route	
			self.route = route	
		address=''
		maps = frappe.get_single('Google Settings')
		if maps.enable:	
			if self.business_address:
				address += self.business_address+','
			if self.city:
				address += self.city + ','
			if self.state:
				address += self.state + ' '
			if self.zip_code:
				address += self.zip_code		
			validate_geo_location(self, address)
		if self.show_in_website:
			address=''
			if self.business_address:
				address += self.business_address+','
			if self.city:
				address += self.city + ','
			if self.zip_code:
				address += self.zip_code

				# if check_domain('saas'):
				# 	check_website = frappe.db.get_all('Website', filters={'business': self.name}, fields=['business', 'theme', 'home_page', 'domain_name'])
				# 	if check_website and check_website[0].theme:
				# 		web_theme = frappe.get_doc('Web Theme', check_website[0].theme)
				# 		web_theme.footer_address = address
				# 		web_theme.footer_phone = self.contact_number
				# 		web_theme.footer_email = self.contact_email
				# 		web_theme.save(ignore_permissions=True)
				# else:
				check_website = frappe.db.get_all('Web Theme', filters={'is_active': 1}, fields=['name'])
				if check_website and check_website[0].name:
					web_theme = frappe.get_doc('Web Theme', check_website[0].name)
					web_theme.footer_address = address
					web_theme.footer_phone = self.contact_number
					web_theme.footer_email = self.contact_email
					web_theme.save(ignore_permissions=True)

		if not self.random_id:
			from frappe.utils import random_string
			self.random_id = random_string(12)
		# if check_domain('multi_vendor'):
		# 	get_shop_user = frappe.db.get_all('Shop User',filters={'restaurant':self.name},fields=['*'])
		# 	if not get_shop_user:
		# 		current_year = datetime.date.today().year
		# 		rest_name = self.restaurant_name.title()
		# 		password = "#"+rest_name.replace(' ', '')+"@"+str(current_year)+"#"
		# 		shop_user = frappe.new_doc('Shop User')
		# 		shop_user.first_name = 'Admin'
		# 		shop_user.mobile_no = self.contact_number
		# 		shop_user.email = self.contact_email
		# 		shop_user.restaurant = self.name
		# 		shop_user.set_new_password = password
		# 		shop_user.save(ignore_permissions=True)


		preparation_time = None
		min_value = 0
		for x in self.preparation_time_table:
			if x.is_default == 1:
				preparation_time = x.estimated_time
			if min_value == 0:
				min_value = x.estimated_time
			elif x.estimated_time < min_value:
				min_value = x.estimated_time
		if not preparation_time:
			preparation_time = min_value
		# if len(self.preparation_time_table) == 0:
		# 	restaurant_preparation_times = frappe.db.get_all("Restaurant Preparation Time",fields=['*'],filters={"parent":self.name},order_by="estimated_time")
		# 	# frappe.db.sql('''UPDATE `tabBusiness` SET avg_preparation_time = %(avg_preparation_time)s WHERE name=%(name)s''', {"name":self.name, 'avg_preparation_time':restaurant_preparation_times[0].estimated_time})
		# 	if restaurant_preparation_times:
		# 		preparation_time = 	int(restaurant_preparation_times[0].estimated_time)	
		# if preparation_time:
		self.avg_preparation_time = preparation_time

		if not self.meta_title:
			self.meta_title = self.restaurant_name
		if not self.meta_keywords:
			self.meta_keywords = self.restaurant_name.replace(" ", ", ")
		if not self.meta_description:
			self.meta_description = "About: {0}".format(self.restaurant_name)

	def on_update(self):		
		NestedSet.on_update(self)
		list_size=get_settings_value_from_domain('Media Settings','list_thumbnail_size')
		if self.business_images:
			for item in self.business_images:
				# frappe.log_error("item", item)
				if not item.thumbnail:
					update_thumb(item,list_size)
		# if check_domain("restaurant"):
		# 	if len(self.preparation_time_table) == 0:
		# 		prepartion_time_templates = frappe.db.get_all("Preparation Time Template",fields=['*'])
		# 		if len(prepartion_time_templates)>0:
		# 			preparation_time_table = []
		# 			for x in prepartion_time_templates:
		# 				preparation_time = frappe.new_doc("Restaurant Preparation Time")
		# 				preparation_time.parent = self.name
		# 				preparation_time.parentfield = "preparation_time_table"
		# 				preparation_time.parenttype = "Business"
		# 				preparation_time.is_default = 0
		# 				preparation_time.preparation_time_label = x.name
		# 				preparation_time.save(ignore_permissions=True)
		# 	frappe.publish_realtime('business_update', {'name': self.name})		

	# def after_insert(self):
	# 	if check_domain('saas'):
	# 		frappe.defaults.add_default('business_setup', '[]', self.name, 'Business')
	# 		# insert_default_data(self.name, self.restaurant_name)
	# 		frappe.enqueue('go1_commerce.go1_commerce.doctype.business.business.insert_default_data', business=self.name, business_name=self.restaurant_name)	

	def validate_email_type(self, email):
		from frappe.utils import validate_email_address
		validate_email_address(email.strip(), True)

	def id_generator(self,size=4, chars=string.ascii_uppercase):
		return ''.join(random.choice(chars) for _ in range(size))

	def get_context(self, context):
		# from go1_commerce.go1_commerce.api import check_domain
		context.brand_name = self
	
		context.template = 'templates/pages/businessdetail.html'
		# if check_domain('restaurant'):
		# 	try:
		# 		domain = frappe.get_request_header('host')
		# 	except Exception as e:
		# 		domain = None

		# 	if domain and check_domain('saas') and not frappe.db.get_value('Website', domain):
		# 		if not self.publish_in_market_place:
		# 			frappe.local.flags.redirect_location = '/404'
		# 			raise frappe.Redirect
		# 	elif domain and check_domain('saas') and frappe.db.get_value('Website', domain):
		# 		business = frappe.db.get_value('Website', domain, 'business')
		# 		if business != self.name:
		# 			frappe.local.flags.redirect_location = '/404'
		# 			raise frappe.Redirect
		# 	_ord_type = frappe.form_dict.type
		# 	self.get_restaurant_info(context, _ord_type)
		# else:
		min_price = frappe.form_dict.min
		max_price = frappe.form_dict.max
		sort = frappe.form_dict.sort
		rating = frappe.form_dict.rating
		context.minPrice = min_price
		context.maxPrice = max_price
		context.sort = sort
		context.rating = rating
		attr = []

		from go1_commerce.go1_commerce.api import get_vendor_based_products
		if not sort:
			context.sort = get_sorted_columns(context.catalog_settings.default_product_sort_order)
		for x in frappe.form_dict:
			if x != 'sort' and x != 'min' and x != 'max' and x != 'rating':
				attr.append({'attribute': x,'value': frappe.form_dict[x]})				
		if attr:
			context.attribute = attr
		context.products = get_vendor_based_products(self.name,sort_by=sort,rating=rating,min_price=min_price,max_price=max_price,attributes=attr) 
		
		allow_review = 0
		if frappe.session.user != 'Guest':
			allow_review = 1
		else:
			if context.catalog_settings.allow_anonymous_users_to_write_product_reviews:
				allow_review = 1
		context.allow_review = allow_review
		context.meta_title = self.meta_title if self.meta_title else context.catalog_settings.meta_title
		context.meta_description = self.meta_description if self.meta_description else context.catalog_settings.meta_description
		context.meta_keywords = self.meta_keywords if self.meta_keywords else context.catalog_settings.meta_keywords

	def get_restaurant_info(self, context, __order_type=None):
		from go1_commerce.go1_commerce.api import get_restaurant_data,check_restaurant_asap_timings,get_common_timings

		ord_type = None
		if __order_type:
			if __order_type.lower() == 'pickup':
				ord_type = 'Pickup'
			elif __order_type.lower() == 'delivery':
				ord_type = 'Delivery'
		preferred_date, preferred_time, order_type = get_preferred_date_time(self.time_zone, self.name, ord_type)
		context.preferred_date = preferred_date
		context.preferred_time = unquote(preferred_time)
		preferred_time_format = frappe.request.cookies.get('order_time_format')
		if preferred_time_format:
			if context.preferred_time == 'ASAP' and preferred_time_format != 'ASAP':
				preferred_time_format = 'ASAP'
				frappe.local.cookie_manager.set_cookie("order_time_format", preferred_time_format)
			context.preferred_time_format = unquote(preferred_time_format)
		if order_type.lower() == 'delivery' and self.pickup and not self.delivery:
			order_type = 'Pickup'
			frappe.local.cookie_manager.set_cookie("order_type", order_type)
		elif order_type.lower() == 'pickup' and self.delivery and not self.pickup:
			order_type = 'Delivery'
			frappe.local.cookie_manager.set_cookie("order_type", order_type)
		context.order_type = order_type	
		context.show_time = 1
		context.show_location = 1
		context.is_business_detail = 1
		restaurant_info = get_restaurant_data(self.name, context.preferred_date, context.preferred_time, limit_data=1, only_available=1)
		context.Restaurant = restaurant_info
		context.title = self.restaurant_name
		general_settings = get_settings_from_domain('Business Setting')
		context.settings = general_settings
		context.score_value = frappe.db.get_all('Score Value',fields=['*'])
		path = frappe.get_module_path("restaurant_cms_website")
		path_parts = path.split('/')
		path_parts = path_parts[:-1]
		url = '/'.join(path_parts)
		site_name = frappe.get_site_path().split('/')[-1:][0]
		context.product_tag = frappe.db.sql('''select name, icon from `tabProduct Tag`''', as_dict=1)
		if general_settings.is_marketplace:		
			if os.path.exists(os.path.join(url,'templates','pages','restaurantlist.html')):
				context.template = 'templates/pages/restaurantdetail.html'
		else:
			if os.path.exists(os.path.join(url,'templates','pages','sv-restaurantdetail.html')):
				context.template = 'templates/pages/sv-restaurantdetail.html'

		tax_rate = 0
		if self.sales_tax:
			tax_percent = frappe.db.sql('''select sum(rate) as tax from `tabTax Rates` where parent = %(parent)s''',{'parent':self.sales_tax},as_dict=1)
			if tax_percent and tax_percent[0].tax:
				tax_rate = tax_percent[0].tax
		try:
			context.tax_rate = int(tax_rate) if (tax_rate).is_integer() else tax_rate
		except Exception as e:
			context.tax_rate = int(tax_rate)

		#check restaurant timing
		context.show_asap = 1
		context.asap_date = None
		if frappe.request.cookies.get('order_date') and frappe.request.cookies.get('order_type'):
			check_availability = check_restaurant_asap_timings(unquote(frappe.request.cookies.get('order_date')), "ASAP",unquote(frappe.request.cookies.get('order_type')),self.name)
			if check_availability.get("show_time_popup") == 1:
				context.show_asap = 0
				if unquote(frappe.request.cookies.get('order_time')) == "ASAP":
					restaurant_timings = get_common_timings(business=self.name)
					if unquote(frappe.request.cookies.get('order_type')) == "Delivery":
						frappe.local.cookie_manager.set_cookie('order_time', restaurant_timings.get("delivery_time")[0].get("Hours")[1].get("value"))
						frappe.local.cookie_manager.set_cookie('order_time_format', restaurant_timings.get("delivery_time")[0].get("Hours")[1].get("label"))
						context.preferred_time_format = unquote(restaurant_timings.get("delivery_time")[0].get("Hours")[1].get("label"))
						
					else:
						frappe.local.cookie_manager.set_cookie('order_time', restaurant_timings.get("pickup_time")[0].get("Hours")[1].get("value"))
						frappe.local.cookie_manager.set_cookie('order_time_format', restaurant_timings.get("pickup_time")[0].get("Hours")[1].get("label"))
						context.preferred_time_format = unquote(restaurant_timings.get("pickup_time")[0].get("Hours")[1].get("label"))
					context.asap_date = frappe.utils.getdate().strftime("%a %d")


		#check restaurant timing

	def insert_sample_records(self):
		insert_default_data(self.name, self.restaurant_name)
		return {'status': 'Success'}

	def on_trash(self):
		NestedSet.on_update(self)
	# def insert_dummy_records(self):
	# 	insert_dummy_data(self.name, self.restaurant_name)
	# 	return {'status': 'Success'}
@frappe.whitelist()
def insert_default_records(name, restaurant_name):
	insert_default_data(name, restaurant_name)
	return {'status': 'Success'}


def get_preferred_date_time(time_zone=None, business=None, order_type=None):
	from urllib.parse import unquote
	from go1_commerce.go1_commerce.api import get_today_date
	preferred_date = frappe.request.cookies.get('order_date')
	preferred_time = frappe.request.cookies.get('order_time')
	today_date = get_today_date(time_zone,replace=True)
	if not preferred_time or not preferred_date:
		preferred_date = None if not preferred_date else preferred_date
		preferred_time = 'ASAP' if not preferred_time else preferred_time
		if not preferred_date:
			frappe.local.cookie_manager.set_cookie("custom_time", '1')
	else:
		if preferred_date: 
			preferred_date = unquote(preferred_date)			
		if preferred_time: 
			preferred_time = unquote(preferred_time)
		else:
			preferred_time = 'ASAP'
	if preferred_date and preferred_time:
		if preferred_time != 'ASAP':
			time = frappe.utils.to_timedelta(preferred_time)
			preferred_datetime = datetime.strptime(str(getdate(preferred_date)) + ' ' + str(time), '%Y-%m-%d %H:%M:%S')
			if preferred_datetime < today_date:
				preferred_date = today_date
				preferred_time = 'ASAP'
		else:
			if getdate(preferred_date) < getdate(today_date):
				preferred_date = today_date
	if not preferred_date:
		preferred_date = today_date

	# if preferred_date:
	# 	check_block = frappe.db.get_all('Online Order Timing Block', filters={'restaurant': business, 'date_to_be_blocked': getdate(preferred_date)}, fields=['from_time', 'to_time', 'full_day'])
	# 	if check_block:
	# 		for blk in check_block:
	# 			if blk.full_day:
	# 				preferred_date = None
	# 				preferred_time = None
	# 				break
	# 			elif preferred_date and preferred_time:
	# 				st_date = datetime.strptime(str(getdate(preferred_date)) + ' ' + str(blk.from_time), '%Y-%m-%d %H:%M:%S')
	# 				ed_date = datetime.strptime(str(getdate(preferred_date)) + ' ' + str(blk.to_time), '%Y-%m-%d %H:%M:%S')
	# 				if preferred_time == 'ASAP':
	# 					__order_date = today_date
	# 				else:
	# 					__order_date = datetime.strptime(str(preferred_date) + ' ' + str(frappe.utils.to_timedelta(preferred_time)), '%Y-%m-%d %H:%M:%S')
	# 				if st_date <= __order_date and ed_date >= __order_date:
	# 					preferred_time = None
	# 					break

	if not order_type:
		order_type = frappe.request.cookies.get('order_type')
	if not order_type or order_type.lower() == "undefined":
		order_type = get_settings_value_from_domain('Business Setting','default_order_type', business=business)
	
	frappe.local.cookie_manager.set_cookie("order_date", str(getdate(preferred_date)))
	frappe.local.cookie_manager.set_cookie("order_time", preferred_time)
	frappe.local.cookie_manager.set_cookie("order_type", order_type)
	return getdate(preferred_date), preferred_time, order_type

def update_thumb(item,list_size):
	file_doc = frappe.get_doc("File", {
		"file_url": item.business_image,
		"attached_to_doctype": "Business",
		"attached_to_name": item.parent
	})
	image_file=item.business_image.split('.')
	file_doc.make_thumbnail(set_as_thumbnail=False,width=list_size,height=list_size,suffix=str(list_size)+"x"+str(list_size))
	# frappe.log_error("file_doc.thumbnail_url", file_doc.thumbnail_url)
	# frappe.log_error("name", image_file[0]+"_"+str(list_size)+"x"+str(list_size)+"."+image_file[1])
	item.thumbnail=image_file[0]+"_"+str(list_size)+"x"+str(list_size)+"."+image_file[1]
	# item.thumbnail=file_doc.thumbnail_url
	item.save()

@frappe.whitelist()
def get_all_weekdays():
	Group = frappe.db.get_all('Week Day',fields=['name','day'],order_by='displayorder asc')
	return Group 
	
# @frappe.whitelist()
# def validate_zip(zip_code):
# 		if len(str(zip_code)) > 6:
# 			frappe.throw(_("Zip code must contain 6 numbers").format(), frappe.PermissionError)
	
# @frappe.whitelist()
# def get_address(lat,lon):
# 	try:
# 		"""
# 		Get address from lat lon and update it on form
# 		"""
# 		api_key="AIzaSyDIYWhhAWut-uIbCt8f0ufwEokvosnIP4E"
# 		responce = requests.get("https://maps.googleapis.com/maps/api/geocode/json?latlng={0},{1}&key=AIzaSyCrOxnXpxrfUi8UeVeviGpkJxds1aoJFPM".format(lat,lon))

# 		# responce = requests.get("http://api.geonames.org/findNearbyJSON?lat={0}&lng={1}&username={2}".format(lat,lon,api_key))
# 		responce_json=json.loads(responce.text)
# 		# address_string=""
# 		# try:
# 		# 	if responce_json['geonames'] :
# 		# 			address_string=responce_json['geonames'][0]['name']+" , "+responce_json['geonames'][0]['adminName1']+" , "+responce_json['geonames'][0]['countryName']	
# 		# except :
# 		# 			frappe.msgprint("The address not found for above location")
# 		# return address_string
# 		return responce_json
# 	except Exception:
# 		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.business.get_address") 
	
@frappe.whitelist()
def validate_geo_location(self,address):
	try:
		if not self.latitude or not self.longitude:				
			from go1_commerce.go1_commerce.api import get_geolocation
			location_data=get_geolocation(address)
			if location_data:
				self.latitude=location_data['latitude']
				self.longitude=location_data['longitude']
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.business.validate_geo_location") 
	
@frappe.whitelist()
def get_timeZone():
	try:
		return {
			"timezones": get_all_timezones()
		}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.business.add_on.get_timeZone") 
	

def get_permission_query_conditions(user):
	try:
		if not user: user = frappe.session.user

		if "System Manager" in frappe.get_roles(user):
			return None
		else:
			user=frappe.db.get_all('Shop User',filters={'name':user},fields=['*'])
			if user:
				return """(`tabBusiness`.name = '{restaurant}')"""\
					.format(restaurant=user[0].restaurant)
			else:
				return None
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.business.get_permission_query_conditions") 
	

@frappe.whitelist()
def get_print_formats():	
	try:
		return frappe.db.sql('''select name from `tabPrint Format` r where r.doc_type="Order"''')
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.business.get_print_formats") 
	
@frappe.whitelist()
def get_sorted_columns(sort_by):
	try:
		switcher = {
			"Relevance": "relevance",
			"Name: A to Z": "name_asc",
			"Name: Z to A": "name_desc",
			"Price: Low to High": "price_asc",
			"Price: High to Low": "price_desc",
			"Newest Arrivals": "creation desc",
			"Date: Oldest first": "creation asc"
		 
		}
		return switcher.get(sort_by, "Invalid value")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product_brand.get_sorted_columns") 
	
@frappe.whitelist()
def get_all_cuisines(category_list):
	# from go1_commerce.go1_commerce.api import check_domain
	condition=''
	if "deals" in frappe.get_installed_apps():
		if category_list:
			condition=' where category in ({0})'.format(category_list)
	return frappe.db.sql('''select name from `tabCuisine` {condition} order by name'''.format(condition=condition),as_dict=1)

@frappe.whitelist()
def get_all_amenities(category_list):
	condition=''
	if category_list:
		condition=' where c.name in ({0})'.format(category_list)
	amenity_group=frappe.db.sql('''select distinct ac.amenity_group from `tabAmenities Category Mapping` ac inner join `tabProduct Category` c on c.name=ac.parent {condition} order by ac.amenity_group'''.format(condition=condition),as_dict=1)
	if amenity_group:
		for item in amenity_group:
			child_condition=''
			if condition=='':
				child_condition=' where ac.amenity_group="%s"' % item.amenity_group
			else:
				child_condition=condition+' and ac.amenity_group="%s"' % item.amenity_group
			item.amenities=frappe.db.sql('''select ac.amenity from `tabAmenities Category Mapping` ac inner join `tabProduct Category` c on c.name=ac.parent {condition} order by ac.amenity'''.format(condition=child_condition),as_dict=1)
	return amenity_group

@frappe.whitelist()
def get_children_new(doctype, parent=None, is_root=False, is_tree=False):
	condition = ''

	if is_root:
		parent = ""
	if parent:
		condition = ' where parent_business = "{0}"'.format(frappe.db.escape(parent))	

	business = frappe.db.sql("""
		select
			name as value, restaurant_name as title,
			exists(select name from `tabBusiness` where parent_business=b.name) as expandable
		from
			`tabBusiness` b
		{condition} order by name"""
		.format(condition=condition),  as_dict=1)
	
	return business

@frappe.whitelist()
def add_branch(**kwargs):
	doc = frappe.get_doc('Business',kwargs.get('parent_business'))
	doc.name = None
	doc.contact_person = kwargs.get('contact_person')
	doc.business_phone = kwargs.get('business_phone')
	doc.contact_number = kwargs.get('contact_number')
	doc.contact_email = kwargs.get('contact_email')
	doc.business_address = kwargs.get('business_address')
	doc.city = kwargs.get('city')
	doc.parent_business = kwargs.get('parent_business')
	doc.is_group = kwargs.get('is_group')
	doc.restaurant_name = kwargs.get('business_name')
	doc.abbr = None
	doc.rgt = None
	doc.lft = None
	doc.old_parent = None
	doc.save(ignore_permissions=True)
	assign_branch_head_permissions(kwargs.get('parent_business'), doc.name)
	return doc.name

def assign_branch_head_permissions(parent_business, business):
	shop_users = frappe.db.get_all('Shop User', filters={'role': 'Manager', 'restaurant': parent_business})
	for user in shop_users:
		frappe.permissions.add_user_permission('Business', business, user.name, ignore_permissions=True)

def get_query_condition(user):
	if not user: user = frappe.session.user
	if "System Manager" in frappe.get_roles(user):
		return None

	if "Vendor" in frappe.get_roles(user):
		shop_user = frappe.db.get_all('Shop User',filters={'name':user},fields=['restaurant'])
		if shop_user and shop_user[0].restaurant:
			return """(`tabBusiness`.name = '{business}' or `tabBusiness`.parent_business = '{business}')""".format(business=shop_user[0].restaurant)
		else:
			return """(`tabBusiness`.owner = '{user}')""".format(user=user)

def has_permission(doc, user):
	if "System Manager" in frappe.get_roles(user):
		return True
	if "Vendor" in frappe.get_roles(user):
		shop_user = frappe.db.get_all('Shop User',filters={'name':user},fields=['restaurant'])
		if shop_user:
			if shop_user[0].restaurant in [doc.name, doc.parent_business]:
				return True
		return False

	return True

@frappe.whitelist(allow_guest=True)
def get_business_reviews(business, page_no=1, page_len=10, as_html=0):
	start = int(page_no) * int(page_len)
	reviews = frappe.db.sql('''select * from `tabBusiness Reviews` where is_approved=1 and  business = %(business)s limit {0}, {1}'''.format(start, page_len), {'business': business}, as_dict=1)
	if as_html:
		template = frappe.get_template("/templates/pages/reviewlist.html")
		return template.render({"reviews": reviews})

	return reviews

@frappe.whitelist()
def enqueue_insert_business_data(business, business_name):
	frappe.enqueue('go1_commerce.go1_commerce.doctype.business.business.insert_default_data', business=business, business_name=business_name)

@frappe.whitelist()
def insert_default_data(business, business_name):
	files_list = ['pages.json', 'shipping_methods.json', 'shipping_rate_methods.json', 'default_web_theme.json', 'default_catalog.json', 'media_setting.json', 'saas_email_alerts.json', 'tax_template.json']
	path = frappe.get_module_path("go1_commerce")
	data_report = create_data_report(business)
	result_json = []
	for item in files_list:
		file_path = os.path.join(path, item)
		if os.path.exists(file_path):
			with open(file_path, 'r') as f:
				out = json.load(f)
			opt = {}
			if out and len(out) > 0:
				opt['document_type'] = out[0].get('doctype')
				opt['no_of_records'] = len(out)
			success_cnt = 0
			for i in out:
				try:
					if item == 'default_web_theme.json':
						i['name'] = '{0} - {1} Theme'.format(business_name, business)
						i['is_active'] = 0
					if item == 'saas_email_alerts.json':
						i['name'] = i['name'] + ' ' + business
					if item not in ['saas_email_alerts.json', 'default_web_theme.json']:
						i['business'] = business
						if i.get('name'):
							i['name'] = i['name'] + ' ' + business
					else:
						if i.get('condition'):
							i['condition'] = i['condition'].replace('{{business_id}}', business)
						if i.get('message'):
							i['message'] = i['message'].replace('{{business_name}}', business_name)
					if item == 'default_catalog.json':
						i.update({
							'site_name': business_name, 'meta_title': business_name, 
							'meta_description': business_name, 'meta_keywords': business_name
						})
					if i.get('doctype') == 'Web Theme':
						if frappe.db.get_value('Web Theme', i.get('name')):
							success_cnt = success_cnt + 1
							continue
					frappe.get_doc(i).insert(ignore_links=True, ignore_mandatory=True)
					success_cnt = success_cnt + 1
				except Exception as e:
					frappe.log_error(frappe.get_traceback(),'insert_default_data') 
			opt['created_records'] = success_cnt
		result_json.append(opt)
	
	def _get_result_json(dt, cnt, scnt):
		return {'document_type': dt, 'no_of_records': cnt, 'created_records': scnt}
	# creating order settings
	order_settings = frappe.new_doc('Order Settings')
	order_settings.allow_cancel_order = 0
	order_settings.default_vendor_order_print_format = 'Order Format'
	order_settings.is_re_order_allowed = 0
	order_settings.enable_returns_system = 0
	order_settings.shipment_by = 'Vendor'
	order_settings.business = business
	order_settings.save(ignore_permissions=True)
	result_json.append(_get_result_json('Order Settings', 1, 1))
	# creating cart settings
	cart_settings = frappe.new_doc('Shopping Cart Settings')
	cart_settings.business = business
	cart_settings.save(ignore_permissions=True)
	result_json.append(_get_result_json('Shopping Cart Settings', 1, 1))
	# creating payment method
	''' pay_method = frappe.new_doc('Payment Method')
	pay_method.payment_method = 'Cash'
	pay_method.display_name = 'Cash'
	pay_method.display_order = 0
	pay_method.business = business
	pay_method.enable = 1
	pay_method.save(ignore_permissions=True) '''
	pay_method = frappe.new_doc('Business Payment Gateway Settings')
	pay_method.business = business
	pay_method.display_name = 'Cash'
	pay_method.gateway_type = 'Cash'
	pay_method.disable = 1
	pay_method.insert(ignore_permissions=True)
	result_json.append(_get_result_json('Payment Method', 1, 1))
	# creating slider
	if not frappe.db.get_all("Slider",filters={"business":business}):
		slider = frappe.new_doc('Slider')
		slider.web_image = '/assets/go1_commerce/images/slider-web.jpg'
		slider.mobile_image = '/assets/go1_commerce/images/slider-mobile.png'
		slider.mobile_app_image = '/assets/go1_commerce/images/slider-mobile.png'
		slider.business = business
		slider.published = 1
		slider.display_order = 0
		slider.title = 'Slider'
		slider.redirect_url = '/'
		slider.save(ignore_permissions=True)
	result_json.append(_get_result_json('Slider', 1, 1))
	frappe.db.set_value('Business', business, 'sample_data', 1)
	update_data_report(data_report.name, json.dumps(result_json))


@frappe.whitelist(allow_guest=True)
def insert_dummy_data(checked_business, business, business_name):
	import re
	vertical_name = re.sub('[^a-zA-Z0-9 ]', '', checked_business).lower().replace(' ','_')
	vertical_name1 = vertical_name+".json"
	path = frappe.get_module_path("go1_commerce")
	path_parts=path.split('/')
	path_parts=path_parts[:-1]
	url='/'.join(path_parts)
	if not os.path.exists(os.path.join(url,'verticals')):
		frappe.create_folder(os.path.join(url,'verticals'))
	# file_path = os.path.join(url, 'verticals', vertical_name1)
	
	file_path = os.path.join(url, 'verticals', vertical_name1)
	if os.path.exists(file_path):
		with open(file_path, 'r') as f:
			out = json.load(f)
		for i in out:
			try:
				i['business'] = business
				i['restaurant'] = business
				i['business_name'] = business_name
				
				frappe.get_doc(i).insert(ignore_links=True, ignore_mandatory=True)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(),'insert_dummy_data')   
	return {'status': 'Success'}


@frappe.whitelist(allow_guest=True)
def insert_business_products1(selected_business,cur_business):
	frappe.enqueue('go1_commerce.go1_commerce.doctype.business.business.insert_business_products', selected_business=selected_business, cur_business=cur_business)

@frappe.whitelist(allow_guest=True)
def insert_business_products(selected_business, cur_business):
	try:
		get_product = frappe.db.sql('''select name from `tabProduct` where restaurant = %(restaurant)s''',{'restaurant':selected_business},as_dict=1)
		category_list = []
		for item in get_product:
			doc = frappe.get_doc('Product', item.name)
			get_item = frappe.copy_doc(doc)
			get_item.restaurant = cur_business
			get_item.save(ignore_permissions=True)
			# if check_domain('restaurant') or check_domain('saas'):
			product_categories= frappe.db.sql('''select * from `tabProduct Category Mapping` where parent=%(parent)s group by category''',{'parent':get_item.name},as_dict=1)
			if len(product_categories)>0:
				for cat in product_categories:
					prod_cate = frappe.db.sql('''select * from `tabProduct Category` where name=%(name)s and business=%(business)s group by name''',{'name':cat.category,'business':selected_business},as_dict=1)
					if prod_cate:
						if prod_cate[0].parent_product_category:
							check_parent = next((x for x in category_list if x.get('old_name') == prod_cate[0].parent_product_category), None)
							if not check_parent:
								cat_doc1 = frappe.get_doc('Product Category', prod_cate[0].parent_product_category)
								get_cat_item1 = frappe.copy_doc(cat_doc1)
								get_cat_item1.business = cur_business
								get_cat_item1.lft = None
								get_cat_item1.rgt = None
								get_cat_item1.parent_product_category = None
								get_cat_item1.old_parent = None
								get_cat_item1.save(ignore_permissions=True)
								category_list.append({
									'name': get_cat_item1.name, 
									'category_name': get_cat_item1.category_name, 
									'old_name': prod_cate[0].parent_product_category
									})
							else:
								get_cat_item1 = frappe._dict(check_parent)
							if get_cat_item1:
								check_child = next((x for x in category_list if x.get('old_name') == cat.category), None)
								if not check_child:
									cat_doc = frappe.get_doc('Product Category', cat.category)
									get_cat_item = frappe.copy_doc(cat_doc)
									get_cat_item.business = cur_business
									get_cat_item.lft = None
									get_cat_item.rgt = None
									get_cat_item.old_parent = None
									get_cat_item.parent_product_category = get_cat_item1.name
									get_cat_item.parent_category_name = get_cat_item1.category_name 
									get_cat_item.save(ignore_permissions=True)
									category_list.append({
										'name': get_cat_item.name, 
										'category_name': get_cat_item.category_name, 
										'old_name': cat.category
										})
								else:
									get_cat_item = frappe._dict(check_child)
								frappe.db.sql('''delete from `tabProduct Category Mapping` where parent = %(parent)s and category=%(category)s''',{'category':cat.category,'parent': get_item.name})
								if get_cat_item:
									doc1=frappe.get_doc({
										"doctype": "Product Category Mapping",
										"category":get_cat_item.name,
										"category_name":get_cat_item.category_name,
										"parent":get_item.name,
										"parenttype":'Product',
										"parentfield":'product_categories'
									})
									doc1.insert(ignore_permissions=True)
						else:							
							check_doc = next((x for x in category_list if x.get('old_name') == cat.category), None)
							if not check_doc:
								cat_doc = frappe.get_doc('Product Category', cat.category)
								get_cat_item = frappe.copy_doc(cat_doc)
								get_cat_item.business = cur_business
								get_cat_item.lft = None
								get_cat_item.rgt = None
								get_cat_item.old_parent = None
								get_cat_item.parent_product_category = None
								get_cat_item.save(ignore_permissions=True)
								category_list.append({
									'name': get_cat_item.name, 
									'category_name': get_cat_item.category_name, 
									'old_name': cat.category
									})
							else:
								get_cat_item = frappe._dict(check_doc)
							frappe.db.sql('''delete from `tabProduct Category Mapping` where parent = %(parent)s and category=%(category)s''',{'category':cat.category,'parent': get_item.name})
							if get_cat_item:
								doc1=frappe.get_doc({
									"doctype": "Product Category Mapping",
									"category":get_cat_item.name,
									"category_name":get_cat_item.category_name,
									"parent":get_item.name,
									"parenttype":'Product',
									"parentfield":'product_categories'
								})
								doc1.insert(ignore_permissions=True)
			attribute_option = ''
			product_attributes = frappe.db.sql('''select * from `tabProduct Attribute Mapping` where parent=%(parent)s''',{'parent':get_item.name},as_dict=1)
			# for attribute in product_attributes:
			# 	attribute_option = frappe.db.sql('''select * from `tabProduct Attribute Option` where parent = %(product)s and attribute=%(attribute)s''',{"product": doc.name,"attribute":attribute.product_attribute,"attribute_id":attribute.name},as_dict = 1)
			for attribute in product_attributes:
				attribute_option = frappe.db.sql('''select * from `tabProduct Attribute Option` where parent = %(product)s and attribute=%(attribute)s''',{"product": doc.name,"attribute":attribute.product_attribute,"attribute_id":attribute.name},as_dict = 1)
				for attr_option in attribute_option:
					doc2=frappe.get_doc({
						"doctype": "Product Attribute Option",
						"attribute":attr_option.attribute,
						"attribute_id":attribute.name,
						"display_order":attr_option.display_order,
						"price_adjustment":attr_option.price_adjustment,
						"weight_adjustment":attr_option.weight_adjustment,
						"attribute_color":attr_option.attribute_color,
						"parent":get_item.name,
						"parenttype":'Product',
						"parentfield":'attribute_options',
						"option_value":attr_option.option_value,
						"is_pre_selected":attr_option.pre_selected
					})
					doc2.insert(ignore_permissions=True)
		# return attribute_option
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.doctype.business.business.insert_business_products')

@frappe.whitelist()
def get_payment_methods(business, custom_payments):
	if custom_payments:
		payment_methods = frappe.db.sql('''select gateway_type as payment_method, display_name, name from `tabBusiness Payment Gateway Settings` where business = %(business)s''',{'business':business}, as_dict=1)
		if payment_methods:
			return payment_methods
	
	if business:
		payment_methods = frappe.db.get_all('Payment Method',filters={'enable':1, 'business': business},order_by='display_order',fields=['payment_method', 'display_name', 'name', 'use_additional_fee_percentage', 'additional_fee_percentage', 'additional_charge'])
		if payment_methods:
			return payment_methods
	
	payment_methods = frappe.db.get_all('Payment Method',filters={'enable':1},order_by='display_order',fields=['payment_method', 'display_name', 'name', 'use_additional_fee_percentage', 'additional_fee_percentage', 'additional_charge'])
	return payment_methods

@frappe.whitelist(allow_guest=True)
def get_business_data_summary(selected_business,cur_business):
	products = frappe.db.sql('''select name from `tabProduct` where restaurant = %(restaurant)s''',{'restaurant':selected_business},as_dict=1)
	categories = frappe.db.sql('''select distinct m.category from `tabProduct` p inner join `tabProduct Category Mapping` m on m.parent=p.name where p.restaurant=%(restaurant)s''',{'restaurant':selected_business},as_dict=1)
	files = frappe.db.sql('''select f.name from `tabProduct` p inner join `tabFile` f on f.attached_to_name=p.name where p.restaurant=%(restaurant)s and f.attached_to_doctype="Product"''',{'restaurant':selected_business},as_dict=1)
	result={"product_count": len(products), "product_category": len(categories), "attached_files": len(files)}
	return result

@frappe.whitelist()
def get_website_details(business):
	web_list = frappe.db.get_all('Website', filters={'business': business})
	if web_list:
		return {'has_web': 1}

	return {'has_web': 0}

@frappe.whitelist()
def get_tip_range(business, tip_template):
	# tip_options = []
	# tip = frappe.db.sql('''select (CONVERT(CHAR(10), TP.from_total), "-", CONVERT(CHAR(10), TP.to_total)) as tip_range, TP.from_total, TP.to_total, TP.tip_label, TP.tip_percent from `tabTip Configuration` TC inner join `tabTip Percentage` TP on TC.name=TP.parent where TC.name=%(name)s group by tip_range''',{'name':tip_template}, as_dict=1)
	tip = frappe.db.sql('''select CONCAT(CAST(TP.from_total AS int), "-", CAST(TP.to_total AS int)) as tip_range, TP.from_total, TP.to_total, TP.tip_label, TP.tip_percent, TP.tip_type, TP.default from `tabTip Configuration` TC inner join `tabTip Percentage` TP on TC.name=TP.parent where TC.name=%(name)s order by TP.idx''',{'name':tip_template}, as_dict=1)
	# tip = frappe.db.sql('''select CONCAT(LTRIM(TP.from_total), "-", LTRIM(TP.to_total)) as tip_range, TP.from_total, TP.to_total, TP.tip_label, TP.tip_percent from `tabTip Configuration` TC inner join `tabTip Percentage` TP on TC.name=TP.parent where TC.name=%(name)s group by tip_range''',{'name':tip_template}, as_dict=1)
	tip_ranges = ''
	tip_options = ''
	tip_ran = list(set([x.tip_label for x in tip]))
	unique_attr = []
	for uni in tip:
		if uni.tip_range not in unique_attr:
			unique_attr.append(uni.tip_range)
	tip_options_list = []
	for attr in unique_attr:
		tip_list = list(filter(lambda x: x.tip_range == attr, tip))
		arr = {}
		if tip_list:
			arr['range'] = attr
			tip_op = []
			for sz in tip_ran:
				check = next((x for x in tip_list if x.tip_label == sz), None)
				if check:
					add=''
					if check.tip_type=="Tip Percentage":
						add = check.tip_label + '%'
					else:
						add = '$' + check.tip_label
					tip_op.append({'tip_amt': check.tip_percent, 'tip_label': add, 'default': check.default})
					arr['tip_lists'] = tip_op
			tip_options_list.append(arr)
	tip_ranges = unique_attr
	tip_options = tip_options_list
	return tip_options_list
