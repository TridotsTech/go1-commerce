# Copyright (c) 2015, Tridots Tech Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
import os
import json

from go1_commerce.go1_commerce.after_install import read_module_path
from go1_commerce.utils.setup import get_settings_from_domain
from go1_commerce.go1_commerce.doctype.data_creation_report.data_creation_report import create_data_report, update_data_report

def get_setup_stages(args=None):
	stages = [
		{
			'status': _('Setting up domain'),
			'fail_msg': _('Failed to setup domain'),
			'tasks': [
				{
					'fn': setup_domain,
					'args': args,
					'fail_msg': _("Failed to setup domain")
				}
			]
		},
		{
			'status': _('Setting up business'),
			'fail_msg': _('Failed to setup business'),
			'tasks': [
				{
					'fn': setup_business,
					'args': args,
					'fail_msg': _("Failed to setup business")
				}
			]
		}
	]
	return stages

def setup_domain(args):
	domain_settings = frappe.get_single('Domain Settings')
	domain_settings.set_active_domains(args.get('domains'))

def setup_complete(args):
	if args.get('currency'):
		catalog_settings = get_settings_from_domain('Catalog Settings')
		if catalog_settings:
			try:
				catalog_settings.default_currency = args.get('currency')
				catalog_settings.save(ignore_permissions=True)
			except Exception:
				pass
	files_list = []
	dashboard = False
	menu = False
	if "dashboard" in frappe.get_installed_apps():
		dashboard = True
	if "school_theme" in frappe.get_installed_apps():
		menu = True
	if "Single Vendor" in args.get('domains'):
		files_list.append('single_vendor_mail_alert.json')
		if dashboard:
			files_list.append('single_vendor_dashboard_groups.json')
		if menu:
			files_list.append('singlevendor_menu_module.json')
	elif "Multi Vendor" in args.get('domains'):
		files_list.append('multi_vendor_mail_alert.json')
		if dashboard:
			files_list.append('multivendor_dashboard_groups.json')
		if menu:
			files_list.append('multivendor_menu_module.json')
	if files_list:
		for item in files_list:
			read_module_path(item)
	if not "SaaS" in args.get('domains'):
		if args.get('sample_data'):
			data_type = 'ecommerce'
			if "Restaurant" in args.get('domains'):
				data_type = 'restaurant'		
			frappe.enqueue('go1_commerce.utils.setup_wizard.create_sample_data', data_type=data_type)
	frappe.enqueue('go1_commerce.utils.setup_wizard.update_meta_information', args=args)

def setup_business(args):
	try:
		if "Single Vendor" in args.get('domains') or args.get('sample_data'):
			doc = frappe.new_doc('Business')
			doc.restaurant_name = args.get('business')
			doc.contact_person = args.get('business')
			doc.contact_number = args.get('contact_number')
			doc.business_phone = args.get('contact_number')
			doc.contact_email = args.get('contact_email')
			doc.business_address = args.get('address')
			doc.city = args.get('city')
			doc.country = args.get('country')
			doc.save(ignore_permissions=True)
		else:
			catalog_settings = get_settings_from_domain('Catalog Settings')
			if catalog_settings:
				catalog_settings.site_name = args.get('business')
				catalog_settings.meta_title = args.get('business')
				catalog_settings.meta_description = args.get('business')
				catalog_settings.save(ignore_permissions=True)
			themes = frappe.db.get_all('Web Theme', filters={'is_active': 1})
			if themes:
				web_theme = frappe.get_doc('Web Theme', themes[0].name)
				web_theme.footer_email = args.get('contact_email')
				web_theme.footer_phone = args.get('contact_number')
				web_theme.footer_address = '{0}\n{1}\n{2}'.format(args.get('address'),args.get('city'),args.get('country'))
				web_theme.save(ignore_permissions=True)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), str(e))

@frappe.whitelist()
def create_sample_data(data_type='ecommerce', business=None, file_name=None):
	import time
	time.sleep(30)
	create_records(data_type, business, file_name)

@frappe.whitelist()
def create_records(data_type='ecommerce', business=None, f_name=None):
	try:
		file_name = None
		if data_type == 'ecommerce':
			file_name = 'sample_data_ecommerce.json'
		if f_name:
			file_name = f_name
		data_result = create_data_report(business, 'Sample Data') if business else None
		if file_name:
			path = frappe.get_app_path("go1_commerce")
			file_path = os.path.join(path, 'sample_records', file_name)
			if os.path.exists(file_path):
				with open(file_path, 'r') as f:
					out = json.load(f)
				dt_list = list(set([x.get('doctype') for x in out if x.get('doctype') not in ['Product', 'Slider']]))
				result_json = []
				for dt in dt_list:
					items_list = list(filter(lambda x: x.get('doctype') == dt, out))
					is_saas = None
					opt = {}
					opt['document_type'] = dt
					opt['no_of_records'] = len(items_list)
					success_cnt = 0
					for i in items_list:
						try:
							if i.get('doctype') == 'Product Category' and i.get('parent_product_category'):
								parent = frappe.get_doc('Product Category', {'category_name': i.get('parent_product_category')})
								i['parent_product_category'] = parent.name
							frappe.get_doc(i).insert()
							success_cnt = success_cnt + 1
						except Exception as e:
							frappe.log_error(frappe.get_traceback(), 'go1_commerce.utils.setup_wizard.create_records (category creation)')
					opt['created_records'] = success_cnt
					result_json.append(opt)
				frappe.db.commit()
				frappe.enqueue('go1_commerce.utils.setup_wizard.insert_sample_product_1', data_type=data_type, business=business, f_name=f_name, data_result=data_result.get('name'), result_json=result_json)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.utils.setup_wizard.create_records')

@frappe.whitelist()
def update_meta_information(args):
	if args.get('business'):
		pages = frappe.db.sql_list('''select name from `tabPages`''')
		for item in pages:
			doc = frappe.get_doc('Pages', item)
			doc.meta_title = '{0} - {1}'.format(doc.meta_title, args.get('business'))
			doc.meta_description = '{0} - {1}'.format(doc.meta_description, args.get('business'))
			doc.save(ignore_permissions=True)	
	website_settings = frappe.get_single('Website Settings')
	if "cmswebsite" in frappe.get_installed_apps():
		website_settings.home_page = 'index'
	website_settings.disable_signup = 1
	website_settings.save(ignore_permissions=True)

@frappe.whitelist()
def insert_sample_product(data_type='ecommerce', business=None):
	file_name = None
	if data_type == 'ecommerce':
		file_name = 'sample_data_ecommerce.json'
	from frappe.utils import random_string
	if file_name:
		path = frappe.get_module_path("go1_commerce")
		file_path = os.path.join(path, file_name)
		if os.path.exists(file_path):
			with open(file_path, 'r') as f:
				out = json.load(f)
			abbr = None
			products = list(filter(lambda x: x.get('doctype') == 'Product', out))
			is_saas = None
			today_date = frappe.utils.get_datetime()
			final_count = 0
			series = None
			for idx, i in enumerate(products):
				try:
					final_count = final_count + 1
					if abbr:
						name = 'ITEM-{0}-{1}'.format(abbr, namingindex(idx + 1))
						series = 'ITEM-{0}-'.format(abbr)
					else:
						name = i.get('name')
						series = 'ITEM-'
					frappe.db.sql('''INSERT into tabProduct (name, item, price, old_price, status, is_active, display_home_page, meta_title, meta_description, restaurant, owner, modified_by, creation, modified, disable_add_to_cart_button, inventory_method, naming_series) 
						values(%(name)s, %(item)s, %(price)s, %(old_price)s, "Approved", 1, %(home_page)s, %(item)s, %(item)s, %(business)s, "Administrator", "Administrator", %(dates)s, %(dates)s, 0, "Dont Track Inventory", %(series)s)''',{
						'item': i.get('item'),
						'price': i.get('price'),
						'old_price': i.get('old_price'),
						'name': name,
						'business': business,
						'home_page': (i.get('display_home_page') or 0),
						'dates': today_date,
						'series': series
						}, auto_commit=1)
					if i.get('product_categories'):
						for item in i.get('product_categories'):
							filters = {'category_name': item.get('category_name') if item.get('category_name') else item.get('category')}
							cat = frappe.db.get_all('Product Category', filters=filters, fields=['name', 'category_name'])
							if cat:
								frappe.db.sql('''INSERT into `tabProduct Category Mapping` (name, category, category_name, parent, parenttype, parentfield, owner, modified_by, creation, modified) 
									values(%(name)s, %(category)s, %(category_name)s, %(parent)s, "Product", "product_categories", "Administrator", "Administrator", %(dates)s, %(dates)s)''',{
									'name': random_string(10),
									'category': cat[0].name,
									'category_name': cat[0].category_name,
									'parent': name,
									'dates': today_date
									}, auto_commit=1)
					dc = frappe.get_doc('Product', name)
					dc.save(ignore_permissions=True)
				except Exception as e:
					frappe.log_error(frappe.get_traceback(), 'go1_commerce.utils.setup_wizard.insert_sample_product')
			check_series = frappe.db.sql('''select name, current from `tabSeries` where name = %(name)s''', {'name': series}, as_dict=1)
			if check_series and check_series[0]:
				frappe.db.set_value('''update `tabSeries` set current = {0} where name = "{1}"'''.format(int(final_count) + int(check_series[0].current), series))
			else:
				frappe.db.sql('''insert into `tabSeries` (name, current) values (%(name)s, %(value)s)''', {'name': series, 'value': final_count})

@frappe.whitelist()
def insert_sample_product_1(data_type='ecommerce', business=None, f_name=None, data_result=None, result_json=[]):
	file_name = None
	if data_type == 'ecommerce':
		file_name = 'sample_data_ecommerce.json'
	if f_name:
		file_name = f_name
	from frappe.utils import random_string
	opt = {}
	opt['document_type'] = 'Product'
	if file_name:
		path = frappe.get_app_path("go1_commerce")
		file_path = os.path.join(path, 'sample_records', file_name)
		if os.path.exists(file_path):
			with open(file_path, 'r') as f:
				out = json.load(f)
			products = list(filter(lambda x: x.get('doctype') == 'Product', out))
			opt['no_of_records'] = len(products)
			is_saas = None
			success_cnt = 0
			for i in products:
				try:
					if i.get('product_categories'):
						for item in i.get('product_categories'):
							filters = {'category_name': item.get('category_name') if item.get('category_name') else item.get('category'), 'business': ''}
							if is_saas and business:
								filters['business'] = business
							cat = frappe.db.get_all('Product Category', filters=filters, fields=['name', 'category_name'])
							if cat:
								item['category'] = cat[0].name
								item['category_name'] = cat[0].category_name
					attributes = None
					if i.get('product_attributes'):
						attributes = i.get('product_attributes')
						i['product_attributes'] = []
					dc = frappe.get_doc(i).insert(ignore_permissions=True)
					if attributes and len(attributes) > 0:
						for atr_idx, attr in enumerate(attributes):
							filters = {'business': '', 'attribute_name': attr.get('attribute')}
							attr_info = frappe.db.get_all('Product Attribute', filters=filters)
							if attr_info:
								options = attr.get('options')
								attr.update({'parent': dc.name, 'idx': (atr_idx + 1), 'name': None, 'product_attribute': attr_info[0].name})
								del attr['options']
								attr_obj = frappe.get_doc(attr).insert(ignore_permissions=True)
								for op_idx, op in enumerate(options):
									op.update({'attribute_id': attr_obj.name, 'attribute': attr_info[0].name, 'parent': dc.name, 'idx': (op_idx + 1)})
									frappe.get_doc(op).insert(ignore_permissions=True)
					success_cnt = success_cnt + 1
				except Exception as e:
					frappe.log_error(frappe.get_traceback(), 'go1_commerce.utils.setup_wizard.insert_sample_product')
			opt['created_records'] = success_cnt
			result_json.append(opt)
			if data_result:
				update_data_report(data_result, json.dumps(result_json))
	
def namingindex(val):
	length = 5
	if len(str(val)) == length:
		pass
	else:
		zeros = length - len(str(val))
		str_val = ''
		while len(str_val) < zeros:
			str_val = '{0}0'.format(str_val)
		val = '{0}{1}'.format(str_val, val)
	return val
