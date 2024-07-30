# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals


import frappe
import unittest
import frappe.utils

test_records = frappe.get_test_records('Product Attribute')
test_dependencies = ["Business"]
class TestProductCategory(unittest.TestCase):
	def test_attribute_creation(self):
		if not frappe.db.get_value("Product Attribute",{"attribute_name":"Test Product Attribute 1"}):
			print("---------dir")
			make_attributes()
		
def make_attributes():
	print("---------direct")
	business1 = frappe.get_value("Business", {"restaurant_name": "Test Business 1", "contact_email":"test_business_1@test.com"}, "name")
	business2 = frappe.get_value("Business", {"restaurant_name": "Test Business 2", "contact_email":"test_business_2@test.com"}, "name")
	attr1 = make_attribute("Test Product Attribute 1", business1)
	attr2 = make_attribute("Test Product Attribute 2", business2)
	attr1_doc = frappe.get_doc("Product Attribute", attr1).reload()
	attr2_doc = frappe.get_doc("Product Attribute", attr2).reload()		

def make_attribute(attr_name, business=None):
	if not frappe.db.get_value("Product Attribute", { "attribute_name": attr_name, "business":business}):
		attr = frappe.get_doc({
			"doctype": "Product Attribute",
			"attribute_name": attr_name,
			"business": business,
			"business_name":""
		}).insert()
		return attr.name
	else:
		return frappe.get_value("Product Attribute", { "attribute_name": attr_name, "business":business}, "name")
