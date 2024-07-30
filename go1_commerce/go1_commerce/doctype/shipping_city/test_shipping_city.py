# -*- coding: utf-8 -*-
# Copyright (c) 2020, Tridots Tech and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

class TestShippingCity(unittest.TestCase):
	def test_shipping_city_creation(self):
		make_shipping_city()

def make_shipping_city():
	# from go1_commerce.go1_commerce.api import check_domain
	if not frappe.db.get_value('Country', {'name': "India", 'enabled': 1}):
		frappe.db.set_value('Country', "India", "enabled", 1)

	if not frappe.db.get_value('State', {'state': "Tamil Nadu"}, "name"):
		state = frappe.get_doc({
			'doctype': "State",
			'state': "Tamil Nadu",
			'country': "India"
		}).insert()
	if not frappe.db.get_value('City', {'city': "Chennai"}, "name"):
		state1 = frappe.db.get_value('State', {'state': "Tamil Nadu"}, "name")
		city = frappe.get_doc({
			'doctype': "City",
			'city': "Chennai",
			'state': state1
		}).insert()
	business = frappe.get_value("Business", {"restaurant_name": "Test Business 1", "contact_email":"test_business_1@test.com"}, "name")
	if not frappe.db.get_value('Shipping City', {'city': "Test City 1"}, "name"):
		city1 = frappe.db.get_value('City', {'city': "Chennai"}, "name")
		shipping_city = frappe.get_doc({
			'doctype': "Shipping City",
			'city': "Test City 1",
			'core_city': city1,
			'zipcode_range':600116
		}).insert()
		# if not check_domain('saas') and check_domain('multi_vendor'):
		# 	shipping_city.append("vendor_list",{"vendor":business})
		# else:
		shipping_city.business = business
		shipping_city.save()