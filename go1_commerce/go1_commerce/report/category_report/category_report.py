# Copyright (c) 2023, Tridotstech and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = get_columns(), get_data()
	return columns, data

def get_columns():
	return[
		"Category Id" + ":Link/Product Category:200",
		"Category Name" + ":Data:200",
		"Sub Category Id" + ":Link/Product Category:200",
		"Sub Category Name" + ":Data:200",
		"Sub Sub Category Id" + ":Link/Product Category:200",
		"Sub Sub Category Name" + ":Data:200",
	]

def get_data():
	cat_data = []
	categories = frappe.db.sql(""" SELECT name , category_name FROM `tabProduct Category` 
								   WHERE is_active=1 AND 
								 (parent_product_category IS NULL OR parent_product_category='')	
							     ORDER BY category_name """,as_dict=1)
	for x in categories:
		sub_categories = frappe.db.sql(""" SELECT name , category_name FROM `tabProduct Category` 
								   WHERE is_active=1 AND 
								 (parent_product_category =%(category_id)s)	 ORDER BY category_name 
							  """,{"category_id":x.name},as_dict=1)
		if sub_categories:
			for s in sub_categories:
				sub_sub_categories = frappe.db.sql(""" SELECT name , category_name FROM `tabProduct Category` 
								   WHERE is_active=1 AND 
								 (parent_product_category =%(category_id)s)	 ORDER BY category_name 
							  """,{"category_id":s.name},as_dict=1)
				if sub_sub_categories:
					for ss in sub_sub_categories:
						cat_data.append({
							"category_id":x.name,
							"category_name":x.category_name,
							"sub_category_id":s.name,
							"sub_category_name":s.category_name,
							"sub_sub_category_id":ss.name,
							"sub_sub_category_name":ss.category_name,
							}
							)
				else:
					cat_data.append({
							"category_id":x.name,
							"category_name":x.category_name,
							"sub_category_id":s.name,
							"sub_category_name":s.category_name,
							"sub_sub_category_id":"",
							"sub_sub_category_name":"",
							}
							)
		else:
			cat_data.append({
							"category_id":x.name,
							"category_name":x.category_name,
							"sub_category_id":"",
							"sub_category_name":"",
							"sub_sub_category_id":"",
							"sub_sub_category_name":"",
							}
							)
	return cat_data
