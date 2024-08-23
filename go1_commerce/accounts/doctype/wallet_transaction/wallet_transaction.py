# -*- coding: utf-8 -*-
# Copyright (c) 2019, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt, nowdate
from frappe.utils import now_datetime
from go1_commerce.utils.setup import get_settings
from frappe.query_builder import DocType, Field, Order

current_date=timestamp = now_datetime().strftime(" %Y-%m-%d %H:%M:%S")


class WalletTransaction(Document):
	def validate(self):
		if self.get('__islocal') and not self.status:
			self.status="Pending"
		if not self.balance_amount:
			self.balance_amount=self.amount
		if (self.party_type and self.party) and not self.party_name:
			selected_field = frappe.db.get_all('Party Name List',
											fields=['party_name_field'],
											filters={'parent':'Party Settings',
													'party_type':self.party_type})
			if selected_field:
				res = frappe.db.get_value(self.party_type,self.party,selected_field[0].party_name_field)
				self.party_name = res
			else:
				self.party_name = ""

	def on_update(self):
		pass

	def on_submit(self):
		if self.status == "Pending":
			if self.type!="Service Provider":
				wallet_name = frappe.db.get_value("Wallet", {
					"user": self.party,
					"user_type": self.party_type
				})
			else:
				wallet_name = frappe.db.get_value("Wallet", {
					"user":self.type
				})
			if not wallet_name:
				create_new_wallet_cod(self)
		if self.status == "Credited":
			update_wallet(self)
			pay=make_recived_payment(self.name,self.transaction_type)
		if self.status == "Debited" and self.transaction_type=="Pay":
			pay=make_recived_payment(self.name,self.transaction_type)
			self.debit_wallet()		
		if self.status == "Locked":	
			update_wallet(self)
	
	def on_update_after_submit(self):
		if self.status == "Pending":
			if self.type!="Service Provider":
				wallet_name = frappe.db.get_value("Wallet", {
					"user": self.party,
					"user_type": self.party_type
				})
			else:
				wallet_name = frappe.db.get_value("Wallet", {
					"user":self.type
				})
			if not wallet_name:
				create_new_wallet_cod(self)
		if self.status == "Credited":
			update_wallet(self)
			pay=make_recived_payment(self.name,self.transaction_type)
		if self.status == "Debited" and self.transaction_type=="Pay":
			pay=make_recived_payment(self.name,self.transaction_type)
			self.debit_wallet()
			
	def debit_wallet(self):
		try:
			wallet_transaction = DocType('Wallet Transaction')
			query_1 = (
				frappe.qb.from_(wallet_transaction)
				.select(wallet_transaction.balance_amount, wallet_transaction.party, wallet_transaction.end_date, wallet_transaction.name)
				.where(wallet_transaction.is_settlement_paid == 0)
				.where(wallet_transaction.balance_amount > 0)
				.where(wallet_transaction.transaction_type == "Pay")
				.where(wallet_transaction.party == self.party)
				.where(wallet_transaction.status == self.status)
				.where(wallet_transaction.end_date.isnotnull())
				.orderby(wallet_transaction.end_date, order=Order.asc)
			)
			query_2 = (
				frappe.qb.from_(wallet_transaction)
				.select(wallet_transaction.balance_amount, wallet_transaction.party, wallet_transaction.end_date, wallet_transaction.name)
				.where(wallet_transaction.is_settlement_paid == 0)
				.where(wallet_transaction.balance_amount > 0)
				.where(wallet_transaction.transaction_type == "Pay")
				.where(wallet_transaction.party == self.party)
				.where(wallet_transaction.status == self.status)
				.where(wallet_transaction.end_date.isnull())
			)
			results_1 = query_1.run(as_dict=True)
			results_2 = query_2.run(as_dict=True)
			wallet_trans = results_1 + results_2
			if len(wallet_trans)>0:
				amt = self.amount
				for trans in wallet_trans:
					if flt(amt)>0:
						if flt(amt) < flt(trans.balance_amount):
							self.update_wallet_detail(amt)
							amt = flt(trans.balance_amount) - flt(amt)
							frappe.db.set_value('Wallet Transaction', trans.name, {
									'balance_amount': flt(amt),
								})
							break
						else:
							self.update_wallet_detail(trans.balance_amount)
							amt = flt(amt) - flt(trans.balance_amount)
							frappe.db.set_value('Wallet Transaction', trans.name, {
									'balance_amount': flt(trans.balance_amount),
									'is_settlement_paid': 1
								})
					else:
						break
		except Exception:
				frappe.log_error(frappe.get_traceback(), 
								"Error in accounts.doctype.wallet_entry.wallet_entry.debit_wallet") 

	def update_wallet_detail(self, amt):
		walletDoc = DocType('Wallet')
		query = (
			frappe.qb.from_(walletDoc)
			.select(walletDoc.total_wallet_amount, walletDoc.current_wallet_amount, walletDoc.name)
			.where(walletDoc.user == self.party)
		)
		wallet = query.run(as_dict=True)

		if len(wallet) > 0:
			total = flt(wallet[0].total_wallet_amount) - flt(amt)
			cur_amt = flt(wallet[0].current_wallet_amount) - flt(amt)
			query = (
				frappe.qb.update(walletDoc)
				.set(walletDoc.total_wallet_amount, total)
				.set(walletDoc.current_wallet_amount, cur_amt)
				.where(walletDoc.user == self.party)
			).run()
			

	def before_cancel(self):
		cancel_payment_entry(self)
		update_walletcancel(self)
		doc = frappe.get_doc("Wallet Transaction",self.name)
		doc.flags.ignore_validate_update_after_submit = True
		doc.status = "Cancelled"
		doc.save()


def update_wallet(self):
	try:
		wallet_setting = frappe.get_single("Wallet Settings")
		if self.type!="Service Provider":
			wallet_name = frappe.db.get_value("Wallet", {
				"user": self.party,
				"user_type": self.party_type
			})
		else:
			wallet_name = frappe.db.get_value("Wallet", {
				"user":self.type
			})
		if wallet_name:
			wallet = frappe.get_doc("Wallet", wallet_name)
			if wallet:
				cur_wallet =locked_in=total_wallet= 0
				if self.status == "Credited":
					if self.transaction_type == "Pay":
						cur_wallet = flt(wallet.current_wallet_amount)+flt(self.amount)
						locked_in = flt(wallet.locked_in_amount)
						total_wallet = flt(cur_wallet)+flt(locked_in)
				if self.status == "Locked":
					if self.transaction_type == "Pay":
						cur_wallet = flt(wallet.current_wallet_amount)
						locked_in = flt(wallet.locked_in_amount)+flt(self.amount)
						total_wallet = flt(cur_wallet)+flt(locked_in)
				if self.status == "Pending":
					if self.transaction_type == "Pay":
						cur_wallet = flt(wallet.current_wallet_amount)
						locked_in = flt(wallet.locked_in_amount)+flt(self.amount)
						total_wallet = flt(cur_wallet)+flt(locked_in)
				wallet_detail=frappe.get_doc('Wallet',wallet.name)
				wallet_detail.current_wallet_amount=cur_wallet
				wallet_detail.locked_in_amount=locked_in
				wallet_detail.total_wallet_amount=total_wallet
				wallet_detail.last_updated=current_date
				wallet_detail.save(ignore_permissions=True)
		else:
			create_new_wallet_entry(self)
	except Exception:
		frappe.log_error(frappe.get_traceback(), 
				"Error in accounts.doctype.wallet_entry.wallet_entry.update_wallet") 



def create_new_wallet_entry(self):
	wal = frappe.new_doc("Wallet")
	wal.last_updated = current_date
	user = None
	if self.party:
		user = frappe.get_doc(self.party_type,self.party)
		if self.type != "Service Provider":
			user = frappe.get_doc(self.party_type,self.party)
			wal.user = self.party	
			wal.user_type=self.party_type
		else:
			wal.user = self.type	
			wal.user_type = self.type
		if self.status == "Credited":
			if self.transaction_type == "Pay":
				wal.current_wallet_amount = self.amount
				wal.total_wallet_amount = self.amount
				wal.locked_in_amount = 0
			else:
				if self.is_settlement_paid == 0 and self.type == "Service Provider":
					wal.current_wallet_amount = flt(self.amount)
					wal.total_wallet_amount = flt(self.amount)
					wal.locked_in_amount = 0
				else:
					wal.current_wallet_amount = -1*flt(self.amount)
					wal.total_wallet_amount = -1*flt(self.amount)
					wal.locked_in_amount=0
		if self.status == "Locked":
			if self.transaction_type == "Pay":
				wal.locked_in_amount = flt(self.amount)
				wal.total_wallet_amount = flt(self.amount)
				wal.current_wallet_amount = 0
		if self.status == "Pending":
			if self.transaction_type == "Pay":
					wal.locked_in_amount = flt(self.amount)
					wal.total_wallet_amount = flt(self.amount)
					wal.current_wallet_amount = 0
			else:
				wal.locked_in_amount = flt(self.amount)
				wal.total_wallet_amount = flt(self.amount)
				wal.current_wallet_amount=0
		if self.party_type == "Drivers":
			wal.name1=user.driver_name
			wal.restaurant_name=""
		if self.party_type == "Service Provider":
			wal.name1=self.type
		if self.party_type == "Customers":
			if user:
				if user.last_name:
					name=user.first_name+''+user.last_name
				else:
					name=user.first_name
				wal.name1=name
		if self.party_type == "Supplier":
			if user.last_name:
				name=user.first_name+''+user.last_name
			else:
				name=user.first_name
			wal.name1=name
		wal.insert(ignore_permissions=True)


def create_new_wallet_cod(self):
	wal = frappe.new_doc("Wallet")
	wal.last_updated = current_date
	user = None
	if self.type != "Service Provider":
		user = frappe.get_doc(self.party_type,self.party)
		wal.user = self.party	
		wal.user_type=self.party_type
	else:
		wal.user = self.type	
		wal.user_type = self.type
	if self.status == "Pending":
		if self.transaction_type == "Receive":
			wal.locked_in_amount = 0
			wal.total_wallet_amount = 0
			wal.current_wallet_amount=0
	if self.party_type == "Drivers":
		wal.mobile_no=user.driver_phone
		wal.name1=user.driver_name
		wal.restaurant_name=""
	if self.party_type == "Service Provider":
		wal.name1=self.type
	if self.party_type == "Customers":
		if user:
			if user.last_name:
				name=user.first_name+''+user.last_name
			else:
				name=user.first_name
			wal.name1=name
	if self.party_type == "Supplier":
		if user.last_name:
			name=user.first_name+''+user.last_name
		else:
			name=user.first_name
		wal.name1=name
	wal.insert(ignore_permissions=True)



def update_walletcancel(self):
	try:
		wallet_setting = frappe.get_single("Wallet Settings")
		if self.type!="Service Provider":
			wallet_name = frappe.db.get_value("Wallet", {
				"user": self.party,
				"user_type": self.party_type
			})
		else:
			wallet_name = frappe.db.get_value("Wallet", {
				"user":self.type
			})
		if wallet_name:
			wallet = frappe.get_doc("Wallet", wallet_name)
			if wallet:
				if self.status == "Credited":
					if self.transaction_type == "Pay":
						cur_wallet = flt(wallet.current_wallet_amount)+(-1*flt(self.amount))
						locked_in = flt(wallet.locked_in_amount)
						total_wallet = flt(cur_wallet)+flt(locked_in)
				if self.status == "Debited":
					if self.transaction_type == "Pay":
						cur_wallet = flt(wallet.current_wallet_amount)+(1*flt(self.amount))
						locked_in = flt(wallet.locked_in_amount)
						total_wallet = flt(cur_wallet)+flt(locked_in)
				if self.status == "Locked":
					if self.transaction_type == "Pay":
						cur_wallet = flt(wallet.current_wallet_amount)
						locked_in = flt(wallet.locked_in_amount)+(-1*flt(self.amount))
						total_wallet = flt(cur_wallet)+flt(locked_in)
				if self.status == "Pending":
					if self.transaction_type == "Pay":
						cur_wallet = flt(wallet.current_wallet_amount)
						locked_in = flt(wallet.locked_in_amount)+(-1*flt(self.amount))
						total_wallet = flt(cur_wallet)+flt(locked_in)
				wallet_detail=frappe.get_doc('Wallet',wallet.name)
				wallet_detail.current_wallet_amount=cur_wallet
				wallet_detail.locked_in_amount=locked_in
				wallet_detail.total_wallet_amount=total_wallet
				wallet_detail.last_updated=current_date
				wallet_detail.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), " Error in wallet.update_walletcancel") 



def cancel_payment_entry(self):
	try:
		payment_entry = DocType('Payment Entry')
		payment_reference = DocType('Payment Reference')
		slt = (
			frappe.qb.from_(payment_reference)
			.inner_join(payment_entry)
			.on(payment_reference.parent == payment_entry.name)
			.select(payment_reference.parent.distinct())
			.where(payment_reference.reference_doctype == 'Wallet Transaction')
			.where(payment_reference.reference_name == self.name)
			.where(payment_entry.payment_type == self.transaction_type)
			.where(payment_entry.docstatus == 1)
			.run(as_dict=True)
		)
		if len(slt)>0:
			for n in slt:
				payment = frappe.get_doc("Payment Entry", n.parent)
				payment.docstatus = 2
				payment.save(ignore_permissions=True)
			return "success"
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in wallet.cancel_payment_entry") 



def update_walletcancels(self):
	try:
		if self.type!="Service Provider":
			wallet_name = frappe.db.get_value("Wallet", {
				"user": self.party,
				"user_type": self.party_type })
		else:
			wallet_name = frappe.db.get_value("Wallet", { "user":self.type })
		if wallet_name:
			wallet = frappe.get_doc("Wallet", wallet_name)
			if wallet:
				if self.status == "Cancelled":
					if self.transaction_type == "Pay":
						cur_wallet = flt(wallet.current_wallet_amount)+ (-1*flt(self.amount))
						locked_in = flt(wallet.locked_in_amount)
						total_wallet = flt(cur_wallet)+flt(locked_in)
					else:
						if self.type == "Service Provider":
							cur_wallet = flt(wallet.current_wallet_amount)+flt(-1*self.amount)
							locked_in = flt(wallet.locked_in_amount)+(flt(self.amount))
							total_wallet = flt(cur_wallet)+flt(locked_in)
						else:
							cur_wallet = flt(wallet.current_wallet_amount)+(flt(self.amount))
							locked_in = flt(wallet.locked_in_amount)
							total_wallet = flt(cur_wallet)+flt(locked_in)
				if self.status == "Locked":
					if self.transaction_type == "Pay":
						cur_wallet =flt(wallet.current_wallet_amount)
						locked_in = flt(wallet.locked_in_amount)+flt(-1*self.amount)
						total_wallet = flt(cur_wallet)+flt(locked_in)
				if self.status == "Pending":
					if self.transaction_type == "Pay":
						cur_wallet = flt(wallet.current_wallet_amount)
						locked_in = flt(wallet.locked_in_amount)+(-1*flt(self.amount))
						total_wallet = flt(cur_wallet)+flt(locked_in)
					else:
						cur_wallet = flt(wallet.current_wallet_amount)
						locked_in = flt(wallet.locked_in_amount)+flt(-1*self.amount)
						total_wallet = flt(cur_wallet)+flt(locked_in)
					
				wallet_detail=frappe.get_doc('Wallet',wallet.name)
				wallet_detail.current_wallet_amount=cur_wallet
				wallet_detail.locked_in_amount=locked_in
				wallet_detail.total_wallet_amount=total_wallet
				wallet_detail.last_updated=current_date
				wallet_detail.save(ignore_permissions=True)
		else:
			wal=frappe.new_doc("Wallet")
			wal.last_updated=current_date
			if self.type!="Service Provider":
				user=frappe.get_doc(self.party_type,self.party)
				wal.user=self.party	
				wal.user_type=self.party_type
			else:
				wal.user=self.type	
				wal.user_type=self.type
			if self.transaction_type == "Pay":
				wal.current_wallet_amount=(-1*flt(self.amount))
				wal.total_wallet_amount=(-1*flt(self.amount))
			else:
				wal.current_wallet_amount=self.amount
				wal.total_wallet_amount=self.amount
			if self.party_type == "Drivers":
				wal.mobile_no=user.driver_phone	
				wal.name1=user.driver_name	
				wal.restaurant_name=""
			if self.party_type == "Service Provider":
				wal.name1=self.type
			if self.party_type == "Customers":
				if user.last_name:
					name=user.first_name+''+user.last_name
				else:
					name=user.first_name
				wal.name1=name
			if self.party_type == "Supplier":
				if user.last_name:
					name=user.first_name+''+user.last_name
				else:
					name=user.first_name
				wal.name1=name
			wal.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), 
								"Error in accounts.doctype.wallet_entry.wallet_entry.update_walletcancel") 


def update_transaction_status(Id,doctype,status):
	trans=frappe.get_doc('Wallet Transaction',Id)
	wallet_transaction = DocType('Wallet Transaction')
	providers = (
		frappe.qb.from_(wallet_transaction)
		.select(wallet_transaction.name)
		.where(wallet_transaction.reference == "Order")
		.where(wallet_transaction.order_type == "Order")
		.where(wallet_transaction.is_settlement_paid == 0)
		.where(wallet_transaction.is_fund_added == 0)
		.where(wallet_transaction.transaction_type == "Receive")
		.where(wallet_transaction.status == "Pending")
		.where(wallet_transaction.type == "Service Provider")
		.where(wallet_transaction.order_id == trans.order_id)
		.run(as_dict=True)
	)
	if providers:
		wallet_update = frappe.get_doc('Wallet Transaction',providers[0].name)
		wallet_update.status = "Credited"
		wallet_update.is_settlement_paid = 1
		wallet_update.is_fund_added = 1
		wallet_update.flags.ignore_permissions = True
		wallet_update.db_update()
	make_recived_payment(Id,"Receive")
	trans = (
		frappe.qb.update(wallet_transaction)
		.set(wallet_transaction.status,'Approved')
		.set(wallet_transaction.is_settlement_paid,1)
		.where(wallet_transaction.name,trans.order_id)
		).run()
	

	return "Success"



def update_docstatus(docid, doctype, status, field=None):

	doc = frappe.get_doc(doctype,docid)
	if not field:
		doc.status = status
	else:
		doc[field] = status
	doc.flags.ignore_validate_update_after_submit = True
	doc.is_settlement_paid = 1
	doc.save()
	return "Success"



def make_recived_payment(source_name,payment_type,reference=None):
	try:
		default_currency=get_settings('Catalog Settings')
		w_sources = frappe.db.get_all("Wallet Transaction",fields=["*"],filters={"name":source_name})
		if w_sources:
			source=w_sources[0]
			if source.type != "Service Provider":
				PaymentEntry = DocType('Payment Entry')
				PaymentReference = DocType('Payment Reference')
				query = (
					frappe.qb.from_(PaymentReference)
					.inner_join(PaymentEntry)
					.on(PaymentReference.parent == PaymentEntry.name)
					.select(PaymentReference.parent)
					.where(PaymentReference.reference_doctype == 'Wallet Transaction')
					.where(PaymentReference.reference_name == source_name)
					.where(PaymentEntry.payment_type == payment_type)
				)
				slt = query.run(as_dict=True)
				if len(slt) == 0:
					total=(flt(source.amount))
					pe = frappe.new_doc("Payment Entry")
					pe.payment_type = payment_type
					pe.posting_date = nowdate()
					pe.mode_of_payment = "Cash"
					pe.party_type = source.party_type
					pe.party = source.party
					pe.party_name = source.party_name
					pe.paid_amount = total
					pe.base_paid_amount = total
					pe.received_amount = total
					pe.allocate_payment_amount = 1
					pe.append("references", {
												'reference_doctype': "Wallet Transaction",
												'reference_name': source.name,
												'bill_no': source.name,
												'due_date': nowdate(),
												'total_amount': total,
												'outstanding_amount': 0,
												'allocated_amount': total
											})
					_paytype = ''
					if payment_type == 'Pay':
						_paytype = 'paid to'
					else:
						_paytype = 'received from'
					pe.remarks = 'Amount {0} {1} {2} {3}'.format(default_currency.default_currency, total, _paytype, source.party)
					pe.flags.ignore_permissions=True
					pe.submit()
					return pe.name
			else:
				PaymentEntry = DocType('Payment Entry')
				PaymentReference = DocType('Payment Reference')
				query = (
					frappe.qb.from_(PaymentEntry)
					.inner_join(PaymentReference)
					.on(PaymentReference.parent == PaymentEntry.name)
					.select(PaymentEntry.name)
					.where(PaymentReference.reference_doctype == 'Wallet Transaction')
					.where(PaymentReference.reference_name == reference_name)
					.where(PaymentEntry.payment_type == 'Pay')
				)
				slt = query.run(as_dict=True)
				if len(slt) == 0:
					total=(flt(source.amount))
					pe = frappe.new_doc("Payment Entry")
					pe.payment_type = "Pay"
					pe.posting_date = nowdate()
					pe.mode_of_payment = "Cash"
					pe.type = source.type
					pe.party_type = source.party_type
					pe.party = source.party
					pe.party_name = source.party_name
					pe.contact_person = ""
					pe.contact_email = ""
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
					pe.remarks = 'Amount {0} {1} paid to {2}'.format(default_currency.default_currency, total, source.party)
					pe.flags.ignore_permissions=True
					pe.submit()
					return pe.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), " Error in wallet.make_autowallet_payment") 