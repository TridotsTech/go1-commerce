# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe,json
from frappe.model.document import Document

class CoreSettings(Document):
	pass

@frappe.whitelist()
def set_global_defaults(val):
	app_name=val
	installed_apps = frappe.get_installed_apps()
	if not app_name in installed_apps:
		installed_apps.append(app_name)
		frappe.db.set_global("installed_apps", json.dumps(installed_apps))
		frappe.db.commit()
		return installed_apps

@frappe.whitelist()
def get_doc_fields(doctype, exclude=None):
	trans_ref =""
	labels= ["Section Break", "Column Break"]
	exclude = json.loads(exclude)
	if len(exclude) > 0:
		trans_ref = ", ".join(['"' + i + '"' for i in exclude])
	if len(labels) > 0:
		label = ", ".join(['"' + i + '"' for i in labels])
	fields = frappe.db.sql(f"""	SELECT * 
								FROM `tabDocField` 
								WHERE parent = '{doctype}'
								AND label NOT IN ({label}) 
								AND fieldname NOT IN ({trans_ref}) 
								AND fieldtype = "Section Break" 
								ORDER BY idx """,as_dict=1)
	return fields