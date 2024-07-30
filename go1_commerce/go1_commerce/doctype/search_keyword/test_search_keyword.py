# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals


import frappe
import unittest
import frappe.utils

test_records = frappe.get_test_records('Search Keyword')

class TestSearchKeyword(unittest.TestCase):
	def test_search_creation(self):
		srch_key = make_search_keyword("Test Search Keyword 1")
		srch_key1 = make_search_keyword("Test Search Keyword 2")

def make_search_keyword(keyword):
	if not frappe.db.get_value("Search Keyword", {"keyword": keyword}):
		srch_key = frappe.get_doc({
			"doctype": "Search Keyword",
			"keyword": keyword
		}).insert()
		srch_key.reload()