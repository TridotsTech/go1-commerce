# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import getdate
from frappe.model.document import Document
from frappe.query_builder import DocType

class DiscountTemplate(Document):
	pass

def get_all_templates():
	DiscountTemplate = DocType('Discount Template')
	query = (
	    frappe.qb.from_(DiscountTemplate)
	    .select(DiscountTemplate.name, DiscountTemplate.name1, DiscountTemplate.image)
	)
	result = query.run(as_dict=True)

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

def get_template_info(name):
	return frappe.get_doc('Discount Template', name)
