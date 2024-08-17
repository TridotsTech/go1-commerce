# -*- coding: utf-8 -*-
# Copyright (c) 2019, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt
from frappe.query_builder import DocType

class PaymentEntry(Document):
	def validate(self):
		if self.paid_amount and len(self.get("references")) == 1:
			for d in self.get("references"):
				if not flt(self.paid_amount) >= flt(d.total_amount):
					frappe.throw("Amount is greater than allocated total amount!")
				remain = flt(d.total_amount) - flt(self.paid_amount)
				d.outstanding_amount = remain
				d.allocated_amount = self.paid_amount
				if d.reference_doctype == 'Order':
					outstanding = frappe.db.get_value('Order', d.reference_name, 'outstanding_amount')
					if flt(outstanding) < flt(d.allocated_amount) and self.payment_type =="Receive":
						frappe.throw(frappe._('Amount is greater than the outstanding amount'))

	def on_update(self):
		if self.party_type and self.party:
			selected_field = frappe.db.get_all('Party Name List',
									fields=['party_name_field'],
									filters={'parent':'Party Settings','party_type':self.party_type})
			if selected_field:
				res = frappe.db.get_value(self.party_type,self.party,selected_field[0].party_name_field)
				self.party_name = res

	def update_receive_payment_status_and_outstanding(self,d):
		payment = frappe.get_doc(d.reference_doctype, d.reference_name)
		payment.outstanding_amount = d.outstanding_amount
		if d.reference_doctype == "Sales Invoice":
			if flt(d.total_amount) == flt(d.allocated_amount):
				from go1_commerce.accounts.api import update_docstatus
				update_docstatus(d.reference_doctype, d.reference_name, "status","Paid",
									paid_amount = self.paid_amount)
		payment_status = frappe.db.get_value("DocField", {"parent": d.reference_doctype,
															"fieldname": "payment_status"})
		if flt(d.total_amount) == flt(d.allocated_amount) and payment_status:
			payment.payment_status = "Paid"
		else:
			if frappe.db.get_value("DocField", {"parent": d.reference_doctype,
												"fieldname": "payment_status"}):
				payment.payment_status = "Partially Paid"
		try:
			payment.save(ignore_permissions=True)
			frappe.db.commit()
		except Exception:
			if d.reference_doctype == "Order":
				Order = DocType('Order')
				query = (
					frappe.qb.update(Order)
					.set(Order.outstanding_amount, d.outstanding_amount)
					.set(Order.payment_status, payment.payment_status)
					.where(Order.name == d.reference_name)
				).run()
				frappe.db.commit()

	def update_pay_payment_status_and_outstanding(self,d):
		# if frappe.db.get_value("Purchase Invoice",d.reference_name,"name"):
		#     frappe.db.set_value("Purchase Invoice",d.reference_name,"outstanding_amount",d.outstanding_amount)
		if d.reference_doctype == 'Order':
			if flt(d.outstanding_amount) == flt(0):
				amount = 0
				frappe.log_error("DDD11",d.outstanding_amount)
			else:
				amount = d.outstanding_amount * -1
			payment = frappe.get_doc(d.reference_doctype, d.reference_name)
			payment.outstanding_amount = amount
			if flt(d.total_amount) == flt(d.allocated_amount):
				payment.payment_status = "Refunded"
			else:
				payment.payment_status = "Partially Refunded"
			try:
				payment.save(ignore_permissions=True)

			except Exception:
				frappe.log_error("4")
				frappe.log_error(frappe.get_traceback(), "accounts.payment_entry.on_submit")
				if d.reference_doctype == "Order":
					Order = DocType("Order")
					query = (
						frappe.qb.update(Order)
						.set(Order.outstanding_amount, d.outstanding_amount)
						.set(Order.payment_status, payment.payment_status)
						.where(Order.name==d.reference_name)
					).run()
					
			frappe.db.commit()


	def on_submit(self):
		if self.paid_amount:
			for d in self.get("references"):
				if self.payment_type == "Receive":
					if d.reference_doctype == "Wallet Transaction":
						is_settlement_paid = frappe.db.get_value(d.reference_doctype,d.reference_name,"is_settlement_paid")
					if d.reference_doctype == "Wallet Transaction" and is_settlement_paid == 0:
						frappe.db.set_value(d.reference_doctype,d.reference_name,"is_settlement_paid",1)
						frappe.db.commit()
					self.update_receive_payment_status_and_outstanding(d)
				elif self.payment_type == "Pay":
					self.update_pay_payment_status_and_outstanding(d)
				slt = []
				if self.payment_type:
					PaymentEntry = DocType('Payment Entry')
					PaymentReference = DocType('Payment Reference')
					query = (
						frappe.qb.from_(PaymentEntry)
						.inner_join(PaymentReference)
						.on(PaymentEntry.name == PaymentReference.parent)
						.select(PaymentReference.allocated_amount)
						.where(PaymentReference.reference_name == d.reference_name)
						.where(PaymentEntry.payment_type == self.payment_type)
						.where(PaymentEntry.party == self.party)
						.where(PaymentReference.reference_doctype == d.reference_doctype)
						.where(PaymentEntry.docstatus == 1)
						.where(PaymentEntry.name != self.name)
					)
					slt = query.run(as_dict=True)
				total = (d.allocated_amount or 0)
				for refs in slt:
					if refs["allocated_amount"]:
						total += flt(refs["allocated_amount"])
				
				if self.payment_type == "Receive":
					if d.reference_doctype != 'Membership Payment':
						frappe.db.set_value(d.reference_doctype,d.reference_name,"paid_amount",total)
					else:
						frappe.db.set_value(d.reference_doctype, d.reference_name, 'paid', 1)
				elif self.payment_type =="Pay":
					validate_payment_type(d, total)

	def on_cancel(self):
		if self.paid_amount:
			for d in self.get("references"):
				if self.payment_type == "Receive" and d.reference_doctype not in ["Wallet Transaction", "Membership Payment"]:
					outstand_before = frappe.db.get_value(d.reference_doctype,d.reference_name,"outstanding_amount")
					paid_before = frappe.db.get_value(d.reference_doctype,d.reference_name,"paid_amount")
					outstand_after = flt(outstand_before)+flt(self.paid_amount)
					paid_after = flt(paid_before) - flt(self.paid_amount)
					frappe.db.set_value(d.reference_doctype,d.reference_name,"outstanding_amount",outstand_after)
					frappe.db.set_value(d.reference_doctype,d.reference_name,"paid_amount",paid_after)
					frappe.db.commit()
					
					if paid_after == 0:
						frappe.db.set_value(d.reference_doctype, d.reference_name, 'payment_status', 'Pending')
					else:
						frappe.db.set_value(d.reference_doctype, d.reference_name, 'payment_status', 'Partially Paid')
						
				if self.payment_type == "Pay" and d.reference_doctype == "Purchase Invoice":
					outstand_before = frappe.db.get_value("Purchase Invoice",d.reference_name,"outstanding_amount")
					paid_before = frappe.db.get_value("Purchase Invoice",d.reference_name,"paid_amount")
					outstand_after = flt(outstand_before) + flt(self.paid_amount)
					paid_after = flt(paid_before) - flt(self.paid_amount)
					frappe.db.set_value("Purchase Invoice",d.reference_name,"outstanding_amount",outstand_after)
					frappe.db.set_value("Purchase Invoice",d.reference_name,"paid_amount",paid_after)
					frappe.db.commit()
					
				if self.payment_type == 'Pay' and d.reference_doctype == 'Expense Entry':
					if d.total_amount == d.allocated_amount:
						frappe.db.set_value(d.reference_doctype, d.reference_name, 'outstanding_amount', d.allocated_amount)
					else:
						outstanding = frappe.db.get_value(d.reference_doctype, d.reference_name, 'outstanding_amount')
						outstanding = outstanding + d.allocated_amount
						frappe.db.set_value(d.reference_doctype, d.reference_name, 'outstanding_amount', outstanding)
					frappe.db.commit()
					
				if self.payment_type == 'Receive' and d.reference_doctype == 'Membership Payment':
					frappe.db.set_value(d.reference_doctype, d.reference_name, 'paid', 0)
					frappe.db.commit()

def validate_payment_type(d, total):
	if d.reference_doctype == "Purchase Invoice":
		frappe.db.set_value("Purchase Invoice",d.reference_name,"paid_amount",total)
		paid = frappe.db.get_value("Purchase Invoice",d.reference_name,"paid_amount")
		grand = frappe.db.get_value("Purchase Invoice",d.reference_name,"grand_total")
		frappe.db.commit()
		if flt(paid) == flt(grand):
			frappe.db.set_value("Purchase Invoice",d.reference_name,"status","Paid")
		else:
			frappe.db.set_value("Purchase Invoice",d.reference_name,"status","Partially Paid")
		frappe.db.commit()
	if d.reference_doctype == "Invoice":
		frappe.db.set_value("Invoice",d.reference_name,"paid_amount",total)
		paid = frappe.db.get_value("Invoice",d.reference_name,"paid_amount")
		grand = frappe.db.get_value("Invoice",d.reference_name,"grand_total")
		if flt(paid) == flt(grand):
			frappe.db.set_value("Invoice",d.reference_name,"status","Paid")
		frappe.db.commit()
	if d.reference_doctype == 'Expense Entry':
		outstanding = 0
		if d.allocated_amount == d.total_amount:
			outstanding = 0
		else:
			outstanding = d.total_amount - d.allocated_amount
		frappe.db.set_value(d.reference_doctype, d.reference_name, 'outstanding_amount', outstanding)
		frappe.db.commit()
	if d.reference_doctype == 'Order':
		outstanding = 0
		if d.allocated_amount == d.total_amount:
			outstanding = 0
		else:
			outstanding = d.total_amount - d.allocated_amount
		frappe.db.set_value(d.reference_doctype, d.reference_name, 'outstanding_amount', outstanding)
		# frappe.db.set_value("Invoice",d.reference_name,"payment_status","Paid")
		frappe.db.commit()
		if d.reference_doctype == "Order":
			from go1_commerce.go1_commerce.\
				doctype.order.order import update_order_shipment_payment
			update_order_shipment_payment(d.reference_name)



def get_reference_details(reference_doctype, reference_name, party_account_currency):
	total_amount = outstanding_amount = exchange_rate = None
	ref_doc = frappe.get_doc(reference_doctype, reference_name)
	company_currency = "USD"
	if reference_doctype == "Invoice":
		if party_account_currency == company_currency:
			if ref_doc.doctype == "Expense Claim":
				total_amount = ref_doc.total_sanctioned_amount
			elif ref_doc.doctype == "Employee Advance":
				total_amount = ref_doc.advance_amount
			else:
				total_amount = ref_doc.base_grand_total
			exchange_rate = 1
		else:
			total_amount = ref_doc.grand_total
			exchange_rate = 1
		if reference_doctype in ("Invoice"):
			outstanding_amount = ref_doc.get("outstanding_amount")
		else:
			outstanding_amount = flt(total_amount) - flt(ref_doc.advance_paid)
	return frappe._dict({"due_date": ref_doc.get("due_date"),
						"total_amount": total_amount,
						"outstanding_amount": outstanding_amount,
						"exchange_rate": exchange_rate})