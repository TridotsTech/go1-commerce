# Copyright (c) 2024, Tridotstech PVT LTD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BuilderData(Document):
	def get_category_products(self,category=None, sort_by=None, page_no=1,
							 page_size=6,
							brands=None, rating=None,min_price=None, 
							max_price=None,attributes=None,
							productsid=None,customer=None,route=None):
		frappe.log_error("check_category",category)
		frappe.log_error("brands",brands)
		frappe.log_error("attributes",attributes)
		from go1_commerce.go1_commerce.v2.product import get_category_products as _get_category_products
		return _get_category_products(category=category, 
							sort_by=sort_by, 
							page_no=page_no,
							page_size=page_size,
							brands=brands, 
							rating=rating,
							min_price=min_price, 
							max_price=max_price,
							attributes=attributes,
							customer=customer,
							route=route)
	def get_product_details(self,route):
		from go1_commerce.go1_commerce.v2.product import get_product_details as _get_product_details
		return _get_product_details(route=route)
	def get_category_filters(self,route):
		from go1_commerce.go1_commerce.v2.category import get_category_filters as _get_category_filters
		return _get_category_filters(route=route)
	def get_attributes_data(self,options):
		options_data = options.split(",")
		options_filter = ""
		if options_data:
			options_filter = ','.join(['"' + x + '"' for x in options_data if x])
		# frappe.log_error("options_filter",options_filter)
		selected_options_data = frappe.db.sql(f""" 
									SELECT 
										CONCAT(A.attribute_name," : ") AS attribute_name ,
										PAO.option_value,
										PAO.unique_name
									FROM 
										`tabProduct Attribute Option` PAO
									INNER JOIN 
										`tabProduct Attribute` A
									ON 
										PAO.attribute = A.name
									WHERE PAO.unique_name IN ({options_filter})
								""",as_dict=1)
		# frappe.log_error("selected_options_data",selected_options_data)
		return selected_options_data
