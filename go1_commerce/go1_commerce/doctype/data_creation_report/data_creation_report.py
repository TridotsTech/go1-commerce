# -*- coding: utf-8 -*-
# Copyright (c) 2020, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe.utils import get_datetime

class DataCreationReport(Document):
	def get_json(self):
		res_json = []
		if self.result_json:
			res_json = json.loads(self.result_json)
		return res_json

def create_data_report(data_type='Default Data'):
	doc = frappe.new_doc('Data Creation Report')
	doc.started_at = get_datetime()
	doc.data_type = data_type
	doc.is_completed = 0
	doc.save(ignore_permissions=True)
	return doc



def update_data_report(name, results):
	doc = frappe.get_doc('Data Creation Report', name)
	doc.result_json = results
	doc.completed_at = get_datetime()
	doc.is_completed = 1
	doc.save(ignore_permissions=True)
	webpage_builders = frappe.db.get_all("Web Page Builder")
	frappe.log_error(webpage_builders,'page builder') 
	for x in webpage_builders:
		webpage_builder = frappe.get_doc("Web Page Builder",x.name)
		webpage_builder.save()
