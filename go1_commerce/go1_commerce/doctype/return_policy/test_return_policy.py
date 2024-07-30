# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals


import frappe
import unittest
import frappe.utils

test_records = frappe.get_test_records('Return Policy')

class TestReturnPolicy(unittest.TestCase):
	pass
		
		

def make_return_policy(name, business=None):
	if not frappe.db.get_value("Return Policy", { "heading": name, "business":business}):
		return_policy = frappe.get_doc({
			"doctype": "Return Policy",
			"heading": name,
			"business": business,
			"description": "Test Return Policy Description",
			"no_of_days": 5,
			"business_name":""
		}).insert()
		return return_policy.name
	else:
		return frappe.get_value("Return Policy", { "heading": name, "business":business}, "name")
