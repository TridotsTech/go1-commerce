# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator


class Pages(WebsiteGenerator):
	def autoname(self):
		self.name = self.page_title
	def validate(self):
		if not self.route:
			self.route = self.scrub(self.page_title)
		super(Pages, self).validate()
		if not self.meta_title:
			self.meta_title = self.page_title
		if not self.meta_keywords:
			self.meta_keywords = self.page_title.replace(" ", ", ")
		if not self.meta_description:
			self.meta_description = "About: "+self.page_title


	def get_context(self, context):
		try:
			page = None
			if context.get('web_domain'):
				check_routes = frappe.db.get_all('Pages', 
							filters = {'route': self.route},
							fields = ['page_title', 'is_published', 'include_right_sidebar', 'content',
									'meta_title', 'meta_description', 'meta_keywords'])
				if check_routes:
					page = check_routes[0]
			if not page:
				page = self
			if page.meta_title:
				context.meta_title = page.meta_title
			if page.meta_description:
				context.meta_description = page.meta_description
			if page.meta_keywords:
				context.meta_keywords = page.meta_keywords
			context.page = page
			context.mobile_page_title = self.page_title
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Error in pages.pages.terms_and_conditions.get_context") 