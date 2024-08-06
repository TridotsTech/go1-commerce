# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Campaign(Document):
    def on_update(self):
        if self.get("campaign_schedules"):
            for ecmp in self.campaign_schedules:
                for k in frappe.db.get_all ("Email Campaign",{"campign_id":ecmp.name,"status":["IN",["Scheduled","In Progress"]],"email_template":["!=",ecmp.email_template]},["name"]):
                    doc = frappe.get_doc("Email Campaign",k.name)
                    doc.email_template = ecmp.email_template
                    doc.save(ignore_permissions = True)