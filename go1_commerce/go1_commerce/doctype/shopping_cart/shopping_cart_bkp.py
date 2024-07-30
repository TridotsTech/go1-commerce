# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.core.doctype.domain_settings.domain_settings import get_active_domains
from frappe.utils import flt
from go1_commerce.utils.setup import get_settings_from_domain
from go1_commerce.go1_commerce.api import check_domain
from go1_commerce.go1_commerce.api import get_product_price

class ShoppingCart(Document):
	def validate(self):
		from go1_commerce.go1_commerce.api import check_domain		
		if self.cart_type == 'Shopping Cart':			
			if not check_domain('restaurant'):
				self.validate_cart_qty()
		if self.items and check_domain('b2b'):
			for cartitem in self.items:
				user_id = frappe.db.get_value("Customers", self.customer, "user_id")
				if not user_id:
					user_id = frappe.session.user
				role = frappe.get_roles(user_id)
				roles = ','.join('"{0}"'.format(r) for r in role)
				query = '''SELECT price FROM `tabProduct Pricing Rule` WHERE parent="{product}" AND parentfield="pricing_rule" AND role IN ({roles}) ORDER BY creation DESC'''.format(roles=roles,product=cartitem.product)
				product_pricing_rule = frappe.db.sql('''{query}'''.format(query=query),as_dict=1)
				if product_pricing_rule:
					cartitem.price = product_pricing_rule[0].price
				else:
					product_info = frappe.get_doc("Product",cartitem.product)
					product_price = product_info.price
					price_details = get_product_price(product_info, customer=self.customer)
					if price_details and price_details.get('discount_amount'):
						product_price = price_details.get('rate')
					cartitem.price = product_price

		if check_domain('restaurant'):
			if not self.business:
				if self.items:
					self.business = frappe.db.get_value('Product', self.items[0].product, 'restaurant')
		self.validate_item_price()	
		self.validate_subtotal_discount_forfree_item()	
	
	def validate_cart_qty(self):
		if self.items:
			cart_settings = get_settings_from_domain('Shopping Cart Settings')
			qty_count = sum(int(x.quantity) for x in self.items if x.quantity)
			if int(qty_count) >= cart_settings.max_cart_items:
				frappe.throw(frappe._('Maximum {0} products can be added in your shopping cart'.format(cart_settings.max_cart_items)))

	def validate_item_price(self):
		from go1_commerce.go1_commerce.doctype.discounts.discounts import get_product_discount
		from go1_commerce.go1_commerce.api import validate_attributes_stock as _validate_stock
		free_items = []
		if self.items:
			for item in self.items:

				if not item.is_free_item:
					allow = False
					if self.flags.get('__update') == 1:
						allow = True
					if item.get('__islocal') or item.get('__unsaved'):
						allow = True
					if allow:	
						product_info = None
						if frappe.db.exists("Product",item.product):		
							product_info = frappe.get_doc('Product', item.product)
							if check_domain('b2b'):
								user_id = frappe.db.get_value("Customers", self.customer, "user_id")
								if not user_id:
									user_id = frappe.session.user
								role = frappe.get_roles(user_id)
								roles = ','.join('"{0}"'.format(r) for r in role)
								query = '''SELECT price FROM `tabProduct Pricing Rule` WHERE parent="{product}" AND parentfield="pricing_rule" AND role IN ({roles}) ORDER BY creation DESC'''.format(roles=roles,product=product_info.name)
								product_pricing_rule = frappe.db.sql('''{query}'''.format(query=query),as_dict=1)
								if product_pricing_rule:
									product_info.price = product_pricing_rule[0].price
							product_rate = item.price
							if product_info and product_info.get('custom_entered_price') and product_info.get('custom_entered_price') == 1:
								product_rate = item.price
							elif product_info:
								product_rate = product_info.price
							discount_info = None
							if item.attribute_description:
								res = _validate_stock(item.product, item.attribute_ids, item.attribute_description, item.quantity)
								if res and res['status'] == 'Success':
									if float(res['price']) > 0:								
										product_rate = res['price']								
								else:
									attribute_name = ''
									if '\n' not in item.attribute_ids:
										attribute_name = '"' + item.attribute_ids + '"'
									else:
										attribute_name = '"' + '","'.join(item.attribute_ids.split('\n'))[:-2]
									price = frappe.db.sql('''select sum(price_adjustment) as price from `tabProduct Attribute Option` where name in ({list})'''.format(list=attribute_name))
									if price and price[0][0]:
										product_rate = float(product_rate) + float(price[0][0])
									ab = frappe.db.sql('''select option_value, product_title from `tabProduct Attribute Option` where name in ({list})'''.format(list=attribute_name),as_dict = True)
									if ab:
										title = ''
										for pr in ab:
											if pr.option_value == ("Other Amount").lower():
												product_rate = item.price
											if pr.product_title and pr.product_title not in ['', '-'] and item.product_name != pr.product_title:
												title = pr.product_title
										if title not in ['', '-']:
											item.product_name = title
							item.price = product_rate
							item.discount_rule = None
							attribute_id = None
							if item.attribute_ids:
								attribute_id = item.attribute_ids.replace('\n','')
							pdt_array = ','.join('"{0}"'.format(r.product) for r in self.items)
							
							price_info = get_product_discount(product_info, item.quantity, product_rate, self.customer, website_type=self.website_type, attribute_id=attribute_id, product_array=pdt_array)
							if price_info.get('discount_amount'):
								
								item.price = price_info.get('rate')
								item.discount_rule = price_info.get('discount_rule')
							elif price_info.get('free_item') and self.cart_type == 'Shopping Cart':
								
								item.discount_rule = price_info.get('discount_rule')
								new_item = self.update_free_item(item, price_info)
								
								if new_item:
									free_items.append(new_item)
							elif price_info.get('products_list') and self.cart_type == 'Shopping Cart':
								item.discount_rule = price_info.get('discount_rule')
								new_item = self.update_free_item(item, price_info)
								if new_item:
									free_items.append(new_item)
							elif price_info.get('discount_rule'):
								item.discount_rule = price_info.get('discount_rule')
							if item.discount_rule and not price_info.get('free_item') and self.cart_type == 'Shopping Cart':
								
								self.validate_free_item(item, item.discount_rule)
				item.total = float(item.quantity) * float(item.price)
				if not item.is_free_item:
					self.calculate_item_tax(item)
		for itm in free_items:
			self.append('items', itm)
		self.tax = sum(item.tax for item in self.items if (item.tax and item.is_free_item != 1))
		self.tax_breakup = ''
		self.total = sum(item.total for item in self.items if item.is_free_item != 1)
		

	def validate_subtotal_discount_forfree_item(self):

		from go1_commerce.go1_commerce.doctype.discounts.discounts import get_ordersubtotal_discount_forfree_item
		price_info = get_ordersubtotal_discount_forfree_item(self.total, self.customer, self.items, total_weight=0, is_recurring=0, 
	shipping_method=None, payment_method=None, shipping_charges=0, business=None, website_type=None)
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
		tax_info = None
		from go1_commerce.go1_commerce.api import check_domain
		restaurant = check_domain('restaurant')
		if restaurant and self.business:
			tax_info = frappe.db.get_value('Business', self.business, 'sales_tax')
		elif not restaurant:
			tax_info = frappe.db.get_value('Product', item.product, 'tax_category')
		if tax_info:
			catalog_settings = get_settings_from_domain('Catalog Settings', business=self.business)
			tax_template = frappe.get_doc('Product Tax Template', tax_info)
			if tax_template.tax_rates:
				item_tax = 0
				item_breakup = ''
				for tax in tax_template.tax_rates:
					tax_value = 0
					if catalog_settings.included_tax:
						tax_value = (flt(item.total) * tax.rate / (100 + tax.rate))
					else:
						tax_value = flt(item.total) * tax.rate / 100
					item_tax = item_tax + tax_value
					item_breakup += str(tax.tax) + ' - ' + str(tax.rate) + '% - ' + str(tax_value) + '\n'
				item.tax = item_tax
				item.tax_breakup = item_breakup

	def update_free_item(self, cart_item, price_info):
		# add free item
		if price_info and price_info.get('same_product')==0:
			if price_info.get('products_list'):
				for discount_item in price_info.get('products_list'):
					qty = int(discount_item.get('free_qty'))
					val = float(cart_item.get('quantity')) / float(price_info.get('min_qty'))
					if val > 0:
						qty = int(discount_item.get('free_qty')) * int(val)
					updated = 0
					for item in self.items:
						if item.is_free_item and item.discount_rule == cart_item.get('discount_rule') and item.product != cart_item.get('product'):
							updated = 1
							item.quantity = qty

					if not updated:
						product_name, rate = frappe.db.get_value('Product', discount_item.get('free_item'), ['item','price'])
						new_item = None
						from datetime import datetime
						new_item = {
								"product": discount_item.get('free_item'),
								"quantity": qty,
								"price": rate,
								"product_name": product_name,
								"total": float(rate) * float(qty),
								"is_free_item": 1,
								"discount_rule": price_info.get('discount_rule'),
								"creation": datetime.now()
							}
						if discount_item.get('attribute_ids'):
							html = ''
							options = frappe.db.sql('''select o.price_adjustment, o.option_value, p.attribute from `tabProduct Attribute Option` o left join `tabProduct Attribute Mapping` p on p.name = o.attribute_id where o.name=%(name)s and o.parent=%(parent)s''',{'name': discount_item.get('attribute_ids'), 'parent': discount_item.get('free_item')},as_dict=1)
							if options:
								html += '<div class="cart-attributes"><span class="attr-title">'+options[0].attribute+' </span> : <span>'+options[0].option_value+'</span></div>'
								rate = float(rate) + float(options[0].price_adjustment)
								total = float(rate) * float(qty)
								new_item['price'] = rate
								new_item['total'] = total
							new_item['attribute_ids'] = discount_item.get('attribute_ids')
							new_item['attribute_description'] = html
						return new_item
						
		else:
			
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
					options = frappe.db.sql('''select o.price_adjustment, o.option_value, p.attribute from `tabProduct Attribute Option` o left join `tabProduct Attribute Mapping` p on p.name = o.attribute_id where o.name=%(name)s and o.parent=%(parent)s''',{'name': attr[0]['attribute_ids'], 'parent': price_info.get('free_item')},as_dict=1)
					if options:
						html += '<div class="cart-attributes"><span class="attr-title">'+options[0].attribute+' </span> : <span>'+options[0].option_value+'</span></div>'
						rate = float(rate) + float(options[0].price_adjustment)
						total = float(rate) * float(qty)
						new_item['price'] = rate
						new_item['total'] = total
				
				if cart_item.get('product') == price_info.get('free_item'):
					new_item['attribute_ids'] = cart_item.get('attribute_ids')
					new_item['attribute_description'] = cart_item.get('attribute_description')				
				
				return new_item

	def validate_free_item(self, cart_item, discount_rule):
		for item in self.items:
			if item.is_free_item:
				if item.discount_rule == discount_rule:
					self.remove(item)

	def validate_price_stock(self):
		if self.items:
			for item in self.items:
				
				if not item.is_free_item:
					product_info = frappe.get_doc('Product', item.product)
					if item.attribute_ids:
						if product_info.inventory_method == 'Track Inventory By Product Attributes':
							self.validate_attributes_stock(item, product_info)
						else:
							self.validate_stock(item, product_info)
					else:
						self.validate_stock(item, product_info)
	
	def validate_stock(self, cart_item, product_info):
		if product_info.inventory_method == 'Track Inventory':
			if product_info.maximum_order_qty and product_info.maximum_order_qty < product_info.stock:
				if int(cart_item.quantity) > product_info.maximum_order_qty:
					frappe.throw(frappe._('Sorry! Maximum allowed quantity is {0}'.format(product_info.maximum_order_qty)))
			else:
				if int(cart_item.quantity) > product_info.stock:
					frappe.throw(frappe._('Sorry! Available stock is {0}'.format(product_info.stock)))
		elif product_info.inventory_method == 'Dont Track Inventory':								
			if product_info.maximum_order_qty:
				if not int(cart_item.quantity) <= product_info.maximum_order_qty:
					frappe.throw(frappe._('Sorry! Maximum allowed quantity is {0}'.format(product_info.maximum_order_qty)))
			if product_info.minimum_order_qty:
				if not int(cart_item.quantity) >= product_info.minimum_order_qty:
					cart_item.quantity = product_info.minimum_order_qty

	def validate_attributes_stock(self, cart_item, product_info):
		from go1_commerce.go1_commerce.api import validate_attributes_stock as _validate_stock
		res = _validate_stock(cart_item.product, cart_item.attribute_ids, cart_item.attribute_description, cart_item.quantity)
		
		if res and res['status'] == 'Failed':
			frappe.throw(frappe._('{0}'.format(res['message'])))
		if not res:
			self.validate_stock(cart_item, product_info)

	def calculate_product_tax(self):
		if self.items:
			cart_total = total_tax = total = 0
			tax_splitup=[]
			for item in self.items:
				item.total = float(item.quantity) * float(item.price)
				if not item.is_free_item:
					item_total_tax = 0
					item_breakup = ''
					cart_total = flt(cart_total) + flt(item.total)
					item_tax = frappe.db.get_value('Product',item.product,'tax_category')
					if item_tax:
						tax_template = frappe.get_doc('Product Tax Template',item_tax)
						if tax_template.tax_rates:
							for tax in tax_template.tax_rates:
								tax_value = 0
								catalog_settings = get_settings_from_domain('Catalog Settings')
								if catalog_settings.included_tax:
									tax_value = round((flt(item.total)*tax.rate/(100+tax.rate)),2)
								else:
									tax_value = round(flt(item.total)*tax.rate/100,2)
								item_total_tax = item_total_tax+tax_value
								item_breakup += str(tax.tax) + ' - ' + str(tax.rate) + '% - ' + str(tax_value) + '\n'
								cur_tax = next((x for x in tax_splitup if (x['type'] == tax.tax and x['rate'] == tax.rate)), None)
								if cur_tax:
									for it in tax_splitup:
										if it['type'] == tax.tax:
											it['amount'] = it['amount'] + tax_value
								else:
									tax_splitup.append({'type':tax.tax,'rate':round(float(tax.rate),2),'amount':tax_value})
							total_tax = total_tax + item_total_tax
						item.tax_breakup = item_breakup
						item.tax = item_total_tax
					else:
						item.tax_breakup = ''
						item.tax = 0
			self.tax = total_tax
			self.total = cart_total

			if tax_splitup:
				tax_sp = ''
				for item in tax_splitup:
					rate_tax = ("{:12.2f}".format(item['rate']))
					tax_sp += str(item['type'])+' - '+ rate_tax + '% - '+str(round(item['amount'],2))+'\n'
				self.tax_breakup = tax_sp
		else:
			self.tax = 0
			self.total = 0
			self.tax_breakup = ''
	
	def calculate_business_tax(self):
		self.tax = 0
		self.total = 0
		self.tax_breakup = ''
		if self.items and self.business:
			cart_total = total_tax = total = 0
			tax_splitup=[]
			business_tax = frappe.db.get_value('Business',self.business,'sales_tax')
			if business_tax:
				tax_template = frappe.get_doc('Product Tax Template',business_tax)
				if tax_template.tax_rates:
					for item in self.items:
						if not item.is_free_item:
							item_total_tax = 0
							item_breakup = ''
							cart_total = cart_total + item.total
							for tax in tax_template.tax_rates:
								tax_value = item.total * tax.rate / 100
								item_total_tax = item_total_tax + tax_value
								item_breakup+=str(tax.tax) + ' - ' + str(tax.rate) + '% - ' + str(tax_value) + '\n'
								cur_tax=next((x for x in tax_splitup if (x['type'] == tax.tax and x['rate'] == tax.rate)),None)
								if cur_tax:
									for it in tax_splitup:
										if it['type'] == tax.tax:
											it['amount'] = it['amount'] + tax_value
								else:
									tax_splitup.append({'type':tax.tax,'rate':tax.rate,'amount':tax_value})
							total_tax = total_tax + item_total_tax
							item.tax_breakup = item_breakup
							item.tax = item_total_tax
					self.tax = total_tax
					self.total = cart_total
					if tax_splitup:
						tax_sp = ''
						for item in tax_splitup:
							tax_sp += str(item['type']) + ' - ' + str(item['rate']) + '% - ' + str(round(item['amount'],2)) + '\n'
						self.tax_breakup = tax_sp					
			else:
				self.total = cart_total

def check_cart_discounts():
	cart_list = frappe.db.sql('''select name from `tabShopping Cart` where exists (select discount_rule from `tabCart Items` c where c.parent = `tabShopping Cart`.name)''',as_dict=1)
	for item in cart_list:
		doc = frappe.get_doc('Shopping Cart', item.name)
		doc.save(ignore_permissions=True)