# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import re
from frappe.model.document import Document
from frappe.website.utils import cleanup_page_name

class SearchKeyword(Document):
	def validate(self):
		self.make_route()

	def make_route(self):
		if not self.route:
			self.route = cleanup_page_name(self.keyword).replace('_', '-')