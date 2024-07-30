# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
from datetime import datetime

class Delivery(Document):
	def validate(self):		
		if self.driver_assigned:
			for item in self.driver_assigned:
				if not item.notified_at:
					item.notified_at = datetime.now()
				if not item.order_id:
					item.order_id=self.order