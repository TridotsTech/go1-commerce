# -*- coding: utf-8 -*-
# Copyright (c) 2020, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class APILog(Document):
	def onload(self):
		if not self.seen:
			self.db_set('seen', 1, update_modified=0)
			frappe.db.commit()

def set_old_logs_as_seen():
	frappe.db.sql("""UPDATE `tabAPI Log` SET `seen` = 1
					WHERE `seen` = 0 
     					AND `creation` < (NOW() - INTERVAL '7' DAY)""")
	frappe.db.sql("""DELETE FROM `tabAPI Log` 
               		WHERE `creation` < (NOW() - INTERVAL '30' DAY)""")

@frappe.whitelist()
def clear_api_logs():
	'''Flush all API Logs'''
	frappe.only_for('System Manager')
	frappe.db.sql('''DELETE FROM `tabAPI Log`''')
	frappe.db.sql('''DELETE FROM `tabApi Log Group`''')