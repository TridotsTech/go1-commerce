# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

class TestPaymentMethod(unittest.TestCase):
	def test_payment_creation(self):
		business1 = frappe.get_value("Business", {"restaurant_name": "Test Business 1", "contact_email":"test_business_1@test.com"}, "name")
		business2 = frappe.get_value("Business", {"restaurant_name": "Test Business 2", "contact_email":"test_business_2@test.com"}, "name")
		pay1 = make_payment_method("Test Payment Method 1")
		pay2 = make_payment_method("Test Payment Method 2")
		pay1_doc = frappe.get_doc("Payment Method", pay1).reload()
		pay2_doc = frappe.get_doc("Payment Method", pay2).reload()
		
		

def make_payment_method(payment_method):
	if not frappe.db.get_value("Payment Method", { "payment_method": payment_method}):
		pay = frappe.get_doc({
			"doctype": "Payment Method",
			"payment_method": payment_method,
			"display_order": 1,
			"enable": 1
		}).insert()
		return pay.name
	else:
		return frappe.get_value("Payment Method", { "payment_method": payment_method}, "name")

