# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals


import frappe
import unittest
import frappe.utils
import frappe, json

test_dependencies = ["Product", "Product Category", "Business"]
test_records = frappe.get_test_records('Discounts')

class TestDiscounts(unittest.TestCase):
	def test_discount_creation(self):
		business1 = frappe.get_value("Business", {"restaurant_name": "Test Business 1", "contact_email":"test_business_1@test.com"}, "name")
		business2 = frappe.get_value("Business", {"restaurant_name": "Test Business 2", "contact_email":"test_business_2@test.com"}, "name")
		cat1 = frappe.db.get_value("Product Category",{"category_name":"Test Product Category 1", "business":business1}, "name")
		prd1 = frappe.db.get_value("Product",{"item":"Test Product 1", "restaurant":business1}, "name")
		print("------------busi")
		print(prd1)
		discounts1 = make_discounts(discount_name="Test Discounts 1", discount_type="Assigned to Products", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement=None, price_or_product="Price", same_item=0)
		discounts2 = make_discounts(discount_name="Test Discounts 2", discount_type="Assigned to Categories", percent_or_amount="Discount Percentage", business=business2, item=cat1, requirement=None, price_or_product=None, same_item=0)
		discounts3 = make_discounts(discount_name="Test Discounts 3", discount_type="Assigned to Sub Total", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement=None, price_or_product=None, same_item=0, coupon_code=0)
		discounts4 = make_discounts(discount_name="Test Discounts 4", discount_type="Assigned to Business", percent_or_amount="Discount Percentage", business=business2, item=business2, requirement=None, price_or_product=None, same_item=0)
		discounts5 = make_discounts(discount_name="Test Discounts 5", discount_type="Assigned to Products", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement="Specific Shipping Method", price_or_product="Price", same_item=0)
		discounts6 = make_discounts(discount_name="Test Discounts 6", discount_type="Assigned to Products", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement="Specific Payment Method", price_or_product="Price", same_item=0)
		discounts7 = make_discounts(discount_name="Test Discounts 7", discount_type="Assigned to Categories", percent_or_amount="Discount Percentage", business=business1, item=cat1, requirement="Specific Shipping Method", price_or_product=None, same_item=0)
		discounts8 = make_discounts(discount_name="Test Discounts 8", discount_type="Assigned to Categories", percent_or_amount="Discount Percentage", business=business1, item=cat1, requirement="Specific Payment Method", price_or_product=None, same_item=0)
		discounts9 = make_discounts(discount_name="Test Discounts 9", discount_type="Assigned to Business", percent_or_amount="Discount Percentage", business=business1, item=business1, requirement="Specific Shipping Method", price_or_product=None, same_item=0)
		discounts10 = make_discounts(discount_name="Test Discounts 10", discount_type="Assigned to Business", percent_or_amount="Discount Percentage", business=business1, item=business1, requirement="Specific Payment Method", price_or_product=None, same_item=0)
		discounts11 = make_discounts(discount_name="Test Discounts 11", discount_type="Assigned to Sub Total", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement="Specific price range", price_or_product=None, same_item=0, coupon_code=1)
		discounts12 = make_discounts(discount_name="Test Discounts 12", discount_type="Assigned to Sub Total", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement="Has any one product in cart", price_or_product=None, same_item=0, coupon_code=0)
		discounts13 = make_discounts(discount_name="Test Discounts 13", discount_type="Assigned to Sub Total", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement="Has all these products in cart", price_or_product=None, same_item=0, coupon_code=0)
		discounts14 = make_discounts(discount_name="Test Discounts 14", discount_type="Assigned to Sub Total", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement="Specific Shipping Method", price_or_product=None, same_item=0, coupon_code=0)
		discounts15 = make_discounts(discount_name="Test Discounts 15", discount_type="Assigned to Sub Total", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement="Specific Payment Method", price_or_product=None, same_item=0, coupon_code=0)
		discounts16 = make_discounts(discount_name="Test Discounts 16", discount_type="Assigned to Sub Total", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement="Limit to business", price_or_product=None, same_item=0, coupon_code=0)
		discounts17 = make_discounts(discount_name="Test Discounts 17", discount_type="Assigned to Delivery Charges", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement=None, price_or_product=None, same_item=0)
		discounts18 = make_discounts(discount_name="Test Discounts 18", discount_type="Assigned to Delivery Charges", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement="Specific Shipping Method", price_or_product=None, same_item=0)
		discounts19 = make_discounts(discount_name="Test Discounts 19", discount_type="Assigned to Delivery Charges", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement="Specific Payment Method", price_or_product=None, same_item=0)
		discounts20 = make_discounts(discount_name="Test Discounts 20", discount_type="Assigned to Products", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement="Specific Shipping Method", price_or_product="Product", same_item=1)
		discounts21 = make_discounts(discount_name="Test Discounts 21", discount_type="Assigned to Products", percent_or_amount="Discount Percentage", business=business1, item=prd1, requirement="Specific Payment Method", price_or_product="Product", same_item=0)
		discounts22 = make_discounts(discount_name="Test Discounts 22", discount_type="Assigned to Products", percent_or_amount="Discount Amount", business=business1, item=prd1, requirement=None, price_or_product="Price", same_item=0)
		# discounts23 = make_discounts(discount_name="Test Discounts 23", discount_type="Assigned to Business", percent_or_amount="Discount Amount", business=business1, item=business1, requirement="Specific Shipping Method", price_or_product=None, same_item=0)
		# discounts24 = make_discounts(discount_name="Test Discounts 24", discount_type="Assigned to Sub Total", percent_or_amount="Discount Amount", business=business1, item=prd1, requirement="Specific price range", price_or_product=None, same_item=0, coupon_code=0)
		# discounts25 = make_discounts(discount_name="Test Discounts 25", discount_type="Assigned to Sub Total", percent_or_amount="Discount Amount", business=business1, item=prd1, requirement="Specific price range", price_or_product=None, same_item=0, coupon_code=1)
		discount_doc = frappe.get_doc("Discounts", discounts1).reload()
		discount_doc1 = frappe.get_doc("Discounts", discounts2).reload()
		discount_doc2 = frappe.get_doc("Discounts", discounts3).reload()
		discount_doc3 = frappe.get_doc("Discounts", discounts4).reload()
		discount_doc4 = frappe.get_doc("Discounts", discounts5).reload()
		discount_doc5 = frappe.get_doc("Discounts", discounts6).reload()
		discount_doc6 = frappe.get_doc("Discounts", discounts7).reload()
		discount_doc7 = frappe.get_doc("Discounts", discounts8).reload()
		

def make_discounts(discount_name, discount_type, percent_or_amount, business=None, item=None, requirement=None, price_or_product=None, same_item=None, coupon_code=None):
	if not frappe.db.get_value("Discounts", { "name1": discount_name, "business":business}):
		discount = frappe.get_doc({
			"doctype": "Discounts",
			"name1": discount_name,
			"discount_type":discount_type,
			"business": business,
			"percent_or_amount": percent_or_amount,
			"discount_percentage": 10,
			"business_name":""
		}).insert()
		if discount.discount_type == "Assigned to Products":
			discount.price_or_product_discount = price_or_product
			if price_or_product == "Product":
				if same_item == 0:
					discount.same_product = 0
					discount.free_product = item
					discount.free_qty = 1
				else:
					discount.same_product = 1
					discount.free_qty = 1
			item_list = []
			item_list1 = []
			if requirement == "Specific Shipping Method":
				method_name = frappe.db.get_value("Shipping Method",{"shipping_method_name":"Test Shipping Method 1", "business":business}, "name")
				item_list.append({'item':method_name, 'item_name':"Test Shipping Method 1", 'idx':1})
				discount.append("discount_requirements",{"discount_requirement":requirement, "items_list":json.dumps(item_list)})
				discount.save()
			if requirement == "Specific Payment Method":
				method_name = frappe.db.get_value("Payment Method",{"payment_method":"Test Payment Method 1", "business":business}, "name")
				item_list1.append({'item':method_name, 'item_name':"Test Payment Method 1", 'idx':1})
				discount.append("discount_requirements",{"discount_requirement":requirement, "items_list":json.dumps(item_list1)})
				discount.save()
			if item:
				discount.append("discount_products",{"items":item, "item_name":""})
				discount.save()
		if discount.discount_type == "Assigned to Categories":
			item_list = []
			item_list1 = []
			if requirement == "Specific Shipping Method":
				method_name = frappe.db.get_value("Shipping Method",{"shipping_method_name":"Test Shipping Method 1", "business":business}, "name")
				item_list.append({'item':method_name, 'item_name':"Test Shipping Method 1", 'idx':1})
				discount.append("discount_requirements",{"discount_requirement":requirement, "items_list":json.dumps(item_list)})
				discount.save()
			if requirement == "Specific Payment Method":
				method_name = frappe.db.get_value("Payment Method",{"payment_method":"Test Payment Method 1", "business":business}, "name")
				item_list1.append({'item':method_name, 'item_name':"Test Payment Method 1", 'idx':1})
				discount.append("discount_requirements",{"discount_requirement":requirement, "items_list":json.dumps(item_list1)})
				discount.save()
			if item:
				discount.append("discount_categories",{"category":item, "category_name":""})
				discount.save()
		if discount.discount_type == "Assigned to Sub Total":
			if coupon_code == 1:
				discount.requires_coupon_code = 1
				discount.coupon_code = "Test Coupon 1"
			discount.append("discount_requirements",{"discount_requirement":"Spend x amount", "amount_to_be_spent":1000})
			discount.save()
			item_list1 = []
			item_list2 = []
			item_list3 = []
			item_list4 = []
			item_list5 = []
			if requirement == "Specific price range":
				discount.append("discount_requirements",{"discount_requirement":requirement, "min_amount":1000, "max_amount":2000})
				discount.save()
			if requirement == "Has any one product in cart":
				prd1 = frappe.db.get_value("Product",{"item":"Test Product 1", "restaurant":business}, "name")
				item_list1.append({'item':prd1, 'item_name':"Test Product 1", 'idx':1})
				discount.append("discount_requirements",{"discount_requirement":requirement, "items_list":json.dumps(item_list1)})
				discount.save()
			if requirement == "Has all these products in cart":
				prd1 = frappe.db.get_value("Product",{"item":"Test Product 1", "restaurant":business}, "name")
				item_list2.append({'item':prd1, 'item_name':"Test Product 1", 'idx':1})
				discount.append("discount_requirements",{"discount_requirement":requirement, "items_list":json.dumps(item_list2)})
				discount.save()
			if requirement == "Limit to business":
				business1 = frappe.get_value("Business", {"restaurant_name": "Test Business 1", "contact_email":"test_business_1@test.com"}, "name")
				item_list5.append({'item':business1, 'item_name':"Test Business 1", 'idx':1})
				discount.append("discount_requirements",{"discount_requirement":requirement, "items_list":json.dumps(item_list5)})
				discount.save()
			if requirement == "Specific Shipping Method":
				method_name = frappe.db.get_value("Shipping Method",{"shipping_method_name":"Test Shipping Method 1", "business":business}, "name")
				item_list3.append({'item':method_name, 'item_name':"Test Shipping Method 1", 'idx':1})
				discount.append("discount_requirements",{"discount_requirement":requirement, "items_list":json.dumps(item_list3)})
				discount.save()
			if requirement == "Specific Payment Method":
				method_name = frappe.db.get_value("Payment Method",{"payment_method":"Test Payment Method 1", "business":business}, "name")
				item_list4.append({'item':method_name, 'item_name':"Test Payment Method 1", 'idx':1})
				discount.append("discount_requirements",{"discount_requirement":requirement, "items_list":json.dumps(item_list4)})
				discount.save()
		if discount.discount_type == "Assigned to Business":
			item_list = []
			item_list1 = []
			if requirement == "Specific Shipping Method":
				method_name = frappe.db.get_value("Shipping Method",{"shipping_method_name":"Test Shipping Method 1", "business":business}, "name")
				item_list.append({'item':method_name, 'item_name':"Test Shipping Method 1", 'idx':1})
				discount.append("discount_requirements",{"discount_requirement":requirement, "items_list":json.dumps(item_list)})
				discount.save()
			if requirement == "Specific Payment Method":
				method_name = frappe.db.get_value("Payment Method",{"payment_method":"Test Payment Method 1", "business":business}, "name")
				item_list1.append({'item':method_name, 'item_name':"Test Payment Method 1", 'idx':1})
				discount.append("discount_requirements",{"discount_requirement":requirement, "items_list":json.dumps(item_list1)})
				discount.save()
			if item:
				discount.append("discount_business",{"business":item, "business_name":""})
				discount.save()
		if discount.discount_type == "Assigned to Delivery Charges":
			item_list = []
			item_list1 = []
			discount.discount_percentage = 100
			if requirement == "Specific Shipping Method":
				method_name = frappe.db.get_value("Shipping Method",{"shipping_method_name":"Test Shipping Method 1", "business":business}, "name")
				item_list.append({'item':method_name, 'item_name':"Test Shipping Method 1", 'idx':1})
				discount.append("discount_requirements",{"discount_requirement":requirement, "items_list":json.dumps(item_list)})
				discount.save()
			if requirement == "Specific Payment Method":
				method_name = frappe.db.get_value("Payment Method",{"payment_method":"Test Payment Method 1", "business":business}, "name")
				item_list1.append({'item':method_name, 'item_name':"Test Payment Method 1", 'idx':1})
				discount.append("discount_requirements",{"discount_requirement":requirement, "items_list":json.dumps(item_list1)})
				discount.save()
		return discount.name
	else:
		return frappe.get_value("Discounts", { "name1": discount_name, "business":business}, "name")
