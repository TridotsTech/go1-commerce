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

