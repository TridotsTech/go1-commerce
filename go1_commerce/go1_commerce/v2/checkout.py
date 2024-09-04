from __future__ import unicode_literals, print_function
import frappe, json
from frappe import _
from frappe.utils import getdate,get_datetime
from datetime import datetime
from six import string_types
from go1_commerce.utils.utils import get_today_date
from go1_commerce.utils.utils import get_customer_from_token,other_exception
from frappe.query_builder import DocType, Field, Order

@frappe.whitelist()
def check_cartitems_stock_mob(customer_id=None):
	try:
		if customer_id:
			customers = frappe.db.get_all('Customers', 
						filters={'name': customer_id}, 
						fields=['*'])
		else:
			customers = frappe.db.get_all('Customers',
						filters={'user_id': frappe.session.user}, 
						fields=['*'])
		cart = frappe.db.get_all('Shopping Cart', 
			filters={'customer': customers[0].name, 'cart_type': 'Shopping Cart'}, 
			fields=['name', 'tax', 'tax_breakup'])
		if cart:
			CartItems = DocType("Cart Items")
			Product = DocType("Product")
			query = (
				frappe.qb
				.from_(CartItems)
				.join(Product)
				.on(Product.name == CartItems.product)
				.select(
					CartItems.name,
					CartItems.product,
					CartItems.quantity,
					CartItems.attribute_description,
					CartItems.attribute_ids,
					CartItems.price.as_("cart_price"),
					CartItems.total,
					CartItems.product_name,
					Product.price.as_("product_price"),
					Product.stock,
					Product.short_description,
					Product.route,
					Product.image
				)
				.where(CartItems.parent == cart[0].name)
				.orderby(CartItems.idx)
			)
			items= query.run(as_dict=True)
			stock = False
			for cart_item in items:
				ProductId = cart_item.product
				add_qty = 'false'
				from go1_commerce.go1_commerce.v2.orders\
					import validate_product_cart_qty1
				res = validate_product_cart_qty1(ProductId, attributeId=cart_item.
					attribute_ids, add_qty=add_qty,customer=customer_id)
				if res:
					if res['status'] == False:
						stock = False
						return {'status': False, 'message': res['message']}
					else:
						stock = True
			if stock == True:
				return {'status': True, 'message': ''}
	except Exception:
		other_exception("Error in v2.checkout.check_cartitems_stock_mob")

@frappe.whitelist()
def get_payment_methods():
	try:
		PaymentMethod = DocType("Payment Method")
		query = (
			frappe.qb.from_(PaymentMethod)
			.select(
				PaymentMethod.name,
				PaymentMethod.display_name.as_("payment_method"),
				PaymentMethod.description,
				PaymentMethod.redirect_controller,
				PaymentMethod.payment_type,
				PaymentMethod.additional_charge,
				PaymentMethod.use_additional_fee_percentage,
				PaymentMethod.additional_fee_percentage
			)
			.where(PaymentMethod.enable == 1)
			.orderby(PaymentMethod.display_order)
		)
		payment_method= query.run(as_dict=True)
		return payment_method
	except Exception:
		other_exception('Error in v2.checkout.get_payment_method')
	
@frappe.whitelist()	
def get_shipping_methods():
	try:
		order_settings = frappe.get_single('Order Settings')
		ShippingMethod = DocType("Shipping Method")
		query = (
			frappe.qb
			.from_(ShippingMethod)
			.select(
				ShippingMethod.name,
				ShippingMethod.shipping_method_name,
				ShippingMethod.description,
				ShippingMethod.is_deliverable
			)
			.where(ShippingMethod.show_in_website == 1)
			.orderby(ShippingMethod.display_order)
		)
		data = query.run(as_dict=True)
		return data
	except Exception:
		other_exception("Error in v2.checkout.get_shipping_method")

@frappe.whitelist()	
def calculate_shipping_charges(shipping_method,shipping_addr,cart_id):
	try:
		from go1_commerce.utils.setup import get_settings
		ShippingRateMethod = DocType("Shipping Rate Method")
		query = (
			frappe.qb.from_(ShippingRateMethod)
			.select(
				ShippingRateMethod.name.as_("id"),
				ShippingRateMethod.shipping_rate_method.as_("shipping_category")
			)
			.where(ShippingRateMethod.is_active == 1)
		)
		active_shipping_rate_method_info= query.run(as_dict=True)
		if active_shipping_rate_method_info:
			active_shipping_rate_method_info = active_shipping_rate_method_info[0]
			catalog_settings = get_settings('Catalog Settings')
			shopping_cart = frappe.get_doc('Shopping Cart', cart_id)
			shipping_address_info = frappe.get_doc('Customer Address', shipping_addr)
			shipping_charges_resp = get_sh_charges_by_sh_method(active_shipping_rate_method_info,shipping_method,
														shipping_address_info,shopping_cart)
			if shipping_charges_resp.get("status") == "success":
				final_shipping_charges = shipping_charges_resp.get("shipping_charges")
				return calculate_tax_for_sh_chrgs(final_shipping_charges,shopping_cart,catalog_settings)
			else:
				return shipping_charges_resp
		else:
			return {"status":"failed","message":"Default Shipping Rate Method is not found."}
	except Exception:
		other_exception("Error in v2.checkout.calculate_shipping_charges")

def get_sh_charges_by_sh_method(SRM_info,shipping_method,shipping_addr,shopping_cart):
	from go1_commerce.go1_commerce.v2.orders import\
		calculate_weight_based_shipping_charges ,\
		calculate_total_based_shipping_charges , \
		calculate_fixed_rate_shipping_charges , \
		calculate_distance_based_shipping_charges, \
		calculate_distance_weight_based_shipping_charges, \
		calculate_distance_total_based_shipping_charges,\
		calculate_shipping_charges_distance_and_weight_group,\
		calculate_per_distance_per_weight_based_sh_chrgs
	sh_charges_resp = None
	if SRM_info.shipping_category == 'Fixed Rate Shipping':
		sh_charges_resp = calculate_fixed_rate_shipping_charges(shipping_method,shipping_addr,shopping_cart)
	
	elif SRM_info.shipping_category == 'Shipping By Total':
		sh_charges_resp = calculate_total_based_shipping_charges(shipping_method,shipping_addr,shopping_cart)
	
	elif SRM_info.shipping_category == 'Shipping By Weight':
		sh_charges_resp = calculate_weight_based_shipping_charges(shipping_method,shopping_cart)
	
	elif SRM_info.shipping_category == 'Shipping By Distance':
		sh_charges_resp = calculate_distance_based_shipping_charges(shipping_method,shipping_addr,shopping_cart)
		
	elif SRM_info.shipping_category == 'Shipping By Distance and Total':
		sh_charges_resp = calculate_distance_total_based_shipping_charges(shipping_method,shipping_addr,shopping_cart)
		
	elif SRM_info.shipping_category == 'Shipping By Distance and Weight':
		sh_charges_resp = calculate_distance_weight_based_shipping_charges(shipping_method, shipping_addr,shopping_cart)
		
	elif SRM_info.shipping_category == 'Shipping By Distance / Weight':
		sh_charges_resp = calculate_per_distance_per_weight_based_sh_chrgs(SRM_info.get("id"),shipping_addr,shopping_cart)
		
	elif SRM_info.shipping_category == 'Shipping By Group By Distance and Weight':
		sh_charges_resp = calculate_shipping_charges_distance_and_weight_group(SRM_info.get("id"),shipping_addr,
																			   shopping_cart)
	return sh_charges_resp

def calculate_tax_for_sh_chrgs(shipping_charges,shopping_cart,catalog_settings):
	tax_percent = total_tax_amount = 0
	if shipping_charges and catalog_settings.shipping_is_taxable and catalog_settings.shipping_tax_class:
		tax_template = frappe.get_doc('Product Tax Template',catalog_settings.shipping_tax_class)
		for item in tax_template.tax_rates:
			tax_percent += item.rate
			if catalog_settings.shipping_price_includes_tax:
				total_tax_amount += round(shipping_charges * item.rate / (100 + item.rate), 2)
			else:
				total_tax_amount += round(shipping_charges * item.rate / 100, 2)
	return {'status':'success','shipping_charges': shipping_charges,
			'shipping_tax_rate': total_tax_amount,
			'shipping_tax_percent': tax_percent,
			'item_tax_rate': shopping_cart.tax if shopping_cart else 0}


@frappe.whitelist()
def get_order_discount(subtotal,total_weight=0,shipping_method=None,payment_method=None,shipping_charges=0):
	try:
		cart_items = None
		customer_id = get_customer_from_token()
		from go1_commerce.go1_commerce.doctype.discounts.discounts \
		import get_order_subtotal_discount
		from go1_commerce.go1_commerce.v2.orders\
		import calculate_tax_after_discount , calculate_tax_without_discount
		customer_cart = frappe.db.get_all('Shopping Cart', 
						filters={'cart_type': 'Shopping Cart', 
								 'customer': customer_id}, 
						fields=['*'])
		if customer_cart:
			cart_items = frappe.db.get_all('Cart Items', 
						 filters={'parent': customer_cart[0].name, 'is_free_item': 0}, 
						 fields=['product', 'quantity', 'parent', 'price', 
								 'attribute_ids', 'attribute_description',
								 'is_free_item', 'total', 'discount_rule'])
		if cart_items:
			response = get_order_subtotal_discount(subtotal, customer_id, cart_items, 
					   total_weight,shipping_method, payment_method,shipping_charges)
			if response and (response.get('discount_rule') or \
				response.get('product_discount')) or response.get('shipping_discount'):
				(tax, tax_splitup) = calculate_tax_after_discount(customer_id, 
									 response.get('discount_amount'),
									 response.get('discount_rule'), 
									 subtotal, cart_items, response=response)
				return {'status': 'Success',
						'discount_amount': response.get('discount_amount'),
						'discount': response.get('discount_rule'),
						'tax': tax,
						'tax_splitup': tax_splitup,
						'discount_response': response}
			else:
				(tax, tax_splitup) = calculate_tax_without_discount(customer_id,subtotal, cart_items,
									discount_amount=0,discount=None, response=response)
				return {'status': 'Success',
						'discount_amount': 0,
						'discount': None,
						'tax': tax,
						'tax_splitup': tax_splitup,
						'discount_response': response}	
		return {'status': 'failed', 'discount_amount': 0}
	except Exception:
		other_exception("Error in v2.checkout.get_order_discount")

@frappe.whitelist()
def validate_coupon(coupon_code, customer_id, subtotal, total_weight=0, discount_type=None, 
	shipping_method=None, payment_method=None, ngCart=None,shipping_charges=None):
	try:
		cart_items = None
		if ngCart:
			if isinstance(ngCart, string_types):
				ngCart = json.loads(ngCart)
			cart_items = []
			for item in ngCart:
				attribute_ids = None
				if item.get('Addons'):
					attribute_ids = '\n'.join([x.get('name') for x in item.get('Addons')])
				item_info = item.get('item')
				cart_items.append({'product': item.get('id'),
									'quantity': item.get('quantity'),
									'price': item.get('prices'),
									'attribute_ids': attribute_ids,
									'attribute_description': '', 
									'is_free_item': 0,
									'total': float(item.get('quantity'))  * float(item.get('prices')),
									'discount_rule': item_info.get('discount_rule')})
		else:
			customer_cart = frappe.db.get_all('Shopping Cart', 
							filters={'cart_type':'Shopping Cart','customer': customer_id},
							 fields=['*'])
			if customer_cart:
				cart_items = frappe.db.get_all('Cart Items',
							 filters={'parent': customer_cart[0].name, 'is_free_item': 0}, 
							 fields=['product', 'quantity', 'parent', 'price', 
									 'attribute_ids', 'attribute_description',
									 'is_free_item', 'total', 'discount_rule'])
		return get_validate_coupons_cart_items(coupon_code, subtotal, customer_id,cart_items,shipping_charges, 
					discount_type,total_weight, shipping_method, payment_method)
	except Exception:
		other_exception("Error in v2.checkout.validate_coupon")


def get_validate_coupons_cart_items(coupon_code, subtotal, customer_id, cart_items,shipping_charges,
								discount_type,total_weight, shipping_method, payment_method):
	from go1_commerce.go1_commerce.doctype.discounts.discounts\
	import get_coupon_code
	if cart_items:
		response = get_coupon_code(coupon_code, subtotal, customer_id, cart_items,
				   discount_type = discount_type, shipping_method=shipping_method, 
				   payment_method=payment_method, shipping_charges=shipping_charges, 
					total_weight =total_weight)
		if response and response.get('discount_rule'):
			if not response.get("shipping_discount"):
				return val_shipping_discount(response,total_weight, shipping_method, payment_method,subtotal,
										discount_type,cart_items,customer_id)
			else:
				return {
						'status': 'success',
						'shipping_charges': response.get('shipping_charges'),
						'shipping_discount':response.get('shipping_discount'),
						'shipping_label':response.get('shipping_label'),
						'shipping_discount_id':response.get('discount_rule')
						}
		elif response:
			return {'status': 'failed', 'message': response.get('message')}


def get_caskback_account(calculate_tax_after_discount,response, subtotal,discount_type,
							cart_items, prev_discount,customer_id,cashback_amount):
	if cashback_amount > 0:
		if response.get('cashback'):
			response['cashback_amount'] = float(response['cashback_amount']) + cashback_amount
		else:
			response['cashback'] = 1
			response['cashback_amount'] = cashback_amount
	(tax, tax_splitup) = calculate_tax_after_discount(customer_id, response.get('discount_amount'),
							response.get('discount_rule'), subtotal,
							cart_items, prev_discount, discount_type, response=response)
	return {'status': 'success',
			'discount_amount': response.get('discount_amount'),
			'discount': response.get('discount_rule'),
			'tax': tax,
			'tax_splitup': tax_splitup,
			'discount_response': response,
			'prev_discount': prev_discount}


def val_shipping_discount(response,total_weight, shipping_method, payment_method,subtotal,
									discount_type,cart_items,customer_id):
	from go1_commerce.go1_commerce.v2.orders\
		import calculate_tax_after_discount
	prev_discount = None
	cashback_amount = 0
	check_other_discounts = get_order_discount(subtotal,
							total_weight, shipping_method, payment_method)
	if check_other_discounts and check_other_discounts['status'] != 'failed':
		prev_discount = check_other_discounts
		if prev_discount['discount_response']:
			prev_res = prev_discount['discount_response']
			if prev_res.get('cashback') == 1:
				cashback_amount = prev_res.get('cashback_amount')
	return get_caskback_account(calculate_tax_after_discount,response,subtotal, \
										discount_type,cart_items,prev_discount, \
										customer_id,cashback_amount)

@frappe.whitelist()
def get_cart_delivery_slots(shipping_method=None):
	try:
		if not shipping_method:
			shipping_methods = frappe.db.get_all("Shipping Method",filters={"is_deliverable":1,
																			"show_in_website":1},order_by="name")
			if shipping_methods:
				shipping_method = shipping_methods[0].name
		return get_cart_delivery_categories(shipping_method)
	except Exception:
		other_exception("Error in v2.checkout.get_shipping_method_with_delivery_slots_for_mobile")

def get_cart_delivery_categories(shipping_method):

	default_delivery_slots = []
	DeliverySlotShippingMethod = DocType("Delivery Slot Shipping Method")
	DeliverySetting = DocType("Delivery Setting")
	query = (
		frappe.qb.from_(DeliverySlotShippingMethod)
		.join(DeliverySetting)
		.on(DeliverySetting.name == DeliverySlotShippingMethod.parent)
		.select(DeliverySlotShippingMethod.parent)
		.where(DeliverySetting.enable == 1)
	)
	
	if shipping_method:
		query = query.where(DeliverySlotShippingMethod.shipping_method == shipping_method)
	delivery_list= query.run(as_dict=True)
	for x in delivery_list:
		slot_cat = frappe.db.get_all("Delivery Slot Category", filters={"parent":x.parent})
		if not slot_cat:
			(dates_lists, blocked_day_list) = get_delivery_slots_list(x.parent)
			x.dates_lists = dates_lists
			x.blocked_day_list = blocked_day_list
			for available_day in x.dates_lists:
				if getdate(str(available_day.get("date")).split(" ")[0]) in blocked_day_list:
					available_day["allowed"] = 0
				else:
					available_day["allowed"] = 1
			default_delivery_slots.append(x)
	return default_delivery_slots

def get_delivery_slots_list(name):
	delivery = frappe.get_doc('Delivery Setting', name)
	if delivery:
		today_date = get_today_date(replace=True)
		dates_list = []
		blocked_day_list = []
		if delivery.enable_start_date and delivery.no_of_dates_start_from>0:
			today_date = frappe.utils.add_days(today_date, int(delivery.no_of_dates_start_from))
			slots_list = get_slot_lists(delivery.delivery_slots, today_date, 
										delivery.min_time, delivery.restrict_slot, 
										delivery.max_booking_slot)
			if slots_list:
				dates_list.append({'date': today_date, 'slots': slots_list, 
								  'format_date': today_date.strftime('%b %d, %Y')})
		if delivery.slot_for_current_date:
			slots_list = get_slot_lists(delivery.delivery_slots, today_date, 
										delivery.min_time, delivery.restrict_slot, 
										delivery.max_booking_slot)
			if slots_list:
				dates_list.append({'date': today_date, 
								   'slots': slots_list, 
								   'format_date': today_date.strftime('%b %d, %Y')})
		data = get_delivery_list(delivery,today_date,dates_list,blocked_day_list)
		return data
  
  
def get_delivery_list(delivery,today_date,dates_list,blocked_day_list):
	if delivery.enable_future_dates:
		allowed_dates = delivery.no_of_future_dates
		if delivery.slot_for_current_date:
			allowed_dates = int(allowed_dates) + 1
		new_date = today_date
		block_day = new_date.strftime('%A')
		while len(dates_list) < int(allowed_dates):
			new_date = frappe.utils.add_days(new_date, days=1)
			block_day = new_date.strftime('%A')
			new_slot_list = []
			dtfmt = '%Y-%m-%d %H:%M:%S'
			for item in delivery.delivery_slots:
				allow = False
				slot_date = datetime.strptime(str(getdate(new_date)) + ' ' + str(item.from_time), dtfmt)
				to_date = datetime.strptime(str(getdate(new_date)) + ' ' + str(item.to_time), dtfmt)
				if delivery.restrict_slot:
					check_bookings = frappe.db.get_all('Order Delivery Slot',
										filters={'order_date': new_date, 
												'from_time': slot_date.strftime("%H:%M:%S")}, 
										limit_page_length=1000)
					if len(check_bookings) < int(delivery.max_booking_slot):
						allow = True
				else:
					allow = True
				if allow:
					doc = item.__dict__
					doc['time_format'] = '{0} - {1}'.format(slot_date.strftime('%I:%M %p'), 
														to_date.strftime('%I:%M %p'))
					new_slot_list.append(doc)
			blocked_day = frappe.db.get_all("Delivery Day Block",
							filters={	'parenttype':'Delivery Setting',
										'parentfield':'enable_day',
										'parent':delivery.name},
							fields=['day'])
			day_list = list(set([x.day for x in blocked_day if x.day == block_day]))
			if day_list and len(day_list) > 0:
				date1 = getdate(new_date)
				blocked_day_list.append(date1)
			dates_list.append({'date': new_date, 'slots': new_slot_list,
								'format_date': new_date.strftime('%b %d, %Y')})
			return [dates_list, blocked_day_list]


def get_slot_lists(slots, date, min_time, restrict, max_booking_slot):
	slot_list = []
	dtfmt = '%Y-%m-%d %H:%M:%S'
	for item in slots:
		current_date = get_datetime()
		from_date = datetime.strptime(str(getdate(date)) + ' ' + str(item.from_time), dtfmt)
		to_date = datetime.strptime(str(getdate(date)) + ' ' + str(item.to_time), dtfmt)
		if from_date > current_date:
			diff = frappe.utils.time_diff_in_seconds(from_date, current_date)
			current_date
			if diff >= (int(min_time) * 60):
				allow = False
				if restrict:
					check_bookings = frappe.db.get_all('Order Delivery Slot',
									 filters={'order_date': date, 
												'from_time': from_date.strftime("%H:%M:%S")}, 
									 limit_page_length=1000)
					if len(check_bookings) < int(max_booking_slot):
						allow = True
				else:
					allow = True
				if allow:
					doc = item.__dict__
					doc['time_format'] = '{0} - {1}'.format(from_date.strftime('%I:%M %p'), 
															to_date.strftime('%I:%M %p'))
					slot_list.append(doc)
	return slot_list
	
@frappe.whitelist()
def get_country_states(country):
	try:
		State = DocType("State")
		query = (
			frappe.qb.from_(State)
			.select(State.name)
			.where(State.country == country)
		)
		return query.run(as_dict=True)
	except Exception:
		other_exception("Error in v2.cart.get_country_states")


@frappe.whitelist()
def validate_order_pincode_validate(cartitems,ship_addr):
	try:
		CustomerAddress = DocType("Customer Address")
		query = (
			frappe.qb
			.from_(CustomerAddress)
			.select("*")
			.where(CustomerAddress.name == ship_addr)
		)
		customer_shipping_address= query.run(as_dict=True)
		if customer_shipping_address:
			items = ''
			i = 0
			for x in cartitems:
				check_avail = check_pincode_availability(customer_shipping_address[0].zipcode)
				if not check_avail.get("is_available"):
					i += 1
					items += '<br>' + str(i) + '. ' + x.product_name
			if len(items)>0:
				return {'status': "Failed", 
						'message': "The following items are not available for the location "\
									+ customer_shipping_address[0].zipcode + '' + items}
			return {'status': "Success"}
		else:
			return {'status': "Failed",
					'message':"Shipping Address not found."}
	except Exception:
		other_exception("Error in v2.checkout.validate_order_pincode_validate")


def check_pincode_availability(zipcode):
	try:
		pincode_available = False
		ShippingCity = DocType("Shipping City")
		query = (
			frappe.qb
			.from_(ShippingCity)
			.select(ShippingCity.zipcode_range, ShippingCity.name)  # Select specific fields
		)
		pincodes= query.run(as_dict=True)
		shipping_city=""
		if pincodes:
			for item in pincodes:
				if shipping_city:
					shipping_city += ', '	
				shipping_city += "'" + item.name + "'"
				pincode_available = shipping_zip_matches(zipcode,item.zipcode_range)
				if pincode_available == True:
					break
		if pincode_available == True:
			return {'is_available': 1}
		else:
			return {'is_available': 0}
	except Exception:
		frappe.log_error(message=frappe.get_traceback(),title='Error in v2.checkout.check_pincode_availability')
		return {'is_available': 0}

@frappe.whitelist()
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
	return returnValue