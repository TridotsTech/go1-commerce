# -*- coding: utf-8 -*-
# Copyright (c) 2021, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class DeliverySetting(Document):
	pass

def check_category_exist_or_not():
	category = []
	is_exist = frappe.db.sql('''SELECT category 
								FROM `tabDelivery Slot Category` 
								WHERE parenttype = "Delivery Setting" 
									AND parentfield = "delivery_slot_category" ''', as_dict = 1)
	if is_exist:
		for x in is_exist:
			category.append(x.category)
	return category