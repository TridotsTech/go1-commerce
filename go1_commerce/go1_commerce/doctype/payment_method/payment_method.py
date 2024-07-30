# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PaymentMethod(Document):
	def validate(self):
		if not self.display_name:
			self.display_name = self.payment_method
