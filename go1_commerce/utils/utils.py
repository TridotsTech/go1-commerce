# -*- coding: utf-8 -*-
# Copyright (c) 2017, Tridots Tech Private Ltd. and contributors
# For license information, please see license.txt


import frappe
from functools import wraps
from subprocess import Popen, PIPE, STDOUT
import re, shlex
from frappe.utils import today, encode, nowtime
from six import iteritems, text_type, string_types
import json
from frappe.desk.reportview import validate_args
from frappe.model.db_query import check_parent_permission
from frappe import _

def run_command(commands, doctype, key, cwd='..', docname=' ', after_command=None):
	verify_whitelisted_call()
	start_time = frappe.utils.time.time()
	console_dump = ""
	logged_command = " && ".join(commands)
	logged_command += " "
	sensitive_data = ["--mariadb-root-password", "--admin-password", "--root-password"]
	for password in sensitive_data:
		logged_command = re.sub("{password} .*? ".format(password=password), '', logged_command, flags=re.DOTALL)
	doc = frappe.get_doc({'doctype': 'Executed Command', 'key': key, 'source': doctype+': '+docname,
		'command': logged_command, 'console': console_dump, 'status': 'Ongoing'})
	doc.insert()
	frappe.db.commit()
	frappe.publish_realtime(key, "Executing Command:\n{logged_command}\n\n".format(logged_command=logged_command), user=frappe.session.user)
	try:
		for command in commands:
			terminal = Popen(shlex.split(command), stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=cwd)
			for c in iter(lambda: safe_decode(terminal.stdout.read(1)), ''):
				frappe.publish_realtime(key, c, user=frappe.session.user)
				console_dump += c
		if terminal.wait():
			_close_the_doc(start_time, key, console_dump, status='Failed', user=frappe.session.user)
		else:
			_close_the_doc(start_time, key, console_dump, status='Success', user=frappe.session.user)
	except Exception as e:
		_close_the_doc(start_time, key, "{} \n\n{}".format(e, console_dump), status='Failed', user=frappe.session.user)
	finally:
		frappe.db.commit()
		frappe.enqueue('go1_commerce.utils.utils._refresh',
			doctype=doctype, docname=docname, commands=commands)

def run_ssl_command(commands, doctype, key, cwd='..', docname=' ', after_command=None):
	verify_whitelisted_call()
	start_time = frappe.utils.time.time()
	console_dump = ""
	logged_command = " && ".join(commands)
	logged_command += " " 
	sensitive_data = ["--mariadb-root-password", "--admin-password", "--root-password"]
	for password in sensitive_data:
		logged_command = re.sub("{password} .*? ".format(password=password), '', logged_command, flags=re.DOTALL)
	doc = frappe.get_doc({'doctype': 'Executed Command', 'key': key, 'source': doctype+': '+docname,
		'command': logged_command, 'console': console_dump, 'status': 'Ongoing'})
	doc.insert()
	frappe.db.commit()
	frappe.publish_realtime(key, "Executing Command:\n{logged_command}\n\n".format(logged_command=logged_command), user=frappe.session.user)
	try:
		for command in commands:
			terminal = Popen(shlex.split(command), stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=cwd)
			input2 = "Y"
			input3 = "Y"
			concat_query = "{}\n{}\n".format(input2, input3)
			terminal.communicate(input=concat_query.encode('utf-8'))
			for c in iter(lambda: safe_decode(terminal.stdout.read(1)), ''):
				frappe.publish_realtime(key, c, user=frappe.session.user)
				console_dump += c
		if terminal.wait():
			_close_the_doc(start_time, key, console_dump, status='Failed', user=frappe.session.user)
		else:
			_close_the_doc(start_time, key, console_dump, status='Success', user=frappe.session.user)
	except Exception as e:
		_close_the_doc(start_time, key, "{} \n\n{}".format(e, console_dump), status='Failed', user=frappe.session.user)
	finally:
		frappe.db.commit()
		frappe.enqueue('go1_commerce.utils.utils._refresh',
			doctype=doctype, docname=docname, commands=commands)

def _close_the_doc(start_time, key, console_dump, status, user):
	time_taken = frappe.utils.time.time() - start_time
	final_console_dump = ''
	console_dump = console_dump.split('\n\r')
	for i in console_dump:
		i = i.split('\r')
		final_console_dump += '\n'+i[-1]
	frappe.set_value('Executed Command', key, 'console', final_console_dump)
	frappe.set_value('Executed Command', key, 'status', status)
	frappe.set_value('Executed Command', key, 'time_taken', time_taken)
	frappe.publish_realtime(key, '\n\n'+status+'!\nThe operation took '+str(time_taken)+' seconds', user=user)

def _refresh(doctype, docname, commands):
	frappe.get_doc(doctype, docname).run_method('after_command', commands=commands)

@frappe.whitelist()
def verify_whitelisted_call():
	if 'go1_commerce' not in frappe.get_installed_apps():
		raise ValueError("This site does not have Ecommerce Business Store installed.")

def safe_decode(string, encoding = 'utf-8'):
	try:
		string = string.decode(encoding)
	except Exception:
		pass
	return string

@frappe.whitelist()
def run_queue_method(command):
	commands=[]
	if command:
		commands.append(command)
	key = today() + " " + nowtime()
	frappe.enqueue('go1_commerce.utils.utils.run_command',
		commands=commands,
		doctype="Website",
		key=key
	)

@frappe.whitelist()
def role_auth(role,method="GET"):
	def custom_decorator(func):
		@frappe.whitelist()
		@wraps(func)
		def wrapper(*args, **kwargs):
			request_type = frappe.local.request.method
			if not request_type == method and method!="PATCH":
				frappe.response.http_status_code = 400
				frappe.response['message']= {"status":"Failed","error_message":"Bad Request","data":""}
			else:	
				authorization_header = frappe.get_request_header("Authorization", "").split(" ")
				if len(authorization_header)>1:
					token = authorization_header[1].split(":")
					users = frappe.db.get_all("User", filters={"api_key": token[0]})
					if users:
						has_role = frappe.db.get_all('Has Role',
								filters={'parent': users[0].name, 'role': role})
						if has_role:
							if role =='Customer':
								customer_email = frappe.db.get_all("Customers", filters={"email": users[0].name})
								if customer_email:
									return func(*args, **kwargs)
							else:
								return func(*args, **kwargs)
						else:
							frappe.response.http_status_code = 403
							frappe.response['message']= {"status":"Failed","error_message":"Authorization Required","data":""}
				frappe.response.http_status_code = 403
				frappe.response['message']= {"status":"Failed","error_message":"Authorization Required","data":""}
		return wrapper
	return custom_decorator

@frappe.whitelist()
def customer_reg_auth(method="GET"):
	def customer_reg_decorator(func):
		@frappe.whitelist()
		@wraps(func)
		def wrapper(*args, **kwargs):
			request_type = frappe.local.request.method
			if not request_type == method:
				frappe.response.http_status_code = 400
				frappe.response['message']= {"status":"Failed","error_message":"Bad Request","data":""}
				
			else:	
				authorization_header = frappe.get_request_header("Authorization", "").split(" ")
				if len(authorization_header)>1:
					token = authorization_header[1]
					customer_regs = frappe.db.get_all("Customer Registration",filters={"uuid":token})
					if customer_regs:
						return func(*args, **kwargs)
							
					else:
						frappe.response.http_status_code = 403
						frappe.response['message']= {"status":"Failed","error_message":"Authorization Required","data":""}
				frappe.response.http_status_code = 403
				frappe.response['message']= {"status":"Failed","error_message":"Authorization Required","data":""}
		return wrapper
	return customer_reg_decorator

def get_auth_token(user):
	api_key = frappe.db.get_value("User", user, "api_key")
	if api_key:
		api_secret = frappe.utils.password.get_decrypted_password("User", user, fieldname='api_secret')
		return {"api_secret": api_secret, "api_key": api_key}
	else:
		return {"status":"failed","error_message":"Api key not generated."}

def get_customer_from_token():
	if frappe.get_request_header("Authorization", ""):
		authorization_header = frappe.get_request_header("Authorization", "").split(" ")
		if authorization_header and len(authorization_header)>1:
			token = authorization_header[1].split(":")
			users = frappe.db.get_all("User",filters={"api_key":token[0]})
			if users:
				customer_email = frappe.db.get_all("Customers",filters={"email":users[0].name,"customer_status":"Approved"})
				if customer_email:
					customer_id = customer_email[0].name
					frappe.log_error("customer_id",customer_id)
					return customer_id
	return None

def get_customer_reg_from_token():
	authorization_header = frappe.get_request_header("Authorization", "").split(" ")
	if authorization_header and len(authorization_header)>1:
		token = authorization_header[1]
		customer_regs = frappe.db.get_all("Customer Registration",filters={"uuid":token})
		if customer_regs:
			return customer_regs[0].name
	return None
def get_sales_executive_from_token():
	authorization_header = frappe.get_request_header("Authorization", "").split(" ")
	if authorization_header and len(authorization_header)>1:
		token = authorization_header[1].split(":")
		users = frappe.db.get_all("User",filters={"api_key":token[0]})
		if users:

			se_email = frappe.db.get_all("Employee",filters={"email_id":users[0].name})
			if se_email:
				return se_email[0].name
	return None

@frappe.whitelist()
def get_sales_executive_customer_list():
	authorization_header = frappe.get_request_header("Authorization", "").split(" ")
	if authorization_header:
		token = authorization_header[1].split(":")
		users = frappe.db.get_all("User",filters={"api_key":token[0]})
		if users:
			se_email = frappe.db.get_all("Employee",filters={"email_id":users[0].name})
			Customers = DocType("Customers")
			Route = DocType("Route")
			condition = ""
			if se_email and se_email[0].name:
			    condition = Customers.route == Route.parent
			query = (
			    frappe.qb.from_(Customers)
			    .left_join(Route)
			    .on(Customers.route == Route.parent)
			    .select(Customers.name, Customers.center, Customers.route, Route.se, Route.se_name)
			    .where(Customers.route.is_not_null())
			)
			if condition:
			    query = query.where(condition)
			result = query.run(as_dict=True)

	return None

def get_today_date(time_zone=None, replace=False):
	'''
		get today  date based on selected time_zone
	'''
	from datetime import date, datetime, timedelta
	from pytz import timezone
	if not time_zone:
		time_zone = frappe.db.get_single_value('System Settings', 'time_zone')
	currentdate = datetime.now()
	currentdatezone = datetime.now(timezone(time_zone))
	if replace:
		return currentdatezone.replace(tzinfo=None)
	else:
		return currentdatezone

def exception_errors(code):
	try:
		if frappe.local.response.exc_type:
			del frappe.local.response.exc_type
		frappe.local.response.http_status_code = code
		frappe.local.response.message = {"status":"Failed","error_message":json.loads(frappe.local.message_log[0]).get('message'),"data":""}
		if frappe.local.message_log and frappe.local.message_log[0]:
			del frappe.local.message_log[0]
	except IndexError:
		try:
			frappe.local.response.http_status_code = code
			frappe.local.response.status = "Failed"
			frappe.local.response.message = json.loads(frappe.local.message_log)
		except TypeError:
			pass

def authentication_exception():
	exception_errors(code = 400)

def uniquevalidation_exception():
	exception_errors(code = 400)

def doesnotexist_exception():
	exception_errors(code = 404)

def permission_exception():
	exception_errors(code = 400)

def validation_exception():
	exception_errors(code = 400)

def linkvalidation_exception():
	exception_errors(code = 400)

def updateaftersubmit_exception():
	exception_errors(code = 400)

def oserror_exception():
	exception_errors(code = 400)

def error_400_bad_request(msg):
	frappe.response.http_status_code = 400
	frappe.local.response.message = {"status":"Failed","error_message":msg}

def response_200_(data,msg=""):
	frappe.response.http_status_code = 200 
	frappe.local.response.message = {"status":"Success","success_massage":msg,"data":data}

def error404_not_found_error(msg):
	frappe.response.http_status_code = 400 
	frappe.local.response.message = {"status":"Failed","error_message":msg}

def se_not_found_error(msg = None):
	frappe.local.response.http_status_code = 400
	frappe.local.response.message = {"status":"Failed","error_message":"Sales Executive Not Found" if not msg else msg}

def other_exception(msg):
	frappe.local.response.http_status_code = 400
	frappe.local.response.message = {"status":"Failed","error_message":"Internal server error."}
	frappe.log_error(title = f'Error in {msg}',message = frappe.get_traceback())

def check_mandatory_exception(message=None):
	try:
		if message:
			frappe.response.http_status_code = 404
			frappe.response['message']={"status":"Failed","error_message":message,"data":""}
		else:
			del frappe.local.response.exc_type
			frappe.local.response.http_status_code = 404
			frappe.local.response.message = {"status":"Failed","error_message":json.loads(frappe.local.message_log[0]).get('message'),"data":""}
			del frappe.local.message_log[0]
	except IndexError:
		frappe.local.response.http_status_code = 404
		frappe.local.response.status = "Failed"
		frappe.local.response.message = json.loads(frappe.local.message_log)

def get_uploaded_file_content(filedata):
	try:

		import base64
		if filedata:
			if "," in filedata:
				filedata = filedata.rsplit(",", 1)[1]
			uploaded_content = base64.b64decode(filedata)
			return uploaded_content
		else:
			frappe.msgprint(_('No file attached'))
			return None

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "utils.utils.get_uploaded_file_content")

def delete_file(path):
	import os
	if path:
		parts = os.path.split(path.strip('/'))
		if parts[0] == 'files':
			path = frappe.utils.get_site_path('public', 'files', parts[-1])
		else:
			path = frappe.utils.get_site_path('private', 'files', parts[-1])
		path = encode(path)
		if os.path.exists(path):
			os.remove(path)

@frappe.whitelist()
def validate_link(doctype: str, docname: str, fields=None):
	if not isinstance(doctype, str):
		frappe.throw(_("DocType must be a string"))

	if not isinstance(docname, str):
		frappe.throw(_("Document Name must be a string"))

	if doctype != "DocType" and doctype != "Order Item" and not (
		frappe.has_permission(doctype, "select") or frappe.has_permission(doctype, "read")
	):
		frappe.throw(
			_("You do not have Read or Select Permissions for {}").format(frappe.bold(doctype)),
			frappe.PermissionError,
		)

	values = frappe._dict()
	values.name = frappe.db.get_value(doctype, docname, cache=True)

	fields = frappe.parse_json(fields)
	if not values.name or not fields:
		return values

	try:
		values.update(get_value(doctype, fields, docname))
	except frappe.PermissionError:
		frappe.clear_last_message()
		frappe.msgprint(
			_("You need {0} permission to fetch values from {1} {2}").format(
				frappe.bold(_("Read")), frappe.bold(doctype), frappe.bold(docname)
			),
			title=_("Cannot Fetch Values"),
			indicator="orange",
		)

	return values	

@frappe.whitelist()
def get_value(doctype, fieldname, filters=None, as_dict=True, debug=False, parent=None):
	from frappe.utils import get_safe_filters

	"""Returns a value form a document
	:param doctype: DocType to be queried
	:param fieldname: Field to be returned (default `name`)
	:param filters: dict or string for identifying the record"""
	if frappe.is_table(doctype):
		check_parent_permission(parent, doctype)

	if not frappe.has_permission(doctype, parent_doctype=parent):
		frappe.throw(_("No permission for {0}").format(_(doctype)), frappe.PermissionError)

	filters = get_safe_filters(filters)
	if isinstance(filters, str):
		filters = {"name": filters}

	try:
		fields = frappe.parse_json(fieldname)
	except (TypeError, ValueError):
		fields = [fieldname]

	if not filters:
		filters = None

	if frappe.get_meta(doctype).issingle:
		value = frappe.db.get_values_from_single(fields, filters, doctype, as_dict=as_dict, debug=debug)
	else:
		value = get_list(
			doctype,
			filters=filters,
			fields=fields,
			debug=debug,
			limit_page_length=1,
			parent=parent,
			as_dict=as_dict,
		)

	if as_dict:
		return value[0] if value else {}

	if not value:
		return

	return value[0] if len(fields) > 1 else value[0][0]
@frappe.whitelist()
def get_list(
	doctype,
	fields=None,
	filters=None,
	order_by=None,
	limit_start=None,
	limit_page_length=20,
	parent=None,
	debug=False,
	as_dict=True,
	or_filters=None,
):
	"""Returns a list of records by filters, fields, ordering and limit

	:param doctype: DocType of the data to be queried
	:param fields: fields to be returned. Default is `name`
	:param filters: filter list by this dict
	:param order_by: Order by this fieldname
	:param limit_start: Start at this index
	:param limit_page_length: Number of records to be returned (default 20)"""
	if frappe.is_table(doctype):
		check_parent_permission(parent, doctype)

	args = frappe._dict(
		doctype=doctype,
		parent_doctype=parent,
		fields=fields,
		filters=filters,
		or_filters=or_filters,
		order_by=order_by,
		limit_start=limit_start,
		limit_page_length=limit_page_length,
		debug=debug,
		as_list=not as_dict,
	)

	validate_args(args)
	return frappe.get_list(**args)


@frappe.whitelist()
def cancel_all_linked_docs(docs, ignore_doctypes_on_cancel_all=None):
	"""
	Cancel all linked doctype, optionally ignore doctypes specified in a list.

	Arguments:
	        docs (json str) - It contains list of dictionaries of a linked documents.
	        ignore_doctypes_on_cancel_all (list) - List of doctypes to ignore while cancelling.
	"""
	if ignore_doctypes_on_cancel_all is None:
		ignore_doctypes_on_cancel_all = []
	from frappe.desk.form.linked_with import validate_linked_doc
	docs = json.loads(docs)
	if isinstance(ignore_doctypes_on_cancel_all, str):
		ignore_doctypes_on_cancel_all = json.loads(ignore_doctypes_on_cancel_all)
	for i, doc in enumerate(docs, 1):
		if validate_linked_doc(doc, ignore_doctypes_on_cancel_all):
			if frappe.db.get_value(doc.get("doctype"), doc.get("name"),"docstatus")==1:
				linked_doc = frappe.get_doc(doc.get("doctype"), doc.get("name"))
				linked_doc.cancel()
		frappe.publish_progress(percent=i / len(docs) * 100, title="Cancelling documents")

def validate_date(dates):
	import re
	pattern_str = r'^\d{4}-\d{2}-\d{2}$'
	for date in dates:
		if not re.match(pattern_str, date):
			return False
	return True

def get_today_date(time_zone = None, replace = False):
	''' get today  date based on selected time_zone '''
	from pytz import timezone
	from datetime import datetime
	if not time_zone:
		time_zone = frappe.db.get_single_value('System Settings', 'time_zone')
	currentdatezone = datetime.now(timezone(time_zone))
	if replace:
		return currentdatezone.replace(tzinfo=None)
	else:
		return currentdatezone
	
def get_attributes_json(attribute_id):
	if attribute_id:
		if attribute_id.find('\n'):
			attribute_ids = attribute_id.split('\n')
			ids_list = []
			for x in attribute_ids:
				if x:
					ids_list.append(x)
			attribute_id = json.dumps(ids_list)
		return attribute_id.replace(' ','')