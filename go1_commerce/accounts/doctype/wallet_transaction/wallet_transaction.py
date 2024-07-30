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
			pay=make_recived_payment(self,self.transaction_type)
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
			pay=make_recived_payment(self,self.transaction_type)
		if self.status == "Debited" and self.transaction_type=="Pay":
			pay=make_recived_payment(self.name,self.transaction_type)
			self.debit_wallet()
			
	def debit_wallet(self):
		try:
			wallet_trans = frappe.db.sql('''(SELECT balance_amount, party, end_date, name 
											FROM `tabWallet Transaction` 
											WHERE is_settlement_paid = 0 
												AND balance_amount > 0 
												AND transaction_type = "Pay" 
												AND party = %(party)s 
												AND status = %(status)s 
												AND end_date IS NOT NULL 
											ORDER BY end_date ASC) 
											UNION 
											(SELECT balance_amount, party, end_date, name 
											FROM `tabWallet Transaction` 
											WHERE is_settlement_paid = 0 
												AND balance_amount > 0 
												AND transaction_type = "Pay" 
												AND party = %(party)s 
												AND status = %(status)s 
												AND end_date IS NULL)
										''', {'party': self.party, 'status': self.status}, as_dict=True)
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
		wallet = frappe.db.sql('''	SELECT total_wallet_amount, current_wallet_amount, name 
									FROM `tabWallet` 
									WHERE user = %s
								''', self.party, as_dict=True)

		if len(wallet) > 0:
			total = flt(wallet[0].total_wallet_amount) - flt(amt)
			cur_amt = flt(wallet[0].current_wallet_amount) - flt(amt)
			frappe.db.sql('''UPDATE `tabWallet` 
							SET total_wallet_amount = %s, 
								current_wallet_amount = %s 
							WHERE user = %s
						''', (total, cur_amt, self.party))

	def before_cancel(self):
		cancel_payment_entry(self)
		update_walletcancel(self)
		doc = frappe.get_doc("Wallet Transaction",self.name)
		doc.flags.ignore_validate_update_after_submit = True
		doc.status = "Cancelled"
		doc.save()

@frappe.whitelist(allow_guest=True)
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


@frappe.whitelist(allow_guest=True)
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

@frappe.whitelist(allow_guest=True)
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


@frappe.whitelist(allow_guest=True)
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


@frappe.whitelist(allow_guest=True)
def cancel_payment_entry(self):
	try:
		slt = frappe.db.sql(""" SELECT DISTINCT R.parent 
								FROM `tabPayment Entry` P, `tabPayment Reference` R
								WHERE R.parent = p.name 
									AND R.reference_doctype = 'Wallet Transaction' 
									AND R.reference_name = %s 
									AND P.payment_type = %s 
									AND P.docstatus = 1
							""", (self.name, self.transaction_type), as_dict=True)
		if len(slt)>0:
			for n in slt:
				payment = frappe.get_doc("Payment Entry", n.parent)
				payment.docstatus = 2
				payment.save(ignore_permissions=True)
			return "success"
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in wallet.cancel_payment_entry") 


@frappe.whitelist(allow_guest=True)
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

@frappe.whitelist(allow_guest=True)
def update_transaction_status(id,doctype,status):
	trans=frappe.get_doc('Wallet Transaction',id)
	providers = frappe.db.sql('''SELECT name 
								FROM `tabWallet Transaction` 
								WHERE reference = "Order" 
									AND order_type = "Order" 
									AND is_settlement_paid = 0 
									AND is_fund_added = 0 
									AND transaction_type = "Receive" 
									AND status = "Pending" 
									AND type = %s 
									AND order_id = %s
							''', ("Service Provider", trans.order_id), as_dict=True)
	if providers:
		wallet_update = frappe.get_doc('Wallet Transaction',providers[0].name)
		wallet_update.status = "Credited"
		wallet_update.is_settlement_paid = 1
		wallet_update.is_fund_added = 1
		wallet_update.flags.ignore_permissions = True
		wallet_update.db_update()
	make_recived_payment(id,"Receive")
	frappe.db.sql(	'''	UPDATE `tabWallet Transaction` 
						SET status = 'Approved', 
							is_settlement_paid = 1 
						WHERE name = %(id)s
					''', {"id": id})

	return "Success"


@frappe.whitelist(allow_guest=True)
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


@frappe.whitelist(allow_guest=True)
def make_recived_payment(source_name,payment_type,reference=None):
	try:
		frappe.log_error("SO NA",source_name.name)
		default_currency=get_settings('Catalog Settings')
		w_sources = frappe.db.get_all("Wallet Transaction",fields=["*"],filters={"name":source_name.name})
		if w_sources:
			source=w_sources[0]
			if source.type != "Service Provider":
				slt = frappe.db.sql(""" SELECT R.parent 
										FROM `tabPayment Entry` P 
										JOIN `tabPayment Reference` R ON R.parent = P.name 
										WHERE R.reference_doctype = 'Wallet Transaction' 
											AND R.reference_name = %s 
											AND P.payment_type = %s
									""", (source.name, payment_type), as_dict=True)
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
				slt = frappe.db.sql(""" SELECT p.name 
										FROM `tabPayment Entry` p 
										JOIN `tabPayment Reference` r ON r.parent = p.name 
										WHERE r.reference_doctype = 'Wallet Transaction' 
											AND r.reference_name = %s 
											AND p.payment_type = 'Pay'
									""", (source.name,), as_dict=True)
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