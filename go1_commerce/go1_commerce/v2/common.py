from __future__ import unicode_literals, print_function
import frappe, json, os
import frappe.modules
from frappe import _,STANDARD_USERS
from frappe.utils import now,now_datetime, get_formatted_email,get_files_path
from datetime import date, datetime, timedelta
from pytz import timezone
from six import  string_types
from go1_commerce.utils.utils import get_auth_token,get_customer_from_token,\
	other_exception
from go1_commerce.utils.setup import get_settings_value, get_settings

@frappe.whitelist(allow_guest=True)
def get_all_website_settings(allow_guest = True):
	try:
		import os
		path = get_files_path()
		file_path = os.path.join(path, "settings/all_website_settings.json")
		all_categories = None
		if os.path.exists(file_path):
				f = open(file_path)
				# frappe.log_error("FFFFFFF",type(f))
				all_categories = json.load(f)
		frappe.log_error("all_categories",all_categories)
		return all_categories
	except Exception:
		frappe.log_error(title = "Error in get_all_website_settings", message = frappe.get_traceback())

def generate_all_website_settings_json_doc(doc,method):
	try:
		res_data = get_all_website_settings_data()
		frappe.log_error("res_data",res_data)
		path = get_files_path()
		if not os.path.exists(os.path.join(path,'settings')):
			frappe.create_folder(os.path.join(path,'settings'))
		with open(os.path.join(path,'settings', 'all_website_settings.json'), "w") as f:
			content = json.dumps(json.loads(frappe.as_json(res_data)), separators=(',', ':'))
			# content = json.dumps(res_data)
			f.write(content)
	except Exception:
		frappe.log_error(title = "Error in generate_all_website_settings_json_doc", message = frappe.get_traceback())


def check_app_setting_exist(app_settings):
	default_footer = None
	default_header = None
	if app_settings.default_header:
		if 'go1_cms' in frappe.get_installed_apps():
			from go1_cms.go1_cms.api import get_header_info as go1_get_header_info
			default_header = go1_get_header_info(app_settings.default_header)
		else:
			default_header = get_header_info(app_settings.default_header)
	if app_settings.default_footer:
		if 'go1_cms' in frappe.get_installed_apps():
			from go1_cms.go1_cms.api import get_footer_info as go1_get_footer_info
			default_footer = go1_get_footer_info(app_settings.default_footer)
		else:
			default_footer = get_header_info(app_settings.default_footer)
	website_logo = app_settings.website_logo
	login_image = app_settings.login_image
	return [login_image,website_logo,default_footer,default_header]

def iterate_parent_cat_in_web_settings(parent_categories):
	for category in parent_categories:
		filtered_category = {}
		for key, value in category.items():
			if value is not None:
				filtered_category[key] = value if value else ""
			if key == "child":
				filtered_category[key] = []
				for child_item in value:
					filtered_child = {}
					for child_key, child_value in child_item.items():
						if child_value is not None:
							filtered_child[child_key] = child_value if child_value else ""
					filtered_category[key].append(filtered_child)
		return filtered_category

@frappe.whitelist(allow_guest=True)
def get_all_website_settings_data():
	catalog_settings = frappe.get_single('Catalog Settings')
	media_settings = frappe.get_single('Media Settings')
	cart_settings = frappe.get_single('Shopping Cart Settings')
	order_settings = frappe.get_single('Order Settings')
	app_settings = frappe.get_single('Mobile App Setting')
	wallet_settings = frappe.get_single('Wallet Settings')
	res_data = {}
	enable_loyalty = 0
	enable_subscription = 0
	if catalog_settings and media_settings and cart_settings and order_settings and app_settings:
		if frappe.db.sql(''' select * from `tabModule Def` where app_name='loyalty' ''', as_dict=True):
			if order_settings.enabled:
				enable_loyalty = 1
		if frappe.db.sql(''' select * from `tabModule Def` where app_name='subscription' ''', as_dict=True):
			enable_subscription = 1
		locations = []
		location_areas = []
		default_location = None
		tracking_codes = frappe.db.get_all("Social Tracking Code",
				     	 fields=['google_site_verification',
		   						 'google_analytics_code',
								 'tag_manager_snippet',
								 'pixel_code',
								 'live_chat_snippet',
								 'whatsapp_snippet',
								 'facebook_messenger',
								 'facebook_page_id',
								 'header_script'])
		enable_multi_store = 0
		enable_multi_vendor = 0
		
		if order_settings:
			if order_settings.enable_zipcode:
				location_areas = frappe.db.sql('''select name, area, zipcode,city 
												  from `tabArea` order by area''',as_dict=1)
					
		enable_left_panel = 1
		if catalog_settings.disable_category_filter and \
		   catalog_settings.disable_price_filter and \
		   catalog_settings.disable_brand_filter and \
		   catalog_settings.disable_ratings_filter:
			enable_left_panel = 0
		default_header = default_footer = website_logo = login_image = None
		if app_settings:
			if app_settings.default_header:
				if 'go1_cms' in frappe.get_installed_apps():
					from go1_cms.go1_cms.api import get_header_info as go1_get_header_info
					default_header = go1_get_header_info(app_settings.default_header)
				else:
					default_header = get_header_info(app_settings.default_header)
			if app_settings.default_footer:
				if 'go1_cms' in frappe.get_installed_apps():
					from go1_cms.go1_cms.api import get_footer_info as go1_get_footer_info
					default_footer = go1_get_footer_info(app_settings.default_footer)
				else:
					default_footer = get_header_info(app_settings.default_footer)
			website_logo = app_settings.website_logo
			login_image = app_settings.login_image
		from go1_commerce.go1_commerce.v2.category import get_parent_categories
		res_data={
			"default_header":default_header,
			"default_footer":default_footer,
			# "enable_multi_vendor":enable_multi_vendor,
			"no_of_records_per_page":catalog_settings.no_of_records_per_page,
			"products_per_row":catalog_settings.products_per_row,
			"show_short_description":catalog_settings.show_short_description,
			"show_brand":catalog_settings.show_brand,
			# "enable_loyalty":enable_loyalty,
			"disable_category_filter":catalog_settings.disable_category_filter,
			'additional_menus':catalog_settings.additional_menu,
			"disable_price_filter":catalog_settings.disable_price_filter,
			"disable_brand_filter":catalog_settings.disable_brand_filter,
			"disable_ratings_filter":catalog_settings.disable_ratings_filter,
			# "enable_left_panel":enable_left_panel,
			"website_logo":website_logo,
			"login_image":login_image,
			"upload_review_images":catalog_settings.upload_review_images,
			"included_tax":catalog_settings.included_tax,
			"enable_related_products":catalog_settings.enable_related_products,
			"enable_best_sellers":catalog_settings.enable_best_sellers,
			"customers_who_bought":catalog_settings.customers_who_bought,
			"default_product_sort_order":catalog_settings.default_product_sort_order,
			# "enable_subscription":enable_subscription,
			"enable_wallet":order_settings.enable_wallet,
			"enable_guest_checkout":order_settings.enable_checkout_as_guest,
			"allow_customer_to_addwallet":order_settings.allow_customer_to_add_wallet,
			"enable_map":order_settings.enable_map,
			"allow_cancel_order":order_settings.allow_cancel_order,
			"enable_driver_for_shipment":order_settings.enable_driver_for_shipment,
			"enable_auto_debit_wallet":wallet_settings.customer_auto_debit,
			"show_bestsellers_in_shopping_cart":cart_settings.show_bestsellers_in_shopping_cart,
			"enable_shipping_address":cart_settings.enable_ship_addr,
			"show_gift_card_box":order_settings.show_gift_card_box,
			"enable_reorder":order_settings.is_re_order_allowed,
			"enable_returns_system":order_settings.enable_returns_system,
			"collecting_the_bank_details":order_settings.collecting_the_bank_details,
			"default_products_per_row":catalog_settings.products_per_row,
			"enable_referral":order_settings.enable_referral,
			"enable_terms_of_service":order_settings.terms_of_service,
			"return_based_on":order_settings.return_based_on,
			"return_request_period":order_settings.return_request_period,
			"enable_question_and_answers":catalog_settings.enable_question_and_answers,
			"enable_recently_viewed_products":catalog_settings.enable_recetly_viewed_products,
			"enable_best_sellers":catalog_settings.enable_best_sellers,
			"default_country":frappe.db.get_value("System Settings","System Settings","country"),
			"currency":catalog_settings.default_currency,
			"currency_symbol":frappe.db.get_value("Currency",catalog_settings.default_currency,"symbol"),
			"enable_customers_who_bought":catalog_settings.customers_who_bought,
			"allow_guest_to_review":catalog_settings.allow_anonymous_users_to_write_product_reviews,
			"account_settings":{
				"enable_gender":order_settings.enable_gender,
				# "enable_lastname":order_settings.enable_lastname,
				# "is_gender_required":order_settings.is_gender_required,
				"is_lastname_required":order_settings.is_lastname_required,
				"enable_dob":order_settings.enable_dob,
				"dob_required":order_settings.dob_required,
				"enable_state":order_settings.enable_state,
				"is_state_required":order_settings.is_state_required,
				"enable_house_type":order_settings.enable_house_type,
				"is_house_type_required":order_settings.is_house_type_required,
				"is_country_required":order_settings.is_country_required,
				"enable_landmark":order_settings.enable_landmark,
				"is_landmark_required":order_settings.is_landmark_required,
				"enable_door_no":order_settings.enable_door_no,
				"is_door_no_required":order_settings.is_door_no_required,
				# "enable_message_forum":order_settings.enable_message_forum,
				# "enable_vendor_contact_form":order_settings.enable_vendor_contact_form,
			},
			# "catalog_settings":catalog_settings,
			"picode_vaidation":{
				"pincode_type":order_settings.pincode,
				"min_pincode_length":order_settings.min_pincode_length,
				"max_pincode_length":order_settings.max_pincode_length,
			},
			"password_validation":{
				"password_policy":order_settings.password_policy,
				"min_password_length":order_settings.min_password_length,
			},
			"phone_vaidation":{
				"min_phone_length":order_settings.min_phone_length,
				"max_phone_length":order_settings.max_phone_length,
			},
			"enable_zipcode":order_settings.enable_zipcode,
			# "radius_based_validation":order_settings.radius_based_validation,
			"location_areas":location_areas,
			# "locations":locations,
			"default_location":default_location,
			# "enable_multi_store":enable_multi_store,
			"app_settings":app_settings,
			"social_tracking_codes":tracking_codes[0] if tracking_codes else None,
			"default_meta_title":catalog_settings.meta_title,
			"default_meta_description":catalog_settings.meta_description,
			"default_meta_keywords":catalog_settings.meta_keywords,
			# "market_place_fees":frappe.db.get_all("Market Place Fee",fields=["fee_name","fee_amount","fee_type","fee_percentage"]),
			"all_categories":get_parent_categories()
		}
	#to store the response data 
	return res_data

# @frappe.whitelist(allow_guest=True)
# def get_all_website_settings_data():
# 	catalog_settings = frappe.get_single('Catalog Settings')
# 	media_settings = frappe.get_single('Media Settings')
# 	cart_settings = frappe.get_single('Shopping Cart Settings')
# 	order_settings = frappe.get_single('Order Settings')
# 	frappe.log_error("order_settings",order_settings)
# 	app_settings = frappe.get_single('Mobile App Setting')
# 	wallet_settings = frappe.get_single('Wallet Settings')
# 	res_data = {}
# 	if catalog_settings and media_settings and cart_settings and order_settings and app_settings:
# 		location_areas = []
# 		tracking_codes = frappe.db.get_all("Social Tracking Code",
# 							fields=['google_site_verification','google_analytics_code','tag_manager_snippet',
# 									'pixel_code','live_chat_snippet','whatsapp_snippet','facebook_messenger',
# 									'facebook_page_id','header_script'])
# 		if order_settings:
# 			if order_settings.enable_zipcode:
# 				location_areas = frappe.db.sql('''select name, area, zipcode,city 
# 												  from `tabArea` order by area''',as_dict=1)
# 		default_header = default_footer = website_logo = login_image = None
# 		if app_settings:
# 			data = check_app_setting_exist(app_settings)
# 			login_image,website_logo,default_footer,default_header = data[0],data[1],data[2],data[3]
# 		country = frappe.db.get_value("System Settings","System Settings","country")
# 		symbol = frappe.db.get_value("Currency",catalog_settings.default_currency,"symbol")
# 		from go1_commerce.go1_commerce.v2.category import get_parent_categories
# 		parent_categories = get_parent_categories()
# 		filtered_categories = []
# 		filtered_category = iterate_parent_cat_in_web_settings(parent_categories)

# 		filtered_categories.append(filtered_category)
# 		tracking_codes = tracking_codes[0] if tracking_codes else None
# 		json_data = {
# 					"catalog_settings":catalog_settings,
# 					"media_settings":media_settings,
# 					"cart_settings":cart_settings,
# 					"order_settings":order_settings,
# 					"app_settings":app_settings,
# 					"wallet_settings":wallet_settings,
# 					"location_areas":location_areas,
# 					"location_areas":location_areas,
# 					"tracking_codes":tracking_codes,
# 					"default_header":default_header,
# 					"default_footer":default_footer,
# 					"website_logo":website_logo,
# 					"login_image":login_image,
# 					"country":country,
# 					"symbol":symbol,
# 					"parent_categories":filtered_categories
# 			   }
# 		res_data = (frappe.render_template('/templates/website_settings_data.html', json_data))
# 		result = minify_string(res_data)
# 		frappe.log_error("TYPEEE",type(result))
# 		return result
# 	else:
# 		return res_data

def minify_string(html):
	import re
	return_String = html.replace('\n',"")
	return re.sub(">\s*<","><",return_String)


def get_today_date(time_zone=None, replace=False):
	'''
		get today  date based on selected time_zone
	'''

	if not time_zone:
		time_zone = frappe.db.get_single_value('System Settings', 'time_zone')
	currentdate = datetime.now()
	currentdatezone = datetime.now(timezone(time_zone))
	if replace:
		return currentdatezone.replace(tzinfo=None)
	else:
		return currentdatezone


def get_footer_info(footer_id,app_settings):
	footer_list = frappe.db.get_all("Footer Component",
										filters={"name":app_settings.default_footer},
										fields=['title'])
	if footer_list:
		path = frappe.utils.get_files_path()
		with open(os.path.join(path, 'data_source', (footer_id.lower().replace(' ','_')  + '_web.json'))) as f:
			data = json.loads(f.read())
			lists = []
			for item in data:
				if item.get('section_type')=="Menu":
					page_section_menu = frappe.get_value("Page Section",item.get('section'),"menu")
					menu = frappe.db.get_all("Menu",
				  		   filters={"name":page_section_menu},
						   fields=['is_static_menu','name'])
					if menu:
						parent_menus = frappe.db.sql(""" SELECT 
															menu_label,redirect_url,icon 
														 FROM 
															`tabMenus Item` 
														 WHERE parent=%(menu_id)s 
														 AND (parent_menu IS NULL OR parent_menu='') 
														 ORDER BY idx""",{"menu_id":menu[0].name},as_dict=1)
						item["menus"] = parent_menus
				lists.append(item)
		footer_list[0].items = lists
		return footer_list[0]
	return None

def get_header_info(header_id):
	default_header = None
	headers_list = frappe.db.get_all("Header Component",
				   filters={"name":header_id},
				   fields=['menu',
		   				   'enable_top_menu',
						   'is_menu_full_width'])
	if headers_list:
		menu = frappe.db.get_all("Menu",
			   filters={"name":headers_list[0].menu},
			   fields=['is_static_menu','name'])
		if menu:
			headers_list[0].is_static_menu = menu[0].is_static_menu
			headers_list[0].menus = headers_list_parent_menus(menu,headers_list)
			if headers_list[0].enable_top_menu==1:
				left_items = headers_list_left_items(header_id)
				right_items = headers_list_right_items(header_id)
				headers_list[0].top_menu = {"left_items":left_items,"right_items":right_items}
		default_header = headers_list[0]
	return default_header

def headers_list_right_items(header_id):
	right_items =  frappe.db.sql(""" SELECT menu_label,redirect_url,icon 
										FROM `tabMenus Item` 
										WHERE position='Right' 
										AND parent=%(menu_id)s 
										AND parentfield='top_menus' 
										AND (parent_menu IS NULL OR parent_menu='') 
										ORDER BY idx""",{"menu_id":header_id},as_dict=1)
	for x in right_items:
		x.child_menu =  frappe.db.sql(""" SELECT menu_label,redirect_url,icon 
											FROM `tabMenus Item` 
											WHERE position='Right' 
											AND parent=%(menu_id)s AND parentfield='top_menus' 
											AND parent_menu=%(parent_menu)s ORDER BY idx""",
											{"parent_menu":x.menu_label,"menu_id":header_id}
											,as_dict=1)
		for sub_menu in x.child_menu:
			sub_menu.child_menu =  frappe.db.sql(""" SELECT menu_label,redirect_url,icon 
														FROM `tabMenus Item` 
														WHERE position='Right' 
														AND parent=%(menu_id)s 
														AND parentfield='top_menus' 
														AND parent_menu=%(parent_menu)s 
														ORDER BY idx""",
														{"parent_menu":sub_menu.menu_label,
														"menu_id":header_id},as_dict=1)
	return right_items

def headers_list_left_items(header_id):
	left_items =  frappe.db.sql(""" SELECT menu_label,redirect_url,icon 
									FROM `tabMenus Item` 
									WHERE position='Left' 
									AND parent=%(menu_id)s AND parentfield='top_menus' 
									AND (parent_menu IS NULL OR parent_menu='') 
									ORDER BY idx""",{"menu_id":header_id},as_dict=1)
	for x in left_items:
		x.child_menu =  frappe.db.sql(""" SELECT menu_label,redirect_url,icon 
											FROM `tabMenus Item` 
											WHERE position='Left' 
											AND parent=%(menu_id)s 
											AND parentfield='top_menus' 
											AND parent_menu=%(parent_menu)s 
											ORDER BY idx""",{"parent_menu":x.menu_label,
											"menu_id":header_id},as_dict=1)
		for sub_menu in x.child_menu:
			sub_menu.child_menu =  frappe.db.sql(""" SELECT menu_label,redirect_url,icon 
														FROM `tabMenus Item` 
														WHERE position='Left' 
														AND parent=%(menu_id)s 
														AND parentfield='top_menus' 
														AND parent_menu=%(parent_menu)s 
														ORDER BY idx""",
														{"parent_menu":sub_menu.menu_label,
														"menu_id":header_id},as_dict=1)
	return left_items


def headers_list_parent_menus(menu,headers_list):
	parent_menus = frappe.db.sql(""" SELECT menu_label,redirect_url 
										FROM `tabMenus Item` 
										WHERE parent=%(menu_id)s AND parentfield='menus' 
										AND (parent_menu IS NULL OR parent_menu='') 
										ORDER BY idx""",{"menu_id":menu[0].name},as_dict=1)
	for x in parent_menus:
		x.child_menu =  frappe.db.sql(""" SELECT menu_label,redirect_url 
											FROM `tabMenus Item` 
											WHERE parent=%(menu_id)s AND parentfield='menus' 
											AND parent_menu=%(parent_menu)s 
											ORDER BY idx""",{"parent_menu":x.menu_label,
															"menu_id":menu[0].name},as_dict=1)
		for sub_menu in x.child_menu:
			sub_menu.child_menu =  frappe.db.sql(""" SELECT menu_label,redirect_url 
														FROM `tabMenus Item` 
														WHERE parent=%(menu_id)s 
														AND parentfield='menus' 
														AND parent_menu=%(parent_menu)s 
														ORDER BY idx""",
														{"parent_menu":sub_menu.menu_label,
														"menu_id":menu[0].name},as_dict=1)
	headers_list[0].menus = parent_menus

@frappe.whitelist(allow_guest = True)
def get_doc_meta(doctype):
	try:
		frappe.local.response.data = frappe.get_meta(doctype)
		frappe.local.response.status = "success"
		frappe.local.response.http_status_code = 200
	except Exception:
		other_exception("Error in v2.common.get_doc_meta")

@frappe.whitelist(allow_guest=True)
def send_user_forget_pwd_mail(user, domain=None):
	if not domain:
		try:
			domain = frappe.get_request_header('host')
		except Exception as e:
			pass

	if frappe.db.get_value('User', user):
		doc = frappe.get_doc('User', user)
		return reset_password(doc, send_email=True)
	else:
		return {"status":"Failed",
				"message":"We couldnt find the user with this email."}

def reset_password(doc, send_email=False, password_expired=False):
	from frappe.utils import get_url, random_string
	key = random_string(32)
	doc.db_set("reset_password_key", key)
	doc.db_set("last_reset_password_key_generated_on", now_datetime())
	url = "/update-password?key=" + key
	if password_expired:
		url = "/update-password?key=" + key + "&password_expired=true"
	link = get_url(url)
	if send_email:
		send_login_mail(doc, _("Password Reset"), "password_reset", {"link": link}, now=True)
	return "/"

def send_login_mail(doc, subject, template, add_args, now=None):
	"""send mail with login details"""
	from frappe.utils import get_url
	from frappe.utils.user import get_user_fullname
	created_by = get_user_fullname(frappe.session["user"])
	if created_by == "Guest":
		created_by = "Administrator"
	args = {
		"first_name": doc.first_name or doc.last_name or "user",
		"user": doc.name,
		"title": subject,
		"login_url": get_url(),
		"created_by": created_by}
	args.update(add_args)
	sender = (frappe.session.user not in STANDARD_USERS and get_formatted_email(frappe.session.user) or None)
	frappe.sendmail(
		recipients=doc.email,
		sender=sender,
		subject=subject,
		template=template,
		args=args,
		header=[subject, "green"],
		delayed=(not now) if now is not None else doc.flags.delay_emails,
		retry=3) 

@frappe.whitelist(allow_guest = True)
def get_page_builder_data_pagination(page, customer=None,application_type="mobile",page_no=1,page_size=4):
	page = [frappe.get_doc("Web Page Builder",page)]
	path = frappe.utils.get_files_path()
	import os
	if page[0].page_type == 'Adaptive':
		ptype =  ('_web')
		if application_type == "mobile":
			ptype =  ('_mobile')
	else:
		ptype = ('_web')
	use_page_builder = 1
	page_builders = frappe.db.get_all("Web Page Builder",filters={"name":page[0].name},
										fields=['use_page_builder'])
	if page_builders:
		use_page_builder = page_builders[0].use_page_builder
	if use_page_builder:
		with open(os.path.join(path, 'data_source', (page[0].name.lower().replace(' ','_') +ptype + '.json'))) as f:
			data = json.loads(f.read())
			return validate_page_builder_data_pagination(data,page_size,page_no,customer)
	else:
		return frappe.db.get_all("Web Page Builder",
									filters={"name":page[0].name},
									fields=['content','name','use_page_builder'])


def chack_section_type_equals_dynamic_in_item(item):
	if item.get('section_type')=="Dynamic":
		doc = frappe.get_list('Child Page Section',
					filters={"page_section":item.get('section')},
					fields={"name","conditions","page_section","section_type",
							"section_title","reference_document","sort_field","sort_by",
							"custom_section_data","is_editable","dynamic_id","field_list",
							"no_of_records","background_color","text_color"})
		child_section_data = []
		for d in doc:
			sections ={}
			sections['section_title']= d['section_title']
			sections['section_type'] = d['section_type']
			if d['section_type']=="Dynamic Section":
				value = get_page_builder_query(d)
				query = value[0]
				field_list = value[1]
				res_data = get_page_builder_result(query,d,field_list)
				sections['data'] = res_data
			child_section_data.append(sections)
		item['child_section_data'] = child_section_data

def validate_page_builder_data_pagination(data,page_size,page_no,customer):
	from go1_cms.go1_cms.doctype.page_section.page_section import get_data_source
	lists = []
	from_no = (page_no - 1)*page_size
	to_no = page_no*page_size if from_no>0 else page_size
	index = 0
	for item in data:
		if index>=from_no and index<to_no:
			if item.get('login_required') == 1 and customer:
				doc = frappe.get_doc('Page Section', item.get('section'))
				item['data'] = get_data_source(doc.query, doc.reference_document, 
													doc.no_of_records, 1, customer)
			if item.get('dynamic_data') == 1:
				if item['section_type'] in ['Slider','Predefined Section', 'Custom Section', 'Lists',
											'Tabs']:
					doc = frappe.get_doc('Page Section', item.get('section'))
					item = doc.run_method('section_data', customer=customer,add_info=None)
			chack_section_type_equals_dynamic_in_item(item)
			lists.append(item)
		index = index+1
	return lists

def get_page_builder_result(query,d,field_list):
	if d['get_data_from_doctype']==0:
		res_data = frappe.db.sql(query.format(query=query,
						field_list=d['field_list'],
						reference_document=d['reference_document'],
						conditions=d['conditions'],sort_field=d['sort_field'],
						sort_by=d['sort_by'],no_of_records=d['no_of_records'],
						reference_doc=d['reference_doc'],
						get_data_from_doctype=d['get_data_from_doctype'],
						from_doctype=d['from_doctype'],
						reference_field=d['reference_field']),
						as_dict=1)
	if d['get_data_from_doctype']==1:
		res_data = frappe.db.sql(query.format(query=query,field_list=field_list,
							reference_document=d['reference_document'],
							conditions=d['conditions'],sort_field=d['sort_field'],
							sort_by=d['sort_by'],no_of_records=d['no_of_records'],
							reference_doc=d['reference_doc'],
							get_data_from_doctype=d['get_data_from_doctype'],
							from_doctype=d['from_doctype'],
							reference_field=d['reference_field']),
							as_dict=1)
	return res_data


def get_page_builder_query(d):
	query = "SELECT "
	if not d['field_list']:
		query += "* FROM `tab{reference_document}`"
	if d['field_list'] and d['get_data_from_doctype']==0:
		query += "{field_list} FROM `tab{reference_document}`"
	if d['field_list'] and d['get_data_from_doctype']==1:
		field_list =""
		fields = d['field_list'].split(',')
		for i in fields:
			field_list +="B."+i+","
		l = len(field_list)
		field_list = field_list[:l-1]
		query += "{field_list} FROM `tab{reference_document}` A "
	if d['get_data_from_doctype']==1 and d['reference_doc']:
		query += "INNER JOIN `tab{from_doctype}` B ON A.name = B.{reference_field}"
	if d['conditions']:
		query+=" WHERE {conditions}"
	if d['reference_doc'] and d['get_data_from_doctype']==1 and not d['conditions']:
		query += " WHERE A.name='{reference_doc}'"
	if d['reference_doc'] and d['get_data_from_doctype']==1 and d['conditions']:
		query += " and A.name='{reference_doc}'"
	if d['reference_doc'] and d['get_data_from_doctype']==0 and d['conditions']:
		query += "and parent={reference_doc}"
	if d['reference_doc'] and d['get_data_from_doctype']==0 and not d['conditions']:
		query += "WHERE parent={reference_doc}"
	if d['sort_field'] and d['sort_by']:
		query += " ORDER BY {sort_field} {sort_by} "
	if d['no_of_records']:
		query += " LIMIT {no_of_records} "
	return [query,field_list]


def check_route(route):
	theme_settings = frappe.db.get_all("Web Theme",
										filters={"is_active":1},
										fields=['default_header','default_footer','enable_page_title',
												'page_title_bg','page_title_tag','title_text_align',
												'page_title_overlay','page_title_color',
												'container_max_width'])
	page_builder_dt = frappe.db.get_all('Web Page Builder',
										filters={'route': route}, 
										fields=['text_color','is_transparent_sub_header',
												'sub_header_title','sub_header_bg_color',
												'sub_header_bg_img','footer_component', 
												'header_component','enable_sub_header',
												'edit_header_style','is_transparent_header'])
	data = validate_page_builder_dt(page_builder_dt,theme_settings)
	sub_header = data[0]
	header_content = data[1]
	footer_content = data[2]

	return [sub_header,header_content,footer_content]
@frappe.whitelist(allow_guest=True)
def get_page_content_with_pagination(route=None, user=None, customer=None,
										application_type="mobile",seller_classify="All Stores",
										page_no=1,page_size=4):
	try:
		page_content = page_type = list_content = list_style = None
		side_menu = sub_header = None
		if not user:
			customer = get_customer_from_token()
		if user and not customer:
			customer_info = frappe.db.get_all('Customers', filters={'user_id': user})
			if customer_info:
				customer = customer_info[0].name
		page_ = validate_route(customer,application_type,page_no,page_size,route,page_type)
		page_content = page_[0]
		page_type = page_[1]
		page_content = validate_page_section(page_content,seller_classify)
		out = validate_page_type(page_type,route,side_menu,list_content,list_style)
		list_style = out[0]
		side_menu = out[1]
		list_content = out[2]
		header_content = None
		footer_content = None
		if route:
			data = check_route(route)
			sub_header = data[0]
			header_content = data[1]
			footer_content = data[2]
		return {"sub_header":sub_header,"side_menu":side_menu,
				"list_content":list_content,"list_style":list_style,
				"page_type":page_type,"page_content":page_content,
				"header_content":header_content,
				"footer_content":footer_content}
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback(), title='Error in page_content')			

def validate_route(customer,application_type,page_no,page_size,route,page_type):
	page_content = None
	if not route:
		home_page = frappe.db.get_single_value('Website Settings', 'home_page')
		home = frappe.db.get_all('Web Page Builder', 
								filters={'route': home_page}, 
								fields=['name', 'page_type','w_page_type','route'])
		if home:
			page_type = home[0]['w_page_type']
			page_content =  get_page_builder_data_pagination(home[0]["name"], customer,application_type,
													page_no=page_no,page_size=page_size)
		else:{	"status":"failed",
				"message":"Something went wrong"}
	else:
		check_builder = frappe.db.get_all('Web Page Builder', 
											filters={"route":route}, 
											fields=['name', 'page_type','w_page_type','route'])
		frappe.log_error("Web Page builder",check_builder)
		if check_builder:
			page_type = check_builder[0].w_page_type
			if check_builder[0].page_type !="List" and check_builder[0].page_type != "Detail":
				page_content =  get_page_builder_data_pagination(check_builder, customer,application_type,
																page_no=page_no,page_size=page_size)
	return [page_content,page_type]

def validate_page_section(page_content,seller_classify):
	from go1_commerce.go1_commerce.v2.product import get_list_product_details	
	for page_section in page_content:
		if page_section.get("reference_document") == "Product":
			products_data = []
			if page_section.get("data"):
				items_filter = ""
				conditional_products = []
				items_filter = ",".join(['"' + psp.get('name') + '"' for psp in page_section.get("data")])
				conditional_products = get_conditional_products(seller_classify=seller_classify,
																	items_filter=items_filter)
				if conditional_products:
					p_data = get_list_product_details(conditional_products)
					for pr in p_data:
						if pr.get("vendor_price_list"):
							if pr.get("has_variants") == 0:
								products_data.append(pr)
							else:
								for v in pr.get("vendor_price_list"):
									if v.variants:
										products_data.append(pr)
			page_section["data"] = products_data
	return page_content


def check_builder_in_validate_page(check_builder):
	columns = ''
	condition = ''
	order_by = " ORDER BY creation DESC "
	if check_builder[0]['condition']:condition = " WHERE "+check_builder[0]['condition']
	if check_builder[0].sort_field:
		order_by = " ORDER BY " + check_builder[0].sort_field+" "+ check_builder[0].sort_by
	cols_json = json.loads(check_builder[0]['columns_mapping'])
	for x in cols_json:
		for key in x.keys():columns += x[key] +" as " + key + ","
	columns = columns[:-1]
	list_content = frappe.db.sql(f"""SELECT 
										{columns} 
									FROM 
										`tab{check_builder[0].document}` doc 
									{condition} {order_by}""", as_dict=1)
	list_style = check_builder[0].list_style
	if check_builder[0].enable_side_menu:
		s_data = None
		if check_builder[0].data_fetch_from:
			s_data = frappe.db.get_all(check_builder[0].data_fetch_from,fields=['*'])
		side_menu = {"enabled":check_builder[0].enable_side_menu,
					"data":s_data, 'position':check_builder[0].side_menu_position,
					'display_field':check_builder[0].side_menu_display_field}
	else:
		side_menu = {"enabled":0}

	return[list_content, list_style, side_menu]
		

def validate_page_type(page_type,route,list_content,side_menu,list_style):
	if page_type == "List":
		list_content = []
		check_builder = frappe.db.get_all('Web Page Builder', filters={"route":route}, 
										fields=['name','side_menu_display_field','side_menu_position',
												'list_style','page_type','list_style','columns_mapping',
												'document','condition','sort_field','sort_by',
												'enable_side_menu','data_fetch_from'])
		if check_builder:
			data = check_builder_in_validate_page(check_builder)
			list_content = data [0]
			list_style = data [1]
			side_menu = data [2]

	return [list_style,side_menu,list_content]


def enabled_sub_header(page_builder_dt):
	sub_header = {"enabled":1,"sub_header_title":page_builder_dt[0].sub_header_title,
				"sub_header_bg_color":page_builder_dt[0].sub_header_bg_color,
				"is_transparent":page_builder_dt[0].is_transparent_sub_header,
				"text_color":page_builder_dt[0].text_color,
				"container_max_width":page_builder_dt[0].container_max_width,
				"enable_breadcrumbs":page_builder_dt[0].enable_breadcrumbs,
				"page_title_overlay":page_builder_dt[0].page_title_overlay,
				"sub_header_bg_img":page_builder_dt[0].sub_header_bg_img,
				"title_text_align":page_builder_dt[0].title_text_align}
	return sub_header


def not_enabled_sub_header(page_builder_dt, theme_settings):
	sub_header = {"enabled":0}
	if theme_settings:
		if theme_settings[0].enable_page_title:
			sub_header = {"enabled":1,
					"sub_header_title":page_builder_dt[0].name,
					"sub_header_bg_color":theme_settings[0].page_title_bg,
					"sub_header_bg_img":theme_settings[0].page_title_bg_img,
					"is_transparent":theme_settings[0].is_transparent,
					"text_color":theme_settings[0].page_title_color,
					"page_title_overlay":theme_settings[0].page_title_overlay,
					"title_text_align":theme_settings[0].title_text_align,
					"container_max_width":theme_settings[0].container_max_width,
					"enable_breadcrumbs":theme_settings[0].enable_breadcrumbs}
			return sub_header
		
def validate_page_builder_dt(page_builder_dt,theme_settings):
	footer_content = None
	header_content = None
	sub_header = None
	if page_builder_dt:
		if page_builder_dt[0].footer_component:
			footer_content = get_page_footer_info(page_builder_dt[0].footer_component)
		else:
			if theme_settings:
				if theme_settings[0].default_footer:
					footer_content = get_page_footer_info(theme_settings[0].default_footer)
		if page_builder_dt[0].header_component:
			header_content = get_page_header_info(page_builder_dt[0].header_component)
		else:
			if theme_settings:
				if theme_settings[0].default_header:
					header_content = get_page_header_info(theme_settings[0].default_header)
		if page_builder_dt[0].enable_sub_header:
			sub_header = enabled_sub_header(page_builder_dt)
		else:
			sub_header = not_enabled_sub_header(page_builder_dt, theme_settings)
		if page_builder_dt[0].edit_header_style:
			if page_builder_dt[0].is_transparent_header:
				header_content.is_transparent_header = 1
	return [sub_header,header_content,footer_content]



def check_route_in_page_content(route,customer,application_type):
	check_builder = frappe.db.get_all('Web Page Builder',
										filters={"name":route}, 
										fields=['name', 'page_type','w_page_type','route'])
	if check_builder:
		page_type = check_builder[0].w_page_type
		if check_builder[0].page_type !="List" and check_builder[0].page_type != "Detail":
			
			page_content =  get_page_builder_data(check_builder, customer,application_type)
	else:
		return {
			"status":"Failed",
			"message":"Route " + route + "not found."
		}
	return [page_type, page_content]
@frappe.whitelist(allow_guest=True)
def get_page_content(route, user=None, customer=None,application_type="mobile",seller_classify="All Stores"):
	try:
		page_content = page_type = list_content = list_style = None
		side_menu = sub_header = None
		if user and not customer:
			customer_info = frappe.db.get_all('Customers', filters={'user_id': user})
			if customer_info: 
				customer = customer_info[0].name
		if route:
			data = check_route_in_page_content(route,customer,application_type)
			page_type = data[0]
			page_content = data[1]
		customer = get_customer_from_token()
		page_content = validate_page_section(page_content,seller_classify)
		out = validate_page_type(page_type,route,side_menu,list_content,list_style)
		list_style = out[0]
		side_menu = out[1]
		list_content = out[2]
		header_content = None
		footer_content = None
		if route:
			theme_settings = frappe.db.get_all("Web Theme",filters={"is_active":1},
										fields=['default_header','default_footer','enable_page_title',
												'page_title_bg','page_title_tag','title_text_align',
												'page_title_overlay','page_title_color','container_max_width'])
			page_builder_dt = frappe.db.get_all('Web Page Builder', filters={'route': route}, 
										fields=['text_color','is_transparent_sub_header','sub_header_title',
												'sub_header_bg_color','sub_header_bg_img','footer_component',
												'header_component','enable_sub_header','edit_header_style',
												'is_transparent_header'])
			data = validate_page_builder_dt(page_builder_dt,footer_content,theme_settings,header_content,sub_header)
			sub_header = data[0]
			header_content = data[1]
			footer_content = data[2]
		return {"sub_header":sub_header,"side_menu":side_menu,
				"list_content":list_content,"list_style":list_style,
				"page_type":page_type,"page_content":page_content,
				"header_content":header_content,
				"footer_content":footer_content}
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback(), title='Error in page_content')			


def conditional_products_query(items_filter,conditions):
	query = f"""SELECT DISTINCT 
			PP.product, P.item AS ITEM, PP.price_list, PP.name AS product_price,
			(SELECT price FROM `tabProduct Price` pr 
				INNER JOIN `tabPrice List Zone` zpr ON pr.price_list = zpr.parent
				WHERE product = P.name AND price > 0 ORDER BY price LIMIT 1) AS price, 
			P.has_variants, P.short_description, P.tax_category, P.full_description,
			P.sku, P.name, P.route, P.inventory_method, P.minimum_order_qty,
			P.disable_add_to_cart_button, P.weight,PP.old_price,
			P.gross_weight, P.approved_total_reviews, CM.category
		FROM `tabProduct` P
		INNER JOIN `tabProduct Price` PP ON PP.product = P.name
		INNER JOIN `tabPrice List Zone` Z ON PP.price_list = Z.parent
		INNER JOIN `tabProduct Category Mapping` CM ON CM.parent = P.name
		INNER JOIN `tabProduct Category` PC ON CM.category = PC.name
		WHERE P.is_active = 1 AND P.show_in_market_place = 1 
			AND PP.price > 0 AND P.status = 'Approved'
			AND P.name IN ({items_filter}) {conditions}
		GROUP BY PP.product"""
	
	return query
	
def get_conditional_products(seller_classify,items_filter):
	conditions = ""
	catalog_settings = frappe.get_single('Catalog Settings')
	seller_classify_cond = ""
	if seller_classify!="All Stores":
		seller_classify_cond = "AND AB.business_classification='" + seller_classify + "'"
	query = no_stock_products_yuery(items_filter,conditions,seller_classify_cond)
	if catalog_settings.no_stock_products==1:
		query = conditional_products_query(items_filter,conditions)
	result = frappe.db.sql(query, as_dict=True)
	return result

def no_stock_products_yuery(items_filter,conditions,seller_classify_cond):
	query = f"""SELECT DISTINCT 
				PP.product, P.item, PP.price_list,P.full_description,P.route AS brand_route 
				PP.name AS product_price,P.has_variants, P.short_description,P.tax_category,
				P.brand_name AS product_brand (
					SELECT price 
					FROM `tabProduct Price` PR 
					INNER JOIN `tabPrice List Zone` ZPR 
					ON PR.price_list = ZPR.parent 
					WHERE product = P.name AND price > 0 
					ORDER BY price 
					LIMIT 1) AS price, PP.old_price,
				P.sku, P.name, P.route, P.inventory_method, P.minimum_order_qty,P.image AS product_image,
				P.disable_add_to_cart_button, P.weight,P.approved_total_reviews,CM.category,P.gross_weight
			FROM `tabProduct` P 
			INNER JOIN `tabProduct Price` PP 
				ON PP.product = P.name 
			INNER JOIN `tabProduct Category Mapping` CM 
				ON CM.parent = P.name 
			INNER JOIN `tabProduct Category` PC 
				ON CM.category = PC.name 
			WHERE P.is_active = 1 AND P.show_in_market_place = 1 AND
				PP.price > 0 AND P.status = 'Approved' 
			AND (CASE WHEN (P.has_variants = 1 AND 
				EXISTS (SELECT VC.name 
						FROM `tabProduct Variant Combination` VC 
						WHERE VC.show_in_market_place = 1 '{seller_classify_cond}' AND 
							VC.disabled = 0 THEN 1 = 1 
					WHEN (P.has_variants = 0 THEN 1 = 1 ELSE 1 = 0 END) 
			AND P.name IN (%s) %s GROUP BY PP.product """ % (items_filter, conditions)
	return query

@frappe.whitelist(allow_guest=True)
def check_domain(domain_name):
	try:
		from frappe.core.doctype.domain_settings.domain_settings import get_active_domains
		domains_list = get_active_domains()
		domains = frappe.cache().hget('domains', 'domain_constants')
		if not domains:
			return False
		if domains[domain_name] in domains_list:
			return True
		return False
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback(), title='Error in check_domain')


def get_page_header_info(header_id):
	header_list = frappe.db.get_all("Header Component",
									filters={"name":header_id},
								fields=['is_transparent_header','title','is_menu_full_width',
										'layout_json','enable_top_menu','sticky_on_top','is_dismissable',
										'layout','sticky_header','call_to_action_button','button_text',
										'button_link','link_target','is_transparent_header',
										'sticky_header_background','menu_text_color'])
	if header_list:
		path = frappe.utils.get_files_path()
		file_path = os.path.join(path, 'data_source', (header_id.lower().replace(' ','_')  + '_web.json'))
		if os.path.exists(file_path):
			with open(file_path) as f:
				data = json.loads(f.read())
				lists = get_page_header_info_data(data)
			header_list[0].items = lists
			if header_list[0].enable_top_menu==1:
				left_items = get_page_header_info_left_items(header_id)
				right_items = get_page_header_info_right_items(header_id)
				header_list[0].top_menu = { "left_items":left_items,
											"right_items":right_items}
		return header_list[0]
	return None

def get_page_header_info_right_items(header_id):
	right_items = frappe.db.sql(""" SELECT 
										menu_label,redirect_url,icon 
									FROM `tabMenus Item` 
									WHERE position='Right' AND parent=%(menu_id)s 
										AND parentfield='top_menus' 
										AND (parent_menu IS NULL OR parent_menu='') 
									ORDER BY idx""",{"menu_id":header_id},as_dict=1)
	for x in right_items:
		x.child_menu = frappe.db.sql("""SELECT 
											menu_label,redirect_url,icon 
										FROM `tabMenus Item` 
										WHERE position='Right' AND parent=%(menu_id)s 
											AND parentfield='top_menus' 
											AND parent_menu=%(parent_menu)s 
										ORDER BY idx""",{"parent_menu":x.menu_label,
														"menu_id":header_id},as_dict=1)
		for sub_menu in x.child_menu:
			sub_menu.child_menu =  frappe.db.sql("""SELECT 
														menu_label,redirect_url,icon 
													FROM `tabMenus Item` 
													WHERE position='Right' AND parent=%(menu_id)s 
														AND parentfield='top_menus' 
														AND parent_menu=%(parent_menu)s 
													ORDER BY idx""",
														{"parent_menu":sub_menu.menu_label,
															"menu_id":header_id},as_dict=1)
	return right_items

def get_page_header_info_left_items(header_id):
	left_items =  frappe.db.sql(""" SELECT 
										menu_label,redirect_url,icon 
									FROM `tabMenus Item` 
									WHERE position = 'Left' AND parent=%(menu_id)s AND 
										parentfield = 'top_menus' AND (parent_menu IS NULL OR 
										parent_menu = '') 
									ORDER BY idx""",{"menu_id":header_id},as_dict=1)
	for x in left_items:
		x.child_menu = frappe.db.sql("""SELECT
											menu_label,redirect_url,icon 
										FROM `tabMenus Item` 
										WHERE position='Left' AND parent=%(menu_id)s AND 
											parentfield='top_menus' AND 
											parent_menu=%(parent_menu)s 
										ORDER BY idx""",
												{"parent_menu":x.menu_label,
													"menu_id":header_id},as_dict=1)
		for sub_menu in x.child_menu:
			sub_menu.child_menu = frappe.db.sql(""" SELECT 
														menu_label,redirect_url,icon 
													FROM `tabMenus Item` 
													WHERE position='Left' AND parent=%(menu_id)s 
														AND parentfield='top_menus' 
														AND parent_menu=%(parent_menu)s 
													ORDER BY idx""",
													{"parent_menu":sub_menu.menu_label,
													"menu_id":header_id},as_dict=1)
	return left_items


def page_header_child_menu(x,menu):
	x.child_menu = frappe.db.sql("""SELECT 
										menu_label,redirect_url,icon,mega_m_col_index 
									FROM `tabMenus Item` 
									WHERE parent=%(menu_id)s AND parentfield='menus' 
										AND parent_menu=%(parent_menu)s 
									ORDER BY idx""",{"parent_menu":x.menu_label,
														"menu_id":menu[0].name},as_dict=1)
	for sub_menu in x.child_menu:
		sub_menu.child_menu = frappe.db.sql(""" SELECT 
													menu_label,redirect_url,icon 
												FROM `tabMenus Item` 
												WHERE parent=%(menu_id)s 
													AND parentfield='menus' 
													AND parent_menu=%(parent_menu)s 
												ORDER BY idx""",
												{"parent_menu":sub_menu.menu_label,
													"menu_id":menu[0].name},as_dict=1)
def get_page_header_info_data(data):
	lists = []
	for item in data:
		if item.get('section_type')=="Menu":
			page_section_menu = frappe.get_value("Page Section",item.get('section'),"menu")
			menu = frappe.db.get_all("Menu",
									filters={"name":page_section_menu},
									fields=['is_static_menu','name'])
			if menu:
				item["is_static_menu"] = menu[0].is_static_menu
				menu_id = menu[0].name
				query = f"""SELECT 
								menu_label,redirect_url,is_mega_menu,no_of_column 
							FROM `tabMenus Item` 
							WHERE parent= '{menu_id}' AND (parent_menu IS NULL OR parent_menu='') 
							ORDER BY idx""" 
				parent_menus = frappe.db.sql(query,as_dict=1)
				for x in parent_menus:
					page_header_child_menu(x,menu)
				item["menus"] = parent_menus
		lists.append(item)
	return lists

def get_page_footer_info(footer_id):
	footer_list = frappe.db.get_all("Footer Component",filters={"name":footer_id},
										fields=['title','enable_link_icon','layout_json','enable_copyright',
												'copyright_layout','fc_ct_type','cp_fc_alignment',
												'sc_ct_type','cp_sc_alignment','cp_fc_content','cp_sc_content'])
	if footer_list:
		path = frappe.utils.get_files_path()
		with open(os.path.join(path, 'data_source', (footer_id.lower().replace(' ','_')  + '_web.json'))) as f:
			data = json.loads(f.read())
			lists = []
			for item in data:
				if item.get('section_type')=="Menu":
					page_section_menu = frappe.get_value("Page Section",item.get('section'),"menu")
					menu = frappe.db.get_all("Menu",filters={"name":page_section_menu},
													fields=['is_static_menu','name'])
					if menu:
						parent_menus = frappe.db.sql("""SELECT 
															menu_label,redirect_url 
														FROM `tabMenus Item` 
														WHERE parent=%(menu_id)s AND 
															(parent_menu IS NULL OR parent_menu='') 
														ORDER BY idx""",{"menu_id":menu[0].name},as_dict=1)
						item["menus"] = parent_menus
				lists.append(item)
		g_list = []
		column_indexes = frappe.db.sql("""	SELECT 
												column_index 
											FROM `tabMobile Page Section` 
											WHERE parent=%(f_id)s 
											GROUP BY column_index""",{"f_id":footer_id},as_dict=1)
		for x in column_indexes:
			result = [m for m in lists if m.get("column_index") == x.get("column_index")] 
			g_list.append({"column_index":x.column_index,"items":result})
		footer_list[0].items = g_list
		if footer_list[0].layout_json:
			footer_list[0].layout_json_data=json.loads(footer_list[0].layout_json)
		return footer_list[0]
	return None

@frappe.whitelist(allow_guest=True)
def send_otp(mobile_no,doctype="Customer"):
	if doctype == "SE":
		check_mobile = frappe.db.get_all("Employee",filters = {"mobile_no":mobile_no})
		if not check_mobile:
			return {"status":"Failed",
					"message":"Employee not found."}
	if doctype == "Vendor":
		usr = frappe.db.get_all("Shop User",filters={"mobile_no":mobile_no},
								fields=["email","name","full_name","restaurant"])
		if not usr:
			return {"status":"Failed",
					"message":"Seller not found associated with this mobile no.."}
	from frappe.utils.data import add_to_date
	from frappe.utils import now
	platform_settings = frappe.get_single('Order Settings')
	check_exist = frappe.db.get_all("User OTP Verification",filters={"mobile_number":mobile_no})
	otp_doc = None
	if not check_exist:
		otp_doc = frappe.get_doc({
			'doctype':'User OTP Verification',
			'mobile_number':mobile_no,
			'otp':generate_random_nos(platform_settings.otp_length),
			'expiry_on': add_to_date(now(),seconds=int(platform_settings.otp_expiry),as_datetime=True)
		})
	else:
		otp_doc = frappe.get_doc("User OTP Verification",check_exist[0].name)
		otp_doc.otp=generate_random_nos(platform_settings.otp_length)
		otp_doc.expiry_on=add_to_date(now(),seconds=int(platform_settings.otp_expiry),as_datetime=True)
	otp_doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status":"Success","message":"OTP sent successfully."}

@frappe.whitelist(allow_guest=True)
def validate_otp(mobile_no,otp,doctype):
	check_otp = frappe.db.get_all("User OTP Verification",
								filters={"mobile_number":mobile_no,"otp":otp,"expiry_on":(">=",now())})
	if check_otp:
		if doctype == "Customer":
			customer_login_resp = customer_login(mobile_no)
			if customer_login_resp.get("status")=="Success":
				return customer_login_resp
			else:
				return customer_registration_login(mobile_no)
		# if doctype == "SE":
		# 	check_mobile = frappe.db.get_all("Employee",
		# 								filters={"mobile_no":mobile_no},
		#   								fields=['name','email_id','role','full_name','designation'])
		# 	if check_mobile:
		# 		token = get_auth_token(check_mobile[0].email_id)
		# 		login_response = {}
		# 		if token:
		# 			login_response['api_key'] = token['api_key']
		# 			login_response['api_secret'] = token['api_secret']
		# 			login_response['status'] = "Success"
		# 			login_response['role'] = check_mobile[0].role
		# 			login_response['full_name'] = check_mobile[0].full_name
		# 			login_response['designation'] = check_mobile[0].designation
		# 		return login_response
		# 	else:
		# 		return {"status":"Failed","message":"Employee not found."}
		# if doctype == "Vendor":
		# 	return vendor_login(mobile_no)
	else:
		return {"status":"Failed","message":"Invalid OTP or OTP expired."}
	
def customer_login(phone):
	usr = frappe.db.get_all("Customers",filters={"phone":phone},fields=["email","name","full_name"])
	if usr:
		token = get_auth_token(usr[0].email)
		if token:
			has_role = frappe.db.get_all('Has Role',
							filters={'parent': usr[0].email, 'role': "Customer"})
			if not has_role:
				frappe.local.response.http_status_code = 500
				frappe.local.response.status = "Failed"
				frappe.local.response.message = "You dont have access."
				return
			return {'type':'Customer',
					'api_key': token['api_key'],
					'api_secret': token['api_secret'],
					'customer_id':usr[0].name,
					'customer_email':usr[0].email,
					'customer_name':usr[0].full_name,
					'status':"Success",
					"message":"OTP verfied successfully."}
	return {"status":"Failed"}

def vendor_login(phone):
	usr = frappe.db.get_all("Shop User",filters={"mobile_no":phone},
										fields=["email","name","full_name"])
	if usr:
		token = get_auth_token(usr[0].email)
		if token:
			has_role = frappe.db.get_all('Has Role',
							filters={'parent': usr[0].email, 'role': "Vendor"})
			if not has_role:
				frappe.local.response.http_status_code = 500
				frappe.local.response.status = "Failed"
				frappe.local.response.message = "You dont have access."
				return
			return {'type':'Vendor',
					'api_key': token['api_key'],
					'api_secret': token['api_secret'],
					'id':usr[0].name,
					'email':usr[0].email,
					'full_name':usr[0].full_name,
					'status':"Success",
					"message":"OTP verfied successfully."}
	return {"status":"Failed"}

def customer_registration_login(phone):
	import string
	import random
	pwd = str(''.join(random.choices(string.ascii_uppercase +
								 string.digits, k=8)))
	catalog_settings = frappe.get_single('Catalog Settings')
	email = phone+"@"+catalog_settings.site_name+".com"
	order_settings = frappe.get_single('Order Settings')
	if not order_settings.auto_customer_approval:
		usr = frappe.db.get_value("Customer Registration",{"phone":phone})
		if usr:
			cus_reg = frappe.get_doc("Customer Registration",usr)
			if not cus_reg.uuid:
				import uuid
				cus_reg.uuid  = uuid.uuid4().hex
				cus_reg.save(ignore_permissions=True)
				frappe.db.commit()
			return {'type':'Customer Registration',
					'data':cus_reg,
					'status':"Success",
					"message":"OTP verfied successfully."}
		else:
			import uuid
			cus_reg = frappe.new_doc("Customer Registration")
			cus_reg.phone = phone
			cus_reg.uuid  = uuid.uuid4().hex
			cus_reg.save(ignore_permissions=True)
			frappe.db.commit()
			return {'type':'Customer Registration',
					'data':cus_reg,
					'status':"Success",
					"message":"OTP verfied successfully."}	
	else:
		status = "Waiting for Approval" if not order_settings.auto_customer_approval else "Approved"
		cus_reg = frappe.new_doc("Customers")
		cus_reg.phone = phone
		cus_reg.first_name = phone
		cus_reg.email = email
		cus_reg.new_password  = pwd
		cus_reg.customer_status = status
		cus_reg.save(ignore_permissions=True)
		frappe.db.commit()
		token = get_auth_token(email)
		if token:
			has_role = frappe.db.get_all('Has Role',
							filters={'parent': email, 'role': "Customer"})
			if not has_role:
				frappe.local.response.http_status_code = 500
				frappe.local.response.status = "Failed"
				frappe.local.response.message = "You dont have access."
				return
			return {
					'type':'Customer',
					'api_key': token['api_key'],
					'api_secret': token['api_secret'],
					'customer_id':cus_reg.name,
					'customer_email':cus_reg.email,
					'customer_name':cus_reg.full_name,
					'status':"Success",
					"message":"OTP verfied successfully."
				}	
		return {"status":"Failed"}

def generate_random_nos(n):
	from random import randint
	range_start = 10**(n-1)
	range_end = (10**n)-1
	return randint(range_start, range_end)

def get_page_builder_data(page, customer=None,application_type="mobile"):
	path = frappe.utils.get_files_path()
	import os
	if page[0].page_type == 'Adaptive':
		ptype =  ('_web')
		if application_type == "mobile":
			ptype =  ('_mobile')
	else:
		ptype = ('_web')
	use_page_builder = 1
	page_builders = frappe.db.get_all("Web Page Builder",filters={"name":page[0].name},
											fields=['use_page_builder'])
	if page_builders:
		use_page_builder = page_builders[0].use_page_builder
	file_path = os.path.join(path, 'data_source', (page[0].name.lower().replace(' ','_') + ptype + '.json'))
	if use_page_builder:
		with open(file_path) as f:
			data = json.loads(f.read())
			from go1_cms.go1_cms.doctype.page_section.page_section import get_data_source
			lists = []
			for item in data:
				if item.get('login_required') == 1 and customer:
					doc = frappe.get_doc('Page Section', item.get('section'))
					item['data'] = get_data_source(doc.query, doc.reference_document, doc.no_of_records, 1, 
													customer)
				if item.get('dynamic_data') == 1:
					item_list = ['Slider','Predefined Section', 'Custom Section', 'Lists', 'Tabs']
					if item['section_type'] in item_list:
						doc = frappe.get_doc('Page Section', item.get('section'))
						item = doc.run_method('section_data', customer=customer,add_info=None)
				if item.get('section_type')=="Dynamic":
					fields=["name","conditions","page_section","section_type","section_title",
							"reference_document","sort_field","sort_by","custom_section_data",
							"is_editable","dynamic_id","field_list","no_of_records","background_color",
							"text_color"]
					doc = frappe.get_list('Child Page Section',
											filters={"page_section":item.get('section')},fields = fields)
					child_section_data = []
					for d in doc:
						sections ={}
						sections['section_title']= d['section_title']
						sections['section_type'] = d['section_type']
						if d['section_type']=="Dynamic Section":
							value = get_page_builder_query(d)
							query = value[0]
							field_list = value[1]
							res_data = get_page_builder_result(query,d,field_list)
							sections['data'] = res_data
						child_section_data.append(sections)
					item['child_section_data'] = child_section_data
				lists.append(item)
			return lists
	else:
		fields = ['content','name','use_page_builder']
		return frappe.db.get_all("Web Page Builder",filters={"name":page[0].name},fields = fields)

@frappe.whitelist()
def generate_option_unique_names():
	try:
		p_options = frappe.db.sql(""" 	SELECT 
											name,attribute,option_value 
										FROM `tabProduct Attribute Option` """,as_dict=1)
		from frappe.website.utils import cleanup_page_name 
		for x in p_options:
			route = (frappe.db.get_value("Product Attribute",x.attribute,"attribute_name").lower())
			attr_route = cleanup_page_name(route)
			attr_route = attr_route.replace("-","_")
			option_route = cleanup_page_name(x.option_value.lower().strip())
			option_route = option_route.replace("-","_")
			frappe.db.set_value("Product Attribute Option",x.name,"unique_name",attr_route+"_"+option_route)
		frappe.db.commit()
	except Exception:
		frappe.log_error(title = "Error in generate_option_unique_names", message = frappe.get_traceback())

@frappe.whitelist()
def get_city_based_role():
	m_settings = frappe.get_single("Market Place Settings")
	roles = ",".join(['"' + x.role + '"' for x in m_settings.city_based_role])
	frappe.log_error("roles",roles)
	return roles

@frappe.whitelist()
def generate_combination_options():
	try:
		combinations = frappe.db.get_all("Product Variant Combination",
												filters={"disabled":0,"show_in_market_place":1},
												fields=['name','parent','attribute_id'])
		
		for v in combinations:
			if v.attribute_id:
				attribute_ids = v.attribute_id.split('\n')
				for	opt in attribute_ids:
					if opt:
						if not frappe.db.get("Combination Option Mapping",
										filters={"product_id":v.name,"combination_id":v.name,"option_id":opt}):
							frappe.get_doc({
								"doctype": "Combination Option Mapping",
								"product_id": v.parent,
								"combination_id": v.name,
								"option_id":opt}).insert()
		frappe.db.commit()
	except Exception:
		frappe.log_error(title = "Error in generate_combination_options", message = frappe.get_traceback())

def update_device_id(doctype,docname,device_id,role):
	if not frappe.db.get_all("App Alert Device",filters={"user":docname}):
		app_device = frappe.get_doc({
				"doctype": "App Alert Device",
				"document": doctype,
				"user": docname,
				"device_id":device_id,
				"role":role
			})
		app_device.save(ignore_permissions=True)
	else:
		device_list = frappe.db.get_all("App Alert Device",filters={"user":docname})
		if device_list:
			device_doc = frappe.get_doc("App Alert Device",device_list[0].name)
			device_doc.device_id = device_id
			device_doc.save(ignore_permissions=True)
	frappe.db.commit()

@frappe.whitelist(allow_guest=True)
def get_blog_list(category=None,page_no=1,page_size=12):
	condition = ""
	if category:
		condition = " AND blog_category = '%s' "%(category)
	bloglist_query = f"""SELECT name,title,thumbnail_image,blog_intro,published_on,route 
						FROM 
							`tabBlog Post` 
						WHERE published = 1 %s 
						ORDER BY published_on DESC  
						LIMIT %s,%s """%(condition,(int(page_no) - 1) * int(page_size),page_size)
	return frappe.db.sql(bloglist_query,as_dict=1)

@frappe.whitelist(allow_guest=True)
def get_blog_categories():
	bloglist_query = f"""SELECT name,title,route 
						FROM 
							`tabBlog Category` 
						WHERE published = 1 
						ORDER BY creation DESC """
	return frappe.db.sql(bloglist_query,as_dict=1)

@frappe.whitelist(allow_guest=True)
def get_blog_details(route):
	try:
		blog_details = frappe.db.sql("""SELECT B.*,BR.full_name AS blogger_full_name,BR.bio,BR.avatar 
										FROM 
											`tabBlog Post` B 
										LEFT JOIN 
											`tabBlogger` BR 
											ON BR.name = B.blogger 
										WHERE published = 1 AND B.route=%(b_route)s""",
											{"b_route":route},as_dict=1)
		if blog_details:
			condition = " AND blog_category = '%s' "%(blog_details[0].blog_category)
			related_bloglist_query = 	f"""SELECT B.name, B.title, B.thumbnail_image, B.blog_intro,
												B. published_on, B.route 
											FROM `tabBlog Post` B 
											WHERE B.published = 1 AND 
												B.route <> '{route}' {condition} 
											ORDER BY published_on DESC 
											LIMIT 0, 6"""
			related_bloglist = frappe.db.sql(related_bloglist_query,as_dict=1)
			comments = frappe.db.get_all("Blog Comments",
									filters={"blog_name":blog_details[0].name},
									fields=["name1","email","comments","creation"],
									order_by="creation desc")
			return {"status":"success",
					"blog_details":blog_details[0],
					"related_bloglist":related_bloglist,
					"comments":comments}
		else:
			return {"status":"failed","Message":"Not Found"}
	except Exception:
		frappe.log_error(title = "Error in get_blog_details", message = frappe.get_traceback())

@frappe.whitelist(allow_guest=True)
def insert_blog_comments(data):
	try:
		doc = data
		if isinstance(doc, string_types):
				doc = json.loads(doc)
		response=doc
		blog=frappe.new_doc('Blog Comments')
		blog.blog_name=response.get('blog')
		blog.name1=response.get('user_name')
		blog.email=response.get('email')
		blog.comments=response.get('message')
		blog.save(ignore_permissions=True)
		return blog.__dict__
	except Exception:
		frappe.log_error(title = "Error in insert_blog_comments", message = frappe.get_traceback())

@frappe.whitelist()
def get_blogger_bloglist(customer_email):
	try:
		check_blogger = frappe.db.get_all("Blogger",filters={"user":customer_email})
		blogger_id = None
		if check_blogger:
			blogger_id = check_blogger[0].name
		fields=['name','title','blog_category','published_on','route','published','thumbnail_image']
		return frappe.db.get_all("Blog Post",filters={"blogger":blogger_id},fields=fields)
	except Exception:
		frappe.log_error(title = "Error in get_blogger_bloglist", message = frappe.get_traceback())


def customer_web_permission(doc, ptype, user, verbose=False):
	try:
		if 'Customer' in frappe.get_roles(user) or 'Vendor' in frappe.get_roles(user):
			if doc.email == user:
				return True
			else:
				return False
		else:
			return False
	except Exception:
		frappe.log_error('Error in v2.common.customer_web_permission', frappe.get_traceback())
  

def login_customer(login_manager):
	try:
		if frappe.session.user != 'Guest':
			customer = frappe.db.get_all('Customers',
								filters={'user_id': frappe.session.user},
								fields=['name'])
			if customer:
				frappe.local.cookie_manager.set_cookie('customer_id', customer[0].name)
				move_cart_items(customer[0].name)
		guest_sid = frappe.request.cookies.get('guestsid')
		if guest_sid:
			frappe.cache().hdel(guest_sid, 'locations_list')
			frappe.cache().hdel(guest_sid, 'destinations_list')
			frappe.cache().hdel(guest_sid, 'user_location')
			frappe.local.cookie_manager.delete_cookie('guestsid')
	except Exception:
		frappe.log_error('Error in v2.common.login_customer', frappe.get_traceback())



@frappe.whitelist()
def move_cart_items(customer, guest_id=None):
	try:
		if not guest_id:
			guest = frappe.request.cookies.get('guest_customer')
		else:
			guest = guest_id
		if guest:
			guest_cart = frappe.db.get_all('Shopping Cart', 
								  filters={'customer': guest, 'cart_type': 'Shopping Cart'}, 
								  fields=['name', 'business'])
			if guest_cart:
				update_cart('Shopping Cart', customer, guest, guest_cart)
			guest_cart2 = frappe.db.get_all('Shopping Cart', 
								   filters={'customer': guest, 'cart_type': 'Wishlist'}, 
								   fields=['name', 'business'])
			if guest_cart2:
				update_cart('Wishlist', customer, guest, guest_cart2)
			recently_viewed_products = frappe.get_all('Customer Viewed Product',
											fields=['product'], 
											filters={'parent': guest_id}, order_by='viewed_date desc')
			if recently_viewed_products:
				update_recently_viewed_products(guest_id, customer)
	except Exception:
		frappe.log_error('Error in v2.common.move_cart_items',frappe.get_traceback())


def update_cart(cartType, customer, guest, guest_cart_info):
	try:
		guest_cart = guest_cart_info[0].name
		cart = frappe.db.get_all('Shopping Cart', 
									filters={'customer': customer, 'cart_type': cartType}, 
									fields=['*'])
		if cart:
			cartitems = frappe.db.get_all('Cart Items', filters={'parent': cart[0].name})
			if cartitems:
				validate_cart_items(guest_cart, cart)
			else:
				frappe.db.sql('''UPDATE `tabCart Items` 
								SET parent = %(n_parent)s 
								WHERE parent = %(parent)s
							''', {'n_parent': cart[0].name, 'parent': guest_cart})

			parent_doc = frappe.get_doc('Shopping Cart', cart[0].name)
			parent_doc.flags.update({'__update': True})
			parent_doc.save(ignore_permissions=True)
		else:
			doc = frappe.get_doc('Shopping Cart', guest_cart)
			doc.customer = customer
			doc.customer_name = frappe.db.get_value('Customers',customer, 'full_name')
			doc.flags.update({'__update': True})
			doc.save(ignore_permissions=True)
	except Exception:
		frappe.log_error('Error in v2.common.update_cart', frappe.get_traceback())


def validate_cart_items(guest_cart, cart):
	g_cart_items = frappe.db.get_all('Cart Items', 
								filters={'parent': guest_cart, 'is_free_item': 0}, 
								fields=['product', 'name', 'quantity', 'price'])
	if g_cart_items:
		for item in g_cart_items:
			g_item = frappe.db.get_all('Cart Items', 
									fields=['product', 'name', 'quantity'],
									filters={
											'parent': cart[0].name,
											'product': item.product,
											'attribute_description': item.attribute_description
											})
			if g_item:
				item_info = frappe.get_doc('Product', g_item[0].product)
				if item_info:
					validate_item_info(item, g_item, item_info)
				frappe.db.sql('''UPDATE FROM `tabCart Items` 
								WHERE name = %(name)s
							''', {'name': item.name})
			else:
				frappe.db.sql('''UPDATE `tabCart Items` 
								SET parent = %(parent)s 
								WHERE name = %(name)s
							''', {'parent': cart[0].name, 'name': item.name})


def validate_item_info(item, g_item, item_info):
	qty = float(item.quantity) + float(g_item[0].quantity)
	if item_info.inventory_method == 'Dont Track Inventory':
		frappe.db.sql('''UPDATE `tabCart Items` 
						SET quantity = {qty} 
						WHERE name = %(name)s
					'''.format(qty = qty),{'name': g_item[0].name})

		frappe.db.sql('''UPDATE `tabCart Items` 
						SET total = {total} 
						WHERE name = %(name)s
					'''.format(total = float(item.price)	* float(qty)), 
						{'name': g_item[0].name})

	elif item_info.inventory_method == 'Track Inventory':
		if item_info.stock >= g_item[0].quantity:
			frappe.db.sql('''UPDATE `tabCart Items` 
							SET quantity = {qty} 
							WHERE name = %(name)s
						'''.format(qty = float(qty)),{'name': g_item[0].name})

			frappe.db.sql('''UPDATE `tabCart Items` 
							SET total = {total} 
							WHERE name = %(name)s
						'''.format(total=float(item.price)	* float(qty)), 
							{'name': g_item[0].name})


@frappe.whitelist(allow_guest=True)
def update_recently_viewed_products(guest_id, customer_id):
	recently_viewed_products = frappe.get_all('Customer Viewed Product', 
											fields=['product', 'viewed_date', 'name'],
											filters={'parent': guest_id}, order_by='viewed_date desc')
	for x in recently_viewed_products:
		frappe.enqueue("go1_commerce.go1_commerce.api.\
				delete_viewed_products",customer_id = customer_id, name = x.name, product = x.product)


@frappe.whitelist(allow_guest=True)
def create_help_article_json(doc, method):
	import frappe.modules
	module = frappe.modules.get_doctype_module(doc.doctype_name)
	module_name = frappe.db.sql('''SELECT * 
									FROM `tabModule Def` 
									WHERE name = %(name)s 
								''',{'name': module}, as_dict=True)

	path = frappe.get_module_path(module_name[0].module_name)
	url = path
	if not os.path.exists(os.path.join(url,'help_desk')):
		frappe.create_folder(os.path.join(url,'help_desk'))
	file_path = os.path.join(url, 'help_desk', 'help_article.json')
	temp1 = []
	temp = {}
	if os.path.exists(file_path):
		with open(file_path, 'r') as f:
			data = json.load(f)
			try:
				if data[doc.doctype_name]:
					temp1.append({
									'title': doc.title,
									'category':doc.category,
         							'domain_name':doc.domain_name,
									'content':doc.content,
									'published':doc.published, 
									'doctype':doc.doctype_name
								})
					data[doc.doctype_name] = temp1
			except Exception as e:
				temp1.append({
								'title': doc.title,
								'category':doc.category,
								'domain_name':doc.domain_name,
								'content':doc.content,
								'published':doc.published, 
								'doctype':doc.doctype_name
							})
				data[doc.doctype_name] = temp1
		with open(os.path.join(url,'help_desk', ('help_article.json')), "w") as f:
			f.write(frappe.as_json(data))
	else:
		temp1.append({
						'title': doc.title,
						'category':doc.category,
						'domain_name':doc.domain_name,
						'content':doc.content,
						'published':doc.published, 
						'doctype':doc.doctype_name
					})
		temp[doc.doctype_name] = temp1
		with open(os.path.join(url,'help_desk', ('help_article.json')), "w") as f:
			f.write(frappe.as_json(temp))


@frappe.whitelist(allow_guest=True)
def get_domains_data():
	try:
		import os
		domain_constants = None
		path = frappe.get_module_path('go1_commerce')
		file_path = os.path.join(path, 'domains.json')
		if os.path.exists(file_path):
			with open(file_path) as f:
				data = json.loads(f.read())
				domain_constants = data
				frappe.cache().hset('domains', 'domain_constants', domain_constants)
		return domain_constants
	except Exception:
		frappe.log_error('Error in v2.common.get_domains_data', frappe.get_traceback())


def get_custom_translations(messages, language):
	translations = frappe.db.sql('''SELECT source_text, translated_text 
                              		FROM `tabTranslation` 
									WHERE language = %(lang)s
								''', {'lang': language}, as_dict=1)
	for item in translations:
		messages[item.source_name] = item.target_name
	return messages


def get_business_defaults():
	defaults = frappe.cache().hget("defaults", 'Business')

	if not defaults:
		res = frappe.db.sql("""SELECT defkey, defvalue, parent 
								FROM `tabDefaultValue`
								WHERE parenttype = %s 
								ORDER BY creation
							""", ('Business'), as_dict=1)
		defaults = frappe._dict({})
		for d in res:
			defaults[d.parent] = d.defvalue
		frappe.cache().hset("defaults", 'business', defaults)
	return defaults


def boot_session(bootinfo):
	try:
		defaults = get_settings('Catalog Settings')
		if defaults.get('default_currency'):
			bootinfo.sysdefaults.currency = defaults.default_currency
		bootinfo.docs += frappe.db.sql("""SELECT name, fraction, fraction_units,number_format, 
												smallest_currency_fraction_value, symbol 
											FROM tabCurrency
											WHERE enabled = 1
										""", as_dict = 1, 
										update = {'doctype': ':Currency'})
		filters = {}
		if check_domain('single_vendor'):
			filters = {'name': frappe.db.get_single_value('Core Settings', 'default_business')}
		if "System Manager" not in frappe.get_roles(frappe.session.user):
			settings = frappe.db.get_all('Business', fields=['name'], filters=filters)
			if settings:
				bootinfo.sysdefaults.business = settings[0].name
		# domain_configuration = frappe.get_single('Server Configuration')
		# bootinfo.sysdefaults.domain_configuration = domain_configuration
		translation_settings = frappe.get_single('Core Settings')
		bootinfo.sysdefaults.translation_settings = translation_settings
		doc_list = frappe.db.sql('''SELECT enbled_doctype 
									FROM `tabEnabled Doctypes` 
									WHERE parent = "Core Settings"
								''', as_dict=1)
		tan_enabled_docs = []
		for n in doc_list:
			tan_enabled_docs.append(n.enbled_doctype)
		bootinfo.sysdefaults.translation_enabled_docs = tan_enabled_docs
		domains = []
		domains = get_domains_data()
		bootinfo.sysdefaults.domain_constants = domains
		bootinfo['__messages'] = get_custom_translations(bootinfo['__messages'], bootinfo.lang)
		bootinfo.sysdefaults.business_defaults = get_business_defaults()
		apps = frappe.get_installed_apps()
		for app in apps:
			module_name = frappe.db.sql(''' SELECT * 
											FROM `tabModule Def` 
											WHERE app_name = %(app_name)s 
										''',{'app_name': app}, as_dict=True)
			for module in module_name:
				path = frappe.get_module_path(module.module_name)
				url = path
				help_dek = "help_article.json"
				file_path = os.path.join(url, 'help_desk', help_dek)
				if os.path.exists(file_path):
					with open(file_path, 'r') as f:
						out = json.load(f)
					bootinfo.sysdefaults[module.module_name] = out
	except Exception:
		frappe.log_error('Error in v2.common.boot_session', frappe.get_traceback())