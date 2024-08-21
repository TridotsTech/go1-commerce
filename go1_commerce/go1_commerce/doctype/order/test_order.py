# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals


import frappe
import unittest
import frappe.utils
from frappe.utils import flt
import frappe, json
from frappe.test_runner import make_test_records_for_doctype
from datetime import date, datetime, timedelta
from go1_commerce.go1_commerce.doctype.product.test_product import make_products

test_dependencies = ["Product"]
test_records = frappe.get_test_records('Order')

class TestOrder(unittest.TestCase):
	def setUp(self):
		make_test_records_for_doctype("Product", force=True)

	def test_order_creation(self):
		make_products()
		business1 = frappe.get_value("Business", {"restaurant_name": "Test Business 1", "contact_email":"test_business_1@test.com"}, "name")
		business2 = frappe.get_value("Business", {"restaurant_name": "Test Business 2", "contact_email":"test_business_2@test.com"}, "name")
		customer1 = frappe.get_value("Customers", {"email": "testcustomer1@gmail.com", "first_name":"Test Customer 1"}, "name")
		customer2 = frappe.get_value("Customers", {"email": "testcustomer2@gmail.com", "first_name":"Test Customer 2"}, "name")
		prd1 = frappe.get_value("Product",{"item":"Test Product 1"}, "name")
		prd2 = frappe.get_value("Product",{"item":"Test Product 2"}, "name")
		order1 = make_order( product=prd1, customer=customer1, shipping_charge=0, tax=0, attr=0, status="Placed", shipping_status="Pending", payment_status="Pending", subtotal_discount=0, delivery_discount=0)
		order2 = make_order( product=prd1, customer=customer1, shipping_charge=1, tax=0, attr=0, status="Placed", shipping_status="Pending", payment_status="Pending", subtotal_discount=0, delivery_discount=0)
		order3 = make_order( product=prd1, customer=customer1, shipping_charge=1, tax=1, attr=0, status="Placed", shipping_status="Pending", payment_status="Pending", subtotal_discount=0, delivery_discount=0)
		order4 = make_order( product=prd2, customer=customer2, shipping_charge=0, tax=1, attr=0, status="Placed", shipping_status="Pending", payment_status="Pending", subtotal_discount=0, delivery_discount=0)
		order5 = make_order( product=prd1, customer=customer1, shipping_charge=0, tax=0, attr=0, status="Placed", shipping_status="Pending", payment_status="Pending", subtotal_discount=0, delivery_discount=0)
		order6 = make_order( product=prd2, customer=customer1, shipping_charge=0, tax=0, attr=1, status="Placed", shipping_status="Pending", payment_status="Pending", subtotal_discount=0, delivery_discount=0)
		order7 = make_order( product=prd2, customer=customer1, shipping_charge=0, tax=0, attr=0, status="Packed", shipping_status="Packed", payment_status="Pending", subtotal_discount=0, delivery_discount=0)
		order8 = make_order( product=prd2, customer=customer1, shipping_charge=0, tax=0, attr=0, status="Shipped", shipping_status="Shipped", payment_status="Pending", subtotal_discount=0, delivery_discount=0)
		order9 = make_order( product=prd2, customer=customer1, shipping_charge=0, tax=0, attr=0, status="Delivered", shipping_status="Delivered", payment_status="Pending", subtotal_discount=0, delivery_discount=0)
		order10 = make_order( product=prd2, customer=customer1, shipping_charge=0, tax=0, attr=0, status="Completed", shipping_status="Delivered", payment_status="Paid", subtotal_discount=0, delivery_discount=0)
		order11 = make_order( product=prd2, customer=customer1, shipping_charge=0, tax=0, attr=0, status="Placed", shipping_status="Pending", payment_status="Pending", subtotal_discount=1, delivery_discount=0)
		order12 = make_order( product=prd1, customer=customer1, shipping_charge=1, tax=1, attr=0, status="Placed", shipping_status="Pending", payment_status="Pending", subtotal_discount=1, delivery_discount=0)
		order13 = make_order( product=prd1, customer=customer1, shipping_charge=1, tax=0, attr=0, status="Placed", shipping_status="Pending", payment_status="Pending", subtotal_discount=1, delivery_discount=0)
		order14 = make_order( product=prd1, customer=customer1, shipping_charge=0, tax=1, attr=0, status="Placed", shipping_status="Pending", payment_status="Pending", subtotal_discount=1, delivery_discount=0)
		order_doc = frappe.get_doc("Order", order1).reload()
		order_doc1 = frappe.get_doc("Order", order2).reload()

def make_order( product, customer, shipping_charge, tax, attr, status, shipping_status, payment_status, subtotal_discount, delivery_discount):
	from go1_commerce.go1_commerce.v2.cart import validate_attributes_stock
	from go1_commerce.go1_commerce.api import get_order_discount, calculate_vendor_based_shipping_charges
	from go1_commerce.go1_commerce.doctype.discounts.discounts import get_product_discount
	from go1_commerce.accounts.api import make_payment
	customer_info = frappe.get_doc('Customers', customer)
	method_name = frappe.db.get_value("Shipping Method", "name")
	payment_name = frappe.db.get_value("Payment Method", "name")
	shipping_method_name = frappe.db.get_value("Shipping Method", "shipping_method_name")
	payment_method_name = frappe.db.get_value("Payment Method", "payment_method")
	item_info = frappe.get_doc("Product", product)
	price = item_info.price
	attribute_description = ""
	attribute_ids = ""
	if item_info.inventory_method == "Track Inventory":
		attribute1 = frappe.db.get_value("Product Attribute Mapping",{"parent":item_info.name}, "name")
		attribute_name = frappe.db.get_value("Product Attribute Mapping",{"parent":item_info.name}, "attribute")
		if attribute1:
			attribute_option = frappe.db.get_value("Product Attribute Option",{"attribute_id":attribute1}, "name")
			option_value = frappe.db.get_value("Product Attribute Option",{"attribute_id":attribute1}, "option_value")
			attr_html = "<div class='cart-attributes'><span class='attr-title'>"+attribute_name+" </span> : <span>"+option_value+"</span></div>"
			attribute_description = attr_html
			attribute_ids = attribute_option
			price = validate_attributes_stock(item_info.name, attribute_option, attr_html, 1, "true", 1)
			if price['status'] == "True":
				price = price['price']
	
	cart1 = frappe.get_doc({
		"doctype": 'Shopping Cart',
		"customer": customer,
		"cart_type": "Shopping Cart"
		})
	cart1.append('items', {
		'product': item_info.name,
		'quantity': 1,
		'price': price,
		'attribute_description': attribute_description,
		'attribute_ids': attribute_ids,
		'special_instruction': '',
		'creation': datetime.now(),
		'__islocal': 1
	})
	cart1.insert()
	tax1 = ''
	if tax == 1:
		tax1 = calculate_item_tax(cart1)
	order = frappe.get_doc({
		"doctype": "Order",
		"customer": customer,
		"customer_name": customer_info.first_name,
		"customer_email": customer_info.email,
		"phone":customer_info.phone,
		"status": status,
		"payment_status": payment_status,
		"first_name": customer_info.first_name,
		"shipping_first_name": customer_info.first_name,
		"address": "Lake View extate",
		"city":"Chennai",
		"state": "Tamil Nadu",
		"country": "India",
		"zipcode": "600022",
		"shipping_shipping_address": "Lake View extate",
		"shipping_city":"Chennai",
		"shipping_state": "Tamil Nadu",
		"shipping_country": "India",
		"shipping_zipcode": "600022",
		"shipping_phone": customer_info.phone,
		"shipping_method": method_name,
		"shipping_method_name": shipping_method_name,
		"payment_method": payment_name,
		"payment_method_name": payment_method_name
	})
	discount = 0
	cart = frappe.db.get_all('Shopping Cart', filters={'customer': customer, 'cart_type': 'Shopping Cart'}, fields=['name', 'tax', 'tax_breakup', 'business'])
	if subtotal_discount==1:
		discount_amt = get_order_discount(price, customer, 0, method_name, payment_name)
		if discount_amt:
			discount = discount_amt['discount_amount']
	order.discount = discount
	tax_amt = 0
	if cart and cart[0].tax:
		tax_amt = cart[0].tax
		tax_breakup = get_product_tax(cart1, price)
		if tax_breakup:
			order.tax_json = json.dumps(tax_breakup['tax_json'])
			order.tax_breakup = tax_breakup['tax_breakup']
	order.total_tax_amount = cart[0].tax
	if shipping_charge == 1 or delivery_discount == 1:
		customer_addr = frappe.db.get_all('Customer Address', filters={'parent': customer}, fields=['name'])
		if customer_addr and customer_addr[0] and method_name:
			shipping_charge = calculate_vendor_based_shipping_charges(method_name, customer_addr[0].name, price, None, cart[0].name)
			if shipping_charge:
				order.shipping_charges = shipping_charge['shipping_charges']
	order.append("order_item", { "item": item_info.name, "item_name":item_info.item, "price": price, "attribute_description":attribute_description, "attribute_ids":attribute_ids, "quantity": 1, "shipping_status":shipping_status, "amount": price, "tax":tax_amt})
	order.insert()
	if payment_status == "Paid":
		make_payment(source_name=None, target_doc=None, order=order.name, mode_of_payment="Cash", amount=order.total_amount)
	order.reload()
	order.submit()
	return order.name

def calculate_item_tax( item):
		tax_info = None
		tax = ''
		tax_breakup = ''
		item = frappe.db.get_all('Cart Items',filters={'parent':item.name},fields=['*'])[0]
		from go1_commerce.utils.setup import get_settings_from_domain
		tax_info = frappe.db.get_value('Product', item.product, 'tax_category')
		if tax_info:
			catalog_settings = get_settings_from_domain('Catalog Settings')
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
				tax = item_tax
				tax_breakup = item_breakup
				cart1 = frappe.get_doc('Cart Items', item.name)
				cart1.tax = tax
				cart1.tax_breakup = tax_breakup
				cart1.save()
		return {'tax':tax, 'tax_breakup':tax_breakup}

def get_product_tax(item, total):
	tax_template = None
	tax_splitup = []
	item_tax = 0
	from go1_commerce.utils.setup import get_settings_from_domain
	cart = frappe.db.get_all('Cart Items',filters={'parent':item.name},fields=['*'])[0]
	product_tax = frappe.db.get_value('Product', cart.product, 'tax_category')
	if product_tax:
		tax_template = frappe.get_doc('Product Tax Template', product_tax)
	catalog_settings = get_settings_from_domain('Catalog Settings')
	if tax_template:
		if tax_template.tax_rates:
			tax_type = ''
			for tax in tax_template.tax_rates:
				if catalog_settings.included_tax:
					tax_type = 'Incl. Tax'
					tax_value = flt(total) * tax.rate / (100 + tax.rate)
				else:
					tax_type = 'Excl. Tax'
					tax_value = total * tax.rate / 100
				item_tax = item_tax + tax_value
				cur_tax = next((x for x in tax_splitup if (x['type'] == tax.tax and x['rate'] == tax.rate)), None)
				if cur_tax:
					for it in tax_splitup:
						if it['type'] == tax.tax:
							it['amount'] = it['amount'] + tax_value
				else:
					tax_splitup.append({'type': tax.tax,'rate': tax.rate, 'amount': tax_value, 'account': tax.get('account_head'), 'tax_type': tax_type })
	tax_json = []
	if tax_splitup:
		tax_breakup = ''
		for s in tax_splitup:
			tax_json.append(s)
			tax_breakup += str(s['type']) + ' - ' + str('{0:.2f}'.format(round(s['rate'], 2))) + '% - ' + str('{0:.2f}'.format(round(s['amount'], 2))) + ' - ' + tax_type + '\n'
	return {'tax_json': tax_json, 'tax_breakup':tax_breakup}