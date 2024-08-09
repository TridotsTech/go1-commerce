# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals


import frappe
import unittest
import frappe.utils

test_records = frappe.get_test_records('Product Category')

class TestProductCategory(unittest.TestCase):
	def test_category_creation(self):
		business1 = frappe.get_value("Business", {"restaurant_name": "Test Business 1", "contact_email":"test_business_1@test.com"}, "name")
		business2 = frappe.get_value("Business", {"restaurant_name": "Test Business 2", "contact_email":"test_business_2@test.com"}, "name")
		cat1 = make_product_category("Test Product Category 1")
		cat2 = make_product_category("Test Product Category 2")
		cat1_doc = frappe.get_doc("Product Category", cat1).reload()
		cat2_doc = frappe.get_doc("Product Category", cat2).reload()
		
		

def make_product_category(category_namee):
	if not frappe.db.get_value("Product Category", { "category_name": category_name}):
		cat = frappe.get_doc({
			"doctype": "Product Category",
			"category_name": category_name,
			"meta_title": category_name,
			"meta_keywords": category_name,
			"meta_description": category_name,
			"display_order":1
		}).insert()
		return cat.name
	else:
		return frappe.get_value("Product Category", { "category_name": category_name}, "name")
