# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, os, re, json
from frappe.website.website_generator import WebsiteGenerator
from frappe.utils import touch_file, encode
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, getdate, nowdate, get_url, add_days
from datetime import datetime
from pytz import timezone
from frappe.utils import get_files_path
import pytz
from urllib.parse import unquote
from six import string_types
from go1_commerce.utils.setup import get_settings, get_settings_value
from frappe.desk.reportview import get_match_cond, get_filters_cond
from frappe.query_builder import DocType, Field, functions as fn, Order
from frappe.query_builder.functions import Function

class Product(WebsiteGenerator):
	website = frappe._dict(
							condition_field = "show_in_website",
							no_cache = 1
						)

	def on_trash(self):
		delete_whoose_data(self)


	def autoname(self): 
		naming_series = "ITEM-"
		from frappe.model.naming import make_autoname
		self.name = make_autoname(naming_series + '.#####', doc = self)


	def validate(self):
		self.make_route()
		self.insert_search_words()
		self.validate_order_qty()
		self.item = self.item.lstrip()
		if not self.barcode:
			self.check_barcode()
		if self.old_price and self.old_price > 0 and self.price:
			if self.old_price < self.price:
				frappe.throw(_('Old Price must be greater than the Product Price'))
		if self.status != 'Approved':
			self.status = 'Approved'
		check_attr_combination_price(self)
		self.validate_attribute_options()
		if not self.meta_title:
			self.meta_title = self.item
		if not self.meta_keywords:
			self.meta_keywords = self.item.replace(" ", ", ")
		if not self.meta_description:
			self.meta_description = "About: {0}".format(self.item)
		if self.get("sku"):
			check_other = frappe.db.get_all("Product",
											filters = {
														"sku":self.get("sku"),
														"name":("!=",self.get("name")),
														"status":"Approved"
													})
			if check_other:
				frappe.msgprint("SKU already exist in the system.")
		if self.brand:
			check_brands = frappe.db.get_all("Product Brand Mapping",filters = {"parent":self.name})
			if check_brands:
				for x in self.product_brands:
					x.brand = self.brand
					x.brand_name = self.brand_name
					x.unique_name = self.brand_unique_name
			else:
				self.append("product_brands",{"brand":self.brand,"brand_name":self.brand_name,
														"unique_name":self.brand_unique_name})
		if not self.sku and self.has_variants == 0:
			self.sku = self.name.split('ITEM-')[1] + "000"
		self.set_default_image()

	def set_default_image(self):
		if self.product_images:
			cover_image=next((x for x in self.product_images if x.is_primary==1),None)
			if not cover_image:
				self.product_images[0].is_primary=1
			if self.image:
				check_image = next((x for x in self.product_images if x.list_image == self.image), None)
				if not check_image:
					self.image = None
			if not self.image:
				if cover_image:
					self.image=cover_image.list_image
					self.list_images = self.product_images[0].image_name
				else:
					self.image=self.product_images[0].list_image
			
			else:
				if self.image.startswith("/files"):
					file_name = self.image.split("/files/")[-1]
					if not os.path.exists(get_files_path(frappe.as_unicode(file_name.lstrip("/")))):
						self.image=""


	def insert_search_words(self):
		try:
			words = ''
			data = ''
			catalog_settings = get_settings('Catalog Settings')
			if catalog_settings.search_fields:
				count = 1
				for s in catalog_settings.search_fields:
					lenght = len(catalog_settings.search_fields)
					if (len(catalog_settings.search_fields) == 1):
						data += s.fieldname
					else:
						if(count != lenght):
							data += s.fieldname+','
						else:
							data += s.fieldname
					count=count+1
				Product = DocType('Product')
				result_query = (
					frappe.qb.from_(Product)
					.select(*data.split(','))  
					.where(Product.name == self.name)
				)
				products = result_query.run(as_dict=True)
				if products:
					for item in products:
						for key, value in item.items():
							if value:
								words +=value
			else:
				if self.item:
					words += str(self.item)
			if catalog_settings.disable_search_keyword == 0:
				if self.search_keyword:
					for item in self.search_keyword:
						words += item.search_keywords
			p = re.compile(r'<.*?>')
			words = p.sub('', words)
			search_words = words.translate ({ord(c): " " for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+"})
			if search_words:
				self.search_words = search_words
		except Exception:
			frappe.log_error(frappe.get_traceback(), 
					"Error in product.insert_search_words")

	def check_barcode(self):
		try:
			catalog_settings = get_settings('Catalog Settings')
			if catalog_settings:
				if catalog_settings.generate_barcode_for_product:
					import barcode 
					from barcode.writer import ImageWriter
					EAN = barcode.get_barcode_class('code128')
					ean = EAN(self.name, writer=ImageWriter())
					fullname = ean.save(self.name)
					filename = randomStringDigits(18)
					path = 'public/files/{filename}.png'.format(filename=filename)
					touch_file(os.path.join(frappe.get_site_path(),path))
					f = open(os.path.join(frappe.get_site_path(),path), 'wb')
					ean.write(f)
					self.barcode = "/files/" + filename + ".png"
		except Exception:
			frappe.log_error(frappe.get_traceback(), 
					"Error in product.check_barcode")

	def validate_stock(self):
		if self.stock:
			if self.stock < 0:
				frappe.throw(_('Stock cannot be negative value'))
	

	def validate_order_qty(self):
		if self.minimum_order_qty and self.maximum_order_qty:
			if not int(self.minimum_order_qty)>0:
				frappe.throw(_("Minimum order quantity should be greater than zero"))
			if not int(self.maximum_order_qty) >= int(self.minimum_order_qty):
				frappe.throw(_("Maximum order quantity should be greater than minimum order quantity"))


	def make_route(self):
		if not self.route:
			self.route = self.scrub(self.item)
			check_category_exist = frappe.get_list('Product Category', fields=["route"], 
										  filters={"route": self.route},ignore_permissions =True)
			check_route = self.scrub(self.item) + "-" + str(len(check_category_exist))
			routes='"{route}","{check_route}"'.format(route=self.route,check_route=check_route)
			Product = DocType('Product')
			route_list = routes.split(',')
			check_exist_query = (
				frappe.qb.from_(Product)
				.select(Product.name)
				.where(Product.route.isin(route_list))
				.where(Product.name != self.name)
			)
			check_exist = check_exist_query.run(as_dict=True)

			if check_exist and len(check_exist) > 0:
				st = str(len(check_exist))
				self.route = self.scrub(self.item) + "-" + st
			if check_category_exist and len(check_category_exist) >0:
				st = str(len(check_exist)+len(check_category_exist))
				self.route = self.scrub(self.item) + "-" + st

		
	def on_update(self):
		update_whoose_search(self)
		self.get_product_availability()
		media_settings = get_settings('Media Settings')
		category = None
		if self.product_categories: 
			category = sorted(
								self.product_categories,
								key = lambda x: x.idx,
								reverse = False
							)[0].category
		list_size = media_settings.list_thumbnail_size
		if category:
			size = frappe.db.get_value('Product Category',category,'product_image_size')
			if size and int(size) > 0:
				list_size = size
		if not self.return_policy:
			self.return_description = ""
		if self.has_variants:
			if self.variant_combination:
				if self.inventory_method != "Track Inventory By Product Attributes":
					self.inventory_method = "Track Inventory By Product Attributes"
		if not self.has_variants:
			if self.inventory_method != "Track Inventory":
				self.inventory_method = "Track Inventory"
		if self.has_variants == 1 and self.variant_combination and self.is_combinations_are_generated == 0:
			self.is_combinations_are_generated = 1
		if self.brand:
			check_brands = frappe.db.get_all("Product Brand Mapping",filters = {"parent":self.name})
			if check_brands:
				for x in self.product_brands:
					x.brand = self.brand
			else:
				self.append("product_brands",{"brand":self.brand})
			frappe.db.commit()
		self.update_product_mapping()
	
	def insert_combination_mapping(self):
		sku_no = 1
		sku_seq = frappe.db.get_all("Product Variant Combination",
									filters = {"parent":self.name},
									fields = ['sku'],
									order_by = "sku desc",
									limit_page_length = 1
								)
		if sku_seq:
			if sku_seq[0].sku:
				l_sku = sku_seq[0].sku
				sku_no = int(l_sku[-3:])+1
		for v in self.variant_combination:
			if not v.sku:
				v_sku = self.name.split("ITEM-")[1]+'%03d' % sku_no
				frappe.db.set_value("Product Variant Combination",v.name,"sku",v_sku)
				v.sku = v_sku
				sku_no = sku_no+1
			if v.product_title:
				v.product_title = v.product_title.rstrip('/')
				v.product_title = v.product_title.rstrip(',')
			if v.disabled==0:
				attribute_ids = v.attribute_id.split('\n')
				for opt in attribute_ids:
					if opt:
						if not frappe.db.get("Combination Option Mapping",
							filters = {"product_id":self.name,"combination_id":v.name,"option_id":opt}):
							frappe.get_doc({
											"doctype": "Combination Option Mapping",
											"product_id": self.name,
											"combination_id": v.name,
											"option_id":opt,
										}).insert()
		frappe.db.commit()  


	def update_product_mapping(self):
		if not self.sku:
			self.sku = self.name.split('ITEM-')[1]+"000"
		if self.variant_combination:
			self.insert_combination_mapping()
		if self.product_brands:
			for x in self.product_brands:
				if not x.unique_name:
					frappe.db.set_value("Product Brand Mapping",x.name,
										"unique_name",self.scrub(x.brand))
			frappe.db.commit()  
		if self.attribute_options:
			for x in self.attribute_options:
				if not x.unique_name:
					frappe.db.set_value("Product Attribute Option",x.name,"unique_name",
						 self.scrub(frappe.db.get_value(
														"Product Attribute",
														x.attribute,
														"attribute_name"
													).lstrip())+"_" + self.scrub(x.option_value.lstrip()))
				if not x.attribute_id:
					p_attr_id = frappe.db.get_all("Product Attribute Mapping",
								   filters={"parent":self.name,"product_attribute":x.attribute})
					if p_attr_id:
						x.attribute_id = p_attr_id[0].name
			frappe.db.commit()
		if self.product_attributes:
			for x in self.product_attributes:
				if not x.attribute_unique_name:
					frappe.db.set_value("Product Attribute Mapping",x.name,
						 "attribute_unique_name",self.scrub(x.attribute.lstrip()))    
			frappe.db.commit()
		if self.product_categories:
			frappe.enqueue('go1_commerce.\
				  go1_commerce.doctype.product.product.\
				  update_category_data_json',queue = 'short',at_front = True,doc = self)

	def validate_attribute_options(self):
		if self.product_attributes:
			lists = ''
			for item in self.product_attributes:
				if not item.get('__islocal'):
					ProductAttributeOption = DocType('Product Attribute Option')
					check_attributes_query = (
						frappe.qb.from_(ProductAttributeOption)
						.select(ProductAttributeOption.name)
						.where(ProductAttributeOption.attribute_id == item.name)
					)
					check_attributes = check_attributes_query.run()

					if not check_attributes and (item.control_type != "Text Box" and \
								  item.control_type != "Multi Line Text"):
						lists += '<li>{0}</li>'.format(item.product_attribute)


	def get_product_availability(self):
		if self.stock and self.stock > 0 and self.inventory_method == 'Track Inventory':
			notification_product = frappe.db.get_all("Product Availability Notification",
											fields=['product','is_email_send','name','attribute_id'], 
											filters={'is_email_send': 0, 'product': self.name})
			if notification_product:
				for stock_avail in notification_product:
					availability = frappe.get_doc("Product Availability Notification",stock_avail.name)
					availability.is_email_send=1
					availability.save(ignore_permissions=True)
		if self.inventory_method == 'Track Inventory By Product Attributes' and \
											len(self.variant_combination)>0:
			notification_product = frappe.db.get_all("Product Availability Notification",
											fields=['product','is_email_send','name','attribute_id'], 
											filters={'is_email_send': 0, 'product': self.name})
			if notification_product:
				for stock_avail in notification_product:
					if stock_avail.attribute_id:
						attribute_id = stock_avail.attribute_id.strip()
						check_data = next((x for x in self.variant_combination \
								if x.attribute_id == stock_avail.attribute_id), None)
						if check_data and check_data.stock > 0:
							availability = frappe.get_doc("Product Availability Notification",
												stock_avail.name)
							availability.is_email_send=1
							availability.save()


	def get_context(self, context):
		try:
			page_builder = frappe.db.get_all("Web Page Builder",
									filters={"published":1,"document":"Product"},
									fields=['file_path'])
			if page_builder:
				context.template = page_builder[0].file_path
			from go1_commerce.go1_commerce.v2.product \
				import get_product_price
			catalog_settings = context.catalog_settings
			price_details = get_product_price(self)
			orgprice = self.price
			self.check_price_details(context,price_details,orgprice)
			if self.meta_keywords:
				context.meta_keywords=self.meta_keywords if self.meta_keywords else self.item
			else:
				context.meta_keywords = context.catalog_settings.meta_keywords
			self.get_product_mapping(context,catalog_settings,orgprice)
			self.get_custom_fields(context,catalog_settings)
		except Exception:
			frappe.log_error('Error in product.product.get_context', frappe.get_traceback())
	
	

	def get_product_variant_combination(self,context,productattributes,video_list,
									 size_chart,size_charts,size_chart_params,
									 product_attributes,attr_product_title):
		for attribute in productattributes:
			if attribute.size_chart:
				data = self.get_size_chart_content(size_charts,attribute)
				size_charts = data[0]
				size_chart_params = data[1]
			options = frappe.db.get_all("Product Attribute Option",fields=['*'],
					filters={'parent':self.name,'attribute':attribute.product_attribute,
					'attribute_id':attribute.name},order_by='display_order',limit_page_length=50)           
			for op in options:
				txt = '"%' + op.name + '%"'
				ProductVariantCombination = DocType('Product Variant Combination')
				varients_query = (
					frappe.qb.from_(ProductVariantCombination)
					.select(
						ProductVariantCombination.name,
						ProductVariantCombination.attributes_json,
						ProductVariantCombination.attribute_id,
						ProductVariantCombination.option_color,
						ProductVariantCombination.parent,
						ProductVariantCombination.image_list
					)
					.where(ProductVariantCombination.parent == self.name)
					.where(ProductVariantCombination.attribute_id.like(txt))
					.orderby(ProductVariantCombination.idx)
				)
				varients = varients_query.run(as_dict=True)
				if op.is_pre_selected == 1:
					if op.product_title and op.product_title != '-':
						attr_product_title = op.product_title
				image = self.get_product_attribute_option(context,op,varients,video_list)

			product_attributes.append({
										"attribute":attribute.product_attribute,
										"attribute_name":attribute.attribute,
										"is_required":attribute.is_required,
										"control_type":attribute.control_type,
										"attribute_chart":attribute.size_chart,
										"options":options,
										"size_charts":size_charts,
										'size_chart':size_chart,
										'size_chart_params':size_chart_params
									})
		context.product_title = attr_product_title
		context.attr_image = image
		

	def get_size_chart_content(self,size_charts,attribute):
		size_charts = frappe.db.get_all('Size Chart',
										filters = {'name':attribute.size_chart},
										fields = ['size_chart_image','name'])
		SizeChartContent = DocType('Size Chart Content')
		size_chart_query = (
			frappe.qb.from_(SizeChartContent)
			.select(
				Field('attribute_values').trim().as_('attribute_values'),
				SizeChartContent.chart_title,
				SizeChartContent.chart_value,
				SizeChartContent.name
			)
			.where(SizeChartContent.parent == attribute.size_chart)
			.orderby(SizeChartContent.display_order)
		)
		size_chart = size_chart_query.run(as_dict=True)
		unique_sizes = list(set([x.chart_title for x in size_chart]))
		unique_attr = []
		for uni in size_chart:
			if uni.attribute_values not in unique_attr:
				unique_attr.append(uni.attribute_values)
		size_chart_list = []
		for attr in unique_attr:
			sizes_list = list(filter(lambda x: x.attribute_values == attr, size_chart))
			arr = {}
			if sizes_list:
				arr['attribute'] = attr
				for sz in unique_sizes:
					check = next((x for x in sizes_list if x.chart_title == sz), None)
					if check:
						arr[sz] = check.chart_value
					else:
						arr[sz] = ''
				size_chart_list.append(arr)
		size_chart = size_chart_list
		size_chart_params = unique_sizes
		return [size_charts,size_chart_params]

	def get_product_attribute_option(context,op,varients,video_list):
		if op.image_list:
			images = json.loads(op.image_list)
			if len(images) > 0:
				images = sorted(images, key=lambda x: x.get('is_primary'), reverse=True)
				op.image_attribute = images[0].get('thumbnail')
				if op.is_pre_selected == 1:                     
					image = []
					for im in images:
						image.append({
										'original_image': im.get('image'), 
										'detail_image': im.get('detail_thumbnail'), 
										'detail_thumbnail': im.get('thumbnail')
									})
		if len(varients) >0:
			combination_img = varients[0]
			if combination_img.image_list:
				images = json.loads(combination_img.image_list)
				if len(images) > 0:
					images = sorted(
									images, 
									key = lambda x: x.get('is_primary'),
									reverse = True
								)
					image=[]
					for im in images:
						image.append({'original_image': im.get('image'),
										'detail_image': im.get('detail_thumbnail'),
										'detail_thumbnail': im.get('thumbnail')
									})
			attribute_video = frappe.get_all('Product Attribute Option Video',
											filters = {"option_id":combination_img.name},
											fields = ["youtube_video_id","video_type"])
			if attribute_video:
				for video in attribute_video:
					if video.youtube_video_id:
						video_list.append({
											'video_link':video.youtube_video_id,
											'video_type':video.video_type
										})
		if op.is_pre_selected == 1:
			attribute_video = frappe.get_all('Product Attribute Option Video',
												filters = {"option_id":op.name},
												fields = ["youtube_video_id","video_type"])
			if attribute_video:
				for video in attribute_video:
					if video.youtube_video_id:
						video_list.append({
											'video_link':video.youtube_video_id, 
											'video_type':video.video_type
											})
		return image
			
	def get_product_brand(self,context):
		if self.status != 'Approved':
			frappe.local.flags.redirect_location = '/404'
			raise frappe.Redirect
		ProductBrand = DocType('Product Brand')
		ProductBrandMapping = DocType('Product Brand Mapping')
		brands_query = (
			frappe.qb.from_(ProductBrand)
			.inner_join(ProductBrandMapping)
			.on(ProductBrand.name == ProductBrandMapping.brand)
			.select(
				ProductBrand.name,
				ProductBrand.brand_name,
				ProductBrand.brand_logo,
				ProductBrand.route,
				ProductBrand.warranty_information.as_('warranty_info'),
				ProductBrand.description
			)
			.where(ProductBrandMapping.parent == self.name)
			.groupby(ProductBrand.name)
			.orderby(ProductBrandMapping.idx)
		)
		context.brands = brands_query.run(as_dict=True)
		self.get_product_reviews(context)
		productattributes = frappe.db.get_all('Product Attribute Mapping',
												fields = ["*"], 
												filters = {"parent":self.name},
												order_by = "display_order",
												limit_page_length = 50
											)
		image = []
		if self.product_images:
			for item in self.product_images:
				image.append({
								"original_image":item.product_image,
								"product_image":item.detail_image,
								"detail_image":item.detail_image,
								"detail_thumbnail":item.detail_thumbnail
							})
		if self.product_images:
			context.og_image = self.product_images[0].product_image
		path1 = frappe.local.request.path
		context.page_url = get_url() + path1
		return productattributes
			

	def get_specification_group(self,context,catalog_settings,product_attributes,video_list):
		if catalog_settings.product_thumbnail_image_position:
			context.image_position = catalog_settings.product_thumbnail_image_position
		context.catalog_settings = catalog_settings
		context.attributes=product_attributes
		from go1_commerce.go1_commerce.v2.product \
											import get_enquiry_product_detail
		context.type_of_category = get_enquiry_product_detail(self.name)
		specification_group = []
		SpecificationGroup = DocType('Specification Group')
		ProductSpecAttrMapping = DocType('Product Specification Attribute Mapping')
		specification_attribute_query = (
			frappe.qb.from_(ProductSpecAttrMapping)
			.inner_join(SpecificationGroup)
			.on(SpecificationGroup.name == ProductSpecAttrMapping.spec_group_name1)
			.select(
				ProductSpecAttrMapping.spec_group_name.distinct(),
				SpecificationGroup.display_order
			)
			.where(ProductSpecAttrMapping.parent == self.name)
			.orderby(ProductSpecAttrMapping.idx)
		)
		specification_attribute = specification_attribute_query.run(as_dict=True)
		if specification_attribute:
			for item in specification_attribute:
				groups = frappe.db.get_all('Product Specification Attribute Mapping',
											fields = ['specification_attribute','options'], 
											filters = {"parent":self.name,'spec_group_name':item},
											order_by = 'idx')
				specification_group.append({"name":item, "groups":groups})
		context.specification_attribute_grouping = specification_group
		demovideo = frappe.db.get_all('Product Video',
										fields = ["*"], 
										filters = {"parent":self.name},
										order_by = "display_order")
		context.demo_video = demovideo
		if len(video_list)>0:
			context.demo_video = video_list
		if frappe.session.user != 'Guest':
			update_customer_recently_viewed(self.name)
		context.page_path = get_url()
			

	def check_price_details(self,context,price_details,orgprice):
		if price_details:
			if price_details.get('discount_amount'):
				orgprice = price_details.get('rate')
			context.discount_rule = price_details.get('discount_rule')
			context.discount_label = price_details.get('discount_label')
		if flt(orgprice) != flt(self.price):
			context.old_price=self.price
			context.price=orgprice
		if self.disable_add_to_cart_button == 1:
			self.set_product_availability(0, 'Out of Stock', context)
		elif self.inventory_method=='Dont Track Inventory':
			self.set_product_availability(1, 'In Stock', context)
		elif self.inventory_method=='Track Inventory':
			if self.stock == 0:
				self.set_product_availability(0, 'Out of Stock', context)
			elif self.stock > 0:
				self.set_product_availability(1, 'In Stock', context)
		else:
			self.set_product_availability(1, 'In Stock', context)
		if self.meta_title:
			context.meta_title=self.meta_title if self.meta_title else self.item
		else:
			context.meta_title = context.catalog_settings.meta_title
		if self.meta_description:        
			context.meta_description=self.meta_description if self.meta_description else self.item 
		else:
			context.meta_description = context.catalog_settings.meta_description


	def get_custom_fields(self,context,catalog_settings):
		custom_values = []
		if catalog_settings.display_custom_fields == 1:
			if frappe.db.get_all("Custom Field",filters={"dt":"Product"}):
				CustomField = DocType('Custom Field')
				custom_fields_query = (
					frappe.qb.from_(CustomField)
					.select(CustomField.label, CustomField.fieldname)
					.where(
						(CustomField.dt == 'Product') &
						(CustomField.fieldtype != 'Table') &
						(CustomField.fieldtype != 'Section Break') &
						(CustomField.fieldtype != 'Column Break') &
						(CustomField.fieldtype != 'HTML') &
						(CustomField.fieldtype != 'Check') &
						(CustomField.fieldtype != 'Text Editor')
					)
				)
				custom_fields = custom_fields_query.run(as_dict=True)
				for field in custom_fields:
					Product = DocType('Product')
					custom_value_query = (
						frappe.qb.from_(Product)
						.select(Field(field.fieldname))
						.where(Product.name == self.name)
					)
					custom_value = custom_value_query.run(as_dict=True)
					custom_values.append({
											"field":field.fieldname,
											"label":field.label,
											"value":custom_value[0][field.fieldname]
										})
		context.custom_values = custom_values
		context.product_name = self.item.replace("'","").replace('"','')
		recent_products = []
		best_sellers_list = []
		if catalog_settings.detail_page_template == "Default Layout":
			recent_products = get_recent_products()
			from go1_commerce.go1_commerce.v2.product \
				import get_bestsellers
			best_sellers_list = get_bestsellers(None,limit=5)
		context.recent_products = recent_products
		context.best_sellers = best_sellers_list
		context.product_category = context.item_categories
		if not self.return_policy:
			context.return_description = ""


	def get_product_mapping(self,context, catalog_settings, orgprice):
		allow_review = 0
		if frappe.session.user != 'Guest':
			allow_review = 1
		else:
			if context.catalog_settings.allow_anonymous_users_to_write_product_reviews:
				allow_review = 1
		context.allow_review = allow_review
		ziprange = frappe.request.cookies.get("ziprange")
		context.ziprange = ziprange
		ProductCategoryMapping = DocType('Product Category Mapping')
		categories_list_query = (
			frappe.qb.from_(ProductCategoryMapping)
			.select(ProductCategoryMapping.category, ProductCategoryMapping.category_name)
			.where(ProductCategoryMapping.parent == self.name)
			.orderby(ProductCategoryMapping.idx)
			.limit(1)
		)
		categories_list = categories_list_query.run(as_dict=True)
		if categories_list:
			product_category = frappe.db.get_all('Product Category',
												fields = ["*"], 
												filters = {"name":categories_list[0].category},
												order_by = "display_order",
												limit_page_length = 1)
			context.item_categories = product_category[0]
		self.set_tax_rate(context,catalog_settings,orgprice)
		if context.map_api:
			self.check_website_product_available(context)
		product_enquiry = get_product_scroll(self.name, 1, 5)
		context.product_enquiry = product_enquiry
		context.mobile_page_title = self.item
		if self.product_attributes:
			for item in self.product_attributes:
				if not "Table" in item.control_type:
					context.control_type_check = 1
		advance_amount = 0
		context.advance_amount = advance_amount


	def get_product_reviews(self, context):     
		context.approved_reviews = get_product_reviews_list(self.name, 0, 10)
		if context.catalog_settings.upload_review_images:
			ProductReview = DocType('Product Review')
			ReviewImage = DocType('Review Image')
			review_images_query = (
				frappe.qb.from_(ProductReview)
				.inner_join(ReviewImage).on(ProductReview.name == ReviewImage.parent)
				.select(
					ReviewImage.review_thumbnail,
					ReviewImage.image,
					ReviewImage.list_image,
					ReviewImage.parent,
					ReviewImage.name,
					ProductReview.product
				)
				.where(ProductReview.product == self.name)
			)
			review_images = review_images_query.run(as_dict=True)
			context.review_img = review_images


	def set_product_availability(self,allow_cart,stock_availability,context):
		context.allow_cart=allow_cart
		context.stock_availability=stock_availability


	def set_tax_rate(self, context,catalog_settings,orgprice):
		try:
			tax_rate1 = 0
			overall_tax_rates = 0
			if self.tax_category:
				tax_template=frappe.get_doc('Product Tax Template',self.tax_category)
				if tax_template and tax_template.tax_rates:
					item_tax = 0
					for tax in tax_template.tax_rates:
						if catalog_settings.included_tax:
							item_tax = item_tax + round(orgprice * tax.rate / (100 + tax.rate), 2)
						else:
							item_tax = item_tax + round(orgprice * tax.rate / 100, 2)
						overall_tax_rates = overall_tax_rates + tax.rate
					context.tax_rate1 = tax_rate1 + item_tax       
					context.overall_tax_rates = overall_tax_rates
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Error in doctype.product.set_tax_rate")

	def check_website_product_available(self, context):
		zipcode = state = country = city = None
		if context.customer_address:
			address = None
			if frappe.request.cookies.get('addressId'):
				address = next((x for x in context.customer_address if x.name == \
					frappe.request.cookies.get('addressId')), None)
			elif not frappe.request.cookies.get('guestaddress'):
				address = context.customer_address[0]
			if address:
				zipcode, city = address.zipcode, address.city
				state, country = address.state, address.country
		if not zipcode and frappe.request.cookies.get('guestaddress'):
			addr = unquote(frappe.request.cookies.get('guestaddress'))
			if addr.find(',') > -1:
				zipcode = addr.split(',')[0]
				state = addr.split(',')[1]
				country = addr.split(',')[2]
				city = addr.split(',')[3]
			else:
				zipcode = addr
				frappe.log_error("Zipcode",zipcode)          
				zipcode, city, state, country = get_location_details(zipcode)
				frappe.local.cookie_manager.set_cookie("guestaddress", '{0},{1},{2},{3}'.\
										   format(zipcode,state,country,city))
		if not zipcode:
			zipcode = '600001'
			city, state, country = 'Chennai', 'Tamil Nadu', 'India'
			frappe.local.cookie_manager.set_cookie("guestaddress", '{0},{1},{2},{3}'.\
										  format(zipcode,state,country,city))
		if zipcode:
			html = "zipcode :" + str(zipcode) + "\n"
			html += "state :" + str(state) + "\n"
			html += "country :" + str(country) + "\n"
			from go1_commerce.go1_commerce.v2.product \
				import check_user_location_delivery
			res = check_user_location_delivery(zipcode, state, country)
			html += "res :" + str(res) + "\n"
			if res:
				context.delivery_area = res.get('allow')
				delivery_days = res.get('delivery_days')
				if delivery_days and type(delivery_days) == int:
					from_date = getdate(nowdate())
					to_date = add_days(from_date, int(delivery_days))
					context.delivery_date = '{0}'.format(to_date.strftime('%a, %b %d'))
				context.zipcode = zipcode
				context.city = city 


	def check_commission(self):     
		if self.commission_category:
			VendorDetail = DocType('Vendor Detail')
			commission_query = (
				frappe.qb.from_(VendorDetail)
				.select('*')
				.where(VendorDetail.parent == self.commission_category)
				.where(
					(VendorDetail.product.is_null() | (VendorDetail.product == self.name))
				)
			)
			commission = commission_query.run(as_dict=True)
			if commission:
				self.commission_rate=commission[0].rate
				self.commission_amount=self.price*commission[0].rate/100
			else:
				cmm=frappe.get_doc('Commission Settings',self.commission_category)
				self.commission_rate=cmm.default_rate
				self.commission_amount=self.price*cmm.default_rate/100


	def validate_availability(self):
		from frappe.utils import add_to_date
		if not self.current_availability and not self.next_available_at:
			system_settings = frappe.get_single('System Settings')
			actual_date = datetime.now(timezone(system_settings.time_zone))
			dtfmt = '%Y-%m-%d %H:%M:%S'
			day=actual_date.strftime('%A')
			new_date=actual_date.replace(tzinfo=None)
			if not self.all_time:
				if self.menu_item_timings:
					for item in self.menu_item_timings:
						from_date = datetime.strptime(str(actual_date.date())+' '+\
															str(item.from_time),dtfmt)
						to_date=datetime.strptime(str(actual_date.date())+' '+str(item.to_time),dtfmt)
						if from_date > new_date and not self.next_available_at:
							self.next_available_at = from_date
						elif not self.next_available_at and len(self.menu_item_timings) == 1:
							self.next_available_at = add_to_date(from_date, days=1)
	

def remove_html_tags(text):
	try:
		"""Remove html tags from a string"""
		import re
		return re.sub(re.compile('<.*?>'), '', text)
	except Exception:
		frappe.log_error(frappe.get_traceback(), 
				   ' Error in product.events.remove_html_tags')

def get_location_details(zipcode):
	city = state = country = None
	from go1_commerce.go1_commerce.utils.google_maps \
																import get_geolocation
	response = get_geolocation(zipcode)
	if response and response.get('address_components'):
		for item in response.get('address_components'):
			if "country" in item.get('types'):
				country = item.get('long_name')
			elif "administrative_area_level_1" in item.get('types'):
				state = item.get('long_name')
			elif "postal_code" in item.get('types'):
				zipcode = item.get('long_name')
			elif "locality" in item.get('types'):
				city = item.get('long_name')
			elif "administrative_area_level_2" in item.get('types'):
				city = item.get('long_name')
	return zipcode, city, state, country

@frappe.whitelist()
def get_all_tags():
	""" get the tags set in the  """
	tags = frappe.get_all("Product Tag",
		fields=["title"], distinct=True)

	active_tags = [row.get("title") for row in tags]
	return active_tags

@frappe.whitelist()
def get_product_attribute_options(attribute,product,attribute_id):
	try:
		filters = {
			'parent': product,
			'attribute': attribute,
			'attribute_id': attribute_id
		}
		attributeoptions = frappe.get_all(
			'Product Attribute Option',
			filters=filters,
			fields=['*']
		)
		return attributeoptions
	except Exception:
		frappe.log_error(frappe.get_traceback(),
				   "Error in doctype.product.get_product_attribute_options") 

@frappe.whitelist()
def get_parent_product_attribute_options(attribute,product):
	try:
		filters = {
			'parent': product,
			'attribute': attribute
		}
		attributeoptions = frappe.get_all(
			'Product Attribute Option',
			filters=filters,
			fields=['*'],
			order_by='idx ASC'
		)
		return attributeoptions
	except Exception:
		frappe.log_error(frappe.get_traceback(),
				   "Error in doctype.product.get_product_attribute_options") 


@frappe.whitelist()
def get_product_specification_attribute_options(attribute):
	try:
		spec_option = DocType('Specification Attribute Option')
		query = (
			frappe.qb.from_(spec_option)
			.select(spec_option.option_value)
			.where(spec_option.parent == attribute)
			.orderby(spec_option.display_order)
		)
		attributeoptions = query.run(as_dict=True)
		return attributeoptions
	except Exception:
		frappe.log_error(frappe.get_traceback(),
				"Error in doctype.product.get_product_specification_attribute_options") 


@frappe.whitelist()
def insert_product_attribute_options(attribute,product,option,display_order,price_adjustment,
									weight_adjustment,image,pre_selected,attribute_color,
									product_title,parent_option=None,attribute_id = None,
									disable=None,available_datetime=None):
	try:
		attribute_option = DocType('Product Attribute Option')
		query = (
			frappe.qb.from_(attribute_option)
			.select('*')
			.where(
				(attribute_option.parent == product) &
				(attribute_option.attribute == attribute) &
				(attribute_option.attribute_id == attribute_id)
			)
		)
		attributeoptions = query.run(as_dict=True)
		if len(attributeoptions) == 0:
			pre_selected = 1
		else:
			if int(pre_selected) == 1:
				for optionitem in attributeoptions:
					option_doc = frappe.get_doc("Product Attribute Option",optionitem.name)
					option_doc.is_pre_selected = 0
					option_doc.save()
		insert_product_attribute_option(attribute,product,option,display_order,price_adjustment,
									weight_adjustment,image,pre_selected,attribute_color,product_title,
									parent_option,attribute_id,disable,available_datetime)
		attribute_option = DocType('Product Attribute Option')
		query = (
			frappe.qb.from_(attribute_option)
			.select('*')
			.where(
				(attribute_option.parent == product) &
				(attribute_option.attribute == attribute) &
				(attribute_option.attribute_id == attribute_id)
			)
		)
		results = query.run(as_dict=True)
		return results
	except Exception:
		frappe.log_error(frappe.get_traceback(),
				   "Error in doctype.product.insert_product_attribute_options")


@frappe.whitelist()
def insert_product_attribute_option(attribute,product,option,display_order,price_adjustment,
									weight_adjustment,image,pre_selected,attribute_color,
									product_title,parent_option=None,attribute_id = None,
									disable=None,available_datetime=None):
	doc=frappe.get_doc({
			"doctype": "Product Attribute Option",
			"attribute":attribute,
			"attribute_id":attribute_id,
			"display_order":display_order,
			"price_adjustment":price_adjustment,
			"weight_adjustment":weight_adjustment,
			"attribute_color":attribute_color,
			"parent":product,
			"parenttype":'Product',
			"parentfield":'attribute_options',
			"option_value":option,
			"product_title":product_title,
			"image":image,
			"is_pre_selected":pre_selected,
			"parent_option":parent_option })
	doc.disable = int(disable)
	if int(disable)==1:
		doc.available_datetime = available_datetime
	doc.insert()
		

def update_product_attribute_options(attribute,product,option,display_order,price_adjustment,
									weight_adjustment,optionid,image,pre_selected,attribute_color,
									product_title,parent_option=None,attribute_id = None, 
									disable=None,available_datetime=None):
	try:
		attribute_option = DocType('Product Attribute Option')
		query = (
			frappe.qb.from_(attribute_option)
			.select('*')
			.where(
				(attribute_option.parent == product) &
				(attribute_option.attribute == attribute) &
				(attribute_option.attribute_id == attribute_id)
			)
		)
		attributeoptions = query.run(as_dict=True)
		

		update_product_attribute_option(attributeoptions,attribute,product,option,display_order,
									price_adjustment,weight_adjustment,optionid,image,pre_selected,
									attribute_color,product_title,parent_option=None,
									attribute_id = None,disable=None,available_datetime=None)
		attribute_option = DocType('Product Attribute Option')
		query = (
			frappe.qb.from_(attribute_option)
			.select('*')  # Select all columns
			.where(
				(attribute_option.parent == product) &
				(attribute_option.attribute == attribute) &
				(attribute_option.attribute_id == attribute_id)
			)
		)
		attributeoptions = query.run(as_dict=True)
		return attributeoptions
	except Exception:
		frappe.log_error(frappe.get_traceback(),
				   "Error in doctype.product.update_product_attribute_options") 


@frappe.whitelist()
def update_product_attribute_option(attributeoptions,attribute,product,option,display_order,
									price_adjustment,weight_adjustment,optionid,image,pre_selected,
									attribute_color,product_title,parent_option=None,
									attribute_id = None,disable=None,available_datetime=None):
	if int(pre_selected) == 1:
		for x in attributeoptions:
			opt = frappe.get_doc("Product Attribute Option", x.name)
			opt.is_pre_selected = 0
			opt.save()
	doc=frappe.get_doc("Product Attribute Option",optionid)
	doc.attribute=attribute
	doc.attribute_id=attribute_id
	doc.display_order=display_order
	doc.parent=product
	doc.price_adjustment=price_adjustment
	doc.weight_adjustment=weight_adjustment
	doc.attribute_color=attribute_color
	doc.product_title=product_title
	doc.option_value=option
	doc.parent_option = parent_option
	doc.disable = int(disable)
	if int(disable)==1:
		doc.available_datetime = available_datetime
	doc.image=image
	doc.is_pre_selected=pre_selected
	doc.save()

@frappe.whitelist()
def get_all_brands():
	try:
		product_brand = DocType('Product Brand')
		query = (
			frappe.qb.from_(product_brand)
			.select(
				product_brand.brand_logo,
				product_brand.name,
				product_brand.brand_name,
				product_brand.published
			)
			.where(product_brand.published == 1)
			.orderby(product_brand.brand_name)
		)
		results = query.run(as_dict=True)
		return results
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.product.get_all_brands") 



@frappe.whitelist()
def get_all_category_list():    
	try:
		lists=[]
		product_category = DocType('Product Category')
		query = (
			frappe.qb.from_(product_category)
			.select(
				product_category.category_image,
				product_category.category_name,
				product_category.parent_category_name,
				product_category.is_active,
				product_category.name
			)
			.where(
				(product_category.is_active == 1) &
				((product_category.parent_product_category.isnull()) |
				 (product_category.parent_product_category == ""))
			)
		)
		cat = query.run(as_dict=True)
		if cat:
			for sub in cat:
				sub.indent = 0
				lists.append(sub)
				sub.subcat = get_sub_category_list(sub.name)
				if sub.subcat:
					for subsub in sub.subcat:
						subsub.indent = 1
						lists.append(subsub)
						subsub.subsubcat = get_sub_category_list(subsub.name)
						if subsub.subsubcat:
							for listcat in subsub.subsubcat:
								listcat.indent=2
								lists.append(listcat)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.product.get_all_category_list") 


@frappe.whitelist()
def get_sub_category_list(category):    
	try:
		product_category = DocType('Product Category')
		query = (
			frappe.qb.from_(product_category)
			.select(
				product_category.category_image,
				product_category.category_name,
				product_category.parent_category_name,
				product_category.is_active,
				product_category.name
			)
			.where(
				(product_category.is_active == 1) &
				(product_category.parent_product_category == category)
			)
		)
		results = query.run(as_dict=True)
		return results
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.product.get_sub_category_list") 


def approve_products(names,status):
	try:
		import json
		data = json.loads(names)
		if len(data)==0:
			frappe.msgprint(_('Please select any items'))
		else:
			for item in data:
				frappe.db.set_value('Product',item,'status',status)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.product.approve_products") 

@frappe.whitelist()
def get_product_attributes_with_options(product):
	attributes=frappe.db.get_all('Product Attribute Mapping',filters={'parent':product},
							  fields=['name','product_attribute','is_required','control_type',
								'attribute_unique_name','attribute'],order_by='display_order')
	if attributes:
		for item in attributes:
			item.options=get_product_attribute_options(item.product_attribute,product,item.name)            
	return attributes


@frappe.whitelist()
def create_variant_combinations(attributes):
	try:
		import json
		options = []
		all_options = []
		response = json.loads(attributes)
		p_combinations = frappe.db.get_all("Product Variant Combination",
										filters={"parent":json.loads(attributes)[0].get("product")},
										fields=['attribute_id'])
		for item in response:
			if item.get('attroptions'):
				li = [x.get('option_value') for x in item.get('attroptions')]
				options.append(li)
			all_options += item.get('attroptions')
		import itertools
		combination = list(itertools.product(*options))
		lists = []
		sku_seq = frappe.db.get_all("Product Variant Combination",
								filters={"parent":json.loads(attributes)[0].get("product")},
								fields=['sku'],order_by="sku desc",limit_page_length=1)
		lists = get_combination_list(sku_seq,combination,all_options,p_combinations,attributes,lists)
		return lists
	except Exception:
		frappe.log_error(title = "create_variant_combinations", message = frappe.get_traceback())
		frappe.response.status = "failed"


@frappe.whitelist()	
def get_combination_list(sku_seq,combination,all_options,p_combinations,attributes,lists):
	sku_no = 0
	if sku_seq:
		if sku_seq[0].sku:
			l_sku = sku_seq[0].sku
			sku_no = int(l_sku[-3:])+1
	for item in combination:
		html=''
		ids=''
		price=0
		variant_text = ""
		attributes_json = []
		for li in item:
			check=next((x for x in all_options if x.get('option_value')==li),None)
			if check and check.get('name'):
				attribute_name = frappe.db.get_value("Product Attribute", \
										 check.get('attribute'), "attribute_name")
				ids+=check.get('name')+'\n'
				html+='<div data-name="'+str(ids)+'" class="btn btn-default btn-xs btn-link-to-form" \
					style="border: 1px solid #d1d8dd;margin: 2px;min-width: 50px;text-align: left;">\
					<p style="text-align: left;margin: 0px;font-size: 11px;">'+attribute_name+'</p> \
					<span style="font-weight: 700;">'+li+'</span></div>'
				price+=check.get('price_adjustment')
				variant_text+= li+" , "
				attributes_json.append(check.get('name'))
		if ids:
			if not any(obj['attribute_id'] == ids for obj in p_combinations):
				v_sku = json.loads(attributes)[0].get("product").split("ITEM-")[1]+'%03d' % sku_no
				p_title = frappe.db.get_value("Product",json.loads(attributes)[0].\
								  get("product"),"item")+" - "+get_attributes_text(attributes_json)
				lists.append({'sku':v_sku,'product_title':p_title,'attribute_html':html,\
				  'attribute_id':ids, 'stock': 1,'price':price, 'attributes_json': attributes_json})
				sku_no = sku_no + 1
		else:
			frappe.throw(_("Please add and save the attribute options to create the combinations"))
	return lists


@frappe.whitelist()
def get_attributes_text(attributes_json):
	combination_txt=""
	if attributes_json:
		variant = (attributes_json)
		attribute_html = ""
		for obj in variant:
			if attribute_html:
				attribute_html +=", "
			option_value, attribute = frappe.db.get_value("Product Attribute Option", obj, \
												 ["option_value","attribute"])
			attribute_name = frappe.db.get_value("Product Attribute", attribute, "attribute_name")
			attribute_html += attribute_name+":"+option_value
		combination_txt = attribute_html
	return combination_txt


@frappe.whitelist()	
def get_category_based_attributes(txt,filters):
	condition=''
	if filters.get('productId'):
		category_mapping = DocType('Product Category Mapping')
		query = (
			frappe.qb.from_(category_mapping)
			.select(
				fn.GroupConcat(fn.Concat('"', category_mapping.category, '"')).as_("category")
			)
			.where(category_mapping.parent == filters.get('productId'))
		)
		category_list = query.run(as_dict=True)
		main_doc = DocType(doctype)
		business_category = DocType('Business Category')
		cat_list = '""'
		if category_list and category_list[0].category:
			cat_list = category_list[0].category
		query = (
			frappe.qb.from_(main_doc)
			.left_join(business_category)
			.on(main_doc.name == business_category.parent)
			.select(main_doc.name, main_doc.attribute_name)
			.where(
				(fn.If(business_category.category.isnotnull(), 
						business_category.category.in_(cat_list), 
						1)) &
				(fn.If(txt, 
					   (main_doc.name.like(f"%{txt}%")) | (main_doc.attribute_name.like(f"%{txt}%")), 
					   1))
			)
		)
		results = query.run(as_dict=True)
		return results
	doc = DocType(filters.get('type'))
	query = (
		frappe.qb.from_(doc)
		.select(doc.name)
	)
	return query.run(as_dict=True)
	


def get_vendor_based_tax_templates():
	tax_template = DocType('Product Tax Template')
	query = (
		frappe.qb.from_(tax_template)
		.select(tax_template.name)
	)
	results = query.run(as_dict=True)
	return [row['name'] for row in results]


def get_vendor_based_return_policy():
	ReturnPolicy = DocType('Return Policy')
	query = (
		frappe.qb.from_(ReturnPolicy)
		.select(ReturnPolicy.name)
	)
	results = query.run(as_dict=True)
	return [row['name'] for row in results]


@frappe.whitelist()
def update_image(imageId,image_name,is_primary):
	doc=frappe.get_doc('Product Image',imageId)
	doc.image_name=image_name
	doc.is_primary=is_primary
	doc.save(ignore_permissions=True)



@frappe.whitelist()
def delete_product_attribute_option(option):
	try:
		attribute_option_video = DocType('Product Attribute Option Video')
		query = (
			frappe.qb.from_(attribute_option_video)
			.select(attribute_option_video.name, attribute_option_video.option_id)
			.where(attribute_option_video.option_id == option)
		)
		attribute_video = query.run(as_dict=True)
		if attribute_video:
			for video in attribute_video:
				video_doc = frappe.get_doc('Product Attribute Option Video',video.name)
				video_doc.delete()
		doc=frappe.get_doc("Product Attribute Option", option)
		if doc.get('image_list'):
			images = json.loads(doc.get('image_list'))
			from go1_commerce.go1_commerce.v2.product \
				import delete_attribute_image
			for im in images:
				delete_attribute_image(im)
		doc.delete()
		return {'status':'success'}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 
				   "Error in doctype.product.product.delete_product_attribute_option")


@frappe.whitelist()
def delete_product_attribute_option_image(ref_doctype, file_url):
	try:
		file_doc = DocType('File')
		query = (
			frappe.qb.from_(file_doc)
			.delete()
			.where(
				(file_doc.attached_to_doctype == ref_doctype) &
				(file_doc.file_url == file_url)
			)
		)
		query.run()
		return {'status': "Success"}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(),
			"Error in doctype.product.product.delete_product_attribute_option_image")


def randomStringDigits(stringLength=6):
	import random
	import string
	lettersAndDigits = string.ascii_uppercase + string.digits
	return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))



def update_product_categories(category1,name):
	ProductCategoryMapping = DocType('Product Category Mapping')
	query = (
		frappe.qb.from_(ProductCategoryMapping)
		.delete()
		.where(
			(ProductCategoryMapping.name == name)
		)
	)
	query.run()
	for x in json.loads(category1):
		paper_question = frappe.new_doc("Product Category Mapping")
		paper_question.category=x['category']
		paper_question.category_name=x['category_name']
		paper_question.parent=name
		paper_question.parentfield="product_categories"
		paper_question.parenttype="Product"
		paper_question.save()



def update_product_categories1(category1,name):
	ProductCategoryMapping = DocType('Product Category Mapping')
	query = (
		frappe.qb.from_(ProductCategoryMapping)
		.delete()
		.where(
			(ProductCategoryMapping.name == name)
		)
	)
	query.run()

	for x in json.loads(category1):
		paper_question = frappe.new_doc("Product Category Mapping")
		paper_question.category=x
		paper_question.parent=name
		paper_question.parentfield="product_categories"
		paper_question.parenttype="Product"
		paper_question.save()


def update_image(count,image_name,primary,childname):
	if image_name:
		frappe.db.set_value('Product Image', childname, 'idx', count)
		frappe.db.set_value('Product Image', childname, 'image_name', image_name)
		frappe.db.set_value('Product Image', childname, 'is_primary', primary)


def format_convertion(price=None):
	magnitude = 0
	num = flt(price)
	while abs(num) >= 100000:
		magnitude += 1
		num /= 100000.0
	rounded_amt = ('%.2f%s' % (num, ['','L'][magnitude]))
	return rounded_amt



def get_product_scroll(item, page_no, page_len):
	try:
		start = (int(page_no) - 1) * int(page_len)
		limit = int(page_len)
		product_enquiry = DocType('Product Enquiry')
		enquiry_answers = DocType('Product Enquiry Answers')
		query = (
			frappe.qb.from_(product_enquiry)
			.left_join(enquiry_answers)
			.on(product_enquiry.name == enquiry_answers.parent)
			.select(
				product_enquiry.name,
				product_enquiry.user_name,
				product_enquiry.email,
				product_enquiry.phone,
				product_enquiry.product,
				product_enquiry.question,
				Function('DATE_FORMAT', product_enquiry.creation, "%d, %b %Y").as_('creation'),
				Function('GROUP_CONCAT', enquiry_answers.answer, Function('SEPARATOR', ";")).as_('ans_list')
			)
			.where(
				(product_enquiry.product == item) &
				(product_enquiry.is_approved == 1)
			)
			.groupby(product_enquiry.name)
			.limit(start, limit)
		)
		product_enquiry = query.run(as_dict=True)
		return product_enquiry
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.product.product.get_product_scroll")



def get_review_scroll(item, page_no, page_len):
	start = (int(page_no) - 1) * int(page_len)
	limit = int(page_len)
	product_review = DocType('Product Review')
	review_image = DocType('Review Image')
	date_format = '%b %d, %Y'
	query = (
		frappe.qb.from_(product_review)
		.inner_join(review_image)
		.on(product_review.name == review_image.parent)
		.select(
			review_image.review_thumbnail,
			review_image.image,
			review_image.list_image,
			product_review.customer,
			review_image.email,
			Function('DATE_FORMAT', product_review.creation, date_format).as_('date'),
			product_review.review_title,
			product_review.review_message,
			product_review.rating,
			product_review.name
		)
		.where(product_review.product == item)
		.orderby(product_review.creation.desc())
		.limit(start, limit)
	)
	Reviews = query.run(as_dict=True)
	return Reviews


 
def get_review_images(name,product):
	product_review = DocType('Product Review')
	review_image = DocType('Review Image')
	date_format = '%b %d, %Y'
	query = (
		frappe.qb.from_(product_review)
		.inner_join(review_image)
		.on(product_review.name == review_image.parent)
		.select(
			review_image.review_thumbnail,
			review_image.image,
			review_image.list_image,
			review_image.name,
			review_image.parent,
			*product_review.fields,
			Function('DATE_FORMAT', product_review.creation, date_format).as_('date')
		)
		.where(product_review.product == product)
	)
	approved_reviews1 = query.run(as_dict=True)
	return approved_reviews1



def get_curreview_images(name):
	dateformat = '%b %d, %Y'
	review = DocType('Product Review')
	review_image = DocType('Review Image')
	query = (
		frappe.qb.from_(review)
		.inner_join(review_image)
		.on(review.name == review_image.parent)
		.select(
			review_image.review_thumbnail,
			review_image.image,
			review_image.list_image,
			review_image.parent,review.name, review.product,review.review_title,
			Function('DATE_FORMAT', review.creation, dateformat).as_('date')
		)
		.where(review.name == name)
	)
	return query.run(as_dict=True)



def check_product_attribute_options(product_attributes = None):
	if product_attributes:
		attribute_len = frappe.get_list("Product Attribute Option",fields = ['name'],
								  filters={'attribute_id' : product_attributes})
		if attribute_len > 0:
			return "true"
		else:
			return "false"
	else:
		pass



def get_product_reviews_list(product, page_no=0, page_len=10):
	start = int(page_no) * int(page_len)
	dateformat='%b %d, %Y'
	ProductReview = DocType('Product Review')
	reviews_query = (
		frappe.qb.from_(ProductReview)
		.select(
			ProductReview.name,
			ProductReview.customer,
			ProductReview.email,
			ProductReview.review_title,
			ProductReview.review_message,
			ProductReview.rating,
			Function('DATE_FORMAT', ProductReview.creation, dateformat).as_('date'),
			ProductReview.creation
		)
		.where(
			(ProductReview.product == product) &
			(ProductReview.is_approved == 1)
		)
		.orderby(ProductReview.creation, order=Order.desc)
		.limit(page_len)
		.offset(start)
	)
	reviews = reviews_query.run(as_dict=True)
	upload_image = get_settings_value('Catalog Settings', 'upload_review_images')
	if upload_image:
		for image in reviews:
			image.review_images=frappe.db.get_all('Review Image',fields=['review_thumbnail',
									'image','list_image','name'],filters={'parent':image.name})
	return reviews



def update_customer_recently_viewed(product, customer=None):
	enable_recently_viewed = get_settings_value('Catalog Settings', 'enable_recetly_viewed_products')
	if enable_recently_viewed:
		if not customer:
			if frappe.request.cookies.get('customer_id'):
				customer = unquote(frappe.request.cookies.get('customer_id'))
		if customer:
			check_already_viewed = frappe.get_all("Customer Viewed Product",
										 filters={'parent':customer,'product':product})
			if not check_already_viewed:
				customer_viewed_product = frappe.new_doc("Customer Viewed Product")
				customer_viewed_product.parent = customer
				customer_viewed_product.parenttype = "Customers"
				customer_viewed_product.parentfield = "viewed_products"
				customer_viewed_product.product = product
				customer_viewed_product.product_name = frappe.db.get_value('Product', product, 'item')
				customer_viewed_product.viewed_date = getdate(nowdate())
				customer_viewed_product.viewed_count = 1
				customer_viewed_product.save(ignore_permissions=True)
				frappe.db.commit()
			else:
				check_already_viewed_update = check_already_viewed[0]
				customer_viewed_product = frappe.get_doc("Customer Viewed Product", 
												check_already_viewed_update.name)
				customer_viewed_product.viewed_date = getdate(nowdate())
				customer_viewed_product.viewed_count = int(customer_viewed_product.viewed_count) + 1
				customer_viewed_product.save(ignore_permissions=True)
				frappe.db.commit()


def show_attribute_err(attribute_id):
	attribute_option = frappe.get_list("Product Attribute Option", 
									fields = ["attribute_id"], 
									filters = {"attribute_id": attribute_id})
	if attribute_option:
		return attribute_option
	else:
		return "Failed"


def check_attr_combination(self):
	if len(self.variant_combination) > 0:
		for i in self.variant_combination:
			att_id = '"' + '","'.join(i.attribute_id.split("\n"))[:-2]
		ProductAttributeOption = DocType('Product Attribute Option')
		if isinstance(att_id, str):
			att_id = (att_id,)
		options_query = (
			frappe.qb.from_(ProductAttributeOption)
			.select(ProductAttributeOption.name)
			.where(
				(ProductAttributeOption.parent == self.name) &
				(ProductAttributeOption.name.notin(att_id))
			)
		)
		options = options_query.run(as_dict=True)
		if options:
			pass
		else:
			frappe.throw("Please delete Attribute combinations and then try to delete attribute")


def delete_attribute_option_alert(option):
	ProductVariantCombination = DocType('Product Variant Combination')
	combination_query = (
		frappe.qb.from_(ProductVariantCombination)
		.select(ProductVariantCombination.name, ProductVariantCombination.attribute_id)
	)
	combination = combination_query.run(as_dict=True)
	att_id_arr = []
	for i in combination:
		att_id = (i.attribute_id.split("\n"))[:-2]
		for item in att_id:
			att_id_arr.append(str(item))
	attributes = frappe.get_doc("Product Attribute Option", option)
	if option  in att_id_arr:   
		frappe.throw("Cannot delete because Product Attribute Option " + attributes.option_value+ "is \
															linked with Product Attribute Combination")
	else:
		return "Success"

@frappe.whitelist()
def show_attribute_deletion_err(item, row_id):
	ProductVariantCombination = DocType('Product Variant Combination')
	ProductAttributeOption = DocType('Product Attribute Option')
	combination_query = (
		frappe.qb.from_(ProductVariantCombination)
		.select(ProductVariantCombination.name, ProductVariantCombination.attribute_id)
		.where(ProductVariantCombination.parent == item)
	)
	combination = combination_query.run(as_dict=True)
	att_id_arr = []
	for i in combination:
		att_id = i['attribute_id'].split("\n")
		att_id_arr.extend([x for x in att_id if x])
	att_id_arr_str = '","'.join(att_id_arr)
	if att_id_arr_str:
		attributes_query = (
			frappe.qb.from_(ProductAttributeOption)
			.select(ProductAttributeOption.name, ProductAttributeOption.attribute_id)
			.where(
				(ProductAttributeOption.attribute_id == row_id) &
				(ProductAttributeOption.name.isin(att_id_arr))
			)
		)
		attributes = attributes_query.run(as_dict=True)
		if attributes:
			return 'Failed'

@frappe.whitelist()
def check_attr_combination_price(self):
	if len(self.variant_combination) > 0:
		for i in self.variant_combination:
			if flt(i.price)<flt(self.price):
				frappe.throw("Attribute combination price should be greater than or equal to base price")

@frappe.whitelist()
def delete_attribute_options(dt, dn):
	try:
		doc = frappe.get_doc(dt, dn)
		attribute_options = get_product_attribute_options(doc.product_attribute, doc.parent, doc.name)
		for item in attribute_options:
			ProductAttributeOptionVideo = DocType('Product Attribute Option Video')
			attribute_video_query = (
				frappe.qb.from_(ProductAttributeOptionVideo)
				.select(ProductAttributeOptionVideo.name, ProductAttributeOptionVideo.option_id)
				.where(ProductAttributeOptionVideo.option_id == item.name)
			)
			attribute_video1 = attribute_video_query.run(as_dict=True)
			if attribute_video1:
				for video1 in attribute_video1:
					frappe.qb.from_(ProductAttributeOptionVideo).delete().where(ProductAttributeOptionVideo.name == video1['name']).run()
			if item.get('image_list'):
				from go1_commerce.go1_commerce.v2.product \
																		import delete_attribute_image
				images = json.loads(item.get('image_list'))
				for im in images:
					delete_attribute_image(im)
			ProductAttributeOption = DocType('Product Attribute Option')
			frappe.qb.from_(ProductAttributeOption).delete().where(ProductAttributeOption.name == item.name).run()
		return {'status': 'success'}
	except Exception as e:
		return {'status': 'Failed'}


@frappe.whitelist()
def insert_attribute_option_video(option_id,video_id,video_type):
	attribute_option_video = frappe.new_doc("Product Attribute Option Video")
	attribute_option_video.option_id = option_id
	attribute_option_video.youtube_video_id = video_id
	attribute_option_video.video_type = video_type
	attribute_option_video.save(ignore_permissions=True)
	ProductAttributeOptionVideo = DocType('Product Attribute Option Video')
	attributeoptions_video = frappe.qb.from_(ProductAttributeOptionVideo).select('*').where(ProductAttributeOptionVideo.option_id == option_id).run(as_dict=True)

	if attributeoptions_video:
		return attributeoptions_video
	 
@frappe.whitelist()
def get_attribute_option_videos(option_id):
	ProductAttributeOptionVideo = DocType('Product Attribute Option Video')
	attributeoptions_video = frappe.qb.from_(ProductAttributeOptionVideo).select('*').where(ProductAttributeOptionVideo.option_id == option_id).run(as_dict=True)
	if attributeoptions_video:
		return attributeoptions_video

@frappe.whitelist()
def delete_product_attribute_option_video(name):
	doc = frappe.get_doc('Product Attribute Option Video', name)
	doc.delete()
	return {'status': "Success"}

@frappe.whitelist()
def update_attribute_option_video(name,video_id,option_id,video_type):
	frappe.db.set_value('Product Attribute Option Video',name,'youtube_video_id',video_id)
	frappe.db.set_value('Product Attribute Option Video',name,'video_type',video_type)
	ProductAttributeOptionVideo = DocType('Product Attribute Option Video')
	attributeoptions_video = (
		frappe.qb.from_(ProductAttributeOptionVideo)
		.select('*')
		.where(ProductAttributeOptionVideo.option_id == option_id)
		.run(as_dict=True)
	)
	if attributeoptions_video:
		return attributeoptions_video


@frappe.whitelist()  
def get_all_category_lists(product_group=None):
	item_group = frappe.db.get_all("Product Category", fields=["*"], filters={"is_active":1})
	for n in item_group:
		child_groups = ", ".join(['"' + frappe.db.escape(i[0]) + '"' for i in get_child_groups(n.name)])
		parent_category = get_parent_item_groups(n.name)
		
@frappe.whitelist()
def get_parent_item_groups(item_group_name):
	item_group = frappe.get_doc("Product Category", item_group_name)
	ProductCategory = DocType('Product Category')
	categories = (
		frappe.qb.from_(ProductCategory)
		.select(ProductCategory.name, ProductCategory.category_name)
		.where(ProductCategory.lft <= item_group.lft)
		.where(ProductCategory.rgt >= item_group.rgt)
		.where(ProductCategory.is_active == 1)
		.orderby(ProductCategory.lft)
		.run(as_dict=True)
	)
	return categories

def get_child_groups(item_group_name):
	item_group = frappe.get_doc("Product Category", item_group_name)
	ProductCategory = DocType('Product Category')
	data = (
		frappe.qb.from_(ProductCategory)
		.select(ProductCategory.name, ProductCategory.category_name)
		.where(ProductCategory.lft >= item_group.lft)
		.where(ProductCategory.rgt <= item_group.rgt)
		.where(ProductCategory.is_active == 1)
		.run(as_dict=True)
	)
	return data


def get_child_categories1(category):
	try:
		lft, rgt = frappe.db.get_value('Product Category', category, ['lft', 'rgt'])
		ProductCategory = DocType('Product Category')
		categories = (
			frappe.qb.from_(ProductCategory)
			.select(ProductCategory.name)
			.where(ProductCategory.is_active == 1)
			.where(ProductCategory.disable_in_website == 0)
			.where(ProductCategory.lft >= lft)
			.where(ProductCategory.rgt <= rgt)
			.run(as_dict=True)
		)
		return categories
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'Error in api.get_child_categories')

@frappe.whitelist()
def get_category_list(reference_doc, reference_fields, filters=None, page_no=1, page_len=20, 
													search_txt=None, search_field="name"):
	reference_field = json.loads(reference_fields)
	ReferenceDoc = DocType(reference_doc)
	start = (int(page_no) - 1) * int(page_len)
	condition = f"{search_field} LIKE {frappe.qb.text('%' + search_txt + '%')}" if search_txt else None
	query = (
		frappe.qb.from_(ReferenceDoc)
		.select(*[getattr(ReferenceDoc, field) for field in reference_field])
		.where(ReferenceDoc.is_active == 1)
	)
	if condition:
		query = query.where(frappe.qb.text(condition))
	list_len = query.orderby(ReferenceDoc.lft).run(as_dict=True)
	list_name = (
		frappe.qb.from_(ReferenceDoc)
		.select(*[getattr(ReferenceDoc, field) for field in reference_field])
		.where(ReferenceDoc.is_active == 1)
	)

	if condition:
		list_name = list_name.where(frappe.qb.text(condition))

	list_name = (
		list_name.orderby(ReferenceDoc.lft)
		.limit(int(page_len))
		.offset(start) 
		)
	
	list_name = list_name.run(as_dict=True)
	if list_name:
		for content in list_name:
			if content.name:
				parent_groups = get_parent_item_groups(content.name)
				if parent_groups:
					parent = ''
					for i in range(0,len(parent_groups)):
						if i != len(parent_groups)-1:
							parent += str(parent_groups[i].category_name)+' >> '
						else:
							parent += str(parent_groups[i].category_name)
					content.parent_categories = parent  
	return {"list_name":list_name, "list_len":len(list_len)}


@frappe.whitelist()
def get_category_attributes(reference_doc, reference_fields, filters=None,page_no=1, page_len=20, 
															search_txt=None, search_field="name"):
	ProductAttribute = DocType('Product Attribute')
	start = (int(page_no) - 1) * int(page_len)
	user = frappe.session.user

	if isinstance(filters, str):
		filters = json.loads(filters)

	condition = ''
	if filters:
		category = ','.join(f'"{r["category"]}"' for r in filters)
	if search_txt:
		searchKey = f'%{search_txt}%'
		condition = f'{ProductAttribute}.{search_field} LIKE {frappe.qb.text(searchKey)}'

	list_name_query = (
		frappe.qb.from_(ProductAttribute)
		.select(ProductAttribute.name, ProductAttribute.attribute_name)
		.where(ProductAttribute.name != "")
	)

	if condition:
		list_name_query = list_name_query.where(frappe.qb.text(condition))

	list_name_query = (
		list_name_query.groupby(ProductAttribute.name, ProductAttribute.attribute_name)
		.limit(int(page_len))
		.offset(start)
	)

	list_name = list_name_query.run(as_dict=True)

	list_len_query = (
		frappe.qb.from_(ProductAttribute)
		.select(ProductAttribute.name, ProductAttribute.attribute_name)
		.where(ProductAttribute.name != "")
	)

	if condition:
		list_len_query = list_len_query.where(frappe.qb.text(condition))

	list_len_query = list_len_query.groupby(ProductAttribute.name, ProductAttribute.attribute_name)

	list_len = list_len_query.run(as_dict=True)

	return {"list_name": list_name, "list_len": len(list_len)}


@frappe.whitelist()
def get_returnpolicy_list(reference_doc, reference_fields, filters=None,page_no=1, 
								page_len=20, search_txt=None, search_field="name"):
	start = (int(page_no) - 1) * int(page_len)
	reference_field = json.loads(reference_fields)
	condition = ''

	if search_txt:
		searchKey = f'%{search_txt}%'
		condition = f'{search_field} LIKE {frappe.qb.text(searchKey)}'

	if filters:
		condition += ' AND ' + filters

	# fields = ','.join([x for x in reference_field])
	Doc = DocType(reference_doc)
	fields = [x for x in reference_field]

	if reference_doc == "Product":
		condition += ' AND is_active = 1 AND status = "Approved"'
	list_name_query = (
		frappe.qb.from_(Doc)
		.select(*fields)
		.where(Doc.name != "")
	)

	if condition:
		list_name_query = list_name_query.where(frappe.qb.text(condition))

	list_name_query = (
		list_name_query.limit(int(page_len)).offset(start)
	)

	list_name = list_name_query.run(as_dict=True)

	list_len_query = (frappe.qb.from_(Doc)
		.select(*fields)
		.where(Doc.name != ""))

	if condition:
		list_len_query = list_len_query.where(frappe.qb.text(condition))

	list_len = list_len_query.run(as_dict=True)
	return {"list_name": list_name, "list_len": len(list_len)}

@frappe.whitelist()
def get_specification_list(reference_doc, reference_fields, filters=None,page_no=1, page_len=20, 
															search_txt=None, search_field="name"):
	start = (int(page_no) - 1) * int(page_len)
	reference_field = json.loads(reference_fields)
	condition = ''
	if search_txt:
		searchKey = f'%{search_txt}%'
		condition += f'{search_field} LIKE {frappe.qb.text(searchKey)}'

	Doc = DocType(reference_doc)
	# fields = [Doc.field(x) for x in reference_field]
	list_name_query = (
		frappe.qb.from_(Doc)
		.select(Doc.name,Doc.attribute_name)
		.where(Doc.name != "")
	)

	if condition:
		list_name_query = list_name_query.where(frappe.qb.text(condition))

	list_name_query = list_name_query.limit(int(page_len)).offset(start)
	list_name = list_name_query.run(as_dict=True)
	list_len_query = (
		frappe.qb.from_(Doc)
		.select(Doc.name,Doc.attribute_name)
		.where(Doc.name != "")
	)

	if condition:
		list_len_query = list_len_query.where(frappe.qb.text(condition))

	list_len = list_len_query.run(as_dict=True)

	return {"list_name": list_name, "list_len": len(list_len)}

@frappe.whitelist()
def get_brand_list(reference_doc, reference_fields, filters=None, page_no=1, page_len=20, 
													search_txt=None, search_field="name"):
	start = (int(page_no) - 1) * int(page_len)
	reference_field = json.loads(reference_fields)
	fields = [DocType(reference_doc).field(x) for x in reference_field]
	condition = ''
	if search_txt:
		searchKey = f'%{search_txt}%'
		condition += f' {search_field} LIKE {frappe.qb.text(searchKey)}'
	Doc = DocType(reference_doc)

	list_name_query = (
		frappe.qb.from_(Doc)
		.select(*fields)
		.where(Doc.published == 1)
	)

	if condition:
		list_name_query = list_name_query.where(frappe.qb.text(condition))

	list_name_query = list_name_query.limit(start, int(page_len))

	list_name = list_name_query.run(as_dict=True)

	list_len_query = (
		frappe.qb.from_(Doc)
		.select(*fields)
		.where(Doc.published == 1)
	)

	if condition:
		list_len_query = list_len_query.where(frappe.qb.text(condition))

	list_len = list_len_query.run(as_dict=True)
	return {"list_name": list_name, "list_len": len(list_len)}

@frappe.whitelist()
def get_recent_products():
	try:
		Product = DocType('Product')
		roles = frappe.get_roles(frappe.session.user)
		roles = ','.join(f'"{r}"' for r in roles)
		recent_products_query = (
			frappe.qb.from_(Product)
			.select(
				Product.name, 
				Product.price, 
				Product.item, 
				Product.route, 
				Product.image.as_("detail_thumbnail")
			)
			.where((Product.is_active == 1) & (Product.status == "Approved"))
			.orderby(Product.creation, order=frappe.qb.terms.Order.desc)
			.limit(5)
		)
		recent_products = recent_products_query.run(as_dict=True)
		return recent_products
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'Error in doctype.product.product.get_recent_products')

@frappe.whitelist()
def insert_attribute_template(attribute,product_attr,message):
	try:
		ProductAttributeTemplate = DocType('Product Attribute Template')
		template_query = (
			frappe.qb.from_(ProductAttributeTemplate)
			.select(ProductAttributeTemplate.name)
			.where(ProductAttributeTemplate.attribute_id == attribute)
		)
		template = template_query.run(as_dict=True)
		if template:
			check_already_value = frappe.delete_doc("Product Attribute Template",template[0].name)
		attribute_option = frappe.new_doc('Product Attribute Template')
		attribute_option.attribute_id = attribute
		attribute_option.attribute_name = product_attr
		attribute_options = []
		attribute_option.save(ignore_permissions=True)
		if attribute_option:
			docs = json.loads(message)
			for item in docs:
				doc=frappe.get_doc({
					"doctype": "Attribute Option",
					"attribute":item['attribute'],
					"attribute_id":item['attribute_id'],
					"option_value":item['option_value'],
					"display_order":item['display_order'],
					"price_adjustment":item['price_adjustment'],
					"parent":attribute_option.name,
					"parenttype":'Product Attribute Template',
					"parentfield":'attribute_options',
					"parent_option":item['parent_option'],
					"is_pre_selected": item['is_pre_selected'] })
				doc.insert(ignore_permissions=True)
		return "Success"
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'Error in doctype.product.product.insert_attribute_template')

@frappe.whitelist()
def select_attribute_template(template_name,attribute,product,attribute_id):
	try:
		option_template = (
		frappe.qb.from_(DocType('Product Attribute Template'))
		.select('name', 'attribute_id', 'attribute_name')
		.where('name = %s', template_name)
		.run(as_dict=True)
	)
		if option_template:
			
			opt_temp = (
				frappe.qb.from_(DocType('Attribute Option'))
				.select('*')
				.where('parent = %s', option_template[0].name)
				.run(as_dict=True)
			)
			if opt_temp:
				for item in opt_temp:
					doc=frappe.get_doc({
						"doctype": "Product Attribute Option",
						"attribute":attribute,
						"attribute_id":attribute_id,
						"display_order":item.display_order,
						"price_adjustment":item.price_adjustment,
						"weight_adjustment":item.weight_adjustment,
						"attribute_color":item.attribute_color,
						"parent":product,
						"parenttype":'Product',
						"parentfield":'attribute_options',
						"option_value":item.option_value,
						"parent_option":item.parent_option,
						"is_pre_selected":item.pre_selected,
						"disable":item.disable,
						"available_datetime":item.available_datetime })
					doc.insert(ignore_permissions=True)
				result = (
					frappe.qb.from_(DocType('Product Attribute Option'))
					.select('*')
					.where('parent = %s', product)
					.where('attribute = %s', attribute)
					.where('attribute_id = %s', attribute_id)
					.run(as_dict=True)
				)
				return result
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'Error in doctype.product.product.select_attribute_template')


def delete_option(name):
	frappe.db.delete('Product Attribute Mapping', filters={'name': name})
	return "success"

@frappe.whitelist()
def get_order_settings():
	check_file_uploader = 0
	apps = frappe.get_installed_apps()
	if 'frappe_s3_attachment' in apps:
		s3_settings = frappe.get_single("S3 File Attachment")
		if s3_settings.aws_key and s3_settings.aws_secret and (not s3_settings.disable_s3_file_attachment or s3_settings.disable_s3_file_attachment==0):
			check_file_uploader = 1
	return {"order_settings":get_settings('Order Settings'),
			"s3_enable":check_file_uploader}


def get_role_list(doctype, txt, searchfield, start, page_len, filters):
	condition=''
	if filters.get('productId'):
		product = filters.get('productId')
		categories = (
			frappe.qb.from_(DocType('Product Category Mapping'))
			.select('category')
			.where('parent = %s', product)
			.run(as_dict=True)
		)
		category_list = {
			'category': ','.join(f'"{row["category"]}"' for row in categories)
		}
		if txt:
			condition += ' and (A.name like %(txt)s or A.attribute_name like %(txt)s)'      
		cat_list = '""'
		if category_list and category_list[0].category:
			cat_list = category_list[0].category
		doctype = filters.get('type')
		cat_list = ','.join(f'"{category}"' for category in filters.get('category_list', []))  # Assuming filters.get('category_list') returns a list of categories
		condition = filters.get('condition', '')  # Assuming condition is a string that gets appended to the query
		txt = filters.get('txt', '')
		query = (
			frappe.qb.from_(DocType(doctype).alias('A'))
			.left_join(DocType('Business Category').alias('C'), 'A.name = C.parent')
			.select('A.name', 'A.attribute_name')
			.where(
				frappe.qb.cond(
					'C.category IN %s', (tuple(filters.get('category_list', [])) if filters.get('category_list') else None)
				).or_('C.category IS NULL')
			)
			.run(as_dict=True)
		)
		filtered_results = [row for row in query if condition in row['attribute_name'] and txt in row['name']]
		result = filtered_results
	conditions = []
	role = DocType('Role')
	query = (
		frappe.qb.from_(role)
		.select(role.name)
		.where(role.disabled == 0)
		.where(role.name.notin(["System Manager", "Administrator"]))
	)
	query = query.where(getattr(role, searchfield).like(f"%{txt}%"))
	query = query.where(get_filters_cond(doctype, filters, conditions))
	query = query.where(get_match_cond(doctype))
	query = query.orderby(
		frappe.qb.case()
		.when(role.name.like(f"%{txt.replace('%', '')}%"), 
			  role.name.locate(f"%{txt.replace('%', '')}%"))
		.else_(99999)
		.desc(),
		role.idx.desc(),
		role.name
	)
	query = query.limit(start, page_len)
	results = query.run(as_dict=True)

	return results


def get_all_products_with_attributes(category=None, brand=None, item_name=None, active=None, featured=None,):
	try:
		lists=[]
		subcat=get_products(category=category, brand=brand, item_name=item_name, active=active, 
																			featured=featured)
		if subcat:
			for subsub in subcat:
				subsub.indent=0
				subsub.doctype="Product"
				lists.append(subsub)
				subsub.subsubcat=get_product_attributes(subsub.name)
				if subsub.subsubcat:
					for listcat in subsub.subsubcat:
						listcat.indent=1
						listcat.doctype="Product Attribute Option"
						lists.append(listcat)
		return lists
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.product.get_all_products_with_attributes") 
	

def get_product_attributes(name):   
	try:
		parent_name  = name
		attribute_option = DocType('Product Attribute Option')
		attribute_mapping = DocType('Product Attribute Mapping')
		query = (
			frappe.qb.from_(attribute_option)
			.join(attribute_mapping)
			.on(attribute_option.attribute_id == attribute_mapping.name)
			.select(
				attribute_option.name.as_('docname'),
				frappe.qb.concat_ws(' - ', attribute_mapping.attribute, attribute_option.parent_option).as_('name'),
				attribute_option.option_value.as_('item'),
				attribute_option.parent_option,
				attribute_option.price_adjustment.as_('price'),
				attribute_option.attribute
			)
			.where(attribute_mapping.parent == parent_name)
			.orderby(attribute_mapping.display_order, 'name')
		)
		
		results = query.run(as_dict=True)
		
		return results
		
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.product.get_product_attributes") 


def get_products(category=None, brand=None, item_name=None, active=None, featured=None):
	# Define DocTypes
	product = DocType('Product')
	product_category_mapping = DocType('Product Category Mapping')
	product_brand_mapping = DocType('Product Brand Mapping')
	
	# Base query
	query = frappe.qb.from_(product)
	
	# Joins and Filters
	if category or brand:
		if category:
			query = query.join(product_category_mapping).on(product.name == product_category_mapping.parent)
			query = query.where(product_category_mapping.category == category)
		if brand:
			query = query.join(product_brand_mapping).on(product.name == product_brand_mapping.parent)
			query = query.where(product_brand_mapping.brand == brand)
	
	# Adding filters
	if item_name:
		query = query.where(product.item.like(f"%{item_name}%"))
	if active is not None:
		active_value = 1 if active == "Yes" else 0
		query = query.where(product.is_active == active_value)
	if featured is not None:
		featured_value = 1 if featured == "Yes" else 0
		query = query.where(product.display_home_page == featured_value)
	
	# Select and Order
	query = (
		query.select(
			product.name,
			product.item,
			product.price,
			product.sku,
			product.old_price,
			product.stock,
			product.inventory_method,
			product.name.as_('docname'),
			frappe.qb.case()
			.when(product.is_active > 0, 'Yes')
			.else_('No')
			.as_('is_active'),
			frappe.qb.case()
			.when(product.display_home_page > 0, 'Yes')
			.else_('No')
			.as_('display_home_page'),
			product.name.as_('id'),
			product.name.as_('name1')
		)
	)
	
	# Execute the query
	results = query.run(as_dict=True)
	
	# Process images for each product
	for item in results:
		images = frappe.qb.from_('tabProduct Image').select('detail_thumbnail', 'detail_image').where('parent', item['name']).orderby('is_primary', 'DESC').run(as_dict=True)
		image_html = '<div class="row">'
		for img in images:
			if img.get('detail_thumbnail'):
				image_html += (
					f'<div class="col-md-4 popup" data-poster="{img["detail_image"]}" '
					f'data-src="{img["detail_image"]}" style="margin-bottom:10px;padding-left:0px;padding-right:0px;">'
					f'<a href="{img["detail_image"]}"><img class="img-responsive" id="myImg" '
					f'src="{img["detail_thumbnail"]}" onclick="showPopup(\'{img["detail_image"]}\')"></a></div>'
				)
		image_html += '</div>'
		item['image'] = image_html
	
	return results


def update_bulk_data(doctype,docname,fieldname,value):
	try:
		if doctype=="Product Attribute Option":
			if fieldname== "price":
				fieldname = "price_adjustment"
			if fieldname== "item":
				fieldname = "option_value"
		if doctype=="Product":
			if fieldname== "is_active" or fieldname== "display_home_page":
				if value=="Yes":
					value=1
				elif value=="No":
					value=0
		frappe.db.set_value(doctype,docname,fieldname,value)
		doc = frappe.get_doc(doctype,docname)
		return doc
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.product.update_bulk_data") 


def get_gallery_list(parent, name=None):
	product_image = DocType('Product Image')
	query = frappe.qb.from_(product_image)
	if parent:
		query = query.where(product_image.parent == parent)
	if name:
		query = query.where(product_image.name == name)
	query = (
		query.select('*')
		.orderby(product_image.idx)
	)
   
	results = query.run(as_dict=True)
	
	return results


def get_product_template(name=None):
	user = frappe.session.user
	if name:
		return frappe.get_doc("Product", name)
	return frappe.db.get_all("Product", fields=["*"], filters={"is_template":1})


def get_product_templates(name=None):
	if name:
		return frappe.get_doc("Product", name)
	return frappe.db.get_all("Product", fields=["*"], filters={"is_template":1})


def save_gallery_changes(data):
	doc = data
	if isinstance(doc, string_types):
		doc = json.loads(doc)
	ret = frappe.get_doc(doc.get('doc_type'),doc.get('doc_name'))
	ret.image_name= doc.get('img_name')
	ret.title= doc.get('img_caption')
	ret.save()
	return ret


def upload_img():
	try:
		files = frappe.request.files
		content = None
		dt = frappe.form_dict.doctype
		dn = frappe.form_dict.docname
		if 'files[]' in files:
			file = files['files[]']
			content = file.stream.read()
			filename = file.filename
		if content:
			ret = frappe.get_doc({
					"doctype": "File",
					"attached_to_name": dn,
					"attached_to_doctype": dt,
					"file_name":frappe.form_dict.name,
					"is_private": 0,
					"content": content})
			ret.save(ignore_permissions=True)
			frappe.db.commit()
			return ret.as_dict()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(),"Error in doctype.product.upload_img")


def get_query_condition(user):
	if not user: 
		user = frappe.session.user
	
			
def get_record_count(dt):
	doc = DocType(dt)
	query = frappe.qb.from_(doc)
	query = (
		query.select(
			frappe.qb.case()
			.when(doc.is_test_record == 0, 'actual')
			.else_('test')
			.as_('record_type'),
			frappe.qb.functions.Count('*').as_('count')
		)
		.groupby(doc.is_test_record)
	)
	results = query.run(as_dict=True)
	out = {}
	for item in results:
		out[item['record_type']] = item['count']
	return out


def clear_test_records(dt):
	test_records = frappe.db.get_all(dt, filters={'is_test_record': 1}, limit_page_length=500, 
														order_by='creation desc')
	docs = len(test_records)
	for i, item in enumerate(test_records):
		frappe.delete_doc(dt, item.name)
		frappe.publish_progress(float(i) * 100 / docs, title='Deleting sample records', 
													description='Please wait...')
	return {'status': 'Success'}



def product_detail_onscroll(productid, layout):
	from go1_commerce.go1_commerce.V2.product \
		import get_product_other_info, get_customer_recently_viewed_products
	contexts = {}
	catalog_settings=get_settings('Catalog Settings')
	contexts['catalog_settings']= catalog_settings
	contexts['currency']= frappe.cache().hget('currency','symbol')
	active_theme = None
	if not active_theme:
		theme = frappe.db.get_all('Web Theme', filters={'is_active': 1})
		if theme:
			active_theme = theme[0].name
	if active_theme:
		theme_settings = frappe.get_doc('Web Theme', active_theme)
	if theme_settings.grid_product_box:
		contexts['product_box'] = frappe.db.get_value('Product Box', theme_settings.grid_product_box, 'route')
	elif catalog_settings.product_boxes:
		contexts['product_box'] = frappe.db.get_value('Product Box', catalog_settings.product_boxes, 'route')
	else:
		contexts['product_box'] = None
	category_mapping = DocType('Product Category Mapping')
	category = DocType('Product Category')
	query = (
		frappe.qb.from_(category_mapping)
		.join(category)
		.on(category.name == category_mapping.category)
		.select(
			category_mapping.category,
			category_mapping.category_name,
			category.route.as_('route')
		)
		.where(category_mapping.parent == productid)
		.orderby(category_mapping.idx)
		.limit(1)
	)
	categories_list = query.run(as_dict=True)
	for category in categories_list:
		check_product_box = frappe.db.get_value("Product Category",category.category,
														'product_box_for_list_view')
		if check_product_box:
			contexts['product_box']=frappe.db.get_value('Product Box',check_product_box,'route')
		else:
			from go1_commerce.go1_commerce.v2.product \
																		import get_parent_categorie
			parent_categories = get_parent_categorie(category.category)
			for parent_category in parent_categories:
				check_product_box = frappe.db.get_value("Product Category",parent_category.name,\
																	'product_box_for_list_view')
				if check_product_box:
					contexts['product_box']=frappe.db.get_value('Product Box',check_product_box,'route')
	a_related_products = a_best_seller_category = a_products_purchased_together = []
	a_product_category = categories_list[0] if categories_list else {}
	if catalog_settings.customers_who_bought or catalog_settings.enable_best_sellers or \
														catalog_settings.enable_related_products:
		additional_info = get_product_other_info(productid)
		a_related_products = additional_info['related_products']
		a_best_seller_category = additional_info['best_seller_category']
		a_products_purchased_together = additional_info['products_purchased_together']
	contexts['related_products'] = a_related_products
	contexts['bestseller_item'] = a_best_seller_category
	contexts['show_best_sellers'] = a_products_purchased_together
	contexts['product_category'] = a_product_category
	contexts['recent_viewed_products'] = get_customer_recently_viewed_products()
	if layout=="Meat Layout":
		product_enquiry = get_product_scroll(productid, 1, 5)
		contexts['product_enquiry'] = product_enquiry
		contexts['approved_reviews'] = get_product_reviews_list(productid, 0, 10)
		contexts['approved_total_reviews'] = frappe.db.get_value('Product',productid,'approved_total_reviews')
		if catalog_settings.upload_review_images:
			review = DocType('Product Review')
			review_image = DocType('Review Image')
			query = (
				frappe.qb.from_(review)
				.join(review_image)
				.on(review.name == review_image.parent)
				.select(
					review_image.review_thumbnail,
					review_image.image,
					review_image.list_image,
					review_image.parent,
					review_image.name,
					review.product
				)
				.where(review.product == productid)
			)
			review_images = query.run(as_dict=True)
			contexts['review_img'] = review_images
		template = frappe.render_template(
						"/templates/pages/DetailPage/detailpage_otherinfo_meat.html", contexts)
	else:
		template = frappe.render_template(
						"/templates/pages/DetailPage/additional_product_info.html", contexts)
	return template

@frappe.whitelist()
def insert_product_attribute_and_options(doc):
	try:
		if isinstance(doc, string_types):
			doc = json.loads(doc)
		for item in doc:
			if item.get('product_attribute') and item.get('attribute'):
				if item.get('name'):
					attr = frappe.get_doc("Product Attribute Mapping", item.get('name'))
				else:
					attr = frappe.new_doc("Product Attribute Mapping")
					attr.parent = item.get('product')
					attr.parenttype = "Product"
					attr.parentfield = "product_attributes"
				attr.idx= item.get('idx')
				attr.attribute= frappe.db.get_value("Product Attribute",
										item.get('product_attribute'), "attribute_name")
				attr.control_type= item.get('control_type')
				attr.display_order= item.get('display_order')
				attr.is_required= item.get('is_required')
				attr.product_attribute= item.get('product_attribute')
				attr.quantity= item.get('quantity')
				if item.get('name'):
					attr.save()
					frappe.db.commit()
				else:
					attr.insert()
					frappe.db.commit()
				if item.get('attroptions'):
					for opt in item.get('attroptions'):
						if opt.get('name'):
							docs = frappe.get_doc("Product Attribute Option", opt.get('name'))
						else: 
							docs= frappe.new_doc("Product Attribute Option")
							docs.parent=attr.parent
							docs.parenttype='Product'
							docs.parentfield='attribute_options'
						docs.idx=opt.get('idx')
						docs.attribute=attr.product_attribute
						docs.attribute_id=attr.name
						docs.display_order=opt.get('display_order')
						docs.price_adjustment=opt.get('price_adjustment')
						docs.weight_adjustment=opt.get('weight_adjustment')
						docs.attribute_color=opt.get('attribute_color')
						docs.option_value=opt.get('option_value')
						docs.product_title=opt.get('product_title')
						docs.image=opt.get('image')
						docs.is_pre_selected=opt.get('is_pre_selected')
						docs.parent_option=opt.get('parent_option')
						docs.disable = int(opt.get('disable'))
						docs.ignore_permissions = True
						if int(opt.get('disable'))==1:
							docs.available_datetime = opt.get('available_datetime')
						if opt.get('name'):
							docs.save()
							frappe.db.commit()
						else:
							docs.insert()
							frappe.db.commit()
		return doc
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.product.insert_product_attribute_and_options") 


def get_doc_images(dt, dn):
	if dt == "Product Category":        
		category_mapping = DocType('Product Category Mapping')
		product = DocType('Product')
		query = (
			frappe.qb.from_(category_mapping)
			.join(product)
			.on(product.name == category_mapping.parent)
			.select(category_mapping.parent)
			.where(category_mapping.category == category_name)
			.groupby(product.name)
		)
		results = query.run(as_dict=True)
		products= [row['parent'] for row in results]
	elif dt == "Product Brand":
		brand_mapping = DocType('Product Brand Mapping')
		product = DocType('Product')
		query = (
			frappe.qb.from_(brand_mapping)
			.join(product)
			.on(product.name == brand_mapping.parent)
			.select(brand_mapping.parent)
			.where(brand_mapping.brand == brand_name)
			.groupby(product.name)
		)
		results = query.run(as_dict=True)
		products= [row['parent'] for row in results]
	elif dt == "Product":
		products = [dn]
	if products and len(products) > 0:
		product_list = ",".join(['"' + i + '"' for i in products])
		product_image = DocType('Product Image')
		query = (
			frappe.qb.from_(product_image)
			.select(
				product_image.list_image,
				product_image.detail_thumbnail.as_('thumbnail'),
				product_image.product_image
			)
			.where(product_image.parent.isin(product_list))
			.orderby(product_image.idx)
		)
		results = query.run(as_dict=True)
		return results
	return []



def get_attributes_combination(product):
	combination=frappe.db.get_all('Product Variant Combination',filters={'parent':product},fields=['*'])
	productdoc=frappe.db.get_all('Product',fields=['*'],filters={'name':product})
	return combination,productdoc



def get_attributes_name(attribute_id,product):
	combination=frappe.db.get_all('Product Variant Combination',
							   filters={
								   'parent':product,
								   'attribute_id':attribute_id.replace(",","\n")if attribute_id else "",},
								   fields=['*'])  
	return combination


def create_product(source_name, target_doc=None):
	doc = get_mapped_doc('Product', source_name, {
		'Product': {
			'doctype': 'Product'
		},
		'Product Image': {
			'doctype': 'Product Image',
		},
		'Product Video': {
			'doctype': 'Product Video',
		},
		'Product Category Mapping': {
			'doctype': 'Product Category Mapping',
		},
		'Product Brand Mapping': {
			'doctype': 'Product Brand Mapping',
		},
		'Product Attribute Mapping': {
			'doctype': 'Product Attribute Mapping',
		},
		'Product Variant Combination': {
			'doctype': 'Product Variant Combination',
		},
		'Product Specification Attribute Mapping': {
			'doctype': 'Product Specification Attribute Mapping',
		},
		'Product Search Keyword': {
			'doctype': 'Product Search Keyword',
		},
	}, target_doc)
	return doc


def delete_current_img(childname, doctype):
	try:
		image_doc = 'Product Image'
		if childname:
			getimg = frappe.db.get_all(image_doc, fields=['*'],
					filters={'name': childname})
			if getimg:
				img = frappe.get_doc(image_doc, childname)
				if doctype == 'Product':
					from go1_commerce.utils.utils import delete_file
					filename = img.product_image
					delete_file(img.list_image)
					delete_file(img.detail_thumbnail)
					delete_file(img.detail_image)
					delete_file(img.email_thumbnail)
					delete_file(img.mini_cart)
					delete_file(img.cart_thumbnail)
				img.delete()
				if getimg[0].is_primary == 1 and image_doc == 'Product Image':
					frappe.db.set_value(getimg[0].parenttype,
										getimg[0].parent, 'image', '')
				if filename:
					getimg1 = frappe.get_list('File', fields=['*'],
												filters={'file_url': filename})
					if getimg1:
						fle = frappe.get_doc('File', getimg1[0].name)
						fle.delete()
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'delete_current_img')


def check_exist_sku(doc):
	doc = json.loads(doc)
	if doc.get("sku"):
		check_other = frappe.db.get_all("Product",filters={"sku":doc.get("sku"),
										"name":("!=",doc.get("name")),"status":"Approved"})
		return check_other
	return []


def update_whoose_search(self):
	try:
		delete_whoose_data(self)
		if self.product_categories:
			cat_route = frappe.db.get_value("Product Category",self.product_categories[0].category,"route")
			from go1_commerce.go1_commerce.v2.whoosh \
				import insert_update_search_data
			send__data = []
			dict__ = {}
			if self.is_active==1 and self.status=="Approved":
				dict__['name'] = self.name
				dict__['product_id'] = self.name
				dict__['title'] = self.item
				dict__['route'] = cat_route + "/" +self.route if cat_route else self.route
				dict__['type'] = "Product"
				dict__['search_keyword'] = self.item
				dict__['product_image'] = self.image
				send__data.append(dict__)
				dict__ = {}
				if self.search_keyword:
					for s__ in self.search_keyword:
						dict__['name'] = s__.name
						dict__['title'] = self.item
						dict__['product_id'] = self.name
						dict__['route'] = cat_route + "/" +self.route if cat_route else self.route
						dict__['type'] = "Product"
						dict__['product_image'] = self.image
						dict__['search_keyword'] = s__.search_keywords
						send__data.append(dict__)
						dict__ = {}
			insert_update_search_data(send__data)
	except Exception:
		frappe.log_error(title="Error in update product search data",message = frappe.get_traceback())

@frappe.whitelist()
def delete_combination(dt, dn):
	frappe.delete_doc(dt, dn)
	frappe.db.commit()

def update_attr_options():
	attribute_option = DocType('Product Attribute Option')
	product = DocType('Product')
	query = (
		frappe.qb.from_(attribute_option)
		.join(product)
		.on(product.name == attribute_option.parent)
		.select(product.name)
		.where(
			(attribute_option.attribute_id.isnull() | (attribute_option.attribute_id == ''))
		)
		.groupby(product.name)
	)
	p_list = query.run(as_dict=True)
	for p in p_list:
		p_doc = frappe.get_doc("Product",p.name)
		if p_doc.attribute_options:
			for x in p_doc.attribute_options:
				if not x.unique_name:
					frappe.db.set_value("Product Attribute Option",x.name,"unique_name",
						 p_doc.scrub(frappe.db.get_value("Product Attribute",
									   x.attribute,"attribute_name").lstrip())+"_"+p_doc.scrub(
										   x.option_value.lstrip()))
				if not x.attribute_id:
					p_attr_id = frappe.db.get_all("Product Attribute Mapping",
								   filters={"parent":p_doc.name,"product_attribute":x.attribute})
					if p_attr_id:
						x.attribute_id = p_attr_id[0].name
			p_doc.save(ignore_permissions=True)


def update_product_variant_combinations():
	p_list = frappe.db.get_all("Product",filters={"has_variants":1})
	for p in p_list:
		p_doc = frappe.get_doc("Product",p.name)
		if not p_doc.variant_combination:
			product_attributes = []
			for attr in p_doc.product_attributes:
				product_attribute = {"product": p_doc.name,
									"attribute": frappe.db.get_value("Product Attribute",\
													attr.attribute,'attribute_name'),
									"control_type": "Radio Button List",
									"display_order": attr.idx,
									"is_required": "Yes",
									"product_attribute": attr.attribute,
									"name":attr.name }
				product_attribute["attroptions"] = []
				options = frappe.db.get_all("Product Attribute Option",fields=['*'],
								filters={'parent':p_doc.name,'attribute':attr.product_attribute,
								'attribute_id':attr.name},order_by='display_order',limit_page_length=50)  
				for p_attr_opt_doc in options:
					product_attribute["attroptions"].append(p_attr_opt_doc)
				if product_attribute["attroptions"]:
					product_attributes.append(product_attribute)
			combinations = generate_combinations(p_doc.name,product_attributes)
			if combinations:
				p_doc.variant_combination=[]
			frappe.log_error(title=p_doc.name,message=combinations)
			for c in combinations:
				p_doc.append("variant_combination",{
					"product_title": c.get("product_title"),
					"attributes_json": json.dumps(c.get("attributes_json")),
					"attribute_id": c.get("attribute_id"),
					"attribute_html": c.get("attribute_html"),
					"sku": c.get("sku"),
					"show_in_market_place": 1,
					"price": p_doc.price})
			if combinations:
				p_doc.save(ignore_permissions=True)
				frappe.db.commit()


def generate_combinations(product_id,attributes):
	options=[]
	all_options=[]
	response = attributes
	p_combinations = frappe.db.get_all("Product Variant Combination",
									filters={"parent":product_id},fields=['attribute_id'])
	for item in response:
		if item.get('attroptions'):
			li=[x.get('option_value') for x in item.get('attroptions')]
			options.append(li)
		all_options+=item.get('attroptions')
	import itertools
	combination=list(itertools.product(*options))
	lists=[]
	sku_no = 1
	sku_seq = frappe.db.get_all("Product Variant Combination",
							 filters={"parent":product_id},fields=['sku'],
							 order_by="sku desc",limit_page_length=1)
	if sku_seq:
		if sku_seq[0].sku:
			l_sku = sku_seq[0].sku
			sku_no = int(l_sku[-3:])+1
	for item in combination:
		html=''
		ids=''
		price=0
		variant_text = ""
		attributes_json = []
		for li in item:
			check=next((x for x in all_options if x.get('option_value')==li),None)
			if check and check.get('name'):
				attribute_name = frappe.db.get_value("Product Attribute", 
										 check.get('attribute'), "attribute_name")
				ids+=check.get('name')+'\n'
				html+='<div data-name="'+str(ids)+'" class="btn btn-default btn-xs btn-link-to-form" \
					style="border: 1px solid #d1d8dd;margin: 2px;min-width: 50px;text-align: left;">\
					<p style="text-align: left;margin: 0px;font-size: 11px;">'+attribute_name+'</p> \
						<span style="font-weight: 700;">'+li+'</span></div>'
				price+=check.get('price_adjustment')
				variant_text+= li+" / "
				attributes_json.append(check.get('name'))
		if ids:
			if not any(obj['attribute_id'] == ids for obj in p_combinations):
				v_sku = product_id.split("ITEM-")[1]+'%03d' % sku_no
				p_title = frappe.db.get_value("Product",product_id,"item")+" - "+variant_text[:-1]
				lists.append({'sku':v_sku,'product_title':p_title,
							'attribute_html':html,'attribute_id':ids, 'stock': 1,
							'price':price, 'attributes_json': attributes_json})
				sku_no = sku_no+1
	return lists


def update_category_data_json(doc):
	from frappe.utils import get_files_path	
	path = get_files_path()
	if doc.product_categories:
		for x in doc.product_categories:
			cat_route = frappe.db.get_value("Product Category",x.category,"route")
			cat_route = cat_route.replace("/","-")
			if not os.path.exists(os.path.join(path,cat_route+"-"+x.category)):
				frappe.create_folder(os.path.join(path,cat_route+"-"+x.category))
			from go1_commerce.go1_commerce.v2.category \
				import get_category_filters_json
			filters_resp = get_category_filters_json(category=x.category)
			if filters_resp.get("attribute_list"):
				with open(os.path.join(path,(cat_route+"-"+x.category), 'attributes.json'), "w") as f:
					content = json.dumps(filters_resp.get("attribute_list"), separators=(',', ':'))
					f.write(content)
			if filters_resp.get("brand_list"):
				with open(os.path.join(path,(cat_route+"-"+x.category), 'brands.json'), "w") as f:
					content = json.dumps(filters_resp.get("brand_list"), separators=(',', ':'))
					f.write(content)
			if filters_resp.get("category_list"):
				with open(os.path.join(path,(cat_route+"-"+x.category), 'categories.json'), "w") as f:
					content = json.dumps(filters_resp.get("category_list"), separators=(',', ':'))
					f.write(content)


def update_attr_options_unique_names():
	p_list = frappe.db.get_all("Product",filters={"has_variants":1})
	for p in p_list:
		p_doc = frappe.get_doc("Product",p.name)
		if p_doc.attribute_options:
			for x in p_doc.attribute_options:
				frappe.db.set_value("Product Attribute Option",x.name,
						"unique_name",p_doc.scrub(frappe.db.get_value("Product Attribute",
						x.attribute,"attribute_name").lstrip())+"_"+p_doc.scrub(x.option_value.lstrip()))
			frappe.db.commit()


def delete_whoose_data(self):
	try:
		from go1_commerce.go1_commerce.v2.whoosh \
			import remove_deleted_data
		send__data = []
		send__data.append(self.name)
		if self.search_keyword:
			for s__ in self.search_keyword:
				send__data.append(s__.name)
		remove_deleted_data(send__data)
	except Exception:
		frappe.log_error(title="Error in delete product search data",message = frappe.get_traceback())
