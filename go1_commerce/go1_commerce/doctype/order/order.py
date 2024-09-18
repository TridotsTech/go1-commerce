# -*- coding: utf-8 -*-
# Copyright (c) 2018 info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from urllib.error import HTTPError
import frappe, json, math, os
from frappe.query_builder import DocType, functions as fn, Order
from frappe.model.document import Document
from frappe.utils import flt, nowdate, getdate, now, get_datetime, touch_file
from datetime import datetime, timedelta
from go1_commerce.utils.setup import get_settings_value, get_settings
from frappe.desk.form.linked_with import get_linked_docs, get_linked_doctypes
from go1_commerce.go1_commerce.v2.orders \
	import calculate_tax_from_template, calculate_tax_without_discount, make_sales_invoice ,\
		get_today_date


whitelisted_globals = {
	"int": int,
	"float": float,
	"long": int,
	"round": round,
	"date": datetime.date,
	"getdate": getdate,
	"str":str,
	"math": math
}


class Order(Document):
	@property
	def customer_info_html(self):
		if not self.get('__islocal') :
			return frappe.render_template('templates/dynamic_components/customer_info.html',
									{"order_details" :self})
		return ""
	
	
	@property
	def order_info_html(self):
		if not self.get('__islocal') and self.creation:
			return frappe.render_template('templates/dynamic_components/order_info.html',
								{"order_details" :self})
		return ""
	
	@property
	def address_info_html(self):
		if not self.get('__islocal'):
			return frappe.render_template('templates/dynamic_components/address_info.html',
								{"show_address":1,"order_details" :self})
		return ""

	
	@property
	def items_html(self):
		try:
			if self.order_subtotal:
				delivery_slot = []
				check_delivery_slot = frappe.db.get_all('Order Delivery Slot',
											filters = {'order': self.name},
											fields = ['order_date', 'from_time', 'to_time','product_category'])
				if check_delivery_slot:
					for deli_slot in check_delivery_slot:
						category = ''
						if deli_slot.product_category:
							category = frappe.get_value('Product Category',
								deli_slot.product_category, 'category_name')
						from_time = datetime.strptime(str(deli_slot.from_time), '%H:%M:%S').time()
						to_time = datetime.strptime(str(deli_slot.to_time), '%H:%M:%S').time()
						delivery_slot.append({
											'delivery_date': deli_slot.order_date.strftime('%b %d, %Y'),
											'from_time': from_time.strftime('%I:%M %p'),
											'to_time': to_time.strftime('%I:%M %p'),
											'category': category
											})
				order_settings = frappe.get_single('Order Settings')
				catalog_settings = frappe.get_single('Catalog Settings')
				additional_charges = frappe.db.get_all("Order Additional Charge",
														filters = {"parent":self.name},
														fields=['charge_name','amount'])
				currency = frappe.db.get_value("Currency",self.currency,"symbol")
				items_html = frappe.render_template(
													'templates/dynamic_components/items_info.html',
													{
														"catalog_settings":catalog_settings,
														"order_details" :self,
														'currency':currency,
														'delivery_slot':delivery_slot,
														"additional_charges":additional_charges,
														"order_settings":order_settings
													})
				return items_html
			return ""
		except Exception:
			frappe.log_error("Error in doctype.order", frappe.get_traceback())


	def on_update(self):
		self.update_delivery_slot()
		if self.order_item:
			from go1_commerce.go1_commerce.doctype.discounts.discounts \
			import check_product_discounts

			total_weight = 0
			for item in self.order_item:
				total_weight += flt(item.weight) if item.weight else 0
			check_product_discounts(
									self.order_item, 
									self.customer, 
									self.shipping_method,
									self.payment_method, 
									order = self.name,
									total_weight = total_weight)
		if self.outstanding_amount == 0:
			frappe.db.set_value("Order", self.name, "payment_status", "Paid")
		catalog_settings = get_settings("Catalog Settings")
		included_tax = catalog_settings.included_tax
		cart_item = {}
		if included_tax:
			tax_type = 'Incl. Tax'
		else:
			tax_type = 'Excl. Tax'
		if self.docstatus == 1:
			self.update_items_stock()
		tax_splitup = []
		tax_json = []
		tax_breakup = ""
		if self.docstatus == 0:
			tax = sum(item.tax for item in self.order_item if (item.tax and item.is_free_item != 1))
			for i in self.order_item:
				cart_item["product"] = i.item
				cart_item["amount"] = i.amount
				cart_item["tax"] = i.tax
				cart_item = frappe._dict(cart_item)
				total=cart_item.amount
				item_tax = 0
				from go1_commerce.go1_commerce.v2.orders \
					import insert_order_tax_template
				tax_splitup = insert_order_tax_template(total,cart_item,included_tax,item_tax,
														tax_splitup,tax_type)
				if tax_splitup:
					if not self.tax_breakup:
						self.tax_breakup = ""
					for s in tax_splitup: 
						tax_json.append(s)
						self.tax_breakup += str(s['type']) + ' - ' + str('{0:.2f}'.
									format(s['rate'])) + '% - ' + str('{0:.2f}'.
									format(s['amount'])) + ' - ' + tax_type + '\n'
			frappe.db.set_value('Order', self.name, 'tax_json', json.dumps(tax_json))
			frappe.db.set_value('Order', self.name, 'tax_breakup', tax_breakup)
			frappe.db.set_value('Order', self.name, 'total_tax_amount',self.total_tax_amount)
			


	def validate(self):
		catalog_settings = frappe.get_single('Catalog Settings')
		if not self.currency and catalog_settings.default_currency:
			self.currency = catalog_settings.default_currency
		self.included_tax = catalog_settings.included_tax

		if not self.shipping_shipping_address:
			self.set_customer_address()
		if not self.shipping_method:
			shipping_methods = frappe.db.get_all("Shipping Method",
													filters = {"show_in_website":1}, 
													order_by = "display_order",
													fields = ['shipping_method_name','name'])
			if shipping_methods:
				self.shipping_method = shipping_methods[0].name
				self.shipping_method_name = shipping_methods[0].shipping_method_name
		if not self.payment_method:
			payment_methods = frappe.db.get_all("Payment Method",
												filters = {"enable":1},
												order_by = "display_order",
												fields = ['payment_method','name'])
			if payment_methods:
				self.payment_method = payment_methods[0].name
				self.payment_method_name = payment_methods[0].payment_method
		self.update_order()
		self.validate_product_quantity()


	def validate_product_quantity(self):
		if self.status == "Placed" and self.docstatus == 1:
			for item in self.order_item:
				quantity = frappe.db.get_value("Product", item.item,"stock")
				has_variants = frappe.db.get_value("Product",item.item,"has_variants")
				if quantity >= item.quantity and has_variants == 0:
					updated_quantity = quantity - item.quantity
					frappe.db.set_value(
											"Product",
											item.item,
											"stock",
											updated_quantity
										)
					frappe.db.commit()
				elif has_variants == 1:
					attr_id = update_variant_id(item.item, item.varaint_txt)
					ProductVariantCombination = DocType('Product Variant Combination')
					ProductAttributeOption = DocType('Product Attribute Option')

					query = (
						frappe.qb.from_(ProductVariantCombination)
						.join(ProductAttributeOption)
						.on(ProductVariantCombination.attribute_id == ProductAttributeOption.name)
						.select(ProductVariantCombination.stock, ProductVariantCombination.product_title, ProductVariantCombination.name)
						.where((ProductVariantCombination.attribute_id == attr_id) & 
							(ProductVariantCombination.parent == item.item))
						.limit(1)
					)
					variant_stock = query.run(as_dict=True)
					if variant_stock:
						variant_stock = variant_stock[0]
						if variant_stock.stock >= item.quantity:
							updated_quantity = variant_stock.stock - item.quantity
							frappe.db.set_value(
												"Product Variant Combination",
												variant_stock.name,
												"stock",
												updated_quantity
											)
							frappe.db.commit() 
					else:
						frappe.throw("Please Select varient for the item")
							
					

	def set_item_info(self,catalog_settings):
		subtotal = 0
		for item in self.order_item:
			subtotal = subtotal + (item.price*item.quantity)
		for item in self.order_item:
			item.weight = frappe.db.get_value("Product",item.item,"weight")
			item.ordered_weight = frappe.db.get_value("Product",item.item,"weight")
			if not item.item_name:
				item.item_name = frappe.db.get_value("Product",item.item,"item")
			if not item.amount:
				item.amount = item.price*item.quantity
			if item.attribute_ids:
				if not item.attribute_description:
					attributes_combination_text=get_attributes_combination_text(
																item.attribute_ids.replace("\\n","\n")
															)
					attr_html = ""
					if attributes_combination_text:
						attr_html = '<div class="cart-attributes">'
						attr_html_text = attributes_combination_text[0].combination_txt.split(',')
						for attr_html_txt in attr_html_text:
							attr_html += 	'<div class="attribute"><span class="attr-title">'+\
												attr_html_txt.split(':')[0]+'</span> : <span>'+\
												attr_html_txt.split(':')[1]+'</span> </div>'
						attr_html += "</div>"
					item.attribute_description = attr_html
					item.attribute_ids = item.attribute_ids.replace("\\n","\n")

			if not item.tax:
				tax_value = 0
				discount = 0
				if self.discount:
					price_weightage = item.amount / subtotal * 100
					price_weightage = math.ceil(price_weightage * 100) / 100
					new_discount = float(price_weightage)* float(self.discount) / 100
					new_discount = math.ceil(new_discount * 100) / 100
					discount = discount + new_discount
				item.d_amount = discount
				p_tax = frappe.db.get_value("Product",item.item,"tax_category")
				if p_tax:
					tax_template = frappe.get_doc('Product Tax Template',p_tax)
					if tax_template:
						total = 0
						total += flt(item.amount) if item.amount else 0
						if item.shipping_charges:
							total = flt(total) + flt(item.shipping_charges)
						if not catalog_settings.included_tax:
							total += flt(item.tax) if item.tax else 0
						if item.d_amount:
							total = flt(total) - flt(item.d_amount)
						if tax_template.tax_rates:
							for tax_rate in tax_template.tax_rates:
								if catalog_settings.included_tax:
									tax_value = flt(total) * tax_rate.rate / (100 + tax_rate.rate)
								else:
									tax_value = total * tax_rate.rate / 100
						item.tax = tax_value
	
	def set_customer_address(self):
		customer_info = frappe.get_doc("Customers",self.customer)
		self.set_default_address(customer_info)
	
	
	def set_default_address(self,customer_info):
		c_address = None
		if customer_info.table_6:
			c_address = customer_info.table_6[0]
		addresses = list(filter(lambda r: r.get('is_default') == 1, customer_info.table_6))
		if addresses:
			c_address = addresses[0]
		if c_address:
			self.address = c_address.address
			self.city = c_address.city
			self.country = c_address.country
			self.first_name = c_address.first_name
			self.last_name = c_address.last_name
			self.shipping_city = c_address.city
			self.shipping_country = c_address.country
			self.shipping_first_name = c_address.first_name
			self.landmark = c_address.landmark
			self.shipping_landmark = c_address.landmark
			self.shipping_last_name = c_address.last_name
			self.shipping_phone = c_address.phone
			self.phone = c_address.phone
			self.shipping_shipping_address = c_address.address
			self.shipping_zipcode = c_address.zipcode
			self.zipcode = c_address.zipcode
			self.state = c_address.state
			self.shipping_state = c_address.state
			self.latitude = c_address.latitude
			self.longitude = c_address.longitude


	def check_items(self):
		if self.owner:
			if not self.order_item or len(self.order_item) == 0:
				frappe.throw("Please choose items.")
				self.reload()
	
	
	def validate_price_quantity(self):
		if self.owner:
			if len(self.order_item) > 0:
				for row in self.order_item :
					if row.price <= 0 and row.quantity <= 0 :
						frappe.throw("Please Enter Price and Quantity.")
					if row.price <= 0 :
						frappe.throw("Please Enter Price.")
					if row.quantity <= 0 :
						frappe.throw("Please Enter Quantity.")
					if row.current_stock <= 0 :
						frappe.throw("Stock Quantity Not Available.")
					self.reload()
		return {
				"status":"Success"
			}
	
	
	def update_delivery_slot(self):
		if self.delivery_slot and self.delivery_date:
			slot = self.delivery_slot.split(",")
			start_time = frappe.utils.to_timedelta(slot[0])
			end_time = frappe.utils.to_timedelta(slot[1])
			if not frappe.db.get_all("Order Delivery Slot",filters = {
																		"order_date":self.delivery_date,
																		"order":self.name,
																		"from_time":start_time,
																		"to_time":end_time}):
				frappe.get_doc({
				"doctype":"Order Delivery Slot",
				"order":self.name,
				"order_date":self.delivery_date,
				"from_time":start_time,
				"to_time":end_time
				}).save(ignore_permissions=True)


	def check_attr_ids(self,item,attr_ids):
		ProductVariantCombination = DocType('Product Variant Combination')
		query = (
			frappe.qb.from_(ProductVariantCombination)
			.select(ProductVariantCombination.weight, ProductVariantCombination.sku, ProductVariantCombination.attribute_html)
			.where(
				(ProductVariantCombination.parent == item.item) &
				(ProductVariantCombination.attribute_id == item.attribute_ids)
			)
		)
		combination = query.run(as_dict=True)
		if combination:
			if combination[0].sku:
				item_sku = combination[0].sku
			attributes_combination_text = get_attributes_combination_text(attr_ids)
			attr_html = ""
			if attributes_combination_text:
				attr_html = '<div class="cart-attributes">'
				attr_html_text = attributes_combination_text[0].combination_txt.split(',')
				for attr_html_txt in attr_html_text:
					attr_html += '<div class="attribute"><span class="attr-title">' + attr_html_txt.split(':')[0] + \
									'</span> : <span>' + attr_html_txt.split(':')[1] + '</span> </div>'
				attr_html += "</div>"
			frappe.db.set_value(item.doctype,item.name,'attribute_description',attr_html)
			item.attribute_description = attr_html
			item_weight = combination[0].weight


	def update_order_doc_status(self, tax):
		if self.docstatus == 0:
			self.total_tax_amount = tax
			frappe.db.set_value(self.doctype,self.name,'total_tax_amount',tax)
			Order = DocType('Order')
			update_query = (
				frappe.qb.update(Order)
				.set(Order.total_tax_amount, self.total_tax_amount)
				.where(Order.name == self.name)
			)
			update_query.run()
			frappe.db.commit()
		else:
			self.total_tax_amount = tax
			frappe.db.set_value(self.doctype,self.name,'total_tax_amount',tax)
			frappe.db.commit()
		
		
	def shipping_tax_subtotal(self,subtotal):
		if self.shipping_method:
			shipping_method_name = frappe.db.get_value('Shipping Method', self.shipping_method, 'shipping_method_name')
			self.shipping_method_name = shipping_method_name
			frappe.db.set_value(self.doctype,self.name,'shipping_method_name',shipping_method_name)
		if self.tax_breakup and self.tax_breakup.find(' - shipping') != -1:
			delivery_tax = self.tax_breakup.split('\n')
			break_up = ''
			for t in delivery_tax:
				if t and t.find(' - shipping') == -1:
					break_up = break_up + t + '\n'
			self.tax_breakup = break_up
			if self.tax_json:
				tax_json = json.loads(self.tax_json)
				new_json = []
				for t in tax_json:
					if not t.get('is_shipping'):
						new_json.append(t)
				self.tax_json = json.dumps(new_json)
		shipping_charge_tax = self.shipping_charge_tax()
		self.order_subtotal = subtotal
		frappe.db.set_value(self.doctype,self.name,'order_subtotal',subtotal)
		return shipping_charge_tax


	def update_order(self):
		catalog_settings = frappe.get_single('Catalog Settings')
		order_settings = frappe.get_single('Order Settings')
		tax = subtotal = 0
		
		if self.order_item:
			self.set_item_info(catalog_settings)
			if self.order_item:
				for item in self.order_item:
					item_sku = frappe.db.get_value('Product',item.item,'sku')
					item_weight = frappe.db.get_value('Product',item.item,'weight')
					attr_ids = item.attribute_ids
					if item.attribute and not item.attribute_ids:
						attr_ids = item.attribute
						item.attribute_ids = item.attribute
					if attr_ids:
						self.check_attr_ids(item,attr_ids)

					if item_weight and int(item_weight) > 0:
						weight = item_weight
					else:
						weight = 0
					if self.docstatus==0:
						item.item_sku = item_sku
					else:
						frappe.db.set_value(item.doctype,item.name,'item_sku',item_sku)
					frappe.db.set_value(item.doctype,item.name,'weight',(weight*item.quantity))
					attr_image =''
					if item.attribute_ids:
						attr_ids = item.attribute_ids.split('\n')
						id_list = []
						for i in attr_ids:
							if i: id_list.append(i)
						ids = ",".join(['"' + x + '"' for x in id_list])
						ProductAttributeOption = DocType('Product Attribute Option')
						query = (
							frappe.qb.from_(ProductAttributeOption)
							.select('*')
							.where(ProductAttributeOption.parent == item.item)
							.where(ProductAttributeOption.name.isin(id_list))
						)
						options = query.run(as_dict=True)
						title = ''
						for op in options:
							if op.image_list:
								images = json.loads(op.image_list)
								if len(images) > 0:
									images = sorted(images, key = lambda x: x.get('is_primary'), reverse = True)
									attr_image = images[0].get('thumbnail')
							if op.product_title and op.product_title not in ['', '-']:
								title = op.product_title
						if title != '' and item.item_name != title:
							item.item_name = title
					
					ProductImage = DocType('Product Image')
					query = (
						frappe.qb.from_(ProductImage)
						.select(ProductImage.cart_thumbnail, ProductImage.list_image)
						.where(ProductImage.parent == item.item)
						.orderby(ProductImage.is_primary)
						.limit(1)
					)
					result = query.run(as_dict=True)
					if attr_image:
						if self.docstatus == 0:
							item.item_image = attr_image
						else:
							frappe.db.set_value(item.doctype,item.name,'item_image',attr_image)
					elif result and result[0].cart_thumbnail:
						if self.docstatus == 0:
							item.item_image = result[0].cart_thumbnail
						else:
							frappe.db.set_value(item.doctype,item.name,'item_image',result[0].cart_thumbnail)

					if not item.is_free_item:
						total = 0
						amount = 0
						# discount = 0
						# frappe.log_error("discount",self.discount)
						# if self.discount:
						# 	price_weightage = item.amount / subtotal * 100
						# 	price_weightage = math.ceil(price_weightage * 100) / 100
						# 	new_discount = float(price_weightage)* float(amount) / 100
						# 	new_discount = math.ceil(new_discount * 100) / 100
						# 	discount = discount + new_discount
						# item.d_amount = discount
						if self.docstatus==1:
							frappe.db.set_value(item.doctype,item.name,'amount',item.amount)
						total += flt(item.amount) if item.amount else 0
						if item.shipping_charges:
							total = flt(total) + flt(item.shipping_charges)
						if not catalog_settings.included_tax:
							total += flt(item.tax) if item.tax else 0
						if item.d_amount:
							total = flt(total) - flt(item.d_amount)
						if self.docstatus==0:
							item.t_amount = total
						else:
							frappe.db.set_value(item.doctype,item.name,'t_amount',total)
						tax = tax + (item.tax if item.tax else 0)
						subtotal = subtotal + (flt(item.price) * int(item.quantity))

		self.update_order_doc_status(tax)

		if not self.shipping_charges > 0:
			shippingcharge_res = calculate_shipping_charges(self)
			if shippingcharge_res:
				self.shipping_charges = shippingcharge_res.get("shipping_charges") if shippingcharge_res.get("shipping_charges") else 0
				frappe.db.set_value('Order', self.name, 'shipping_charges', shippingcharge_res.get("shipping_charges") if shippingcharge_res.get("shipping_charges") else 0)
		# else:
		# 	shippingcharge_res = calculate_shipping_charges(self)
		# 	if shippingcharge_res:
		# 		self.shipping_charges = shippingcharge_res.get("shipping_charges") if shippingcharge_res.get("shipping_charges") else 0
		# 		frappe.db.set_value('Order', self.name, 'shipping_charges', shippingcharge_res.get("shipping_charges") if shippingcharge_res.get("shipping_charges") else 0)
		self.shipping_tax_subtotal(subtotal)
		tax_template = None
		tax_val=0
		if not self.tax_breakup:
			tax_val = self.total_tax_amount
		if self.tax_breakup:
			tax_parts = self.tax_breakup.split('\n')
			for t in tax_parts:
				splits = t.split(' - ')
				if len(splits) > 3 and splits[3] and splits[3] == 'Excl. Tax':
					tax_val = tax_val + float(splits[2])
				if len(splits) > 3 and splits[3] and splits[3] == 'Incl. Tax':
					tax_val = tax_val + float(splits[2])
		if not self.discount:
			self.discount = 0

		if self.discount and self.discount > 0:
			temp_discount = str(self.discount).split('.')
			self.discount = math.ceil(self.discount * 100) / 100
		new_disount = 0
		if self.is_admin_order==1 and not self.discount>0:
			self.discount = 0
			new_disount = self.calculate_discount(order_settings)
			items_discount = self.calculate_items_discount()
			self.discount = self.discount + items_discount
		# self.total_tax_amount = tax_val
		frappe.db.set_value(self.doctype, self.name,'total_tax_amount', tax_val)
		frappe.db.set_value(self.doctype, self.name,'total_tax_amount', math.ceil(self.total_tax_amount * 100) / 100)
		frappe.db.set_value(self.doctype, self.name,'discount',self.discount)

		if not catalog_settings.included_tax:
			total_amount = self.order_subtotal - self.discount + self.shipping_charges + self.total_tax_amount + float(self.pickup_charge)
		else:
			total_amount = self.order_subtotal - self.discount + self.shipping_charges + float(self.pickup_charge)
		self.total_amount = total_amount
		if self.gift_card_amount:
			self.total_amount = self.total_amount - flt(self.gift_card_amount)
		self.order_subtotal_after_discount = float(self.order_subtotal) - float(self.discount)
		if self.docstatus == 1:
			frappe.db.set_value(self.doctype,self.name,'order_subtotal_after_discount',self.order_subtotal_after_discount)
		if not self.payment_gateway_charges:
			self.payment_charges()
		if self.checkout_attributes:
			for attr in self.checkout_attributes:
				self.total_amount += flt(attr.price_adjustment)
		if not self.barcode:
			self.check_barcode()
		if not self.qrcode:
			self.check_qrcode()
		self.total_amount = math.ceil(self.total_amount * 100) / 100
		
		if self.docstatus == 1:
			frappe.db.set_value(self.doctype,self.name,'total_amount',self.total_amount)
		if self.payment_status == "Paid":
			update_giftcard_payments(self.name,self.transaction_id)
			if self.giftcard_coupon_code:
				update_giftcard_status(self)
		if self.docstatus == 0:
			if self.outstanding_amount == 0:
				Order = DocType('Order')
				query = (
					frappe.qb.update(Order)
					.set(Order.docstatus, 1)
					.where(Order.name == self.name)
				)
				query.run()
				frappe.db.commit()
		self.check_outstanding_balance(self.total_amount,new_disount)
		workflow = frappe.db.get_all('Workflow', filters={'is_active': 1, 'document_type': 'Order'})
		if workflow:
			if self.workflow_state == 'Order Delivered':
				if self.driver:
					Order = DocType('Order')
					query = (
						frappe.qb.from_(Order)
						.select(Order.name)
						.where(Order.name != self.name)
						.where(Order.driver == self.driver)
						.where(Order.driver_status != 'Delivered')
						.where(Order.status.notin(['Completed', 'Cancelled']))
					)
					check_orders = query.run()

					if not check_orders:
						frappe.db.set_value('Drivers', self.driver, 'working_status', 'Available')
						frappe.db.commit()


	def get_discount_info(self,item,res):
		new_items_discount = 0
		discount_info = frappe.db.get_all("Discounts",
					filters = {"name":res.get('discount_rule')},
					fields = ['percent_or_amount','discount_percentage','discount_amount','discount_type'])

		discount_requirements = frappe.db.get_all("Discount Requirements",
								filters = {"parent":res.get('discount_rule')},
								fields = ['items_list','discount_requirement'])
		customer_list = []
		if discount_requirements:
			for dr in discount_requirements:
				if dr.discount_requirement == "Limit to customer":
					items = json.loads(dr.items_list)
					customer_list = [i.get('item') for i in items]
		
		is_allowed = 1
		
		if customer_list:
			if self.customer not in customer_list:
				is_allowed = 0
		if is_allowed:
			if discount_info[0].percent_or_amount == "Discount Percentage":
				d_amount = (flt(item.price) * flt(item.quantity))*flt(discount_info[0].discount_percentage)/100
			else:
				d_amount = round(flt(item.quantity)*flt(discount_info[0].discount_amount),2)
		new_items_discount = new_items_discount + d_amount
	def calculate_items_discount(self):
		from go1_commerce.go1_commerce.doctype.discounts.discounts \
		import get_product_discount

		new_items_discount = 0
		for item in self.order_item:
			d_amount = 0
			res = get_product_discount(frappe.get_doc("Product",item.item), item.quantity, item.price, 
									customer_id=self.customer, attribute_id=item.attribute_ids)
			if res:
				self.get_discount_info(item,res)
		return new_items_discount
	
	
	def calculate_discount(self, order_settings):
		new_disount = self.discount
		allowed_discount = 1
		customer_orders = frappe.db.get_all("Order",
								filters={"docstatus":1,"customer":self.customer,"name":("!=",self.name)})
		if not customer_orders:
			allowed_discount = 0
		if self.order_item and len(self.order_item) > 0 \
					and order_settings.allow_admin_to_edit_order == 1 and self.is_custom_discount == 0:
			data = self.check_order_item()
			check_subtotal_discount = data[0]
			discount_response = data[1]
			total_weight = data[2]
			self.check_sub_discount_info(check_subtotal_discount,discount_response,total_weight)
		return new_disount


	def check_sub_discount_info(self,check_subtotal_discount,discount_response,total_weight):
		if check_subtotal_discount:
			self.check_sub_total_discounut(total_weight)
		if discount_response and discount_response.get('discount_amount'):
			self.discount = math.ceil(float(discount_response.get('discount_amount')) * 100) / 100
			new_disount = discount_response.get('discount_amount')
			if self.docstatus == 1:
				frappe.db.set_value(self.doctype, self.name, 'discount', self.discount)
		discount_history = frappe.db.get_all("Discount Usage History",filters={'order_id':self.name})
		for x in discount_history:
			DiscountUsageHistory = DocType('Discount Usage History')
			query = (
				frappe.qb.from_(DiscountUsageHistory)
				.where(DiscountUsageHistory.name == x.name)
				.delete()
			)
			query.run()
		if discount_response and discount_response.get('discount_amount'):
			from go1_commerce.go1_commerce.v2.orders \
				import insert_discount_usage_history
			insert_discount_usage_history(
											self.name, 
											self.customer, 
											discount_response.get('discount_rule')
										)
		for x in self.order_item:
			if x.discount and x.is_free_item == 0:
				discount_usage_history = frappe.db.get_all("Discount Usage History",
														filters={"order_id":self.name},
														fields=['*'])
				if not discount_usage_history:
					from go1_commerce.go1_commerce.v2.orders \
					 import insert_discount_usage_history
					insert_discount_usage_history(
													self.name, 
													self.customer, 
													x.discount
												)
	
	
	def check_order_item(self):
		total_weight = 0
		for item in self.order_item:
			total_weight += flt(item.weight) if item.weight else 0
		check_subtotal_discount = 1
		discount_response = None
		if self.discount_coupon:
			discount_response = get_coupon_discount(
														self.name,
														self.order_subtotal,
														self.discount_coupon
													)
			if discount_response:
				if discount_response.get("status") != "failed":
					check_subtotal_discount = 0
					if discount_response.get("new_order_item"):
						child = discount_response.get("new_order_item")
						order_items = update_order_item(child)
						self.append("order_item",order_items)
				else:
					self.discount_coupon = None
					frappe.db.set_value('Order', self.name, 'discount_coupon', None)
					self.discount =  0
					new_disount = 0
					frappe.db.set_value(self.doctype,self.name,'discount',0)
		return [check_subtotal_discount,discount_response,total_weight]


	def check_sub_total_discounut(self, total_weight):
		from go1_commerce.go1_commerce.doctype.discounts.discounts \
		import get_order_subtotal_discount
		discount_response = get_order_subtotal_discount(
														self.order_subtotal, 
														self.customer,
														self.order_item, 
														total_weight,
														self.shipping_method,
														self.payment_method, 
														self.shipping_charges
													)
		if self.name and len(discount_response.get('products_list'))>0:
			check = next((x for x in self.order_item if (x.is_free_item == 1 \
									and x.discount == discount_response.get('discount_rule'))), None)
			if not check:
				for child in discount_response.get("products_list"):
					product = frappe.get_doc("Product", child.get('product'))
					new_order_item = {}
					new_order_item['amount'] = (product.price*child.get('quantity'))
					new_order_item['is_free_item'] = 1
					new_order_item['is_gift_card'] = 0
					new_order_item['is_rewarded'] = 0
					new_order_item['order_item_type'] = "Product"
					new_order_item['is_scanned'] = 0
					new_order_item['item_name'] = product.item
					new_order_item['item'] = child.get('product')
					new_order_item['item_image'] = product.image
					new_order_item['ordered_weight'] = product.weight
					new_order_item['price'] = product.price
					new_order_item['quantity'] = child.get('quantity')
					new_order_item['return_created'] = 0
					new_order_item['shipping_status'] = "Pending"
					new_order_item['shipping_charges'] = 0
					new_order_item['t_amount'] = (product.price*child.get('quantity'))
					new_order_item['tax'] = 0
					new_order_item['weight'] = product.weight
					order_item_ = order_items_list(new_order_item)
					self.append("order_item", order_item_)

	def update_status_history(self):
		prev_state = self.pre_status
		cur_state = self.status
		workflow = frappe.db.get_all('Workflow', filters={'is_active': 1, 'document_type': 'Order'})
		if workflow:
			cur_state = self.workflow_state
		frappe.db.set_value('Order', self.name, 'pre_status', cur_state)


	def payment_charges(self):
		if frappe.db.get_value('Payment Method', self.payment_method):
			payment = frappe.get_doc('Payment Method', self.payment_method)
			gateway_charges = 0
			if payment.use_additional_fee_percentage:
				gateway_charges = (flt(self.order_subtotal) - flt(self.discount) + flt(self.total_tax_amount) \
					+ flt(self.shipping_charges)) * flt(payment.additional_fee_percentage) / 100
			if payment.additional_charge:
				gateway_charges = flt(gateway_charges) + flt(payment.additional_charge)
			self.payment_gateway_charges = gateway_charges
		else:
			return "Payment method not get"
		
		
	def check_payment_reference(self):
		paid_amount = 0
		si = frappe.db.get_all("Sales Invoice",filters={"reference":self.name})
		if si:
			PaymentReference = DocType('Payment Reference')
			PaymentEntry = DocType('Payment Entry')
			query = (
				frappe.qb.from_(PaymentReference)
				.inner_join(PaymentEntry).on(PaymentEntry.name == PaymentReference.parent)
				.select(PaymentReference.allocated_amount)
				.where(
					PaymentReference.reference_doctype == 'Order',
					PaymentReference.reference_name == self.name,
					PaymentEntry.docstatus == 1,
					PaymentEntry.payment_type == 'Receive'
				)
			)
			payment_reference = query.run(as_dict=True)
			paid_amount += sum(round(flt(x.allocated_amount), 2) for x in payment_reference if x.allocated_amount > 0)
			if not payment_reference:
				if si:
					for sinv in si:
						PaymentReference = DocType('Payment Reference')
						PaymentEntry = DocType('Payment Entry')
						query = (
							frappe.qb.from_(PaymentReference)
							.inner_join(PaymentEntry).on(PaymentEntry.name == PaymentReference.parent)
							.select(PaymentReference.allocated_amount)
							.where(
								PaymentReference.reference_doctype == 'Sales Invoice',
								PaymentReference.reference_name == sinv.name,
								PaymentEntry.docstatus == 1,
								PaymentEntry.payment_type == 'Receive'
							)
						)
						payment_reference = query.run(as_dict=True)
						paid_amount += sum(round(flt(x.allocated_amount), 2) for x in payment_reference if x.allocated_amount > 0)
					
					
	def check_outstanding_balance(self, total_amount,discount_new):
		paid_amount = 0
		outstanding_amount = 0
		if self.outstanding_amount != 0:
			outstanding_amount = round(flt(total_amount), 2)
		payment_reference = frappe.db.get_all('Payment Reference', 
										filters = {
													'reference_doctype': 'Order', 
													'reference_name': self.name, 
													'docstatus': 1
												}, 
										fields = ['allocated_amount'])
		if payment_reference:
			paid_amount = sum(round(flt(x.allocated_amount), 2) for x in payment_reference if x.allocated_amount > 0)
		if not payment_reference:
			self.check_payment_reference()
		discount_amt = 0
		if self.paid_using_wallet and self.paid_using_wallet > 0:
			paid_amount += round(flt(self.paid_using_wallet), 2)
			discount_amt += flt(self.paid_using_wallet)
		if paid_amount > 0 and self.total_amount >= paid_amount:
			outstanding_amount = flt(self.total_amount) - round(flt(paid_amount), 2)
		self.order_subtotal_after_discount = float(self.order_subtotal) - float(discount_new) - float(discount_amt)
		if flt(outstanding_amount) == flt(self.total_amount) and flt(outstanding_amount) > 0:
			if (self.payment_status == "Authorized") or (self.payment_status == 'Paid' and self.transaction_id):
				pass
			else:
				self.payment_status = 'Pending'
		elif flt(outstanding_amount) == flt(0):
			self.payment_status = 'Paid'
			if frappe.db.get_value(self.doctype, self.name, 'docstatus') == 0:
				frappe.db.set_value(self.doctype,self.name,'docstatus', 1)
				frappe.db.commit()
		else:
			self.payment_status = 'Partially Paid'
		self.outstanding_amount = outstanding_amount
		if paid_amount !=0:
			self.paid_amount = paid_amount
		if self.docstatus == 1 and self.status != "Returned":
			frappe.db.set_value(self.doctype,self.name,'outstanding_amount', self.outstanding_amount)
			frappe.db.set_value(self.doctype,self.name,'paid_amount', self.paid_amount)
			frappe.db.set_value(self.doctype,self.name,'payment_status', self.payment_status)
			frappe.db.commit()


	def shipping_charge_tax(self):
		tax_template = None
		tax = charge=0
		text = ''
		calculative_amount = self.shipping_charges
		catalog_settings = frappe.get_single('Catalog Settings')
		if catalog_settings.shipping_is_taxable and catalog_settings.shipping_tax_class:
			tax_template = catalog_settings.shipping_tax_class
			text = 'Shipping'
		tax_splitup = []
		if self.shipping_method_name == 'Delivery':
			self.pickup_charge = 0
		if tax_template:
			tax_type = ''
			if catalog_settings.shipping_is_taxable:
				if catalog_settings.shipping_price_includes_tax:
					tax_type = "Incl. Tax"
				else:
					tax_type = "Excl. Tax"
			tax_info = frappe.get_doc('Product Tax Template', tax_template)
			for item in tax_info.tax_rates:


				if catalog_settings.shipping_price_includes_tax:
					if charge>0 :
						calculative_amount +=charge
					tax_val = float(calculative_amount) * item.rate / (100 + item.rate)
				else:
					tax_val = float(calculative_amount) * float(item.rate) / 100
				cur_tax = next((x for x in tax_splitup if x['type'] == item.tax),None)
				if cur_tax:
					for it in tax_splitup:
						if it['type'] == item.tax:
							it['amount'] = it['amount'] + tax_val
				else:
					tax_splitup.append({
										'type': item.tax,
										'rate': item.rate,
										'amount': tax_val,
										'account': item.get('account_head'), 
										'tax_type': tax_type, 
										'is_shipping': 1
									})
				if catalog_settings.shipping_price_includes_tax==0:
					tax = float(tax) + float(tax_val)
				else:
					tax = float(tax)
			self.total_tax_amount = self.total_tax_amount + tax
			shipping = frappe._('{0}').format(text)
			if not self.tax_breakup:
				self.tax_breakup = ''
			else:
				breakup = self.tax_breakup.split('\n')
				new_breakup = ''
				for br in breakup:
					part = br.split(' - ')
					if len(part) > 4 and part[4] == 'shipping':
						pass
					else:
						new_breakup += br + '\n'
				self.tax_breakup = new_breakup
			tax_json = json.loads(self.tax_json) if self.tax_json else []
			for x in tax_splitup:
				tax_json.append(x)
				self.tax_breakup += '{0} - {1}% - {2} - {3} - shipping\n'.format(
																	(x['type'] + '(' + shipping + ')'),
																	str(x['rate']), str(x['amount']), 
																	tax_type
																)
			
			text = 'Shipping'
			self.tax_json = json.dumps(tax_json)
			return tax


	def get_delivery_timeslot(self, name):
		if self.name:
			delivery_slot = []
			check_delivery_slot = frappe.db.get_all('Order Delivery Slot', 
														filters = {'order': name},
														fields = [
																	'order_date', 
																	'from_time', 
																	'to_time', 
																	'product_category'
																])
			if check_delivery_slot:
				for deli_slot in check_delivery_slot:
					category = ''
					if deli_slot.product_category:
						category = frappe.get_value('Product Category', deli_slot.product_category, 'category_name')
					from_time = datetime.strptime(str(deli_slot.from_time), '%H:%M:%S').time()
					to_time = datetime.strptime(str(deli_slot.to_time), '%H:%M:%S').time()
					delivery_slot.append({
						'delivery_date': deli_slot.order_date.strftime('%b %d, %Y'),
						'from_time': from_time.strftime('%I:%M %p'),
						'to_time': to_time.strftime('%I:%M %p'),
						'category': category
						})
			return delivery_slot


	def check_barcode(self):
		enable_barcode = get_settings_value('Order Settings', 'generate_barcode_for_order')
		if enable_barcode:
			import barcode
			from barcode.writer import ImageWriter
			EAN = barcode.get_barcode_class('code128')
			ean = EAN(self.name, writer=ImageWriter())
			fullname = ean.save(self.name)
			filename = randomStringDigits(18)
			path = 'public/files/{filename}.png'.format(filename=filename)
			touch_file(os.path.join(frappe.get_site_path(), path))
			f = open(os.path.join(frappe.get_site_path(), path), 'wb')
			ean.write(f)
			self.barcode = "/files/" + filename + ".png"


	def check_qrcode(self):
		try:
			enable_qr_code = get_settings_value('Order Settings', 'generate_qrcode_for_order')
			if enable_qr_code:
				import qrcode
				qr = qrcode.QRCode(version = 1, error_correction = qrcode.constants.ERROR_CORRECT_L,
									box_size = 10, border = 4)
				qr.add_data(self.name)
				qr.make(fit=True)
				img = qr.make_image(fill_color="black", back_color="white")
				filename = randomStringDigits(18)
				path = 'public/files/{filename}.png'.format(filename=filename)
				touch_file(os.path.join(frappe.get_site_path(),path))
				img.save(os.path.join(frappe.get_site_path(),path))
				self.qrcode = "/files/" + filename + ".png"
		except Exception:
			frappe.log_error("Erroe in doctype.order.check_qrcode", frappe.get_traceback())


	def update_items_stock(self):
		try:
			if self.name:
				OrderItem = DocType('Order Item')
				Product = DocType('Product')
				query = (
					frappe.qb.from_(OrderItem)
					.inner_join(Product).on(OrderItem.item == Product.name)
					.select('*', Product.inventory_method, Product.stock)
					.where(OrderItem.parent == self.name)
					.orderby(OrderItem.idx)
				)
				items = query.run(as_dict=True)
				if items:
					for item in items:
						has_variant = frappe.db.get_value("Product",item.item,"has_variants")
						if not has_variant:
							if item.inventory_method == "Track Inventory":
								stock = int(item.stock) + int(item.quantity)
								frappe.db.set_value('Product', item.item, 'stock', stock)
								
							elif item.inventory_method == "Track Inventory By Product Attributes":
								variant_stock_update(item)
						else:
							variant_stock_update(item)
		except Exception:
			frappe.log_error("Error in doctype.order.update_items_stock", frappe.get_traceback())


	def on_submit(self):
		if not self.order_item or len(self.order_item) <= 0:
			frappe.throw("Please select atleast one item to create order.")
		order_settings = frappe.get_single('Order Settings')
		invoice_state = "Placed"
		invoice_creation_states = frappe.db.get_all("Auto Invoice Creation Status",
															fields = ['status'],
															filters = {"parent":order_settings.name})
		if self.status in invoice_creation_states and order_settings.enable_invoice == 1 \
					and order_settings.automate_invoice_creation == 1:
			tran_name = frappe.db.get_value("Sales Invoice",{"reference":self.name})
			if not tran_name:
				make_invoice(self.name)
		
		frappe.enqueue('go1_commerce.go1_commerce.doctype.order.order.clear_guest_user_details',
						order_id = self.name)
	def on_cancel(self):
		frappe.log_error("STATUSS",self.status)
		self.cancel_order_detail()
		for item in self.order_item:
			quantity = frappe.db.get_value("Product", item.item,"stock")
			updated_quantity = quantity + item.quantity
			frappe.log_error("updated_quantity",updated_quantity)
			frappe.db.set_value(
									"Product",
									item.item,
									"stock",
									updated_quantity
								)
			frappe.db.commit()


	def update_shipmentbag(self):
		shopping_settings = frappe.get_single('Shopping Cart Settings')
		if self.is_shipment_bag_item == 1 and shopping_settings.enable_shipment_bag == 1 \
						and self.customer_type == "Customers":
			if frappe.db.exists("Shipment Bag",{"customer": self.customer, "is_paid":0}):
				data_name = frappe.db.get_value("Shipment Bag",{"customer": self.customer, "is_paid":0})
				shipment= frappe.get_doc("Shipment Bag", data_name)
				shipment.append('items', {"order_id":self.name, "shipping_charge": self.shipment_charge})
				shipment.save(ignore_permissions = True)
			else:
				shipment= frappe.new_doc("Shipment Bag")
				shipment.customer = self.customer
				shipment.customer_name = self.customer_name
				shipment.append('items', {"order_id":self.name, "shipping_charge": self.shipment_charge})
				shipment.insert(ignore_permissions = True)


	def get_item_image(self, item_code):
		ProductImage = DocType('Product Image')
		query = (
			frappe.qb.from_(ProductImage)
			.select(ProductImage.cart_thumbnail, ProductImage.list_image)
			.where(ProductImage.parent == item_code)
			.orderby(ProductImage.is_primary, order=Order.desc)
			.limit(1)
		)
		result = query.run(as_dict=True)
		if result and result[0].cart_thumbnail:
			return result[0].cart_thumbnail
		elif result and result[0].list_image:
			return result[0].list_image
		else:
			default_image = get_settings_value('Media Settings', 'default_image')
			if default_image:
				return default_image
			return ""


	def adjust_product_inventory(self):
		if self.order_item:
			for item in self.order_item:
				if item.order_item_type == 'Product' and frappe.db.exists("Product", item.item):
					product_info=frappe.get_doc('Product',item.item)
					if product_info.inventory_method=='Track Inventory':
						if int(product_info.stock)>=int(item.quantity):
							product_info.stock=product_info.stock-item.quantity
							frappe.db.set_value('Product',product_info.name,'stock',product_info.stock)
						else:
							frappe.throw("Product stock quantity should be greater than item quantity.")
					elif product_info.inventory_method=='Track Inventory By Product Attributes':
						from go1_commerce.go1_commerce.v2.orders \
						import get_attributes_json
						attribute_id = get_attributes_json(item.attribute_ids)
						check = next((x for x in product_info.variant_combination if x.attributes_json == attribute_id),None)
						if check:
							if check.stock > 0:
								if int(check.stock)>=int(item.quantity):
									check.stock = check.stock - float(item.quantity)
									frappe.db.set_value('Product Variant Combination', check.name, 'stock', check.stock)
								else:
									frappe.throw("Product stock quantity should be greater than item quantity.")

	def on_update_after_submit(self):
		self.update_status_history()
		wallet_settings = frappe.get_single('Wallet Settings')
		if wallet_settings.enable_customer_wallet and wallet_settings.customer_auto_debit and \
								(self.is_admin_order==1 or self.owner!=self.customer_email):
			self.auto_debit_wallet()
		self.update_order()
		order_settings = frappe.get_single('Order Settings')
		allow = False
		if self.get('__islocal') or self.get('__unsaved'):
			allow = True
		invoice_creation_states = frappe.db.get_all("Auto Invoice Creation Status",
													fields = ['status'],
													filters = {"parent":order_settings.name})
		if self.status in invoice_creation_states and order_settings.enable_invoice == 1 \
				and order_settings.automate_invoice_creation == 1:
			tran_name = frappe.db.get_value("Sales Invoice",{"reference":self.name})
			if not tran_name:
				make_invoice(self.name)
		if self.status == 'Cancelled':
			frappe.log_error("Cancelled")
			self.cancel_order_detail()
			self.update_items_stock()

		if self.status == 'Completed' and self.payment_status == 'Paid':
			self.check_cashback()
		self.reload()
		if self.payment_status == "Paid":
			all_trans = frappe.db.get_all('Wallet Transaction',
										filters={
													'order_id':self.name, 
													"status":"Pending",
													"transaction_type" :"Receive"
												})
			for item in all_trans:
				frappe.db.set_value('Wallet Transaction', item.name, 'status', 'Credited')


	def check_wallet_info(self,wallet_info):
		if wallet_info[0].current_wallet_amount>0:
			wallet_amount = wallet_info[0].current_wallet_amount
			amount = 0
			order_payment_status = 'Pending'
			if flt(wallet_amount) >= flt(self.total_amount):
				amount = flt(self.total_amount)
				order_payment_status = 'Paid'
			else:
				amount = flt(wallet_amount)
				order_payment_status = 'Partially Paid'
			wallet_trans_entry = frappe.get_doc({
													"doctype":"Wallet Transaction",
													"reference":"Order",
													"order_type":"Order",
													"order_id":self.name,
													"transaction_date":now(),
													"total_value":amount,
													"amount":amount,
													"is_settlement_paid":0,
													"is_fund_added":1,
													"notes":"Against Order:"+self.name,
													"party_type":"Customers",
													"party":self.customer,
													"transaction_type":"Pay",
													"status":"Debited"
													})
			wallet_trans_entry.submit()
			self.paid_using_wallet = amount
			self.paid_amount = amount
			frappe.db.set_value("Order",self.name,"paid_using_wallet",amount)
			frappe.db.set_value("Order",self.name,"paid_amount",amount)
			frappe.db.commit()


	def auto_debit_wallet(self):
		wallet_transactions = frappe.db.get_all("Wallet Transaction",
												filters={"order_id":self.name,"docstatus":1})
		if wallet_transactions:
			w_transaction_doc = frappe.get_doc("Wallet Transaction",wallet_transactions[0].name)
			w_transaction_doc.cancel()
		from go1_commerce.go1_commerce.v2.orders \
			import wallet_details
		wallet_info = wallet_details(self.customer)
		if wallet_info:
			self.check_wallet_info(wallet_info)


	def update_coupon_discount(self,cart_items):
		total_weight = 0
		for item in self.order_item:
			total_weight += flt(item.weight) if item.weight else 0
		from go1_commerce.go1_commerce.doctype.discounts.discounts \
		import get_coupon_code
		response = get_coupon_code(
									self.discount_coupon, 
									self.order_subtotal, 
									self.customer, 
									cart_items, 
									None,
									shipping_method = self.shipping_method, 
									payment_method = self.payment_method, 
									website_type = None, 
									total_weight = total_weight,
									shipping_charges = self.shipping_charges
								)
		
		
	def cancel_order_detail(self):
		if self.name and self.paid_using_wallet and int(self.paid_using_wallet) > 0:
			tran_name = frappe.db.get_value("Wallet Transaction",{
																	"order_id":self.name,
																	"order_type":"Order"
																})
			if tran_name:
				wall = frappe.get_doc("Wallet Transaction", tran_name)
				wall.docstatus = 2
				wall.save(ignore_permissions=True)
		if self.outstanding_amount == self.total_amount:
			frappe.db.set_value("Order", self.name, "outstanding_amount", 0)
			frappe.db.set_value("Order", self.name, "payment_status", "Cancelled")


	def check_order_delivery(self):
		orderDelivery=frappe.db.get_all('Order Delivery',filters={'order_id':self.name})
		if not orderDelivery:
			from go1_commerce.go1_commerce.v2.orders\
				import notify_drivers
			notify_drivers(self.name)


	def check_cashback(self):
		from go1_commerce.go1_commerce.doctype.discounts.discounts \
		import update_customer_wallet
		update_customer_wallet(self)


def order_items_list(new_order_item):
	order_item = {
					"item":new_order_item['item'], 
					"amount":new_order_item['amount'],
					"is_free_item":new_order_item['is_free_item'],
					"is_gift_card":new_order_item['is_gift_card'],
					"is_rewarded":new_order_item['is_rewarded'],
					"order_item_type":new_order_item['order_item_type'],
					"is_scanned":new_order_item['is_scanned'],
					"item_name":new_order_item['item_name'], 
					"item_image":new_order_item['item_image'],
					"ordered_weight":new_order_item['ordered_weight'],
					"price": new_order_item['price'], 
					"quantity":new_order_item['quantity'],
					"return_created":new_order_item['return_created'], 
					"shipping_status":new_order_item['shipping_status'],
					"shipping_charges":new_order_item['shipping_charges'],
					"t_amount":new_order_item['t_amount'], 
					"tax":new_order_item['tax'], 
					"weight":new_order_item['weight']
				}
	return order_item


def update_order_item(child):
	order_item = {
					"amount":child.amount, 
					"is_free_item":child.is_free_item,
					"is_gift_card":child.is_gift_card,
					"is_rewarded":child.is_rewarded,
					"order_item_type":child.order_item_type, 
					"is_scanned":child.is_scanned,
					"item_name":child.item_name, 
					"item_image":child.item_image, 
					"ordered_weight":child.ordered_weight,
					"price": child.price, 
					"quantity":child.quantity, 
					"return_created":child.return_created,
					"shipping_status":child.shipping_status, 
					"shipping_charges":child.shipping_charges,
					"t_amount":child.t_amount, 
					"tax":child.tax, "weight":child.weight, 
					"discount_coupon":child.discount_coupon
				}
	return order_item


def calculate_shipping_charges(doc):
	shipping_method = doc.shipping_method
	subtotal = doc.order_subtotal
	shipping_addr = {
						"shipping_city":doc.shipping_city, 
						"shipping_country":doc.shipping_country,
						"shipping_shipping_address": doc.shipping_shipping_address, 
						"shipping_state":doc.shipping_state,
						"shipping_zipcode":doc.shipping_zipcode
					}
	items = doc.order_item
	catalog_settings = frappe.get_single('Catalog Settings')
	ShippingRateMethod = DocType('Shipping Rate Method')
	query = (
		frappe.qb.from_(ShippingRateMethod)
		.select(
			ShippingRateMethod.name.as_('id'),
			ShippingRateMethod.shipping_rate_method.as_('name')
		)
		.where(ShippingRateMethod.is_active == 1)
	)
	shipping_rate_method = query.run(as_dict=True)
	return calculate_shipping_charges_method(
												items,
												catalog_settings,
												shipping_rate_method,
												shipping_method, 
												shipping_addr, 
												subtotal
											)

def calculate_shipping_charges_method(items,catalog_settings,shipping_rate_method,shipping_method, 
									shipping_addr,subtotal):
	shipping_charges = 0
	if shipping_rate_method:
		if shipping_rate_method[0].name == 'Shipping By Total':
			shipping_charges = calculate_shipping_charges_by_total(
																	shipping_method,
																	shipping_rate_method,
																	items
																)
		if shipping_rate_method[0].name == 'Fixed Rate Shipping':
			shipping_charges = calculate_multi_vendor_shipping_charges(
																		shipping_method, 
																		shipping_addr, 
																		subtotal, 
																		items
																	)
		if shipping_rate_method[0].name == 'Shipping By Weight':
			shipping_charges = calculate_shipping_charges_by_weight(
																		shipping_method,
																		shipping_rate_method,
																		items
																	)
		if shipping_rate_method[0].name == 'Shipping By Distance':
			shipping_charges = calculate_shipping_charges_by_distance(
																		shipping_method, 
																		shipping_addr, 
																		shipping_rate_method, 
																		items
																	)
		if shipping_rate_method[0].name == 'Shipping By Distance and Total':
			shipping_charges = calculate_shipping_charges_by_distance_and_total(
																				shipping_method, 
																				shipping_addr, 
																				shipping_rate_method, 
																				subtotal, items
																			)
	tax = tax_percent = 0
	if shipping_charges is not None and shipping_charges > 0:
		if catalog_settings.shipping_is_taxable == 1 and catalog_settings.shipping_tax_class != '':
			if catalog_settings.shipping_tax_class:
				tax_template = frappe.get_doc('Product Tax Template',
							catalog_settings.shipping_tax_class)
				for item in tax_template.tax_rates:
					tax_percent = tax_percent + float(item.rate)
					if catalog_settings.shipping_price_includes_tax == 1:
						tax = tax + round(shipping_charges *
							item.rate / (100 + item.rate), 2)
					else:
						tax = tax + round(float(shipping_charges) *
							float(item.rate) / 100, 2)
	return {
			'shipping_charges': shipping_charges,
			'tax_rate': tax,
			'item_tax': 0,
			'tax_percent': tax_percent,
			'status':'Success'
			}



def make_invoice(source_name, target_doc = None):
	make_sales_invoice(
						source_name, 
						target_doc = target_doc, 
						submit = True
					)



def calculate_shipping_charges_by_total(shipping_method, shipping_rate_method, items):
	total_shipping_charges = 0
	total_order_amount = 0
	for item_list in items:
		if item_list.is_free_item == 0:
			item_amount = round(flt(item_list.amount), 2)
			total_order_amount += item_amount

	if shipping_rate_method:
		ShippingByTotalCharges = DocType('Shipping By Total Charges')
		ShippingRateMethod = DocType('Shipping Rate Method')
		query = (
			frappe.qb.from_(ShippingByTotalCharges)
			.inner_join(ShippingRateMethod)
			.on(ShippingRateMethod.name == ShippingByTotalCharges.parent)
			.select(
				ShippingByTotalCharges.shipping_method,
				ShippingByTotalCharges.use_percentage,
				ShippingByTotalCharges.charge_percentage,
				ShippingByTotalCharges.charge_amount,
				ShippingByTotalCharges.order_total_from,
				ShippingByTotalCharges.order_total_to,
				ShippingRateMethod.name
			)
			.where(ShippingByTotalCharges.shipping_method == frappe.qb.Param('shipping_method'))
			.orderby(ShippingByTotalCharges.idx,order=Order.desc)
		)
		shipping_charges_list = query.run(as_dict=True, params={"shipping_method": shipping_method})
		for charge in shipping_charges_list:
			if charge.get('order_total_from') <= total_order_amount < charge.get('order_total_to'):
				if charge.get('use_percentage') == 1:
					total_shipping_charges = (total_order_amount * charge.get('charge_percentage')) / 100
				else:
					total_shipping_charges = charge.charge_amount
				return total_shipping_charges
		last_charge = shipping_charges_list[-1]
		total_shipping_charges = last_charge.charge_amount
	return total_shipping_charges



def calculate_shipping_charges_by_weight(shipping_method, shipping_rate_method, items):
	weight_shipping_charges = 0
	weight_order_amount = 0
	for item_list in items:
		if item_list.is_free_item == 0:
			item_weight = round(flt(item_list.weight), 2)
			weight_order_amount += item_weight

	if shipping_rate_method:
		ShippingByWeightCharges = DocType('Shipping By Weight Charges')
		ShippingRateMethod = DocType('Shipping Rate Method')
		query = (
			frappe.qb.from_(ShippingByWeightCharges)
			.inner_join(ShippingRateMethod)
			.on(ShippingRateMethod.name == ShippingByWeightCharges.parent)
			.select(
				ShippingByWeightCharges.shipping_method,
				ShippingByWeightCharges.charge_amount,
				ShippingByWeightCharges.use_percentage,
				ShippingByWeightCharges.charge_percentage,
				ShippingByWeightCharges.order_weight_from,
				ShippingByWeightCharges.order_weight_to,
				ShippingRateMethod.name
			)
			.where(ShippingByWeightCharges.shipping_method == frappe.qb.Param('shipping_method'))
			.orderby(ShippingByWeightCharges.idx, order=Order.desc)
		)
		shipping_charges_list = query.run(as_dict=True, params={"shipping_method": shipping_method})
		for charge in shipping_charges_list:
			if charge.get('order_weight_from') <= weight_order_amount < charge.get('order_weight_to'):
				if charge.use_percentage == 1:
					weight_shipping_charges = (weight_order_amount * charge.charge_percentage) / 100
				else:
					weight_shipping_charges = charge.charge_amount
				return weight_shipping_charges
		last_charge = shipping_charges_list[-1]
		weight_shipping_charges = last_charge.charge_amount
		return weight_shipping_charges


def calculate_shipping_charges_by_distance(shipping_method, shipping_addr, shipping_rate_method, items):
	hts = ""
	shipping_charges = 0
	if items and items == 1:
		shipping_charges += additional_shipping_cost * item.get('quantity')
	else:
		if items:
			for item in items:
				(enable_shipping, free_shipping,
				additional_shipping_cost) = frappe.db.get_value(
					'Product', item.item, [ 
											'enable_shipping', 
											'free_shipping', 
											'additional_shipping_cost'
										])
				if enable_shipping == 1 and free_shipping == 0:
					shipping_charges += additional_shipping_cost
	business_list = frappe.db.get_all("Business", fields=["*"])
	if business_list:
		business_info = frappe.get_doc('Business', business_list)
		destination = ''
		destination += ', ' + business_info.city + ', ' + business_info.state + ' ' + business_info.country
		if business_info.zipcode:
			destination += ' - ' + business_info.zipcode
		if destination.find('#') > -1:
			destination = destination.replace('#', '')
		source = ''
		source += shipping_addr.get("shipping_shipping_address") + ', '
		source += shipping_addr.get("shipping_city") + ', '
		source += shipping_addr.get("shipping_state") + ' '
		source += shipping_addr.get("shipping_zipcode")
		source += ', ' + shipping_addr.get("shipping_country")
		if source.find('#') > -1:
			source = source.replace('#', '')
		result = get_geodistance(source, destination)
		hts += " result: "+str(result)+"\n"
		distance = 0
		if result['rows'][0]['elements'][0]['status'] != 'ZERO_RESULTS':
			shipping_rate_method = frappe.db.get_all("Shipping Rate Method", fields=["*"])
			if shipping_rate_method[0].distance_unit == 'Kilometers':
				distance = result['rows'][0]['elements'][0]['distance']['value'] * 0.001 * 0.621371
			else:
				distance = result['rows'][0]['elements'][0]['distance']['value'] * 0.001
		distance = round(distance, 2)
		hts += " distance: "+str(distance)+"\n"
		hts += " shipping_method: "+str(	shipping_method)+"\n"
		ShippingChargesByDistance = DocType('Shipping Charges By Distance')
		query = (
			frappe.qb.from_(ShippingChargesByDistance)
			.select(
				ShippingChargesByDistance.charge_amount,
				ShippingChargesByDistance.use_percentage,
				ShippingChargesByDistance.charge_percentage,
				ShippingChargesByDistance.from_distance,
				ShippingChargesByDistance.to_distance
			)
			.where(
				ShippingChargesByDistance.shipping_method == frappe.qb.Param('shipping_method'),
				ShippingChargesByDistance.from_distance <= frappe.qb.Param('distance'),
				ShippingChargesByDistance.to_distance >= frappe.qb.Param('distance')
			)
		)
		shipping_charges_list = query.run(as_dict=True, params={'distance': distance, 'shipping_method': shipping_method})
		if shipping_charges_list:
			if shipping_charges_list[0].use_percentage == 1:
				if items:
					shipping_charges += float(items[0].t_amount) * shipping_charges_list[0]\
										.charge_percentage / 100
			else:
				shipping_charges += float(shipping_charges_list[0].charge_amount)
	return shipping_charges



def calculate_shipping_charges_by_distance_and_total(shipping_method, shipping_addr, shipping_rate_method, 
														subtotal, items):
	shipping_charges = 0
	if items:
		for item in items:
			product_weight, enable_shipping, free_shipping, additional_shipping_cost, tracking_method = \
				frappe.db.get_value('Product', item.item, [
															'weight', 
															'enable_shipping', 
															'free_shipping', 
															'additional_shipping_cost', 
															'inventory_method'
														])
			if enable_shipping == 1 and free_shipping == 0:
				shipping_charges += additional_shipping_cost
	business_list = frappe.db.get_all("Business", fields=["*"])
	if business_list:
		destination = ''
		business_info = frappe.get_doc('Business', business_list)
		if business_info.latitude and business_info.longitude:
			destination = str(business_info.latitude) + ', ' + str(business_info.longitude)
		else:
			destination = "{}, {}, {}".format(business_info.address,
												business_info.city, business_info.state)
			if business_info.zipcode:
				destination += ' - ' + business_info.zipcode
			if '#' in destination:
				destination = destination.replace('#', '')
		source = ''
		source += shipping_addr.get("shipping_shipping_address") + ', ' + shipping_addr.get("shipping_city") + ', '\
					+ shipping_addr.get("shipping_state") + ' ' + shipping_addr.get("shipping_zipcode")\
					+ ', ' + shipping_addr.get("shipping_country")
		if shipping_addr.get("shipping_country"):
			source += ', ' + shipping_addr["shipping_country"]
		result = get_geodistance(source, destination)
		distance = 0
		if result['rows'][0]['elements']:
			if result['rows'][0]['elements'][0]['status'] != 'ZERO_RESULTS':
				shipping_rate_method = frappe.db.get_all("Shipping Rate Method", fields=["*"])
				if shipping_rate_method[0].distance_unit == 'Kilometers':
					distance = result['rows'][0]['elements'][0]['distance']['value'] * 0.001 * 0.621371
				else:
					distance = result['rows'][0]['elements'][0]['distance']['value'] * 0.001
		distance = round(distance, 2)
		ShippingCharges = DocType('Shipping Charges By Distance and Total')
		query = (
			frappe.qb.from_(ShippingCharges)
			.select(
				ShippingCharges.charge_amount,
				ShippingCharges.use_percentage,
				ShippingCharges.charge_percentage,
				ShippingCharges.from_distance,
				ShippingCharges.to_distance,
				ShippingCharges.order_total_from,
				ShippingCharges.order_total_to
			)
			.where(
				ShippingCharges.shipping_method == frappe.qb.Param('shipping_method'),
				ShippingCharges.from_distance <= frappe.qb.Param('distance'),
				ShippingCharges.to_distance >= frappe.qb.Param('distance'),
				ShippingCharges.order_total_from <= frappe.qb.Param('subtotal'),
				ShippingCharges.order_total_to >= frappe.qb.Param('subtotal')
			)
		)
		shipping_charges_list = query.run(as_dict=True, params={
			'shipping_method': shipping_method,
			'distance': distance,
			'subtotal': subtotal
		})
		if shipping_charges_list:
			shipping_charges = shipping_charges+shipping_charges_list[0].charge_amount
	return  shipping_charges


def calculate_multi_vendor_shipping_charges(shipping_method, shipping_addr, subtotal, items):
	from go1_commerce.go1_commerce.v2.orders \
		import get_attributes_json
	shipping_charges_list = []
	ShippingRateMethod = DocType('Shipping Rate Method')
	query = (
		frappe.qb.from_(ShippingRateMethod)
		.select('*')
	)
	shipping_rate_methods = query.run(as_dict=True)
	shipping_mapped_rate_method_check = shipping_rate_methods[0]
	order_total = 0
	weight = 0
	shipping_charges = 0
	for item in items:
		(product_weight, enable_shipping, free_shipping, additional_shipping_cost, tracking_method,
		has_variants) = frappe.db.get_value('Product',item.get('item'),
												['weight',
												'enable_shipping',
												'free_shipping',
												'additional_shipping_cost',
												'inventory_method',
												'has_variants'])
		if enable_shipping == 1 and free_shipping == 0:
			citem = item
			if citem.get('attribute_ids') and has_variants == 1:
				attribute_id = get_attributes_json(citem.get('attribute_ids'))
				ProductVariantCombination = DocType('Product Variant Combination')
				query = (
					frappe.qb.from_(ProductVariantCombination)
					.select('weight')
					.where(ProductVariantCombination.parent == citem.get('item'))
					.where(ProductVariantCombination.attributes_json == attribute_id)
				)
				combination_weight = query.run(as_dict=True)
				if combination_weight:
					weight += combination_weight[0].weight * citem.get('quantity')
					if additional_shipping_cost > 0:
						shipping_charges += additional_shipping_cost * citem.get('quantity')
					order_total = order_total + float(citem.get('amount'))
			else:
				weight += product_weight * citem.get('quantity')
				if additional_shipping_cost > 0:
					shipping_charges += additional_shipping_cost * citem.get('quantity')
				order_total = order_total + float(citem.get('amount'))
				if citem.get('attribute_ids'):
					attr_id = citem.get('attribute_ids').splitlines()
					for item in attr_id:
						ProductAttributeOption = DocType('Product Attribute Option')
						query = (
							frappe.qb.from_(ProductAttributeOption)
							.select('*')
							.where(ProductAttributeOption.name == item)
						)
						attribute_weight = query.run(as_dict=True)
						if attribute_weight and attribute_weight[0].weight_adjustment:
							weight += flt(attribute_weight[0].weight_adjustment) * citem.get('quantity')
	check_shipping_rate_method(
								shipping_mapped_rate_method_check,
								shipping_charges_list,
								shipping_method,
								order_total,
								weight,
								shipping_charges,
								shipping_addr,subtotal
							)

def check_shipping_rate_method(shipping_mapped_rate_method_check,shipping_charges_list,
								shipping_method,order_total,weight,shipping_charges,shipping_addr,subtotal):
	if shipping_mapped_rate_method_check.shipping_rate_method == "Shipping By Total":
		ShippingByTotalCharges = DocType('Shipping By Total Charges')
		query = (
			frappe.qb.from_(ShippingByTotalCharges)
			.select('*')
			.where(
				(ShippingByTotalCharges.shipping_method == shipping_method) &
				(ShippingByTotalCharges.order_total_from <= order_total) &
				(ShippingByTotalCharges.order_total_to >= order_total) &
				(ShippingByTotalCharges.parent == shipping_mapped_rate_method_check.name)
			)
		)
		shipping_charges_list = query.run(as_dict=True)
	ShippingByWeightCharges = DocType('Shipping By Weight Charges')
	if shipping_mapped_rate_method_check.shipping_rate_method == "Shipping By Weight":
		query = (
			frappe.qb.from_(ShippingByWeightCharges)
			.select('*')
			.where(
				(ShippingByWeightCharges.shipping_method == shipping_method) &
				(ShippingByWeightCharges.order_weight_from <= weight) &
				(ShippingByWeightCharges.order_weight_to >= weight) &
				(ShippingByWeightCharges.parent == shipping_mapped_rate_method_check.name)
			)
		)
		shipping_charges_list = query.run(as_dict=True)
	ShippingByFixedRateCharges = DocType('Shipping By Fixed Rate Charges')
	if shipping_mapped_rate_method_check.shipping_rate_method == "Fixed Rate Shipping":
		query = (
			frappe.qb.from_(ShippingByFixedRateCharges)
			.select('*')
			.where(
				(ShippingByFixedRateCharges.shipping_method == shipping_method) &
				(ShippingByFixedRateCharges.parent == shipping_mapped_rate_method_check.name)
			)
		)
		shipping_charges_list = query.run(as_dict=True)
	charges = 0
	if shipping_mapped_rate_method_check.shipping_rate_method != "Shipping By Distance":
		charges = calculate_shipping_charges_lists(
													shipping_charges = shipping_charges,
													shipping_charges_list = shipping_charges_list,
													shipping_addr = shipping_addr, 
													subtotal = order_total
												)
	else:
		if shipping_charges_list[0].use_percentage == 1:
			charges = float(subtotal) * shipping_charges_list[0].charge_percentage / 100
		else:
			charges = float(shipping_charges_list[0].charge_amount)
	vendor_charges = total_shipping_charges = 0
	vendor_charges += charges
	total_shipping_charges += vendor_charges
	return total_shipping_charges



def calculate_shipping_charges_lists(shipping_charges,shipping_addr,subtotal,
	shipping_charges_list):
	if shipping_charges_list:
		shipingmatchedByZip = shipping_charges_list[0]
		if shipingmatchedByZip.use_percentage == 1:
			shipping_charges += float(subtotal) * shipingmatchedByZip.\
								charge_percentage / 100
		else:
			shipping_charges += float(shipingmatchedByZip.charge_amount)
	return shipping_charges


def get_geodistance(source, destination):
	import requests
	maps = frappe.get_single('Google Settings')
	if maps.enable:
		GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/distancematrix/json'
		params = {
					'key': maps.api_key,
					'origins': source,
					'destinations': destination,
					'mode': 'driving',
				}
		req = requests.get(GOOGLE_MAPS_API_URL, params = params)
		res = req.json()
		return res


def update_discount_foradminorder(doc):
	subtotal = doc.order_subtotal
	shipping_charges = doc.shipping_charges
	total_weight = 0
	is_recurring = 0
	shipping_method = doc.shipping_method
	payment_method = doc.payment_method
	cart_items = doc.order_item
	customer_id = doc.customer
	from go1_commerce.go1_commerce.doctype.discounts.discounts \
	import get_order_subtotal_discount
	web_type = 'Marketplace'
	returndata= {
				'status': 'failed', 
				'discount_amount': 0
			}
	if cart_items:
		response = get_order_subtotal_discount(subtotal, customer_id, cart_items,
				total_weight, is_recurring,shipping_method, payment_method,
				shipping_charges, website_type = web_type)
		if response and (response.get('discount_rule') or response.get('product_discount')) \
						or response.get('shipping_discount'):
			(tax, tax_splitup) = calculate_tax_after_discount(
																customer_id,
																response.get('discount_amount'),
																response.get('discount_rule'),
																subtotal, 
																cart_items, 
																response = response
															)
			returndata = {
					'status': 'Success',
					'discount_amount': response.get('discount_amount'),
					'discount': response.get('discount_rule'),
					'tax': tax,
					'tax_splitup': tax_splitup,
					'discount_response': response,
					}
		else:
			(tax, tax_splitup) = calculate_tax_without_discount(
																customer_id,
																subtotal, 
																cart_items,
																discount_amount = 0, 
																discount = None, 
																response = response
															)
			returndata = {
							'status': 'Success',
							'discount_amount': 0,
							'discount': None,
							'tax': tax,
							'tax_splitup': tax_splitup,
							'discount_response': response,
						}
	return returndata



def calculate_tax_after_discount(customer_id, discount_amount, discount, subtotal,
									cart_items, prev_discount=None, discount_type=None, response=None):


	def _calculate_item_discount(dis, subtotal, item):
		new_discount = 0
		subtotal_discount = 0
		if dis.price_or_product_discount == "Price":
			if dis.percent_or_amount == 'Discount Percentage':
				new_discount = float(item.get('t_amount')) * float(dis.discount_percentage) / 100
				subtotal_discount = float(subtotal) * float(dis.discount_percentage) / 100
			if (dis.max_discount_amount and dis.max_discount_amount > 0 \
					and dis.max_discount_amount < subtotal_discount) \
					or dis.percent_or_amount == 'Discount Amount':
				price_weightage = float(item.get('t_amount')) / float(subtotal) * 100
				price_weightage = math.ceil(float(price_weightage) * 100) / 100
				amount = 0
				if dis.max_discount_amount and dis.max_discount_amount > 0:
					amount = dis.max_discount_amount
				else:
					amount = dis.discount_amount
				new_discount = float(price_weightage) * float(amount) / 100
				new_discount = math.ceil(float(new_discount) * 100) / 100
		return new_discount

	def _calculate_item_wise_discount(item, response):
		new_discount = 0
		if response and response.get('products_list'):
			check = next((x for x in response.get('products_list') if x.get('product') == item), None)
			if check and check.get('discount'):
				new_discount = check.get('discount')
		return new_discount
	tax_amt = 0
	tax_splitup = []
	if cart_items:
		prev_discount_info = None
		if prev_discount:
			if prev_discount.get('discount'):
				prev_discount_info = frappe.get_doc('Discounts', prev_discount['discount'])
		if discount:
			dis = frappe.get_doc('Discounts', discount)
		for item in cart_items:
			if not item.get('is_free_item'):
				discount_amout = new_discount = 0
				if discount_type != 'remove':
					if discount:
						new_discount = _calculate_item_discount(dis, subtotal, item)
					if response.get('product_discount'):
						new_discount = new_discount + _calculate_item_wise_discount(
																					item.get('product'), 
																					response
																				)
					discount_amout = discount_amout + float(new_discount)
				if prev_discount:
					new_discount1 = 0
					if prev_discount_info:
						new_discount1 = _calculate_item_discount(prev_discount_info, subtotal, item)
					if prev_discount and prev_discount.get('discount_response'):
						new_discount1 = new_discount1 + _calculate_item_wise_discount(
																	item.get('product'),
																	prev_discount.get('discount_response')
																	)
					discount_amout = discount_amout + float(new_discount1)
				total = item.get('t_amount') - discount_amout
				item_tax = 0
				product_tax = None
				if frappe.db.get_value('Product', item.get('product')):
					product_tax = frappe.db.get_value('Product',
								item.get('product'), 'tax_category')
				if product_tax:
					tax_template = frappe.get_doc('Product Tax Template', product_tax)
					(item_tax, tax_splitup) = calculate_tax_from_template(tax_template,
											total, tax_splitup)
				tax_amt = tax_amt + item_tax
	return (tax_amt, tax_splitup)


def order_detail_template_items(items):
	for item in items:
		attr_image =''
		if item.attribute_ids:
			attr_ids = item.attribute_ids.split('\n')
			id_list = []
			for i in attr_ids:
				if i: id_list.append(i)
			ids = ",".join(['"' + x + '"' for x in id_list])
			ProductAttributeOption = DocType('Product Attribute Option')
			options_query = (
				frappe.qb.from_(ProductAttributeOption)
				.select('*')
				.where((ProductAttributeOption.parent == item.item) &
					(ProductAttributeOption.name.isin(ids)))
			)
			options = options_query.run(as_dict=True)
			for op in options:
				if op.image_list:
					images = json.loads(op.image_list)
					if len(images) > 0:
						images = sorted(images, key=lambda x: x.get('is_primary'), reverse=True)
						attr_image = images[0].get('thumbnail')
		ProductImage = DocType('Product Image')
		result_query = (
			frappe.qb.from_(ProductImage)
			.select(ProductImage.cart_thumbnail, ProductImage.list_image)
			.where(ProductImage.parent == item.item)
			.orderby(ProductImage.is_primary, order=Order.asc)
			.limit(1)
		)
		result = result_query.run(as_dict=True)
		if attr_image:
			item.item_image = attr_image
		elif result and result[0].cart_thumbnail:
			item.item_image = result[0].cart_thumbnail


 
def order_shipment_status(order_info,order_details,):
	order_settings = frappe.get_single('Order Settings')
	shipments = frappe.db.get_all("Shipment",
										filters = {"document_name":order_info[0].name},
										fields = ['*'])
	status_history=[]
	
	tax_splitup = None
	if order_details.tax_json:
		tax_splitup = json.loads(order_details.tax_json)
	check_process_status = 0
	allow_shipment = 0
	check_order_status = frappe.db.get_all("Order Status",
											filters={"shipping_status":"In Process"})
	if check_order_status:
		check_process_status = 1
	if order_details.shipping_method:
		shipping_method = frappe.db.get_all("Shipping Method",
											fields=['is_deliverable'],
											filters={"name":order_details.shipping_method})
		if shipping_method:
			if shipping_method[0].is_deliverable == 1:
				allow_shipment = 1
	customer_fullname,customer_notes = frappe.db.get_value('Customers', order_details.customer,
														["full_name","customer_notes"])
	farm_share_notes = None
	if "johnhenrys_custom_app" in frappe.get_installed_apps() and order_details.is_recurring_order == 1:
		farm_share_notes = frappe.db.get_value('Customers', order_details.customer,"farm_share_notes")
	is_driver = 0
	if "Driver" in frappe.get_roles(frappe.session.user) and not "System Manager" in frappe.get_roles(frappe.session.user):
		is_driver = 1
	today_date = get_today_date(replace=True)
	if order_details.order_time and order_details.order_time != 'ASAP' and order_details.status not in ['Completed', 'Cancelled']:
		order_time = frappe.utils.to_timedelta(order_details.order_time)
		order_date = get_datetime(str(order_details.order_date) + ' ' + str(order_time))
		if order_details.shipping_method_name == 'Delivery' and order_details.expected_travel_time:
			notify_time = notify_time + int(order_details.expected_travel_time)
		if notify_time and int(notify_time) > 0:
			if order_date > today_date:
				diff = frappe.utils.time_diff_in_seconds(order_date, today_date)
				if diff > ((int(notify_time) + 10) * 60):
					order_details.is_pre_order = 1
		collect_time = 0

		if order_details.expected_travel_time and int(order_details.expected_travel_time) > 0:
			collect_time = int(order_details.expected_travel_time)
		collect_datetime = order_date - timedelta(minutes=int(collect_time))
		if getdate(collect_datetime) == getdate(today_date):
			order_details.pickup_time = collect_datetime.strftime('%I:%M %p')
		else:
			order_details.pickup_time = collect_datetime.strftime('%b %d, %I:%M %p')
	elif order_details.order_time == 'ASAP' and order_details.preparation_time and order_details.preparation_time != '':
		mins = int(order_details.preparation_time)
		created = order_details.order_accepted_time if order_details.order_accepted_time else order_details.creation
		collect_datetime = created + timedelta(minutes=int(mins))
		order_details.pickup_time = collect_datetime.strftime('%I:%M %p')
		
	return[order_settings,shipments,status_history,tax_splitup,
			check_process_status,allow_shipment,customer_fullname,
			customer_notes,farm_share_notes,is_driver]



def get_drivers(doctype, txt, searchfield, start, page_len, filters):
	try:
		Drivers = DocType('Drivers')
		user_query = (
			frappe.qb.from_(Drivers)
			.select(Drivers.name)
		)
		user = user_query.run()
		return user
	except Exception:
		frappe.log_error("Error in doctype.order.get_drivers", frappe.get_traceback())



def get_customers(doctype,txt,searchfield,start,page_len,filters):
	try:
		Customers = DocType('Customers')
		query = (
			frappe.qb.from_(Customers)
			.select(Customers.name, Customers.full_name, Customers.phone)
			.where(Customers.customer_status == 'Approved')
			.where(Customers.disable == 0)
			.where(Customers.naming_series != 'GC-')
		)
		if txt:
			query = query.where(
				(Customers.name.like(f"%{txt}%")) |
				(Customers.full_name.like(f"%{txt}%")) |
				(Customers.phone.like(f"%{txt}%"))
			)
		user = query.run(as_dict=True)
		return user
	except Exception:
		frappe.log_error("Error in doctype.order.get_customers", frappe.get_traceback())



def get_order_status(doctype,txt,searchfield,start,page_len,filters):
	try:
		OrderStatus = DocType('Order Status')
		query = (
			frappe.qb.from_(OrderStatus)
			.select(OrderStatus.name)
			.where(OrderStatus.shipping_status.is_not_null())
		)
		if txt:
			query = query.where(OrderStatus.name.like(f"%{txt}%"))
		query = query.orderby(OrderStatus.display_order)
		results = query.run(as_dict=True)
		return results
	except Exception:
		frappe.log_error("Error in doctype.order.order.get_order_status",frappe.get_traceback())



def check_payment(self):
	try:
		if self.payment_status == "Paid":
			payment=frappe.db.get_all('Payment Entry',filters = {'order_id':self.name})
			paymant_type = "Cash" if self.payment_type == "Cash" else "Online Payment"
			if not payment:
				frappe.get_doc({
							"doctype":"Payment Entry",
							"order_id":self.name,
							"customer":self.customer,
							"customer_name":self.customer_name,
							"amount_to_pay":self.total_amount,
							"use_wallet_balance":0,
							"paid_amount":self.total_amount,
							"mode_of_payment":paymant_type
							}).submit()
	except Exception:
		frappe.log_error("Error in doctype.order.check_payment", frappe.get_traceback())



def send_notification(self,doctype = "Order",message = "You have an order!"):
	try:
		frappe.publish_realtime(event = 'msgprint',message = 'hello',user = 'administrator')
	except Exception:
		frappe.log_error("Error in .doctype.order.send_notification", frappe.get_traceback())



def check_orderDelivery(self):
	try:
		orderDelivery = frappe.db.get_all('Order Delivery',filters={'order_id':self.name})
		import random
		import string
		random = ''.join([random.choice(string.ascii_letters
				+ string.digits) for n in range(10)])
		if not orderDelivery:
			self.delivery_created=1
			frappe.get_doc({
				"doctype":"Order Delivery",
				"order_id":self.name,
				"posted_date":getdate(nowdate()),
				"name":random
				}).insert()
	except Exception:
		frappe.log_error("Error in doctype.order.check_orderDelivery", frappe.get_traceback())



def update_orderDelivery(self):
	try:
		orderDelivery=frappe.db.get_all('Delivery',filters={'order_id':self.name})
		if orderDelivery:
			doc=frappe.get_doc('Order Delivery',orderDelivery[0].name)
			if self.driver_status=="Driver Accepted":
				doc.delivery_status="Driver Assigned"
				if doc.driver_assigned:
					for item in doc.driver_assigned:
						if item.driver==self.driver:
							item.status="Accepted"
							frappe.db.set_value('Drivers',item.driver,'working_status','On Duty')
			elif self.driver_status=="Delivered":
				doc.delivery_status="Delivered"
			if self.status=="Cancelled":
				doc.delivery_status="Cancelled"
			doc.save(ignore_permissions=True)
	except Exception:
		frappe.log_error("Error in doctype.order.update_orderDelivery", frappe.get_traceback(),)


def randomStringDigits(stringLength=6):
	import random
	import string
	lettersAndDigits = string.ascii_uppercase + string.digits
	return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


@frappe.whitelist()
def get_order_settings(order_id,doctype):
	if not frappe.db.get_value(doctype, order_id):
		return
	order = frappe.get_doc(doctype,order_id)
	check_process_status = 0
	allow_shipment = 0
	check_order_status = frappe.db.get_all("Order Status",
											filters = {"shipping_status":"In Process"})
	if check_order_status:
		check_process_status = 1
	if order.shipping_method:
		shipping_method = frappe.db.get_all("Shipping Method",
											fields = ['is_deliverable'],
											filters = {"name":order.shipping_method})
		if shipping_method:
			if shipping_method[0].is_deliverable == 1:
				allow_shipment = 1
	loyalty = 0
	if "loyalty" in frappe.get_installed_apps():
		loyalty = 1
	return {"loyalty":loyalty,"proccess_status":check_process_status,
			"order_settings":frappe.get_single('Order Settings'),
			"allow_shipment":allow_shipment}


@frappe.whitelist()
def check_order_settings():
	is_restaurant_driver = 0
	return {
			"order_settings":frappe.get_single('Order Settings'),
			"is_restaurant":False,
			"is_restaurant_driver":is_restaurant_driver}



def make_refund(refund_amount, order):
	payment = get_customer_payments(order)
	if len(payment)>0:
		refund = frappe.get_doc("Payment Entry",payment[0].name)
		refund.cancel()
		if refund.docstatus==2:
			frappe.db.set_value("Order", order, "payment_status", "Refunded")
			return "success"
	return "failed"


@frappe.whitelist()
def mark_as_ready(order):
	order_info = frappe.get_doc("Order",order)
	order_info.status = "Ready"
	order_info.save(ignore_permissions=True)



def get_customer_payments(order):
	PaymentEntry = DocType('Payment Entry')
	PaymentReference = DocType('Payment Reference')
	payments = (
		frappe.qb.from_(PaymentEntry)
		.inner_join(PaymentReference)
		.on(PaymentReference.parent == PaymentEntry.name)
		.select(
			PaymentEntry.name,
			PaymentEntry.posting_date,
			PaymentEntry.paid_amount,
			PaymentReference.outstanding_amount
		)
		.where(
			PaymentReference.reference_doctype == "Order",
			PaymentReference.reference_name == frappe.utils.escape(order)
		)
		.run(as_dict=True)
	)
	return payments

def cancel_order(order):
	if not frappe.db.get_value('Order', order):
		return
	OrderDetail = frappe.get_doc('Order', order)
	if OrderDetail.restaurant_status != 'Accepted' and OrderDetail.status != 'Cancelled':
		OrderDetail.status = 'Cancelled'
		OrderDetail.restaurant_status = 'Not Responded'
		OrderDetail.save(ignore_permissions=True)
		frappe.db.set_value('Order', order, 'workflow_state', 'Order Cancelled')
		frappe.publish_realtime('order_tracking',{
													'name':OrderDetail.name, 
													'workflow_state':'Order Cancelled'
												})
	return {'status': 'Success'}


@frappe.whitelist()
def get_linked_invoice(order):
	return frappe.db.get_value("Sales Invoice",{"reference":order})



def shipping_zip_matches_order(zip, ziprange):
	zipcoderanges = []
	returnValue = False
	if ziprange.find(',') > -1:
		zipcoderanges = ziprange.split(',')
		for x in zipcoderanges:
			if x.find('-') > -1:
				zipcoderanges_after = x.split('-')
				for zipcode in range(int(zipcoderanges_after[0]), int(zipcoderanges_after[1]) + 1):
					if str(zipcode).lower() == str(zip).lower():
						returnValue = True
			else:
				if str(x).lower() == str(zip).lower():
					returnValue = True
	elif ziprange.find('-') > -1:
		zipcoderanges_after = ziprange.split('-')
		for zipcode in range(int(zipcoderanges_after[0]), int(zipcoderanges_after[1]) + 1):
			if str(zipcode).lower() == str(zip).lower():
				returnValue = True
	else:
		if str(ziprange).lower() == str(zip).lower():
			returnValue = True
	return returnValue



def check_installed_app(app_name):
	if app_name in frappe.get_installed_apps():
		return True
	return False



def clear_guest_user_details(order_id):
	if not frappe.db.get_value('Order', order_id):
		return
	order_info = frappe.get_doc('Order', order_id)
	if order_info and order_info.customer and order_info.customer_type=="Customers":
		customer_info = frappe.get_doc('Customers', order_info.customer)
		if customer_info.naming_series == 'GC-':
			frappe.db.set_value('Customers', customer_info.name, 'first_name', 'Guest')
			frappe.db.set_value('Customers', customer_info.name, 'email', None)
			frappe.db.set_value('Customers', customer_info.name, 'phone', None)
			if customer_info.table_6:
				for item in customer_info.table_6:
					item.delete()
			if not order_info.customer_name:
				frappe.db.set_value('Order', order_id, 'customer_name', customer_info.first_name)
		else:
			if not order_info.customer_name:
				frappe.db.set_value('Order', order_id, 'customer_name', customer_info.full_name)



def update_order_shipment_payment(order):
	shipments = frappe.db.get_all("Shipment",filters = {"document_name":order},fields = ['*'])
	if shipments:
		Shipment = DocType('Shipment')
		qr=(
			frappe.qb.update(Shipment)
			.set(Shipment.payment_status, 'Paid')
			.where(Shipment.name == shipments[0].name)
			.run()
		)



def get_order_shipments(name):
	shipments = frappe.db.get_all("Shipment",filters={"document_name":name},fields=['*'])
	return shipments



def update_order_totals(order, shipping_charges, discount_amount, Wallet_amount):
	order_info = frappe.get_doc("Order",order)
	frappe.db.set_value('Order', order, 'shipping_charges', shipping_charges)
	frappe.db.set_value('Order', order, 'discount', discount_amount)
	if flt(order_info.discount)!= flt(discount_amount):
		frappe.db.set_value('Order', order, 'is_custom_discount', 1)
	frappe.db.set_value('Order', order, 'paid_using_wallet', Wallet_amount)
	frappe.db.commit()
	order_info = frappe.get_doc("Order",order)
	order_info.save(ignore_permissions=True)



def create_custom_wallet_entry(order,amount):
	wallet_trans_entry = frappe.get_doc({
											"doctype":"Wallet Transaction",
											"reference":"Order",
											"order_type":"Order",
											"order_id":order.name,
											"transaction_date":now(),
											"total_value":amount,
											"amount":amount,
											"is_settlement_paid":0,
											"is_fund_added":1
										})
	wallet_trans_entry.order_id =  order.name
	wallet_trans_entry.type = "Customers"
	wallet_trans_entry.party_type = "Customers"
	wallet_trans_entry.party = order.customer
	wallet_trans_entry.transaction_type = "Pay"
	wallet_trans_entry.status = "Debited"
	wallet_trans_entry.flags.ignore_permissions = True
	wallet_trans_entry.submit()



def update_order_checkout_attributes(order,attributes):
	for x in json.loads(attributes):
		if x.get('name') and x.get('name') != '':
			frappe.db.set_value(
									'Order Checkout Attributes', 
									x.get("name"), 'attribute_description', 
									x.get("attribute_description")
								)
		else:
			frappe.get_doc({
								'doctype': 'Order Checkout Attributes',
								'parent': order,
								'parenttype': 'Order',
								'parentfield': "checkout_attributes",
								'price_adjustment': (x.get('price_adjustment') or 0),
								'attribute_id': x.get('checkout_attribute_id'),
								'attribute_description': x.get('attribute_description')
							}).insert(ignore_permissions=True)
	frappe.db.commit()
	order_info = frappe.get_doc("Order",order)
	order_info.save(ignore_permissions=True)



def update_giftcard_payments(order_id,transaction_id):
	giftcard_orders = frappe.get_all("Gift Card Order",filters={"order_reference":order_id})
	for x in giftcard_orders:
		giftcard_order = frappe.get_doc("Gift Card Order",x.name)
		giftcard_order.transaction_id = transaction_id
		giftcard_order.payment_status = "Paid"
		giftcard_order.save(ignore_permissions = True)



def update_giftcard_status(order):
	giftcard_orders = frappe.get_all("Gift Card Order",
									filters={
												"giftcart_coupon_code":order.giftcard_coupon_code,
												"is_giftcard_used":0
											})
	for x in giftcard_orders:
		giftcard_order = frappe.get_doc("Gift Card Order",x.name)
		giftcard_order.is_giftcard_used = 1
		giftcard_order.save(ignore_permissions = True)
		usage_history = frappe.new_doc("Gift Card Usage History")
		usage_history.used_code = order.giftcard_coupon_code
		usage_history.customer_name = order.customer_name
		usage_history.customer_email = order.customer_email
		usage_history.customer_phone = order.phone
		usage_history.order_id = order.name
		usage_history.customer = order.customer
		usage_history.save(ignore_permissions=True)
		frappe.db.commit()



def clear_selected_orders(names):
	docs = json.loads(names)
	if len(docs) == 0:
		frappe.throw(frappe._('Please select any record'))
	for i, item in enumerate(docs):
		check_linked_docs('Order', item)
		show_progress(docs, frappe._('Deleting {}'.format('Order')), i, item)


def check_linked_docs(dt, dn):
	linkinfo = get_linked_doctypes(dt)
	linked_docs = get_linked_docs(dt, dn, linkinfo)
	if not linked_docs:
		doc = frappe.get_doc(dt, dn)
		doc.flags.ignore_permissions = True
		if doc.docstatus == 1:
			doc.cancel()
		doc.delete()
	for _dt, link_docs in linked_docs.items():
		for rec in link_docs:
			if _dt == 'Discounts' and dt == 'Order':
				DiscountUsageHistory = DocType('Discount Usage History')
				dis = (
					frappe.qb.delete(DiscountUsageHistory)
					.where(DiscountUsageHistory.parent == rec.name)
					.where(DiscountUsageHistory.order_id == dn)
					.run()
				)
			else:
				check_linked_docs(_dt, rec.name)


def show_progress(docnames, message, i, description):
	n = len(docnames)
	if n >= 10:
		frappe.publish_progress(float(i) * 100 / n, title = message, description = description )


def get_coupon_discount(order_id,order_subtotal,coupon_code):
	status = 'success'
	coupon = frappe.db.get_all('Discounts', 
								filters = {'requires_coupon_code': 1, 'coupon_code': coupon_code}, 
								fields = ['*'])
	msg = ''
	coupon_data = None
	if coupon:
		coupon_data = frappe.get_doc('Discounts', coupon[0].name)
		if coupon_data:
			if  coupon_data.discount_requirements:
				for req in coupon_data.discount_requirements:
					if req.discount_requirement == 'Spend x amount':
						if float(order_subtotal) < float(req.amount_to_be_spent):
							status = 'failed'
							msg = 'Your cart must contain minimum value 0f $' + str(req.amount_to_be_spent)
							break
					elif req.discount_requirement == 'Specific price range':
						if req.min_amount and float(order_subtotal) < float(req.min_amount):
							status = 'failed'
							msg = 'Your cart must contain minimum value of $' + str(req.min_amount)
							break
						if req.max_amount and float(order_subtotal) > float(req.max_amount):
							status = 'failed'
							msg = 'Your cart value must not exceed of $' + str(req.max_amount)
							break
		else:
			status = 'failed'
	else:
		status = 'failed'
	if status == 'failed':
		return {
				'message': msg, 
				'status': status
			}
	if status == 'success':
		if coupon_data.price_or_product_discount == "Price":
			discount_amount = coupon_data.discount_amount
			if coupon_data.percent_or_amount == "Discount Percentage":
				discount_amount = (flt(order_subtotal)*flt(coupon_data.discount_percentage))/100
			if coupon_data.max_discount_amount>0:
				if discount_amount>coupon_data.max_discount_amount:
					discount_amount = coupon_data.max_discount_amount
			OrderItem = DocType('Order Item')
			free_order_items = (
				frappe.qb.select(OrderItem.name)
				.from_(OrderItem)
				.where(OrderItem.parent == order_id)
				.where(OrderItem.is_free_item == 1)
				.where(OrderItem.discount_coupon != '')
				.run(as_dict=True)
			)
			for item in free_order_items:
				delete_result  = (
					frappe.qb.delete(OrderItem)
					.where(OrderItem.name == item['name'])
					.run()
				)
			frappe.db.commit()
			return {
					"discount_amount":discount_amount,
					"discount_rule":coupon_data.name,
					"status":status
					}
		else:
			get_order_item(order_id, coupon_code,coupon_data,msg,status)


def get_order_item(order_id, coupon_code,coupon_data,msg,status):
	new_order_item = ""
	OrderItem = DocType('Order Item')
	free_order_items = (
		frappe.qb.select(OrderItem.name)
		.from_(OrderItem)
		.where(OrderItem.parent == order_id)
		.where(OrderItem.is_free_item == 1)
		.where(OrderItem.discount_coupon != '')
		.run(as_dict=True)
	)
	for item in free_order_items:
		delete_result  =(
			frappe.qb
			.delete(OrderItem)
			.where(OrderItem.name == item['name'])
			.run()
		)
	frappe.db.commit()
	if coupon_data.free_product:
		product = frappe.get_doc("Product",coupon_data.free_product)
		new_order_item = frappe.new_doc("Order Item")
		new_order_item.amount = (product.price*coupon_data.free_qty)
		new_order_item.is_free_item = 1
		new_order_item.is_gift_card = 0
		new_order_item.parent = order_id
		new_order_item.parentfield = "order_item"
		new_order_item.parenttype =  "Order"
		new_order_item.is_rewarded = 0
		new_order_item.order_item_type = "Product"
		new_order_item.is_scanned = 0
		new_order_item.item_name = product.item
		new_order_item.item = coupon_data.free_product
		new_order_item.item_image = product.image
		new_order_item.ordered_weight = product.weight
		new_order_item.price = product.price
		new_order_item.quantity = coupon_data.free_qty
		new_order_item.return_created = 0
		new_order_item.shipping_status = "Pending"
		new_order_item.shipping_charges = 0
		new_order_item.t_amount = (product.price*coupon_data.free_qty)
		new_order_item.tax = 0
		new_order_item.weight = product.weight
		new_order_item.discount_coupon = coupon_code
		new_order_item.insert()
		return {
				'message': msg, 
				'status': status, 
				"new_order_item": new_order_item
				}


@frappe.whitelist()
def update_order_items_status(Products, status, OrderId, doctype, Tracking_Number = None,
								Tracking_Link = None,create_shipment = None, driver = None):
	try:
		if doctype == "Order":
			order_doc = frappe.get_doc("Order",OrderId)
			for x in order_doc.order_item:
				x.shipping_status = status
				if Tracking_Number:
					x.tracking_number = Tracking_Number
				if Tracking_Link:
					x.tracking_link = Tracking_Link
			order_doc.status = status
			order_doc.is_admin_updating_order = 1
			order_doc.save(ignore_permissions=True)
			frappe.db.commit()
		if create_shipment:
			create_order_shipment(doctype, OrderId, Products,Tracking_Number, Tracking_Link, driver)
	except Exception:
		frappe.log_error("Error in doctype.order.order.update_order_items_status", frappe.get_traceback())



def create_order_shipment(dt, dn, products, tracking_number = None, tracking_link = None, driver = None):
	try:
		doc = frappe.get_doc(dt, dn)
		qty = 0
		order_shipmemt = frappe.db.get_all('Shipment',fields=['name'],filters={'document_name':dn})
		if not order_shipmemt:
			shipment = frappe.new_doc('Shipment')
			shipment.document_type = dt
			shipment.document_name = dn
			if doc.payment_status in ['Pending', 'Paid']:
				shipment.payment_status = doc.payment_status
			else:
				shipment.payment_status = 'Pending'
			shipment.shipped_date = get_today_date(replace=True)
			shipment.tracking_number = tracking_number
			shipment.tracking_link = tracking_link
			if driver:
				shipment.driver = driver
			if doc.get('business'):
				shipment.business = doc.business
			for item in doc.order_item:
				shipment.append('items',{
											'item_type': "Product",
											'item': item.item,
											'item_name': item.item_name,
											'quantity': item.quantity,
											'price': item.price,
											'total': item.amount,
											'attribute_description': item.attribute_description
										})
				qty = qty + item.quantity
			shipment.total_quantity = qty
			shipment.order_total = doc.total_amount
			shipment.docstatus = 1
			shipment.save(ignore_permissions=True)
		else:
			frappe.db.set_value('Shipment', order_shipmemt[0].name, 'status', "Shipped")
			frappe.db.set_value('Shipment', order_shipmemt[0].name, 'tracking_number', tracking_number)
			frappe.db.set_value('Shipment', order_shipmemt[0].name, 'tracking_link', tracking_link)
			check_ship_date = frappe.db.get_all("Custom Field",
												filters={"dt":"Order","fieldname":"ship_date"})
			if check_ship_date:
				if doc.ship_date:
					frappe.db.set_value(
										'Shipment', 
										order_shipmemt[0].name, 
										'shipped_date', doc.ship_date
									)
			if driver:
				frappe.db.set_value('Shipment', order_shipmemt[0].name, 'driver', driver)
	except Exception:
			frappe.log_error("Error in doctype.order.create_order_shipment", frappe.get_traceback())


@frappe.whitelist()
def get_order_items(OrderId,fntype):
	try:
		if fntype == 'packed' or fntype == 'Packed':
			status_update = frappe.get_doc("Order" ,OrderId)
			status_update.status = "Packed"
			status_update.shipping_status = "Packed"
			status_update.save(ignore_permissions = True)
			frappe.db.set_value("Order",OrderId,'pre_status',"Packed")
			return "Success"
		
		elif fntype == 'shipped':
			status_update=frappe.get_doc("Order" ,OrderId)
			status_update.status = "Shipped"
			status_update.shipping_status = "Shipped"
			status_update.save(ignore_permissions = True)
			frappe.db.set_value("Order",OrderId,'pre_status',"Shipped")
			return "Success"
		
		elif fntype == 'delivered':
			status_update = frappe.get_doc("Order" ,OrderId)
			status_update.status = "Delivered"
			status_update.shipping_status = "Delivered"
			order_shipmemt = frappe.db.get_all('Shipment',
											fields = ['name'],
											filters = {'document_name':OrderId})
			if order_shipmemt:
				frappe.db.set_value('Shipment', order_shipmemt[0].name, 'status', "Delivered")
				check_delivery_date = frappe.db.get_all("Custom Field",
														filters={
																	"dt":"Order",
																	"fieldname":"delivery_date"
																})
				if check_delivery_date:
					my_time = datetime.min.time()
					my_datetime = datetime.combine(getdate(nowdate()), my_time)
					frappe.db.set_value(
										'Shipment', 
										order_shipmemt[0].name, 
										'delivered_date',
										my_datetime
									)
				else:
					my_time = datetime.min.time()
					my_datetime = get_today_date(replace=True)
					frappe.db.set_value(
											'Shipment', order_shipmemt[0].name, 
											'delivered_date', 
											my_datetime
										)
					
			status_update.save(ignore_permissions=True)
			frappe.db.set_value("Order",OrderId,'pre_status',"Delivered")
			OrderItem = DocType('Order Item')
			updt = (
				frappe.qb.update(OrderItem)
				.set(OrderItem.shipping_status, 'Delivered')
				.set(OrderItem.delivery_date, getdate(nowdate()))
				.where(OrderItem.parent == OrderId).run()
			)
			return "Success"
	except Exception:
		frappe.log_error("Error in doctype.order.get_order_items", frappe.get_traceback())


@frappe.whitelist()
def _get_order_items_(OrderId, fntype):
	try:
		OrderItem = DocType('Order Item')
		query = (
			frappe.qb.from_(OrderItem)
			.select(
				OrderItem.item,
				OrderItem.item_name,
				OrderItem.quantity,
				OrderItem.price,
				OrderItem.amount,
				OrderItem.name
			)
			.where(OrderItem.parent == OrderId)
		)
		if fntype == 'packed':
			query = query.where(
				(OrderItem.shipping_status == 'Pending') | (OrderItem.shipping_status.is_null())
			)
		elif fntype == 'shipped':
			query = query.where(
				(OrderItem.shipping_status == 'Packed') |
				(OrderItem.shipping_status == 'Ready to Ship') |
				(OrderItem.shipping_status == 'In Process')
			)
		lists = query.run(as_dict=True)
		get_order_items(OrderId, fntype)
		return lists
	except Exception:
		frappe.log_error("Error in doctype.order._get_order_items_", frappe.get_traceback())



def get_shipment_bag_id(order_id):
	ShipmentBagItem = DocType('Shipment Bag Item')
	query = (
		frappe.qb
		.from_(ShipmentBagItem)
		.select(ShipmentBagItem.parent)
		.where(ShipmentBagItem.order_id == order_id)
		.orderby(ShipmentBagItem.idx)
	)
	items = query.run(as_dict=True)
	if items:
		return {
				"status":"success",
				"shipment_id":items[0].parent
			}
	else:
		return {
				"status":"failed",
				"shipment_id":items[0].parent
			}


@frappe.whitelist()
def get_attributes_combination(product):
	combination = frappe.db.get_all('Product Variant Combination',
									filters = {'parent':product, 'disabled':0},
									fields = ['*'])
	for item in combination:
		if item and item.get('attributes_json'):
			variant = json.loads(item.get('attributes_json'))
			attribute_html = ""
			for obj in variant:
				if attribute_html:
					attribute_html += ", "
				option_value, attribute = frappe.db.get_value("Product Attribute Option", 
															obj, 
															["option_value","attribute"])

				attribute_name = frappe.db.get_value("Product Attribute", attribute, "attribute_name")
				attribute_html += "<b>" + attribute_name+"</b>:" + option_value
			item["combination_txt"] = attribute_html
	productdoc = frappe.db.get_all('Product',fields = ['*'],filters = {'name':product})
	return combination, productdoc


def get_attributes_combination_text(attribute):
	try:
		combination = frappe.db.get_all('Product Variant Combination',
										filters = {'attribute_id':attribute},
										fields = ['*'])
		for item in combination:
			if item and item.get('attributes_json'):
				variant = json.loads(item.get('attributes_json'))
				attribute_html = ""
				for obj in variant:
					if obj:
						if attribute_html:
							attribute_html +=", "
						if frappe.db.get_all("Product Attribute Option",filters={"name":obj}):
							option_value, attribute = frappe.db.get_value(
																			"Product Attribute Option", 
																			obj, 
																			[
																				"option_value",
																				"attribute"
																			])
							attribute_name = frappe.db.get_value("Product Attribute", 
																attribute, 
																"attribute_name")
							attribute_html += attribute_name + " : " + option_value
				item["combination_txt"] = attribute_html
		return combination
	except Exception:
		frappe.log_error('Error in v2.product.get_attributes_combination', frappe.get_traceback())



def update_variant_id(product, v_text):
	combination = frappe.db.get_all('Product Variant Combination',
									filters = {'parent':product, 'disabled':0},
									fields = ['*'])
	for item in combination:
		if item and item.get('attributes_json'):
			variant = json.loads(item.get('attributes_json'))
			attribute_html = ""
			for obj in variant:
				if attribute_html:
					attribute_html +=", "
				option_value, attribute = frappe.db.get_value("Product Attribute Option", 
															obj, 
															["option_value","attribute"])

				attribute_name = frappe.db.get_value("Product Attribute", attribute, "attribute_name")
				attribute_html += "<b>" + attribute_name + "</b>:" + option_value
			item["combination_txt"] = attribute_html
			if attribute_html == v_text:
				return item.get("attribute_id")


def variant_stock_update(item):
	from go1_commerce.go1_commerce.v2.orders \
		import get_attributes_json
	attribute_id = get_attributes_json(item.attribute_ids)
	check_data = frappe.db.get_all('Product Variant Combination',
							filters = {'parent': item.item, 'attributes_json': attribute_id},
							fields = ['stock', 'price', 'weight', 'name', 'sku', 'role_based_pricing'])
	
	if check_data:
		stock = int(check_data[0].stock) + int(item.quantity)
		frappe.db.set_value(
							'Product Variant Combination', 
							check_data[0].name, 
							'stock', 
							stock
						)


@frappe.whitelist()
def get_doc_single_value(doctype, fieldname, filters=None, as_dict=True, debug=False, parent=None):
	"""Returns a value form a document
	:param doctype: DocType to be queried
	:param fieldname: Field to be returned (default `name`)
	:param filters: dict or string for identifying the record"""
	from frappe.utils import get_safe_filters
	filters = get_safe_filters(filters)
	if isinstance(filters, str):
		filters = {"name": filters}
	try:
		fields = frappe.parse_json(fieldname)
	except (TypeError, ValueError):
		fields = [fieldname]

	if not filters:
		filters = None
	if frappe.get_meta(doctype).issingle:
		value = frappe.db.get_values_from_single(fields, filters, doctype, as_dict = as_dict, debug = debug)
	else:
		value = frappe.db.get_all(doctype, filters = filters,fields = fields, page_length = 1)
	if as_dict:
		return value[0] if value else {}

	if not value:
		return
	return value[0] if len(fields) > 1 else value[0][0]


@frappe.whitelist()
def get_customer_details(doctype,fields,filters):
	details = frappe.db.get_all(doctype,fields = fields,filters = filters,page_length = 1)
	return details[0] if details else {}



def get_list( doctype, fields = None, filters = None, order_by = None, limit_start = None,
				limit_page_length = 20, parent = None, debug = False, as_dict = True, or_filters = None):
	"""Returns a list of records by filters, fields, ordering and limit

	:param doctype: DocType of the data to be queried
	:param fields: fields to be returned. Default is `name`
	:param filters: filter list by this dict
	:param order_by: Order by this fieldname
	:param limit_start: Start at this index
	:param limit_page_length: Number of records to be returned (default 20)"""
	from frappe import _
	from frappe.desk.reportview import validate_args
	from frappe.model.db_query import check_parent_permission
	if frappe.is_table(doctype):
		check_parent_permission(parent, doctype)
	args = frappe._dict(
						doctype = doctype,
						parent_doctype = parent,
						fields = fields,
						filters = filters,
						or_filters = or_filters,
						order_by = order_by,
						limit_start = limit_start,
						limit_page_length = limit_page_length,
						debug = debug,
						as_list = not as_dict,
					)
	validate_args(args)
	return frappe.get_list(**args)



def calculate_vendor_order_shipping_charges(order_item, order_doc):
	shipping_charges = 0
	shipping_rate_methods = []
	ShippingRateMethod = DocType('Shipping Rate Method')
	query = (
		frappe.qb.from_(ShippingRateMethod)
		.select(ShippingRateMethod.name, ShippingRateMethod.shipping_rate_method)
	)
	shipping_rate_methods = query.run(as_dict=True)
	if shipping_rate_methods:
		vo_shipping_charges = 0
		shipping_rate_method = shipping_rate_methods[0]
		if shipping_rate_method.shipping_rate_method == "Fixed Rate Shipping":
			OrderItem = DocType('Order Item')
			business_list_query = (
				frappe.qb
				.from_(OrderItem)
				.select(OrderItem.business)
				.where(OrderItem.parent == order_doc.name)
				.groupby(OrderItem.business)
			)
			business_list = business_list_query.run(as_dict=True)
			ShippingByFixedRateCharges = DocType('Shipping By Fixed Rate Charges')
			if business_list:
				shipping_charges_list_query = (
					frappe.qb.from_(ShippingByFixedRateCharges)
					.select('*')
					.where(
						(ShippingByFixedRateCharges.shipping_method == order_doc.shipping_method) &
						(ShippingByFixedRateCharges.parent == shipping_rate_method.name)
					))
				shipping_charges_list = shipping_charges_list_query.run(as_dict=True)
				if shipping_charges_list:
					vo_shipping_charges = round(shipping_charges_list[0].charge_amount / len(business_list),2)
					shipping_by_total(
										order_item,
										order_doc,
										shipping_rate_method
									)
					shipping_by_weight(
										order_item,
										order_doc,
										shipping_rate_method
									)
		for x in order_item:
			(enable_shipping, free_shipping,
				additional_shipping_cost) = frappe.db.get_value('Product',
												x.get('item'),
												['enable_shipping',
												'free_shipping',
												'additional_shipping_cost'
												])
			if enable_shipping == 1 and free_shipping == 0:
				vo_shipping_charges += additional_shipping_cost
		shipping_charges = vo_shipping_charges
	return shipping_charges



def shipping_by_total(catalog_settings, order_item, order_doc, shipping_rate_method):
	if shipping_rate_method.shipping_rate_method == "Shipping By Total":
		order_total = 0
		order_total = sum(round(flt(x.amount+x.tax), 2) for x in order_item)
		if catalog_settings.included_tax:
			order_total = sum(round(flt(x.amount), 2) for x in order_item)
		ShippingByTotalCharges = DocType('Shipping By Total Charges')
		shipping_charges_list_query = (
			frappe.qb.from_(ShippingByTotalCharges)
			.select('*')
			.where(
				(ShippingByTotalCharges.shipping_method == order_doc.shipping_method) &
				(order_total >= ShippingByTotalCharges.order_total_from) &
				(order_total <= ShippingByTotalCharges.order_total_to) &
				(ShippingByTotalCharges.parent == shipping_rate_method.name)
			)
		)
		shipping_charges_list = shipping_charges_list_query.run(as_dict=True)
		if shipping_charges_list:
			if shipping_charges_list[0].use_percentage == 1:
				vo_shipping_charges += float(sum(round(flt(x.amount), 2) for x in order_item)) * shipping_charges_list[0].\
									charge_percentage / 100
			else:
				vo_shipping_charges += float(shipping_charges_list[0].charge_amount)


def shipping_by_weight(order_item, order_doc, shipping_rate_method):
	if shipping_rate_method.shipping_rate_method == "Shipping By Weight":
		order_weight = 0
		for x in order_item:
			weight = frappe.db.get_value('Product',x.get('item'),['weight'])
			order_weight += weight
		ShippingByWeightCharges = DocType('Shipping By Weight Charges')
		shipping_charges_list_query = (
			frappe.qb.from_(ShippingByWeightCharges)
			.select('*')
			.where(
				(ShippingByWeightCharges.shipping_method == order_doc.shipping_method) &
				(order_weight >= ShippingByWeightCharges.order_weight_from) &
				(order_weight <= ShippingByWeightCharges.order_weight_to) &
				(ShippingByWeightCharges.parent == shipping_rate_method.name)
			)
		)
		shipping_charges_list = shipping_charges_list_query.run(as_dict=True)
		if shipping_charges_list:
			if shipping_charges_list[0].use_percentage == 1:
				vo_shipping_charges += float(sum(round(flt(x.amount), 2) for x in order_item)) * \
											shipping_charges_list[0].charge_percentage / 100
			else:
				vo_shipping_charges += float(shipping_charges_list[0].charge_amount)


@frappe.whitelist()
def get_product_price(product, customer, attribute = None):
	try:
		price = 0
		old_price = 0
		discount_list = get_discount_list()
		products = frappe.db.get_all("Product",
										filters = {"name":product}, 
										fields = ['price','old_price','name'])
		if products:
			product_info = products[0]
			if attribute:
				vc = frappe.db.get_all("Product Variant Combination",
								filters = {"attribute_id":attribute},
								fields = ['price'])
				if vc:
					product_info.price = vc[0].price
			price_details = None
			product_info["product_price"] = product_info.price
			return _discount_info(
									discount_list, 
									product_info, 
									customer, 
									price_details
								)
	except Exception:
			frappe.log_error("Error in doctype.order.get_product_price", frappe.get_traceback())
			return {
					"price":price,
					"old_price":old_price
				}


def get_discount_list():
	Discounts = DocType('Discounts')
	today = get_today_date()
	discount_list_query = (
		frappe.qb
		.from_(Discounts)
		.select(Discounts.name)
		.where(
			(Discounts.discount_type.isin(['Assigned to Products', 'Assigned to Categories'])) &
			( (Discounts.start_date.isnull()) |
				(Discounts.start_date <= today)) &
			((Discounts.end_date.isnull()) |
				(Discounts.end_date >= today))
		)
	)
	discount_list = discount_list_query.run(as_dict=True)
	return discount_list


def _discount_info(discount_list, product_info, customer, price_details):
	if discount_list:
		from go1_commerce.go1_commerce.v2.product \
			import get_product_price as _get_product_price
		price_details = _get_product_price(product_info, customer = customer)
		if price_details:
			discount_info = frappe.db.get_all("Discounts",
				filters = {"name":price_details.get('discount_rule')},
				fields = ['percent_or_amount','discount_percentage','discount_amount','discount_type'])
			discount_requirements = frappe.db.get_all("Discount Requirements",
									filters = {"parent":price_details.get('discount_rule')},
									fields = ['items_list','discount_requirement'])
			customer_list = []
			if discount_requirements:
				for dr in discount_requirements:
					if dr.discount_requirement == "Limit to customer":
						items = json.loads(dr.items_list)
						customer_list = [i.get('item') for i in items]
			is_allowed = 1
			if customer_list:
				if customer not in customer_list:
					is_allowed = 0
			if discount_info and is_allowed == 1:
				if discount_info[0].percent_or_amount == "Discount Percentage":
					value = discount_info[0].discount_percentage
					product_info["product_price"] = flt(product_info.get("price")) - flt(product_info.get("price"))*flt(value)/100
					product_info["old_price"] = product_info.get("price")
				else:
					product_info["product_price"] = flt(product_info.get("price")) - flt(discount_info[0].discount_amount)
					product_info["old_price"] = product_info.get("price")
	price = product_info.get("product_price")
	old_price = product_info.get("old_price")
	return {
			"price": price,
			"old_price": old_price
		}