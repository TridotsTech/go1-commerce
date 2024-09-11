# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt
from frappe.query_builder import DocType, Field, Order
from frappe.query_builder.functions import IfNull,Function, Trim,Avg, Count, Sum, Concat, Coalesce

class ShoppingCart(Document):
	def validate(self):		
		if self.cart_type == 'Shopping Cart':
			if self.items:
				self.validate_max_cart_qty()
		self.validate_item_price_apply_discount()	
		self.validate_subtotal_discount_for_free_item()	
	
	def validate_max_cart_qty(self):
		""" Validating maximum cart qty by shopping cart settings value """
		qty_count = sum(x.quantity for x in self.items if x.quantity)
		from go1_commerce.utils.setup import get_settings_value
		max_cart_items = get_settings_value('Shopping Cart Settings',"max_cart_items")
		if qty_count >= max_cart_items:
			frappe.throw(frappe._(f'Maximum {max_cart_items} products can be added in your shopping cart.'))

	def validate_item_price_apply_discount(self):
		"""  Get item and variant price and apply discounts """
		free_items = []
		if self.items:
			for item in self.items:
				if not item.is_free_item and (self.flags.get('__update') or item.get('__islocal') \
								  or item.get('__unsaved')):
					if frappe.db.exists("Product",item.product):		
						self.get_item_price(item,free_items)
					else:
						frappe.throw(frappe._(f"The item <b>{item.product_name}</b>\
									is not available.Please remove the item from the cart."))
				if not item.price:
					item.price = frappe.db.get_value("Product",item.product,"price")
				item.total = float(item.quantity) * float(item.price)
				if not item.is_free_item:
					self.calculate_item_tax(item)
		for itm in free_items:
			self.append('items', itm)
		self.tax = sum(item.tax for item in self.items if (item.tax and item.is_free_item != 1))
		self.tax_breakup = ''
		self.total = sum(item.total for item in self.items if item.is_free_item != 1)
		
	def get_item_price(self,item,free_items):
		product_info = frappe.get_doc('Product', item.product)
		if item.attribute_ids:
			self.update_variant_price(item)
		attribute_id = None
		if item.attribute_ids:
			attribute_id = item.attribute_ids.replace('\n','')
		pdt_array = ','.join('"{0}"'.format(r.product) for r in self.items)
		from go1_commerce.go1_commerce.doctype.discounts.discounts import get_product_discount
		after_dis_price_info = get_product_discount(product_info, item.quantity, item.price, self.customer,
									attribute_id = attribute_id, product_array = pdt_array)
		if after_dis_price_info.get('discount_amount'):
			item.old_price = item.price
			item.price = after_dis_price_info.get('rate')
			item.discount_rule = after_dis_price_info.get('discount_rule')
		elif after_dis_price_info.get('free_item') and self.cart_type == 'Shopping Cart':
			item.discount_rule = after_dis_price_info.get('discount_rule')
			new_item = self.update_free_item(item, after_dis_price_info)
			if new_item:
				free_items.append(new_item)
		elif after_dis_price_info.get('products_list') and self.cart_type == 'Shopping Cart':
			item.discount_rule = after_dis_price_info.get('discount_rule')
			new_item = self.update_free_item(item, after_dis_price_info)
			if new_item:
				free_items.append(new_item)
		elif after_dis_price_info.get('discount_rule'):
			item.discount_rule = after_dis_price_info.get('discount_rule')
		if item.discount_rule and not after_dis_price_info.get('free_item') and self.cart_type == 'Shopping Cart':
			self.validate_free_item(item.discount_rule)
			
	def update_variant_price(self,item):
		attribute_ids = None
		product_rate = item.price
		if '\n' not in item.attribute_ids:
			attribute_ids = '"' + item.attribute_ids + '"'
		else:
			attribute_ids = '"' + '","'.join(item.attribute_ids.split('\n'))[:-2]
		# cartattrubutes = [item.attribute_ids.replace("\n", "")]
		ProductAttributeOption = DocType('Product Attribute Option')
		query = frappe.qb.from_(ProductAttributeOption).select(Sum(ProductAttributeOption.price_adjustment).as_("price")).where(ProductAttributeOption.name.isin(attribute_ids))
		price_adjustment= query.run(as_dict=True)
		if price_adjustment:
			product_rate = product_rate + price_adjustment[0].price
		query = frappe.qb.from_(ProductAttributeOption).select(ProductAttributeOption.option_value, ProductAttributeOption.product_title).where(ProductAttributeOption.name.isin(attribute_ids))
		attribute_opts= query.run(as_dict=True)
		if attribute_opts:
			title = None
			for attr_itms in attribute_opts:
				if attr_itms.option_value == "other amount":
					product_rate = item.price
				if attr_itms.product_title and item.product_name != attr_itms.product_title:
					title = attr_itms.product_title
			if title and title not in ['', '-']:
				item.product_name = title
		item.price = product_rate
	
	def update_free_item(self, cart_item, price_info):
		if price_info and not price_info.get('same_product'):
			if price_info.get('products_list'):
				for discount_item in price_info.get('products_list'):
					qty = int(discount_item.get('free_qty'))
					val = float(cart_item.get('quantity')) / float(price_info.get('min_qty'))
					if val > 0:
						qty = int(discount_item.get('free_qty')) * int(val)
					updated = 0
					for item in self.items:
						if item.is_free_item and item.discount_rule == cart_item.get('discount_rule'):
							if item.product != cart_item.get('product'):
								updated = 1
								item.quantity = qty
					if not updated:
						return self.get_price_diff_item(discount_item,price_info,qty)			
		else:
			return self.get_price_same_item(self,price_info,cart_item)
			
	def get_price_diff_item(discount_item,price_info,qty):
		product_name, rate = frappe.db.get_value('Product', discount_item.get('free_item'), ['item','price'])
		new_item = None
		from datetime import datetime
		new_item = {
				"product": discount_item.get('free_item'),
				"quantity": qty,
				"price": rate,
				"product_name": product_name,
				"total": rate * qty,
				"is_free_item": 1,
				"discount_rule": price_info.get('discount_rule'),
				"creation": datetime.now()
			}
		if discount_item.get('attribute_ids'):
			html = ''
			ProductAttributeOption = DocType('Product Attribute Option')
			ProductAttributeMapping = DocType('Product Attribute Mapping')
			query = (
				frappe.qb.from_(ProductAttributeOption)
				.left_join(ProductAttributeMapping).on(ProductAttributeMapping.name == ProductAttributeOption.attribute_id)
				.select(ProductAttributeOption.price_adjustment, ProductAttributeOption.option_value, ProductAttributeMapping.attribute)
				.where(ProductAttributeOption.name == discount_item.get('attribute_ids'))
				.where(ProductAttributeOption.parent == discount_item.get('free_item'))
			)
			options= query.run(as_dict=True)
			if options:
				html += '<div class="cart-attributes"><span class="attr-title">'+ options[0].attribute + \
						' </span> : <span>' + options[0].option_value +'</span></div>'
				rate = rate + options[0].price_adjustment
				total = rate * qty
				new_item['price'] = rate
				new_item['total'] = total
			new_item['attribute_ids'] = discount_item.get('attribute_ids')
			new_item['attribute_description'] = html
		return new_item
	
	def get_price_same_item(self,price_info,cart_item):
		qty = int(price_info.get('free_qty'))
		val = float(cart_item.get('quantity')) / float(price_info.get('min_qty'))
		if val > 0:
			qty = int(price_info.get('free_qty')) * int(val)
		updated = 0
		for item in self.items:
			if not item.discount_rule:
				item.discount_rule = price_info.get('discount_rule')
			if item.is_free_item and item.discount_rule == cart_item.get('discount_rule'):
				updated = 1
				item.quantity = qty
		if not updated:
			product_name, rate = frappe.db.get_value('Product', price_info.get('free_item'), ['item','price'])
			new_item = None
			from datetime import datetime
			new_item = {
					"product": price_info.get('free_item'),
					"quantity": qty,
					"price": rate,
					"product_name": product_name,
					"total": float(rate) * float(qty),
					"is_free_item": 1,
					"discount_rule": price_info.get('discount_rule'),
					"creation": datetime.now()
				}
			attr = price_info.get('products_list')
			if len(attr)>0 and attr[0]['attribute_ids']:
				html = ''
				ProductAttributeOption = DocType('Product Attribute Option')
				ProductAttributeMapping = DocType('Product Attribute Mapping')
				query = (
					frappe.qb.from_(ProductAttributeOption)
					.left_join(ProductAttributeMapping).on(ProductAttributeMapping.name == ProductAttributeOption.attribute_id)
					.select(
						ProductAttributeOption.price_adjustment,
						ProductAttributeOption.option_value,
						ProductAttributeMapping.attribute
					)
					.where(ProductAttributeOption.name == attr[0]['attribute_ids'])
					.where(ProductAttributeOption.parent == price_info.get('free_item'))
				)
				options= query.run(as_dict=True)
				if options:
					html += '<div class="cart-attributes"><span class="attr-title">'+options[0].attribute+' </span> : <span>'\
							+options[0].option_value+'</span></div>'
					rate = float(rate) + float(options[0].price_adjustment)
					total = float(rate) * float(qty)
					new_item['price'] = rate
					new_item['total'] = total
			if cart_item.get('product') == price_info.get('free_item'):
				new_item['attribute_ids'] = cart_item.get('attribute_ids')
				new_item['attribute_description'] = cart_item.get('attribute_description')				
			return new_item

	def validate_subtotal_discount_for_free_item(self):
		from go1_commerce.go1_commerce.doctype.discounts.discounts import get_ordersubtotal_discount_forfree_item
		price_info = get_ordersubtotal_discount_forfree_item(subtotal=self.total, cart_items=self.items, customer_id=self.customer, total_weight=0, 
	shipping_method=None, payment_method=None, shipping_charges=0)
		if price_info and price_info.get('free_item'):
			if price_info.get('products_list'):
				free_items = list(filter(lambda x: x.is_free_item == 1, self.items))
				if len(free_items)>0:
					for item in self.items:
						if item.is_free_item and item.discount_rule == price_info.get('discount_rule'):
							self.remove(item)
				new_items = []
				for itm in self.items:
					if price_info.get('free_item') and self.cart_type == 'Shopping Cart':
						new_item = self.update_free_item(itm, price_info)
						new_items.append(new_item)
				for n in new_items:
					self.append('items', n)
			else:
				for item in self.items:
					if item.is_free_item:
						self.remove(item)

	def calculate_item_tax(self, item):
		tax_info = frappe.db.get_value('Product', item.product, 'tax_category')
		if tax_info:
			from go1_commerce.utils.setup import get_settings_value
			included_tax = get_settings_value('Catalog Settings',"included_tax")
			tax_template = frappe.get_doc('Product Tax Template', tax_info)
			if tax_template.tax_rates:
				item_tax = 0
				item_breakup = ''
				for tax in tax_template.tax_rates:
					tax_value = 0
					if included_tax:
						tax_value = (flt(item.total) * tax.rate / (100 + tax.rate))
					else:
						tax_value = flt(item.total) * tax.rate / 100
					item_tax = item_tax + tax_value
					item_breakup += str(tax.tax) + ' - ' + str(tax.rate) + '% - ' + str(tax_value) + '\n'
				item.tax = item_tax
				item.tax_breakup = item_breakup

	def validate_free_item(self,discount_rule):
		""" if discount is not applied then to remove the added free product """
		for item in self.items:
			if item.is_free_item:
				if item.discount_rule == discount_rule:
					self.remove(item)
					