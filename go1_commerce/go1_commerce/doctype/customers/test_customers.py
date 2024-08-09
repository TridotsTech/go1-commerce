# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals


import frappe
import unittest
import frappe.utils

test_records = frappe.get_test_records('Customers')

class TestCustomer(unittest.TestCase):
	def test_customer_creation(self):
		make_customer()

def make_customer():
	business1 = frappe.get_value("Business", {"restaurant_name": "Test Business 1", "contact_email":"test_business_1@test.com"}, "name")
	business2 = frappe.get_value("Business", {"restaurant_name": "Test Business 2", "contact_email":"test_business_2@test.com"}, "name")
	if not frappe.db.get_value("Customers", {  "email":"testcustomer1@gmail.com"}):
		cust1 = frappe.get_doc(dict(first_name="Test Customer 1",doctype= "Customers", 
				phone="9087654321", 
				gender="Female", 
				
				email="testcustomer1@gmail.com", 
				last_name="Test", 
				set_new_password="#Admin123#",
				table_6=[dict(first_name="Test Customer 1",last_name="", 
				is_default=1, address="Lake View extate", city="Chennai", state="Tamil Nadu", 
				country="India", zipcode="600022", phone="9087654321")]
		)).insert()
		cust1.reload()
	if not frappe.db.get_value("Customers", { "email":"testcustomer2@gmail.com"}):
		cust2 = frappe.get_doc(dict(first_name="Test Customer 2", doctype= "Customers",
				phone="9087654322", 
				gender="Female", 
				
				email="testcustomer2@gmail.com", 
				last_name="Test", 
				set_new_password="#Admin123#",
				table_6=[dict(first_name="Test Customer 2",last_name="", 
				is_default=1, address="Lake View extate", city="Chennai", state="Tamil Nadu", 
				country="India", zipcode="600022", phone="9087654322")]
		)).insert()
		cust2.reload()
