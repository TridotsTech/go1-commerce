# by gopi on 12/4/24

from __future__ import unicode_literals, print_function
import frappe, json
from frappe import _
from frappe.utils import flt,today 
from datetime import datetime
from go1_commerce.utils.utils import other_exception,get_customer_from_token
from go1_commerce.utils.setup import get_settings

class CrudCart:
	def insert_guest_customer(self):
		new_customer = frappe.get_doc({'doctype': 'Customers',
									'naming_series': 'GC-',
									'first_name': 'Guest'
									}).insert(ignore_permissions=True,ignore_mandatory = True)
		frappe.local.cookie_manager.set_cookie('guest_customer', new_customer.name)
		frappe.local.cookie_manager.set_cookie('customer_id', new_customer.name)
		return new_customer.name
	
	def validate_stock_min_max_qty(self,item_info,qty,attribute_ids = None):
		result = None
		if isinstance(qty, str):
			qty = int(qty)
		if item_info.disable_add_to_cart_button == 1:
			result = { 'status': False, 'message': _(f'Sorry! no stock available for the item {item_info.item}.') }
		elif item_info.inventory_method == 'Dont Track Inventory':
			if qty >= item_info.minimum_order_qty and qty <= item_info.maximum_order_qty:
				result = {'status': True}
			else:
				if qty < item_info.minimum_order_qty:
					result = {'status': False, 
							'message': _(f'Minimum order quantity of the item {item_info.item} is {item_info.minimum_order_qty}.')}
				elif qty > item_info.maximum_order_qty:
					result = { 'status': False, 
							'message': _(f'Maximum order quantity of the item {item_info.item} is {item_info.maximum_order_qty}.')}
		elif item_info.inventory_method == 'Track Inventory':
			result = self.check_inventory_method_in_item(item_info,qty)
		else:
			if attribute_ids:
				check_data = frappe.db.get_value('Product Variant Combination',{'parent': item_info.name,
											'attribute_id':attribute_ids},['stock',"name"], as_dict = 1)
				result = self.check_attr_id_in_stock_min_qty(check_data,item_info,qty)

			else:
				result = {"status":False,"message":f"The Attribute id is missing for the item {item_info.item}."}
		return result
	
	def insert_cart_items(self,item_code, qty, qty_type, rate = 0, cart_type = "Shopping Cart",
						attribute = None, attribute_id = None,is_gift_card = None,sender_name = None,
						sender_email = None,sender_message = None,recipient_email = None,
						recipient_date_of_birth = None,recipient_name = None, device_type = None,
						customer = None):
		if not customer:
			customer = get_customer_from_token()
			if not customer:
				cart_settings = frappe.get_single('Shopping Cart Settings')
				if cart_settings.allow_anonymous_user_to_addtocart:
					customer = self.insert_guest_customer()
		if customer:
			product_details_list = ["disable_add_to_cart_button",'item',"inventory_method","minimum_order_qty",
											"maximum_order_qty","stock","name","price"]
			product_details = frappe.db.get_value(
												"Product",
												{
													'name': item_code, 
													'is_active': 1, 
													'status': 'Approved'
												},
													product_details_list, as_dict = 1)
			if product_details:
				return self.validate_update_cart(cart_type,customer,product_details,attribute,qty,rate,
							qty_type,attribute_id,is_gift_card,sender_name,sender_email,sender_message,
							recipient_email,recipient_date_of_birth,recipient_name,device_type)
			else:
				return {'status': 'failed','message': 'Product not exist.'}
		else:
			return {'status': 'failed','message': 'You are not a valid Customer.'}
		
	def validate_update_cart(self,cart_type,customer,product_details,attribute,qty,rate,qty_type,
								attribute_id,is_gift_card,sender_name,sender_email,sender_message,
								recipient_email,recipient_date_of_birth,recipient_name,device_type):
		exe_cart = frappe.db.get_value('Shopping Cart',{'customer': customer,
										'cart_type': cart_type},"name")
		if exe_cart:
			if cart_type == 'Shopping Cart':
				order_settings = get_settings('Order Settings')
				if order_settings.pre_order_not_allow_cart == 1:
					pre_order_status = self.validate_pre_order_items(exe_cart,product_details.name)
					if pre_order_status.get('status') == 'failed':
						return {'status': 'failed','message': pre_order_status.get('message')}
			return self.insert_update_cart_item(customer,product_details,exe_cart,attribute,
											cart_type,qty,rate,qty_type,attribute_id,
											is_gift_card,sender_name,sender_email,sender_message,
											recipient_email,recipient_date_of_birth,
											recipient_name,device_type)
		else:
			res = self.insert_new_cart_item(customer,cart_type,product_details,qty,rate,None,
										attribute,attribute_id,is_gift_card,sender_name,
										sender_email,sender_message,recipient_email, 
										recipient_date_of_birth,recipient_name,device_type)
			if res.get('status'):
				return get_customer_cart(cart_type,customer)
			else:
				return res
		
	def insert_update_cart_item(self,customer,product_details,cart_id,attribute,cart_type,qty,
								rate,qty_type,attribute_id,is_gift_card,sender_name,sender_email,
								sender_message,recipient_email,recipient_date_of_birth,
								recipient_name,device_type):
		cartitem = None
		if attribute_id:
			cartitem = frappe.db.get_value('Cart Items',
									{'product': product_details.name, 'parent': cart_id, 
												'attribute_ids': attribute_id,'is_free_item': 0},'name')
		else:
			cartitem = frappe.db.get_value('Cart Items',{'product': product_details.name,
											'parent': cart_id,'is_free_item': 0},'name')
		if cartitem:
			return self.update_exe_cart_item_qty(customer,product_details,cartitem,cart_type,qty,qty_type)
		else:
			res = self.insert_new_cart_item(customer,cart_type,product_details,qty,rate,cart_id,
										attribute,attribute_id,is_gift_card,sender_name,sender_email,
										sender_message,recipient_email,recipient_date_of_birth,
										recipient_name,device_type)
			if res.get('status'):
				return get_customer_cart(cart_type,customer)
			else:
				return res
	
	def insert_new_cart_item(self,customer,cart_type,product_details,qty,rate,cart_id,attribute, 
						attribute_id,is_gift_card,sender_name,sender_email,sender_message,
						recipient_email,recipient_date_of_birth,recipient_name,device_type):
			cart = None
			if cart_type == "Shopping Cart":
				resp = self.validate_stock_min_max_qty(product_details,qty,attribute_id)
				if not resp.get("status"):
					return resp
			if attribute_id:
				variant_price_info = frappe.db.get_value('Product Variant Combination', 
													{'parent': product_details.name, 'attribute_id': attribute_id},
													["price","old_price"],as_dict = 1)
				if variant_price_info:
					product_details.price = variant_price_info.price
					product_details.old_price = variant_price_info.old_price
				else:
					return {"status":False,"message":f"Price details not found for the product {product_details.item}."}
			if cart_id:
				cart = frappe.get_doc('Shopping Cart', cart_id)
			else:
				cart = frappe.new_doc('Shopping Cart')
				cart.customer = customer
				cart.cart_type = cart_type
				cart.website_type = 'Website'
			self.append_cart_when_insert_new(cart,product_details,qty,attribute, attribute_id,is_gift_card,sender_name,
								sender_email,sender_message,recipient_email,recipient_date_of_birth,recipient_name,device_type)
			return {'status': True,'message':'Cart added'}

	def append_cart_when_insert_new(self,cart,product_details,qty,attribute, attribute_id,is_gift_card,sender_name,
							  sender_email,sender_message,recipient_email,recipient_date_of_birth,recipient_name,device_type):
		cart.append('items', {
			'product': product_details.name,
			'product_name':product_details.item,
			'old_price':product_details.old_price,
			'quantity': qty,
			'price': product_details.price,
			'attribute_description': attribute,
			'attribute_ids': attribute_id,
			'creation': datetime.now(),
			'__islocal': 1,
			'is_gift_card':is_gift_card,
			'sender_name':sender_name,
			'sender_email':sender_email,
			'recipient_name':recipient_name,
			'recipient_email':recipient_email,
			'recipient_date_of_birth':recipient_date_of_birth,
			'sender_message':sender_message,
			'device_type': device_type
			})
		# frappe.log_error("cart",cart.as_dict())
		cart.save(ignore_permissions=True)

	def check_inventory_method_in_item(self,item_info,qty):
		if item_info.stock and item_info.stock >= qty:
			if qty >= item_info.minimum_order_qty and qty <= item_info.maximum_order_qty:
				result = {"status":True}
			else:
				if qty < item_info.minimum_order_qty:
					result = {'status': False, 
						'message': _(f'Minimum order quantity of the item {item_info.item} is {item_info.minimum_order_qty}.')}
				elif qty > item_info.maximum_order_qty:
					result = { 'status': False, 
							'message': _(f'Maximum order quantity of the item {item_info.item} is {item_info.maximum_order_qty}.')}
		else:
			result = { 'status': False,
					'message': _(f'Sorry! no stock available for the item {item_info.item}.')}
		return result

	def check_attr_id_in_stock_min_qty(self,check_data,item_info,qty):
		if check_data:
			if qty <= check_data.stock:
				if qty >= item_info.minimum_order_qty and qty <= item_info.maximum_order_qty:
					result = {'status': True}
				else:
					if not qty >= item_info.minimum_order_qty:
						result = {'status': False, 
							'message': _(f'Minimum order quantity of the item {item_info.item} is { item_info.minimum_order_qty}.')}
					elif not qty <= item_info.maximum_order_qty:
						result = {'status': False, 
							'message': _(f'Maximum order quantity of the item {item_info.item} is {item_info.maximum_order_qty}.')}
			else:
				result = {'status': False,'message':f'No stock available for the the item {item_info.item}.'}
		else:
			result = {'status': False,'message': f'Variant combination not found for the item {item_info.item}.'}
		return result
	
	def update_exe_cart_item_qty(self,customer,product_details,cartitem_id,cart_type,qty,qty_type):
		new_qty = qty
		cartitem = frappe.get_doc('Cart Items',cartitem_id)
		if qty_type not in ['add', 'sub']:
			if int(cartitem.quantity) < int(qty):
				new_qty = int(qty) - int(cartitem.quantity)
		if qty_type == 'add':
			cartitem.quantity = cartitem.quantity + new_qty
		elif qty_type == 'sub':
			cartitem.quantity = cartitem.quantity - new_qty
		else:
			cartitem.quantity = new_qty
		cartitem.total = cartitem.price * cartitem.quantity
		if cart_type == 'Shopping Cart':
			resp = self.validate_stock_min_max_qty(product_details,cartitem.quantity,cartitem.attribute_ids)
			if not resp.get('status'):
				return resp
		cartitem.save(ignore_permissions=True)
		return get_customer_cart(cart_type,customer)
	
	def update_cartitem(self,name, qty, qty_type = None):
		if not frappe.db.get_value("Cart Items",{"name":name}):
			return {'status': 'Failed',"message":"Cart item not found."}
		cart_id = frappe.db.get_value('Cart Items', name, 'parent')
		if cart_id:
			cart_item = frappe.get_doc("Cart Items",name)
			if qty_type == 'add':
				cart_item.quantity = qty + cart_item.quantity
			elif qty_type == 'sub':
				cart_item.quantity = cart_item.quantity - qty
			else:
				cart_item.quantity = qty
			product_details = frappe.db.get_value("Product",{'name': cart_item.product, 'is_active': 1, 'status': 'Approved'},
									["disable_add_to_cart_button",'item',"inventory_method","minimum_order_qty",
											"maximum_order_qty","stock","name"], as_dict = 1)
			resp = self.validate_stock_min_max_qty(product_details,cart_item.quantity,cart_item.attribute_ids)
			if not resp.get('status'):
				return resp
			else:
				cart_item.save(ignore_permissions=True)
				return {'status': 'success','message': 'Cart updated'}
		else:
			return {'status': 'Failed',"message":"product not found in cart to update"}
		
	def validate_pre_order_items(self,cart_id,item_code):
		cartitems = frappe.db.get_all('Cart Items',filters = {'parent': cart_id,"is_free_item":0},
								fields = ['product'])
		current_product_status = frappe.db.get_value("Product",item_code,"enable_preorder_product")
		for x in cartitems:
			cart_product_status = frappe.db.get_value("Product",x.product,"enable_preorder_product")
			if current_product_status != cart_product_status:
				if current_product_status == 1:
					return {'status': 'failed', 
							'message': 'Pre order Items shall not be combined with In-Stock items during\
										checkout. Please place pre order Item separately.'}
				else:
					return {'status': 'failed', 
							'message': 'In-Stock Items shall not be combined with \
										pre order items during checkout. Please place \
										In-Stock Items separately.'}
		return {'status': 'success'}

	def move_item_to_cart(self,name,customer_id = None):
		wishlist_item_doc = frappe.get_doc('Cart Items', name)
		if customer_id:
			customer = customer_id
		else:
			customer = get_customer_from_token()
		product_details = frappe.db.get_value("Product",{'name': wishlist_item_doc.product, 
									'is_active': 1, 'status': 'Approved'},["disable_add_to_cart_button",
									'item',"inventory_method","minimum_order_qty","maximum_order_qty",
									"stock","name"], as_dict = 1)
		if product_details.disable_add_to_cart_button == 1:
			return {"status":"failed",'message': f'No stock available for the item {product_details.item}.'}
		else:
			if customer:
				return self.validate_stock_update_cart(customer,product_details, wishlist_item_doc)
			else:
				return {"status":"failed","message":"Invalid customer."}

	def validate_stock_update_cart(self,customer,product_details,wishlist_item_doc):
		customer_cart = frappe.db.get_value('Shopping Cart',{'customer': customer, 
									'cart_type': 'Shopping Cart'},"name")
		if customer_cart:
			if wishlist_item_doc.attribute_ids:
				shopping_cart_item = frappe.db.get_value('Cart Items',{'parent': customer_cart, 
										'product': wishlist_item_doc.product,
										'attribute_ids': wishlist_item_doc.attribute_ids},"name")
			else:
				shopping_cart_item = frappe.db.get_value('Cart Items',{'parent': customer_cart, 
											'product': wishlist_item_doc.product})
			if shopping_cart_item:
				check_stock = self.update_item_to_existing_cart(wishlist_item_doc,product_details,shopping_cart_item)
				if not check_stock.get("status"):
					return check_stock
				else:
					wishlist_item_doc.delete()
					frappe.db.commit()
			else:
				check_stock = self.add_item_to_existing_cart(wishlist_item_doc,product_details,customer_cart)
				if not check_stock.get("status"):
					return check_stock
				frappe.db.commit()
		else:
			cart = frappe.get_doc({'doctype': 'Shopping Cart','customer': customer,
								'cart_type': 'Shopping Cart'}).insert(ignore_permissions=True)
			check_stock = self.add_item_to_existing_cart(wishlist_item_doc,product_details,cart.name)
			if not check_stock.get("status"):
				return check_stock
			frappe.db.commit()
		return get_cart_items(customer)
	
	def update_item_to_existing_cart(self,wishlist_item_doc,product_details,shopping_cart_item):
		cartitem = frappe.get_doc('Cart Items', shopping_cart_item)
		cartitem.quantity = cartitem.quantity + wishlist_item_doc.quantity
		cartitem.total = cartitem.price * cartitem.quantity
		resp = self.validate_stock_min_max_qty(product_details,cartitem.quantity,cartitem.attribute_ids)
		if resp.get('status'):
			cartitem.save(ignore_permissions=True)
		return resp
	
	def add_item_to_existing_cart(self,wishlist_item_doc,product_details,customer_cart):
		wishlist_item_doc.parent = customer_cart
		resp = self.validate_stock_min_max_qty(product_details,wishlist_item_doc.quantity,wishlist_item_doc.attribute_ids)
		if resp.get("status"):
			wishlist_item_doc.save()
			parent_doc = frappe.get_doc('Shopping Cart',wishlist_item_doc.parent)
			parent_doc.save(ignore_permissions=True)
		return resp
	
	def move_all_tocart(self,customer_id = None):
		if customer_id:
			customer = customer_id
		else:
			customer = get_customer_from_token()
		wishlist_id = frappe.db.get_value('Shopping Cart',{'customer': customer,
								'cart_type': 'Wishlist'},'name')
		if wishlist_id:
			wishlist_items = frappe.db.get_all("Cart Items",filters={"parent":wishlist_id},
											fields=['name','product'])
			if wishlist_items:
				error_msg = ""
				for x in wishlist_items:
					resp = self.move_wishlist_to_cart(x.name, customer)
					if not resp.get("status"):
						error_msg += f'{resp.get("message")},'
				if error_msg:
					return {"status":"failed","message":error_msg.rstrip(',')}	
				else:
					return {"status":"success"}
			else:
				return {"status":"failed","message":"No items in Wishlist"}
		else:
			return {"status":"failed","message":"No items in Wishlist"}
	
	def move_wishlist_to_cart(self,wishlist_item_id, customer):
		wishlist_item_doc = frappe.get_doc('Cart Items', wishlist_item_id)
		product_details = frappe.db.get_value("Product",{
															'name': wishlist_item_doc.product, 
															'is_active': 1, 
															'status': 'Approved'
														},
														[
															"disable_add_to_cart_button",
															'item',
															"inventory_method",
															"minimum_order_qty",
															"maximum_order_qty",
															"stock",
															"name"
														], as_dict = 1)
		customer_cart = frappe.db.get_value('Shopping Cart',{'customer': customer, 
									'cart_type': 'Shopping Cart'},"name")
		if customer_cart:
			self.check_customer_cart_exist_in_move_wishlist(
														wishlist_item_doc,
														product_details,
														customer_cart
													)
		else:
			cart = frappe.get_doc({
									'doctype': 'Shopping Cart',
									'customer': customer,
									'cart_type': 'Shopping Cart'
								}).insert(ignore_permissions = True)
			check_stock = self.add_item_to_existing_cart(
														wishlist_item_doc,
														product_details,
														cart.name
													)
			if not check_stock.get("status"):
				return check_stock
			frappe.db.commit()
		return {"status":True}
	
	def check_customer_cart_exist_in_move_wishlist(self,wishlist_item_doc,product_details,customer_cart):
		if wishlist_item_doc.attribute_ids:
			shopping_cart_item = frappe.db.get_value(
														'Cart Items',
														{'parent': customer_cart, 
														'product': wishlist_item_doc.product, 
														'attribute_ids': wishlist_item_doc.attribute_ids},
														"name"
													)
		else:
			shopping_cart_item = frappe.db.get_value(
														'Cart Items',
														{'parent': customer_cart, 
														'product': wishlist_item_doc.product}
													)
		if shopping_cart_item:
			check_stock = self.update_item_to_existing_cart(
														wishlist_item_doc,
														product_details,
														shopping_cart_item
													)
			if not check_stock.get("status"):
				return check_stock
			else:
				wishlist_item_doc.delete()
				frappe.db.commit()
		else:
			check_stock = self.add_item_to_existing_cart(
														wishlist_item_doc,
														product_details,
														customer_cart
													)
			if not check_stock.get("status"):
				return check_stock
			frappe.db.commit()

@frappe.whitelist(allow_guest = True)
def insert_cart_items(item_code, qty, qty_type, rate = 0, cart_type = "Shopping Cart",
						attribute = None, attribute_id = None,is_gift_card = None,sender_name = None,
						sender_email = None,sender_message = None,recipient_email = None,
						recipient_date_of_birth = None,recipient_name = None, device_type = None,
						customer = None):
	try:
		insert_cart = CrudCart()
		return insert_cart.insert_cart_items(item_code, qty, qty_type, rate, cart_type,
						attribute, attribute_id,is_gift_card ,sender_name ,
						sender_email ,sender_message ,recipient_email ,
						recipient_date_of_birth ,recipient_name , device_type,
						customer)
	except Exception:
		other_exception("Error in v2.cart.insert_cartItems")

@frappe.whitelist(allow_guest = True)
def update_cartitem(name, qty, qty_type = None):
	try:
		update_cart = CrudCart()
		return update_cart.update_cartitem(name, qty, qty_type)
	except Exception:
		other_exception("Error in v2.cart.update_cartitem")
		return {'status': 'error'}
		
@frappe.whitelist(allow_guest = True)
def move_item_to_cart(name,customer_id = None):
	try:
		move_cart = CrudCart()
		return move_cart.move_item_to_cart(name,customer_id)
	except Exception:
		other_exception("Error in v2.carts.move_item_to_cart")

@frappe.whitelist(allow_guest = True)
def move_all_tocart(customer_id = None):
	try:
		move_all_cart = CrudCart()
		return move_all_cart.move_all_tocart(customer_id)
	except Exception:
		other_exception("Error in v2.cart.move_all_tocart")

@frappe.whitelist(allow_guest = True)
def delete_cart_items(name,customer_id = None):
	try:
		if not customer_id:
			customer = get_customer_from_token()
		else:
			customer = customer_id
		if doc := frappe.db.get_value('Cart Items',{'name':name},['name','parent','discount_rule'],as_dict = 1):
			check_free_doc = frappe.db.get_all('Cart Items',{'parent': doc.parent, 'is_free_item': 1,
															'discount_rule': doc.discount_rule})
			if check_free_doc:
				for del_item in check_free_doc:
					frappe.db.sql('''DELETE FROM `tabCart Items` WHERE name = %(name)s''',
											{'name': del_item.name})
					frappe.db.commit()
			frappe.db.sql(f''' DELETE FROM `tabCart Items` WHERE name = '{doc.name}' ''')
			frappe.db.commit()
			parent_doc = frappe.get_doc('Shopping Cart', doc.parent)
			parent_doc.save(ignore_permissions=True)
		return get_cart_items(customer)
	except Exception:
		other_exception("Error in v2.carts.delete_cart_items")
		return {"status":"Failed","message":"something went wrong"}
	
@frappe.whitelist()
def clear_cartitem():
	try:
		customer = get_customer_from_token()
		cart = frappe.db.get_value('Shopping Cart',{'customer': customer,
											'cart_type': 'Shopping Cart'},"name")
		if cart:
			frappe.db.sql(f''' DELETE FROM `tabCart Items` WHERE parent= '{cart}' ''')
			frappe.db.commit()
			parent_doc = frappe.get_doc('Shopping Cart', cart)
			parent_doc.tax = 0
			parent_doc.total = 0
			parent_doc.tax_breakup = ''
			parent_doc.save(ignore_permissions=True)
			return {"status":"success"}
		else:	
			return {"status":"failed","message":'No cart items found.'}
	except Exception:
		other_exception("Error in v2.cart.clear_cartitem")

@frappe.whitelist(allow_guest = True)
def get_cart_items(customer_id = None):
	try:
		if customer_id:
			customer = customer_id
		else:
			customer = get_customer_from_token()
		if customer:
			from go1_commerce.go1_commerce.v2.product import get_bought_together
			cart = get_customer_cart('Shopping Cart',customer)
			wishlist = get_customer_cart('Wishlist',customer)
			customer_bought = get_bought_together(customer)
			return {"status":"success",
		   			'cart': cart,
					'wishlist': wishlist,
					"you_may_like": customer_bought}
		else:
			return {"status":"failed","message":"You are not a valid Customer."}
	except Exception:
		other_exception("Error in v2.carts.get_cartItems")
		return {"status":"failed","message":"something went wrong"}

def get_items_if_customer_cart_exist(customer_cart):
	items = frappe.db.sql(f'''
		SELECT 
			CI.name,CI.product,CI.product_name AS item,
			CI.quantity,CI.price,CI.total,CI.product_name,
			PR.brand AS product_brand,PR.brand_name,
			CI.is_free_item,CI.is_fl_store_item,
			CI.attribute_description,CI.attribute_ids,
			CI.special_instruction,CI.tax_breakup,
			CI.old_price,PR.route,PR.minimum_order_qty,
			PR.image
		FROM 
			`tabCart Items` CI INNER JOIN `tabProduct` PR 
				ON PR.name = CI.product
		WHERE 
			PR.name = CI.product AND CI.parent = '{customer_cart.name}' 
		ORDER BY 
			CI.creation DESC ''', as_dict = 1)
	return items

def check_attr_id_in_item(item):
	if item.attribute_ids:
		attr_ids = item.attribute_ids.split('\n')
		attr_id_list = []
		for attr in attr_ids:
			if attr:
				attr_id_list.append(attr)
		attr_ids = ','.join(['"' + x + '"' for x in attr_id_list])
		options = frappe.db.sql(f''' SELECT image_list FROM `tabProduct Attribute Option` 
										WHERE parent = '{item.product}' AND 
										name IN ({attr_ids})''',as_dict = 1)
		for op in options:
			if op.image_list:
				images = json.loads(op.image_list)
				if images:
					images = sorted(images, key = lambda x: x.get('is_primary'),reverse = True)
					item['image'] = images[0].get('thumbnail')
					
def check_items_in_customer_cart(items,tax_rates,customer_cart,mp_items):
	if items:
		for item in items:
			if item.tax_breakup:
				t_items = item.tax_breakup.split('\n')
				for tx in t_items:
					if tx:
						tx_info = tx.split(' - ')
						check = next((x for x in tax_rates \
								if (x.get('tax_type') == tx_info[0] and \
									x.get('tax_rate') == tx_info[1])), None)
						if not check:
							tax_rates.append({
								'tax_type': tx_info[0],
								'tax_rate': tx_info[1],
								'rate': float(tx_info[1].split('%')[0])
								})
			check_attr_id_in_item(item)
			item.discount_percentage = 0
			if float(item.old_price) > 0 and float(item.price) < float(item.old_price):
				item.discount_percentage = int(round((item.old_price - item.price) / item.old_price * 100, 0))
			mp_items.append(item)
	customer_cart.marketplace_items = mp_items
	
def get_customer_cart(cart_type,customer):
	customer_cart = frappe.db.get_value('Shopping Cart',{'customer': customer,'cart_type': cart_type},
									 ['customer', 'name', 'tax', 'tax_breakup', 'total'], as_dict = 1)
	if customer_cart:
		items = get_items_if_customer_cart_exist(customer_cart)
		tax_rates = []
		mp_items = []
		tax_rate = 0
		check_items_in_customer_cart(items,tax_rates,customer_cart,mp_items)
		if tax_rates:
			tax_rate = sum(x.get('rate') for x in tax_rates)
		customer_cart.tax_rate = tax_rate
		return customer_cart
	else:
		return {}

