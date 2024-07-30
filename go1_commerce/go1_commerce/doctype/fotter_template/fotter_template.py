# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import frappe, os 
from frappe.utils import encode

class FooterTemplate(Document):
	def validate(self):
		if not self.file_name:
			self.file_name = self.name.lower().replace(' ','_')
		path = frappe.get_module_path("cms_website")
		path_parts = path.split('/')
		path_parts = path_parts[:-1]
		url = '/'.join(path_parts)	
		with open(os.path.join(url,'templates','Layout','Footer', (self.file_name+'.html')), "w") as f:
			f.write(encode(self.footer_content))
	