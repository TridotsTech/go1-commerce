# -*- coding: utf-8 -*-
# Copyright (c) 2020, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document

class CheckoutAttributes(Document):
	pass
@frappe.whitelist()
def get_options(attribute):
	return frappe.db.sql('''SELECT option_value 
							FROM 
								`tabCheckout Attributes Options` 
							WHERE parent = %(parent)s 
							ORDER BY display_order''', {'parent': attribute})
