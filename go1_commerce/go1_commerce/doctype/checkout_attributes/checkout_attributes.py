# -*- coding: utf-8 -*-
# Copyright (c) 2020, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
from frappe.query_builder import DocType, Order

class CheckoutAttributes(Document):
	pass

def get_options(attribute):
	CheckoutAttributesOptions = DocType('Checkout Attributes Options')
	query = (
	    frappe.qb.from_(CheckoutAttributesOptions)
	    .select(CheckoutAttributesOptions.option_value)
	    .where(CheckoutAttributesOptions.parent == attribute)
	    .orderby(CheckoutAttributesOptions.display_order, order=Order.asc)
	)
	return query.run(as_dict=False)
