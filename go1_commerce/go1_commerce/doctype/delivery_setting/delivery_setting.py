# -*- coding: utf-8 -*-
# Copyright (c) 2021, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType

class DeliverySetting(Document):
	pass

def check_category_exist_or_not():
	category = []
	DeliverySlotCategory = DocType('Delivery Slot Category')
	query = (
	    frappe.qb.from_(DeliverySlotCategory)
	    .select(DeliverySlotCategory.category)
	    .where(
	        (DeliverySlotCategory.parenttype == "Delivery Setting") &
	        (DeliverySlotCategory.parentfield == "delivery_slot_category")
	    )
	)
	is_exist = query.run(as_dict=True)
	if is_exist:
		for x in is_exist:
			category.append(x.category)
	return category