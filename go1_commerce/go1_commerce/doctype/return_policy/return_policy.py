# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class ReturnPolicy(Document):
	def autoname(self):
		naming_series = 'RP-'
		self.name = make_autoname(naming_series + '.#####', doc=self)


def get_query_condition(user):
	return ""
	
def has_permission(doc, user):
	return True
	