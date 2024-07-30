# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator
from go1_commerce.utils.setup import get_settings

class ProductReviews(WebsiteGenerator):
	pass

@frappe.whitelist(allow_guest=True)
def get_search_datas(searchTxt):
	try:
		searchKey="'%"+searchTxt+"%'"
		search_query=' and ('
		catalog_settings=get_settings('Catalog Settings')
		if len(catalog_settings.search_fields)>0:		
			i=0
			for item in catalog_settings.search_fields:				
				i=i+1
				if i==1:
					search_query+='P.%s like %s' % (item.fieldname,searchKey)
				else:
					search_query+=' or P.%s like %s' % (item.fieldname,searchKey)			
		else:				
			search_query+='P.item like %s' % searchKey
		search_query+=')'
		query=	"""
					SELECT P.name, P.item, P.route 
					FROM `tabProduct` P 
					WHERE P.status = "Approved" 
					AND P.is_active = 1 {search_query}
				""".format(search_query=search_query)

		
		result=frappe.db.sql('''{query}'''.format(query=query),as_dict=1)		
		return result
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in get_search_datas") 			

