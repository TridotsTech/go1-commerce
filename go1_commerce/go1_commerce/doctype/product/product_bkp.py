# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, os, re, json
from frappe.website.website_generator import WebsiteGenerator
from frappe.utils import touch_file, encode
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, getdate, nowdate, get_url, add_days, now
from datetime import datetime
from pytz import timezone
from frappe.utils import strip, get_files_path
import pytz
from urllib.parse import unquote
from six import string_types
from go1_commerce.go1_commerce.api import get_today_date
from go1_commerce.utils.setup import get_settings_from_domain, get_settings_value_from_domain
from frappe.desk.reportview import get_match_cond, get_filters_cond

class Product(WebsiteGenerator):
	

	website = frappe._dict(
		condition_field = "show_in_website",
		no_cache = 1
	)

	def autoname(self): 
		naming_series="ITEM-"
		if self.restaurant:
			abbr=frappe.db.get_value('Business',self.restaurant,'abbr')
			if abbr:
				naming_series+=abbr+'-'
		self.naming_series=naming_series
		from frappe.model.naming import make_autoname
		self.name = make_autoname(naming_series+'.#####', doc=self)

	def validate(self):	
		catalog_settings=get_settings_from_domain('Catalog Settings', business=self.restaurant)
		self.make_route()
		
		self.check_commission()
		self.validate_sku()
		self.insert_search_words()
		self.validate_order_qty()
		if not self.barcode:
			self.check_barcode()
		if self.restaurant and not self.business_email_id:
			self.business_email_id =frappe.db.get_value('Business',self.restaurant,'contact_email')
		if self.old_price and self.old_price>0 and self.price:
			if self.old_price<self.price:
				frappe.throw(_('Old Price must be greater than the Product Price'))
		
				
		if self.status!='Approved':
			self.status='Approved'
		
		check_attr_combination_price(self)
		self.validate_attribute_options()
		if self.status == 'Waiting for Product Approval':
			self.check_auto_update()
		if self.enable_preorder_product==1:
			if self.percentage_or_amount == 'Preorder Percentage':
				if flt(self.preorder_percent)>=100:
					frappe.throw(_('Please enter percentage below 100'))
			if self.percentage_or_amount == 'Preorder Amount':
				if flt(self.preorder_amount)>=flt(self.price):
					frappe.throw(_('Please enter amount below product price'))
		if not self.meta_title:
			self.meta_title = self.item
		if not self.meta_keywords:
			self.meta_keywords = self.item.replace(" ", ", ")
		if not self.meta_description:
			self.meta_description = "About: {0}".format(self.item)

	def check_auto_update(self):
		auto_approval = frappe.db.get_single_value('Core Settings', 'auto_product_approval')
		if auto_approval:
			self.status = 'Approved'

	def insert_search_words(self):
		try:
			# Updated by suguna on 10/08/20
			words=''
			data=''
			catalog_settings=get_settings_from_domain('Catalog Settings', business=self.restaurant)
			if catalog_settings.search_fields:
				count=1
				for s in catalog_settings.search_fields:
					lenght = len(catalog_settings.search_fields)
					if(len(catalog_settings.search_fields)==1):
						data += s.fieldname
					else:
						if(count != lenght):
							data += s.fieldname+','
						else:
							data += s.fieldname
					count=count+1
				products = frappe.db.sql('''select {0} from `tabProduct` where name=%(name)s'''.format(data),{'name':self.name},as_dict=1)
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
			frappe.log_error(frappe.get_traceback(), "ecommerce_bussiness_store.ecommerce_bussiness_store.product.insert_search_words")

	def check_barcode(self):
		try:
			catalog_settings=get_settings_from_domain('Catalog Settings', business=self.restaurant)
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
			frappe.log_error(frappe.get_traceback(), "ecommerce_bussiness_store.ecommerce_bussiness_store.product.check_barcode")   
	def validate_stock(self):
		if self.stock:
			if self.stock < 0:
				frappe.throw(_('Stock cannot be negative value'))
		if self.inventory_method == 'Track Inventory By Product Attributes':
			if not self.variant_combination:
				frappe.throw(_('Please create attribute combinations'))
	def validate_sku(self): 
		if self.sku:    
			check=frappe.db.get_all('Product',filters={'name':('!=',self.name),'sku':self.sku,'restaurant':self.restaurant})
			if check:
				frappe.throw(_('SKU must be unique value'))

	def validate_order_qty(self):
		if not self.minimum_order_qty>0:
			frappe.throw(_("Minimum order quantity should be greater than zero"))
		if not self.maximum_order_qty>=self.minimum_order_qty:
			frappe.throw(_("Maximum order quantity should be greater than minimum order quantity"))

	def make_route(self):
		if not self.route:
			self.route = self.scrub(self.item)
			check_category_exist = frappe.get_list('Product Category', fields=["route"], filters={"route": self.route},ignore_permissions =True)
			check_route = self.scrub(self.item) + "-" + str(len(check_category_exist))
			routes='"{route}","{check_route}"'.format(route=self.route,check_route=check_route)
			check_exist = frappe.db.sql("""select name from `tabProduct` where route in ({routes}) and name!='{name}'""".format(routes=routes,name=self.name),as_dict=1)
			if check_exist and len(check_exist) > 0:
				st = str(len(check_exist))
				if self.restaurant:
					abbr = frappe.db.get_value('Business', self.restaurant, 'abbr')
					if abbr:
						st = abbr.lower()
				self.route = self.scrub(self.item) + "-" + st
			if check_category_exist and len(check_category_exist) >0:
				st = str(len(check_exist)+len(check_category_exist))
				self.route = self.scrub(self.item) + "-" + st


	def on_update(self):
		
		self.get_product_availability()
		media_settings=get_settings_from_domain('Media Settings', business=self.restaurant)
		category=None
		if self.product_categories: category=sorted(self.product_categories,key=lambda x:x.idx,reverse=False)[0].category
		list_size=media_settings.list_thumbnail_size
		if category:
			size=frappe.db.get_value('Product Category',category,'product_image_size')
			if size and int(size) > 0:
				list_size=size
		

		if self.product_images:
			cover_image=next((x for x in self.product_images if x.is_primary==1),None)
			if not cover_image:
				frappe.db.set_value('Product Image', self.product_images[0].name,'is_primary',1)
			if self.image:
				check_image = next((x for x in self.product_images if x.cart_thumbnail == self.image), None)
				if not check_image:
					self.image = None
			if not self.image:
				if cover_image:
					frappe.db.set_value('Product',self.name,'image',cover_image.cart_thumbnail)
				else:
					frappe.db.set_value('Product',self.name,'image',self.product_images[0].cart_thumbnail)
			else:
				'''set primary image value-by siva(Jan ,8,20)'''
				if self.image.startswith("/files"):
					file_name = self.image.split("/files/")[-1]
					if not os.path.exists(get_files_path(frappe.as_unicode(file_name.lstrip("/")))):
						frappe.db.set_value('Product',self.name,'image',"")
				
		if not self.return_policy:
			self.return_description = ""
		
	def add_price(self, price_list=None):
		'''Add a new price'''
		catalog_settings = get_settings_from_domain('Catalog Settings')
		if not price_list:
			price_list = (frappe.db.get_value('Price List', _('Standard Selling')))
			if price_list and (self.inventory_method=="Track Inventory" or self.inventory_method=="Dont Track Inventory"):
				if len(self.get("pricing_details"))>0:
					for item in self.get("pricing_details"):
						if not frappe.db.exists("Product Price",{"price_list": price_list,"business": item.vendor_id,"product": self.name,"price_model":"Standard Pricing"}):
							item_price = frappe.get_doc({
								"doctype": "Product Price",
								"price_list": price_list,
								"product": self.name,
								"price_model":"Standard Pricing",
								"business": item.vendor_id,
								"currency": catalog_settings.default_currency,
								"price": item.price
							})
							item_price.insert()
						else:
							exist = frappe.db.get_value("Product Price",{"price_list": price_list,"business": item.vendor_id,"product": self.name,"price_model":"Standard Pricing"})
							item_price = frappe.get_doc("Product Price",exist)
							item_price.price = item.price
							item_price.save()
							frappe.db.commit()
				else:   
					if not frappe.db.exists("Product Price",{"product": self.name}):
						item_price = frappe.get_doc({
							"doctype": "Product Price",
							"price_list": price_list,
							"product": self.name,
							"price_model":"Standard Pricing",
							"currency": catalog_settings.default_currency,
							"price": self.price
						})
						item_price.insert()
					else:
						exist = frappe.db.get_value("Product Price",{"product": self.name})
						item_price = frappe.get_doc("Product Price",exist)
						item_price.price = item.price
						item_price.save()
						frappe.db.commit()

			if price_list and self.get("variant_combination") and self.inventory_method=="Track Inventory By Product Attributes":
				if frappe.db.exists("Product Price",{"product": self.name, "attribute_id": ""}):
					pname = frappe.db.get_value("Product Price",{"product": self.name, "attribute_id": ""})
					product_doc = frappe.get_doc('Product Price',pname)
					product_doc.delete();
				if len(self.get("vendor_variant_pricing"))>0:
					frappe.log_error("pricing",self.get("vendor_variant_pricing"))
					for item in self.get("vendor_variant_pricing"):
						frappe.log_error("item",item)
						if not frappe.db.exists("Product Price",{"price_list": price_list,"business": item.vendor_id,"product": self.name,"attribute_id": attr.attribute_id,"price_model":"Standard Pricing", "attribute_id": attr.attribute_id}):
							item_price = frappe.get_doc({
								"doctype": "Product Price",
								"price_list": price_list,
								"product": self.name,
								"attribute_id": attr.attribute_id,
								"price_model":"Standard Pricing",
								"business": item.vendor_id,
								"currency": catalog_settings.default_currency,
								"price": item.price
							})
							item_price.insert()
						else:
							exist = frappe.db.get_value("Product Price",{"price_list": price_list,"business": item.vendor_id,"product": self.name,"attribute_id": attr.attribute_id,"price_model":"Standard Pricing", "attribute_id": attr.attribute_id})
							item_price = frappe.get_doc("Product Price",exist)
							item_price.price = item.price
							item_price.save()
							frappe.db.commit()
				else:
					for attr in self.get("variant_combination"):
						frappe.log_error("attr",attr)
						if not frappe.db.exists("Product Price",{"price_list": price_list,"product": self.name,"price_model":"Standard Pricing", "attribute_id": attr.attribute_id}):
							if not frappe.db.exists("Product Price",{"product": self.name, "attribute_id": attr.attribute_id}):
								item_price = frappe.get_doc({
									"doctype": "Product Price",
									"price_list": price_list,
									"product": self.name,
									"attribute_id": attr.attribute_id,
									"price_model":"Standard Pricing",
									"currency": catalog_settings.default_currency,
									"price": self.price
								})
								item_price.insert()
							else:
								exist = frappe.db.get_value("Product Price",{"product": self.name, "attribute_id": attr.attribute_id})
								item_price = frappe.get_doc("Product Price",exist)
								item_price.price = item.price
								item_price.save()
								frappe.db.commit()

	def validate_attribute_options(self):
		if self.product_attributes:
			lists = ''
			for item in self.product_attributes:
				if not item.get('__islocal'):
					check_attributes = frappe.db.sql('''select name from `tabProduct Attribute Option` where attribute_id = %(name)s''',{'name': item.name})
					if not check_attributes and (item.control_type != "Text Box" and item.control_type != "Multi Line Text"):
						lists += '<li>{0}</li>'.format(item.product_attribute)
			if lists and lists != '' :
				frappe.msgprint(_('Please add attribute options for the following.<br><ol style="margin-top: 10px;">{0}</ol>').format(lists))

	def after_insert(self):
		pass

	def get_product_availability(self):
		if self.stock and self.stock > 0 and self.inventory_method == 'Track Inventory':
			notification_product = frappe.db.get_all("Product Availability Notification",fields=['product','is_email_send','name','attribute_id'], filters={'is_email_send': 0, 'product': self.name})
			if notification_product:
				for stock_avail in notification_product:
					availability = frappe.get_doc("Product Availability Notification",stock_avail.name)
					availability.is_email_send=1
					availability.save(ignore_permissions=True)
		if self.inventory_method == 'Track Inventory By Product Attributes' and len(self.variant_combination)>0:
			notification_product = frappe.db.get_all("Product Availability Notification",fields=['product','is_email_send','name','attribute_id'], filters={'is_email_send': 0, 'product': self.name})
			if notification_product:
				for stock_avail in notification_product:
					if stock_avail.attribute_id:
						attribute_id =stock_avail.attribute_id.strip()
						check_data = next((x for x in self.variant_combination if x.attribute_id == stock_avail.attribute_id), None)
						if check_data and check_data.stock > 0:
							availability = frappe.get_doc("Product Availability Notification",stock_avail.name)
							availability.is_email_send=1
							availability.save()
	def get_context(self, context):
		try:
			page_builder = frappe.db.get_all("Web Page Builder",filters={"published":1,"document":"Product"},fields=['file_path'])
			if page_builder:
				context.template = page_builder[0].file_path
			from go1_commerce.go1_commerce.api import get_bestsellers,get_product_price,get_category_products,get_category_detail,get_enquiry_product_detail,get_customer_recently_viewed_products, get_product_other_info,get_parent_categorie
			product_brands = []
			product_attributes = []
			if self.status != 'Approved':
				frappe.local.flags.redirect_location = '/404'
				raise frappe.Redirect
			catalog_settings = context.catalog_settings
			brand_cond = ''
			business = None
			if context.get('web_domain') and context.web_domain.business:
				business = context.web_domain.business
				if not self.restaurant or self.restaurant != business:
					frappe.local.flags.redirect_location = '/404'
					raise frappe.Redirect
			if business:
				brand_cond = ' and b.business = "{0}"'.format(business) 
			context.brands = frappe.db.sql('''select b.name, b.brand_name, b.brand_logo, b.route, b.warranty_information as warranty_info, b.description from `tabProduct Brand` b inner join `tabProduct Brand Mapping` pbm on b.name = pbm.brand where pbm.parent = %(parent)s {condition} group by b.name order by pbm.idx'''.format(condition=brand_cond), {'parent': self.name}, as_dict=1) 
			self.get_product_reviews(context)
			productattributes = frappe.db.get_all('Product Attribute Mapping',fields=["*"], filters={"parent":self.name},order_by="display_order",limit_page_length=50)
			image = []
			video_list = []
			if self.product_images:
				for item in self.product_images:
					image.append({"original_image":item.product_image,"product_image":item.detail_image,"detail_image":item.detail_image,"detail_thumbnail":item.detail_thumbnail})
			img=None
			if self.product_images:
				context.og_image = self.product_images[0].product_image
			path1 = frappe.local.request.path
			context.page_url = get_url() + path1
			attr_product_title = ''
			size_chart = ''
			size_chart_params = ''
			chart_name = ''
			size_charts = ''
			for attribute in productattributes:
				if attribute.size_chart:
					chart_name = attribute.size_chart
					size_charts = frappe.db.get_all('Size Chart',filters={'name':attribute.size_chart},fields=['size_chart_image','name'])
					size_chart = frappe.db.sql('''select TRIM(attribute_values) as attribute_values,chart_title,chart_value,name from `tabSize Chart Content` where parent=%(parent)s order by display_order''',{'parent':attribute.size_chart},as_dict=1)
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
				options = frappe.db.get_all("Product Attribute Option",fields=['*'],filters={'parent':self.name,'attribute':attribute.product_attribute,'attribute_id':attribute.name},order_by='display_order',limit_page_length=50)			
				for op in options:
					txt = '"%' + op.name + '%"'
					varients = frappe.db.sql("""select name, attributes_json, attribute_id, option_color, parent, image_list from `tabProduct Variant Combination` where parent="{product}" and attribute_id like {txt} order by idx asc""".format(product=self.name, txt=txt), as_dict=1)
					if op.is_pre_selected == 1:
						if op.product_title and op.product_title != '-':
							attr_product_title = op.product_title
					if op.image_list:
						images = json.loads(op.image_list)
						if len(images) > 0:
							images = sorted(images, key=lambda x: x.get('is_primary'), reverse=True)
							op.image_attribute = images[0].get('thumbnail')
							if op.is_pre_selected == 1:						
								image = []
								for im in images:
									image.append({'original_image': im.get('image'), 'detail_image': im.get('detail_thumbnail'), 'detail_thumbnail': im.get('thumbnail')})
					if len(varients) >0:
						combination_img = varients[0]
						if combination_img.image_list:
							images = json.loads(combination_img.image_list)
							if len(images) > 0:
								images = sorted(images, key=lambda x: x.get('is_primary'), reverse=True)
								image=[]
								for im in images:
									image.append({'original_image': im.get('image'), 'detail_image': im.get('detail_thumbnail'), 'detail_thumbnail': im.get('thumbnail')})

						attribute_video = frappe.get_all('Product Attribute Option Video',filters={"option_id":combination_img.name},fields=["youtube_video_id","video_type"])
						if attribute_video:
							for video in attribute_video:
								if video.youtube_video_id:
									video_list.append({'video_link':video.youtube_video_id,'video_type':video.video_type})
					if op.is_pre_selected == 1:
						attribute_video = frappe.get_all('Product Attribute Option Video',filters={"option_id":op.name},fields=["youtube_video_id","video_type"])
						if attribute_video:
							for video in attribute_video:
								if video.youtube_video_id:
									video_list.append({'video_link':video.youtube_video_id,'video_type':video.video_type})	

				product_attributes.append({"attribute":attribute.product_attribute,"attribute_name":attribute.attribute,"is_required":attribute.is_required,"control_type":attribute.control_type,"attribute_chart":attribute.size_chart,"options":options,"size_charts":size_charts,'size_chart':size_chart,'size_chart_params':size_chart_params})
			context.product_title = attr_product_title
			context.attr_image = image
			context.sel_image = img
			image_position = ''
			if catalog_settings.product_thumbnail_image_position:
				context.image_position = catalog_settings.product_thumbnail_image_position
			context.catalog_settings = catalog_settings
			context.attributes=product_attributes
			context.type_of_category = get_enquiry_product_detail(self.name)
			specification_group = []
			specification_attribute = frappe.db.sql_list('''select distinct sam.spec_group_name,sg.display_order from `tabSpecification Group` sg inner join `tabProduct Specification Attribute Mapping` sam on sg.name=sam.spec_group_name1 where sam.parent=%(name)s order by sam.idx''',{'name':self.name})
			if specification_attribute:
				for item in specification_attribute:
					groups = frappe.db.get_all('Product Specification Attribute Mapping',fields=['specification_attribute','options'], filters={"parent":self.name,'spec_group_name':item},order_by='idx')
					specification_group.append({"name":item, "groups":groups})
			context.specification_attribute_grouping = specification_group
			
			
			demovideo = frappe.db.get_all('Product Video',fields=["*"], filters={"parent":self.name},order_by="display_order")
			context.demo_video = demovideo
			if len(video_list)>0:
				context.demo_video = video_list
			frappe.log_error(context.demo_video, "context.demo_video")
			if frappe.session.user != 'Guest':
				update_customer_recently_viewed(self.name)
			context.page_path = get_url()
			path = frappe.local.request.path
			context.currenturl = get_url() + path	

			price_details = get_product_price(self)
			orgprice = self.price
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

			if self.meta_keywords:
				context.meta_keywords=self.meta_keywords if self.meta_keywords else self.item
			else:
				context.meta_keywords = context.catalog_settings.meta_keywords
			allow_review=0
			if frappe.session.user!='Guest':
				allow_review=1
			else:
				if context.catalog_settings.allow_anonymous_users_to_write_product_reviews:
					allow_review=1
			context.allow_review=allow_review

			
			ziprange=frappe.request.cookies.get("ziprange")
			context.ziprange=ziprange
			categories_list = frappe.db.sql('''select category, category_name from `tabProduct Category Mapping` where parent = %(parent)s order by idx limit 1''',{'parent':self.name}, as_dict=1)
			
			if categories_list:
				product_category=frappe.db.get_all('Product Category',fields=["*"], filters={"name":categories_list[0].category},order_by="display_order",limit_page_length=1)
				context.item_categories=product_category[0]
			vendor=frappe.db.sql('''select p.restaurant, b.route, b.restaurant_name from `tabProduct` p, `tabBusiness` b where b.name = p.restaurant and p.restaurant=%(restaurant)s''',{'restaurant':self.restaurant}, as_dict=1)      
			if vendor:
				context.vendor=vendor[0]
			self.check_book_app(context)
			self.set_tax_rate(context,catalog_settings,orgprice)
			if context.map_api:
				self.check_website_product_available(context)
			product_enquiry = get_product_scroll(self.name, 1, 5)
			context.product_enquiry = product_enquiry
			if self.restaurant:
				business = frappe.get_doc("Business", self.restaurant)
				context.business_route = business.route
			context.mobile_page_title = self.item

			if 'temple' in frappe.get_installed_apps():
				from temple.temple.api import get_related_events
				if self.product_categories:
					for x in self.product_categories:
						if "Upcoming Events" in x.category_name:
							context.upcoming_events_flag = 1	
							related_events = get_related_events(self.name)
							for i in related_events:
								if i.full_description:
									full_description = str(remove_html_tags(i.full_description))
									i.full_description = full_description[:95] + '...'
							context.related_events = related_events
						elif "Saree Sponsorship" in x.category_name:
							context.saree_sponsorship_flag = 1
							if self.full_description:
								context.full_description = self.full_description
						elif "Poojas" in x.category_name:
							context.poojas_flag = 1
			control_type_check = 0
			if self.product_attributes:
				for item in self.product_attributes:
					if not "Table" in item.control_type:
						context.control_type_check = 1

			farming_practises = None

			check_field = frappe.db.sql(''' SELECT *  FROM `tabCustom Field` where dt='Product Category' and fieldname='farming_practises' ''',as_dict=1)
			if check_field:
				if categories_list:
					product_category=frappe.db.get_all('Product Category',fields=["*"], filters={"name":categories_list[0].category},order_by="display_order",limit_page_length=1)
					if product_category:
						check_category = frappe.db.sql(''' SELECT farming_practises FROM `tabProduct Category` WHERE name=%(category)s''',{'category':product_category[0].name},as_dict=1)
						if check_category:
							if check_category[0].farming_practises:
								farming_practises = check_category[0].farming_practises
							else:
								check_category = frappe.db.sql(''' SELECT farming_practises FROM `tabProduct Category` WHERE name=%(category)s''',{'category':product_category[0].parent_product_category},as_dict=1)
								if check_category:
									if check_category[0].farming_practises:
										farming_practises = check_category[0].farming_practises
			context.farming_practises = farming_practises
			advance_amount = 0
			if self.enable_preorder_product == 1:
				if self.percentage_or_amount=="Preorder Percentage":
					advance_amount += flt(self.price) * flt(self.preorder_percent) / 100
				else:
					advance_amount += flt(self.preorder_amount)
			context.advance_amount = advance_amount
			custom_values = []
			if catalog_settings.display_custom_fields == 1:
				if frappe.db.get_all("Custom Field",filters={"dt":"Product"}):
					custom_fields = frappe.db.sql('''SELECT label,fieldname FROM `tabCustom Field` WHERE dt = "Product" AND fieldtype<> "Table" AND fieldtype<> "Section Break" AND fieldtype<> "Column Break" AND fieldtype<> "HTML"  AND fieldtype<> "Check" AND fieldtype<> "Text Editor" ''',as_dict=1)
					for field in custom_fields:
						query = "SELECT "+field.fieldname +" FROM `tabProduct` WHERE name='{0}'".format(self.name)
						custom_value = frappe.db.sql(query,as_dict=1)
						custom_values.append({"field":field.fieldname,"label":field.label,"value":custom_value[0][field.fieldname]})
			context.custom_values = custom_values
			context.product_name = self.item.replace("'","").replace('"','')
			recent_products = []
			best_sellers_list = []
			if catalog_settings.detail_page_template == "Default Layout":
				recent_products = get_recent_products(None)
				best_sellers_list = get_bestsellers(None,limit=5)
			context.recent_products = recent_products
			context.best_sellers = best_sellers_list
			context.product_category = context.item_categories
			if not self.return_policy:
				context.return_description = ""
		except Exception:
			frappe.log_error(frappe.get_traceback(),'go1_commerce.go1_commerce.product.product.get_context')
	

	def get_contexttt(self, context):
		try:
			from go1_commerce.go1_commerce.api import get_bestsellers,get_product_price,get_category_products,get_category_detail,get_enquiry_product_detail,get_customer_recently_viewed_products, get_product_other_info
			product_brands = []
			product_attributes = []

			if self.status != 'Approved':
				frappe.local.flags.redirect_location = '/404'
				raise frappe.Redirect
			catalog_settings = context.catalog_settings
			brand_cond = ''
			business = None
			if context.get('web_domain') and context.web_domain.business:
				business = context.web_domain.business
				if not self.restaurant or self.restaurant != business:
					frappe.local.flags.redirect_location = '/404'
					raise frappe.Redirect
			if business:
				brand_cond = ' and b.business = "{0}"'.format(business) 
			context.brands = frappe.db.sql('''select b.name, b.brand_name, b.brand_logo, b.route, b.warranty_information as warranty_info, b.description from `tabProduct Brand` b inner join `tabProduct Brand Mapping` pbm on b.name = pbm.brand where pbm.parent = %(parent)s {condition} group by b.name order by pbm.idx'''.format(condition=brand_cond), {'parent': self.name}, as_dict=1) 

			self.get_product_reviews(context)
			productattributes = frappe.db.get_all('Product Attribute Mapping',fields=["*"], filters={"parent":self.name},order_by="display_order",limit_page_length=50)
			image = []
			video_list = []
			if self.product_images:
				for item in self.product_images:
					image.append({"original_image":item.product_image,"product_image":item.detail_image,"detail_image":item.detail_image,"detail_thumbnail":item.detail_thumbnail})
			img=None
			if self.product_images:
				context.og_image = self.product_images[0].product_image
			path1 = frappe.local.request.path
			context.page_url = get_url() + path1
			attr_product_title = ''
			size_chart = ''
			size_chart_params = ''
			chart_name = ''
			size_charts = ''
			for attribute in productattributes:
				if attribute.size_chart:
					chart_name = attribute.size_chart
					size_charts = frappe.db.get_all('Size Chart',filters={'name':attribute.size_chart},fields=['size_chart_image','name'])
					size_chart = frappe.db.sql('''select TRIM(attribute_values) as attribute_values,chart_title,chart_value,name from `tabSize Chart Content` where parent=%(parent)s order by display_order''',{'parent':attribute.size_chart},as_dict=1)
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
				options = frappe.db.get_all("Product Attribute Option",fields=['*'],filters={'parent':self.name,'attribute':attribute.product_attribute,'attribute_id':attribute.name},order_by='display_order',limit_page_length=50)			
				for op in options:
					if op.is_pre_selected == 1:
						if op.product_title and op.product_title != '-':
							attr_product_title = op.product_title
					if op.image_list:
						images = json.loads(op.image_list)
						if len(images) > 0:
							images = sorted(images, key=lambda x: x.get('is_primary'), reverse=True)
							op.image_attribute = images[0].get('thumbnail')
							if op.is_pre_selected == 1:						
								image = []
								for im in images:
									image.append({'original_image': im.get('image'), 'detail_image': im.get('detail_thumbnail'), 'detail_thumbnail': im.get('thumbnail')})
					if op.is_pre_selected == 1:
						attribute_video = frappe.get_all('Product Attribute Option Video',filters={"option_id":op.name},fields=["youtube_video_id","video_type"])
						if attribute_video:
							for video in attribute_video:
								if video.youtube_video_id:
									video_list.append({'video_link':video.youtube_video_id,'video_type':video.video_type})					
				product_attributes.append({"attribute":attribute.product_attribute,"attribute_name":attribute.attribute,"is_required":attribute.is_required,"control_type":attribute.control_type,"attribute_chart":attribute.size_chart,"options":options,"size_charts":size_charts,'size_chart':size_chart,'size_chart_params':size_chart_params})
			context.product_title = attr_product_title
			context.attr_image = image
			context.sel_image = img
			image_position = ''
			if catalog_settings.product_thumbnail_image_position:
				context.image_position = catalog_settings.product_thumbnail_image_position
			context.catalog_settings = catalog_settings
			context.attributes=product_attributes
			context.type_of_category = get_enquiry_product_detail(self.name)
			specification_group = []
			specification_attribute = frappe.db.sql_list('''select distinct sam.spec_group_name,sg.display_order from `tabSpecification Group` sg inner join `tabProduct Specification Attribute Mapping` sam on sg.name=sam.spec_group_name1 where sam.parent=%(name)s order by sam.idx''',{'name':self.name})
			if specification_attribute:
				for item in specification_attribute:
					groups = frappe.db.get_all('Product Specification Attribute Mapping',fields=['specification_attribute','options'], filters={"parent":self.name,'spec_group_name':item},order_by='idx')
					specification_group.append({"name":item, "groups":groups})
				
			context.specification_attribute_grouping = specification_group
			additional_info = get_product_other_info(self.name, context.get('domain'))
			context.related_products = additional_info['related_products']
			context.bestseller_item = additional_info['best_seller_category']
			context.show_best_sellers = additional_info['products_purchased_together']
			context.product_category = additional_info['product_category']
			
			demovideo = frappe.db.get_all('Product Video',fields=["*"], filters={"parent":self.name},order_by="display_order")
			context.demo_video = demovideo
			if len(video_list)>0:
				context.demo_video = video_list

			context.recent_viewed_products = get_customer_recently_viewed_products(domain=context.get('domain'))
			if frappe.session.user != 'Guest':
				update_customer_recently_viewed(self.name)
			context.page_path = get_url()
			path = frappe.local.request.path
			context.currenturl = get_url() + path		

			price_details = get_product_price(self)
			orgprice = self.price
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

			if self.meta_keywords:
				context.meta_keywords=self.meta_keywords if self.meta_keywords else self.item
			else:
				context.meta_keywords = context.catalog_settings.meta_keywords
			allow_review=0
			if frappe.session.user!='Guest':
				allow_review=1
			else:
				if context.catalog_settings.allow_anonymous_users_to_write_product_reviews:
					allow_review=1
			context.allow_review=allow_review
			recent_products = []
			best_sellers_list = []
			if context.catalog_settings.detail_page_template == "Default Layout":
				recent_products = get_recent_products(business)
				best_sellers_list = get_bestsellers(business=business,limit=5)
			context.recent_products = recent_products
			context.best_sellers = best_sellers_list
			ziprange=frappe.request.cookies.get("ziprange")
			context.ziprange=ziprange
			categories_list = frappe.db.sql('''select category, category_name from `tabProduct Category Mapping` where parent = %(parent)s order by idx limit 1''',{'parent':self.name}, as_dict=1)
			if categories_list:
				product_category=frappe.db.get_all('Product Category',fields=["*"], filters={"name":categories_list[0].category},order_by="display_order",limit_page_length=1)
				context.item_categories=product_category[0]
			vendor=frappe.db.sql('''select p.restaurant, b.route, b.restaurant_name from `tabProduct` p, `tabBusiness` b where b.name = p.restaurant and p.restaurant=%(restaurant)s''',{'restaurant':self.restaurant}, as_dict=1)      
			if vendor:
				context.vendor=vendor[0]
			self.check_book_app(context)
			self.set_tax_rate(context,catalog_settings,orgprice)
			if context.map_api:
				self.check_website_product_available(context)
			product_enquiry = get_product_scroll(self.name, 1, 5)
			context.product_enquiry = product_enquiry
			if self.restaurant:
				business = frappe.get_doc("Business", self.restaurant)
				context.business_route = business.route
			context.mobile_page_title = self.item

			if 'temple' in frappe.get_installed_apps():
				from temple.temple.api import get_related_events
				if self.product_categories:
					for x in self.product_categories:
						if "Upcoming Events" in x.category_name:
							context.upcoming_events_flag = 1	
							related_events = get_related_events(self.name)
							for i in related_events:
								if i.full_description:
									full_description = str(remove_html_tags(i.full_description))
									i.full_description = full_description[:95] + '...'
							context.related_events = related_events
						elif "Saree Sponsorship" in x.category_name:
							context.saree_sponsorship_flag = 1
							if self.full_description:
								context.full_description = self.full_description
						elif "Poojas" in x.category_name:
							context.poojas_flag = 1
			control_type_check = 0
			if self.product_attributes:
				for item in self.product_attributes:
					if not "Table" in item.control_type:
						context.control_type_check = 1


			farming_practises = None

			check_field = frappe.db.sql(''' SELECT *  FROM `tabCustom Field` where dt='Product Category' and fieldname='farming_practises' ''',as_dict=1)
			if check_field:
				if categories_list:
					product_category=frappe.db.get_all('Product Category',fields=["*"], filters={"name":categories_list[0].category},order_by="display_order",limit_page_length=1)
					if product_category:
						check_category = frappe.db.sql(''' SELECT farming_practises FROM `tabProduct Category` WHERE name=%(category)s''',{'category':product_category[0].name},as_dict=1)
						if check_category:
							if check_category[0].farming_practises:
								farming_practises = check_category[0].farming_practises
							else:
								check_category = frappe.db.sql(''' SELECT farming_practises FROM `tabProduct Category` WHERE name=%(category)s''',{'category':product_category[0].parent_product_category},as_dict=1)
								if check_category:
									if check_category[0].farming_practises:
										farming_practises = check_category[0].farming_practises
			context.farming_practises = farming_practises
			
			advance_amount = 0
			if self.enable_preorder_product == 1:
				if self.percentage_or_amount=="Preorder Percentage":
					advance_amount += flt(self.price) * flt(self.preorder_percent) / 100
				else:
					advance_amount += flt(self.preorder_amount)
			context.advance_amount = advance_amount
			custom_values = []
			if catalog_settings.display_custom_fields == 1:
				if frappe.db.get_all("Custom Field",filters={"dt":"Product"}):
					custom_fields = frappe.db.sql('''SELECT label,fieldname FROM `tabCustom Field` WHERE dt = "Product" AND fieldtype<> "Table" AND fieldtype<> "Section Break" AND fieldtype<> "Column Break" AND fieldtype<> "HTML"  AND fieldtype<> "Check" AND fieldtype<> "Text Editor" ''',as_dict=1)
					for field in custom_fields:
						query = "SELECT "+field.fieldname +" FROM `tabProduct` WHERE name='{0}'".format(self.name)
						custom_value = frappe.db.sql(query,as_dict=1)
						custom_values.append({"field":field.fieldname,"label":field.label,"value":custom_value[0][field.fieldname]})
			context.custom_values = custom_values
			context.product_name = self.item.replace("'","").replace('"','')
			
		except Exception:
			frappe.log_error(frappe.get_traceback(),'go1_commerce.go1_commerce.product.product.get_context')
	def get_product_reviews(self, context):		
		context.approved_reviews = get_product_reviews_list(self.name, 0, 10)
		
		if context.catalog_settings.upload_review_images:
			review_images = frappe.db.sql('''select RI.review_thumbnail,RI.image,RI.list_image,RI.parent,RI.name,PR.product from `tabProduct Review` PR inner join `tabReview Image` RI on PR.name=RI.parent where PR.product=%(product)s''',{'product':self.name},as_dict=1)
			context.review_img = review_images

	def set_product_availability(self,allow_cart,stock_availability,context):
		context.allow_cart=allow_cart
		context.stock_availability=stock_availability

	def check_book_app(self, context):
		context.isbookshop=0
		installed_apps=frappe.db.sql(''' select * from `tabModule Def` where app_name='book_shop' ''',as_dict=True)
		if len(installed_apps)>0:
			context.isbookshop=1
			context.book_type=self.book_type
			context.published_year=self.published_year
			context.number_of_pages=self.number_of_pages
			if self.author:
				authors=frappe.db.get_all("Author", fields=['author_name', 'route'], filters={'published':1,'name':self.author},limit_page_length=1)
				if authors:
					context.author=authors[0]
			if self.publisher:
				publishers=frappe.db.get_all("Publisher", fields=['publisher_name', 'route'], filters={'published':1,'name':self.publisher},limit_page_length=1)
				if publishers:
					context.publisher=publishers[0]

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
			frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.set_tax_rate")

	def check_website_product_available(self, context):
		zipcode = state = country = city = None
		if context.customer_address:
			address = None
			if frappe.request.cookies.get('addressId'):
				address = next((x for x in context.customer_address if x.name == frappe.request.cookies.get('addressId')), None)
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
				zipcode, city, state, country = get_location_details(zipcode)
				frappe.local.cookie_manager.set_cookie("guestaddress", '{0},{1},{2},{3}'.format(zipcode,state,country,city))
		if not zipcode:
			zipcode = '600001'
			city, state, country = 'Chennai', 'Tamil Nadu', 'India'
			frappe.local.cookie_manager.set_cookie("guestaddress", '{0},{1},{2},{3}'.format(zipcode,state,country,city))
		if zipcode:
			html = "zipcode :"+str(zipcode)+"\n"
			html += "state :"+str(state)+"\n"
			html += "country :"+str(country)+"\n"
			from go1_commerce.go1_commerce.api import check_user_location_delivery
			res = check_user_location_delivery(zipcode, state, country)
			html += "res :"+str(res)+"\n"
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
			commission=frappe.db.sql('''select * from `tabVendor Detail` where parent=%(category)s and (case when product is not null then product=%(product)s else 1=1 end) and (case when vendor is not null then vendor=%(vendor)s else 1=1 end)''',{'product':self.name,'vendor':self.restaurant,'category':self.commission_category},as_dict=1)
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
			restaurant = frappe.get_doc('Business',self.restaurant)
			if restaurant.time_zone:
				actual_date = datetime.now(timezone(restaurant.time_zone))
			else:
				system_settings = frappe.get_single('System Settings')
				actual_date = datetime.now(timezone(system_settings.time_zone))
			dtfmt = '%Y-%m-%d %H:%M:%S'
			day=actual_date.strftime('%A')
			new_date=actual_date.replace(tzinfo=None)
			if not self.all_time:
				if self.menu_item_timings:
					for item in self.menu_item_timings:
						from_date = datetime.strptime(str(actual_date.date())+' '+str(item.from_time),dtfmt)
						to_date=datetime.strptime(str(actual_date.date())+' '+str(item.to_time),dtfmt)
						if from_date > new_date and not self.next_available_at:
							self.next_available_at = from_date
						elif not self.next_available_at and len(self.menu_item_timings) == 1:
							self.next_available_at = add_to_date(from_date, days=1)
			if not self.next_available_at:
				if restaurant.opening_hour:
					from go1_commerce.go1_commerce.api import check_next_seven_days
					timing = check_next_seven_days(restaurant.opening_hour, getdate(new_date))
					if timing:
						self.next_available_at = datetime.strptime(str(getdate(timing['date']))+' '+str(timing['from_hrs']),dtfmt)

def remove_html_tags(text):
	try:
		"""Remove html tags from a string"""
		import re
		return re.sub(re.compile('<.*?>'), '', text)
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.product.events.remove_html_tags')

@frappe.whitelist(allow_guest=True)
def get_location_details(zipcode):
	city = state = country = None
	from go1_commerce.go1_commerce.api import get_geolocation
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
def get_related_option(addon,parent):
	try:
		Group = frappe.db.sql("""select option_name from `tabItem Option` where add_on = %s and parent=%s""", (addon,parent))
		return Group
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.get_related_option") 

def convert_product_image(image_name,size,productid,updated_column=None,updated_name=None):
	try:
		
		org_file_doc = frappe.get_doc("File", {
					"file_url": image_name,
					"attached_to_doctype": "Product",
					"attached_to_name": productid
				})
		if org_file_doc:
			return_url = org_file_doc.make_thumbnail(set_as_thumbnail=False,width=size,height=size,suffix=str(size)+"x"+str(size),updated_doc='Product Image',updated_name=updated_name,updated_column=updated_column)
			
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.convert_product_image") 

@frappe.whitelist()
def get_all_tags():
	""" get the tags set in the  """
	tags = frappe.get_all("Product Tag",
		fields=["title"], distinct=True)

	active_tags = [row.get("title") for row in tags]
	# active_tags.append("")
	return active_tags

@frappe.whitelist()
def get_related_option_from_addon(add_on):
	try:
		order = frappe.get_list("Add On Option", fields=["options"] , filters={"parent": add_on})
		return order
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.get_related_option_from_addon") 

@frappe.whitelist()
def get_relatedoption(addon):
	try:
		Group = frappe.db.sql("""select option_name from `tabItem Option` where add_on = %s""", (addon))    
		return Group
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.get_relatedoption") 

@frappe.whitelist()
def get_product_attribute_options(attribute,product,attribute_id):
	try:
		attributeoptions = frappe.db.sql("""select * from `tabProduct Attribute Option` where parent = %(product)s and attribute=%(attribute)s and attribute_id = %(attribute_id)s""", {"product": product,"attribute":attribute,"attribute_id":attribute_id},as_dict = 1)
		return attributeoptions
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.get_product_attribute_options") 

@frappe.whitelist()
def get_parent_product_attribute_options(attribute,product):
	try:
		attributeoptions = frappe.db.sql("""select * from `tabProduct Attribute Option` where parent = %(product)s and attribute = %(attribute)s order by idx asc""", {"product": product,"attribute":attribute},as_dict = 1)
		return attributeoptions
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.get_product_attribute_options") 


@frappe.whitelist()
def get_product_specification_attribute_options(attribute):
	try:
		attributeoptions = frappe.db.sql("""select option_value from `tabSpecification Attribute Option` where parent = %(attribute)s order by display_order""", {"attribute":attribute},as_dict = 1)
		return attributeoptions
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.get_product_specification_attribute_options") 


@frappe.whitelist()
def insert_product_attribute_options(attribute,product,option,display_order,price_adjustment,weight_adjustment,image,pre_selected,attribute_color,product_title,parent_option=None,attribute_id = None,disable=None,available_datetime=None):
	try:
		# formats = '%d-%m-%Y %H:%M:%S' # The format 
		# available_datetime = datetime.datetime.strptime(available_datetime, formats)
		
		attributeoptions = frappe.db.sql("""select * from `tabProduct Attribute Option` where parent = %(product)s and attribute=%(attribute)s and attribute_id = %(attribute_id)s""", {"product": product,"attribute":attribute,"attribute_id":attribute_id},as_dict = 1)
		if len(attributeoptions) == 0:
			pre_selected = 1
		else:
			if int(pre_selected) == 1:
				for optionitem in attributeoptions:
					option_doc = frappe.get_doc("Product Attribute Option",optionitem.name)
					option_doc.is_pre_selected = 0
					option_doc.save()

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
				"parent_option":parent_option
			})
		doc.disable = int(disable)
		if int(disable)==1:
			doc.available_datetime = available_datetime
		doc.insert()
		
		return frappe.db.sql("""select * from `tabProduct Attribute Option` where parent = %(product)s and attribute=%(attribute)s and attribute_id = %(attribute_id)s""", {"product": product,"attribute":attribute,"attribute_id":attribute_id},as_dict = 1)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.insert_product_attribute_options") 

@frappe.whitelist()
def update_product_attribute_options(attribute,product,option,display_order,price_adjustment,weight_adjustment,optionid,image,pre_selected,attribute_color,product_title,parent_option=None,attribute_id = None, disable=None,available_datetime=None):
	try:
		import datetime
		
		attributeoptions = frappe.db.sql("""select * from `tabProduct Attribute Option` where parent = %(product)s and attribute=%(attribute)s and attribute_id = %(attribute_id)s""", {"product": product,"attribute":attribute,"attribute_id":attribute_id},as_dict = 1)
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
	
		attributeoptions = frappe.db.sql("""select * from `tabProduct Attribute Option` where parent = %(product)s and attribute=%(attribute)s and attribute_id = %(attribute_id)s""", {"product": product,"attribute":attribute,"attribute_id":attribute_id},as_dict = 1)
		return attributeoptions
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.update_product_attribute_options") 

@frappe.whitelist()
def get_product_categories():
	pass

@frappe.whitelist()
def get_all_brands():
	try:
		condition=''
		if "Vendor" in frappe.get_roles(frappe.session.user):
			shop_user=frappe.get_all('Shop User',filters={'name':frappe.session.user},fields=['restaurant'])
			if shop_user:
				condition=" and (case when business is not null then business='{business}' else 1=1 end)".format(business=shop_user[0].restaurant)
		return frappe.db.sql('''select brand_logo,name,brand_name,published from `tabProduct Brand` where published=1 {condition} order by brand_name'''.format(condition=condition))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.get_all_brands") 

@frappe.whitelist(allow_guest=True)
def get_all_category_list():    
	try:
		lists=[]
		condition=''
		if "Vendor" in frappe.get_roles(frappe.session.user):
			shop_user = frappe.db.get_all('Shop User',filters={'name':frappe.session.user},fields=['restaurant'])
			if shop_user and shop_user[0].restaurant:
				categories = frappe.db.sql('''select group_concat(concat('"',category,'"')) as list from `tabBusiness Category` where parenttype="Business" and parent=%(parent)s group by parent''',{'parent':shop_user[0].restaurant},as_dict=1)
				if categories and categories[0].list:
					condition += ' and name in ({categories})'.format(categories=categories[0].list)
		cat = frappe.db.sql('''select category_image,category_name,parent_category_name,is_active,name from `tabProduct Category` where is_active=1 and (parent_product_category IS NULL or parent_product_category="" ) {condition}'''.format(condition=condition),as_dict=1)
		if cat:
			for sub in cat:
				sub.indent = 0
				lists.append(sub)
				sub.subcat = get_sub_category_list(sub.name, condition)
				if sub.subcat:
					for subsub in sub.subcat:
						subsub.indent = 1
						lists.append(subsub)
						subsub.subsubcat = get_sub_category_list(subsub.name, condition)
						if subsub.subsubcat:
							for listcat in subsub.subsubcat:
								listcat.indent=2
								lists.append(listcat)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.get_all_category_list") 

@frappe.whitelist()
def get_sub_category_list(category, condition=''):    
	try:
		s = frappe.db.sql('''select category_image,category_name,parent_category_name,is_active,name from `tabProduct Category` where is_active=1 and parent_product_category=%(category)s {0}'''.format(condition),{"category":category},as_dict=1)
		return s
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.get_sub_category_list") 

@frappe.whitelist()
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
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.approve_products") 

@frappe.whitelist()	
def save_as_template(names, selected_business):
	try:
		import json
		data = json.loads(names)
		if len(data)==0:
			frappe.msgprint(_('Please select any items'))
		else:
			for item in data:
				doc = frappe.get_doc('Product', item).as_dict()
				if doc.template_saved!=1:
					vertical_name = re.sub('[^a-zA-Z0-9 ]', '', selected_business).lower().replace(' ','_')
					vertical_name1 = vertical_name+".json"
					path = frappe.get_module_path("go1_commerce")
					path_parts=path.split('/')
					path_parts=path_parts[:-1]
					url='/'.join(path_parts)
					if not os.path.exists(os.path.join(url,'verticals')):
						frappe.create_folder(os.path.join(url,'verticals'))
					file_path = os.path.join(url, 'verticals', vertical_name1)
					data = []
					if os.path.exists(file_path):
						with open(file_path, 'r') as f:
							data = json.load(f)
							data.append(doc)
						with open(os.path.join(url,'verticals', (vertical_name+'.json')), "w") as f:
							f.write(frappe.as_json(data))
					else:
						doc1 = []
						doc1.append(doc)
						with open(os.path.join(url,'verticals', (vertical_name+'.json')), "w") as f:
							f.write(frappe.as_json(doc1))
					frappe.db.set_value('Product',item,'template_saved',1)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.save_as_template") 

@frappe.whitelist()
def get_product_attributes_with_options(product):
	attributes=frappe.db.get_all('Product Attribute Mapping',filters={'parent':product},fields=['name','product_attribute','is_required','control_type','attribute_unique_name'],order_by='display_order')
	if attributes:
		for item in attributes:
			item.options=get_product_attribute_options(item.product_attribute,product,item.name)			
	return attributes

@frappe.whitelist()
def create_variant_combinations(attributes):
	options=[]
	all_options=[]
	import json
	frappe.log_error("--attributes---",attributes)
	response=json.loads(attributes)
	frappe.log_error("--response---",response)
	for item in response:
		if item.get('attroptions'):
			li=[x.get('option_value') for x in item.get('attroptions')]
			options.append(li)
		all_options+=item.get('attroptions')
	import itertools
	combination=list(itertools.product(*options))
	lists=[]
	for item in combination:
		html=''
		ids=''
		price=0
		attributes_json = []
		
		for li in item:
			check=next((x for x in all_options if x.get('option_value')==li),None)
			if check and check.get('name'):
				attribute_name = frappe.db.get_value("Product Attribute", check.get('attribute'), "attribute_name")
				
				ids+=check.get('name')+'\n'
				html+='<div data-name="'+str(ids)+'" class="btn btn-default btn-xs btn-link-to-form" style="border: 1px solid #d1d8dd;margin: 2px;min-width: 50px;text-align: left;"><p style="text-align: left;margin: 0px;font-size: 11px;">'+attribute_name+'</p> <span style="font-weight: 700;">'+li+'</span></div>'
				price+=check.get('price_adjustment')
				attributes_json.append(check.get('name'))
		if ids:
			lists.append({'attribute_html':html,'attribute_id':ids, 'stock': 1,'price':price, 'attributes_json': attributes_json})
		else:
			frappe.throw(_("Please add and save the attribute options to create the combinations"))
	return lists

@frappe.whitelist()
def get_category_based_attributes(doctype, txt, searchfield, start, page_len, filters):
	condition=''
	if filters.get('productId'):
		category_list = frappe.db.sql('''select group_concat(concat('"', category, '"')) category from `tabProduct Category Mapping` where parent=%(product)s''',{'product':filters.get('productId')},as_dict=1)
		if txt:
			condition += ' and (a.name like %(txt)s or a.attribute_name like %(txt)s)'		
		cat_list = '""'
		if category_list and category_list[0].category:
			cat_list = category_list[0].category
		if "Vendor" in frappe.get_roles(frappe.session.user) and frappe.session.user != 'Administrator':
			shop_user = frappe.db.get_all('Shop User', filters={'name': frappe.session.user}, fields=['restaurant'])
			if shop_user and shop_user[0].restaurant:				
				condition += ' and (case when business is not null then business = "{0}" else 1 = 1 end)'.format(shop_user[0].restaurant)
			else:
				condition += ' and business is null'
		return frappe.db.sql('''select a.name, a.attribute_name from `tab{doctype}` a left join `tabBusiness Category` c 
			on a.name=c.parent where (case when c.category is not null then c.category in ({category}) else 1=1 end) {condition}'''.format(category=cat_list,doctype=filters.get('type'),condition=condition),
			{'txt':'%'+txt+'%'})

	return frappe.db.sql('''select name from `tab{doctype}`'''.format(doctype=filters.get('type')))

@frappe.whitelist()
def get_vendor_based_tax_templates(doctype, txt, searchfield, start, page_len, filters):
	condition=''
	return frappe.db.sql('''select name from `tabProduct Tax Template`''')

@frappe.whitelist()
def get_vendor_based_return_policy(doctype, txt, searchfield, start, page_len, filters):
	condition=''
	return frappe.db.sql('''select name from `tabReturn Policy`''')

@frappe.whitelist()
def update_image(imageId,image_name,is_primary):
	doc=frappe.get_doc('Product Image',imageId)
	doc.image_name=image_name
	doc.is_primary=is_primary
	doc.save(ignore_permissions=True)

@frappe.whitelist()
def check_shop_user(name):
	return frappe.db.sql('''select restaurant from `tabShop User` where name=%s''',name,as_dict=1)

@frappe.whitelist()
def delete_product_attribute_option(option):
	try:
		attribute_video = frappe.db.sql('''select name,option_id from `tabProduct Attribute Option Video` where option_id=%(option_id)s''',{'option_id':option},as_dict=1)
		if attribute_video:
			for video in attribute_video:
				video_doc = frappe.get_doc('Product Attribute Option Video',video.name)
				video_doc.delete()
		doc=frappe.get_doc("Product Attribute Option", option)
		if doc.get('image_list'):
			images = json.loads(doc.get('image_list'))
			from go1_commerce.go1_commerce.api import delete_attribute_image
			for im in images:
				delete_attribute_image(im)
		doc.delete()
		return {'status':'success'}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.product.delete_product_attribute_option")


@frappe.whitelist()
def delete_product_attribute_option_image(ref_doctype, file_url):
	try:
		frappe.db.sql('''delete from `tabFile` where attached_to_doctype=%(ref_doctype)s and file_url = %(file_url)s''',{'file_url':file_url,'ref_doctype':ref_doctype})
		return {'status': "Success"}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.product.delete_product_attribute_option_image")

def randomStringDigits(stringLength=6):
	import random
	import string
	lettersAndDigits = string.ascii_uppercase + string.digits
	return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))

@frappe.whitelist()
def check_menu_available_time():
	try:
		product_list = frappe.db.sql('''select name, restaurant, next_available_at from `tabProduct` where current_availability = 0 and cast(next_available_at as date) = curdate()''',as_dict=1)
		if product_list:
			for item in product_list:
				time_zone = None
				if item.restaurant:
					time_zone = frappe.db.get_value('Business',item.restaurant, 'time_zone')
				if not time_zone:
					time_zone = frappe.db.get_single_value('System Settings','time_zone')
				actual_date = datetime.now(timezone(time_zone))
				ref_date = actual_date.replace(tzinfo=None)
				if ref_date >= item.next_available_at:
					frappe.db.set_value('Product',item.name,'current_availability',1)
					frappe.db.set_value('Product',item.name,'next_available_at',None)
		options = frappe.db.sql('''select o.*, p.restaurant from `tabProduct Attribute Option` o left join `tabProduct` p on p.name = o.parent where disable = 1''', as_dict=1)
		if options:
			for opt in options:
				time_zone = None
				if opt.restaurant:
					time_zone = frappe.db.get_value('Business', opt.restaurant, 'time_zone')
				actual_date = get_today_date(time_zone, True)
				if opt.available_datetime:
					if actual_date >= opt.available_datetime:
						frappe.db.set_value('Product Attribute Option', opt.name, 'disable', 0)
						frappe.db.set_value('Product Attribute Option', opt.name, 'available_datetime',None)
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.product.check_menu_available_time")

@frappe.whitelist()
def get_product(name):
	return frappe.get_doc('Product',name)

@frappe.whitelist(allow_guest=True)
def update_product_categories(category1,name):
	frappe.db.sql('''delete from `tabProduct Category Mapping` where parent=%(name)s''',{'name':name})
	for x in json.loads(category1):
		paper_question = frappe.new_doc("Product Category Mapping")
		paper_question.category=x['category']
		paper_question.category_name=x['category_name']
		paper_question.parent=name
		paper_question.parentfield="product_categories"
		paper_question.parenttype="Product"
		paper_question.save()

@frappe.whitelist(allow_guest=True)
def update_product_categories1(category1,name):
	frappe.db.sql('''delete from `tabProduct Category Mapping` where parent=%(name)s''',{'name':name})
	for x in json.loads(category1):
		paper_question = frappe.new_doc("Product Category Mapping")
		paper_question.category=x
		paper_question.parent=name
		paper_question.parentfield="product_categories"
		paper_question.parenttype="Product"
		paper_question.save()

@frappe.whitelist()
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

@frappe.whitelist(allow_guest = True)
def get_product_scroll(item, page_no, page_len):
	try:
		start = (int(page_no) - 1) * int(page_len)
		product_enquiry = frappe.db.sql('''select pq.name, pq.user_name, pq.email, pq.phone, pq.product, 
			pq.question, date_format(pq.creation, "%d, %b %Y") as creation,group_concat(pa.answer SEPARATOR ";") as ans_list from `tabProduct Enquiry` pq left join `tabProduct Enquiry Answers` 
			pa on pq.name = pa.parent where pq.product = "{name}" and is_approved=1 group by pq.name limit {start}, {limit}'''.format(start=start, limit=page_len, name=item), as_dict=1)     
		return product_enquiry
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.product.get_product_scroll")

@frappe.whitelist(allow_guest=True)
def get_review_scroll(item, page_no, page_len):
	start=(int(page_no)-1)*int(page_len)
	dateformat='%b %d, %Y'
	Reviews=frappe.db.sql('''select RI.review_thumbnail,RI.image,RI.list_image, PR.customer,email,date_format(PR.creation,%(format)s) as date,PR.review_title,PR.review_message,PR.rating,PR.name 
		from `tabProduct Review` PR inner join `tabReview Image` RI on PR.name=RI.parent where PR.product=%(item)s order by PR.creation desc limit {start},{limit}'''
		.format(start=start,limit=page_len),{'item':item,'format':dateformat},as_dict=1)
	return Reviews

@frappe.whitelist(allow_guest=True) 
def get_review_images(name,product):
	dateformat='%b %d, %Y'
	approved_reviews1 = frappe.db.sql('''select RI.review_thumbnail,RI.image,RI.list_image,RI.name,RI.parent,PR.*,date_format(PR.creation,%(format)s) as date from `tabProduct Review` PR inner join `tabReview Image` RI on PR.name=RI.parent where PR.product=%(product)s''',{'product':product,'format':dateformat},as_dict=1)
	return approved_reviews1

@frappe.whitelist(allow_guest=True)
def get_curreview_images(name):
	dateformat='%b %d, %Y'
	approved_review = frappe.db.sql('''select RI.review_thumbnail,RI.image,RI.list_image,RI.parent,PR.*,date_format(PR.creation,%(format)s) as date from `tabProduct Review` PR inner join `tabReview Image` RI on PR.name=RI.parent where PR.name=%(name)s''',{'name':name,'format':dateformat},as_dict=1)
	return approved_review

@frappe.whitelist(allow_guest=True)
def check_product_attribute_options(product_attributes = None):
	if product_attributes:
		attribute_len = frappe.get_list("Product Attribute Option",fields = ['name'],filters={'attribute_id' : product_attributes})
		if attribute_len > 0:
			return "true"
		else:
			return "false"
	else:
		pass

@frappe.whitelist(allow_guest=True)
def get_product_reviews_list(product, page_no=0, page_len=10):
	start = int(page_no) * int(page_len)
	dateformat='%b %d, %Y'
	reviews = frappe.db.sql(''' select name,customer, email, review_title, review_message, rating, 
		date_format(creation,%(format)s) as date, creation from `tabProduct Review` where product = %(product)s and is_approved = 1 order by 
		creation desc limit {start},{limit}'''.format(start=start, limit=page_len),{'product': product,'format':dateformat}, as_dict=1)
	upload_image = get_settings_value_from_domain('Catalog Settings', 'upload_review_images')
	if upload_image:
		for image in reviews:
			image.review_images=frappe.db.get_all('Review Image',fields=['review_thumbnail','image','list_image','name'],filters={'parent':image.name})

	return reviews

@frappe.whitelist(allow_guest=True)
def update_customer_recently_viewed(product, customer=None):
	enable_recently_viewed = get_settings_value_from_domain('Catalog Settings', 'enable_recetly_viewed_products')
	if enable_recently_viewed:
		if not customer:
			if frappe.request.cookies.get('customer_id'):
				customer = unquote(frappe.request.cookies.get('customer_id'))
		if customer:
			check_already_viewed = frappe.get_all("Customer Viewed Product",filters={'parent':customer,'product':product})
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
				customer_viewed_product = frappe.get_doc("Customer Viewed Product", check_already_viewed_update.name)
				customer_viewed_product.viewed_date = getdate(nowdate())
				customer_viewed_product.viewed_count = int(customer_viewed_product.viewed_count) + 1
				customer_viewed_product.save(ignore_permissions=True)
				frappe.db.commit()

@frappe.whitelist()
def show_attribute_err(attribute_id):
	attribute_option = frappe.get_list("Product Attribute Option", fields = ["attribute_id"], filters = {"attribute_id": attribute_id})
	if attribute_option:
		return attribute_option
	else:
		return "Failed"

@frappe.whitelist()
def check_attr_combination(self):
	if len(self.variant_combination) > 0:
		for i in self.variant_combination:
			att_id = '"' + '","'.join(i.attribute_id.split("\n"))[:-2]
		options = frappe.db.sql('''select name from `tabProduct Attribute Option` where parent = %(parent)s and name not in ({0})'''.format(att_id),{'parent': self.name},as_dict = 1)		
		if options:
			pass
		else:
			frappe.throw("Please delete Attribute combinations and then try to delete attribute")

@frappe.whitelist()
def delete_attribute_option_alert(option):
	combination = frappe.db.sql('''select name,attribute_id from `tabProduct Variant Combination`''',as_dict = 1)
	att_id_arr = []
	for i in combination:
		att_id = (i.attribute_id.split("\n"))[:-2]
		for item in att_id:
			att_id_arr.append(str(item))
	attributes = frappe.get_doc("Product Attribute Option", option)
	if option  in att_id_arr:	
		frappe.throw("Cannot delete because Product Attribute Option " + attributes.option_value+ "is linked with Product Attribute Combination")
	else:
		return "Success"

@frappe.whitelist()
def show_attribute_deletion_err(item, row_id):
	combination = frappe.db.sql('''select name, attribute_id from `tabProduct Variant Combination` where parent = %(parent)s''', {'parent': item},as_dict = 1)	
	att_id_arr = '""'
	for i in combination:
		att_id = (i.attribute_id.split("\n"))
		att_id_arr = ",".join(['"' + x + '"' for x in att_id if x])
	attributes = frappe.db.sql('''select name,attribute_id from `tabProduct Attribute Option` where attribute_id = %(attr_id)s and name in ({lists})'''.format(lists=att_id_arr),{'attr_id':row_id},as_dict = 1)	
	if attributes:
		return 'Failed'

@frappe.whitelist()
def check_attr_combination_price(self):
	if len(self.variant_combination) > 0:
		for i in self.variant_combination:
			if i.price<self.price:
				frappe.throw("Attribute combination price should be greater than or equal to base price")

@frappe.whitelist()
def delete_attribute_options(dt, dn):
	try:
		doc = frappe.get_doc(dt, dn)
		attribute_options = get_product_attribute_options(doc.product_attribute, doc.parent, doc.name)
		for item in attribute_options:
			attribute_video1 = frappe.db.sql('''select name,option_id from `tabProduct Attribute Option Video` where option_id=%(option_id)s''',{'option_id':item.name},as_dict=1)
			if attribute_video1:
				for video1 in attribute_video1:
					frappe.db.sql('''delete from `tabProduct Attribute Option Video` where name=%(name)s''',{'name':video1.name})
			if item.get('image_list'):
				from go1_commerce.go1_commerce.api import delete_attribute_image
				images = json.loads(item.get('image_list'))
				for im in images:
					delete_attribute_image(im)
			frappe.db.sql('''delete from `tabProduct Attribute Option` where name=%(name)s''',{'name':item.name})
			
		return {'status': 'success'}
	except Exception as e:
		return {'status': 'Failed'}

@frappe.whitelist(allow_guest=True)
def insert_attribute_option_video(option_id,video_id,video_type):
	attribute_option_video = frappe.new_doc("Product Attribute Option Video")
	attribute_option_video.option_id = option_id
	attribute_option_video.youtube_video_id = video_id
	attribute_option_video.video_type = video_type
	attribute_option_video.save(ignore_permissions=True)
	attributeoptions_video = frappe.db.sql("""select * from `tabProduct Attribute Option Video` where option_id = %(option_id)s""", {"option_id": option_id},as_dict = 1)
	if attributeoptions_video:
		return attributeoptions_video

@frappe.whitelist()		
def get_attribute_option_videos(option_id):
	attributeoptions_video = frappe.db.sql("""select * from `tabProduct Attribute Option Video` where option_id = %(option_id)s""", {"option_id": option_id},as_dict = 1)
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
	attributeoptions_video = frappe.db.sql("""select * from `tabProduct Attribute Option Video` where option_id = %(option_id)s""", {"option_id": option_id},as_dict = 1)
	if attributeoptions_video:
		return attributeoptions_video

@frappe.whitelist(allow_guest=True)   
def get_all_category_lists(product_group=None):
	item_group = frappe.db.get_all("Product Category", fields=["*"], filters={"is_active":1})
	for n in item_group:
		child_groups = ", ".join(['"' + frappe.db.escape(i[0]) + '"' for i in get_child_groups(n.name)])
		parent_category = get_parent_item_groups(n.name)
		
@frappe.whitelist()
def get_parent_item_groups(item_group_name):
	item_group = frappe.get_doc("Product Category", item_group_name)
	return frappe.db.sql("""select name, category_name from `tabProduct Category`
		where lft <= %s and rgt >= %s
		and is_active=1
		order by lft asc""", (item_group.lft, item_group.rgt), as_dict=True)

def get_child_groups(item_group_name):
	item_group = frappe.get_doc("Product Category", item_group_name)
	return frappe.db.sql("""select name, category_name
		from `tabProduct Category` where lft>=%(lft)s and rgt<=%(rgt)s
			and is_active = 1""", {"lft": item_group.lft, "rgt": item_group.rgt})

def get_child_categories1(category):
	try:
		lft, rgt = frappe.db.get_value('Product Category', category, ['lft', 'rgt'])
		return frappe.db.sql('''select name from `tabProduct Category` where is_active = 1 and disable_in_website = 0 and lft >= {lft} and rgt <= {rgt}'''.format(lft=lft, rgt=rgt), as_dict=1)
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.api.get_child_categories')
@frappe.whitelist()
def get_category_list(reference_doc, reference_fields, filters=None, page_no=1, page_len=20, business=None, search_txt=None, search_field="name"):
	reference_field = json.loads(reference_fields)
	condition = ''
	start = (int(page_no) - 1) * int(page_len)
	if search_txt:
		searchKey = '"%' + search_txt + '%"'
		condition += ' and {search_field} like {search_txt}'.format(search_field=search_field, search_txt=searchKey)
	
	fields = ','.join([x for x in reference_field])
	
	list_len = frappe.db.sql('''select {field} from `tab{dt}` where is_active = 1 {cond} order by lft'''.format(field=fields, dt=reference_doc, cond=condition), as_dict=1)
	
	list_name = frappe.db.sql('''select {field} from `tab{dt}` where is_active = 1 {cond} order by lft limit {page_no}, {page_len}'''.format(field=fields, dt=reference_doc, cond=condition, page_no=start, page_len=page_len), as_dict=1)
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

@frappe.whitelist(allow_guest=True)
def get_category_attributes(reference_doc, reference_fields, filters=None,page_no=1, page_len=20, business=None, search_txt=None, search_field="name"):
	condition = ''
	category = ''
	start = (int(page_no) - 1) * int(page_len)
	user = frappe.session.user
	if isinstance(filters, string_types):
		filters = json.loads(filters)
	if filters:
		category = ','.join('"{0}"'.format(r["category"]) for r in filters)
		condition += ' and c.category in ({category})'.format(category=category)
	if search_txt:
		searchKey = '"%' + search_txt + '%"'
		condition += ' and a.{search_field} like {search_txt}'.format(search_field=search_field, search_txt=searchKey)
	if "Vendor" in frappe.get_roles(frappe.session.user):
		users = frappe.db.sql('''SELECT DISTINCT parent FROM `tabHas Role` WHERE role="{role}"'''.format(role="Admin"), as_dict=1)
		if users: admin = ','.join(['"' + user.parent + '"' for user in users])
		if admin:
			admin = admin+',"'+user+'"'
		condition += " and (a.business is null or a.owner in ({0}))".format(admin)

	query = 'select	a.name, a.attribute_name from `tabProduct Attribute` a left join `tabBusiness Category` c ON c.parent=a.name where c.name!="" {condition} limit {page_no}, {page_len}'.format(category=category, condition=condition, page_no=start, page_len=page_len)

	list_name = frappe.db.sql('''{query}'''.format(query=query), as_dict=True)
	list_len = frappe.db.sql('''select	a.name, a.attribute_name from `tabProduct Attribute` a left join `tabBusiness Category` c ON c.parent=a.name where c.name!="" {condition}'''.format(condition=condition), as_dict=True)
	return {"list_name":list_name, "list_len":len(list_len)}

@frappe.whitelist()
def get_returnpolicy_list(reference_doc, reference_fields, filters=None,page_no=1, page_len=20, business=None, search_txt=None, search_field="name"):
	start = (int(page_no) - 1) * int(page_len)
	reference_field = json.loads(reference_fields)
	condition = ''

	if search_txt:
		searchKey = '"%' + search_txt + '%"'
		condition += ' and {search_field} like {search_txt}'.format(search_field=search_field, search_txt=searchKey)
	if filters:
		condition += filters
	fields = ','.join([x for x in reference_field])
	if reference_doc=="Product":
		condition += " and is_active=1 and status='Approved' "
	list_name = frappe.db.sql('''select {field} from `tab{dt}` where name != "" {cond} limit {page_no}, {page_len}'''.format(field=fields, dt=reference_doc, cond=condition, page_no=start, page_len=page_len), as_dict=1)
	list_len = frappe.db.sql('''select {field} from `tab{dt}` where name != "" {cond}'''.format(field=fields, dt=reference_doc, cond=condition), as_dict=1)
	return {"list_name":list_name, "list_len":len(list_len)}


@frappe.whitelist()
def get_specification_list(reference_doc, reference_fields, filters=None,page_no=1, page_len=20, business=None, search_txt=None, search_field="name"):
	start = (int(page_no) - 1) * int(page_len)
	reference_field = json.loads(reference_fields)
	condition = ''
	if search_txt:
		searchKey = '"%' + search_txt + '%"'
		condition += ' and {search_field} like {search_txt}'.format(search_field=search_field, search_txt=searchKey)
	
	fields = ','.join([x for x in reference_field])
	list_name = frappe.db.sql('''select {field} from `tab{dt}` where name != "" {cond} limit {page_no}, {page_len}'''.format(field=fields, dt=reference_doc, cond=condition, page_no=start, page_len=page_len), as_dict=1)
	list_len = frappe.db.sql('''select {field} from `tab{dt}` where name != "" {cond}'''.format(field=fields, dt=reference_doc, cond=condition), as_dict=1)
	
	return {"list_name":list_name, "list_len":len(list_len)}


@frappe.whitelist()
def get_brand_list(reference_doc, reference_fields, filters=None, page_no=1, page_len=20, business=None, search_txt=None, search_field="name"):
	start = (int(page_no) - 1) * int(page_len)
	reference_field = json.loads(reference_fields)
	fields = ','.join([x for x in reference_field])
	condition = ''
	if search_txt:
		searchKey = '"%' + search_txt + '%"'
		condition += ' and {search_field} like {search_txt}'.format(search_field=search_field, search_txt=searchKey)
	if "Vendor" in frappe.get_roles(frappe.session.user) and frappe.session.user != 'Administrator':
		shop_user = frappe.db.get_all('Shop User',filters={'name':frappe.session.user},fields=['restaurant'])
		if shop_user and shop_user[0].restaurant:
			condition += ' and business="" or (case when business is not null then business="{0}" else 1=1 end)'.format(shop_user[0].restaurant)
	list_name = frappe.db.sql('''select {field} from `tab{dt}` where published = 1 {cond}  limit {page_no}, {page_len}'''.format(field=fields, dt=reference_doc, cond=condition, page_no=start, page_len=page_len), as_dict=1)
	list_len = frappe.db.sql('''select {field} from `tab{dt}` where published = 1 {cond}'''.format(field=fields, dt=reference_doc, cond=condition), as_dict=1)
	
	return {"list_name":list_name, "list_len":len(list_len)}

@frappe.whitelist()
def get_recent_products(business = None):
	try:
		recent_cond = ''
		if business:
			recent_cond = ' and p.restaurant = "{0}"'.format(business)
		return frappe.db.sql('''select  p.name, p.price, p.item, p.route , (select detail_thumbnail from `tabProduct Image` i where parent=p.name 
				  limit 1) as detail_thumbnail from `tabProduct` p where is_active=1 and status="Approved" {0} order by creation desc limit 5 '''.format(recent_cond), as_dict=1)
		
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.doctype.product.product.get_recent_products')

@frappe.whitelist()
def insert_attribute_template(attribute,product_attr,message):
	try:
		template = frappe.db.sql('''select name from `tabProduct Attribute Template` where attribute_id=%(attribute_id)s''',{'attribute_id':attribute},as_dict=1)
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
					"is_pre_selected": item['is_pre_selected']
				})
				doc.insert(ignore_permissions=True)
		return "Success"
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.doctype.product.product.insert_attribute_template')

@frappe.whitelist()
def select_attribute_template(template_name,attribute,product,attribute_id):
	try:
		option_template = frappe.db.sql('''select name,attribute_id,attribute_name from `tabProduct Attribute Template` where name=%(name)s''',{'name':template_name},as_dict=1)
		if option_template:
			opt_temp = frappe.db.sql('''select * from `tabAttribute Option` where parent=%(parent)s''',{'parent':option_template[0].name},as_dict=1)
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
						"available_datetime":item.available_datetime
					})
					doc.insert(ignore_permissions=True)
				return frappe.db.sql("""select * from `tabProduct Attribute Option` where parent = %(product)s and attribute=%(attribute)s and attribute_id = %(attribute_id)s""", {"product": product,"attribute":attribute,"attribute_id":attribute_id},as_dict = 1)
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.doctype.product.product.select_attribute_template')


@frappe.whitelist()
def delete_option(name):
	frappe.db.sql('''delete from `tabProduct Attribute Mapping` where name=%(name)s''',{'name':name})
	return "success"

@frappe.whitelist()
def insert_json(selected_business,name):
	doc = frappe.get_doc('Product', name).as_dict()
	vertical_name = re.sub('[^a-zA-Z0-9 ]', '', selected_business).lower().replace(' ','_')
	vertical_name1 = vertical_name+".json"
	path = frappe.get_module_path("go1_commerce")
	path_parts=path.split('/')
	path_parts=path_parts[:-1]
	url='/'.join(path_parts)
	if not os.path.exists(os.path.join(url,'verticals')):
		frappe.create_folder(os.path.join(url,'verticals'))
	file_path = os.path.join(url, 'verticals', vertical_name1)
	data = []
	if os.path.exists(file_path):
		with open(file_path, 'r') as f:
			data = json.load(f)
			data.append(doc)
		with open(os.path.join(url,'verticals', (vertical_name+'.json')), "w") as f:
			f.write(frappe.as_json(data))
	else:
		doc1 = []
		doc1.append(doc)
		with open(os.path.join(url,'verticals', (vertical_name+'.json')), "w") as f:
			f.write(frappe.as_json(doc1))
	frappe.db.set_value('Product',doc.name,'template_saved',1)

@frappe.whitelist()
def get_order_settings():
	check_file_uploader = 0
	apps = frappe.get_installed_apps(True)
	if 'frappe_s3_attachment' in apps:
		s3_settings = frappe.get_single("S3 File Attachment")
		if s3_settings.aws_key and s3_settings.aws_secret and (not s3_settings.disable_s3_file_attachment or s3_settings.disable_s3_file_attachment==0):
			check_file_uploader = 1
	return {"order_settings":get_settings_from_domain('Order Settings'),"s3_enable":check_file_uploader}

@frappe.whitelist()
def get_role_list(doctype, txt, searchfield, start, page_len, filters):
	condition=''
	setting = get_settings_from_domain('Business Setting')
	if filters.get('productId'):
		category_list = frappe.db.sql('''select group_concat(concat('"', category, '"')) category from `tabProduct Category Mapping` where parent=%(product)s''',{'product':filters.get('productId')},as_dict=1)
		if txt:
			condition += ' and (a.name like %(txt)s or a.attribute_name like %(txt)s)'		
		cat_list = '""'
		if category_list and category_list[0].category:
			cat_list = category_list[0].category
		if "Vendor" in frappe.get_roles(frappe.session.user) and frappe.session.user != 'Administrator':
			shop_user = frappe.db.get_all('Shop User', filters={'name': frappe.session.user}, fields=['restaurant'])
			if shop_user and shop_user[0].restaurant:				
				condition += ' and (case when business is not null then business = "{0}" else 1 = 1 end)'.format(shop_user[0].restaurant)
			else:
				condition += ' and business is null'
		return frappe.db.sql('''select a.name, a.attribute_name from `tab{doctype}` a left join `tabBusiness Category` c 
			on a.name=c.parent where (case when c.category is not null then c.category in ({category}) else 1=1 end) {condition}'''.format(category=cat_list,doctype=filters.get('type'),condition=condition),
			{'txt':'%'+txt+'%'})
	conditions = []
	return frappe.db.sql("""select name from `tabRole`
		where disabled = 0 and name not in ("System Manager","Administrator")
			and ({key} like %(txt)s)
			{fcond} {mcond}
		order by
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999),
			idx desc,
			name
		limit %(start)s, %(page_len)s""".format(**{
			'key': searchfield,
			'fcond': get_filters_cond(doctype, filters, conditions),
			'mcond': get_match_cond(doctype)
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		})
	
@frappe.whitelist()
def get_models(reference_doc, reference_fields):
	reference_field = json.loads(reference_fields)
	list_name = frappe.db.get_all(reference_doc,fields=reference_field,filters={"is_active":1},limit_page_length=2000)
	return {"list_name":list_name}

@frappe.whitelist()
def get_all_products_with_attributes(category=None, brand=None, item_name=None, active=None, featured=None, business=None):
	try:
		lists=[]
		subcat=get_products(category=category, brand=brand, item_name=item_name, active=active, featured=featured, business=business)
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
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.get_all_products_with_attributes") 
	
@frappe.whitelist()
def get_product_attributes(name):	
	try:
		query = '''select AO.name as docname,concat_ws(' - ', PA.attribute, AO.parent_option) as name,AO.option_value as item, AO.parent_option,AO.price_adjustment as price,AO.attribute from `tabProduct Attribute Option` AO inner join `tabProduct Attribute Mapping` PA on AO.attribute_id=PA.name where PA.parent="{parent}" order by PA.display_order, name'''.format(parent=name)
		s= frappe.db.sql(query,as_dict=1)
		return s
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.get_product_attributes") 

@frappe.whitelist()
def get_products(category=None,brand=None,cat_doctype=None,brand_doctype=None,item_name=None,active=None,featured=None, business=None):
	if category or brand:
		filters = ''
		joins = ''
		if category:
			joins += ' inner join `tabProduct Category Mapping` PCM on PCM.parent=P.name'
			filters += " and PCM.category='{category}'".format(category=category)
		if brand:
			joins += ' inner join `tabProduct Brand Mapping` PBM on PBM.parent=P.name'
			filters += ' and PBM.brand="{brand}"'.format(brand=brand)
		if item_name:
			item_name = '"%' + item_name + '%"'
			filters += ' and P.item like %s' % (item_name)
		if active:
			if active=="Yes":
				active=1
			else:
				active=0
			filters += ' and P.is_active=%s' % (active)
		if featured:
			if featured=="Yes":
				featured=1
			else:
				featured=0
			filters += ' and P.display_home_page=%s' % (featured)
		if business:
			filters += ' and P.restaurant = "{0}"'.format(business)
		query = '''select P.name,P.item,P.price,P.sku,P.old_price,P.stock,P.inventory_method,P.name as docname,CASE WHEN P.is_active>0 THEN 'Yes' ELSE 'No' END as is_active,CASE WHEN P.display_home_page>0 THEN 'Yes' ELSE 'No' END as display_home_page,P.name as id,P.name as name1 from `tabProduct` P {joins} where P.name!='' {condition} '''.format(condition=filters,joins=joins)
		p = frappe.db.sql(query,as_dict=1)
		for items in p:
			images = frappe.db.sql('''select detail_thumbnail,detail_image from `tabProduct Image` where parent=%(name)s order by is_primary desc''',{'name':items.name},as_dict=1)
			image = '<div class="row">'
			for img in images:
				if img.detail_thumbnail:
					image += '<div class="col-md-4 popup" data-poster="'+img.detail_image+'" data-src='+img.detail_image+' style="margin-bottom:10px;padding-left:0px;padding-right:0px;"><a href="'+img.detail_image+'"><img class="img-responsive" id="myImg" src="'+ img.detail_thumbnail +'" onclick=showPopup("'+img.detail_image+'")></a></div>'
			image+='</div>'
			items.image = image
	else:
		filters = ''
		if item_name:
			item_name = '"%' + item_name + '%"'
			filters += ' and P.item like %s' % (item_name)
		if active:
			if active=="Yes":
				active=1
			else:
				active=0
			filters += ' and P.is_active=%s' % (active)
		if featured:
			if featured=="Yes":
				featured=1
			else:
				featured=0
			filters += ' and P.display_home_page=%s' % (featured)
		if business: filters += ' and P.restaurant = "{0}"'.format(business)
		query = '''select P.name,P.item,P.price,P.sku,P.old_price,P.stock,P.inventory_method,P.name as docname,CASE WHEN P.is_active>0 THEN 'Yes' ELSE 'No' END as is_active,CASE WHEN P.display_home_page>0 THEN 'Yes' ELSE 'No' END as display_home_page,P.name as id,P.name as name1 from `tabProduct` P where P.name!= '' {condition}'''.format(condition=filters)
		p = frappe.db.sql(query,as_dict=1)
		for items in p:
			images = frappe.db.sql('''select detail_thumbnail,detail_image from `tabProduct Image` where parent=%(name)s order by is_primary desc''',{'name':items.name},as_dict=1)
			image = '<div class="row">'
			for img in images:
				if img.detail_thumbnail:
					image += '<div class="col-md-4 popup" data-poster="'+img.detail_image+'" data-src='+img.detail_image+' style="margin-bottom:10px;padding-left:0px;padding-right:0px;"><a href="'+img.detail_image+'"><img class="img-responsive" id="myImg" src="'+ img.detail_thumbnail +'" onclick=showPopup("'+img.detail_image+'")></a></div>'
			image+='</div>'
			items.image = image
	return p

@frappe.whitelist()
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
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.update_bulk_data") 

@frappe.whitelist()
def get_gallery_list(parent, name=None):
	condition = ""
	if parent:
		condition += 'where parent =%(parent)s'
	if name:
		condition += 'and name =%(name)s'
	else:
		name = ""
	return frappe.db.sql('''select * from `tabProduct Image` {condition} order by idx asc'''.format(condition=condition),{"parent":parent, "name" :name},as_dict=1)

@frappe.whitelist()
def get_product_template(name=None, business=None):
	user = frappe.session.user
	if name:
		return frappe.get_doc("Product", name)
	if "Vendor" in frappe.get_roles(user):
		shop_users = frappe.db.get_all('Shop User', filters={'email': user}, fields=['restaurant'])
		if shop_users:
			return frappe.db.get_all("Product", fields=["*"], filters={"restaurant": shop_users[0].restaurant, "is_template":1})
	return frappe.db.get_all("Product", fields=["*"], filters={"is_template":1})


@frappe.whitelist()
def get_product_templates(name=None, business=None):
	if name:
		return frappe.get_doc("Product", name)
	if business:
		condition = ""
		vendor_data = frappe.db.sql('''select distinct parent from `tabMulti Vendor Pricing` where vendor_id!="{business}" order by idx asc'''.format(business=business),as_dict=1)
		frappe.log_error("vendor_data", vendor_data)
		if len(vendor_data)>0:
			condition += ",".join(['"' + x.parent + '"' for x in vendor_data])
			frappe.log_error(condition, "condition")
			return frappe.db.sql('''select * from `tabProduct` where is_template=1 and name in ({condition})'''.format(condition=condition),as_dict=1)
	return frappe.db.get_all("Product", fields=["*"], filters={"is_template":1})

@frappe.whitelist()
def save_gallery_changes(data):
	doc = data
	if isinstance(doc, string_types):
		doc = json.loads(doc)
	ret = frappe.get_doc(doc.get('doc_type'),doc.get('doc_name'))
	ret.image_name= doc.get('img_name')
	ret.title= doc.get('img_caption')
	ret.save()
	return ret

@frappe.whitelist()
def upload_img():
	try:
		import base64
		files = frappe.request.files
		content = None
		filename = None
		img_type = frappe.form_dict.type
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
					"content": content,
				})
			ret.save(ignore_permissions=True)
			frappe.db.commit()
			return ret.as_dict()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(),"go1_commerce.go1_commerce.doctype.product.upload_img")

def get_query_condition(user):
	if not user: user = frappe.session.user
	catalog_settings = get_settings_from_domain('Catalog Settings')
	if "Vendor" in frappe.get_roles(user):
		shop_users = frappe.db.get_all('Shop User', filters={'email': user}, fields=['restaurant'])
		if shop_users:
			if catalog_settings.enable_vendor_based_pricing==1:
				vendor_data = frappe.db.sql('''select distinct p.name from `Product` p left join `tabMulti Vendor Pricing` v ON v.parent=p.name left join `tabMulti Vendor Variant Pricing` m ON m.parent=p.name where v.vendor_id!="{business}" and m.vendor_id!="{business}"'''.format(business=shop_users[0].restaurant),as_dict=1)
				condition=""
				if len(vendor_data)>0:
					condition += ",".join(['"' + x.parent + '"' for x in vendor_data])
				frappe.log_error(condition, "condition")
				return "(`tabProduct`.restaurant='{0}' and `tabProduct`.restaurant is not null) or (`tabProduct`.name in ({1}))".format((shop_users[0].restaurant or ''), condition)
			return "(`tabProduct`.restaurant='{0}' and `tabProduct`.restaurant is not null)".format((shop_users[0].restaurant or ''))
			
@frappe.whitelist()
def get_record_count(dt, business=None):
	condition = ''
	if business:
		condition = ' where restaurant = "{0}"'.format(business)
	d = frappe.db.sql('''select (case when is_test_record = 0 then "actual" else "test" end) as record_type, count(*) count from `tab{dt}` {cond} group by is_test_record'''.format(dt=dt, cond=condition), as_dict=1)
	out = {}
	for item in d:
		out[item.record_type] = item.count
	return out

@frappe.whitelist()
def clear_test_records(dt, business=None):
	test_records = frappe.db.get_all(dt, filters={'is_test_record': 1, 'restaurant': (business or '')}, limit_page_length=500, order_by='creation desc')
	docs = len(test_records)
	for i, item in enumerate(test_records):
		frappe.delete_doc(dt, item.name)
		frappe.publish_progress(float(i) * 100 / docs, title='Deleting sample records', description='Please wait...')

	return {'status': 'Success'}

@frappe.whitelist(allow_guest=True)
def product_detail_onscroll(productid, layout, domain=None):
	from go1_commerce.go1_commerce.api import get_bestsellers, get_product_other_info, get_customer_recently_viewed_products
	contexts = {}
	business =frappe.db.get_value('Product',productid,'restaurant')
	catalog_settings=get_settings_from_domain('Catalog Settings', business=business)
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
	categories_list = frappe.db.sql('''select category, category_name, (select route from `tabProduct Category` c where c.name = pcm.category) as route from `tabProduct Category Mapping` pcm where parent = %(parent)s order by idx limit 1''', {'parent': productid}, as_dict=1)
	for category in categories_list:
		check_product_box = frappe.db.get_value("Product Category",category.category,'product_box_for_list_view')
		if check_product_box:
			contexts['product_box']=frappe.db.get_value('Product Box',check_product_box,'route')
		else:
			from go1_commerce.go1_commerce.api import get_parent_categorie
			parent_categories = get_parent_categorie(category.category)
			for parent_category in parent_categories:
				check_product_box = frappe.db.get_value("Product Category",parent_category.name,'product_box_for_list_view')
				if check_product_box:
					contexts['product_box']=frappe.db.get_value('Product Box',check_product_box,'route')
	a_related_products = a_best_seller_category = a_products_purchased_together = []
	a_product_category = categories_list[0] if categories_list else {}
	if catalog_settings.customers_who_bought or catalog_settings.enable_best_sellers or catalog_settings.enable_related_products:
		additional_info = get_product_other_info(productid, domain)
		a_related_products = additional_info['related_products']
		a_best_seller_category = additional_info['best_seller_category']
		a_products_purchased_together = additional_info['products_purchased_together']
	contexts['related_products'] = a_related_products
	contexts['bestseller_item'] = a_best_seller_category
	contexts['show_best_sellers'] = a_products_purchased_together
	contexts['product_category'] = a_product_category
	contexts['recent_viewed_products'] = get_customer_recently_viewed_products(domain=domain)
	if layout=="Meat Layout":
		product_enquiry = get_product_scroll(productid, 1, 5)
		contexts['product_enquiry'] = product_enquiry
		contexts['approved_reviews'] = get_product_reviews_list(productid, 0, 10)
		contexts['approved_total_reviews'] = frappe.db.get_value('Product',productid,'approved_total_reviews')
		if catalog_settings.upload_review_images:
			review_images = frappe.db.sql('''select RI.review_thumbnail,RI.image,RI.list_image,RI.parent,RI.name,PR.product from `tabProduct Review` PR inner join `tabReview Image` RI on PR.name=RI.parent where PR.product=%(product)s''',{'product':productid},as_dict=1)
			contexts['review_img'] = review_images
		template = frappe.render_template("/templates/pages/DetailPage/detailpage_otherinfo_meat.html", contexts)
	else:
		template = frappe.render_template("/templates/pages/DetailPage/additional_product_info.html", contexts)
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
				attr.attribute= frappe.db.get_value("Product Attribute",item.get('product_attribute'), "attribute_name")
				attr.attribute_unique_name= frappe.db.get_value("Product Attribute",item.get('product_attribute'), "unique_name")
				attr.control_type= item.get('control_type')
				attr.display_order= item.get('display_order')
				attr.is_required= item.get('is_required')
				attr.product_attribute= item.get('product_attribute')
				attr.quantity= item.get('quantity')
				if item.get('name'):
					attr.save()
				else:
					attr.insert()
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
						else:
							docs.insert()
		
		return doc
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.product.insert_product_attribute_and_options") 

@frappe.whitelist()
def get_doc_images(dt, dn):
	if dt == "Product Category":		
		products = frappe.db.sql_list('''select m.parent from `tabProduct Category Mapping` m inner join tabProduct p on p.name = m.parent where m.category = %(name)s group by p.name''',{'name': dn})
	elif dt == "Product Brand":
		products = frappe.db.sql_list('''select m.parent from `tabProduct Brand Mapping` m inner join tabProduct p on p.name = m.parent where m.brand = %(name)s group by p.name''',{'name': dn})
	elif dt == "Product":
		products = [dn]
	if products and len(products) > 0:
		product_list = ",".join(['"' + i + '"' for i in products])
		return frappe.db.sql('''select list_image, detail_thumbnail as thumbnail, product_image from `tabProduct Image` where parent in ({product}) order by idx'''.format(product=product_list), as_dict=1)
	return []

@frappe.whitelist()
def upload_galleryimg():
	import base64
	from go1_commerce.go1_commerce.mobileapi import get_uploaded_file_content, update_doc
	from go1_commerce.go1_commerce.api import update_to_file

	files = frappe.request.files
	content = None
	filename = None
	img_type = frappe.form_dict.type
	attached_to_doctype = frappe.form_dict.doctype
	attached_to_name = frappe.form_dict.docname
	child_doc = frappe.form_dict.child_doc
	child_name = frappe.form_dict.child_name
	attached_to_field = frappe.form_dict.attached_to_field
	img_field = frappe.form_dict.img_field
	val = []
	if 'files[]' in files:
		file = files['files[]']
		content = file.stream.read()
		filename = file.filename
	if content:
		ret = frappe.get_doc({
			"doctype": "File",
			"attached_to_doctype": attached_to_doctype,
			"attached_to_name": attached_to_name,
			"folder": "Home",
			"file_name": filename,
			"is_private": 0,
			"content": content
			}).insert(ignore_permissions=True)
		if child_doc and attached_to_field:
			update_to_file(ret.file_name, ret.attached_to_doctype, img_type, ret.file_url, ret.attached_to_name, ret.name, 1,
	1, ret.attached_to_doctype, attached_to_field, image_doctype='Product Image', img_field=None)



@frappe.whitelist(allow_guest=True)
def get_attributes_combination(product):
	combination=frappe.db.get_all('Product Variant Combination',filters={'parent':product},fields=['*'])
	productdoc=frappe.db.get_all('Product',fields=['*'],filters={'name':product})
	return combination,productdoc

@frappe.whitelist(allow_guest=True)
def get_attributes_name(attribute_id,product):
	combination=frappe.db.get_all('Product Variant Combination',filters={'parent':product,'attribute_id':attribute_id.replace(",","\n")if attribute_id else "",},fields=['*'])	
	return combination

@frappe.whitelist()
def create_product(source_name, target_doc=None):
	doc = get_mapped_doc('Product', source_name, {
		'Product': {
			'doctype': 'Product'
		},
		'Product Pricing Rule': {
			'doctype': 'Product Pricing Rule',
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

@frappe.whitelist(allow_guest=True)
def get_all_options(attribute=None):
	filters={}
	if attribute:
		filters["parent"]= attribute
	options = frappe.get_all("Add On Option", fields=["options"], filters=filters)
	return options
