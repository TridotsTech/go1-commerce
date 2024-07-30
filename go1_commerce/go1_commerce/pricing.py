# -*- coding: utf-8 -*-
# Copyright (c) 2019, Tridots and contributors
# For license information, please see license.txt
from __future__ import unicode_literals, print_function
import frappe, json, requests, os, re, time, socket, math
from frappe import _
from frappe.utils import cstr, flt, getdate, nowdate, now, today, encode, get_url, get_datetime, to_timedelta, add_days,get_files_path
from datetime import date, datetime, timedelta
from urllib.parse import urljoin, unquote, urlencode
from frappe.core.doctype.domain_settings.domain_settings import get_active_domains
from six import iteritems, text_type, string_types


@frappe.whitelist(allow_guest=True)
def get_product_pricing(product, attribute_id=None, customer=None, desired_qty=0,order_date=nowdate(), price_list=None, seller_classify=None, zipcode=None):
	
	if not price_list:
		price_list = get_default_price_list(customer, zipcode=None)
	'''Get product price based on price model when b2b domain enabled.'''
	product_info = frappe.get_doc("Product", product)
	price = product_info.price
	product_price = get_product_price(product=product, attribute_id=attribute_id, order_date= order_date, price_list=price_list)
	product_price_name=""
	if product_price:
		product_price = product_price[0]
		product_price_name = product_price.name
		if product_price.price_model=="Standard Pricing":
			price = product_price.price
		if product_price.price_model=="Package Pricing":
			price = check_packing_list(product_price.name, desired_qty, product)
		if product_price.price_model=="Graduated Pricing":
			price = graduated_pricing(product_price.name, desired_qty, product)
		if product_price.price_model=="Volume Pricing":
			price = volume_pricing(product_price.name, desired_qty, product)
		if product_price.price_model=="Volumetric Pricing":
			price = volumetric_ricing(product_price.name, desired_qty, product)
	
	return frappe._dict({"product":product, "price":price, "desired_qty":desired_qty, "product_price_name": product_price_name})

def get_vendor_pricing(product, attribute_id=None, price_name=None, center=None,min_price=None,max_price=None,seller_classify="All Stores"):
	price_condition = ""
	classify_cond = ""
	if min_price:
		price_condition = " AND price>="+min_price
	if max_price:
		price_condition = " AND price<="+max_price
	product_price  = frappe.db.sql('''select price_model,business,vendor_name,min(price) as product_price,old_price from `tabProduct Price` p inner join `tabPrice List Zone` Z ON p.price_list = Z.parent  where p.product="{product}"  and p.price>0 and Z.zone="{center}" {price_condition} GROUP BY business,vendor_name ORDER BY product_price'''.format(product=product, price_name=price_name, center=center,price_condition=price_condition), as_dict=True)
	if seller_classify!="All Stores":
		classify_cond = " AND B.business_classification='"+seller_classify+"'"
		product_price  = frappe.db.sql('''select price_model,business,vendor_name,min(price) as product_price,old_price from `tabProduct Price` p inner join `tabPrice List Zone` Z ON p.price_list = Z.parent inner join `tabBusiness` B ON B.name = p.business where p.product="{product}"  and p.price>0 and Z.zone="{center}" {price_condition} {classify_cond} GROUP BY business,vendor_name ORDER BY product_price'''.format(classify_cond=classify_cond,product=product, price_name=price_name, center=center,price_condition=price_condition), as_dict=True)
	 
	p_prices = []
	if product_price:
		for x in product_price:
			if x.price_model=="Package Pricing":
				x.product_price = check_packing_list(x.name, desired_qty, product)
			if x.price_model=="Graduated Pricing":
				x.product_price = graduated_pricing(x.name, desired_qty, product)
			if x.price_model=="Volume Pricing":
				x.product_price = volume_pricing(x.name, desired_qty, product)
			x.discount_percentage = 0
			if float(x.old_price) > 0 and float(x.product_price) < float(x.old_price):
				x.discount_percentage = int(round((x.old_price - x.product_price) / 
										x.old_price * 100, 0))
			x.stock = 0
			p_bin = frappe.db.sql(""" SELECT actual_qty FROM  `tabBin` B 
											 WHERE B.warehouse=%(warehouse)s AND B.product=%(product)s AND
											 B.business=%(business)s
											""",{"warehouse":center,"product":product,"business":x.business},as_dict=1)
			if p_bin:
				x.stock = p_bin[0].actual_qty
			variants = []
			is_allowed = 1
			if x.stock == 0:
				is_allowed = 0
			x.variants = variants
			if frappe.db.get_value("Product",product,"has_variants")==1:
				is_allowed = 1
				p_variants  = frappe.db.sql('''select attribute_id,price as product_price,old_price from `tabProduct Price` p inner join `tabPrice List Zone` Z ON p.price_list = Z.parent where p.product="{product}"  and p.price>0 and Z.zone="{center}" and p.business="{business}" {price_condition} AND attribute_id IS NOT NULL ORDER BY price'''.format(business=x.business,product=product, price_name=price_name, center=center,price_condition=price_condition), as_dict=True)
				is_price_update = 0
				x.default_variant = None
				for v in p_variants:
					v.discount_percentage = 0
					if float(v.old_price) > 0 and float(v.product_price) < float(v.old_price):
						v.discount_percentage = int(round((v.old_price - v.product_price) / 
												v.old_price * 100, 0))
					combinations = get_attributes_combination(v.attribute_id)
					v.variant_text = ""
					if combinations:
						v.variant_text = combinations[0].combination_txt
					attr_bin = frappe.db.sql(""" SELECT attribute_quantity FROM `tabBin Attribute Stock` BA
												 INNER JOIN `tabBin` B ON B.name = BA.parent 
												 WHERE warehouse=%(warehouse)s AND product=%(product)s AND
												 business=%(business)s AND BA.attribute_id=%(attribute_id)s
												""",{"attribute_id":v.attribute_id,"warehouse":center,"product":product,"business":x.business},as_dict=1)
					v.stock = 0
					if attr_bin:
						v.stock = attr_bin[0].attribute_quantity
					if v.stock>0 and frappe.db.get_value("Product Variant Combination",{"attribute_id":v.attribute_id,"disabled":0,"show_in_market_place":1}):
						if is_price_update==0:
							x.product_price = v.product_price
							x.old_price = v.old_price
							is_price_update = 1
							x.default_variant = v
						variants.append(v)
				x.variants = variants
			if is_allowed==1:
				p_prices.append(x) 
	return	p_prices

def get_product_vendor_pricing(product, attribute_id=None, price_name=None, center=None):
	product_price  = frappe.db.sql('''select * from `tabProduct Price` p inner join `tabPrice List Zone` Z ON p.price_list = Z.parent where p.product="{product}"  and p.price>0 and Z.zone="{center}"  ORDER BY price'''.format(product=product, price_name=price_name, center=center), as_dict=True)
	if product_price:
		for x in product_price:
			if x.price_model=="Standard Pricing":
				x.product_price = x.price
				x.old_price = x.old_price
			if x.price_model=="Package Pricing":
				x.product_price = check_packing_list(x.name, desired_qty, product)
			if x.price_model=="Graduated Pricing":
				x.product_price = graduated_pricing(x.name, desired_qty, product)
			if x.price_model=="Volume Pricing":
				x.product_price = volume_pricing(x.name, desired_qty, product)
			x.discount_percentage = 0
			if float(x.old_price) > 0 and float(x.product_price) < float(x.old_price):
				x.discount_percentage = int(round((x.old_price - x.product_price) / 
										x.old_price * 100, 0))
			x.stock = 0
			p_bin = frappe.db.sql(""" SELECT actual_qty FROM  `tabBin` B 
											 WHERE B.warehouse=%(warehouse)s AND B.product=%(product)s AND
											 B.business=%(business)s
											""",{"warehouse":center,"product":product,"business":x.business},as_dict=1)
			if p_bin:
				x.stock = p_bin[0].actual_qty
			variants = []
			p_variants  = frappe.db.sql('''select attribute_id,price as product_price,old_price from `tabProduct Price` p inner join `tabPrice List Zone` Z ON p.price_list = Z.parent where p.product="{product}"  and p.price>0 and Z.zone="{center}" and p.business="{business}" AND attribute_id IS NOT NULL ORDER BY price'''.format(business=x.business,product=product, price_name=price_name, center=center), as_dict=True)
			for v in p_variants:
				v.discount_percentage = 0
				if float(v.old_price) > 0 and float(v.product_price) < float(v.old_price):
					v.discount_percentage = int(round((v.old_price - v.product_price) / 
											v.old_price * 100, 0))
				combinations = get_attributes_combination(v.attribute_id)
				v.variant_text = ""
				if combinations:
					v.variant_text = combinations[0].combination_txt
				attr_bin = frappe.db.sql(""" SELECT attribute_quantity FROM `tabBin Attribute Stock` BA
											 INNER JOIN `tabBin` B ON B.name = BA.parent 
											 WHERE warehouse=%(warehouse)s AND product=%(product)s AND
											 business=%(business)s AND BA.attribute_id=%(attribute_id)s
											""",{"attribute_id":v.attribute_id,"warehouse":center,"product":product,"business":x.business},as_dict=1)
				v.stock = 0
				if attr_bin:
					v.stock = attr_bin[0].attribute_quantity
				if v.stock>0 and frappe.db.get_value("Product Variant Combination",{"attribute_id":v.attribute_id,"disabled":0,"show_in_market_place":1}):
					variants.append(v)
			x.variants = variants
	return	product_price

def graduated_pricing(price_list_rate_name, desired_qty, product, attribute_id=None):
	"""
		Check the graduated pricing based on  desired_qty.
		:param price_list_rate_name: Name of Product Price
		:param desired_qty: desired_qty
		:param product: str, Product Doctype field product
		:param attribute_id: if variant
	"""
	price = 0
	graduated_pricing = frappe.db.get_all("Product Graduated Pricing", fields=["*"], filters={"parent":price_list_rate_name},order_by="idx asc", limit_page_length=10)
	if len(graduated_pricing)>0:
		for r in graduated_pricing:
			exist = list(filter(lambda r: (r.get('first_unit') <= int(desired_qty) and float(r.get('last_unit')) >= int(desired_qty)), graduated_pricing))
			if float(r.get('last_unit')) < int(desired_qty):
				if r.get('per_unit'):
					price += r.get('per_unit') * int(desired_qty)
				if r.get('flat_rate'):
					price += r.get('flat_rate')/int(desired_qty)
			if r.get('first_unit') <= int(desired_qty) and float(r.get('last_unit')) >= int(desired_qty):
				if r.get('per_unit'):
					price += r.get('per_unit') * int(desired_qty)
				if r.get('flat_rate'):
					price += r.get('flat_rate')/int(desired_qty)
			
	return price

def volume_pricing(price_list_rate_name, desired_qty, product, attribute_id=None):
	"""
		Check the graduated pricing based on  qty.
		:param price_list_rate_name: Name of Product Price
		:param desired_qty: Qt
		:param product: str, Product Doctype field product
		:param attribute_id: if variant
	"""
	price = 0
	volume_pricing = frappe.db.get_all("Product Price Detail", fields=["*"], filters={"parent":price_list_rate_name},order_by="idx asc", limit_page_length=10)
	if len(volume_pricing)>0:
		for r in volume_pricing:
			if r.get('first_unit') <= int(desired_qty) and float(r.get('last_unit')) >= int(desired_qty):
				if r.get('per_unit'):
					price = r.get('per_unit') * int(desired_qty)
					break
				if r.get('flat_rate'):
					price = r.get('flat_rate')/int(desired_qty)
					break

	return price	

def check_packing_list(price_list_rate_name, desired_qty, product, attribute_id=None):
	"""
		Check if the desired qty is within the increment of the packing list.
		:param price_list_rate_name: Name of Product Price
		:param desired_qty: Desired Qt
		:param product: str, Product Doctype field product
		:param attribute_id: if variant
	"""
	flag = True
	price = 0
	package_pricing = frappe.db.get_all("Pricing Package Unit", fields=["*"], filters={"parent":price_list_rate_name},order_by="idx asc", limit_page_length=10)
	if len(package_pricing)>0:
		for r in package_pricing:
			if r.packing_unit:
				packing_increment = int(desired_qty) % int(r.packing_unit)
				if packing_increment == 0:
					price = r.price/r.packing_unit
					break
	return price

def apply_price_list_on_item(args):
	item_doc = frappe.db.get_value("Product", args.product, ['name'], as_dict=1)
	item_details = get_price_list_rate(args, item_doc)

	item_details.update(get_pricing_rule_for_item(args, item_details.price_list_rate))

	return item_details

def get_product_price(product,order_date,customer=None,attribute_id=None,price_list=None, ignore_party=True):
	"""
		Get name, price_list_rate from Product Price based on conditions
			Check if the desired qty is within the increment of the packing list.
		:param args: dict (or frappe._dict) with mandatory fields price_list, uom
			optional fields  customer
		:param product: str, Product Doctype field product
	"""
	args = {}
	args['product'] = product
	args['price_list'] = price_list
	

	conditions = """where product='{product}'
		and price_list='{price_list}' and price>0 """.format(product=product, price_list=price_list)

	if args.get('uom'):
		conditions += """and ifnull(uom, '') in ('')"""

	if not ignore_party:
		if args.get("customer"):
			conditions += " and customer=%(customer)s"
		else:
			conditions += "and (customer is null or customer = '')"
	if args.get('order_date'):
		conditions += """ and %(order_date)s between
			ifnull(valid_from, '2000-01-01') and ifnull(valid_upto, '2500-12-31')"""
	query = """ select * from `tabProduct Price` {conditions}
		order by price asc""".format(conditions=conditions)

	data = frappe.db.sql(query, args, as_dict=True)

	if not data:
		conditions = """where product='{product}'
		and price_list='{price_list}' and price>0 """.format(product=product, price_list="Standard Selling")

		if args.get('uom'):
			conditions += """and ifnull(uom, '') in ('')"""

		if not ignore_party:
			if args.get("customer"):
				conditions += " and customer=%(customer)s"
			else:
				conditions += "and (customer is null or customer = '')"

		if args.get('order_date'):
			conditions += """ and %(order_date)s between
				ifnull(valid_from, '2000-01-01') and ifnull(valid_upto, '2500-12-31')"""
		query = """ select * from `tabProduct Price` {conditions}
		order by price asc""".format(conditions=conditions)
		
		data = frappe.db.sql(query, args, as_dict=True)
		
	return data

def insert_product_price(product):
	"""Insert Product Price if Price List and Price List Rate are specified and currency is the same"""
	if frappe.has_permission("Product Price", "write"):
		item = frappe.get_doc("Product", product)
		args = frappe._dict({"product":item.name, "price_list":""})
		price_list_rate = args.price

		product_price = frappe.db.get_value('Product Price',
			{'product': args.product, 'price_list': args.price_list},
			['name', 'price_list_rate'], as_dict=1)
		if product_price and product_price.name:
			if product_price.price_list_rate != price_list_rate :
				frappe.db.set_value('Product Price', product_price.name, "price_list_rate", price_list_rate)
				frappe.msgprint(_("Product Price updated for {0} in Price List {1}").format(args.product,
					args.price_list), alert=True)
		else:
			product_price = frappe.get_doc({
				"doctype": "Product Price",
				"price_list": args.price_list,
				"product": args.product,
				"attribute_id": args.attribute_id,
				"price_list_rate": price_list_rate
			})
			product_price.insert()
			frappe.msgprint(_("Product Price added for {0} in Price List {1}").format(args.product,
				args.price_list), alert=True)

@frappe.whitelist(allow_guest=True)
def get_default_price_list(customer=None, zipcode=None, user=None):
	"""Return default price list for party (Document object)"""
	condition = ""																
	roles = []
	if not customer and frappe.session.user!="Administrator":
		from go1_commerce.utils.utils import get_customer_from_token
		customer = get_customer_from_token()
	rolelist = ""
	qry=""
	query = '''SELECT p.name FROM `tabPrice List` p WHERE p.selling=1 AND p.enabled=1 {condition} ORDER BY p.creation DESC'''.format(condition=condition)
	product_pricing = frappe.db.sql('''{query}'''.format(query=query),as_dict=1)
	if product_pricing:
		if customer: 
			customer_doc = frappe.get_doc("Customers", customer)
			cquery = '''select p.name from `tabPrice List` p inner join `tabPrice List Zone` z on z.parent = p.name where z.zone="{center}"'''.format(center=customer_doc.center)
			price_list = frappe.db.sql(cquery, as_dict=True)
			
			if len(price_list)>0:
				return price_list[0].name
			else:
				return "Standard Selling"
		else:
			return product_pricing[0].name
	else:
		query = '''SELECT name FROM `tabPrice List` WHERE selling=1 AND enabled=1 ORDER BY creation DESC'''
		product_pricing = frappe.db.sql('''{query}'''.format(query=query),as_dict=1)
		if product_pricing:
			return product_pricing[0].name
		else:
			return "Standard Selling"

@frappe.whitelist(allow_guest=True)
def get_customer_product_pricing(product, attribute=None, customer=None):
    condition = ""
    
    if attribute:
        condition = " AND PP.attribute_id='{attribute}'".format(attribute=attribute)

    query = "SELECT DISTINCT PP.product, PP.price_list, PP.name as product_price,\
            PP.price, PP.old_price FROM `tabProduct Price` PP\
            INNER JOIN `tabPrice List Zone` Z ON PP.price_list = Z.parent\
            WHERE PP.price>0 {condition}".format(product=product, condition=condition)

    result = frappe.db.sql(query, as_dict=True)
    return result
def get_attributes_combination(attribute):
	try:
		combination=frappe.db.get_all('Product Variant Combination',filters={'attribute_id':attribute},fields=['*'])
		for item in combination:
			varienthtml =""
			if item and item.get('attributes_json'):
				variant = json.loads(item.get('attributes_json'))
				attribute_html = ""
				for obj in variant:
					if obj:
						if attribute_html:
							attribute_html +=", "
						if frappe.db.get_all("Product Attribute Option",filters={"name":obj}):
							option_value, attribute = frappe.db.get_value("Product Attribute Option", obj, ["option_value","attribute"])
							attribute_name = frappe.db.get_value("Product Attribute", attribute, "attribute_name")
							attribute_html += attribute_name+" : "+option_value
				item["combination_txt"] = attribute_html
		return combination
	except Exception:
		frappe.log_error(title=f' Error in v2.product.get_attributes_combination',
		message=frappe.get_traceback())
