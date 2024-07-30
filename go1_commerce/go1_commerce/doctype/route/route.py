# Copyright (c) 2023, Tridots Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Route(Document):
	def validate(self):
		if self.route_se:
			for x in self.route_se:
				check_exist = frappe.db.get_all("Route SE",filters={"parent":self.name,"se":x.se,"name":("!=",x.name)})
				if check_exist:
					frappe.throw("Sales Executive <b>"+x.se_name +"( "+x.se+" )</b> is already mapped to this route.")
			ses_names = ""
			for x in self.route_se:
				ses_names += x.se_name+","
			self.se_names = ses_names[:-1]