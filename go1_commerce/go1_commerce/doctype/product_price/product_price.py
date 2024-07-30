# -*- coding: utf-8 -*-
# Copyright (c) 2022, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe,json
from frappe.model.document import Document
from frappe import _
from frappe.utils.data import getdate

class ProductPriceDuplicateProduct(frappe.ValidationError):
	pass

class ProductPrice(Document):
	def validate(self):
		self.validate_product()
		self.validate_dates()
		self.update_price_list_details()
		self.update_product_details()
		self.check_duplicates()
		if self.attribute_id:
			self.attribute_description = frappe.db.get_value("Product Variant Combination",
												{"attribute_id":self.attribute_id},"attribute_html")
	def validate_product(self):
		if not frappe.db.exists("Product", self.product):
			frappe.throw(_("Product {0} not found.").format(self.product))

	def validate_dates(self):
		if self.valid_from and self.valid_upto:
			if getdate(self.valid_from) > getdate(self.valid_upto):
				frappe.throw(_("Valid From Date must be lesser than Valid Upto Date."))

	def update_price_list_details(self):
		if self.price_list:
			price_list_details = frappe.db.get_value("Price List",
				{"name": self.price_list, "enabled": 1},
				["buying", "selling", "currency"])

			if not price_list_details:
				link = frappe.utils.get_link_to_form('Price List', self.price_list)
				frappe.throw("The price list {0} does not exist or is disabled".format(link))

			self.buying, self.selling, self.currency = price_list_details

	def update_product_details(self):
		if self.product:
			self.product_name = frappe.db.get_value("Product", self.product,["item"])

	def check_duplicates(self):
		conditions = '''where product = "{product}" and attribute_id="{attribute_id}" and price_list = "{price_list}" and name != "{name}"'''.format(product=self.product,attribute_id=self.attribute_id, price_list=self.price_list, name=self.name)

		for field in [
			"valid_from",
			"valid_upto",
			"customer"]:
			if self.get(field):
				conditions += " and {0} = '{1}' ".format(field, self.get(field))
			else:
				conditions += "and {0} = ''".format(field)
		query = """select price
				from `tabProduct Price`
				{conditions}""".format(conditions=conditions)
		frappe.log_error(query, "query")
		price = frappe.db.sql(query,as_dict=True)
		if price:
			frappe.throw(_("Product Price appears multiple times based on Price List, \
				  		Customer, Currency, Product, Qty, and Dates."), ProductPriceDuplicateProduct)

	def before_save(self):
		if self.selling:
			self.reference = self.customer
		if self.buying and not self.selling:
			self.customer = None



@frappe.whitelist()
def get_attributes_combination_html(attribute):
	return frappe.db.get_value("Product Variant Combination",{"attribute_id":attribute},
														"attribute_html")
@frappe.whitelist()
def get_attributes_combination(product):
	combination=frappe.db.get_all('Product Variant Combination',filters={'parent':product},
							   					fields=['*'])
	for item in combination:
		if item and item.get('attributes_json'):
			variant = json.loads(item.get('attributes_json'))
			attribute_html = ""
			for obj in variant:
				if attribute_html:
					attribute_html +=", "
				option_value, attribute = frappe.db.get_value("Product Attribute Option", obj, 
												  				["option_value","attribute"])
				
				attribute_name = frappe.db.get_value("Product Attribute", attribute, 
										 						"attribute_name")
				attribute_html += "<b>"+attribute_name+"</b>:"+option_value
				
			item["combination_txt"] = attribute_html

	productdoc=frappe.db.get_all('Product',fields=['*'],filters={'name':product})
	return combination,productdoc