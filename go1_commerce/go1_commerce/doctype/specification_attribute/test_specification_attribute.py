# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

test_records = frappe.get_test_records('Specification Attribute')

class TestSpecificationAttribute(unittest.TestCase):
	def test_attribute_creation(self):
		business1 = frappe.get_value("Business", {"restaurant_name": "Test Business 1", "contact_email":"test_business_1@test.com"}, "name")
		business2 = frappe.get_value("Business", {"restaurant_name": "Test Business 2", "contact_email":"test_business_2@test.com"}, "name")
		specification = make_specification("Test Specification Attribute 1")
		specification1 = make_specification("Test Specification Attribute 2")
		specification_doc = frappe.get_doc("Specification Attribute", specification).reload()
		specification1_doc = frappe.get_doc("Specification Attribute", specification1).reload()
		
		

def make_specification(name):
	if not frappe.db.get_value("Specification Attribute", { "attribute_name": name}):
		specification = frappe.get_doc({
			"doctype": "Specification Attribute",
			"attribute_name": name,
			"display_order": 1
		}).insert()
		return specification.name
	else:
		return frappe.get_value("Specification Attribute", { "attribute_name": name}, "name")

