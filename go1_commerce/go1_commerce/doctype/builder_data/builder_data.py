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
	def get_category_products(self,params):
		customer = None
		if not params.get("customer") and frappe.request.cookies.get('customer_id'):
			customer = frappe.request.cookies.get('customer_id')
		from go1_commerce.go1_commerce.v2.product import get_category_products as _get_category_products
		product_list = _get_category_products(params)
		customer_cart = None
		frappe.log_error("get_customer_cart_items",customer)
		if customer:
			customer_cart = self.get_customer_cart_items(customer)
		for x in product_list:
			x.in_cart = False
			x.in_wishlist = False
			x.in_cart_qty = 0
			x.cart_item_id = ""
			x.wishlist_item_id = ""
			if customer_cart:
				if customer_cart.get("cart") and customer_cart.get("cart").get("items"):
					check_exist = list(filter(lambda ci: ci.product == x.name, customer_cart.get("cart").get("items")))
					if check_exist:
						x.in_cart = True
						x.in_cart_qty = check_exist[0].quantity
						x.cart_item_id = check_exist[0].name
				if customer_cart.get("wishlist") and customer_cart.get("wishlist").get("items"):
					check_exist = list(filter(lambda ci: ci.product == x.name, customer_cart.get("wishlist").get("items")))
					if check_exist:
						x.in_wishlist = True
						x.wishlist_item_id = check_exist[0].name
		frappe.log_error("product_list",product_list)
		return product_list
	def get_product_details(self,route):
		from go1_commerce.go1_commerce.v2.product import get_product_details as _get_product_details
		return _get_product_details(route=route)
	def get_category_filters(self,route):
		from go1_commerce.go1_commerce.v2.category import get_category_filters as _get_category_filters
		return _get_category_filters(route=route)
	def get_attributes_data(self,options):
		try:
			options_data = options.split(",")
			options_filter = ""
			if options_data:
				options_filter = ','.join(['"' + x + '"' for x in options_data if x])
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
			frappe.log_error("get_attributes_data",query)
			selected_options_data = query.run(as_dict=True)
			return selected_options_data
		except Exception:
			frappe.log_error(title = "Error in builder_data.get_attributes_data", 
								message = frappe.get_traceback())

	def get_customer_cart_items(self,customer=None):
		cart_obj={}
		frappe.log_error("cart customer",customer)
		if customer:
			from go1_commerce.go1_commerce.v2.cart import get_customer_cart_items as _get_customer_cart
			cart_obj = _get_customer_cart(customer)
			currency = frappe.db.get_single_value("Catalog Settings","default_currency")
			currency_symbol = frappe.db.get_value("Currency",currency,"symbol")
			if cart_obj.get("status") == "success":
				if cart_obj.get("cart"):
					total_amount = 0
					for c in cart_obj.get("cart").get("items"):
						c.formatted_price = frappe.utils.fmt_money(c["price"],currency=currency_symbol)
						total_amount = c["total"] + total_amount
					cart_obj.get("cart")["formatted_total"] = frappe.utils.fmt_money(total_amount,currency=currency_symbol)
				if cart_obj.get("wishlist"):
					for c in cart_obj.get("wishlist").get("items"):
						c.formatted_price = frappe.utils.fmt_money(c["price"],currency=currency_symbol)
			 
		return cart_obj

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
			frappe.log_error(title = "Error in builder_data.get_all_settings", 
								message = frappe.get_traceback())


