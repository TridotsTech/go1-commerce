# -*- coding: utf-8 -*-
# Copyright (c) 2019, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PartyType(Document):
	pass

@frappe.whitelist()
def get_party_name(party_type,party):
	party_name = "item"
	if party_type == "Business":
		party_name = "restaurant_name"
	if party_type == "Product":
		party_name = "item"
	if party_type == "Offers":
		party_name = "offer_title"
	if party_type == "Customers":
		party_name = "full_name"
	if party_type == "Supplier":
		party_name = "full_name"
	return frappe.db.get_value(party_type,party,party_name)