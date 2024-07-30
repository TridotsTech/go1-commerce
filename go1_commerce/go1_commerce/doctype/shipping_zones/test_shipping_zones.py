# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals


import frappe
import unittest
import frappe.utils

test_records = frappe.get_test_records('Shipping Zones')

class TestShippingZones(unittest.TestCase):
	def test_zones_creation(self):
		make_shipping_zones("Test Shipping Zone 1")

def make_shipping_zones(zone):
	if not frappe.db.get_value("Shipping Zones", { "zone_name": zone}):
		to_city = frappe.db.get_value('Shipping City', {'city': "Porur"}, "name")
		zone = frappe.get_doc({
			"doctype": "Shipping Zones",
			"zone_name": zone,
			"to_city": to_city
		}).insert()