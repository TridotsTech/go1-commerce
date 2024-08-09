# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals


import frappe
import unittest
import frappe.utils
from frappe.utils import flt
import frappe, json
from datetime import date, datetime, timedelta

test_records = frappe.get_test_records('Product Tax Template')

class TestProductTaxTemplate(unittest.TestCase):
	def test_tax_template_creation(self):
		if not frappe.db.get_value('Product Tax Template', {'title': "Test Product Tax 1"}):
			make_tax_templates()

def make_tax_templates():
	business1 = frappe.get_value("Business", {"restaurant_name": "Test Business 1", "contact_email":"test_business_1@test.com"}, "name")
	business2 = frappe.get_value("Business", {"restaurant_name": "Test Business 2", "contact_email":"test_business_2@test.com"}, "name")
	tax_template = make_tax_template('Test Product Tax 1')

def make_tax_template(tax_name):
	if not frappe.db.get_value('Product Tax Template', {'title': tax_name}):
		if not frappe.db.get_value('Product Tax Template', {'title': tax_name}):
			
			tax_temp = frappe.get_doc({
				'doctype': "Product Tax Template",
				'title': tax_name
			})
			installed_apps=frappe.db.sql(''' select * from `tabModule Def` where app_name='accounts' ''',as_dict=True)
			if len(installed_apps)>0:
				if not frappe.db.get_value('Account', {'account_name': "Test Account 1"}):
					account = frappe.get_doc({
						'doctype': "Account",
						'account_name': "Test Account 1"
					}).insert()
				account_id = frappe.db.get_value('Account', {'account_name': "Test Account 1"}, "name")
				account_name = frappe.db.get_value('Account', {'account_name': "Test Account 1"}, "account_name")
				tax_temp.append('tax_rates', {'account_head': account_id, 'tax': account_name, 'rate': 18})
				tax_temp.insert()
			else:
				tax_temp.append('tax_rates', {'tax': "GST", 'rate': 18})
				tax_temp.insert()