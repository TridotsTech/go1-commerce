# Copyright (c) 2024, Tridotstech Private Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, os
from frappe.model.document import Document
from frappe.utils import get_files_path

class CatalogSettings(Document):
	def on_update(self):
		frappe.log_error(title = "catalog self", message = self.as_dict())
		path = get_files_path()
		if not os.path.exists(os.path.join(path,'settings')):
			frappe.create_folder(os.path.join(path,'settings'))
		with open(os.path.join(path,'settings', self.name.lower() + '.json'), "w") as f:
			f.write(frappe.as_json(self))
