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
from frappe.query_builder import DocType, Order

@frappe.whitelist()
def generate_all_settings(doc,method):
	try:
		frappe.log_error("check settings","settings")
		res_data = 	{
						"catalog_settings":(frappe.get_single("Catalog Settings")).as_dict(),
						"order_settings":(frappe.get_single("Order Settings")).as_dict(),
						"cart_settings":(frappe.get_single("Shopping Cart Settings")).as_dict(),
						"wallet_settings":(frappe.get_single("Wallet Settings")).as_dict(),
						"social_tracking_codes":(frappe.get_single("Social Tracking Codes")).as_dict()
					}
		path = get_files_path()
		if not os.path.exists(os.path.join(path,'settings')):
			frappe.create_folder(os.path.join(path,'settings'))
		with open(os.path.join(path,'settings', 'all_settings.json'), "w") as f:
			content = json.dumps(json.loads(frappe.as_json(res_data)), separators=(',', ':'))
			f.write(content)
	except Exception:
		frappe.log_error(title = "Error in generate_all_settings",
						 message = frappe.get_traceback())



@frappe.whitelist(allow_guest=True)
def get_all_website_settings():
	try:
		import os
		path = get_files_path()
		file_path = os.path.join(path, "settings/all_website_settings.json")
		all_categories = None
		if os.path.exists(file_path):
				f = open(file_path)
				all_categories = json.load(f)
		return all_categories
	except Exception:
		frappe.log_error(title = "Error in get_all_website_settings", message = frappe.get_traceback())

def generate_all_website_settings_json_doc(doc,method):
	try:
		res_data = get_all_website_settings_data()
		path = get_files_path()
		if not os.path.exists(os.path.join(path,'settings')):
			frappe.create_folder(os.path.join(path,'settings'))
		with open(os.path.join(path,'settings', 'all_website_settings.json'), "w") as f:
			content = json.dumps(json.loads(frappe.as_json(res_data)), separators=(',', ':'))
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

def get_all_website_settings_data():
	catalog_settings = frappe.get_single('Catalog Settings')
	media_settings = frappe.get_single('Media Settings')
	cart_settings = frappe.get_single('Shopping Cart Settings')
	order_settings = frappe.get_single('Order Settings')
	wallet_settings = frappe.get_single('Wallet Settings')
	res_data = {}
	if catalog_settings and media_settings and cart_settings and order_settings:
		locations = []
		location_areas = []
		default_location = None
		tracking_codes = frappe.get_single("Social Tracking Codes")
		enable_multi_store = 0
		enable_multi_vendor = 0
		
		if order_settings:
			if order_settings.enable_zipcode:
				Area = DocType("Area")
				query = (
					frappe.qb.from_(Area)
					.select(Area.name, Area.area, Area.zipcode, Area.city)
					.orderby(Area.area)
				)
				location_areas= query.run(as_dict=True)
					
		enable_left_panel = 1
		default_header = default_footer = website_logo = login_image = None
		from go1_commerce.go1_commerce.v2.category import get_parent_categories
		res_data={
			"default_header":default_header,
			"default_footer":default_footer,
			"no_of_records_per_page":10,
			"products_per_row":5,
			"show_short_description":'',
			"show_brand":1,
			"disable_category_filter":0,
			'additional_menus':'',
			"disable_price_filter":0,
			"disable_brand_filter":0,
			"disable_ratings_filter":0,
			"website_logo":website_logo,
			"login_image":login_image,
			"upload_review_images":'',
			"included_tax":catalog_settings.included_tax,
			"enable_related_products":1,
			"enable_best_sellers":1,
			"customers_who_bought":1,
			"default_product_sort_order":'',
			"enable_wallet":order_settings.enable_wallet,
			"enable_guest_checkout":order_settings.enable_checkout_as_guest,
			"allow_customer_to_addwallet":order_settings.allow_customer_to_add_wallet,
			"enable_map":order_settings.enable_map,
			"allow_cancel_order":order_settings.allow_cancel_order,
			"enable_auto_debit_wallet":wallet_settings.customer_auto_debit,
			"show_bestsellers_in_shopping_cart":cart_settings.show_bestsellers_in_shopping_cart,
			"enable_shipping_address":cart_settings.enable_ship_addr,
			"show_gift_card_box":order_settings.show_gift_card_box,
			"enable_reorder":order_settings.is_re_order_allowed,
			"enable_returns_system":order_settings.enable_returns_system,
			"default_products_per_row":5,
			"return_based_on":order_settings.return_based_on,
			"return_request_period":order_settings.return_request_period,
			"enable_question_and_answers":1,
			"enable_recently_viewed_products":1,
			"enable_best_sellers":1,
			"default_country":frappe.db.get_value("System Settings","System Settings","country"),
			"currency":catalog_settings.default_currency,
			"currency_symbol":frappe.db.get_value("Currency",catalog_settings.default_currency,"symbol"),
			"enable_customers_who_bought":1,
			"allow_guest_to_review":1,
			"account_settings":{
				"enable_gender":order_settings.enable_gender,
				"is_gender_required":order_settings.is_gender_required,
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
			},
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
			"location_areas":location_areas,
			"default_location":default_location,
			"social_tracking_codes":tracking_codes.as_dict() if tracking_codes else None,
			"default_meta_title":catalog_settings.meta_title,
			"default_meta_description":catalog_settings.meta_description,
			"default_meta_keywords":catalog_settings.meta_keywords,
			"all_categories":get_parent_categories()
		}
	return res_data


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
						MenusItem = DocType("Menus Item")
						query = (
							frappe.qb.from_(MenusItem)
							.select(MenusItem.menu_label, MenusItem.redirect_url, MenusItem.icon)
							.where((MenusItem.parent == menu[0].name) & ((MenusItem.parent_menu.isnull()) | (MenusItem.parent_menu == "")))
							.orderby(MenusItem.idx) 
						)
						parent_menus= query.run(as_dict=True)
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
	MenusItem = DocType("Menus Item")
	query = (
		frappe.qb.from_(MenusItem)
		.select(MenusItem.menu_label, MenusItem.redirect_url, MenusItem.icon)
		.where(
			(MenusItem.position == 'Right') & 
			(MenusItem.parent == header_id) & 
			(MenusItem.parentfield == 'top_menus') &
			((MenusItem.parent_menu.isnull()) | (MenusItem.parent_menu == ""))
		)
		.orderby(MenusItem.idx)
	)
	right_items= query.run(as_dict=True)
	for x in right_items:
		MenusItem = DocType("Menus Item")
		query = (
			frappe.qb.from_(MenusItem)
			.select(MenusItem.menu_label, MenusItem.redirect_url, MenusItem.icon)
			.where(
				(MenusItem.position == 'Right') & 
				(MenusItem.parent == header_id) & 
				(MenusItem.parentfield == 'top_menus') & 
				(MenusItem.parent_menu == x.menu_label)
			)
			.orderby(MenusItem.idx)
		)
		x.child_menu = query.run(as_dict=True)
		for sub_menu in x.child_menu:
			MenusItem = DocType("Menus Item")
			query = (
				frappe.qb
				.from_(MenusItem)
				.select(MenusItem.menu_label, MenusItem.redirect_url, MenusItem.icon)
				.where(
					(MenusItem.position == 'Right') & 
					(MenusItem.parent == header_id) & 
					(MenusItem.parentfield == 'top_menus') & 
					(MenusItem.parent_menu == sub_menu.menu_label)
				)
				.orderby(MenusItem.idx)
			)
			sub_menu.child_menu = query.run(as_dict=True)
	return right_items

def headers_list_left_items(header_id):
	MenusItem = DocType("Menus Item")
	query = (
		frappe.qb.from_(MenusItem)
		.select(MenusItem.menu_label, MenusItem.redirect_url, MenusItem.icon)
		.where(
			(MenusItem.position == 'Left') & 
			(MenusItem.parent == header_id) & 
			(MenusItem.parentfield == 'top_menus') & 
			((MenusItem.parent_menu.is_null()) | (MenusItem.parent_menu == ''))
		)
		.orderby(MenusItem.idx)
	)
	left_items= query.run(as_dict=True)
	for x in left_items:
		query = (
			frappe.qb.from_(MenusItem)
			.select(MenusItem.menu_label, MenusItem.redirect_url, MenusItem.icon)
			.where(
				(MenusItem.position == 'Left') & 
				(MenusItem.parent == header_id) & 
				(MenusItem.parentfield == 'top_menus') & 
				(MenusItem.parent_menu == x.menu_label)
			) 
			.orderby(MenusItem.idx)
		)
		x.child_menu= query.run(as_dict=True)
		for sub_menu in x.child_menu:
			query = (
				frappe.qb.from_(MenusItem)
				.select(MenusItem.menu_label, MenusItem.redirect_url, MenusItem.icon)
				.where(
					(MenusItem.position == 'Left') & 
					(MenusItem.parent == header_id) & 
					(MenusItem.parentfield == 'top_menus') & 
					(MenusItem.parent_menu == sub_menu.menu_label)
				)
				.orderby(MenusItem.idx)
			)
			sub_menu.child_menu = query.run(as_dict=True)
	return left_items


def headers_list_parent_menus(menu,headers_list):
	MenusItem = DocType("Menus Item")
	query = (
		frappe.qb.from_(MenusItem)
		.select(MenusItem.menu_label, MenusItem.redirect_url) 
		.where(
			(MenusItem.parent == menu[0].name) & 
			(MenusItem.parentfield == 'menus') & 
			((MenusItem.parent_menu.is_null()) | (MenusItem.parent_menu == ''))
		)
		.orderby(MenusItem.idx)
	)
	parent_menus= query.run(as_dict=True)
	for x in parent_menus:
		query = (
			frappe.qb.from_(MenusItem)
			.select(MenusItem.menu_label, MenusItem.redirect_url)
			.where(
				(MenusItem.parent == menu[0].name) & 
				(MenusItem.parentfield == 'menus') & 
				(MenusItem.parent_menu == x.menu_label)
			) 
			.orderby(MenusItem.idx)
		)
		x.child_menu= query.run(as_dict=True)
		for sub_menu in x.child_menu:
			query = (
				frappe.qb.from_(MenusItem)
				.select(MenusItem.menu_label, MenusItem.redirect_url)
				.where(
					(MenusItem.parent == menu[0].name) & 
					(MenusItem.parentfield == 'menus') & 
					(MenusItem.parent_menu == sub_menu.menu_label)
				)
				.orderby(MenusItem.idx) 
			)
			sub_menu.child_menu = query.run(as_dict=True)
	headers_list[0].menus = parent_menus

def get_doc_meta(doctype):
	try:
		frappe.local.response.data = frappe.get_meta(doctype)
		frappe.local.response.status = "success"
		frappe.local.response.http_status_code = 200
	except Exception:
		other_exception("Error in v2.common.get_doc_meta")

@frappe.whitelist(allow_guest=True)
def send_user_forget_pwd_mail(user):
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
def get_page_content_with_pagination(params):
	try:
		return get_content_with_pagination(params.get('route'), params.get('user'), params.get('customer'),
										params.get('application_type','mobile'),params.get('seller_classify','All Stores'),
										params.get('page_no',1),params.get('page_size',4))
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback(), title='Error in page_content')			


def get_content_with_pagination(route, user, customer,application_type,seller_classify,
										page_no,page_size):
	try:
		page_content = page_type = list_content = list_style = None
		side_menu = sub_header = None
		if not user and not customer:
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
	document = check_builder[0]['document']
	condition = check_builder[0].get('condition', '')
	sort_field = check_builder[0].get('sort_field', 'creation')
	sort_by = check_builder[0].get('sort_by', 'DESC')
	columns_mapping = json.loads(check_builder[0]['columns_mapping'])
	Doc = DocType(document)
	select_columns = []
	for column in columns_mapping:
		for key, value in column.items():
			select_columns.append(f"{value} as {key}")
	where_conditions = frappe.qb.where(f"{condition}") if condition else None
	order_by = f"{sort_field} {sort_by}"
	query = (
		frappe.qb.from_(Doc)
		.select(*select_columns) 
		.where(where_conditions) 
		.orderby(order_by)
	)
	list_content= query.run(as_dict=True)
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


def conditional_products_query(items_filter,conditions):
	query = f"""SELECT DISTINCT 
			P.item AS product, P.item AS ITEM,
			 P.price, 
			P.has_variants, P.short_description, P.tax_category, P.full_description,
			P.sku, P.name, P.route, P.inventory_method, P.minimum_order_qty,
			P.disable_add_to_cart_button, P.weight,P.old_price,
			P.gross_weight, P.approved_total_reviews, CM.category
		FROM `tabProduct` P
		INNER JOIN `tabProduct Category Mapping` CM ON CM.parent = P.name
		INNER JOIN `tabProduct Category` PC ON CM.category = PC.name
		WHERE P.is_active = 1 AND P.show_in_market_place = 1 
			AND P.status = 'Approved'
			AND P.name IN ({items_filter}) {conditions}
		"""
	
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
				P.item as product, P.item, P.full_description,P.route AS brand_route 
				P.name AS product_price,P.has_variants, P.short_description,P.tax_category,
				P.brand_name AS product_brand ,P.price, P.old_price,
				P.sku, P.name, P.route, P.inventory_method, P.minimum_order_qty,P.image AS product_image,
				P.disable_add_to_cart_button, P.weight,P.approved_total_reviews,CM.category,P.gross_weight
			FROM `tabProduct` P 
			
			INNER JOIN `tabProduct Category Mapping` CM 
				ON CM.parent = P.name 
			INNER JOIN `tabProduct Category` PC 
				ON CM.category = PC.name 
			WHERE P.is_active = 1 AND P.show_in_market_place = 1 AND
				 P.status = 'Approved' 
			AND (CASE WHEN (P.has_variants = 1 AND 
				EXISTS (SELECT VC.name 
						FROM `tabProduct Variant Combination` VC 
						WHERE VC.show_in_market_place = 1 '{seller_classify_cond}' AND 
							VC.disabled = 0 THEN 1 = 1 
					WHEN (P.has_variants = 0 THEN 1 = 1 ELSE 1 = 0 END) 
			AND P.name IN (%s) %s  """ % (items_filter, conditions)
	return query

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
	MenuItem = DocType('Menus Item')
	query = (
		frappe.qb.from_(MenuItem)
		.select(
			MenuItem.menu_label,
			MenuItem.redirect_url,
			MenuItem.icon
		)
		.where(
			(MenuItem.position == 'Right') &
			(MenuItem.parent == header_id) &
			(MenuItem.parentfield == 'top_menus') &
			((MenuItem.parent_menu.isnull()) | (MenuItem.parent_menu == ''))
		)
		.orderby(MenuItem.idx)
	)
	right_items = query.run(as_dict=True)
	for x in right_items:
		MenuItem = DocType('Menus Item')
		query = (
			frappe.qb.from_(MenuItem)
			.select(
				MenuItem.menu_label,
				MenuItem.redirect_url,
				MenuItem.icon
			)
			.where(
				(MenuItem.position == 'Right') &
				(MenuItem.parent == header_id) &
				(MenuItem.parentfield == 'top_menus') &
				(MenuItem.parent_menu == x.menu_label)
			)
			.orderby(MenuItem.idx)
		)
		x.child_menu = query.run(as_dict=True)
		for sub_menu in x.child_menu:
			MenuItem = DocType('Menus Item')
			query = (
				frappe.qb.from_(MenuItem)
				.select(
					MenuItem.menu_label,
					MenuItem.redirect_url,
					MenuItem.icon
				)
				.where(
					(MenuItem.position == 'Right') &
					(MenuItem.parent == header_id) &
					(MenuItem.parentfield == 'top_menus') &
					(MenuItem.parent_menu == sub_menu.menu_label)
				)
				.orderby(MenuItem.idx)
			)
			sub_menu.child_menu = query.run(as_dict=True)
	return right_items

def get_page_header_info_left_items(header_id):
	MenuItem = DocType('Menus Item')
	query = (
		frappe.qb.from_(MenuItem)
		.select(
			MenuItem.menu_label,
			MenuItem.redirect_url,
			MenuItem.icon
		)
		.where(
			(MenuItem.position == 'Left') &
			(MenuItem.parent == header_id) &
			(MenuItem.parentfield == 'top_menus') &
			((MenuItem.parent_menu.is_null()) | (MenuItem.parent_menu == ''))
		)
		.orderby(MenuItem.idx)
	)
	left_items = query.run(as_dict=True)
	for x in left_items:
		query = (
			frappe.qb.from_(MenuItem)
			.select(
				MenuItem.menu_label,
				MenuItem.redirect_url,
				MenuItem.icon
			)
			.where(
				(MenuItem.position == 'Left') &
				(MenuItem.parent == header_id) &
				(MenuItem.parentfield == 'top_menus') &
				(MenuItem.parent_menu == x.menu_label)
			)
			.orderby(MenuItem.idx)
		)
		x.child_menu = query.run(as_dict=True)
		
		for sub_menu in x.child_menu:
			query = (
				frappe.qb.from_(MenuItem)
				.select(
					MenuItem.menu_label,
					MenuItem.redirect_url,
					MenuItem.icon
				)
				.where(
					(MenuItem.position == 'Left') &
					(MenuItem.parent == header_id) &
					(MenuItem.parentfield == 'top_menus') &
					(MenuItem.parent_menu == sub_menu.menu_label)
				)
				.orderby(MenuItem.idx)
			)
			sub_menu.child_menu = query.run(as_dict=True)
	return left_items


def page_header_child_menu(x,menu):
	MenuItem = DocType('Menus Item')
	query = (
		frappe.qb.from_(MenuItem)
		.select(
			MenuItem.menu_label,
			MenuItem.redirect_url,
			MenuItem.icon,
			MenuItem.mega_m_col_index
		)
		.where(
			(MenuItem.parent == menu[0].name) &
			(MenuItem.parentfield == 'menus') &
			(MenuItem.parent_menu == sub_menu.menu_label)
		)
		.orderby(MenuItem.idx)
	)
	x.child_menu = query.run(as_dict=True)
	for sub_menu in x.child_menu:
		query = (
			frappe.qb
			.from_(MenuItem)
			.select(
				MenuItem.menu_label,
				MenuItem.redirect_url,
				MenuItem.icon
			)
			.where(
				(MenuItem.parent == menu[0].name) &
				(MenuItem.parentfield == 'menus') &
				(MenuItem.parent_menu == sub_menu.menu_label)
			)
			.orderby(MenuItem.idx)
		)
		sub_menu.child_menu = query.run(as_dict=True)
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
				MenuItem = DocType('Menus Item')
				query = (
					frappe.qb.from_(MenuItem)
					.select(
						MenuItem.menu_label,
						MenuItem.redirect_url,
						MenuItem.is_mega_menu,
						MenuItem.no_of_column
					)
					.where(
						(MenuItem.parent == menu_id) &
						((MenuItem.parent_menu.isnull()) | (MenuItem.parent_menu == ''))
					)
					.orderby(MenuItem.idx)
				)
				parent_menus= query.run(as_dict=True)
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
						MenuItem = DocType('Menus Item')
						query = (
							frappe.qb.from_(MenuItem)
							.select(MenuItem.menu_label, MenuItem.redirect_url)
							.where(
								(MenuItem.parent == menu[0].name) &
								((MenuItem.parent_menu.isnull()) | (MenuItem.parent_menu == ''))
							)
							.orderby(MenuItem.idx)
						)
						parent_menus = query.run(as_dict=True)
						item["menus"] = parent_menus
				lists.append(item)
		g_list = []
		MobilePageSection = DocType('Mobile Page Section')
		query = (
			frappe.qb.from_(MobilePageSection)
			.select(MobilePageSection.column_index)
			.where(MobilePageSection.parent == footer_id)
			.groupby(MobilePageSection.column_index)
		)
		column_indexes = query.run(as_dict=True)
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
	if mobile_no and not frappe.db.exists("Customers",{"phone":mobile_no}):
		return {"status":"Failed","message":"Customer not exist."}
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
		ProductAttributeOption = DocType('Product Attribute Option')
		query = (
			frappe.qb.from_(ProductAttributeOption)
			.select(
				ProductAttributeOption.name,
				ProductAttributeOption.attribute,
				ProductAttributeOption.option_value
			)
			.where(ProductAttributeOption.name != "")
		)
		p_options = query.run(as_dict=True)
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
	BlogPost = DocType('Blog Post')
	query = (
		frappe.qb
		.from_(BlogPost)
		.select(
			BlogPost.name,
			BlogPost.title,
			BlogPost.thumbnail_image,
			BlogPost.blog_intro,
			BlogPost.published_on,
			BlogPost.route
		)
		.where(BlogPost.published == 1)
		.orderby(BlogPost.published_on, order=Order.desc)
		.limit(page_size)
		.offset((int(page_no) - 1) * int(page_size))
	)
	if category:
		query = query.where(BlogPost.blog_category == category)
	return query.run(as_dict=True)

@frappe.whitelist(allow_guest=True)
def get_blog_categories():
	BlogCategory = DocType('Blog Category')
	query = (
		frappe.qb.from_(BlogCategory)
		.select(
			BlogCategory.name,
			BlogCategory.title,
			BlogCategory.route
		)
		.where(BlogCategory.published == 1)
		.orderby(BlogCategory.creation, order=Order.desc)
	)
	return query.run(as_dict=True)

@frappe.whitelist(allow_guest=True)
def get_blog_details(route):
	try:
		BlogPost = DocType('Blog Post')
		Blogger = DocType('Blogger')
		blog_details_query = (
			frape.qb.from_(BlogPost)
			.left_join(Blogger)
			.on(Blogger.name == BlogPost.blogger)
			.select(
				BlogPost.star, 
				Blogger.full_name.as_('blogger_full_name'),
				Blogger.bio,
				Blogger.avatar
			)
			.where(BlogPost.published == 1)
			.where(BlogPost.route == route)
		)
		blog_details = blog_details_query.run(as_dict=True)
		if blog_details:
			blog_category = blog_details[0].get('blog_category', None)
			related_bloglist=[]
			if blog_category:
				related_bloglist_query = (
					frappe.qb.from_(BlogPost)
					.select(
						BlogPost.name,
						BlogPost.title,
						BlogPost.thumbnail_image,
						BlogPost.blog_intro,
						BlogPost.published_on,
						BlogPost.route
					)
					.where(BlogPost.published == 1)
					.where(BlogPost.route != route)
					.where(BlogPost.blog_category == blog_category)
					.orderby(BlogPost.published_on, order=Order.desc)
					.limit(6)
				)
				related_bloglist = related_bloglist_query.run(as_dict=True)
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

def logout_customer(login_manager):
	try:
		sid = frappe.local.session.sid
		frappe.cache().hdel(sid, 'locations_list')
		frappe.cache().hdel(sid, 'destinations_list')
		frappe.cache().hdel(sid, 'user_location')
		frappe.local.cookie_manager.delete_cookie('customer_id')
		frappe.local.cookie_manager.delete_cookie('guest_customer')
		frappe.local.cookie_manager.delete_cookie('addressId')
		frappe.local.cookie_manager.delete_cookie('guest_customer_phone')
		frappe.local.cookie_manager.delete_cookie('guest_customer_name')
	except Exception:
		frappe.log_error('Error in v2.common.logout_customer', frappe.get_traceback())	


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
								  fields=['name'])
			if guest_cart:
				update_cart('Shopping Cart', customer, guest, guest_cart)
			guest_cart2 = frappe.db.get_all('Shopping Cart', 
								   filters={'customer': guest, 'cart_type': 'Wishlist'}, 
								   fields=['name'])
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
				CartItems = DocType('Cart Items')
				upd = (frappe.qb.update(CartItems)
					.set(CartItems.parent, cart[0].name)
					.where(CartItems.parent == guest_cart)
				).run()

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
				CartItems = DocType('Cart Items')
				upt=(frappe.qb.update(CartItems)
					.set(CartItems.parent, cart[0].name)
					.where(CartItems.name == item.name)
				).run()
				


def validate_item_info(item, g_item, item_info):
	qty = float(item.quantity) + float(g_item[0].quantity)
	if item_info.inventory_method == 'Dont Track Inventory':
		upt =(frappe.qb.update(CartItems)
			.set(CartItems.quantity, qty)
			.where(CartItems.name == g_item[0].name)
		).run()
		total = float(item.price) * float(qty)
		upt=(frappe.qb.update(CartItems)
			.set(CartItems.total, total)
			.where(CartItems.name == g_item[0].name)
		).run()
		

	elif item_info.inventory_method == 'Track Inventory':
		if item_info.stock >= g_item[0].quantity:
			upt=(frappe.qb.update(CartItems)
				.set(CartItems.quantity, qty)
				.where(CartItems.name == g_item[0].name)
			).run()
			total = float(item.price) * float(qty)
			upt=(frappe.qb.update(CartItems)
				.set(CartItems.total, total)
				.where(CartItems.name == g_item[0].name)
			).run()
			

@frappe.whitelist()
def update_recently_viewed_products(guest_id, customer_id):
	recently_viewed_products = frappe.get_all('Customer Viewed Product', 
											fields=['product', 'viewed_date', 'name'],
											filters={'parent': guest_id}, order_by='viewed_date desc')
	for x in recently_viewed_products:
		frappe.enqueue("go1_commerce.go1_commerce.api.\
				delete_viewed_products",customer_id = customer_id, name = x.name, product = x.product)


def get_custom_translations(messages, language):
	Translation = DocType('Translation')
	translations = (frappe.qb.select(Translation.source_text, Translation.translated_text)
					.from_(Translation)
					.where(Translation.language == language)
				   ).run(as_dict=True)
	for item in translations:
		messages[item.source_name] = item.target_name
	return messages

def boot_session(bootinfo):
	try:
		defaults = get_settings('Catalog Settings')
		if defaults.get('default_currency'):
			bootinfo.sysdefaults.currency = defaults.default_currency
		Currency = DocType('Currency')
		currencies = (frappe.qb.select(Currency.name, Currency.fraction, Currency.fraction_units,
								Currency.number_format, Currency.smallest_currency_fraction_value, Currency.symbol)
					  .from_(Currency)
					  .where(Currency.enabled == 1)
					 ).run(as_dict=True)
		bootinfo.docs += currencies
		bootinfo.docs[-1].update({'doctype': ':Currency'})
		filters = {}
		
		if "System Manager" not in frappe.get_roles(frappe.session.user):
			settings = frappe.db.get_all('Business', fields=['name'], filters=filters)
			if settings:
				bootinfo.sysdefaults.business = settings[0].name
		# domain_configuration = frappe.get_single('Server Configuration')
		# bootinfo.sysdefaults.domain_configuration = domain_configuration
		domains = []
		# domains = get_domains_data()
		# bootinfo.sysdefaults.domain_constants = domains
		bootinfo['__messages'] = get_custom_translations(bootinfo['__messages'], bootinfo.lang)
		
		apps = frappe.get_installed_apps()
		for app in apps:
			ModuleDef = DocType('Module Def')
			module_name = (frappe.qb.from_(ModuleDef)
							 .select('*')
							 .where(ModuleDef.app_name == app)
						  ).run(as_dict=True)
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


@frappe.whitelist()
def insert_doc(data):
	try:
		from six import string_types
		if isinstance(data, string_types):
			data = json.loads(data)
		keys = data.keys()
		insert_doc = frappe.new_doc(data.get('doctype'))
		for key in keys:
			if type(data.get(key)) != list:
				setattr(insert_doc, key, data.get(key))
		insert_doc.save(ignore_permissions=True)
		return insert_doc.as_dict()
	except Exception as e:
		frappe.log_error("Error in v2.common.insert_doc",frappe.get_traceback())

@frappe.whitelist()
def update_doc(data):
	try:
		from six import string_types
		if isinstance(data, string_types):
			data = json.loads(data)
		keys = data.keys()
		if frappe.db.exists(data.get('doctype'), data.get('name')):
			update_doc = frappe.get_doc(data.get('doctype'), data.get('name'))
			for key in keys:
				if type(data.get(key)) != list:
					setattr(update_doc, key, data.get(key))
			update_doc.save(ignore_permissions=True)
			return update_doc.as_dict()
	except Exception as e:
		frappe.log_error("Error in v2.common.update_doc",frappe.get_traceback())
