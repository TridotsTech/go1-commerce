# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt,nowdate, getdate
from frappe.utils import flt, nowdate,getdate, add_to_date
import datetime
from frappe.utils import flt,getdate,nowdate
from datetime import datetime
from frappe.utils import now_datetime
from go1_commerce.utils.setup import get_settings
current_date = timestamp = now_datetime().strftime(" %Y-%m-%d %H:%M:%S")

class Wallet(Document):
	pass

def get_all_orders_transaction(**kwargs):
	transaction = frappe.db.sql('''SELECT order_id
								FROM `tabWallet Transaction`
								WHERE docstatus = 1
									AND type = "Business"
									AND reference = "Order"
									AND order_type = "Order"
									AND is_settlement_paid = 0
									AND transaction_type = "Pay"
									AND party = %s 
								ORDER BY creation desc
							''',kwargs.get('user'),as_dict=1)
	return transaction

def get_all_orders_total_count(**kwargs):
	total_count = frappe.db.sql('''SELECT ifnull(count(*),0) 
								AS count 
								FROM `tabWallet Transaction`
								WHERE docstatus = 1
									AND is_settlement_paid = 0 
									AND party = %s 
								ORDER BY creation desc
							''',kwargs.get('user'),as_dict=1)
	return total_count

def get_all_orders_list(start,**kwargs):
	order_list = frappe.db.sql('''SELECT 
									ifnull(order_id,name) AS name,
									ifnull(reference,'') AS reference ,total_value , amount 
								FROM `tabWallet Transaction`
								WHERE docstatus = 1
									AND is_settlement_paid = 0 
									AND transaction_type = "Pay"
									AND party = %s 
								ORDER BY creation desc limit {0},{1}
							'''.format(start,int(kwargs.get('page_len'))),kwargs.get('user'),as_dict=1)
	return order_list

@frappe.whitelist()
def get_all_orders(**kwargs):
	try:
		condition = 'total_amount <> 0'
		currencyname = get_settings("Catalog Settings")
		if currencyname.default_currency:
			currency = frappe.db.get_value("Currency",currencyname.default_currency,'symbol')
		else:
			currency = "₹"
		start=(int(kwargs.get('page_no'))-1)*int(kwargs.get('page_len'))
		transaction = get_all_orders_transaction(**kwargs)
		if transaction:
			order_trans = ", ".join(['"' + i['order_id'] + '"' for i in transaction])
		total_count = get_all_orders_total_count(**kwargs)
		order_list = get_all_orders_list(start,**kwargs)
		res = {	'orders':order_list,
         		'count':total_count[0].count,
           		"currency":currency}
		return res
	except Exception:
		frappe.log_error(frappe.get_traceback(), "wallet.get_all_orders")

def total_and_order_list(start, **kwargs):
	total_count = frappe.db.sql('''SELECT ifnull(count(*),0) AS count 
								FROM `tabWallet Transaction`
								WHERE docstatus = 1
									AND is_settlement_paid = 0 
									AND transaction_type = "Receive"
									AND status = "Pending"
									AND party = %s 
								ORDER BY creation desc
							''',kwargs.get('user'),as_dict = 1)
	order_list = frappe.db.sql('''SELECT 
									ifnull(order_id,name) AS name,
									ifnull(reference,'') AS reference ,total_value , amount 
								FROM `tabWallet Transaction` 
								WHERE docstatus = 1 
									AND is_settlement_paid = 0 
									AND transaction_type = "Receive"
									AND status = "Pending"
									AND party = %s 
								ORDER BY creation desc limit {0},{1}
							'''.format(start,int(kwargs.get('page_len'))),kwargs.get('user'),as_dict=1)
	return [total_count, order_list]

@frappe.whitelist()
def get_commission_list(**kwargs):
	try:
		condition = 'total_amount <> 0'
		currencyname = get_settings("Catalog Settings")
		if currencyname.default_currency:
			currency = frappe.db.get_value("Currency",currencyname.default_currency,'symbol')
		else:
			currency = "₹"
		start = (int(kwargs.get('page_no'))-1)*int(kwargs.get('page_len'))
		transaction = frappe.db.sql('''SELECT order_id 
									FROM `tabWallet Transaction`
									WHERE docstatus = 1
										AND reference = "Order"
										AND order_type = "Order"
										AND is_settlement_paid = 1 
										AND is_fund_added = 0
										AND transaction_type = "Receive"
										AND party = %s 
          							ORDER BY creation desc
								''',kwargs.get('user'),as_dict=1)
		if transaction:
			order_trans = ", ".join(['"' + i['order_id'] + '"' for i in transaction])
		data = total_and_order_list(start, **kwargs)
		total_count = data[0]
		order_list = data[1]
		return {'orders':order_list,
				'count':total_count[0].count,
    			"currency":currency}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "wallet.get_commission_list")

def counter_play(start_count, **kwargs):
	counterpay_total_count = frappe.db.sql('''SELECT 
													ifnull(count(*),0) AS count 
												FROM `tabWallet Transaction`
												WHERE docstatus = 1 AND party = %s
													AND transaction_type = "Receive"
													AND disabled = 0 
												ORDER BY creation desc
											''',kwargs.get('user'),as_dict=1)
	counterpay_order_list = frappe.db.sql('''SELECT 
												name, transaction_type as reference,transaction_date,total_value, 
												amount, status,notes 
											FROM`tabWallet Transaction` 
											WHERE docstatus = 1
												AND party = %s
												AND transaction_type = "Receive" 
												AND disabled = 0 
											ORDER BY creation desc limit {0},{1}
										'''.format(start_count,int(kwargs.get('counter_page_len'))),
												kwargs.get('user'),as_dict=1)
	return [counterpay_total_count,counterpay_order_list]

def get_transactions(start_count, start, **kwargs):
	total_count = frappe.db.sql('''SELECT 
										ifnull(count(*),0) as count 
									FROM `tabWallet Transaction` 
									WHERE docstatus = 1 
										AND party = %s
										AND disabled = 0 
         							ORDER BY creation desc
								''',kwargs.get('user'),as_dict=1)
	order_list = frappe.db.sql('''SELECT 
										name, transaction_type as reference,transaction_date ,total_value,
										amount,status, notes 
									FROM `tabWallet Transaction` 
									WHERE docstatus = 1 
										AND party = %s
										AND transaction_type = "Pay"
										AND disabled = 0 
									ORDER BY creation desc 
									LIMIT {0},{1}
								'''.format(start,int(kwargs.get('page_len'))),kwargs.get('user'),as_dict=1)
	data = counter_play(start_count, **kwargs)
	counterpay_total_count = data[0]
	counterpay_order_list = data[1]
	return total_count,order_list,counterpay_total_count,counterpay_order_list

def get_transactions_not_proiv(start_count, start, **kwargs):
	total_count = frappe.db.sql(f'''SELECT IFNULL(COUNT(*), 0) AS count
									FROM `tabWallet Transaction`
									WHERE docstatus = 1
									AND party = %s
									AND transaction_type = "Pay"
									AND disabled = 0
									ORDER BY creation DESC
									''',kwargs.get('user'),as_dict=1)

	order_list = frappe.db.sql(f""" SELECT name, transaction_type AS reference, transaction_date, 
										total_value, amount, status, notes 
									FROM `tabWallet Transaction` 
									WHERE docstatus = 1 
										AND party = %(user)s 
										AND transaction_type = "Pay" 
										AND disabled = 0 
									ORDER BY creation DESC 
									LIMIT %(start)s, %(page_len)s
								""", {'user': kwargs.get('user'), 'start': start, 'page_len': int(kwargs.get('page_len'))}, as_dict=True)

	counterpay_total_count = frappe.db.sql(f""" SELECT IFNULL(COUNT(*), 0) AS count
												FROM `tabWallet Transaction`
												WHERE docstatus = 1
													AND party = %(user)s
													AND transaction_type = "Pay"
													AND disabled = 0
												ORDER BY creation DESC
											""", {'user': kwargs.get('user')}, as_dict=True)

	counterpay_order_list = frappe.db.sql(f"""	SELECT name, transaction_type AS reference, 
													transaction_date, total_value, amount, status, notes 
												FROM `tabWallet Transaction` 
												WHERE docstatus = 1 
													AND party = %(user)s 
													AND transaction_type = "Pay" 
													AND disabled = 0 
												ORDER BY creation DESC 
												LIMIT %(start_count)s, %(counter_page_len)s
											""",{'user': kwargs.get('user'), 'start_count': start_count,
													'counter_page_len': int(kwargs.get('counter_page_len'))}, 
													as_dict=True)

	return [total_count,order_list,counterpay_total_count,counterpay_order_list]

@frappe.whitelist()
def get_transaction_history(**kwargs):
	try:
		condition = 'total_amount <> 0'
		currencyname = get_settings("Catalog Settings")
		if currencyname.default_currency:
			currency = frappe.db.get_value("Currency",currencyname.default_currency,'symbol')
		else:
			currency = "₹"
		start = (int(kwargs.get('page_no'))-1)*int(kwargs.get('page_len'))
		start_count = (int(kwargs.get('counter_page_no'))-1)*int(kwargs.get('counter_page_len'))
		if kwargs.get('user') != "Service Provider":
			transaction = frappe.db.sql(''' SELECT order_id 
											FROM `tabWallet Transaction`
											WHERE docstatus = 1
												AND type = "Business"
												AND reference = "Order" 
												AND order_type = "Order"
												AND party = %s
												AND transaction_type = "Pay"
												AND disabled = 0 
											ORDER BY creation desc
							   			''',kwargs.get('user'),as_dict = 1)
			if transaction:
				order_trans = ", ".join(['"' + i['order_id'] + '"' for i in transaction])
			get_transactions(start_count,start, **kwargs)
		else:
			transaction = frappe.db.sql('''SELECT order_id 
											FROM `tabWallet Transaction` 
											WHERE docstatus = 1
												AND reference = "Order"
												AND order_type = "Order"
												AND type = %s
												AND transaction_type = "Pay"
												AND disabled = 0 
											ORDER BY creation desc
							   			''',kwargs.get('user'),as_dict = 1)
			if transaction:
				order_trans = ", ".join(['"' + i['order_id'] + '"' for i in transaction])
		data = get_transactions_not_proiv(start_count, start, **kwargs)
		total_count = data[0]
		order_list = data[1]
		counterpay_total_count = data[2]
		counterpay_order_list = data[3]
		return {
				'orders':order_list,
				'count':total_count[0].count,
				"currency":currency,
				"counter_pay":counterpay_order_list,
				"counterpay_count":counterpay_total_count[0].count
			   }
	except Exception:
		frappe.log_error(frappe.get_traceback(), " Error in wallet.get_commission_list")

@frappe.whitelist(allow_guest = True)
def make_withdraw_request(source_name,order_list=None):
	try:
		if source_name:
			source = frappe.get_all("Wallet",fields=["*"],
									filters={"name":source_name},ignore_permissions=True)[0]
		if flt(source.outstanding_amount)>0:
			total = source.outstanding_amount
		else:	
			total = source.withdraw_amount
		orderlist=order_list
		if len(orderlist)>0:
			trans_ref = ", ".join(['' + i + '' for i in orderlist])
		pe = frappe.new_doc("Wallet Withdrawal Request")
		pe.posting_date = nowdate()
		pe.party_type = source.user_type
		pe.party = source.user
		pe.party_name = source.name1
		pe.withdraw_amount = source.current_wallet_amount
		pe.withdrawal_type = "Auto Withdraw"
		pe.status = "Approved"
		if trans_ref:
			pe.order_ref=trans_ref
		pe.flags.ignore_permissions = True
		pe.submit()
		return "success"
	except Exception:
		frappe.log_error(frappe.get_traceback(), "wallet.make_withdraw_request") 

@frappe.whitelist(allow_guest = True)
def add_fund_to_wallet(source_name):
	default_currency = get_settings("Catalog Settings")
	if source_name:
		source = frappe.get_all("Wallet",fields = ["*"],filters = {"name":source_name})[0]
	transaction = frappe.db.sql(f'''SELECT order_id,amount,total_value,name 
									FROM `tabWallet Transaction` 
									WHERE is_settlement_paid=0
										AND transaction_type="Receive"
										AND status="Pending"
										AND party=%s 
									ORDER BY creation desc
							 	''',source.user,as_dict=1)
	for trans in transaction:
		wallet_entry = frappe.get_doc("Wallet Transaction",trans.name)
		wallet_entry.status="Approved"
		wallet_entry.save(ignore_permissions=True)
	return "success"


def get_if_not_provider(source, vendor):
    for n in source:
        n.to_be_received = frappe.db.sql('''SELECT  IFNULL(sum(amount),0) AS amount  
                                            FROM `tabWallet Transaction` 
                                            WHERE party = %s 
												AND transaction_type = "Receive" 
												AND status = "Pending"
                                        ''', vendor, as_dict = 1)[0].amount
        n.claimed_amount = frappe.db.sql('''SELECT IFNULL(sum(amount),0) AS amount 
                                            FROM `tabWallet Transaction` 
                                            WHERE party = %s 
												AND transaction_type = "Receive" 
												AND status = "Approved"
                                        ''', vendor, as_dict = 1)[0].amount
        n.total_amount = frappe.db.sql('''SELECT IFNULL(sum(amount),0) AS amount 
                                            FROM `tabWallet Transaction` 
                                            WHERE party = %s 
                                            	AND transaction_type = "Receive"
                                        ''', vendor, as_dict = 1)[0].amount
    return source


def get_if_provider(source, vendor):
	for n in source:
		n.to_be_received = frappe.db.sql('''SELECT IFNULL(sum(amount),0) AS amount  
											FROM `tabWallet Transaction` 
											WHERE type = %s 
											AND transaction_type = "Receive" 
											AND status = "Pending"
										''',vendor,as_dict = 1) [0].amount
		n.climed_amount= frappe.db.sql('''SELECT IFNULL(sum(amount),0) AS amount 
											FROM `tabWallet Transaction` 
											WHERE type = %s 
											AND transaction_type = "Receive" 
											AND (status = "Approved" OR status = "Credited")
										''',vendor,as_dict = 1)[0].amount
		n.total_amount=frappe.db.sql('''SELECT IFNULL(sum(amount),0) AS amount 
										FROM `tabWallet Transaction` 
										WHERE type = %s 
										AND transaction_type = "Receive"
									''',vendor,as_dict = 1)[0].amount
	return source

@frappe.whitelist(allow_guest = True)
def get_counter_apy_counters(vendor):
	if vendor!="Service Provider":
		source = frappe.db.sql(""" SELECT user_type, user, name1 AS user_name 
									FROM`tabWallet`
									WHERE user = %s
								""", vendor, as_dict = 1)
		return get_if_not_provider(source, vendor)
	else:
		source = frappe.db.sql(""" SELECT user_type, user, name1 AS user_name 
									FROM `tabWallet` 
									WHERE user = %s
						 		""", vendor, as_dict = 1)
		return get_if_provider(source, vendor)

@frappe.whitelist()
def get_wallet_settings():
	return frappe.get_single("Wallet Settings")

@frappe.whitelist()
def total_counter_graph_options(common_filters = [], ignore_permissions = True, count = 100):
	dash = get_dash_value()
	chart_options={}
	label=frappe.db.sql_list("""SELECT A.dt
								FROM (SELECT DATE_ADD('{from_date}', 
						  			INTERVAL @rownum := @rownum + 1 DAY) AS dt 
								FROM `tab{doctype}` 
						  		JOIN (SELECT @rownum := -1) r) A
								LEFT JOIN `tab{doctype}` O ON O.creation = A.dt 
						  		WHERE A.dt <= '{to_date}' 
						  		GROUP BY A.dt
							""".format(doctype = dash['reference_doctype'],
								  from_date=add_to_date(nowdate(),days = -7),to_date = nowdate()))
	labels=[]
	values=[]
	if count>0 and len(label)>0:
		check_data = frappe.db.sql('''SELECT name 
									FROM `tab{doctype}` 
									WHERE date(creation) between "{start_date}" 
										AND "{end_date}"
								'''.format(doctype = dash['reference_doctype'],
											start_date = label[0],end_date = label[len(label)-1]))
		if not check_data:
			lists = frappe.db.sql_list("""SELECT date(creation)
										FROM `tab{doctype}` ORDER BY creation desc limit 1
									""".format(doctype = dash['reference_doctype']))										
			label = frappe.db.sql_list("""SELECT A.dt
										FROM (SELECT DATE_ADD('{from_date}', 
											INTERVAL @rownum := @rownum + 1 DAY) AS dt 
										FROM `tab{doctype}` 
										JOIN (SELECT @rownum := -1) r) A
										LEFT JOIN `tab{doctype}` O ON O.creation = A.dt WHERE A.dt <= '{to_date}' 
										GROUP BY A.dt
									""".format(doctype = dash['reference_doctype'],
												from_date = add_to_date(lists[0],days = -7),to_date = lists[0]))
	for item in label:
		counter_filter = []
		dt = getdate(item)
		next_date = add_to_date(dt,days=1)
		counter_filter.append(['creation','>',datetime(year = dt.year, day = dt.day, month = dt.month)])
		counter_filter.append(['creation','<',datetime(year = next_date.year, day = next_date.day,
															month = next_date.month)])
		new_filter = (common_filters+counter_filter)
		graph_res = frappe.get_list(dash['reference_doctype'],fields=['*'],
							filters=new_filter,ignore_permissions=ignore_permissions,limit_page_length=count)
		if dash['counter_type'] == 'Count':
			values.append(len(graph_res))
		elif dash['counter_type'] == 'Sum':
			values.append(round(sum(res[dash['referred_field']] for res in graph_res),2))
		else:
			values.append(round((sum(res[dash['referred_field']] for res in graph_res)/len(graph_res)),2))
		labels.append(dt.strftime("%b %d %y"))
	chart_options = dash['graph_style']
	chart_options['xaxis'] = { 'categories': labels }
	chart_options['series'] = [{ 'data':values }]
	return {"chart_options":dict(chart_options)}


def get_dash_value():
	dash = {"reference_doctype":"Wallet Transaction", 
			"counter_type":"Sum", 
			"referred_field":"amount", 
			"graph_style":{"tooltip": {"fixed": {"enabled": 1}}, 
							"colors": ["#f3eef2"], 
							"chart": {"background": "#d83c6b", 
							"sparkline": {"enabled": 1}, 
							"height": 100, 
							"animations": {"easing": "easein", 
											"speed": 800, "enabled": 1, 
											"animateGradually": {"enabled": 1, "delay": 150}}, 
							"type": "bar"}, 
							"plotOptions": {"bar": {"columnWidth": "80%", 
													"horizontal": 0, 
													"barHeight": "100%"}}, 
							"markers": {"size": 0}, 
							"stroke": {"curve": "smooth", "width": 1}}}
	return dash