# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals


import frappe
import unittest
import frappe.utils

test_records = frappe.get_test_records('Product Brand')

class TestProductBrand(unittest.TestCase):
	def test_brand_creation(self):
		business1 = frappe.get_value("Business", {"restaurant_name": "Test Business 1", "contact_email":"test_business_1@test.com"}, "name")
		business2 = frappe.get_value("Business", {"restaurant_name": "Test Business 2", "contact_email":"test_business_2@test.com"}, "name")
		brand = make_product_brand("Test Product Brand 1", business1)
		brand1 = make_product_brand("Test Product Brand 2", business2)
		brand_doc = frappe.get_doc("Product Brand", brand).reload()
		brand1_doc = frappe.get_doc("Product Brand", brand1).reload()
		
		

def make_product_brand(brand_name, business=None):
	if not frappe.db.get_value("Product Brand", { "brand_name": brand_name, "business":business}):
		brand = frappe.get_doc({
			"doctype": "Product Brand",
			"brand_name": brand_name,
			"published":1,
			"business": business,
			"business_name":""
		}).insert()
		return brand.name
	else:
		return frappe.get_value("Product Brand", { "brand_name": brand_name, "business":business}, "name")
