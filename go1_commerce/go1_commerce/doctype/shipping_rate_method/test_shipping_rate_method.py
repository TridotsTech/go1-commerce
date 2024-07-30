# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals


import frappe
import unittest
import frappe.utils
from frappe.utils import flt
import frappe, json
from datetime import date, datetime, timedelta

test_records = frappe.get_test_records('Shipping Rate Method')

class TestShippingRateMethod(unittest.TestCase):
	def test_shipping_creation(self):
		business1 = frappe.get_value("Business", {"restaurant_name": "Test Business 1", "contact_email":"test_business_1@test.com"}, "name")
		business2 = frappe.get_value("Business", {"restaurant_name": "Test Business 2", "contact_email":"test_business_2@test.com"}, "name")
		rate_shipping = make_shipping_rate_method(business1, "Fixed Rate Shipping", 1)
		rate_shipping1 = make_shipping_rate_method(business1, "Shipping By Weight", 0)
		rate_shipping2 = make_shipping_rate_method(business1, "Shipping By Total", 0)
		doc_rate_shipping = frappe.get_doc("Shipping Rate Method", rate_shipping).reload()
		doc_rate_shipping1 = frappe.get_doc("Shipping Rate Method", rate_shipping1).reload()
		doc_rate_shipping2 = frappe.get_doc("Shipping Rate Method", rate_shipping2).reload()

def make_shipping_rate_method(business, rate_method_name, is_active):
	# from go1_commerce.go1_commerce.api import check_domain
	rate_method = frappe.get_doc({
		"doctype": 'Shipping Rate Method',
		"is_active": is_active,
		"title": rate_method_name,
		"shipping_rate_method": rate_method_name
	}).insert()
	# if not check_domain('saas') and check_domain('multi_vendor'):
	# 	rate_method.append("vendors",{"vendor":business})
	# else:
		# rate_method.business = business
	rate_method.save()
	method_name = frappe.db.get_value("Shipping Method",{"business":business}, "name")
	zone_name = frappe.db.get_value("Shipping Zones",{"zone_name":"Test Shipping Zone 1"}, "name")
	if rate_method_name and rate_method_name == "Fixed Rate Shipping":
		rate_method.append('shipping_by_fixed_rate', {'shipping_method': method_name, 'shipping_zone': zone_name, 'charge_amount': 50})
		rate_method.save()
	if rate_method_name and rate_method_name == "Shipping By Weight":
		rate_method.append('shipping_by_weight_charges', {'shipping_method': method_name, 'shipping_zone': zone_name, 'order_weight_from': 0, 'order_weight_to':100, 'charge_amount': 50})
		rate_method.save()
	if rate_method_name and rate_method_name == "Shipping By Total":
		rate_method.append('shipping_by_total', {'shipping_method': method_name, 'shipping_zone': zone_name, 'order_total_from': 0, 'order_total_to':100, 'charge_amount': 50})
		rate_method.save()
	print("---------------name")
	print(rate_method)
	return rate_method.name