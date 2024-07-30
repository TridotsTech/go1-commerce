# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals


import frappe
import unittest
import frappe.utils

test_records = frappe.get_test_records('Shipping Method')

class TestShippingMethod(unittest.TestCase):
	def test_shipping_creation(self):
		business1 = frappe.get_value("Business", {"restaurant_name": "Test Business 1", "contact_email":"test_business_1@test.com"}, "name")
		business2 = frappe.get_value("Business", {"restaurant_name": "Test Business 2", "contact_email":"test_business_2@test.com"}, "name")
		ship1 = make_shipping_method("Test Shipping Method 1", business1)
		ship2 = make_shipping_method("Test Shipping Method 2", business2)
		ship1_doc = frappe.get_doc("Shipping Method", ship1).reload()
		ship2_doc = frappe.get_doc("Shipping Method", ship2).reload()
		
		

def make_shipping_method(shipping_method_name, business=None):
	if not frappe.db.get_value("Shipping Method", { "shipping_method_name": shipping_method_name, "business":business}):
		ship = frappe.get_doc({
			"doctype": "Shipping Method",
			"shipping_method_name": shipping_method_name,
			"display_order": 1,
			"show_in_website": 1,
			"business": business,
			"business_name":""
		}).insert()
		return ship.name
	else:
		return frappe.get_value("Shipping Method", { "shipping_method_name": shipping_method_name, "business":business}, "name")
