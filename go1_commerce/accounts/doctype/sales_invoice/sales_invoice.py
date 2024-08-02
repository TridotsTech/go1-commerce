# -*- coding: utf-8 -*-
# Copyright (c) 2020, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from go1_commerce.utils.setup import get_settings_value, get_settings

class SalesInvoice(Document):
	def autoname(self): 
		naming_series='INV-.YYYY.-'
		self.naming_series=naming_series
		from frappe.model.naming import make_autoname
		self.name = make_autoname(naming_series+'.#####', doc=self)

	def on_submit(self):
		from go1_commerce.accounts.api import make_invoice_payment
		if frappe.db.exists("Order", self.reference):
			doc = frappe.get_doc("Order", self.reference)
		if doc.payment_status=="Paid":
			order_settings = get_settings('Order Settings')
			if order_settings.automate_invoice_creation==1:
				make_invoice_payment(source_name=None, source=self.name)

	def on_update_after_submit(self):
		if self.reference and self.status=="Paid":
			if frappe.db.exists("Order", self.reference):
				doc = frappe.get_doc("Order", self.reference)
				doc.payment_status = "Paid"
				outstanding_amount = self.total_amount - self.paid_amount
				doc.paid_amount = self.paid_amount
				self.outstanding_amount = outstanding_amount
				doc.db_update()
				frappe.db.sql('''UPDATE `tabOrder` SET outstanding_amount = %(outstanding_amount)s , 
							  payment_status= %(payment_status)s WHERE name = %(doc_name)s''',
							  {"payment_status":"Paid", "doc_name":self.reference, "outstanding_amount": outstanding_amount})
				frappe.db.commit()
				res = frappe.db.sql(f"""SELECT * FROM `tabOrder` WHERE name = ''{self.reference}""")