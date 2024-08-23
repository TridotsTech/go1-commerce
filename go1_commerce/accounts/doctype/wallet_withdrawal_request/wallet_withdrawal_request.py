# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt, nowdate
from frappe.utils import flt, nowdate, now
from go1_commerce.utils.setup import get_settings_value
from frappe.query_builder import DocType, Field

class WalletWithdrawalRequest(Document):
	def validate(self):
		order = frappe.get_all("Wallet",fields=['*'],filters={"user":self.party})
		if len(order)>0:
			if flt(order[0].current_wallet_amount) < flt(self.withdraw_amount):
				frappe.throw(frappe._("Requested Amount ({0}) is greater than Current Wallet Amount ({1}).").format(self.withdraw_amount,order[0].current_wallet_amount))
			request = frappe.get_all("Wallet Withdrawal Request",fields=['*'],filters={"party":self.party,'status':"Pending",'docstatus':1,'name':('!=',self.name)} )
			if len(request)>0:
				frappe.throw(frappe._("Can't create the request."))
		else:
			frappe.throw(frappe._("Requested Amount is greater than Current Wallet Amount."))

	def on_update_after_submit(self):
		if self.withdrawal_type == "Self" and self.status == "Approved":
			make_wallet_transaction(self.name)

	def on_submit(self):
		if self.withdrawal_type == "Auto Withdraw" and self.status == "Approved":
			make_wallet_transaction(self.name)
		

@frappe.whitelist()
def update_requested_status(id,doctype,status):
	trans = frappe.get_doc('Wallet Withdrawal Request',id)
	trans.status = status
	trans.save(ignore_permissions=True)
	return "Success"	
		


def make_wallet_transaction(source_name):
	try:
		if source_name:
			source = frappe.get_all("Wallet Withdrawal Request",fields=["*"],
									filters={"name":source_name},ignore_permissions=True)[0]
		trans_ref=transacrtion_reference(source)
		trans_ref = "Against Order: "+trans_ref
		wallet_trans_entry = frappe.get_doc({"doctype":"Wallet Transaction",
											"reference":"Order",
											"order_type":"Order",
											"order_id":"",
											"transaction_date":now(),
											"total_value":source.withdraw_amount,
											"amount":source.withdraw_amount,
											"is_settlement_paid":0,
											"is_fund_added":1 })
		if trans_ref:
			wallet_trans_entry.notes = trans_ref
		if source.reference_doc:
			wallet_trans_entry.order_id =  source.reference_doc
		wallet_trans_entry.type = source.party_type
		wallet_trans_entry.party_type = source.party_type
		wallet_trans_entry.party = source.party
		wallet_trans_entry.party_name = source.party_name
		wallet_trans_entry.transaction_type = "Pay"
		wallet_trans_entry.status = "Debited"
		wallet_trans_entry.flags.ignore_permissions = True
		wallet_trans_entry.submit()
		frappe.db.set_value("Wallet Withdrawal Request",source_name,"status","Paid")
		frappe.db.set_value("Wallet Withdrawal Request",source_name,"outstanding_amount",0)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "wallet.make_wallet_transaction") 
	

def get_payment_entry(default_currency,source,total):
	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Pay"
	pe.posting_date = nowdate()
	pe.mode_of_payment = "Cash"
	pe.party_type = source.party_type
	pe.party = source.party
	pe.party_name = source.party_name
	pe.contact_person = ""
	pe.contact_email = ""
	# pe.paid_from = account_settings.paid_from_account
	# pe.paid_to = account_settings.paid_to_account
	pe.paid_from_account_currency = default_currency
	pe.paid_to_account_currency = default_currency
	pe.paid_amount = total
	pe.base_paid_amount = total
	pe.received_amount = total
	pe.allocate_payment_amount = 1
	pe.append("references", {
		'reference_doctype': "Wallet Transaction",
		'reference_name': source.name,
		"bill_no": "",
		"due_date": "",
		'total_amount': total,
		'outstanding_amount': 0,
		'allocated_amount': total
	})
	pe.flags.ignore_permissions=True
	pe.submit()


def make_autowallet_payment(source_name):
	try:
		default_currency = get_settings_value("Catalog Settings","default_currency")
		source=frappe.get_all("Wallet Transaction",fields=["*"],filters={"name":source_name})[0]
		if flt(source.outstanding_amount)>0:
			total=source.outstanding_amount
		else:	
			total=source.withdraw_amount
		get_payment_entry(default_currency,total, source)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "wallet.make_autowallet_payment") 

	
def transacrtion_reference(source):
	try:
		tran = ""
		WalletTransaction = DocType('Wallet Transaction')
		query = (
			frappe.qb.from_(WalletTransaction)
			.select(
				WalletTransaction.balance_amount,
				WalletTransaction.party,
				WalletTransaction.name,
				WalletTransaction.reference,
				WalletTransaction.order_type,
				WalletTransaction.order_id
			)
			.where(WalletTransaction.is_settlement_paid == 0)
			.where(WalletTransaction.balance_amount > 0)
			.where(WalletTransaction.transaction_type == 'Pay')
			.where(WalletTransaction.party == source.party)
		)
		wallet_trans = query.run(as_dict=True)
		if len(wallet_trans)>0:
			amt = source.withdraw_amount
			for trans in wallet_trans:
				if flt(amt)>0:
					if flt(amt) <= flt(trans.balance_amount):
						if tran:
							tran +=","+trans.name
							if trans.reference and trans.order_id:
								tran +="("+trans.reference+":"+trans.order_id+")"
						else:
							tran +=trans.name
							if trans.reference and trans.order_id:
								tran +="("+trans.reference+":"+trans.order_id+")"
						break
					else:
						tran +=","+trans.name
						if trans.reference and trans.order_id:
							tran +="("+trans.reference+":"+trans.order_id+")"
				else:
					break
		return tran
	except Exception:
		frappe.log_error(frappe.get_traceback(), "wallet.transacrtion_reference") 


def make_wallet_payment(source_name, target_doc=None):
	try:
		default_currency=get_settings_value("Catalog Settings","default_currency")
		source=frappe.db.get_list("Wallet Transaction",fields=["*"],filters={"name":source_name})[0]
		if flt(source.outstanding_amount)>0:
			total=source.outstanding_amount
		else:	
			total=source.withdraw_amount
		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Pay"
		pe.posting_date = nowdate()
		pe.mode_of_payment = "Cash"
		pe.party_type = source.party_type
		pe.party = source.party
		pe.party_name = source.party_name
		pe.contact_person = ""
		pe.contact_email = ""
		# pe.paid_from = paid_from_account
		# pe.paid_to = paid_to_account
		pe.paid_from_account_currency = default_currency
		pe.paid_to_account_currency = default_currency
		pe.paid_amount = total
		pe.base_paid_amount = total
		pe.received_amount = total
		pe.allocate_payment_amount = 1
		pe.append("references", {'reference_doctype': "Wallet Transaction",
								'reference_name': source.name,
								"bill_no": "",
								"due_date": "",
								'total_amount': total,
								'outstanding_amount': 0,
								'allocated_amount': total })
		return pe
	except Exception:
		frappe.log_error(frappe.get_traceback(), "wallet.make_withdraw_request") 