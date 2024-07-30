# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class CartItems(Document):
	def on_update(self):	
		parent=frappe.get_doc(self.parenttype,self.parent)
		parent.save(ignore_permissions=True)
	
	def after_delete(self):
		parent=frappe.get_doc(self.parenttype,self.parent)
		parent.save(ignore_permissions=True)
	