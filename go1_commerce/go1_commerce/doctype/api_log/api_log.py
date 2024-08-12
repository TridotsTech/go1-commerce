# -*- coding: utf-8 -*-
# Copyright (c) 2020, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType, Interval

class APILog(Document):
	def onload(self):
		if not self.seen:
			self.db_set('seen', 1, update_modified=0)
			frappe.db.commit()

def set_old_logs_as_seen():
    ApiLog = DocType('API Log')
    frappe.qb.update(ApiLog)
        .set(ApiLog.seen, 1)
        .where((ApiLog.seen == 0) & (ApiLog.creation < (now() - Interval(days=7))))
        .run()
    frappe.qb.from_(ApiLog)
        .delete()
        .where(ApiLog.creation < (now() - Interval(days=30)))
        .run()

def clear_api_logs():
    frappe.only_for('System Manager')
    
    ApiLog = DocType('API Log')
    ApiLogGroup = DocType('Api Log Group')
    frappe.qb.from_(ApiLog).delete().run()
    frappe.qb.from_(ApiLogGroup).delete().run()