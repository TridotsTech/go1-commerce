# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import getdate
from frappe.model.document import Document

class DiscountTemplate(Document):
	pass

@frappe.whitelist()
def get_all_templates():
	return frappe.db.sql('''SELECT name, name1, image 
							FROM `tabDiscount Template`''', as_dict=1)

@frappe.whitelist()
def create_discount(template):
	from frappe.model.mapper import get_mapped_doc
	doc = get_mapped_doc("Discount Template", template, {
															"Discount Template": {
																"doctype": "Discounts"
															},
															"Discount Requirements":{
																"doctype": "Discount Requirements"
															}
														}, None, ignore_permissions=True)
	doc.start_date = getdate()
	doc.save(ignore_permissions=True)
	return doc

@frappe.whitelist()
def get_template_info(name):
	return frappe.get_doc('Discount Template', name)
