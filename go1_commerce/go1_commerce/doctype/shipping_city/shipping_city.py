# -*- coding: utf-8 -*-
# Copyright (c) 2020, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document


class ShippingCity(Document):
	pass

@frappe.whitelist()
def get_area_list(reference_doc, reference_fields, city):
	reference_field = json.loads(reference_fields)
	fields = ','.join([x for x in reference_field])
	list_name = frappe.db.sql('''select {field} from `tab{dt}` where city ="{city}"'''.format(field=fields, dt=reference_doc, city=city), as_dict=1)
	return {"list_name":list_name}


@frappe.whitelist()
def get_areas_fromziprange(ziprange):
	zipcoderanges = zip_code(ziprange)
	if zipcoderanges:
		zipcodes = [str(i) for i in zipcoderanges]
		zipcodes = str(zipcodes)[1:-1]
		query = '''SELECT name, area, idx, zipcode FROM `tabArea` WHERE zipcode in ({zipcodes})'''.format(zipcodes=zipcodes)
		areas = frappe.db.sql("""{query}""".format(query=query),as_dict=1)
		if areas:
			return areas


@frappe.whitelist()
def zip_code(ziprange):
	zipcoderanges = []
	returnValue = []
	if ziprange.find(',') > -1:
		zipcoderanges = ziprange.split(',')
		for x in zipcoderanges:
			if x.find('-') > -1:
				zipcoderanges_after = x.split('-')
				for zipcode in range(int(zipcoderanges_after[0]), int(zipcoderanges_after[1]) + 1):
					returnValue.append(int(zipcode))
			else:
				returnValue.append(int(x))
	elif ziprange.find('-') > -1:
		zipcoderanges_after = ziprange.split('-')
		for zipcode in range(int(zipcoderanges_after[0]), int(zipcoderanges_after[1]) + 1):
			returnValue.append(int(zipcode))
	else:
		returnValue.append(int(ziprange))
	return returnValue
