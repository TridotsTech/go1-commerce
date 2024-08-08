#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe, json, os, re
from frappe.utils import get_files_path
from datetime import datetime
from go1_commerce.utils.google_maps import get_geolocation

@frappe.whitelist()
def get_settings_from_domain(dt):
	return get_settings(dt)

@frappe.whitelist()
def get_settings(dt):
	dt_map = {
		'Catalog Settings': 'Catalog Settings',
		'Media Settings': 'media',
		'Shopping Cart Settings': 'cart',
		'Order Settings': 'order'
	}
	if dt_map.get(dt):
		path = get_files_path()
		file_path = os.path.join(path, 'settings', dt_map.get(dt), '.json')
		if os.path.exists(file_path):
			with open(file_path) as f:
				data = json.loads(f.read())
				keys = data.keys()
				for k in keys:
					if type(data.get(k)) == list:
						child = []
						for item in data.get(k):
							child.append(frappe._dict(item))
						data[k] = child
				return frappe._dict(data)
	return frappe.get_single(dt)

@frappe.whitelist()
def get_settings_value(dt, field):
	settings = frappe.db.get_single_value(dt, field)
	# settings = frappe.db.sql('''SELECT name, {1} 
	# 							FROM `tab{0}` 
	# 							WHERE name!= ""'''.format(dt, field), as_dict=1)
	if settings:
		return settings
	

def is_website_published(doc):
	"""Return true if published in website"""
	if get_condition_field(doc):
		return doc.get(get_condition_field(doc)) and True or False
	else:
		return True


def get_condition_field(doc):
	condition_field = get_website_properties(doc, 'condition_field')
	if not condition_field:
		if doc.meta.is_published_field:
			condition_field = doc.meta.is_published_field
	return condition_field


@frappe.whitelist(allow_guest=True)
def get_subdomain(url):
	try:
		import frappe
		import tldextract
		cur_domain = frappe.local.request.host_url.split('/')[-2:][0]
		info = tldextract.extract(cur_domain)
		subdomain=info.subdomain.split(".")[-1:][0]
		cur_domain = info.domain
		if subdomain and subdomain != "www":
			cur_domain = subdomain + "."+info.domain + "." + info.suffix
		else:
			cur_domain = info.domain + "." + info.suffix
		return cur_domain
	except Exception as e:
		return url

def save_file(doc, folder=None):
	from six import text_type
	"""write file to disk with a random name (to compare)"""
	file_path = get_files_path(is_private=doc.is_private)
	frappe.create_folder(file_path)
	if folder:
		if not os.path.exists(os.path.join(file_path, folder)):
			frappe.create_folder(os.path.join(file_path, folder))
	doc.content = doc.get_content()
	if isinstance(doc.content, text_type):
		doc.content = doc.content.encode()
	if folder:
		with open(os.path.join(file_path.encode('utf-8'), folder.encode('utf-8'), doc.file_name.encode('utf-8')),'wb+') as f:
			f.write(doc.content)
	else:
		with open(os.path.join(file_path.encode('utf-8'), doc.file_name.encode('utf-8')), 'wb+') as f:
			f.write(doc.content)
	if folder:
		return get_files_path('{0}/{1}'.format(folder, doc.file_name), is_private=doc.is_private)
	return get_files_path(doc.file_name, is_private=doc.is_private)


@frappe.whitelist(allow_guest=True)
def get_favicon_for_domain(dt):
	favicon=""
	settings = frappe.db.sql('''select name from `tab{0}` '''.format(dt), as_dict=1)
	if settings:
		seting = frappe.get_doc(dt, settings[0].name)
		if seting.theme:
			favicon =  frappe.db.get_value("Web Theme", seting.theme, 'favicon')
		else:
			if frappe.db.get_value("Web Theme", {"is_active":1}, 'favicon'):
				favicon =  frappe.db.get_value("Web Theme", {"is_active":1}, 'favicon')
	settings = frappe.db.sql('''select name from `tab{0}` where name!= ""'''.format(dt), as_dict=1)
	if settings:
		seting =  frappe.get_doc(dt, settings[0].name)
		if seting.theme:
			if seting.theme:
				favicon = frappe.db.get_value("Web Theme", seting.theme, 'favicon')
			else:
				if frappe.db.get_value("Web Theme", {"is_active":1}, 'favicon'):
					favicon = frappe.db.get_value("Web Theme", {"is_active":1}, 'favicon')
	return favicon


def autoname_newsletter(doc, method = None):
	series = 'N-'
	from frappe.model.naming import make_autoname
	doc.name = make_autoname(series + '.#####', doc=doc)


def get_query_condition_email_group_member(user):
	if not user: user = frappe.session.user
	if "System Manager" in frappe.get_roles(user):
		return None


def get_query_condition_newsletter(user):
	if not user: user = frappe.session.user
	if "System Manager" in frappe.get_roles(user):
		return None


def update_api_log(cmd):
	order_settings = frappe.get_single('Order Settings')
	if order_settings.enable_api_logs:
		if not order_settings.api_log_method or len(order_settings.api_log_method) == 0:
			return
		check_method = next((x for x in order_settings.api_log_method if x.method == cmd), None)
		if check_method:
			cur_user = frappe.session.user
			get_user = frappe.db.get_all('API Log',filters={'user':cur_user},fields=['name'])
			if get_user:
				doc=frappe.get_doc({
					"doctype": "Api Log Group",
					"method":cmd,
					"date":datetime.now(),
					"headers":json.dumps({'host': frappe.request.headers.get('host'), 'user_agent': frappe.request.headers.get('user_agent'), 'origin': frappe.request.headers.get('origin')}),
					"parameters":frappe.as_json(frappe.form_dict),
					"parent":get_user[0].name,
					"parenttype":'API Log',
					"parentfield":'log_group'
				})
				doc.insert(ignore_permissions=True)
			else:
				headers = json.dumps({'host': frappe.request.headers.get('host'), 'user_agent': frappe.request.headers.get('user_agent'), 'origin': frappe.request.headers.get('origin')})
				parameters = frappe.as_json(frappe.form_dict)
				doc = frappe.new_doc('API Log')
				doc.user = frappe.session.user if (frappe.session.user != 'Guest') else None
				doc.append("log_group",({"method":cmd, "date": datetime.now(),"headers":headers,"parameters":parameters}))
				doc.save(ignore_permissions=True)


@frappe.whitelist()
def clear_api_log():
	frappe.enqueue('go1_commerce.utils.setup.delete_api_logs')

@frappe.whitelist()
def clear_executed_command_log():
	frappe.enqueue('go1_commerce.utils.setup.delete_executed_command_logs')

@frappe.whitelist()
def delete_api_logs():
	try:
		enable_api_log = frappe.db.get_single_value('Order Settings', 'enable_api_logs')
		if enable_api_log:
			logs = frappe.db.sql('''select group_concat(concat('"', name, '"')) from `tabAPI Log` where creation < date_sub(curdate(), interval 7 day) order by creation limit 100''')
			if logs and logs[0] and logs[0][0]:
				frappe.db.sql('''delete from `tabApi Log Group` where parent in ({name})'''.format(name=logs[0][0]))
				frappe.db.sql('''delete from `tabAPI Log` where name in ({name})'''.format(name=logs[0][0]))
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.utils.setup.delete_api_logs')

@frappe.whitelist()
def delete_executed_command_logs():
	try:
		logs = frappe.db.sql('''select group_concat(concat('"', name, '"')) from `tabExecuted Command` where creation < date_sub(curdate(), interval 30 day) order by creation limit 100''')
		if logs and logs[0] and logs[0][0]:
			frappe.db.sql('''delete from `tabExecuted Command` where name in ({name})'''.format(name=logs[0][0]))
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.utils.setup.delete_executed_command_logs')


@frappe.whitelist()
def get_theme_settings():
	theme = frappe.db.get_all('Web Theme', filters={'is_active': 1})
	if theme:
		active_theme = theme[0].name
	return active_theme

@frappe.whitelist()
def read_file_from_url(url):
	import urllib

	f = urllib.urlopen(url)
	file = f.read().decode('utf-8')
	data = json.loads(file)
	return data


@frappe.whitelist()
def get_doc_versions(doctype, name, check_field_change=False, check_field=None):
	versions = frappe.get_version(doctype, name)
	if check_field_change and check_field:
		field_versions = []
		for v in versions:
			if v.get('version') and v.get('version').get('changed'):
				for ch in v.get('version').get('changed'):
					if ch[0] == check_field:
						field_versions.append({'old_value': ch[1], 'new_value': ch[2]})
		return field_versions

	return versions

@frappe.whitelist()
def validate_zip_code(zipcode, domain=None):
	settings = get_settings_from_domain('Order Settings')
	if settings:
		if int(settings.min_pincode_length) > 0 and len(zipcode) < int(settings.min_pincode_length):
			frappe.throw(frappe._('Postal/Zip code must contain {0} characters').format(settings.min_pincode_length))
		if int(settings.max_pincode_length) > 0 and len(zipcode) > int(settings.max_pincode_length):
			frappe.throw(frappe._('Postal/Zip code should not exceed {0} characters').format(settings.max_pincode_length))
		if settings.pincode == 'Only Number':
			res = re.match('^[0-9]*$', zipcode)
			if not res:
				frappe.throw(frappe._('Postal/Zip code must contain only number'))
		if settings.pincode == 'Number, Letters':
			res = re.search('(?=.*[a-z])(?=.*\d)[a-z\d]', zipcode)
			if not res:
				frappe.throw(frappe._('Postal/Zip code must contain numbers & letters'))
			if re.search('(?=.*[!%&@#$^*?_~])[!%&@#$^*?_~]', zipcode):
				frappe.throw(frappe._('Postal/Zip code must contain numbers & letters'))

def validate_google_settings(doc, method):
	if doc.enable and doc.api_key and doc.default_address:
		if doc.default_address != frappe.db.get_single_value('Google Settings', 'default_address'):
			doc.latitude = None
			doc.longitude = None
		if not doc.latitude or not doc.longitude:
			res = get_geolocation(doc.default_address)
			if res and res.get('latitude'):
				doc.latitude = res.get('latitude')
			if res and res.get('longitude'):
				doc.longitude = res.get('longitude')

@frappe.whitelist()
def update_help_articles():
	apps = frappe.get_installed_apps()
	modules_list = frappe.db.sql(''' select * from `tabModule Def` where app_name in ({}) '''.format(','.join(['"' + x + '"' for x in apps])), as_dict=True)
	for module in modules_list:
		path = frappe.get_module_path(module.module_name)
		file_path = os.path.join(path, 'help_desk', 'help_article.json')
		if os.path.exists(file_path):
			with open(file_path, 'r') as f:
				out = json.load(f)
				if out:
					keys = out.keys()
					for k in keys:
						for item in out[k]:
							check_record = frappe.db.sql('''select name from `tabHelp Article` where category = %(category)s and doctype_name = %(doctype)s''', {'category': item.get('category'), 'doctype': k}, as_dict=1)
							if check_record:
								doc = frappe.get_doc('Help Article', check_record[0].name)
							else:
								doc = frappe.new_doc('Help Article')
								doc.category = item.get('category')
								doc.doctype_name = item.get('doctype')
								doc.domain_name = item.get('domain_name')
								doc.published = item.get('published')
								doc.title = item.get('title')
								doc.owner = 'Administrator'
							doc.content = item.get('content')							
							doc.save(ignore_permissions=True)

@frappe.whitelist()
def clear_logs():
	'''
	used command to delete log files- find . -name "*.pyc" -exec rm -f {} \;
	'''
	dateTimeObj = datetime.now()
	key = dateTimeObj.strftime("%Y-%m-%d %H:%M:%S.%f")
	filelist = []
	for x in range(10):
		filelist.append("frappe.log."+str(x))
	for y in range(10):
		filelist.append("web.error.log."+str(x))
	for z in range(10):
		filelist.append("web.log."+str(x))
	commands=[]
	for files in filelist:
		commands.append("find . -name '{files}' -exec rm -f {} \;".format(files=files))

	frappe.enqueue('go1_commerce.utils.utils.run_command',
		commands=commands,
		doctype="Website",
		key=key
	)




@frappe.whitelist()
def redirect_to_new_domain(host):
	try:
		import werkzeug.utils
		frappe.log_error(host, "host-redirect_to_new_domain")
		html ="host: "+str(host)+"\n"
		FROM_DOMAIN = host
		html +="FROM_DOMAIN: "+str(FROM_DOMAIN)+"\n"
		TO_DOMAIN = "www."+host
		html +="TO_DOMAIN: "+str(TO_DOMAIN)+"\n"
		frappe.log_error(html, "html-redirect_to_new_domain---1")
		werkzeug.utils.redirect(TO_DOMAIN)
		
		from urllib.parse import urlparse, urlunparse
		from flask import Flask, redirect, request
		frappe.log_error(request.url, "request.url")
		urlparts = urlparse(request.url)
		html +="urlparts: "+str(urlparts)+"\n"
		html +="urlparts.netloc: "+str(urlparts.netloc)+"\n"
		frappe.log_error(html, "html-redirect_to_new_domain---2")
		app = Flask(__name__)
		
		
		if urlparts.netloc == FROM_DOMAIN:
			urlparts_list = list(urlparts)
			html +="urlparts_list: "+str(urlparts_list)+"\n"
			urlparts_list[1] = TO_DOMAIN
			frappe.log_error(html, "html-urlparts_list")
			dt = redirect(urlunparse(urlparts_list), code=301)
			frappe.log_error(dt, "dt-urlparts_list")
			return redirect(urlunparse(urlparts_list), code=301)
	except Exception as e:
		frappe.log_error(e,"setup.redirect_to_new_domain")

@frappe.whitelist()
def minify_string(html):
	import re
	return_String = html.replace('\n','')
	return re.sub(">\s*<","><",return_String)
