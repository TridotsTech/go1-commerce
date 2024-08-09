# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator
from frappe.model.naming import make_autoname
from go1_commerce.utils.setup import get_settings_value

class ProductBrand(WebsiteGenerator):
	def autoname(self):
		naming_series = 'PB-'
		self.name = make_autoname(naming_series + '.#####', doc=self)

	def validate(self):	
		self.make_route()

	def make_route(self):		
		self.route="brand/"+frappe.scrub(self.brand_name)
		cat = frappe.scrub(self.brand_name)
		if self.category:
			cat = cat+"_"+frappe.scrub(self.category_name)
		self.unique_name = cat

	def get_context(self, context):
		context.brand_name=self
		min_price=frappe.form_dict.min
		max_price=frappe.form_dict.max
		sort=frappe.form_dict.sort
		rating=frappe.form_dict.rating
		context.minPrice=min_price
		context.maxPrice=max_price
		context.sort=sort
		context.rating=rating
		attr=[]
		default_product_sort_order = get_settings_value('Catalog Settings', 'default_product_sort_order')
		from go1_commerce.go1_commerce.api\
			import get_brand_based_products
		if not sort:
			context.sort=get_sorted_columns(default_product_sort_order)
		for x in frappe.form_dict:
			if x!='sort' and x!='min' and x!='max' and x!='rating':
				attr.append({'attribute':x,'value':frappe.form_dict[x]})				
		if attr:
			context.attribute=attr
		context.products=get_brand_based_products(self.name, sort_by=sort, rating=rating, 
											min_price=min_price,max_price=max_price, attributes=attr) 


def permissions(user):
	if not user: user=frappe.session.user
	if "System Manager" in frappe.get_roles(user):
		return None



def get_sorted_columns(sort_by):
	try:
		switcher = {
			"Relevance": "relevance",
			"Name: A to Z": "name_asc",
			"Name: Z to A": "name_desc",
			"Price: Low to High": "price_asc",
			"Price: High to Low": "price_desc",
			"Newest Arrivals": "creation desc",
			"Date: Oldest first": "creation asc"
		}
		return switcher.get(sort_by, "Invalid value")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.product_brand.get_sorted_columns") 
	