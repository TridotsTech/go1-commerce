# -*- coding: utf-8 -*-
# Copyright (c) 2020, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
from frappe.query_builder import DocType

class ShippingCity(Document):
	pass


def get_area_list(reference_doc, reference_fields, city):
	reference_field = json.loads(reference_fields)
	fields = ','.join([x for x in reference_field])
	ReferenceDoc = DocType(reference_doc)
	query = frappe.qb.from_(ReferenceDoc).select(*fields.split(',')).where(ReferenceDoc.city == city)
	list_name= query.run(as_dict=True)
	return {"list_name":list_name}



def get_areas_fromziprange(ziprange):
	zipcoderanges = zip_code(ziprange)
	if zipcoderanges:
		zipcodes = [str(i) for i in zipcoderanges]
		zipcodes = str(zipcodes)[1:-1]
		Area = DocType('Area')
		query = frappe.qb.from_(Area).select(Area.name, Area.area, Area.idx, Area.zipcode).where(Area.zipcode.isin(zipcodes))
		areas= query.run(as_dict=True)
		if areas:
			return areas



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
