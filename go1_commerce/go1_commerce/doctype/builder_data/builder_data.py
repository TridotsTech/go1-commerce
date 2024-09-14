# Copyright (c) 2024, Tridotstech PVT LTD and contributors
# For license information, please see license.txt

import frappe

from frappe.model.document import Document
from frappe.query_builder import Field,DocType
from frappe.query_builder.functions import Concat

from go1_commerce.utils.utils import role_auth,get_customer_from_token,other_exception

try:
	catalog_settings = get_settings('Catalog Settings')
	cart_settings = frappe.get_single('Shopping Cart Settings')
	no_of_records_per_page = catalog_settings.no_of_records_per_page
except Exception as e:
	catalog_settings = None
	no_of_records_per_page = 10
	
class BuilderData(Document):
	def get_category_products(self,**params):
		customer = None
		if not params.get("customer") and frappe.request.cookies.get('customer_id'):
			customer = frappe.request.cookies.get('customer_id')
		from go1_commerce.go1_commerce.v2.product import get_category_products as _get_category_products
		product_list = _get_category_products(params.get("params"))
		customer_cart = None
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
		return product_list
		
	def get_product_details(self,route):
		from go1_commerce.go1_commerce.v2.product import get_product_details as _get_product_details
		customer = None
		customer_cart = None
		if frappe.request.cookies.get('customer_id'):
			customer = frappe.request.cookies.get('customer_id')
		p_details =  _get_product_details(route=route)
		currency = frappe.db.get_single_value("Catalog Settings","default_currency")
		currency_symbol = frappe.db.get_value("Currency",currency,"symbol")
		p_details["formatted_price"] = frappe.utils.fmt_money(p_details["price"],currency=currency_symbol)
		p_details["formatted_old_price"] = frappe.utils.fmt_money(p_details["old_price"],currency=currency_symbol)
		if customer:
			customer_cart = self.get_customer_cart_items(customer)
		p_details.in_cart = 0
		p_details.in_wishlist = 0
		p_details.in_cart_qty = 0
		p_details.cart_item_id = ""
		p_details.wishlist_item_id = ""
		if customer_cart:
			if customer_cart.get("cart") and customer_cart.get("cart").get("items"):
				check_exist = list(filter(lambda ci: ci.product == p_details.name, customer_cart.get("cart").get("items")))
				if check_exist:
					p_details.in_cart = 1
					p_details.in_cart_qty = check_exist[0].quantity
					p_details.cart_item_id = check_exist[0].name
			if customer_cart.get("wishlist") and customer_cart.get("wishlist").get("items"):
				check_exist = list(filter(lambda ci: ci.product == p_details.name, customer_cart.get("wishlist").get("items")))
				if check_exist:
					p_details.in_wishlist = 1
					p_details.wishlist_item_id = check_exist[0].name
		from go1_commerce.go1_commerce.v2.product import get_product_other_info
		p_details.other_data = get_product_other_info(p_details.name)
		if p_details.other_data.get("best_seller_category"):
			for x in p_details.other_data.get("best_seller_category"):
				x.in_cart = False
				x.in_wishlist = False
				x.in_cart_qty = 0
				x.cart_item_id = ""
				x.wishlist_item_id = ""
				if customer_cart:
					if customer_cart.get("cart") and customer_cart.get("cart").get("items"):
						check_exist = list(filter(lambda ci: ci.product == x.name, customer_cart.get("cart").get("items")))
						if check_exist:
							x.in_cart = 1
							x.in_cart_qty = check_exist[0].quantity
							x.cart_item_id = check_exist[0].name
					if customer_cart.get("wishlist") and customer_cart.get("wishlist").get("items"):
						check_exist = list(filter(lambda ci: ci.product == x.name, customer_cart.get("wishlist").get("items")))
						if check_exist:
							x.in_wishlist = 1
							x.wishlist_item_id = check_exist[0].name
		if p_details.other_data.get("products_purchased_together"):
			for x in p_details.other_data.get("products_purchased_together"):
				x.in_cart = False
				x.in_wishlist = False
				x.in_cart_qty = 0
				x.cart_item_id = ""
				x.wishlist_item_id = ""
				if customer_cart:
					if customer_cart.get("cart") and customer_cart.get("cart").get("items"):
						check_exist = list(filter(lambda ci: ci.product == x.name, customer_cart.get("cart").get("items")))
						if check_exist:
							x.in_cart = 1
							x.in_cart_qty = check_exist[0].quantity
							x.cart_item_id = check_exist[0].name
					if customer_cart.get("wishlist") and customer_cart.get("wishlist").get("items"):
						check_exist = list(filter(lambda ci: ci.product == x.name, customer_cart.get("wishlist").get("items")))
						if check_exist:
							p_details.in_wishlist = 1
							p_details.wishlist_item_id = check_exist[0].name
		if p_details.other_data.get("related_products"):
			for x in p_details.other_data.get("related_products"):
				x.in_cart = False
				x.in_wishlist = False
				x.in_cart_qty = 0
				x.cart_item_id = ""
				x.wishlist_item_id = ""
				if customer_cart:
					if customer_cart.get("cart") and customer_cart.get("cart").get("items"):
						check_exist = list(filter(lambda ci: ci.product == x.name, customer_cart.get("cart").get("items")))
						if check_exist:
							x.in_cart = 1
							x.in_cart_qty = check_exist[0].quantity
							x.cart_item_id = check_exist[0].name
					if customer_cart.get("wishlist") and customer_cart.get("wishlist").get("items"):
						check_exist = list(filter(lambda ci: ci.product == x.name, customer_cart.get("wishlist").get("items")))
						if check_exist:
							x.in_wishlist = 1
							x.wishlist_item_id = check_exist[0].name
		return p_details

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
				.where(ProductAttributeOption.unique_name.isin(options_data))
			)
			
			selected_options_data = query.run(as_dict=True)
			return selected_options_data
		except Exception:
			frappe.log_error(title = "Error in builder_data.get_attributes_data", 
								message = frappe.get_traceback())

	def get_customer_cart_items(self,customer=None):
		cart_obj={}
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

	def get_customer_dashboard(self, customer_id):
		from go1_commerce.go1_commerce.v2.customer import get_orders_list, get_list_period_wise
		recent_orders = get_orders_list(page_no = 1,page_length = 10, no_subscription_order = 1, customer=customer_id)
		dt = 'Order'
		data = get_list_period_wise(dt,customer_id)
		week_order_list = data[0]
		month_order_list = data[1]
		today_order_list = data[2]
		all_order_list = data[3]
		return {"all_count":len(all_order_list),
				"monthly_count": len(month_order_list),
				"today_orders_count": len(today_order_list),"recent_orders":recent_orders,
				"week_orders_count":len(week_order_list)}

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

	def get_customer_address(self, customer_id = None):
		from go1_commerce.go1_commerce.v2.customer import get_customer_address as _get_customer_address
		return _get_customer_address(customer_id = customer_id)


	def get_checkout_details(self):
		result = {}
		from go1_commerce.go1_commerce.v2.checkout import get_payment_methods as _get_payment_methods, get_shipping_methods as _get_shipping_methods
		result["payment_methods"] = _get_payment_methods()
		result["shipping_methods"] = _get_shipping_methods()
		frappe.log_error("checkout data",result)
		return result

	def get_order_info(self, order_id):
		frappe.log_error("order_id",order_id)
		order = frappe.get_doc('Order', order_id)
		order_detail = order.as_dict()
		order_item_qty =0
		for it in order_detail.order_item:
			if it.quantity:
				order_item_qty += it.quantity
		order_detail.total_item_qty = order_item_qty
		setattr(order_detail, 'total_item_qty', order_item_qty)
		delivery_slot = []
		check_slot = frappe.db.get_all('Order Delivery Slot',
					 filters={'order': order_id}, 
					 fields=['order_date', 'from_time', 'to_time', 'product_category'])
		if check_slot:
			for deli_slot in check_slot:
				category = ''
				if deli_slot.product_category:
					category = frappe.get_value('Product Category', 
							   deli_slot.product_category, 'category_name')
				from_time = datetime.strptime(str(deli_slot.from_time), '%H:%M:%S').time()
				to_time = datetime.strptime(str(deli_slot.to_time), '%H:%M:%S').time()
				delivery_slot.append({
									  'delivery_date': deli_slot.order_date.strftime('%b %d, %Y'),
									  'from_time'    : from_time.strftime('%I:%M %p'),
									  'to_time'      : to_time.strftime('%I:%M %p'),
									  'category'     : category
									})

		data = {"info":order_detail,"delivery_slot":delivery_slot}
		return data

	def get_country_data(self):
		try:
			Country = DocType("Country")
			query = (
				frappe.qb.from_(Country)
				.select(Country.name)
				.where(Country.enabled == 1)
			)
			return query.run(as_dict=True)
		except Exception:
			other_exception("Error in v2.cart.get_country_states")

	def redirect_login(self,redirect_url=None):
		frappe.local.flags.redirect_location = '/login'+("?redirect_url="+redirect_url) if redirect_url else ""
		raise frappe.Redirect

	