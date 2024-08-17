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
from frappe.query_builder import DocType, Order, functions as fn, Field

class Wallet(Document):
	pass

def get_all_orders_transaction(**kwargs):
	WalletTransaction = DocType('Wallet Transaction')
	query = (
		frappe.qb.from_(WalletTransaction)
		.select(WalletTransaction.order_id)
		.where(WalletTransaction.docstatus == 1)
		.where(WalletTransaction.type == "Business")
		.where(WalletTransaction.reference == "Order")
		.where(WalletTransaction.order_type == "Order")
		.where(WalletTransaction.is_settlement_paid == 0)
		.where(WalletTransaction.transaction_type == "Pay")
		.where(WalletTransaction.party == kwargs.get('user'))
		.orderby(WalletTransaction.creation, order=Order.desc)
	)
	transaction = query.run(as_dict=True)
	return transaction

def get_all_orders_total_count(**kwargs):
	WalletTransaction = DocType('Wallet Transaction')
	query = (
		frappe.qb.from_(WalletTransaction)
		.select(fn.IfNull(fn.Count('*'), 0).as_('count'))
		.where(WalletTransaction.docstatus == 1)
		.where(WalletTransaction.is_settlement_paid == 0)
		.where(WalletTransaction.party == kwargs.get('user'))
		.orderby(WalletTransaction.creation, order=Order.desc)
	)
	total_count = query.run(as_dict=True)
	return total_count

def get_all_orders_list(start,**kwargs):
	WalletTransaction = DocType('Wallet Transaction')
	query = (
		frappe.qb.from_(WalletTransaction)
		.select(
			fn.IfNull(WalletTransaction.order_id, WalletTransaction.name).as_('name'),
			fn.IfNull(WalletTransaction.reference, '').as_('reference'),
			WalletTransaction.total_value,
			WalletTransaction.amount
		)
		.where(WalletTransaction.docstatus == 1)
		.where(WalletTransaction.is_settlement_paid == 0)
		.where(WalletTransaction.transaction_type == 'Pay')
		.where(WalletTransaction.party == kwargs.get('user'))
		.orderby(WalletTransaction.creation, order=Order.desc)
		.limit(int(kwargs.get('page_len')))
		.offset(start)
	)
	order_list = query.run(as_dict=True)
	return order_list


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
	WalletTransaction = DocType('Wallet Transaction')
	query = (
		frappe.qb.from_(WalletTransaction)
		.select(
			fn.IfNull(fn.Count('*'), 0).as_('count')
		)
		.where(WalletTransaction.docstatus == 1)
		.where(WalletTransaction.is_settlement_paid == 0)
		.where(WalletTransaction.transaction_type == 'Receive')
		.where(WalletTransaction.status == 'Pending')
		.where(WalletTransaction.party == kwargs.get('user'))
		.orderby(WalletTransaction.creation, order=Order.desc)
	)
	total_count = query.run(as_dict=True)
	WalletTransaction = DocType('Wallet Transaction')
	query = (
		frappe.qb.from_(WalletTransaction)
		.select(
			fn.IfNull(WalletTransaction.order_id, WalletTransaction.name).as_('name'),
			fn.IfNull(WalletTransaction.reference, '').as_('reference'),
			WalletTransaction.total_value,
			WalletTransaction.amount
		)
		.where(WalletTransaction.docstatus == 1)
		.where(WalletTransaction.is_settlement_paid == 0)
		.where(WalletTransaction.transaction_type == 'Receive')
		.where(WalletTransaction.status == 'Pending')
		.where(WalletTransaction.party == kwargs.get('user'))
		.orderby(WalletTransaction.creation, order=Order.desc)
		.limit(int(kwargs.get('page_len')))
		.offset(start)
	)
	order_list = query.run(as_dict=True)
	return [total_count, order_list]


def get_commission_list(**kwargs):
	try:
		condition = 'total_amount <> 0'
		currencyname = get_settings("Catalog Settings")
		if currencyname.default_currency:
			currency = frappe.db.get_value("Currency",currencyname.default_currency,'symbol')
		else:
			currency = "₹"
		start = (int(kwargs.get('page_no'))-1)*int(kwargs.get('page_len'))
		
		WalletTransaction = DocType('Wallet Transaction')
		query = (
			frappe.qb.from_(WalletTransaction)
			.select(WalletTransaction.order_id)
			.where(WalletTransaction.docstatus == 1)
			.where(WalletTransaction.reference == "Order")
			.where(WalletTransaction.order_type == "Order")
			.where(WalletTransaction.is_settlement_paid == 1)
			.where(WalletTransaction.is_fund_added == 0)
			.where(WalletTransaction.transaction_type == "Receive")
			.where(WalletTransaction.party == kwargs.get('user'))
			.orderby(WalletTransaction.creation, order=Order.desc)
		)
		transaction = query.run(as_dict=True)
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
	WalletTransaction = DocType('Wallet Transaction')
	counterpay_total_count_query = (
		frappe.qb.from_(WalletTransaction)
		.select(fn.IfNull(fn.Count('*'), 0).as_('count'))
		.where(WalletTransaction.docstatus == 1)
		.where(WalletTransaction.party == kwargs.get('user'))
		.where(WalletTransaction.transaction_type == "Receive")
		.where(WalletTransaction.disabled == 0)
		.orderby(WalletTransaction.creation, order=Order.desc)
	)
	counterpay_total_count = counterpay_total_count_query.run(as_dict=True)
	counterpay_order_list_query = (
		frappe.qb.from_(WalletTransaction)
		.select(
			WalletTransaction.name, 
			WalletTransaction.transaction_type.as_('reference'),
			WalletTransaction.transaction_date,
			WalletTransaction.total_value,
			WalletTransaction.amount,
			WalletTransaction.status,
			WalletTransaction.notes
		)
		.where(WalletTransaction.docstatus == 1)
		.where(WalletTransaction.party == kwargs.get('user'))
		.where(WalletTransaction.transaction_type == "Receive")
		.where(WalletTransaction.disabled == 0)
		.orderby(WalletTransaction.creation, order=Order.desc)
		.limit(int(kwargs.get('counter_page_len')))
		.offset(start_count)
	)
	counterpay_order_list = counterpay_order_list_query.run(as_dict=True)
	return [counterpay_total_count,counterpay_order_list]

def get_transactions(start_count, start, **kwargs):
	WalletTransaction = DocType('Wallet Transaction')
	total_count_query = (
		frappe.qb.from_(WalletTransaction)
		.select(fn.IfNull(fn.Count('*'), 0).as_('count'))
		.where(WalletTransaction.docstatus == 1)
		.where(WalletTransaction.party == kwargs.get('user'))
		.where(WalletTransaction.disabled == 0)
		.orderby(WalletTransaction.creation, order=Order.desc)
	)
	total_count = total_count_query.run(as_dict=True)
	order_list_query = (
		frappe.qb.from_(WalletTransaction)
		.select(
			WalletTransaction.name,
			WalletTransaction.transaction_type.as_('reference'),
			WalletTransaction.transaction_date,
			WalletTransaction.total_value,
			WalletTransaction.amount,
			WalletTransaction.status,
			WalletTransaction.notes
		)
		.where(WalletTransaction.docstatus == 1)
		.where(WalletTransaction.party == kwargs.get('user'))
		.where(WalletTransaction.transaction_type == "Pay")
		.where(WalletTransaction.disabled == 0)
		.orderby(WalletTransaction.creation, order=Order.desc)
		.limit(int(kwargs.get('page_len')))
		.offset(start)
	)
	order_list = order_list_query.run(as_dict=True)
	data = counter_play(start_count, **kwargs)
	counterpay_total_count = data[0]
	counterpay_order_list = data[1]
	return total_count,order_list,counterpay_total_count,counterpay_order_list

def get_transactions_not_proiv(start_count, start, **kwargs):
	WalletTransaction = DocType('Wallet Transaction')
	total_count_query = (
		frappe.qb.from_(WalletTransaction)
		.select(fn.IfNull(fn.Count('*'), 0).as_('count'))
		.where(WalletTransaction.docstatus == 1)
		.where(WalletTransaction.party == kwargs.get('user'))
		.where(WalletTransaction.transaction_type == "Pay")
		.where(WalletTransaction.disabled == 0)
		.orderby(WalletTransaction.creation, order=Order.desc)
	)
	total_count = total_count_query.run(as_dict=True)

	order_list_query = (
		frappe.qb.from_(WalletTransaction)
		.select(
			WalletTransaction.name,
			WalletTransaction.transaction_type.as_('reference'),
			WalletTransaction.transaction_date,
			WalletTransaction.total_value,
			WalletTransaction.amount,
			WalletTransaction.status,
			WalletTransaction.notes
		)
		.where(WalletTransaction.docstatus == 1)
		.where(WalletTransaction.party == kwargs.get('user'))
		.where(WalletTransaction.transaction_type == "Pay")
		.where(WalletTransaction.disabled == 0)
		.orderby(WalletTransaction.creation, order=Order.desc)
		.limit(int(kwargs.get('page_len')))
		.offset(start)
	)

	order_list = order_list_query.run(as_dict=True)

	counterpay_total_count_query = (
		frappe.qb.from_(WalletTransaction)
		.select(fn.IfNull(fn.Count('*'), 0).as_('count'))
		.where(WalletTransaction.docstatus == 1)
		.where(WalletTransaction.party == kwargs.get('user'))
		.where(WalletTransaction.transaction_type == "Pay")
		.where(WalletTransaction.disabled == 0)
		.orderby(WalletTransaction.creation, order=Order.desc)
	)
	counterpay_total_count = counterpay_total_count_query.run(as_dict=True)

	counterpay_order_list_query = (
		frappe.qb.from_(WalletTransaction)
		.select(
			WalletTransaction.name,
			WalletTransaction.transaction_type.as_('reference'),
			WalletTransaction.transaction_date,
			WalletTransaction.total_value,
			WalletTransaction.amount,
			WalletTransaction.status,
			WalletTransaction.notes
		)
		.where(WalletTransaction.docstatus == 1)
		.where(WalletTransaction.party == kwargs.get('user'))
		.where(WalletTransaction.transaction_type == "Pay")
		.where(WalletTransaction.disabled == 0)
		.orderby(WalletTransaction.creation, order=Order.desc)
		.limit(int(kwargs.get('counter_page_len')))
		.offset(start_count)
	)

	counterpay_order_list = counterpay_order_list_query.run(as_dict=True)

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
			WalletTransaction = DocType('Wallet Transaction')
			transaction_query = (
				frappe.qb.from_(WalletTransaction)
				.select(WalletTransaction.order_id)
				.where(WalletTransaction.docstatus == 1)
				.where(WalletTransaction.type == "Business")
				.where(WalletTransaction.reference == "Order")
				.where(WalletTransaction.order_type == "Order")
				.where(WalletTransaction.party == kwargs.get('user'))
				.where(WalletTransaction.transaction_type == "Pay")
				.where(WalletTransaction.disabled == 0)
				.orderby(WalletTransaction.creation, order=Order.desc)
			)
			transaction = transaction_query.run(as_dict=True)
			if transaction:
				order_trans = ", ".join(['"' + i['order_id'] + '"' for i in transaction])
			get_transactions(start_count,start, **kwargs)
		else:
			WalletTransaction = DocType('Wallet Transaction')
			transaction_query = (
				frappe.qb.from_(WalletTransaction)
				.select(WalletTransaction.order_id)
				.where(WalletTransaction.docstatus == 1)
				.where(WalletTransaction.reference == "Order")
				.where(WalletTransaction.order_type == "Order")
				.where(WalletTransaction.type == kwargs.get('user'))
				.where(WalletTransaction.transaction_type == "Pay")
				.where(WalletTransaction.disabled == 0)
				.orderby(WalletTransaction.creation, order=Order.desc)
			)
			transaction = transaction_query.run(as_dict=True)
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


def add_fund_to_wallet(source_name):
	default_currency = get_settings("Catalog Settings")
	if source_name:
		source = frappe.get_all("Wallet",fields = ["*"],filters = {"name":source_name})[0]
	WalletTransaction = DocType('Wallet Transaction')
	transaction_query = (
		frappe.qb.from_(WalletTransaction)
		.select(WalletTransaction.order_id, WalletTransaction.amount, WalletTransaction.total_value, WalletTransaction.name)
		.where(WalletTransaction.is_settlement_paid == 0)
		.where(WalletTransaction.transaction_type == "Receive")
		.where(WalletTransaction.status == "Pending")
		.where(WalletTransaction.party == source.user)
		.orderby(WalletTransaction.creation, order=Order.desc)
	)
	transaction = transaction_query.run(as_dict=True)
	for trans in transaction:
		wallet_entry = frappe.get_doc("Wallet Transaction",trans.name)
		wallet_entry.status="Approved"
		wallet_entry.save(ignore_permissions=True)
	return "success"


def get_if_not_provider(source, vendor):
	for n in source:
		WalletTransaction = DocType('Wallet Transaction')
		to_be_received_query = (
			frappe.qb.from_(WalletTransaction)
			.select(Function('IFNULL', Function('SUM', WalletTransaction.amount), 0).as_('amount'))
			.where(WalletTransaction.party == vendor)
			.where(WalletTransaction.transaction_type == "Receive")
			.where(WalletTransaction.status == "Pending")
		)

		n.to_be_received = to_be_received_query.run(as_dict=True)[0].amount
		claimed_amount_query = (
			frappe.qb.from_(WalletTransaction)
			.select(Function('IFNULL', Function('SUM', WalletTransaction.amount), 0).as_('amount'))
			.where(WalletTransaction.party == vendor)
			.where(WalletTransaction.transaction_type == "Receive")
			.where(WalletTransaction.status == "Approved")
		)

		n.claimed_amount = claimed_amount_query.run(as_dict=True)[0].amount
		total_amount_query = (
			frappe.qb.from_(WalletTransaction)
			.select(Function('IFNULL', Function('SUM', WalletTransaction.amount), 0).as_('amount'))
			.where(WalletTransaction.party == vendor)
			.where(WalletTransaction.transaction_type == "Receive")
		)

		n.total_amount = total_amount_query.run(as_dict=True)[0].amount
	return source


def get_if_provider(source, vendor):
	for n in source:
		WalletTransaction = DocType('Wallet Transaction')
		to_be_received_query = (
			frappe.qb.from_(WalletTransaction)
			.select(Function('IFNULL', Function('SUM', WalletTransaction.amount), 0).as_('amount'))
			.where(WalletTransaction.type == vendor)
			.where(WalletTransaction.transaction_type == "Receive")
			.where(WalletTransaction.status == "Pending")
		)
		n.to_be_received = to_be_received_query.run(as_dict=True)[0].amount

		claimed_amount_query = (
			frappe.qb.from_(WalletTransaction)
			.select(Function('IFNULL', Function('SUM', WalletTransaction.amount), 0).as_('amount'))
			.where(WalletTransaction.type == vendor)
			.where(WalletTransaction.transaction_type == "Receive")
			.where(WalletTransaction.status.isin(["Approved", "Credited"]))
		)
		n.claimed_amount = claimed_amount_query.run(as_dict=True)[0].amount

		total_amount_query = (
			frappe.qb.from_(WalletTransaction)
			.select(Function('IFNULL', Function('SUM', WalletTransaction.amount), 0).as_('amount'))
			.where(WalletTransaction.type == vendor)
			.where(WalletTransaction.transaction_type == "Receive")
		)
		n.total_amount = total_amount_query.run(as_dict=True)[0].amount
	return source

@frappe.whitelist()
def get_counter_apy_counters(vendor):
	if vendor!="Service Provider":
		Wallet = DocType('Wallet')
		source_query = (
			frappe.qb.from_(Wallet)
			.select(Wallet.user_type, Wallet.user, Wallet.name1.as_('user_name'))
			.where(Wallet.user == vendor)
		)
		source = source_query.run(as_dict=True)
		return get_if_not_provider(source, vendor)
	else:
		Wallet = DocType('Wallet')
		source_query = (
			frappe.qb.from_(Wallet)
			.select(Wallet.user_type, Wallet.user, Wallet.name1.as_('user_name'))
			.where(Wallet.user == vendor)
		)
		source = source_query.run(as_dict=True)
		return get_if_provider(source, vendor)

@frappe.whitelist()
def get_wallet_settings():
	return frappe.get_single("Wallet Settings")


def total_counter_graph_options(common_filters = [], ignore_permissions = True, count = 100):
	dash = get_dash_value()
	chart_options={}
	doctype = DocType(dash['reference_doctype'])
	from_date = add_to_date(nowdate(), days=-7)
	to_date = nowdate()
	query = (
		frappe.qb.from_(
			frappe.qb.from_(
				frappe.qb.select(
					Function('DATE_ADD', from_date, Function('INTERVAL', frappe.qb.field('rownum') + 1, 'DAY')).as_('dt')
				)
				.from_(frappe.qb.from_('tab{doctype}'))
				.join(frappe.qb.select(Function('@rownum := -1')).as_('r'))
			).as_('A')
			.left_join(doctype).on(doctype.creation == 'A.dt')
			.select('A.dt')
			.where('A.dt <= %(to_date)s')
			.groupby('A.dt')
		).format(doctype=doctype, from_date=from_date, to_date=to_date)
	)
	label = query.run(as_dict=True)
	labels=[]
	values=[]
	if count>0 and len(label)>0:
		doctype = DocType(dash['reference_doctype'])
		start_date = label[0]
		end_date = label[-1]
		query = (
			frappe.qb.from_(doctype)
			.select('name')
			.where(
				Field('creation').date() >= start_date,
				Field('creation').date() <= end_date
			)
		)
		check_data = query.run(as_dict=True)
		if not check_data:
			doctype = DocType(dash['reference_doctype'])
			latest_date_query = (
				frappe.qb.from_(doctype)
				.select(Field('creation').date())
				.orderby(Field('creation').desc())
				.limit(1)
			)
			lists = latest_date_query.run(as_dict=True)[0].get('creation')

			from_date = add_to_date(latest_date, days=-7)
			to_date = latest_date
			date_range_query = (
				frappe.qb.from_(
					frappe.qb.from_(doctype)
					.select(
						Function('DATE_ADD', from_date, Function('INTERVAL', Function('@rownum := @rownum + 1 DAY'))).as_('dt')
					)
					.join(frappe.qb.from_(doctype).select().limit(1).as_('r'))
				)
				.left_join(doctype)
				.on(Field('creation') == Field('dt'))
				.select('dt')
				.where(Field('dt') <= to_date)
				.groupby('dt')
			)
			label = date_range_query.run(as_dict=True)
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