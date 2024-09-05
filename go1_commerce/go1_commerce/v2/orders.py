from __future__ import unicode_literals, print_function
import datetime
from datetime import datetime
import frappe, json, requests, os, socket, math
from frappe import _
from frappe.utils import flt, getdate, nowdate
from frappe.model.mapper import get_mapped_doc
from urllib.parse import unquote
from six import string_types
from go1_commerce.utils.setup import get_settings_value
from go1_commerce.utils.utils import role_auth,check_mandatory_exception,\
	get_customer_from_token,other_exception,doesnotexist_exception,permission_exception
from frappe.query_builder import DocType, Field, Order
from frappe.query_builder.functions import IfNull,Function, GroupConcat, Sum

@frappe.whitelist()
def make_sales_invoice(source_name, target_doc = None, submit = False):
	return _make_sales_invoice(source_name, target_doc, submit)

def _make_sales_invoice(source_name, target_doc = None, submit = False, ignore_permissions = False):

	def set_missing_values(source, target):
		target.status = "Unpaid"
		target.naming_series = "INV-YYYY-"
		target.reference = source_name
		target.notes = "Invoice created against: "+source_name
		target.flags.ignore_permissions = ignore_permissions
		target.run_method("set_missing_values")
	doclist = get_mapped_doc("Order", source_name, {
								"Order": {
									"doctype": "Sales Invoice",
									"validation": {
										"docstatus": ["=", 1]
									}
								},
								"Order Item": {
									"doctype": "Sales Invoice Item",
									"add_if_empty": True
								},
							}, target_doc, set_missing_values, ignore_permissions = ignore_permissions)
	if submit == True:
		doclist.docstatus = 1
		doclist.save()
	else:
		return doclist







def get_attributes_json(attribute_id):
	if attribute_id:
		if attribute_id.find('\n'):
			attribute_ids = attribute_id.split('\n')
			ids_list = []
			for x in attribute_ids:
				if x:
					ids_list.append(x)
			attribute_id = json.dumps(ids_list)
		return attribute_id.replace(' ','')

@frappe.whitelist(allow_guest=True)
def validate_coupon_code(coupon_code, order_total, cartitems, user=None):
	try:
		cart_items = json.loads(cartitems)
		coupon = frappe.db.get_all('Discounts', 
								   filters = {'requires_coupon_code': 1, 'coupon_code': coupon_code}, 
								   fields = ['*'])
		status = ''
		if not user:
			user = frappe.session.user
		if coupon:
			coupon_data = frappe.get_doc('Discounts', coupon[0].name)
			if coupon_data.start_date <= getdate(nowdate()) and coupon_data.end_date >= getdate(nowdate()):
				if coupon_data.limitations == 'Unlimited':
					status = 'success'
				elif coupon_data.limitations == 'N times only':
					if coupon_data.limitation_count > len(coupon_data.discount_history):
						status = 'success'
					else:
						return {
								'message': 'Invalid Coupon Code', 
								'status': 'failure'
							}
				else:
					user_count = frappe.db.get_all('Discount Usage History', 
												filters = {'parent': coupon_data.name, 'customer': user})
					if coupon_data.limitation_count > len(user_count):
						status = 'success'
					else:
						return {
								'message': 'You have exceed your limit', 
								'status': 'failure'
							}
				if status == 'success':
					return validate_coupon_data(coupon_data, order_total, cart_items)
			else:
				if coupon_data.start_date > getdate(nowdate()):
					return {
							'message': 'Invalid Coupon Code', 
							'status': 'failure'
						}
				elif coupon_data.end_date < getdate(nowdate()):
					return {
							'message': 'Coupon Code has been expired', 
							'status': 'failure'
						}
		else:
			return {
					'message': 'Invalid Coupon Code', 
					'status': 'failure'
				}
	except Exception:
		frappe.log_error('Error in v2.orders.validate_coupon_code', frappe.get_traceback())


def validate_coupon_data(coupon_data, order_total, cart_items):
	if coupon_data.discount_requirements:
		for req in coupon_data.discount_requirements:
			if req.discount_requirement == 'Spend x amount':
				if float(order_total) < float(req.amount_to_be_spent):
					return {
							'message': 'Your cart must contain minimum value 0f $' + 
								str(req.amount_to_be_spent), 
							'status': 'failure'
						}
				else:
					status = 'success'
			elif req.discount_requirement == 'Have any one product in cart':
				if coupon_data.discount_products:
					for item in cart_items:
						code = next((x.items for x in coupon_data.discount_products if x.items == item.get('id')), None)
						if code:
							status = 'success'
				else:
					status = 'success'
			else:
				if coupon_data.discount_products:
					count = 0
					for item in cart_items:
						code = next((x.items for x in coupon_data.discount_products if x.items == item.get('id')), None)
						if code:
							count = count + 1
					if count == len(coupon_data.discount_products):
						status = 'success'
					else:
						return {
								'message': 'Coupon code cannot be applied', 
								'status': 'failure'
							}
				else:
					status = 'success'
		if status == 'success':
			return {
					'status': 'success', 
					'coupon': coupon_data
				}
		else:
			return {
					'message': 'Coupon code cannot be applied', 
					'status': 'failure'
				}
	else:
		return {
				'status': 'success', 
				'coupon': coupon_data
			}


def validate_domain_and_ips():
	order_settings = frappe.get_single("Order Settings")
	if order_settings:
		hostname = socket.gethostname()
		IPAddr = socket.gethostbyname(hostname)
		blocked_ips = frappe.db.get_all("Block IP Address",
										filters={"parent":order_settings.name,"ip_address":IPAddr})
		if blocked_ips:
			return False
	return True


@frappe.whitelist(allow_guest=True)
def check_min_order_amount(ship_addr=None,cust_id=None):
	allow = True
	categories = []
	order_settings = frappe.get_single('Order Settings')
	order_sub_total = 0
	if not cust_id and frappe.request.cookies.get('customer_id'):
		cust_id = unquote(frappe.request.cookies.get('customer_id'))
	if cust_id:
		customers = frappe.db.get_all('Customers',
										filters = {'name': cust_id},
										fields = ['*'])
	else:
		customers = frappe.db.get_all('Customers',
										filters = {'user_id': frappe.session.user},
										fields = ['*'])
	cart = frappe.db.get_all('Shopping Cart',
								filters = {'customer': customers[0].name},
								fields = ['name', 'tax', 'tax_breakup'])
	items = get_items(cart,order_sub_total,categories)
	if order_settings.min_order_sub_total_amount > 0:
		if not order_sub_total >= order_settings.min_order_sub_total_amount:
			allow = False
			return {'status': False,
					'message': 'The minimum order amount is '\
								+ str('%.2f' % order_settings.min_order_sub_total_amount)}
	if allow:
		result = validate_category_order_amount(
												categories,
												cust_id,
												items,
												ship_addr
											)
		return result
	return {
			'status': True,
			"result":result
		}


def get_items(cart,order_sub_total,categories):
	if cart:
		CartItems = DocType('Cart Items')
		Product = DocType('Product')
		ProductCategoryMapping = DocType('Product Category Mapping')
		query = (
			frappe.qb.from_(CartItems)
			.inner_join(Product)
			.on(Product.name == CartItems.product)
			.select(
				CartItems.name,CartItems.product,CartItems.quantity,
				CartItems.attribute_description,CartItems.price,CartItems.total,
				CartItems.product_name,Product.price,Product.stock,
				Product.short_description,Product.route,Product.image.as_("image"),
				frappe.qb.select(
					GroupConcat(ProductCategoryMapping.category)
				)
				.from_(ProductCategoryMapping)
				.where(ProductCategoryMapping.parent == Product.name)
				.as_("categories")
			)
			.where(CartItems.parent == cart[0].name)
			.orderby(CartItems.idx)
		)
		items = query.run(as_dict = True)
		for cart_item in items:
			order_sub_total += cart_item.total
			if cart_item.categories:
				item_categories = cart_item.categories.split(',')
				for x in item_categories:
					if not str(x) in categories:
						categories.append(str(x))
	return items


def validate_category_order_amount(categories,cust_id,cart_items,ship_addr=None):
	if cust_id:
		customers = frappe.db.get_all('Customers',
										filters = {'name': cust_id},
										fields = ['*'])
	else:
		customers = frappe.db.get_all('Customers',
										filters = {'user_id': frappe.session.user},
										fields = ['*'])
	cart = frappe.db.get_all('Shopping Cart',
								filters = {'customer': customers[0].name},
								fields = ['name', 'tax', 'tax_breakup'])
	err_list = []
	if cart:
		currency = frappe.cache().hget('currency', 'symbol')
		validate_category_minimum_order_amount(categories, cart, err_list)
	if len(err_list) > 0:
		message = 'The minimum order value for '
		__message = 'The minimum order value for '
		for i, err in enumerate(err_list):
			message += '<a href="/{0}"><b>{1}</b></a> items is {2}{3}'.format(
																				err.get('route'),
																				err.get('category_name'),
																				(currency or ''),
																				err.get('order_value')
																			)
			__message += '{0} items is {1}{2}'.format(
														err.get('category_name'), 
														(currency or ''),
														str('%.2f' %err.get('order_value'))
													)
			if (i + 1) < len(err_list):
				message += ', '
				__message += ', '
		return {
				'status': False,
				'message': message,
				'mobile_message': __message
			}
	catalog_settings = frappe.get_single('Catalog Settings')
	if ship_addr:
		pincode_result =  validate_order_pincode_validate(ship_addr)
		return pincode_result
	return {
			'status': True
		}


def validate_category_minimum_order_amount(categories, cart, err_list):
	for category in categories:
		category_filter = [category]
		category_info = frappe.get_doc("Product Category", category)
		check_parent = True
		if category_info.minimum_order_amount > 0:
			category_filter = [category]
			child_categories = get_child_categories(category)
			category_filter.extend([x.name for x in child_categories])
			
			items_and_discounted_items = fetch_cart_items(
															cart_parent = cart[0].name, 
															category_filter = category_filter, 
															category_info = category_info
														)
			regular_items = items_and_discounted_items.get('regular_items', [])
			if regular_items:
				if regular_items[0].order_sub_total:
					if not regular_items[0].order_sub_total >= category_info.minimum_order_amount:
						check_list = next((x for x in err_list if x.get('category') == category_info.name), None)
						if not check_list:
							err_list.append({
											'category': category_info.name,
											'category_name': category_info.category_name,
											'route': category_info.route,
											'order_value': category_info.minimum_order_amount})
						check_parent = False
		if not category_info.parent_product_category:
			check_parent = False
		while check_parent:
			category_info = frappe.get_doc("Product Category", category_info.parent_product_category)
			if not category_info.parent_product_category:
				check_parent = False
			items_and_discounted_items = fetch_cart_items(
															cart_parent = cart[0].name, 
															category_filter = category_filter, 
															category_info = category_info
														)
			regular_items = items_and_discounted_items.get('regular_items', [])
			if regular_items:
				if regular_items[0].order_sub_total:
					if not regular_items[0].order_sub_total >= category_info.minimum_order_amount:
						check_list = next((x for x in err_list if x.get('category') == category_info.name), None)
						if not check_list:
							err_list.append({	
												'category': category_info.name,
												'category_name': category_info.category_name,
												'route': category_info.route,
												'order_value': category_info.minimum_order_amount
											})
						check_parent = False


def fetch_cart_items(cart_parent, category_filter, category_info=None):
	items_and_discounted_items = {}
	CartItems = DocType('Cart Items')
	ProductCategoryMapping = DocType('Product Category Mapping')
	regular_items_query = (
		frappe.qb.from_(CartItems)
		.select(
			Sum(CartItems.total).as_("order_sub_total"),
			CartItems.product_name
		)
		.where(CartItems.parent == cart_parent)
		.where(
			CartItems.product.isin(
				frappe.qb.from_(ProductCategoryMapping)
				.select(ProductCategoryMapping.parent)
				.where(ProductCategoryMapping.category.isin(category_filter))
			)
		)
		.orderby(CartItems.idx)
	)
	regular_items = regular_items_query.run(as_dict=True)
	items_and_discounted_items['regular_items'] = regular_items
	if category_info and category_info.minimum_order_amount > 0:
		discounted_items_query = (
			frappe.qb.from_(CartItems)
			.select(
				Sum(CartItems.total).as_("order_sub_total"),
				CartItems.product_name
			)
			.where(CartItems.parent == cart_parent)
			.where(
				CartItems.product.isin(
					frappe.qb.from_(ProductCategoryMapping)
					.select(ProductCategoryMapping.parent)
					.where(ProductCategoryMapping.category.isin(category_filter))
				)
			)
			.where(CartItems.discount_rule.is_not_null())
			.orderby(CartItems.idx)
		)
		discounted_items = discounted_items_query.run(as_dict=True)
		if discounted_items:
			if discounted_items[0].order_sub_total is None:
				category_info.minimum_order_amount = 0
		else:
			category_info.minimum_order_amount = 0
		items_and_discounted_items['discounted_items'] = discounted_items
	return items_and_discounted_items


def validate_order_pincode_validate(ship_addr):
	CustomerAddress = DocType('Customer Address')
	customer_shipping_address_query = (
		frappe.qb.from_(CustomerAddress)
		.select('*') 
		.where(CustomerAddress.name == ship_addr) 
	)
	customer_shipping_address = customer_shipping_address_query.run(as_dict=True)
	if customer_shipping_address:
		items = ''
		i = 0
		if len(items)>0:
			return {
					'status': False,
					'message': "The following items are not available for the location " + \
								customer_shipping_address[0].zipcode+'' + items
				}
		return {
				'status': True
			}
	else:
		return {
				'status': False,
				'message':"Shipping Address not found."
			}


def get_child_categories(category):
	try:
		if category:
			lft, rgt = frappe.db.get_value('Product Category', category, ['lft', 'rgt'])
			ProductCategory = DocType('Product Category')
			product_category_query = (
				frappe.qb.from_(ProductCategory)
				.select(ProductCategory.name)
				.where(
					ProductCategory.is_active == 1,
					ProductCategory.disable_in_website == 0,
					ProductCategory.lft >= lft,
					ProductCategory.rgt <= rgt
				)
			)
			result = product_category_query.run(as_dict=True)
	except Exception:
		other_exception("api.get_child_categories")


def get_attributes_json(attribute_id):
	if attribute_id:
		if attribute_id.find('\n') != -1:
			attribute_ids = attribute_id.split('\n')
			ids_list = []
			for x in attribute_ids:
				if x:
					ids_list.append(x)
			attribute_id = json.dumps(ids_list)
	return attribute_id


def submit_order(orderId):
	try:
		order = frappe.get_doc('Order', orderId)
		order.docstatus = 1
		order.save(ignore_permissions=True)
	except Exception:
		other_exception("api.submit_order")


def insert_discount_usage_history(order, customer, discount):
	try:
		if not frappe.db.get_all("Discount Usage History",
									filters = {'parent': discount,
											'parenttype': 'Discounts',
											'parentfield': 'discount_history',
											'order_id': order,
											'customer': customer}):
			date_range = None
			usage_history = frappe.get_doc({
											'doctype': 'Discount Usage History',
											'parent': discount,
											'parenttype': 'Discounts',
											'parentfield': 'discount_history',
											'order_id': order,
											'customer': customer,
											'date_range': date_range
											}).insert(ignore_permissions=True)
			frappe.db.commit()
	except Exception:
		other_exception("api.insert_discount_usage_history")


def debit_customer_wallet(cust_id, order_amount, order_id):
	try:
		walletdetails = wallet_details(cust_id)
		if walletdetails and walletdetails[0].current_wallet_amount > 0:
			wallet_amount = walletdetails[0].current_wallet_amount
			amount = 0
			order_payment_status = 'Pending'
			if flt(wallet_amount) >= flt(order_amount):
				amount = flt(order_amount)
				order_payment_status = 'Paid'
			else:
				amount = flt(wallet_amount)
				order_payment_status = 'Partially Paid'
			debit = frappe.new_doc('Wallet Withdrawal Request')
			debit.party_type = 'Customers'
			debit.party = cust_id
			debit.withdraw_amount = amount
			debit.withdrawal_type = 'Self'
			debit.status = 'Approved'
			debit.order_ref = 'Debited for Order.Id: ' + order_id
			debit.reference_doc = order_id
			debit.flags.ignore_permissions = True
			debit.submit()
			withdrawal_request = frappe.get_doc('Wallet Withdrawal Request', debit.name)
			withdrawal_request.status = 'Approved'
			withdrawal_request.save(ignore_permissions=True)
			outstanding_amount = order_amount - amount
			update_order = frappe.get_doc('Order', order_id)
			update_order.payment_status = order_payment_status
			update_order.paid_amount = amount
			update_order.paid_using_wallet = amount
			update_order.outstanding_amount = outstanding_amount
			try:
				update_order.save(ignore_permissions=True)
			except:
				
				Order = DocType('Order')
				update_query = (
					frappe.qb.update(Order)
					.set({
						Order.outstanding_amount: outstanding_amount,
						Order.payment_status: order_payment_status,
						Order.paid_amount: amount,
						Order.paid_using_wallet: amount
					})
					.where(Order.name == order_id)
				)
				
			frappe.db.commit()
	except Exception:
		other_exception("Error in v2.orders.debit_customer_wallet")


def wallet_details(name):
	try:
		Wallet = DocType('Wallet')
		select_query = (
			frappe.qb.from_(Wallet)
			.select('*')
			.where(Wallet.user == name)
		)
		wallet_amount = select_query.run(as_dict=True)
		if wallet_amount:
			return wallet_amount
	except Exception:
		other_exception("api.wallet_details")


@frappe.whitelist(allow_guest=True)
def validate_product_cart_qty(ProductId, attributeId = None, add_qty = None, qty = None, customer = None):
	try:
		products = frappe.db.get_all('Product', 
										fields = ['*'], 
										filters = {'name': ProductId, 'is_active': 1})
		if products:
			product = products[0]
			if customer:
				customer_id = customer
			else:
				customer_id = (unquote(frappe.request.cookies.get('customer_id'))\
								if frappe.request.cookies.get('customer_id') else None)
			if customer_id:
				cart = frappe.db.get_all('Shopping Cart',
								filters = {'customer': customer_id,'cart_type': 'Shopping Cart'},
								fields = ['name', 'tax', 'tax_breakup', 'total'])
				if cart:
					CartItem = DocType('Cart Item')
					Product = DocType('Product')
					query = (
						frappe.qb.from_(CartItem)
						.inner_join(Product).on(Product.name == CartItem.product)
						.select(
							CartItem.name,
							CartItem.product,
							CartItem.attribute_ids,
							CartItem.quantity,
							CartItem.attribute_description,
							CartItem.price,
							CartItem.total,
							CartItem.product_name,
							Product.price,
							Product.stock,
							Product.short_description,
							Product.route,
							Product.image,
							Product.maximum_order_qty
						)
					)
					query = query.where(
						CartItem.parent == cart[0].name,
						CartItem.product == ProductId,
						Product.name == CartItem.product
					)

					if attributeId:
						query = query.where(CartItem.attribute_ids == attributeId)
					query = query.orderby(CartItem.idx)
					cart_items = query.run(as_dict=True)
					if cart_items:
						cart_qty = sum(i.quantity for i in cart_items)
						if add_qty == 'false':
							cart_qty = cart_qty
						else:
							catalog_settings = frappe.get_single('Catalog Settings')
							if catalog_settings.show_quantity_box == 1 and qty:
								cart_qty = int(cart_qty) + int(qty)
							elif qty:
								cart_qty = int(cart_qty) + int(qty)
							else:
								cart_qty = int(cart_qty) + 1
						return _validate_stock(product, cart_qty)
					else:
						return _validate_stock(product, (qty or 1))
				else:
					return _validate_stock(product, (qty or 1))
			else:
				return _validate_stock(product, (qty or 1))
		else:
			return {
					'status': "False", 
					'message': 'Product not exist'
				}
	except Exception:
		frappe.log_error('Error in v2.orders.validate_product_cart_qty', frappe.get_traceback())
		return {
				'status': "Failed", 
				'message': 'Something Went Wrong'
			}


def _validate_stock(product, qty):
	out = {}
	if product.disable_add_to_cart_button == 1:
		out = { 
				'status': False, 
				'message': _('Sorry! no stock available for {0}').format(product.item) 
			}
	elif product.inventory_method == 'Track Inventory':
		if int(product.stock) > 0 and int(product.stock) >= int(qty):
			if int(qty) >= int(product.minimum_order_qty) and int(qty) <= int(product.maximum_order_qty):
				out = {
						'status': True,	
						'message': '', 
						'increment_quantity': 1
					}
			else:
				if int(qty) < int(product.minimum_order_qty):
					out = { 
						   'status': False,
							'message': _('Minimum order quantity of {0} is {1}').format(
																				product.item,
																				product.minimum_order_qty
																			) 
						}
					
				if int(qty) > int(product.maximum_order_qty):
					out = { 
							'status': False,
							'message': _('Maximum order quantity of {0} is {1}').format(product.item,
																				product.maximum_order_qty) 
						}
		else:
			out = { 
					'status': False,
					'message': _('Sorry! no stock available for {0}').format(product.item) 
				}
		
	elif product.inventory_method == 'Dont Track Inventory':
		if int(qty) >= int(product.minimum_order_qty) and int(qty) <= int(product.maximum_order_qty):
			out = {
					'status': True,
					'message': '', 'increment_quantity': 1
				}
		else:
			if int(qty) < int(product.minimum_order_qty):
				out = { 
						'status': False,
						'message': _('Minimum order quantity of {0} is {1}').format(product.item,
																			product.minimum_order_qty) 
					}
			if int(qty) > int(product.maximum_order_qty):
				out = { 
						'status': False,
						'message': _('Maximum order quantity of {0} is {1}').format(product.item,
																				product.maximum_order_qty) 
					}
	return out


def not_check_items(check_items):
	for x in check_items:
		frappe.log_error("Product", x.product)
		if x.attribute_ids:
			check_stock = validate_product_cart_qty(x.product, qty = x.quantity,attributeId = x.attribute_ids)
			if check_stock.get("status") == "Failed":
				return check_stock
		else:
			check_stock = validate_product_cart_qty(x.product, qty = x.quantity)
			frappe.log_error("check_stock", check_stock)
			if check_stock.get("status") == "Failed":
				return check_stock


@frappe.whitelist()
# @role_auth(role='Customer',method="POST")
def insert_order(data):
	if not data.get("customer"):
		customer_id = get_customer_from_token()
	else:
		customer_id = data.get("customer")
	catalog_settings = frappe.get_single('Catalog Settings')
	order_settings = frappe.get_single('Order Settings')
	val_ip = validate_domain_and_ips()
	customers = data.get("customer_name")
	if not frappe.db.get_all("Customers",filters={"name":customer_id,"customer_status":"Approved"}):
		return {
				"status":"Failed",
				"message":"You account not yet verified. You will get notified once verfied."
			}
	if val_ip and customer_id:
		request = data
		if isinstance(request, string_types):
			request = json.loads(request)
		if customer_id != request.get('customer_name'):
			return {
					"status":"Failed",
					"message":"You are not allow to place an order."
				}
		if request.get('customer_name'):
			customers = frappe.db.get_all('Customers',
											filters={'name': request.get('customer_name')},
											fields=['*'])
		else:
			customers = frappe.db.get_all('Customers',
						filters={'user_id': frappe.session.user},
						fields=['*'])
		if not customers or len(customers) == 0:
			return {
					'status': False,
					'message': frappe._('Something went wrong. Please try again.')
				}
		if customers[0].name == 'Guest' and not customers[0].phone:
			return {
					'status': False,
					'message': frappe._('Please login/register to place this order.')
				}
		cart = frappe.db.get_all('Shopping Cart',
										filters = {'customer': customers[0].name,
													'cart_type': 'Shopping Cart'},
										fields = ['name', 'tax', 'tax_breakup', 'total'])
		if not cart or len(cart) == 0:
			return {
					'status': False,
					'message': frappe._('Your cart is empty. Please add items to your cart.')
				}
		else:
			check_items = frappe.db.get_all('Cart Items',
					filters = {'parent': cart[0].name},fields=['*'])
			if not check_items or len(check_items) == 0:
				return {
					'status': False,
					'message': frappe._('Your cart is empty. Please add items to your cart.')
				}
			else:
				not_check_items(check_items)
		check_order_amount = check_min_order_amount(request.get('ship_addr'),
							request.get('customer_name'))
		if order_settings.enable_zipcode:
			from go1_commerce.go1_commerce.v2.checkout\
				import validate_order_pincode_validate
			zip_resp = validate_order_pincode_validate(check_items,request.get("ship_addr"))
			if zip_resp.get("status") == "Failed":
				return zip_resp
		check_multi_store_items = 1
		multi_store_item_result = {}
		if not check_order_amount or check_order_amount['status'] == False:
			out = {
					'status': False, 
					'message': check_order_amount['message']
				}
			if check_order_amount.get('mobile_message'):
				out.update({'mobile_message': check_order_amount.get('mobile_message')})
			return out
		if not check_multi_store_items:
			out = {
					'status': False,
					'message': multi_store_item_result['message']
				}
			return out
		else:
			res = {'status': True}
			if not res or res['status'] == False:
				return {
						'status': False, 
						'message': (res['message'] if res else '')
					}
			else:
				return validate_insert_order(
												res,
												order_settings,
												cart,
												customer_id,
												catalog_settings,
												request,
												customers
											)
	else:
		return {
				'status': False,
				'message': frappe._('You are not allowed do this operation.Please try again.')
			}


def validate_insert_order(res,order_settings,cart,customer_id,catalog_settings,request,customers):
	try:
		order_sub_total = 0
		order_total = 0
		total_weight = 0
		shipping_charge_amt = 0
		if request.get('name'):
			order_id = request.get('name')
		else:
			order_id = (unquote(frappe.request.cookies.get('order_id'))\
						if frappe.request.cookies.get('order_id') else None)
		order = frappe.new_doc('Order')
		if order_id:
			order_doc = frappe.get_doc("Order", order_id)
			order_items = []
			checkout_attributes = []
			order_doc.order_item = order_items
			order_doc.checkout_attributes = checkout_attributes
			order_doc.save(ignore_permissions=True)
			order = frappe.get_doc("Order", order_id)
			
		customer_info = frappe.get_doc("Customers",customer_id)
		order_set_values(request,order)
		get_address_details(request,order,customer_info)
		set_address_details(request,order,customer_info)
		set_payment_method(request,order,customers)
		items = []
		items = get_item(cart,order_sub_total,order_total,total_weight,items)
		order.order_subtotal = order_sub_total
		included_tax = catalog_settings.included_tax
		discount_data = []
		order.discount = 0
		coupon_code = None
		sp_discount = 0
		
		lis = get_discount_amount(
									order,request,
									order_total,
									coupon_code,
									shipping_charge_amt,
									order_id,
									cart,
									discount_data
								)
		order_total = lis[0]
		order_info = lis[1]
		discount_data = lis[2]
		tax_breakup = None
		tax_splitup = []
		if included_tax:
			tax_type = 'Incl. Tax'
		else:
			tax_type = 'Excl. Tax'
		if cart:
			get_items_item(cart)
			for cart_item in items:
				total = float(cart_item.total)
				discount = item_tax = 0
				if not cart_item.is_free_item:
					get_cart_items_list_insert_order(
														request,
														cart_item,
														order_sub_total,
														discount,
														sp_discount,
														total,item_tax,
														included_tax,
														tax_splitup,
														tax_type,
														discount_data
													)
				item_sku = frappe.db.get_value('Product',cart_item.product,'sku')
				item_price = frappe.db.get_value('Product',cart_item.product,'price')
				item_weight = frappe.db.get_value('Product',cart_item.product,'weight')
				tracking_method = frappe.db.get_value('Product',cart_item.product,'inventory_method')
				if cart_item.attribute_ids:
					attribute_id = get_attributes_json(cart_item.attribute_ids)
					ProductVariantCombination = DocType('Product Variant Combination')
					query = (
						frappe.qb.from_(ProductVariantCombination)
						.select(ProductVariantCombination.weight, ProductVariantCombination.sku)
						.where(
							ProductVariantCombination.parent == cart_item.product,
							ProductVariantCombination.attributes_json == attribute_id.replace(" ","")
						)
					)
					combination_weight = query.run(as_dict=True)
					
					if combination_weight:
						item_weight = combination_weight[0].weight
						item_sku = combination_weight[0].sku
				else:
					item_weight = item_weight
					if cart_item.attribute_ids:
						attr_id = cart_item.attribute_ids.splitlines()
						for item in attr_id:
							ProductAttributeOption = DocType('Product Attribute Option')
							query = (
								frappe.qb.from_(ProductAttributeOption)
								.select(*ProductAttributeOption.columns)
								.where(ProductAttributeOption.name == item)
							)
							attribute_weight = query.run(as_dict=True)
							if attribute_weight and attribute_weight[0].weight_adjustment:
								item_weight += flt(attribute_weight[0].weight_adjustment)
				if item_weight == 0:
					item_weight =  1
				base_price = 0
				base_price = cart_item.price / item_weight
				result = insert_order_item(
												order_info,
												cart_item,
												item_sku,
												item_weight,
												total,
												item_tax,
												discount,
												base_price
											)
			checkout_attributes_html(
										request,
										cart,
										order_info,
										cart_item
									)
		discount_free_products(
								request,
								order_info,
								item_weight,
								tax_splitup,
								tax_type,
								sp_discount,
								tax_breakup
							)
		
		from go1_commerce.go1_commerce.v2.cart \
			import clear_cartitem
		clear_cartitem()
		is_redirect = False
		redirect_url = ''
		payment_method = None
		if order_id:
			Order = DocType('Order')
			query = (
				frappe.qb.update(Order)
				.set(Order.payment_status, 'Pending')
				.where(Order.name == order_id)
			)
			query.run()
		if not payment_method:
			payment_method = frappe.db.get_all('Payment Method',
							filters={'enable': 1, 'name': request.get('payment_method')},
							order_by='display_order', fields=['*'])
		if order_settings.submit_order:
			submit_order(order_info.name)
		order_data = frappe.get_doc('Order', order_info.name)
		order_data.save(ignore_permissions=True)
		frappe.local.cookie_manager.delete_cookie('order_id')
		if request.get('discount'):
			insert_discount_usage_history(
											order_data.name, 
											order_data.customer, 
											request.get('discount')
										)
		if coupon_code:
			coupon_discount = coupon_code
			if frappe.db.get_all("Discounts",
				filters={"coupon_code":coupon_code}):
				disc_list = frappe.db.get_all("Discounts",filters={"coupon_code":coupon_code})
				coupon_discount = disc_list[0].name
			insert_discount_usage_history(
											order_data.name,
											order_data.customer, 
											coupon_discount
										)
			frappe.local.cookie_manager.delete_cookie('coupon_txt')
			frappe.local.cookie_manager.delete_cookie('coupon_code')
		if request.get('shipping_discount') and \
					float(order_data.actual_shipping_charges) > float(order_data.shipping_charges):
			insert_discount_usage_history(
											order_data.name,
											order_data.customer, 
											request.get('shipping_discount')
										)
		wallet_settings = frappe.get_single('Wallet Settings')
		check_wallet_settings(
								order_data,
								wallet_settings,
								request
							)
		order_data = frappe.get_doc("Order",order_data.name)
		return {
				'status': True,
				'message': '',
				'order': order_data,
				'is_redirect': is_redirect,
				'redirect_url': redirect_url
			}
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error('Error in v2.order.insert_order', frappe.get_traceback())
		return {
				'status': False,
				'message': frappe._('Something went wrong. Please try again.')
			}


def check_wallet_settings(order_data,wallet_settings,request):
	if wallet_settings.enable_customer_wallet:
		if request.get('manual_wallet_debit') == 1:
			if int(request.get('manual_wallet_debit')) == 1:
				customer_order_total = order_data.total_amount
				if request.get('pointsusage'):
					customer_order_total = customer_order_total - flt(request.get('reward_amount'))
				debit_customer_wallet(
										cust_id = order_data.customer, 
										order_amount = customer_order_total,
										order_id = order_data.name
									)


def get_discount_amount(order,request,order_total,coupon_code,shipping_charge_amt,
							order_id,cart,discount_data):
	if request.get('discount_amount'):
		order_total_list = set_discount_amount(
												order,
												request,
												order_total,
												coupon_code,
												discount_data
											)
		order_total = order_total_list[0]
		discount_data = order_total_list[1]
	order.total_tax_amount = math.ceil(cart[0].tax * 100) / 100
	order.is_recurring_order = int(request.get('is_recurring_order'))\
								if request.get('is_recurring_order') else 0

	shipping_charge_amt = float(request.get('shipping_charge')) if request.get('shipping_charge') else 0
	if request.get('actual_shipping_charges'):
		order.actual_shipping_charges = float(request.get('actual_shipping_charges'))
	else:
		order.actual_shipping_charges = 0
	order.shipping_charges = shipping_charge_amt
	if request.get('shipping_charge'):
		order_total = order_total + float(request.get('shipping_charge'))
	order.pickup_charge = (request.get('pickup_charge') if request.get('pickup_charge') else 0)
	order_total = order_total + float(request.get('pickup_charge')if request.get('pickup_charge') else 0)
	order.tip_amount = (request.get('tip_amount')if request.get('tip_amount') else 0)
	order_total = order_total + float(order.pickup_charge) + \
				float(order.tip_amount)+ float(order.pickup_charge)
	order.shipping_method = request.get('shipping_method')
	order_info = get_shipping_methods(request,order,order_id,order_total)
	return [order_total,order_info,discount_data]


def set_payment_method(request,order,customers):
	if request.get('delivery_slots'):
		for slot in request.get('delivery_slots'):
			order.delivery_date = slot.get('date')
			order.delivery_slot = str(slot.get('from_time')) +","+str(slot.get('to_time'))
	order.payment_gateway_charges = request.get('payment_gateway_charges')
	order.customer_comments = request.get('customer_comments')
	order.payment_method = request.get('payment_method')
	if not request.get('payment_method'):
		payment_methods = frappe.db.get_all("Payment Method",
						filters={"enable":1},
						fields={"name","payment_method"})
		if payment_methods:
			order.payment_method = payment_methods[0].name
			order.payment_method_name = payment_methods[0].payment_method
	if request.get('order_date'):
		order.order_date = request.get('order_date')
	else:
		order.order_date = get_today_date(replace=True)
	if request.get('order_time'):
		order.order_time = request.get('order_time')
	else:
		order.order_time = get_today_date(replace=True).strftime('%I:%M %p')
	if customers:
		order.customer = customers[0].name


def order_set_values(request,order):
	if request.get('subscriptionitem'):
		if request.get('subscriptionitem') == 1 or request.get('subscriptionitem') == '1':
			order.naming_series = 'SUB-ORD-'
		else:
			order.naming_series = 'ORD-'
	else:
		order.naming_series = 'ORD-'
	if frappe.request.cookies.get('guest_customer_name'):
		order.customer_name = unquote(frappe.request.cookies.get('guest_customer_name'))
	if frappe.request.cookies.get('guest_customer_phone'):
		order.customer_phone = unquote(frappe.request.cookies.get('guest_customer_phone'))
	if request.get('guest_name'):
		order.customer_name = request.get('guest_name')
	if request.get('shipping_mode'):
		order.shipping_mode = request.get('shipping_mode')
	if request.get('guest_phone'):
		order.customer_phone = request.get('guest_phone')


def set_address_details(request,order,customer_info):
	order.customer_email = customer_info.email
	if request.get("bill_addr"):
		
		CustomerAddress = DocType('Customer Address')
		query = (
			frappe.qb.from_(CustomerAddress)
			.select('*')
			.where(CustomerAddress.name == request.get('bill_addr'))
		)
		customer_billing_address = query.run(as_dict=True)
		if customer_billing_address:
			order.first_name = customer_billing_address[0].first_name
			order.city = customer_billing_address[0].city
			order.zipcode = customer_billing_address[0].zipcode
			order.last_name = (customer_billing_address[0].last_name or '')
			if order.last_name == 'None':
				order.last_name = None
			order.state = customer_billing_address[0].state
			order.phone = customer_billing_address[0].phone
			order.address = customer_billing_address[0].address
			order.country = customer_billing_address[0].country
			if customer_billing_address[0].landmark:
				order.landmark = customer_billing_address[0].landmark
	if request.get("ship_addr"):
		CustomerAddress = DocType('Customer Address')
		query = (
			frappe.qb.from_(CustomerAddress)
			.select('*')
			.where(CustomerAddress.name == request.get('ship_addr'))
		)
		customer_shipping_address = query.run(as_dict=True)
		
		if customer_shipping_address:
			order.shipping_first_name = customer_shipping_address[0].first_name
			order.shipping_city = customer_shipping_address[0].city
			order.shipping_zipcode = customer_shipping_address[0].zipcode
			order.shipping_last_name = (customer_shipping_address[0].last_name or '')
			if order.shipping_last_name == 'None': 
				order.shipping_last_name = None
			order.shipping_state = customer_shipping_address[0].state
			order.shipping_phone = customer_shipping_address[0].phone
			order.latitude = customer_shipping_address[0].latitude
			order.longitude = customer_shipping_address[0].longitude
			if customer_shipping_address[0].landmark:
				order.shipping_landmark = customer_shipping_address[0].landmark
			order.shipping_shipping_address = customer_shipping_address[0].address
			order.shipping_country = customer_shipping_address[0].country


def get_address_details(request,order,customer_info):
	if not request.get("ship_addr"):
		order.shipping_city = customer_info.business_city
		order.shipping_country = customer_info.business_country
		order.shipping_first_name = customer_info.first_name
		order.shipping_landmark = customer_info.business_landmark
		order.shipping_last_name = customer_info.last_name
		order.shipping_phone = customer_info.business_phone
		order.shipping_shipping_address = customer_info.business_address
		order.shipping_zipcode = customer_info.business_zip
		order.shipping_state = customer_info.business_state


def set_discount_amount(order,request,order_total,coupon_code,discount_data):
	order.discount = float(request.get('discount_amount'))
	order_total = order_total - float(request.get('discount_amount'))
	if request.get('discount'):
		(use_type, percent, amount, max_discount,
		price_or_product_discount) = frappe.db.get_value('Discounts',
												request.get('discount'),['percent_or_amount',
																		'discount_percentage',
																		'discount_amount',
																		'max_discount_amount',
																		'price_or_product_discount'])
		if price_or_product_discount == "Price":
			discount_data.append({
								'use_type': use_type,
								'percent': percent,
								'amount': amount,
								'max_discount': max_discount
								})
	if request.get('coupon_code'):
		coupon_code = request.get('coupon_code')
	elif frappe.request.cookies.get('coupon_code'):
		coupon_code = unquote(frappe.request.cookies.get('coupon_code'))
	if coupon_code:
		if frappe.db.get_all("Discounts",filters={"name":coupon_code}):
			(use_type_c, percent_c, amount_c,
			max_discount_c) = frappe.db.get_value('Discounts',
															coupon_code,
															['percent_or_amount',
															'discount_percentage',
															'discount_amount',
															'max_discount_amount'])
			discount_data.append({
								'use_type': use_type_c,
								'percent': percent_c,
								'amount': amount_c,
								'max_discount': max_discount_c
								})
	return [order_total,discount_data]

def get_item(cart,order_sub_total,order_total,total_weight,items):
	if cart:
		CartItem = DocType('Cart Items')
		Product = DocType('Product')
		query = (
			frappe.qb.from_(CartItem)
			.inner_join(Product).on(Product.name == CartItem.product)
			.select(
				CartItem.name,
				CartItem.product,
				CartItem.special_instruction,
				CartItem.quantity,
				CartItem.attribute_description,
				CartItem.price,
				CartItem.shipping_charges,
				CartItem.product_name,
				CartItem.tax,
				Product.stock,
				Product.short_description,
				Product.route,
				Product.image,
				CartItem.is_free_item,
				CartItem.discount_rule,
				CartItem.attribute_ids,
				CartItem.total
			)
			.where(CartItem.parent == cart[0].name)
			.orderby(CartItem.idx)
		)
		items = query.run(as_dict=True)
		for cart_item in items:
			if not cart_item.is_free_item:
				order_sub_total += cart_item.total
				order_total += cart_item.total
				if cart_item.weight:
					total_weight += cart_item.weight
		
		CartCheckoutAttributes = DocType('Cart Checkout Attributes')
		query = (
			frappe.qb.from_(CartCheckoutAttributes)
			.select('*')
			.where(CartCheckoutAttributes.parent == cart[0].name)
		)
		checkout_attributes = query.run( as_dict=True)
		if checkout_attributes:
			for attr_item in checkout_attributes:
				order_total += attr_item.price_adjustment
	return items


def get_shipping_methods(request,order,order_id,order_total):
	if not request.get('shipping_method'):
		shipping_methods = frappe.db.get_all("Shipping Method",
						filters={"show_in_website":1},
						fields={"name","shipping_method_name"})
		if shipping_methods:
			order.shipping_method = shipping_methods[0].name
			order.shipping_method_name = shipping_methods[0].shipping_method_name
	order.total_amount = order_total
	if order_id:
		check_attributes = frappe.db.get_all('Order Checkout Attributes',
						filters={	'parent':order.name,
									'attribute_id':'Recurring Order Details'})
		for x in check_attributes:
			OrderCheckoutAttributes = DocType('Order Checkout Attributes')
			query = (
				frappe.qb.delete()
				.from_(OrderCheckoutAttributes)
				.where(OrderCheckoutAttributes.name == x.name)
			)
			query.run()
			frappe.db.commit()
	get_checkout_attributes_html(request,order)
	order_info = order.as_dict()
	return order_info


def get_checkout_attributes_html(request,order):
	if request.get("checkout_attributes_html"):
		if request.get("checkout_attributes_html_array"):
			for chk_attributes_item in request.get("checkout_attributes_html_array"):
				order.append('checkout_attributes', {
							'attribute_description': chk_attributes_item.get("attribute_html"),
							'price_adjustment' : chk_attributes_item.get("attribute_price"),
							'attribute_id' : chk_attributes_item.get("attribute_id")
							})
				order.total_amount = order.total_amount + chk_attributes_item.get("attribute_price")
	if request.get('order_from'):
		order.order_from = request.get('order_from')
	if request.get('browser'):
		order.browser = request.get('browser')
	if frappe.request.cookies.get('coupon_txt'):
		order.discount_coupon = frappe.request.cookies.get('coupon_txt')
	if request.get('coupon_code'):
		order.discount_coupon = request.get('coupon_code')
	order.customer_ip = frappe.get_request_header('X-Forwarded-For')
	order.save(ignore_permissions=True)
	frappe.db.commit()


def get_items_item(cart):
	CartItems = DocType('Cart Items')
	Product = DocType('Product')
	query = (
		frappe.qb.from_(CartItems)
		.inner_join(Product).on(Product.name == CartItems.product)
		.select(
			CartItems.name,
			CartItems.product,
			CartItems.checkout_attributes,
			CartItems.special_instruction,
			CartItems.quantity,
			CartItems.price,
			CartItems.total,
			CartItems.shipping_charges,
			CartItems.attribute_ids,
			Product.stock,
			Product.short_description,
			CartItems.is_gift_card,
			CartItems.sender_name,
			CartItems.sender_email,
			CartItems.recipient_name,
			CartItems.recipient_email,
			CartItems.tax,
			CartItems.product_name,
			CartItems.attribute_description,
			CartItems.certificate_type,
			CartItems.certificate_occasion,
			Product.image.as_("image"),
			CartItems.sender_message,
			Product.route,
			CartItems.is_free_item,
			CartItems.discount_rule
		)
		.where(CartItems.parent == cart[0].name)
		.orderby(CartItems.idx)
	)
	items = query.run(as_dict=True)

def get_cart_items_list_insert_order(request,cart_item,order_sub_total,discount,sp_discount,
							total,item_tax,included_tax,tax_splitup,tax_type,discount_data):
	get_cart_item_list(request,cart_item,order_sub_total,discount,discount_data, sp_discount)
	if request.get('discount_products'):
		check_d = next((x for x in request.get('discount_products')\
					if x.get('product')== cart_item.product), None)
		if check_d and check_d.get('discount'):
			discount = discount + flt(check_d.get('discount'))
			if check_d.get('discount_name'):
				web_type = frappe.db.get_value('Discounts',
								check_d.get('discount_name'),
								['website_type', 'discount_provided_by'])
				sp_discount = float(sp_discount) + float(check_d.get('discount'))
	total = total - discount
	insert_order_tax_template(total,cart_item,included_tax,item_tax,tax_splitup,tax_type)


def get_cart_item_list(request,cart_item,order_sub_total,discount,sp_discount,discount_data):
	if request.get('discount_amount'):
		if discount_data:
			for dis in discount_data:
				new_discount = 0
				subtotal_discount = 0
				if dis['use_type'] == 'Discount Percentage':
					new_discount = float(cart_item.total) * float(dis['percent'])/100
					subtotal_discount =float(order_sub_total) * float(dis['percent'])/100
				if (dis.get('max_discount') and dis['max_discount'] > 0 and\
								float(dis['max_discount']) < float(subtotal_discount)) or\
								dis['use_type'] == 'Discount Amount':
					price_weightage = cart_item.total / order_sub_total * 100
					price_weightage = math.ceil(price_weightage * 100) / 100
					amount = 0
					if dis.get('max_discount') and dis['max_discount'] > 0:
						amount = dis['max_discount']
					else:
						amount = dis['amount']
					new_discount = float(price_weightage) * float(amount) / 100
					new_discount = math.ceil(new_discount * 100) / 100
				discount = discount + new_discount
				sp_discount = float(sp_discount) + float(new_discount)


def checkout_attributes_html(request,cart,order_info,cart_item):
	if not request.get("checkout_attributes_html"):
		CartCheckoutAttributes = DocType('Cart Checkout Attributes')
		query = (
			frappe.qb.from_(CartCheckoutAttributes)
			.select('*')
			.where(CartCheckoutAttributes.parent == cart[0].name)
			.orderby(CartCheckoutAttributes.idx)
		)
		checkout_attributes = query.run(as_dict=True)
		if checkout_attributes:
			cart_idx = 1
			for attr in checkout_attributes:
				attr_result = frappe.get_doc({
							'doctype': 'Order Checkout Attributes',
							'parent': order_info.name,
							'parenttype': 'Order',
							'parentfield': 'checkout_attributes',
							'attribute_id': attr.attribute_id,
							'attribute_description':attr.attribute_description,
							'price_adjustment': attr.price_adjustment,
							'idx': cart_idx}).save(ignore_permissions=True)
				cart_idx = cart_idx + 1
	set_gift_card_order(cart_item,order_info)


def set_gift_card_order(cart_item,order_info):
	if cart_item.is_gift_card:
		import uuid
		code = uuid.uuid4().hex
		gift_card_order = frappe.get_doc({
						'doctype': 'Gift Card Order',
						'customer_name':cart_item.sender_name,
						'customer_email':cart_item.sender_email,
						'recipient_name':cart_item.recipient_name,
						'recipient_email':cart_item.recipient_email,
						'certificate_type':cart_item.certificate_type,
						'occasion':cart_item.certificate_occasion,
						'message':cart_item.sender_message,
						'amount': cart_item.price,
						'total_amount':(cart_item.price* cart_item.quantity),
						'card_count': cart_item.quantity,
						'order_reference':order_info.name,
						'giftcart_coupon_code':str(code)[0:13]
						}).insert(ignore_permissions=True)
		frappe.db.commit()


def discount_free_products(request,order_info,item_weight,tax_splitup,tax_type,
											sp_discount,tax_breakup):
	if request.get("discount_free_products"):
		for free_product in request.get("discount_free_products"):
			item_weight = frappe.db.get_value("Product",
										free_product.get("product"),"weight")
			result = frappe.get_doc({
					'doctype': 'Order Item',
					'parent': order_info.name,
					'parenttype': 'Order',
					'parentfield': 'order_item',
					'order_item_type': 'Product',
					'item': free_product.get("product"),
					'item_name': free_product.get("product_name"),
					'item_sku':frappe.db.get_value("Product",free_product.get("product"),"sku"),
					'ordered_weight':item_weight*free_product.get("quantity"),
					'weight':item_weight*free_product.get("quantity"),
					'quantity': free_product.get("quantity"),
					'price': free_product.get("price"),
					'amount': free_product.get("price")*free_product.get("quantity"),
					'attribute_description': free_product.get("attribute_description"),
					'checkout_attributes': free_product.get("checkout_attributes"),
					't_amount': free_product.get("price")*free_product.get("quantity"),
					'shipping_charges': 0,
					'tax': 0,
					'd_amount': 0,
					'attribute_ids': free_product.get("attribute_ids"),
					'special_instruction': "",
					'is_free_item': free_product.get("is_free_item"),
					'is_gift_card': 0,
					'base_price':free_product.get("price")}).insert()
	tax_json = []
	if tax_splitup:
		tax_breakup = ''
		for s in tax_splitup:
			tax_json.append(s)
			tax_breakup += str(s['type']) + ' - ' + str('{0:.2f}'.
						format(s['rate'])) + '% - ' + str('{0:.2f}'.
						format(s['amount'])) + ' - ' + tax_type + '\n'
	frappe.db.set_value('Order', order_info.name, 'tax_json', json.dumps(tax_json))
	frappe.db.set_value('Order', order_info.name, 'tax_breakup', tax_breakup)


def insert_order_item(order_info,cart_item,item_sku,item_weight,total,item_tax,discount,base_price):
	result = frappe.get_doc({
			'doctype': 'Order Item',
			'parent': order_info.name,
			'parenttype': 'Order',
			'parentfield': 'order_item',
			'order_item_type': 'Product',
			'item': cart_item.product,
			'item_name': cart_item.product_name,
			'item_sku':item_sku,
			'ordered_weight':item_weight*cart_item.quantity,
			'weight':item_weight*cart_item.quantity,
			'quantity': cart_item.quantity,
			'price': cart_item.price,
			'amount': cart_item.total,
			'attribute_description': cart_item.attribute_description,
			'checkout_attributes': cart_item.checkout_attributes,
			't_amount': total,
			'shipping_charges': cart_item.shipping_charges,
			'tax': item_tax,
			'd_amount': discount,
			'attribute_ids': cart_item.attribute_ids,
			'special_instruction': cart_item.special_instruction,
			'is_free_item': cart_item.is_free_item,
			'is_gift_card': cart_item.is_gift_card,
			'discount': cart_item.discount_rule,
			'base_price': base_price,
			'is_gift_card':cart_item.is_gift_card,
			'sender_name':cart_item.sender_name,
			'sender_email':cart_item.sender_email,
			'recipient_name':cart_item.recipient_name,
			'recipient_email':cart_item.recipient_email,
			'sender_message':cart_item.sender_message
			}).save(ignore_permissions=True)


def insert_order_tax_template(total,cart_item,included_tax,item_tax,tax_splitup,tax_type):
	tax_template = None
	product_tax = frappe.db.get_value('Product', cart_item.product, 'tax_category')
	if product_tax:
		tax_template = frappe.get_doc('Product Tax Template', product_tax)
	if tax_template:
		if tax_template.tax_rates:
			for tax in tax_template.tax_rates:
				if included_tax:
					tax_value = flt(total) * tax.rate / (100 + tax.rate)
				else:
					tax_value = total * tax.rate / 100
				item_tax = item_tax + tax_value
				cur_tax = next((x for x in tax_splitup if (x['type']==tax.tax and x['rate'] == tax.rate)), None)
				if cur_tax:
					for it in tax_splitup:
						if it['type'] == tax.tax:
							it['amount'] = it['amount'] + tax_value
				else:
					tax_splitup.append({
										'type': tax.tax,
										'rate': tax.rate,
										'amount': tax_value,
										'account':tax.get('account_head'),
										'tax_type': tax_type 
									})
			return tax_splitup


@frappe.whitelist()
def insert_order__(data):
	insert_doc = frappe.new_doc("Order")
	insert_doc.customer = data.get("customer")
	insert_doc.shipping_method =data.get("shipping_method")
	insert_doc.payment_method = data.get("payment_method")
	for item in data.get("order_item"):
		insert_doc.append("order_item",item)
	insert_doc.ship_addr = data.get("ship_addr")
	insert_doc.save(ignore_permissions=True)
	return {
			"status":"success",
			"message":insert_doc
		}


def set_customer_shipping_address(request,order):
	CustomerAddress = DocType('Customer Address')
	query = (
		frappe.qb.from_(CustomerAddress)
		.select('*')
		.where(CustomerAddress.name == request.get('ship_addr')["name"])
	)
	customer_shipping_address = query.run(as_dict=True)
	if customer_shipping_address:
		order.shipping_first_name = customer_shipping_address[0].first_name
		order.shipping_city = customer_shipping_address[0].city
		order.shipping_zipcode = customer_shipping_address[0].zipcode
		order.shipping_last_name = (customer_shipping_address[0].last_name or '')
		if order.shipping_last_name == 'None': order.shipping_last_name = None
		order.shipping_state = customer_shipping_address[0].state
		order.shipping_phone = customer_shipping_address[0].phone
		order.shipping_house_type = customer_shipping_address[0].house_type
		order.latitude = customer_shipping_address[0].latitude
		order.longitude = customer_shipping_address[0].longitude
		if customer_shipping_address[0].door_no:
			order.shipping_door_no = customer_shipping_address[0].door_no
		if customer_shipping_address[0].unit_number:
			order.shipping_unit_number = customer_shipping_address[0].unit_number
		if customer_shipping_address[0].landmark:
			order.shipping_landmark = customer_shipping_address[0].landmark
		order.shipping_shipping_address = customer_shipping_address[0].address
		order.shipping_country = customer_shipping_address[0].country


@frappe.whitelist()
@role_auth(role='Customer')
def get_return_request_info(order_id=None,return_type="Return"):
	try:
		if not order_id:
			return {"status":"Failed",
					"message":"order_id parameter is missing."}
		customer_id = get_customer_from_token()
		if customer_id:
			if customer_id!=frappe.db.get_value("Order",order_id,"customer"):
				return {"status":"Failed",
						"message":"Invalid Customer."}
			OrderItem = DocType('Order Item')
			Order = DocType('Order')
			Product = DocType('Product')
			query = (
				frappe.qb.from_(OrderItem)
				.select(
					OrderItem.name,
					OrderItem.item.as_('product_id'),
					OrderItem.item_name,
					OrderItem.attribute_ids,
					OrderItem.item_sku.as_('sku'),
					Product.brand,
					Product.brand_name,
					OrderItem.quantity
				)
				.inner_join(Order).on(Order.name == OrderItem.parent)
				.inner_join(Product).on(Product.name == OrderItem.item)
			)
			if return_type == "Return":
				ReturnPolicy = DocType('Return Policy')
				query = (
					query.inner_join(ReturnPolicy).on(ReturnPolicy.name == Product.return_policy)
					.where(ReturnPolicy.eligible_for_return == 1)
				)
			if return_type == "Replacement":
				ReplacementPolicy = DocType('Replacement Policy')
				query = (
					query
					.inner_join(ReplacementPolicy).on(ReplacementPolicy.name == Product.replacement_name)
					.where(ReplacementPolicy.eligible_for_replacement == 1)
				)
			query = (
				query
				.where(
					OrderItem.return_created == 0,
					OrderItem.order_item_type == "Product",
					OrderItem.parent == order_id)
				)
			query = query.groupby(OrderItem.attribute_ids, OrderItem.item)
			eligible_items = query.run(as_dict=True)
			for row in eligible_items:
				row.variant_text = ""
				if row.get('attribute_ids'):
					attributes = get_attributes_combination(row.get('attribute_ids'))
					if attributes:
						row.variant_text = attributes[0].combination_txt
					else:
						row.variant_text = ''
		else:
			return {"status":"Failed",
					"message":"Customer not found."}
		return {"eligible_items":eligible_items}
	except Exception:
		other_exception("customer get_eligible_items")


def calculate_shipping_charges_from_list(shipping_charges,shipping_charges_list,
										shipping_addr,subtotal):
	matched_sh_charges = []
	for item in shipping_charges_list:
		if item.shipping_zone:
			to_city = frappe.db.get_value('Shipping Zones', item.shipping_zone,"to_city")
			if to_city:
				zipcode_range = frappe.db.get_value("Shipping City",to_city,"zipcode_range")
				if zipcode_range:
					if zipcode_range:
						if shipping_zip_matches(shipping_addr.zipcode, zipcode_range):
							matched_sh_charges.append(item)
	if not matched_sh_charges:
		for x in shipping_charges_list:
			if x.shipping_zone:
				shipping_state = frappe.db.get_value('Shipping Zones', x.shipping_zone,"state")
				if shipping_state == shipping_addr.state:
					matched_sh_charges.append(x)
		if not matched_sh_charges:
			for x in shipping_charges_list:
				if x.shipping_zone:
					country = frappe.db.get_value('Shipping Zones', x.shipping_zone,"country")
					if country == shipping_addr.country:
						matched_sh_charges.append(x)
	if matched_sh_charges:
		shiping_matched_by_zip = matched_sh_charges[0]
		if shiping_matched_by_zip.get("use_percentage"):
			if shiping_matched_by_zip.get("charge_percentage"):
				shipping_charges += subtotal * shiping_matched_by_zip.get("charge_percentage") / 100
		else:
			shipping_charges += shiping_matched_by_zip.get("charge_amount")
	return shipping_charges

def shipping_zip_matches(zip, ziprange):
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
				if str(x).lower().replace(" ","") == str(zip).lower().replace(" ",""):
					returnValue = True
	elif ziprange.find('-') > -1:
		zipcoderanges_after = ziprange.split('-')
		for zipcode in range(int(zipcoderanges_after[0]), int(zipcoderanges_after[1]) + 1):
			if str(zipcode).lower() == str(zip).lower():
				returnValue = True
	else:
		if str(ziprange).lower() == str(zip).lower():
			returnValue = True
	if ziprange.find('*') > -1:
		zicode_starts = ziprange.split('*')[0]
		if (str(zip).lower()).startswith(zicode_starts.lower()):
			returnValue = True
	return returnValue

def validate_and_calculate_additional_shipping_charges(shopping_cart):
	shipping_not_allowd_products = []
	additional_shipping_charges = 0
	order_subtotal = 0
	for citem in shopping_cart.items:
		if not citem.get("is_free_item"):
			(enable_shipping,free_shipping,
			additional_shipping_cost,product_name) = frappe.db.get_value('Product',citem.product,
																['enable_shipping','free_shipping',
																'additional_shipping_cost',"item"])
			if enable_shipping:
				if not free_shipping:
					if additional_shipping_cost > 0:
						additional_shipping_charges += additional_shipping_cost * citem.quantity
					order_subtotal += citem.total
			else:
				shipping_not_allowd_products.append(product_name)
	if shipping_not_allowd_products:
		return {
				"status":"failed",
				"message":frappe.render_template(f"Shipping is not allowed for the following products - \
										{','.join(shipping_not_allowd_products)}.".rstrip(','))
				}
	else:
		return {
				"status":"success",
				"additional_shipping_charges" : additional_shipping_charges,
				"order_subtotal":order_subtotal
				}

def get_formated_geo_address(address_type,address_dic = None):
	full_address = ""
	if address_type == "Customer":
		if address_dic.get("latitude") and address_dic.get("longitude"):
			full_address = str(address_dic.get("latitude")) + ', ' + str(address_dic.get("longitude"))
		else:
			address_keys = ['address','city','state','zipcode','country']
			for addr in address_keys:
				full_address += f"""{(address_dic.get(addr) + ',') if address_dic.get(addr) else ''}"""
	elif address_type == "Business":
		business = frappe.db.get_all("Business",["latitude",'longitude','country',
												'state','city','zipcode'])
		if business:
			if business[0].latitude and business[0].longitude:
				full_address = str(business[0].latitude) + ', ' + str(business[0].longitude)
			else:
				for addr in business[0]:
					full_address += f"""{(business[0].get(addr) + ',') if business[0].get(addr) else ''}"""
	if full_address:
		if full_address.find('#') != -1:
			full_address = full_address.replace('#', '')
		return {
				"status":"success",
				"full_address":full_address
				}
	else:
		return {
				"status":"failed",
				"message":f"The {address_type} is not found."
				}

def get_geo_distance(source, destination):
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
		if res.get("status") == "OK":
			if res.get("rows") and res.get("rows")[0].get("elements") and \
				res.get("rows")[0].get("elements")[0].get("status") != "NOT_FOUND" and\
				res.get("rows")[0].get("elements")[0].get("status") != "ZERO_RESULTS":
				resp_data = {"distance":{},"duration":{}}
				if 'distance' in res.get("rows")[0].get("elements")[0]:
					resp_data['distance']['kms'] = res.get("rows")[0].get("elements")[0].get("distance").get("text")
					resp_data['distance']['value'] = res.get("rows")[0].get("elements")[0].get("distance").get("value")
				if 'duration' in res.get("rows")[0].get("elements")[0]:
					resp_data['duration']['mins'] = res.get("rows")[0].get("elements")[0].get("duration").get("text")
					resp_data['duration']['value'] = res.get("rows")[0].get("elements")[0].get("duration").get("value")
				return {
						"status":"success",
						"data":resp_data
					}
			else:
				return {
						"status":"failed",
						"message":"something went wrong.not able to calculate the distance."
					}
		else:
			return {
					"status":"failed",
					"message":"something went wrong."
				}
	else:
		return {
				"status":"failed",
				"message":"Please enable the google settings."
			}

def get_formated_source_designation_address(shipping_addr):
	desg_addr_resp = get_formated_geo_address("Customer",shipping_addr)
	if desg_addr_resp.get("status") == "success":
		src_addr_resp = get_formated_geo_address("Business")
		if src_addr_resp.get("status") == "success":
			return {
					"status":"success",
					"designation_address":desg_addr_resp.get("full_address"),
					'src_address':src_addr_resp.get("full_address")
				}
		else:
			return src_addr_resp
	else:
		return desg_addr_resp

def get_source_designation_distance_value(shipping_addr):
	fomated_address_resp = get_formated_source_designation_address(shipping_addr)
	if fomated_address_resp.get("status") == "success":
		src_address = fomated_address_resp.get("src_address")
		designation_address = fomated_address_resp.get("designation_address")
		distance_info = get_geo_distance(src_address,designation_address)
		if distance_info.get("status") == "success":
			if distance_value := distance_info.get("data").get("distance").get("value"):
				return {
						"status":"success",
						"distance_value":distance_value
					}
			else:
				return{
						"status":"failed",
						"message":"source and designation distance not found."
					}
		else:
			return distance_info
	else:
		return fomated_address_resp

def calculate_fixed_rate_shipping_charges(shipping_method,shipping_addr,shopping_cart):
	sh_status = validate_and_calculate_additional_shipping_charges(shopping_cart)
	if sh_status.get("status") == "success":
		shipping_charges = sh_status.get("additional_shipping_charges")
		order_subtotal = sh_status.get("order_subtotal")
		if order_subtotal:
			
			ShippingByFixedRateCharges = DocType('Shipping By Fixed Rate Charges')
			query = (
				frappe.qb.from_(ShippingByFixedRateCharges)
				.select(
					ShippingByFixedRateCharges.shipping_zone,
					ShippingByFixedRateCharges.charge_amount
				)
				.where(ShippingByFixedRateCharges.shipping_method == shipping_method)
			)
			sh_list = query.run(as_dict=True)
			if sh_list:
				total_fxr_sh_charges = calculate_shipping_charges_from_list(
																			shipping_charges,
																			sh_list,
																			shipping_addr,
																			order_subtotal
																		)
				return {
						"status":"success",
						"shipping_charges":total_fxr_sh_charges
					}
			else:
				return {
						"status":"success",
						"shipping_charges":shipping_charges
					}
		else:
			return {
					"status":"success",
					"shipping_charges":shipping_charges
				}
	else:
		return sh_status

def calculate_total_based_shipping_charges(shipping_method,shipping_addr,shopping_cart):
	sh_status = validate_and_calculate_additional_shipping_charges(shopping_cart)
	if sh_status.get("status") == "success":
		shipping_charges = sh_status.get("additional_shipping_charges")
		order_subtotal = sh_status.get("order_subtotal")
		res = {
				"status":"success",
				"shipping_charges":shipping_charges
			}
		if order_subtotal:
			ShippingByTotalCharges = DocType('Shipping By Total Charges')
			query = (
				frappe.qb.from_(ShippingByTotalCharges)
				.select(
					ShippingByTotalCharges.shipping_zone,
					ShippingByTotalCharges.use_percentage,
					ShippingByTotalCharges.charge_amount,
					ShippingByTotalCharges.charge_percentage
				)
				.where(
					(ShippingByTotalCharges.shipping_method == shipping_method) &
					(order_subtotal >= ShippingByTotalCharges.order_total_from) &
					(order_subtotal <= ShippingByTotalCharges.order_total_to)
				)
			)
			sh_list = query.run(as_dict=True)
			if sh_list:
				total_fxr_sh_charges = calculate_shipping_charges_from_list(shipping_charges,
																			sh_list,
																			shipping_addr,
																			order_subtotal)
				return {
						"status":"success",
						"shipping_charges":total_fxr_sh_charges
					}
			else:
				return res
		else:
			return res
	else:
		return sh_status

def calculate_weight_based_shipping_charges(shipping_method,shopping_cart):
	sh_status = validate_and_get_sumof_weight_subtotal_addi_shipping_chrgs(shopping_cart.items)
	if sh_status.get("status") == "success":
		res = {
				"status":"success",
				"shipping_charges":shipping_charges
			}
		shipping_charges = sh_status.get("additional_shipping_charges")
		order_subtotal = sh_status.get("order_subtotal")
		total_weight = sh_status.get("total_weight")
		if order_subtotal:
			ShippingByWeightCharges = DocType('Shipping By Weight Charges')
			query = (
				frappe.qb.from_(ShippingByWeightCharges)
				.select(
					ShippingByWeightCharges.shipping_zone,
					ShippingByWeightCharges.use_percentage,
					ShippingByWeightCharges.charge_amount,
					ShippingByWeightCharges.charge_percentage
				)
				.where(
					(ShippingByWeightCharges.shipping_method == shipping_method) &
					(total_weight >= ShippingByWeightCharges.order_weight_from) &
					(total_weight <= ShippingByWeightCharges.order_weight_to)
				)
			)
			sh_list = query.run(as_dict=True)
			
			if sh_list:
				shiping_matched_by_weight = sh_list[0]
				if shiping_matched_by_weight.get("use_percentage"):
					weight_ = shiping_matched_by_weight.get("charge_percentage") 
					if weight_:
						shipping_charges += order_subtotal * weight_ / 100
				else:
					shipping_charges += shiping_matched_by_weight.get("charge_amount")
				return res
			else:
				return res
		else:
			return res
	else:
		return sh_status

def validate_and_get_sumof_weight_subtotal_addi_shipping_chrgs(shopping_cart_items):
	shipping_not_allowd_products = []
	additional_shipping_charges = total_weight = order_subtotal = 0
	for item in shopping_cart_items:
		if not item.get("is_free_item"):
			(product_weight, enable_shipping,
			free_shipping,additional_shipping_cost,
			product_name,has_variants) = frappe.db.get_value('Product',item.product,['weight',
																'enable_shipping','free_shipping',
																'additional_shipping_cost',
																'item','has_variants'])
			if enable_shipping:
				if not free_shipping:
					if item.attribute_ids and has_variants:
						attribute_id = get_attributes_json(item.attribute_ids)
						combination_weight = get_product_variant_weight(item,attribute_id)
						if combination_weight:
							total_weight += combination_weight * item.quantity
							if additional_shipping_cost > 0:
								additional_shipping_charges += additional_shipping_cost * item.quantity
							order_subtotal += item.total
					else:
						total_weight += product_weight * item.quantity
						if additional_shipping_cost > 0:
							additional_shipping_charges += additional_shipping_cost * item.quantity
						order_subtotal += item.total
						if item.attribute_ids:
							attr_id = item.attribute_ids.splitlines()
							for item in attr_id:
								
								ProductAttributeOption = DocType('Product Attribute Option')
								attribute_weight = (frappe.qb.from_(ProductAttributeOption) 
									.select(ProductAttributeOption.weight_adjustment) 
									.where(ProductAttributeOption.name == item) 
									.run(as_dict=True))
								if attribute_weight and attribute_weight[0].weight_adjustment:
									total_weight += flt(attribute_weight[0].weight_adjustment) * item.quantity
			else:
				shipping_not_allowd_products.append(product_name)
	if shipping_not_allowd_products:
		return {
			"status":"failed",
			"message":f"Shipping is not allowed for the following products.{','.join(shipping_not_allowd_products)}".rstrip(',')
		}
	else:
		return {
				"status":"success",
				"additional_shipping_charges":additional_shipping_charges,
				"order_subtotal":order_subtotal,
				"total_weight":total_weight
			}

def get_product_variant_weight(item,attribute_id):
	loop = 0
	while loop < 2:

		ProductVariantCombination = DocType('Product Variant Combination')
		query = (
			frappe.qb.from_(ProductVariantCombination)
			.select(ProductVariantCombination.weight)
			.where(
				(ProductVariantCombination.parent == item.product) &
				(ProductVariantCombination.attributes_json == attribute_id)
			)
		)
		combination_weight = query.run(as_dict=True)
		if not combination_weight and not loop:
			loop += 1
			attribute_id = str(attribute_id).replace(" ","")
			continue
		else:
			return combination_weight[0].weight if combination_weight else None

def calculate_distance_based_shipping_charges(shipping_method,shipping_addr,shopping_cart):
	sh_status = validate_and_calculate_additional_shipping_charges(shopping_cart)
	if sh_status.get("status") == "success":
		shipping_charges = sh_status.get("additional_shipping_charges")
		order_subtotal = sh_status.get("order_subtotal")
		if order_subtotal:
			return calculate_get_dbased_shipping_charges(shipping_method,shipping_addr,
														order_subtotal,shipping_charges)
		else:
			return {
					"status":"success",
					"shipping_charges":shipping_charges
				}
	else:
		return sh_status

def calculate_get_dbased_shipping_charges(shipping_method, shipping_addr, subtotal,shipping_charges):
	distance_info = get_source_designation_distance_value(shipping_addr)
	if distance_info.get("status") == "success":
		distance_value = distance_info.get("distance_value")
		distance = 0
		distance_unit = frappe.db.get_value("Shipping Rate Method",{"shipping_rate_method":"Shipping By Distance",
														"is_active":1},"distance_unit")
		if distance_unit == 'Miles':
			distance = round((distance_value * 0.001 * 0.621371),2)
		else:
			distance = round((distance_value * 0.001),2)
		ShippingChargesByDistance = DocType('Shipping Charges By Distance')
		query = (
			frappe.qb.from_(ShippingChargesByDistance)
			.select(
				ShippingChargesByDistance.use_percentage,
				ShippingChargesByDistance.charge_percentage,
				ShippingChargesByDistance.charge_amount
			)
			.where(
				(ShippingChargesByDistance.shipping_method == shipping_method) &
				(distance >= ShippingChargesByDistance.from_distance) &
				(distance <= ShippingChargesByDistance.to_distance)
			)
		)
		shipping_charges_list = query.run(as_dict=True)
		
		if shipping_charges_list:
			if shipping_charges_list[0].use_percentage:
				shipping_charges += subtotal * shipping_charges_list[0].charge_percentage / 100
			else:
				shipping_charges += shipping_charges_list[0].charge_amount
		return {
				"status":"success",
				"shipping_charges":shipping_charges
			}
	else:
		return distance_info

def calculate_distance_total_based_shipping_charges(shipping_method,shipping_addr,shopping_cart):
	sh_status = validate_and_calculate_additional_shipping_charges(shopping_cart)
	if sh_status.get("status") == "success":
		shipping_charges = sh_status.get("additional_shipping_charges")
		order_subtotal = sh_status.get("order_subtotal")
		distance_info = get_source_designation_distance_value(shipping_addr)
		if distance_info.get("status") == "success":
			distance_value = distance_info.get("distance_value")
			distance = round((distance_value * 0.001),2)
			ShippingCharges = DocType('Shipping Charges By Distance and Total')
			ShippingRateMethod = DocType('Shipping Rate Method')
			query = (
				frappe.qb.from_(ShippingCharges)
				.join(ShippingRateMethod)
				.on(ShippingRateMethod.name == ShippingCharges.parent)
				.select(
					ShippingCharges.use_percentage,
					ShippingCharges.charge_percentage,
					ShippingCharges.charge_amount
				)
				.where(
					(ShippingCharges.shipping_method == shipping_method) &
					(distance >= ShippingCharges.from_distance) &
					(distance <= ShippingCharges.to_distance) &
					(order_subtotal >= ShippingCharges.order_total_from) &
					(order_subtotal <= ShippingCharges.order_total_to)
				)
			)
			shipping_charges_list = query.run(as_dict=True)
			if shipping_charges_list:
				if shipping_charges_list[0].use_percentage:
					shipping_charges += order_subtotal * shipping_charges_list[0].charge_percentage / 100
				else:
					shipping_charges += shipping_charges_list[0].charge_amount
			return {
					"status":"success",
					"shipping_charges":shipping_charges
				}
		else:
			return distance_info
	else:
		return sh_status

@frappe.whitelist(allow_guest=True)
def calculate_distance_weight_based_shipping_charges(shipping_method,shipping_addr,shopping_cart):
	sh_status = validate_and_get_sumof_weight_subtotal_addi_shipping_chrgs(shopping_cart.items)
	if sh_status.get("status") == "success":
		shipping_charges = sh_status.get("additional_shipping_charges")
		order_subtotal = sh_status.get("order_subtotal")
		total_weight = sh_status.get("total_weight")
		distance_info = get_source_designation_distance_value(shipping_addr)
		if distance_info.get("status") == "success":
			distance_value = distance_info.get("distance_value")
			distance = round((distance_value * 0.001),2)
			ShippingCharges = DocType('Shipping Charges By Distance And Weight')
			ShippingRateMethod = DocType('Shipping Rate Method')
			query = (
				frappe.qb.from_(ShippingCharges)
				.join(ShippingRateMethod)
				.on(ShippingRateMethod.name == ShippingCharges.parent)
				.select(
					ShippingCharges.use_percentage,
					ShippingCharges.charge_percentage,
					ShippingCharges.charge_amount
				)
				.where(
					(ShippingCharges.shipping_method == shipping_method) &
					(distance >= ShippingCharges.from_distance) &
					(distance <= ShippingCharges.to_distance) &
					(total_weight >= ShippingCharges.order_weight_from) &
					(total_weight <= ShippingCharges.order_weight_to)
				)
			)
			shipping_charges_list = query.run(as_dict=True)
			
			if shipping_charges_list:
				if shipping_charges_list[0].use_percentage:
					shipping_charges  += order_subtotal * shipping_charges_list[0].charge_percentage / 100
				else:
					shipping_charges += shipping_charges_list[0].charge_amount
			return {
					"status":"success",
					"shipping_charges":shipping_charges
				}
		else:
			return distance_info
	else:
		return sh_status

def calculate_per_distance_per_weight_based_sh_chrgs(shipping_rate_method,shipping_addr,shopping_cart):
	sh_status = validate_and_get_sumof_weight_subtotal_addi_shipping_chrgs(shopping_cart.items)
	if sh_status.get("status") == "success":
		shipping_charges = sh_status.get("additional_shipping_charges")
		order_subtotal = sh_status.get("order_subtotal")
		total_weight = sh_status.get("total_weight")
		distance_info = get_source_designation_distance_value(shipping_addr)
		if distance_info.get("status") == "success":
			distance_value = distance_info.get("distance_value")
			distance = round((distance_value * 0.001),2)
			charges_per_kg,charges_per_km = frappe.db.get_value("Shipping Rate Method",shipping_rate_method,
												["charges_per_kg","charges_per_km"])
			shipping_charges += round((total_weight * charges_per_kg),2)
			shipping_charges += round((distance * charges_per_km),2)
			return {
					"status":"success",
					"shipping_charges":shipping_charges
				}
		else:
			return distance_info
	else:
		return sh_status

def calculate_shipping_charges_distance_and_weight_group(shipping_rate_method,shipping_addr,shopping_cart):
	sh_status = validate_and_get_sumof_weight_subtotal_addi_shipping_chrgs(shopping_cart.items)
	if sh_status.get("status") == "success":
		shipping_charges = sh_status.get("additional_shipping_charges")
		order_subtotal = sh_status.get("order_subtotal")
		total_weight = sh_status.get("total_weight")
		if order_subtotal:
			distance_info = get_source_designation_distance_value(shipping_addr)
			if distance_info.get("status") == "success":
				distance_value = distance_info.get("distance_value")
				distance = round((distance_value * 0.001),2)
				return get_sh_chrgs_of_distance_and_weight_group(distance,shipping_rate_method,total_weight,order_subtotal,shipping_charges)
			else:
				return distance_info
		else:
			return {
					"status":"success",
					"shipping_charges":shipping_charges
				}
	else:
		return sh_status

def get_sh_chrgs_of_distance_and_weight_group(distance,shipping_rate_method,weight_total,
											subtotal,additional_shipping_charges):
	distance_charge_amount = weight_charge_amount = 0
	remaining_weight = 0
	remaining_distance = 0
	shipping_chrgs_km_kg = frappe.db.get_value("Shipping Rate Method", 
											   shipping_rate_method,
											   ["charges_per_kg_gp","charges_per_km_gp"],
											   as_dict = 1)
	
	ShippingByWeightCharges = DocType('Shipping By Weight Charges')
	query = (
		frappe.qb.from_(ShippingByWeightCharges)
		.select(
			ShippingByWeightCharges.charge_amount,
			ShippingByWeightCharges.order_weight_from,
			ShippingByWeightCharges.order_weight_to
		)
		.where(
			(ShippingByWeightCharges.parent == shipping_rate_method) &
			(total_weight >= ShippingByWeightCharges.order_weight_from) &
			(total_weight <= ShippingByWeightCharges.order_weight_to)
		)
	)
	weight_charges_list = query.run(as_dict=True)
	if weight_charges_list:
		if weight_charges_list[0].use_percentage:
			weight_charge_amount += subtotal * weight_charges_list[0].charge_percentage / 100
		else:
			weight_charge_amount += weight_charges_list[0].charge_amount
	else:
		
		ShippingByWeightCharges = DocType('Shipping By Weight Charges')
		query = (
			frappe.qb.from_(ShippingByWeightCharges)
			.select(
				ShippingByWeightCharges.order_weight_to,
				ShippingByWeightCharges.charge_amount
			)
			.where(
				(ShippingByWeightCharges.parent == shipping_rate_method) &
				(ShippingByWeightCharges.order_weight_to <= weight_total)
			)
			.orderby(ShippingByWeightCharges.order_weight_to, order=Order.desc)
			.limit(1)
		)
		weight_charges_list_all = query.run(as_dict=True)
		if weight_charges_list_all:
			weight_charge_amount += weight_charges_list_all[len(weight_charges_list_all)-1].charge_amount
			remaining_weight = weight_total - weight_charges_list_all[len(weight_charges_list_all)-1].order_weight_to
		else:
			remaining_weight = weight_total
	
	ShippingChargesByDistance = DocType('Shipping Charges By Distance')
	query = (
		frappe.qb.from_(ShippingChargesByDistance)
		.select(
			ShippingChargesByDistance.charge_amount,
			ShippingChargesByDistance.to_distance
		)
		.where(
			(ShippingChargesByDistance.parent == shipping_rate_method) &
			(distance >= ShippingChargesByDistance.from_distance) &
			(distance <= ShippingChargesByDistance.to_distance)
		)
	)
	distance_charges_list = query.run(as_dict=True)
	if distance_charges_list:
		if distance_charges_list[0].use_percentage == 1:
			distance_charge_amount += subtotal * distance_charges_list[0].charge_percentage / 100
		else:
			distance_charge_amount += distance_charges_list[0].charge_amount
	else:
		ShippingChargesByDistance = DocType('Shipping Charges By Distance')
		query = (
			frappe.qb.from_(ShippingChargesByDistance)
			.select(
				ShippingChargesByDistance.charge_amount,
				ShippingChargesByDistance.to_distance
			)
			.where(
				(ShippingChargesByDistance.parent == shipping_rate_method) &
				(ShippingChargesByDistance.to_distance <= distance)
			)
			.orderby(ShippingChargesByDistance.to_distance)
		)
		distance_charges_list_all = query.run(as_dict=True)
		if distance_charges_list_all:
			distance_charge_amount += distance_charges_list_all[len(distance_charges_list_all)-1].charge_amount
			remaining_distance = distance - distance_charges_list_all[len(distance_charges_list_all)-1].to_distance
		else:
			remaining_distance = distance
	if remaining_weight:
		weight_charge_amount += (remaining_weight * shipping_chrgs_km_kg.charges_per_kg_gp)
	if remaining_distance:
		distance_charge_amount += (remaining_distance * shipping_chrgs_km_kg.charges_per_km_gp)
	total_shipping_charges = weight_charge_amount + distance_charge_amount + additional_shipping_charges
	return {
			"status":"success",
			"shipping_charges":total_shipping_charges
		}

@frappe.whitelist(allow_guest = True)
def calculate_tax_after_discount(customer_id, discount_amount, discount, subtotal,
									cart_items, prev_discount=None, discount_type=None, response=None):
	def _calculate_item_discount(dis, subtotal, item):
		new_discount = 0
		subtotal_discount = 0
		if dis.price_or_product_discount=="Price":
			if dis.percent_or_amount == 'Discount Percentage':
				new_discount = float(item.get('total')) * float(dis.discount_percentage) / 100
				subtotal_discount = float(subtotal) * float(dis.discount_percentage) / 100
			if (dis.max_discount_amount and dis.max_discount_amount > 0 \
					and dis.max_discount_amount < subtotal_discount) or dis.percent_or_amount == 'Discount Amount':
				price_weightage = float(item.get('total')) / float(subtotal) * 100
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
						new_discount = new_discount  + _calculate_item_wise_discount(item.get('product'), response)
					discount_amout = discount_amout + float(new_discount)
				if prev_discount:
					new_discount1 = 0
					if prev_discount_info:
						new_discount1 = _calculate_item_discount(prev_discount_info, subtotal, item)
					if prev_discount and prev_discount.get('discount_response'):
						new_discount1 = new_discount1 + _calculate_item_wise_discount(item.get('product'),
										prev_discount.get('discount_response'))
					discount_amout = discount_amout + float(new_discount1)
				total = item.get('total') - discount_amout
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


@frappe.whitelist()
@role_auth(role = 'Customer',method = "POST")
def calculate_tax_without_discount(cart_items):
	tax_amt = 0
	tax_splitup = []
	if cart_items:
		for item in cart_items:
			if not item.get('is_free_item'):
				discount_amout = new_discount = 0
				total = item.get('total') - discount_amout
				item_tax = 0
				product_tax = None
				if frappe.db.get_value('Product', item.get('product')):
					product_tax = frappe.db.get_value('Product', item.get('product'),
								'tax_category')
				if product_tax:
					tax_template = frappe.get_doc('Product Tax Template', product_tax)
					(item_tax, tax_splitup) = calculate_tax_from_template(tax_template, total, tax_splitup)
				tax_amt = tax_amt + item_tax
	return (tax_amt, tax_splitup)

@frappe.whitelist()
def get_geodistance(source, destination):
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
		if res.get("status") == "OK":
			if res.get("rows") and res.get("rows")[0].get("elements") and \
				res.get("rows")[0].get("elements")[0].get("status") != "NOT_FOUND" and\
				res.get("rows")[0].get("elements")[0].get("status") != "ZERO_RESULTS":
				resp_data = {"distance":{},"duration":{}}
				if 'distance' in res.get("rows")[0].get("elements")[0]:
					resp_data['distance']['kms'] = res.get("rows")[0].get("elements")[0].get("distance").get("text")
					resp_data['distance']['value'] = res.get("rows")[0].get("elements")[0].get("distance").get("value")
				if 'duration' in res.get("rows")[0].get("elements")[0]:
					resp_data['duration']['mins'] = res.get("rows")[0].get("elements")[0].get("duration").get("text")
					resp_data['duration']['value'] = res.get("rows")[0].get("elements")[0].get("duration").get("value")
				return {"status":"success","data":resp_data}
			else:
				return {
						"status":"failed",
						"message":"something went wrong.not able to calculate the distance."
					}
		else:
			return {
					"status":"failed",
					"message":"something went wrong."
				}
	else:
		return {
				"status":"failed",
				"message":"Please enable the google settings."
			}

@frappe.whitelist()
@role_auth(role = 'Customer',method = "POST")
def validate_product_cart_qty1(ProductId, attributeId = None, add_qty = None, qty = None, customer = None):
	try:
		catalog_settings = frappe.get_single('Catalog Settings')
		products = frappe.db.get_all('Product',
				fields = ['*'],
				filters = {'name': ProductId, 'is_active': 1})
		if products:
			product = products[0]
			customer_id = (unquote(frappe.request.cookies.get('customer_id'))\
							if frappe.request.cookies.get('customer_id') else None)
			if customer:
				customer_id = customer
			if customer_id:
				cart = frappe.db.get_all('Shopping Cart',
					filters = {'customer': customer_id,'cart_type': 'Shopping Cart'},
					fields = ['name','tax', 'tax_breakup', 'total'])
				if cart:
					return validate_product_cart_qty_conditions(cart,product,ProductId, attributeId,add_qty,qty,customer)
				else:
					return validate_product_cart_qty_inventory_method(product,qty,customer)
			else:
				return validate_inventory_method(product = product, catalog_settings = catalog_settings,
									qty = qty,attributeId = attributeId,customer = customer)
		else:
			return {
					'status': False, 
					'message': 'Product not exist'
					}
	except Exception:
		other_exception("Error in v2.order.validate_product_cart_qty1")


def validate_inventory_method(product,catalog_settings,qty,attributeId,customer):
	if product.inventory_method == 'Track Inventory':
		if product.stock > 0:
			min_stock = product.minimum_order_qty
			if catalog_settings.show_quantity_box == 1 and qty:
				if qty >= product.minimum_order_qty:
					min_stock = qty
				else:
					return {
							'status': False,
							'message': 'Sorry! the minimum order quantity for '
								+ str(product.item.encode('ascii', 'ignore')) + ' is ' + str(min_stock)
								+ ' and the available stock is ' + str(product.stock)
						}
			if flt(product.stock) >= flt(min_stock):
				return {
						'status': True, 
						'message': '',
						'increment_quantity': min_stock
					}
			else:
				return {
						'status': False,
						'message': 'Sorry! the minimum order quantity for'
							+ str(product.item.encode('ascii', 'ignore')) + ' is ' + str(min_stock)
							+ ' and the available stock is ' + str(product.stock)
					}
		else:
			return {
					'status': False,
					'message': 'Sorry! no stock available for'+ str(product.item.encode('ascii', 'ignore'))
				}
	elif product.inventory_method == 'Dont Track Inventory':
		return {
				'status': True, 
				'message': '',
				'increment_quantity': 1
			}
	else:
		res = validate_attributes_stock(product.name,attributeId,'',1, add_qty=None,customer=customer)
		if res:
			if res['status'] == 'Failed':
				return {
						'status': False,
						'message': res['message']
					}
			else:
				return {'status': True,
						'message': '',
						'increment_quantity': 1
					}


def validate_product_cart_qty_conditions(cart,product,ProductId,attributeId,add_qty,qty,customer):
	CartItems = DocType('Cart Items')
	Product = DocType('Product')
	query = (
		frappe.qb.from_(CartItems)
		.inner_join(Product).on(Product.name == CartItems.product)
		.select(
			CartItems.name,
			CartItems.product,
			CartItems.attribute_ids,
			CartItems.quantity,
			CartItems.attribute_description,
			CartItems.price,
			CartItems.total,
			CartItems.product_name,
			Product.price,
			Product.stock,
			Product.short_description,
			Product.route,
			Product.image,
			Product.maximum_order_qty
		)
		.where(
			(CartItems.parent == cart[0].name) &
			(CartItems.product == ProductId) &
			(CartItems.attribute_ids == attributeId)
		)
		.orderby(CartItems.idx)
	)
	cart_items = query.run(as_dict=True)
	if cart_items:
		cart_qty = sum(i.quantity for i in cart_items)
		if add_qty == 'false':
			cart_qty = cart_qty
		else:
			if catalog_settings.show_quantity_box == 1 and qty:
				cart_qty = int(cart_qty) + int(qty)
			elif qty:
				cart_qty = int(cart_qty) + int(qty)
			else:
				cart_qty = int(cart_qty) + 1
		validate_product_cart_qty_conditions_inventory_method(product = product,cart_qty = cart_qty,
														cart_items = cart_items,customer=customer)
	else:
		if product.inventory_method == 'Track Inventory':
			if product.stock > 0:
				min_stock = product.minimum_order_qty
				if catalog_settings.show_quantity_box == 1 and qty:
					if qty >= product.minimum_order_qty:
						min_stock = qty
					else:
						return {
								'status': False,
								'message': 'Sorry! the minimum order quantity for '
									+ str(product.item.encode('ascii', 'ignore')) + ' is ' + str(min_stock)
									+ ' and the available stock is ' + str(product.stock)}
				if flt(product.stock) >= flt(min_stock):
					return {
							'status': True, 
							'message': '',
							'increment_quantity': min_stock
						}
				else:
					return {
							'status': False,
							'message': 'Sorry! the minimum order quantity for '
								+ str(product.item.encode('ascii', 'ignore')) + ' is ' + str(min_stock)
								+ ' and the available stock is ' + str(product.stock)
						}
			else:
				return {
						'status': False,
						'message': 'Sorry! no stock available for '
							+ str(product.item.encode('ascii', 'ignore'))
					}
		elif product.inventory_method == 'Dont Track Inventory':
			return {
					'status': True, 
					'message': '','increment_quantity': 1
				}
		else:
			res = validate_attributes_stock(product.name, attributeId, '', 1, add_qty = None, 
													customer = customer)
			if res:
				if res['status'] == 'Failed':
					return {
							'status': False,
							'message': res['message']
						}
				else:
					return {
							'status': True,
							'message': '', 
							'increment_quantity': 1
						}


def validate_product_cart_qty_conditions_inventory_method(product,cart_qty,cart_items,customer):
	if product.inventory_method == 'Track Inventory':
		if int(product.stock) > 0 and int(product.stock) >= int(cart_qty):
			if int(cart_qty) >= int(product.minimum_order_qty) and int(cart_qty) <=\
						int(product.maximum_order_qty):
				if int(cart_qty) <= int(product.stock):
					return {
							'status': True, 
							'message': '', 
							'increment_quantity': 1
						}
				else:
					return {
							'status': False,
							'message': 'Sorry! the available stock for '
								+ str(product.item.encode('ascii', 'ignore'))
								+ ' is ' + str(product.stock)
						}
			else:
				if not int(cart_qty) >= int(product.minimum_order_qty):
					return {
							'status': False,
							'message': 'Minimum order quantity of'
								+ str(product.item.encode('ascii', 'ignore'))
								+ ' is :' + str(product.minimum_order_qty)
						}
				if not int(cart_qty) <= int(product.maximum_order_qty):
					return {
							'status': False,
							'message': 'Maximum order quantity of '
								+ str(product.item.encode('ascii', 'ignore'))
								+ ' is :' + str(product.maximum_order_qty)
						}
		else:
			return {
					'status': False,
					'message': 'Sorry! no stock available for '
						+ str(product.item.encode('ascii', 'ignore'))
				}
	elif product.inventory_method == 'Dont Track Inventory':
		if int(cart_qty) >= int(product.minimum_order_qty)\
				and int(cart_qty) <= int(product.maximum_order_qty):
			return {
					'status': True, 
					'message': '',
					'increment_quantity': 1
				}
		else:
			if not int(cart_qty) >= int(product.minimum_order_qty):
				return {
						'status': False,
						'message': 'Minimum order quantity of '
							+ str(product.item.encode('ascii', 'ignore'))
							+ ' is :' + str(product.minimum_order_qty)
					}
			if not int(cart_qty) <= int(product.maximum_order_qty):
				return {
						'status': False,
						'message': 'Maximum order quantity of '
							+ str(product.item.encode('ascii', 'ignore'))
							+ ' is :' + str(product.maximum_order_qty)
					}
	else:
		res = validate_attributes_stock(product.name,
				cart_items[0].attribute_ids,
				cart_items[0].attribute_description,
				cart_qty, add_qty=None,customer=customer)
		if res:
			if res['status'] == 'Failed':
				return {
						'status': False,
						'message': res['message']
					}
			else:
				return {
						'status': True,
						'message': '', 'increment_quantity': 1
					}
		else:
			if cart_qty >= product.minimum_order_qty and cart_qty <= product.maximum_order_qty:
				return {
						'status': True, 
						'message': '', 
						'increment_quantity': 1
					}
			else:
				if not cart_qty >= product.minimum_order_qty:
					return {
							'status': False,
							'message': 'Minimum order quantity of '
								+ str(product.item.encode('ascii', 'ignore'))
								+ ' is :' + str(product.minimum_order_qty)
						}
				if not cart_qty <= product.maximum_order_qty:
					return {
							'status': False,
							'message': 'Maximum order quantity of '
								+ str(product.item.encode('ascii', 'ignore'))
								+ ' is :' + str(product.maximum_order_qty)
							}

def validate_product_cart_qty_inventory_method(product,qty,attributeId,customer):
	if product.inventory_method == 'Track Inventory':
			if product.stock > 0:
				min_stock = product.minimum_order_qty
				if catalog_settings.show_quantity_box == 1 and qty:
					if qty >= product.minimum_order_qty:
						min_stock = qty
					else:
						return {
								'status': False,
								'message': 'Sorry! the minimum order quantity for '
									+ str(product.item.encode('ascii', 'ignore'))
									+ ' is ' + str(min_stock)
									+ ' and the available stock is ' + str(product.stock)
							}
				if flt(product.stock) >= flt(min_stock):
					return {
							'status': True, 
							'message': '',
							'increment_quantity': min_stock
						}
				else:
					return {
							'status': False,
							'message': 'Sorry! the minimum order quantity for '
								+ str(product.item.encode('ascii', 'ignore')) + ' is ' + str(min_stock)
								+ ' and the available stock is ' + str(product.stock)
						}
			else:
				return {
						'status': False,
						'message': 'Sorry! no stock available for '
							+ str(product.item.encode('ascii', 'ignore'))
					}
	elif product.inventory_method == 'Dont Track Inventory':
		return {
				'status': True, 
				'message': '',
				'increment_quantity': 1
			}
	else:
		res = validate_attributes_stock(product.name, attributeId, '',1, add_qty = None, 
												customer = customer)
		if res:
			if res['status'] == 'Failed':
				return {
						'status': False,
						'message': res['message']
					}
			else:
				return {
						'status': True,
						'message': '', 
						'increment_quantity': 1
					}


@frappe.whitelist(allow_guest = True)
def validate_attributes_stock(product, attribute_id, variant_html, cart_qty, add_qty = None, customer = None):
	try:
		product_info = frappe.get_doc('Product', product)
		product_price = product_info.price
		check_data = frappe.db.get_all('Product Variant Combination',
										filters = {'parent': product, 'attribute_id': attribute_id},
										fields = ['stock', 'price', 'weight', 'sku', 'role_based_pricing'])
		if check_data:
			if check_data[0].price > 0:
				product_price = check_data[0].price
			qty = 0
			if check_data[0].stock > 0:
				customer_id = (unquote(frappe.request.cookies.get('customer_id')) \
						if frappe.request.cookies.get('customer_id') else None)
				if customer:
					customer_id = customer
				if customer_id:
					cart = frappe.db.get_all('Shopping Cart', fields = ['*'],
									filters = {'customer': customer_id, 'cart_type': 'Shopping Cart'})
					if cart:
						cartitem = frappe.db.get_all('Cart Items', fields = ['*'],
								filters = {'product': product, 'parent': cart[0].name,
											'attribute_description': variant_html})
						if cartitem:
							qty = (float(cartitem[0].qty) if add_qty == True else 0)
			qty = flt(qty) + flt(cart_qty)
			discount = get_product_price(product_info, qty,product_price, attribute_id)
			return _validate_inventory_product_info(qty,check_data,product_info,discount)
		else:
			if product_info.inventory_method == 'Track Inventory By Product Attributes':
				return {
						'status': 'Failed',
						'attr_status': 1,
						'price': product_info.price,
						'message': 'Sorry! No stock available for ' + 
									str(product_info.item.encode('ascii', 'ignore'))
					}
	except Exception:
		frappe.log_error('Error in v2.orders.validate_attributes_stock', frappe.get_traceback())


def _validate_inventory_product_info(qty,check_data,product_info,discount):
	if product_info.inventory_method == 'Track Inventory By Product Attributes':
		return validate_inventory_product_info(qty,check_data,product_info,discount)
	elif product_info.inventory_method == 'Dont Track Inventory':
		return {'status': 'Success',
				'price': check_data[0].price,
				'discount': discount}
	else:
		if qty > product_info.stock:
			return {
					'status': 'Failed',
					'discount': discount,
					'price': check_data[0].price,
					'message': 'Sorry! Available quantity for ' + 
								str(product_info.item.encode('ascii','ignore')) + ' is ' + 
								str(int(product_info.stock)),
					}
		else:
			return validate_product_info(product_info,discount,check_data,qty)


def validate_inventory_product_info(qty,check_data,product_info,discount):
	if qty <= check_data[0].stock and check_data[0].stock != 0:
		return validate_check_data(check_data,discount,qty,product_info)
	else:
		if check_data[0].stock == 0:
			return {
				'status': 'Failed',
				'stock': check_data[0].stock,
				'discount': discount,
				'price': check_data[0].price,
				'message': 'Sorry! No stock available for ' + 
							str(product_info.item.encode('ascii', 'ignore')),
				}
		return {
				'status': 'Failed',
				'stock': check_data[0].stock,
				'discount': discount,
				'price': check_data[0].price,
				'message': 'Sorry! Available quantity for ' + 
							str(product_info.item.encode('ascii', 'ignore')) + ' is ' + 
							str(int(check_data[0].stock)),
			}


def validate_check_data(check_data,discount,qty,product_info):
	if check_data:
		if product_info.maximum_order_qty and qty <= product_info.maximum_order_qty:
			return {
				'status': 'Success',
				'price': check_data[0].price,
				'stock': check_data[0].stock,
				'discount': discount,
			}
		else:
			return {
				'status': 'Failed',
				'discount': discount,
				'price': check_data[0].price,
				'message': 'Maximum allowed quantity for the product ' + 
							str(product_info.item.encode('ascii','ignore')) + 'is '+ 
							str(product_info.maximum_order_qty),
				}
	if product_info.minimum_order_qty and qty >= product_info.minimum_order_qty:
		return {
			'status': 'Success',
			'price': check_data[0].price,
			'stock': check_data[0].stock,
			'discount': discount,
			}
	else:
		return {
			'status': 'Failed',
			'discount': discount,
			'price': check_data[0].price,
			'message': 'Minimum order quantity for the product ' + 
						str(product_info.item.encode('ascii','ignore')) + ' is ' + 
						str(product_info.minimum_order_qty),
			}


def validate_product_info(product_info,discount,check_data,qty):
	if product_info:
		if product_info.maximum_order_qty and qty <= product_info.maximum_order_qty:
			return {
				'status': 'Success',
				'price': check_data[0].price,
				'stock': check_data[0].stock,
				'discount': discount,
				}
		else:
			return {
				'status': 'Failed',
				'discount': discount,
				'price': check_data[0].price,
				'message': 'Maximum allowed quantity for the product ' + 
					str(product_info.item.encode('ascii', 'ignore')) + 'is ' + 
					str(product_info.maximum_order_qty),
				}
	if product_info.minimum_order_qty and qty >= product_info.minimum_order_qty:
		return {
			'status': 'Success',
			'price': check_data[0].price,
			'stock': check_data[0].stock,
			'discount': discount,
			}
	else:
		return {
			'status': 'Failed',
			'discount': discount,
			'price': check_data[0].price,
			'message': 'Minimum order quantity for the product ' + 
				str(product_info.item.encode('ascii', 'ignore')) + ' is ' +
				str(product_info.minimum_order_qty),
			}


def get_product_price(product, qty = 1, rate = None,attribute_id = None, customer = None):
	try:
		web_type = None
		if isinstance(attribute_id, list):
			if len(attribute_id) == 1:
				attribute_id = attribute_id[0]
		cust = customer
		if frappe.request:
			cust = frappe.request.cookies.get('customer_id')
		cart_items=None
		if cust:
			cart = frappe.db.exists("Shopping Cart", {"customer": cust})
			if cart:
				doc = frappe.get_doc("Shopping Cart", cart)
				cart_items = ','.join('"{0}"'.format(r.product) for r in doc.items)
		from go1_commerce.go1_commerce.doctype.discounts.discounts \
		import get_product_discount
		res = get_product_discount(product, qty, rate, customer_id = customer,
									attribute_id = attribute_id, product_array = cart_items)
		return res
	except Exception:
		frappe.log_error('Error in v2.orders.get_product_price', frappe.get_traceback())


@frappe.whitelist()
def get_customer_order_list(page_no = None, page_length = None):
	try:
		if type(page_no) == int and type(page_length) == int and page_no and page_length:
			valid_customer = False
			customer_id = None
			user_email = get_email_from_token()
			if user_email:
				customer_email = frappe.db.get_all("Customers",
													filters = {"email":user_email})
				if customer_email:
					valid_customer = True
					customer_id = customer_email[0].name
			if valid_customer:
				limit_start = (int(page_no)-1)*int(page_length)
				fields_list = ["name","creation","status", "payment_status","total_amount"]
				order = frappe.get_all('Order', 
										filters = {'customer': customer_id,
												   'naming_series': ('!=','SUB-ORD-')},
												fields = fields_list,
												limit_start = limit_start, 
												limit_page_length = page_length,
												order_by = 'creation desc')
				if order:
					for i in order:
						order_items = frappe.get_all('Order Item', fields = ['name','item'],
									filters = {'parent': i.name})
						i.Items = order_items
				return order
		return []
	except Exception:
		other_exception("Error in v2.order.order_list")


def get_email_from_token():
	authorization_header = frappe.get_request_header("Authorization", "").split(" ")
	if authorization_header:
		token = authorization_header[1].split(":")
		users = frappe.db.get_all("User",filters = {"api_key":token[0]})
		if users:
			return users[0].name
	return None


@frappe.whitelist()
@role_auth(role='Customer', method="POST")
def edit_order(order_id):
	customer = get_customer_from_token()
	order = frappe.get_doc('Order',order_id)
	if customer and customer == order.customer:
		OrderItem = DocType('Order Item')
		query = (
			frappe.qb.from_(OrderItem)
			.select(
				OrderItem.item,
				OrderItem.quantity,
				OrderItem.attribute_ids
			)
			.where(OrderItem.parent == order_id)
		)
		old_items = query.run(as_dict=True)
		cart = frappe.db.get_all('Shopping Cart',
									filters = {'customer':customer,'cart_type':'Shopping Cart'})
		edit_cart_items(cart, order, order_id, customer)
		frappe.db.commit()
		return {
				"status":"Success"
			}
	return {
			"status":"Failed",
			"message":"Invalid customer. !"
			}


def get_wallet_list(cart, order_id):
	CartItem = DocType('Cart Item')
	WalletTransaction = DocType('Wallet Transaction')
	frappe.qb.from_(CartItem).delete().where(CartItem.parent == cart[0].name).run()
	wallet_list = (
		frappe.qb.from_(WalletTransaction)
		.select(WalletTransaction.name)
		.where(
			WalletTransaction.order_id == order_id,
			WalletTransaction.docstatus == 1
		)
		.run(as_dict=True)
	)
	return wallet_list


def edit_cart_items(cart,order,order_id,customer):
	if cart:
		wallet_list = get_wallet_list(cart,order_id)
		validate_cart(wallet_list,order_id,order,cart)
	else:
		cart = frappe.new_doc('Shopping Cart')
		cart.customer = customer
		cart.cart_type = "Shopping Cart"
		cart.website_type = 'Website'
		for x in order.order_item:
			if x.is_free_item != 1:
				cart.append('items', {  'product':  x.item,
										'old_price':x.old_price,
										"quantity": x.quantity,
										"price": x.price,
										'attribute_description': x.attribute_description,
										'attribute_ids': x.attribute_ids,
										'__islocal': 1,})
		cart.save(ignore_permissions=True)


def validate_cart(wallet_list,order_id,order,cart):
	for item in wallet_list:
		doc = frappe.get_doc('Wallet Transaction', item.name)
		doc.docstatus = 2
		doc.save(ignore_permissions=True)
	frappe.db.commit()
	for x in order.order_item:
		if x.is_free_item != 1:
			result = frappe.get_doc({	"doctype": "Cart Items",
										"parent": cart[0].name,
										"parenttype": "Shopping Cart",
										"parentfield": "items",
										'product':  x.item,
										'old_price':x.old_price,
										"quantity": x.quantity,
										"price": x.price,
										'attribute_description': x.attribute_description,
										'attribute_ids': x.attribute_ids,
										'__islocal': 1,}).insert(ignore_permissions=True)
	cart_doc = frappe.get_doc('Shopping Cart', cart[0].name)
	cart_doc.flags.__update = 1
	cart_doc.save(ignore_permissions = True)


@frappe.whitelist()
@role_auth(role='Customer',method="POST")
def update_order(data):
	try:
		request = data
		order_id = request.get("order_id")
		customer = request.get("customer")
		if not customer:
			customer = get_customer_from_token()
		check_order = frappe.db.get_all("Order",filters={"name":order_id},fields=['customer'])
		if check_order and customer:
			cart = get_cart_items(order_id,customer)
			if cart:
				items = order_items_list(cart)
				included_tax = catalog_settings.included_tax
				for cart_item in items:
					total = float(cart_item.total)
					tax_breakup = None
					tax_splitup = []
					if included_tax:
						tax_type = 'Incl. Tax'
					else:
						tax_type = 'Excl. Tax'
					discount = item_tax = 0
					order_info = frappe.get_doc('Order', order_id,["*"])
					if not cart_item.is_free_item:
						values = validate_cart_free_item(cart_item,total,included_tax,item_tax,tax_splitup,
															discount,order_info,tax_type)
						item_sku = values[0]
						item_weight = values[2]
						base_price = values[1]
						get_order_itm_list(order_info,cart_item,item_sku,item_weight,total,item_tax,
									discount,base_price)
						frappe.db.commit()
				validate_order_data(order_id,request)
				order_info = frappe.get_doc('Order', order_id)
				order_info.save(ignore_permissions=True)
				
				CartItem = DocType('Cart Item')
				frappe.qb.from_(CartItem).delete().where(CartItem.parent == cart[0].name).run()
				frappe.db.commit()
				return {
						"status":"Success",
						"order_id": order_info.name,
						"message": "Order Updated Successfully"
					}
		else:
			return {
					"message": "Order is not found."
				}
	except frappe.exceptions.DoesNotExistError:
		doesnotexist_exception()
	except frappe.exceptions.PermissionError:
		permission_exception()
	except Exception:
		other_exception("customer update_orders")


def validate_order_data(order_id,request):
	order_data = frappe.get_doc('Order', order_id)
	order_data.paid_using_wallet = 0
	if request.get('discount'):
		insert_discount_usage_history(order_data.name,
		order_data.customer, request.get('discount'))
	coupon_code = None
	if request.get('coupon_code'):
		coupon_code = request.get('coupon_code')
		order_data.discount_coupon = request.get('coupon_code')
	if coupon_code:
		coupon_discount = coupon_code
		if frappe.db.get_all("Discounts",
			filters={"coupon_code":coupon_code}):
			disc_list = frappe.db.get_all("Discounts",
						filters={"coupon_code":coupon_code})
			coupon_discount = disc_list[0].name
			insert_discount_usage_history(order_data.name,
			order_data.customer, coupon_discount)
		else:
			disc_list = frappe.db.get_all("Discounts",
						filters={"name":coupon_code},fields = ['coupon_code','name'])
			if disc_list:
				order_data.discount_coupon = disc_list[0].coupon_code
				coupon_discount = disc_list[0].name
				insert_discount_usage_history(order_data.name,
				order_data.customer, coupon_discount)
	if request.get('discount_amount'):
		order_data.discount = request.get('discount_amount')
	order_data.save(ignore_permissions=True)
	wallet_settings = frappe.get_single('Wallet Settings')
	if wallet_settings.enable_customer_wallet:
		if request.get('manual_wallet_debit') == 1:
			if int(request.get('manual_wallet_debit')) == 1:
				customer_order_total = order_data.total_amount - order_data.discount
				debit_customer_wallet(cust_id = order_data.customer,
						order_amount = customer_order_total, order_id = order_data.name)


def get_cart_items(order_id,customer):
	OrderItem = DocType('Order Item')
	DiscountUsageHistory = DocType('Discount Usage History')
	frappe.qb.from_(OrderItem).delete().where(OrderItem.parent == order_id).run()
	frappe.qb.from_(DiscountUsageHistory).delete().where(DiscountUsageHistory.order_id == order_id).run()
	order_info = frappe.get_doc('Order', order_id)
	cart = frappe.db.get_all('Shopping Cart',
		filters={'customer': customer, 'cart_type': 'Shopping Cart'},
		fields=['name', 'tax', 'tax_breakup', 'total'])
	return cart

def order_items_list(cart):
	CartItem = DocType('Cart Items')
	Product = DocType('Product')
	items = (frappe.qb.from_(CartItem).join(Product).on(Product.name == CartItem.product) 
		.select(
			CartItem.name,
			CartItem.product,
			CartItem.checkout_attributes,
			CartItem.special_instruction,
			CartItem.quantity,
			CartItem.attribute_description,
			CartItem.price,
			CartItem.total,
			CartItem.shipping_charges,
			Product.short_description,
			Product.route,
			CartItem.recipient_name,
			CartItem.recipient_email,
			CartItem.certificate_occasion,
			CartItem.product_name,
			CartItem.tax,
			CartItem.attribute_ids,
			Product.stock,
			CartItem.is_gift_card,
			CartItem.sender_name,
			CartItem.sender_email,
			CartItem.sender_message,
			CartItem.certificate_type,
			Product.image.as_("image"),
			CartItem.is_free_item,
			CartItem.discount_rule
		) 
		.where(CartItem.parent == cart[0].name) 
		.orderby(CartItem.idx) 
		.run(as_dict=True))

	return items

def validate_cart_free_item(cart_item,total,included_tax,item_tax,tax_splitup,discount,order_info,tax_type):
	total = total - discount
	tax_template = None
	if tax_template:
		if tax_template.tax_rates:
			for tax in tax_template.tax_rates:
				if included_tax:
					tax_value = flt(total) * tax.rate / (100 + tax.rate)
				else:
					tax_value = total * tax.rate / 100
				item_tax = item_tax + tax_value
				cur_tax = next((x for x in tax_splitup if (x['type'] == tax.tax and\
									x['rate'] == tax.rate)), None)
				if cur_tax:
					for it in tax_splitup:
						if it['type'] == tax.tax:
							it['amount'] = it['amount'] + tax_value
				else:
					tax_splitup.append({
										'type': tax.tax,
										'rate': tax.rate,
										'amount': tax_value,
										'account':tax.get('account_head'),
										'tax_type': tax_type
										})
	values = get_value_cart_item(cart_item)
	item_weight = values[0]
	item_sku = values[1]
	if item_weight == 0:
		item_weight =  1
	base_price = 0
	base_price = cart_item.price / item_weight
	return [item_sku,base_price,item_weight]


def get_order_itm_list(order_info, cart_item, item_sku, item_weight, total, item_tax, discount, base_price):
	result = frappe.get_doc({
							'doctype': 'Order Item',
							'parent': order_info.name,
							'parenttype': 'Order',
							'parentfield': 'order_item',
							'order_item_type': 'Product',
							'item': cart_item.product,
							'item_name': cart_item.product_name,
							'item_sku':item_sku,
							'ordered_weight':item_weight*cart_item.quantity,
							'weight':item_weight*cart_item.quantity,
							'quantity': cart_item.quantity,
							'price': cart_item.price,
							'amount': cart_item.total,
							'attribute_description': cart_item.attribute_description,
							'checkout_attributes': cart_item.checkout_attributes,
							't_amount': total,
							'shipping_charges': cart_item.shipping_charges,
							'tax': item_tax,
							'd_amount': discount,
							'attribute_ids': cart_item.attribute_ids,
							'special_instruction': cart_item.special_instruction,
							'is_free_item': cart_item.is_free_item,
							'is_gift_card': cart_item.is_gift_card,
							'discount': cart_item.discount_rule,
							'base_price': base_price,
							'is_gift_card':cart_item.is_gift_card,
							'sender_name':cart_item.sender_name,
							'sender_email':cart_item.sender_email,
							'recipient_name':cart_item.recipient_name,
							'recipient_email':cart_item.recipient_email,
							'sender_message':cart_item.sender_message
							}).save(ignore_permissions=True)


def get_value_cart_item(cart_item):
	item_sku = frappe.db.get_value('Product',cart_item.
				product,'sku')
	item_price = frappe.db.get_value('Product',
					cart_item.product,'price')
	item_weight = frappe.db.get_value('Product',
					cart_item.product,'weight')
	tracking_method = frappe.db.get_value('Product',
						cart_item.product,'inventory_method')
	if cart_item.attribute_ids:
		attribute_id = get_attributes_json(cart_item.attribute_ids)
		ProductVariantCombination = DocType('Product Variant Combination')
		combination_weight = (frappe.qb.from_(ProductVariantCombination) 
			.select(
				ProductVariantCombination.weight,
				ProductVariantCombination.sku
			)
			.where(
				(ProductVariantCombination.parent ==  cart_item.product) &
				(ProductVariantCombination.attributes_json == attribute_id.replace(" ", ""))
			)
			.run(as_dict=True))
		
		
		if combination_weight:
			item_weight = combination_weight[0].weight
			item_sku = combination_weight[0].sku
	else:
		item_weight = item_weight
		if cart_item.attribute_ids:
			attr_id = cart_item.attribute_ids.splitlines()
			for item in attr_id:
				ProductAttributeOption = DocType('Product Attribute Option')
				attribute_weight = (frappe.qb.from_(ProductAttributeOption) 
					.select('*') 
					.where(ProductAttributeOption.name == item) 
					.run(as_dict=True))
				if attribute_weight and attribute_weight[0].weight_adjustment:
					item_weight += flt(attribute_weight[0].weight_adjustment)
	return [item_weight,item_sku]


@frappe.whitelist()
@role_auth(role='Customer',method="POST")
def post_order_feedback(order_id, ratings, message):
	customer = get_customer_from_token()
	var = frappe.db.get_value("Order", order_id, "customer")
	if var == customer:
		if not frappe.db.get_all("Order Feedback",filters = {"order" : order_id}):
			order_status = frappe.db.get_value("Order", order_id, "status")
			if order_status == "Delivered" or order_status == "Completed":
				feedback_doc = frappe.new_doc('Order Feedback')
				feedback_doc.order = order_id
				feedback_doc.posted_on = getdate()
				feedback_doc.ratings = ratings
				feedback_doc.comments = message
				feedback_doc.save(ignore_permissions=True)
				return {
						"status":"Success"
					}
		else:
			return {
					"status":"Failed",
					"message":"Already feedback is posted for this order."
				}
	return {
			"status":"Failed",
			"message":"You are not allowed to do this action."
		}


@frappe.whitelist()
def update_order_status(status,OrderId,Tracking_Number=None,Tracking_Link=None):
	try:
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
		order_id = OrderId
		order_doc = None
	except Exception:
		frappe.log_error("Error in v2.orders.update_order_status", frappe.get_traceback())


@frappe.whitelist(allow_guest=True)
def get_checkout_attributes():
	try:
		CheckoutAttributes = DocType('Checkout Attributes')
		checkout_attribute = (frappe.qb.from_(CheckoutAttributes) 
			.select(
				CheckoutAttributes.question,
				CheckoutAttributes.control_type,
				CheckoutAttributes.is_required,
				CheckoutAttributes.name,
				CheckoutAttributes.is_group,
				CheckoutAttributes.charge_based_on_weight,
				CheckoutAttributes.short_description
			) 
			.where(
				(CheckoutAttributes.is_active == 1) &
				((CheckoutAttributes.is_group == 1) | (CheckoutAttributes.parent_attribute.isnull()))
			) 
			.run(as_dict=True))
		if checkout_attribute:
			for item in checkout_attribute:
				CheckoutAttributesOptions = DocType('Checkout Attributes Options')
				item.options = (frappe.qb.from_(CheckoutAttributesOptions) 
					.select(
						CheckoutAttributesOptions.option_value,
						CheckoutAttributesOptions.display_order,
						CheckoutAttributesOptions.price_adjustment,
						CheckoutAttributesOptions.name,
						CheckoutAttributesOptions.is_pre_selected
					) 
					.where(
						CheckoutAttributesOptions.parent == item.name
					) 
					.orderby(CheckoutAttributesOptions.display_order) 
					.run(as_dict=True))
				
				if item.is_group:
					CheckoutAttributes = DocType('Checkout Attributes')
					child_attributes = (frappe.qb.from_(CheckoutAttributes) 
						.select(
							CheckoutAttributes.question,
							CheckoutAttributes.control_type,
							CheckoutAttributes.is_required,
							CheckoutAttributes.name,
							CheckoutAttributes.charge_based_on_weight,
							CheckoutAttributes.parent_attribute,
							CheckoutAttributes.parent_attribute_option,
							CheckoutAttributes.short_description
						) 
						.where(
							(CheckoutAttributes.is_active == 1) &
							(CheckoutAttributes.is_group == 0) &
							(CheckoutAttributes.parent_attribute == item.name)
						) 
						.run(as_dict=True))
					
					for ch in child_attributes:
						CheckoutAttributesOptions = DocType('Checkout Attributes Options')
						ch.options = (frappe.qb.from_(CheckoutAttributesOptions) 
							.select(
								CheckoutAttributesOptions.option_value,
								CheckoutAttributesOptions.display_order,
								CheckoutAttributesOptions.price_adjustment,
								CheckoutAttributesOptions.name,
								CheckoutAttributesOptions.is_pre_selected
							) 
							.where(
								CheckoutAttributesOptions.parent == ch.name
							) 
							.orderby(CheckoutAttributesOptions.display_order) 
							.run(as_dict=True))
						
					item.child_attributes = child_attributes
			return checkout_attribute
	except Exception:
		frappe.log_error('Error in v2.orders.get_checkout_attributes', frappe.get_traceback())


@frappe.whitelist()
@role_auth(role = 'Customer',method = "POST")
def reorder(order_id):
	try:
		order = frappe.get_doc('Order',order_id)
		customer = get_customer_from_token()
		if customer:
			cart = frappe.db.get_all('Shopping Cart',
									filters = {'customer': customer,'cart_type':'Shopping Cart'},
									fields = ['name'])
			cart_doc = frappe.new_doc('Shopping Cart')
			if cart:
				CartItems = DocType('Cart Items')
				det = (frappe.qb.from_(CartItems) 
					.where(CartItems.parent == cart[0].name) 
					.delete())
				
				frappe.db.commit()
				cart_doc = frappe.get_doc('Shopping Cart', cart[0].name)
			cart_doc.cart_type = "Shopping Cart"
			cart_doc.customer = customer
			return get_reorder_list(order,cart_doc)
	except Exception:
		frappe.log_error('Error in v2.order.reorder', frappe.get_traceback())
		return {
				'status': "Failed",
				'message': frappe._('Something went wrong. Please try again.')
			}


def get_reorder_list(order,cart_doc):
	no_stock = 0
	allowed_prdts = 0
	for x in order.order_item:
		if x.is_free_item != 1:
			price = 0
			is_allowed = 1
			if not x.attribute_ids:
				Product = DocType('Product')
				p_price = (frappe.qb.from_(Product) 
					.select(Product.price) 
					.where(Product.name == x.item) 
					.orderby(Product.price) 
					.run(as_dict=True))
				
				if not p_price:
					no_stock = 1
					is_allowed = 0
				if p_price:
					price = p_price[0].price
			cart_items_append(cart_doc,x,price,is_allowed,allowed_prdts)
	frappe.db.commit()
	message = "Successfully added into your Cart"
	if no_stock == 1:
		message = "Some of the items in the previous order is out of stock."
	return {
			"status":"Success" if allowed_prdts > 0 else "Failed",
			"message":message
		}


def cart_items_append(cart_doc,x,price,is_allowed,allowed_prdts):
	if is_allowed==1:
		allowed_prdts = allowed_prdts+1
		cart_doc.append('items',{   
									'product': x.item,
									'quantity': x.quantity,
									'price': price,
									'is_gift_card': x.is_gift_card,
									'total': float(price) * float(x.quantity),
									'attribute_description': x.attribute_description,
									'attribute_ids': x.attribute_ids,
									'special_instruction': x.special_instruction,
									'recipient_email': x.recipient_email,
									'recipient_name': x.recipient_name,
									'sender_email': x.sender_email,
									'sender_message': x.sender_message,
									'sender_name': x.sender_name,
								}).save(ignore_permissions=True)


def calculate_tax_from_template(tax_template, amount, tax_splitup):
	tax_amt = 0
	tax_amt1 = 0
	included_tax = get_settings_value('Catalog Settings', 'included_tax')
	if tax_template.tax_rates:
		for tax in tax_template.tax_rates:
			if included_tax:
				tax_amt = tax_amt + (float(amount) * tax.rate / (100 + tax.rate))
				tax_amt1 = float(amount) * tax.rate / (100 + tax.rate)
			else:
				tax_amt = tax_amt + (float(amount) * tax.rate / 100)
				tax_amt1 = float(amount) * tax.rate / 100
			rate_tax1 = '{:12.2f}'.format(tax.rate)
			cur_tax = next((x for x in tax_splitup if (x['type'] == tax.tax and x['rate'] == tax.rate)), None)
			if cur_tax:
				for it in tax_splitup:
					if it['type'] == tax.tax:
						it['amount'] = it['amount'] + tax_amt1
			else:
				tax_splitup.append({'type': tax.tax, 'rate': rate_tax1, 'amount': tax_amt1})
	return (tax_amt, tax_splitup)


def check_return_request_mandatory_fields(data):
	mand_fields = ["order_id","items","images","remarks"]
	for keys in mand_fields:
		if keys not in data:
			return {
					"status":"Failed",
					"message": f"field:{keys} missing"
				}
	return {
			"status":"Success"
		}


def get_order_item_details(order_item):
	Order = DocType('Order')
	OrderItem = DocType('Order Item')
	resp__ = (frappe.qb.from_(OrderItem) 
		.inner_join(Order).on(OrderItem.parent == Order.name) 
		.select(
			Order.customer,
			Order.customer_email,
			Order.customer_name,
			OrderItem.item.as_("product"),
			OrderItem.item_name.as_("product_name"),
			OrderItem.attribute_description,
			OrderItem.attribute_ids.as_("attribute_id")
		) 
		.where(OrderItem.name == order_item) 
		.run(as_dict=True))
	if resp__:
		return {
				'status':"success",
				"message":resp__[0]
			}
	else:
		return {
				"status":"failed",
				"message":"Order item details not found..!"
			}


@frappe.whitelist()
# @role_auth(role = 'Customer',method = "POST")
def create_return_request(**kwargs):
	try:
		data = json.loads(kwargs.get("data"))
		check_mandatory = check_return_request_mandatory_fields(data)
		if check_mandatory.get("status") == "Success":
			order_details = frappe.get_doc("Order",data.get("order_id"))
			return_doc = frappe.new_doc("Return Request")
			if data.get("images"):
				res = frappe.get_doc({
						"doctype": "File",
						"file_url": data.get("images"),
						"is_private": 0
						})
				return_doc.append("attach_images",{"add_image":res.file_url})
			return_doc.naming_series = "RR-"
			return_doc.posted_on = getdate()
			return_doc.order_id = data.get("order_id")
			return_doc.remarks = data.get("remarks")
			return_doc.customer = order_details.get("customer")
			return_doc.customer_name = order_details.get("customer_name")
			return_doc.customer_email = order_details.get("customer_email")
			return_doc.customer_phone = order_details.get("phone")
			for x in data.get("items"):
				order_item_info = order_details.order_item
				for i in order_item_info:
					return_doc.append("items",{
						"order_item":i.name,
						"quantity":x.get("quantity"),
						"product":i.item,
						"product_name":i.item_name,
						"attribute_description": i.attribute_description,
						"attribute_id": i.attribute_ids,
						"reason_for_return":data.get("return_reason")
						})
			return_doc.type = 'Return'
			return_doc.status = 'Return Initiated'
			return_doc.save(ignore_permissions = True)
			order_details.status = "Returned"
			order_details.save(ignore_permissions = True)
			frappe.db.commit()
			if data.get("driver"):
				if frappe.db.exists("Drivers",data.get("driver")):
					create_return_shipment(return_doc,data.get("driver"))
			return {
					"status":"Success",
					"return_request_id": return_doc.name,
					"message": "Return Request Created Successfully"
				}
		else:
			check_mandatory_exception(check_mandatory.get("message"))
	except Exception:
		frappe.log_error("Error in v2.orders create_return_request", frappe.get_traceback())
		other_exception("customer create_return_request")


@frappe.whitelist()
def get_order_invoices(order_id):
	customer_id = get_customer_from_token()
	if customer_id == frappe.db.get_value("Order",order_id,"customer"):
		import random
		import string
		letters = string.ascii_letters
		token = frappe.db.get_value("Order",order_id,"uuid")
		if not token:
			token = ''.join(random.choice(letters) for i in range(25))
			
			Order = DocType('Order')
			upt =(frappe.qb.update(Order) 
				.set(Order.uuid, token) 
				.where(Order.name == order_id) 
				.run())
			frappe.db.commit()
		url_string = frappe.utils.get_url()+'/api/method/go1_commerce.\
							go1_commerce.v2.orders.get_invoices?token='+str(token)
		return {
				"status":"Success",
				"url":url_string
			}
	else:
		return {
				"status":"Failed",
				"message":'Invalid Order ID. !'
			}

@frappe.whitelist(allow_guest=True)
def get_Products_Tax_Template(name):
	tax = frappe.db.get_all('Product Tax Template', fields = ['name'],
							filters={'name': name})
	if tax:
		for i in tax:
			i.tax_rate = frappe.get_all('Tax Rates', fields = ['rate'],
					filters={'parent': i.name})
	return tax

@frappe.whitelist()
def get_city_based_role():
	m_settings = frappe.get_single("Market Place Settings")
	roles = ",".join(['"' + x.role + '"' for x in m_settings.city_based_role])
	return roles

@frappe.whitelist()
def get_today_date(time_zone = None, replace = False):
	'''
		get today  date based on selected time_zone
	'''
	from pytz import timezone
	if not time_zone:
		time_zone = frappe.db.get_single_value('System Settings', 'time_zone')
	currentdatezone = datetime.now(timezone(time_zone))
	if replace:
		return currentdatezone.replace(tzinfo=None)
	else:
		return currentdatezone


@frappe.whitelist(allow_guest=True)
def create_return_shipment(dt, dn, products, driver, status, tracking_number=None, tracking_link=None):
	try:
		doc = frappe.get_doc(dt, dn)
		frappe.db.set_value(dt, dn, 'status', "Ready to Ship")
		frappe.db.set_value(dt, dn, 'driver', driver)
		items = json.loads(products)
		total = qty = 0
		order_shipmemt = frappe.db.get_all('Return Shipment',fields=['name'],filters={'document_name':dn})
		if not order_shipmemt:
			shipment = frappe.new_doc('Return Shipment')
			shipment.document_type = dt
			shipment.document_name = dn
			shipment.shipped_date = get_today_date(replace = True)
			shipment.status = status
			shipment.driver = driver
			shipment.tracking_number = tracking_number
			shipment.tracking_link = tracking_link
			for item in items:
				shipment.append('items',{
										'item_type': item["order_item_type"],
										'item': item["item"],
										'item_name': item["item_name"],
										'quantity': item["quantity"],
										'price': item["price"],
										'total': item["amount"]
										})
				qty = qty + item["quantity"]
				total += item["amount"]
			shipment.total_quantity = qty
			shipment.order_total = total
			shipment.docstatus = 1
			shipment.save(ignore_permissions = True)
			return shipment
		else:
			frappe.db.set_value('Return Shipment', order_shipmemt[0].name, 'status', "Ready to Ship")
			if tracking_number:
				frappe.db.set_value('Return Shipment', order_shipmemt[0].name, 'tracking_number', tracking_number)
			if tracking_link:
				frappe.db.set_value('Return Shipment', order_shipmemt[0].name, 'tracking_link', tracking_link)
			if driver:
				ReturnShipment = DocType('Return Shipment')
				upt =(frappe.qb.update(ReturnShipment) 
					.set(ReturnShipment.driver, driver) 
					.where(ReturnShipment.name == order_shipmemt[0].name) 
					.run())
				
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in v2.orsers.create_return_shipment")


@frappe.whitelist()
def update_stoke(doc, method):
	data = json.loads(doc.data)
	if data.get("row_changed"):
		changes = data.get("row_changed")
		for i in changes[0][3]:
			field_name = i[0]
			new_value = i[1]
			old_value = i[2]
			if field_name == "quantity":
				if new_value > old_value:
					updated_quantity = new_value - old_value
					set_quantity_variants(doc, updated_quantity, allow = 1)
				else:
					updated_quantity = old_value - new_value
					set_quantity_variants(doc, updated_quantity, allow = 0)
					
					
def set_quantity_variants(doc, quantity, allow = 0):
	from go1_commerce.go1_commerce.\
		doctype.order.order import update_variant_id
	order_items = frappe.db.get_all("Order Item",
									fields = ["*"], 
									filters = {"parent":doc.docname,"parenttype":"Order"})
	for item in order_items:
		has_variant = frappe.db.get_value("Product",item.item,"has_variants")
		if has_variant:
			attr_id = update_variant_id(item.item, item.varaint_txt)
			ProductVariantCombination = DocType('Product Variant Combination')
			ProductAttributeOption = DocType('Product Attribute Option')
			result = (frappe.qb.from_(ProductVariantCombination) 
				.inner_join(ProductAttributeOption) 
				.on(ProductVariantCombination.attribute_id == attr_id) 
				.select(ProductVariantCombination.stock, ProductVariantCombination.product_title, ProductVariantCombination.name) 
				.where(ProductVariantCombination.parent == item.item) 
				.limit(1) 
				.run(as_dict=True))

			variant_stock= result[0] if result else None
			updated_quantity = 0
			if allow == 1:
				updated_quantity = variant_stock.stock + quantity
			else:
				updated_quantity = variant_stock.stock - quantity
			frappe.db.set_value(
								"Product Variant Combination",
								variant_stock.name,
								"stock",
								updated_quantity 
							)
			frappe.db.commit()