# Copyright (c) 2024, Tridotstech PVT LTD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import Field,DocType
from frappe.query_builder.functions import Concat

try:
	catalog_settings = get_settings('Catalog Settings')
	no_of_records_per_page = catalog_settings.no_of_records_per_page
except Exception as e:
	catalog_settings = None
	no_of_records_per_page = 10
	
class BuilderData(Document):
	def get_category_products(self,category=None, sort_by=None, page_no=1,
							 page_size=no_of_records_per_page,
							brands=None, rating=None,min_price=None, 
							max_price=None,attributes=None,
							productsid=None,customer=None,route=None):
		if not customer and frappe.request.cookies.get('customer_id'):
			customer = frappe.request.cookies.get('customer_id')
		from go1_commerce.go1_commerce.v2.product import get_category_products as _get_category_products
		product_list = _get_category_products(category=category, 
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
		if customer:
			customer_cart = self.get_customer_cart_items(customer)
			for x in product_list:
				x.in_cart = False
				x.in_wishlist = False
				x.in_cart_qty = 0
				if customer_cart.get("cart") and customer_cart.get("cart").get("items"):
					check_exist = list(filter(lambda ci: ci.product == x.name, customer_cart.get("cart").get("items")))
					if check_exist:
						x.in_cart = True
						x.in_cart_qty = check_exist[0].quantity
				if customer_cart.get("wishlist") and customer_cart.get("wishlist").get("items"):
					check_exist = list(filter(lambda ci: ci.product == x.name, customer_cart.get("wishlist").get("items")))
					if check_exist:
						x.in_wishlist = True

		return product_list
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
		# selected_options_data = frappe.db.sql(f""" 
		# 							SELECT 
		# 								CONCAT(A.attribute_name," : ") AS attribute_name ,
		# 								PAO.option_value,
		# 								PAO.unique_name
		# 							FROM 
		# 								`tabProduct Attribute Option` PAO
		# 							INNER JOIN 
		# 								`tabProduct Attribute` A
		# 							ON 
		# 								PAO.attribute = A.name
		# 							WHERE PAO.unique_name IN ({options_filter})
		# 						""",as_dict=1)
		ProductAttributeOption = DocType('Product Attribute Option')
		ProductAttribute = DocType('Product Attribute')

		query = (
			frappe.qb.from_(ProductAttributeOption)
			.inner_join(ProductAttribute)
			.on(ProductAttributeOption.attribute == ProductAttribute.name)
			.select(
				Concat(ProductAttribute.attribute_name, " : ").as_("attribute_name"),
				ProductAttributeOption.option_value,
				ProductAttributeOption.unique_name
			)
			.where(ProductAttributeOption.unique_name.isin(options_filter))
		)

		selected_options_data = query.run(as_dict=True)
		return selected_options_data

	def get_customer_cart_items(self,customer):
		from go1_commerce.go1_commerce.v2.cart import get_cart_items
		return get_cart_items(customer)

	def get_all_settings(self):
		try:
			import os,json
			path = frappe.utils.get_files_path()
			file_path = os.path.join(path, "settings/all_settings.json")
			all_categories = None
			if os.path.exists(file_path):
					f = open(file_path)
					all_categories = json.load(f)
			return all_categories
		except Exception:
			frappe.log_error(title = "Error in get_all_settings", 
								message = frappe.get_traceback())
