# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator
from frappe.model.naming import make_autoname
from frappe.utils.nestedset import NestedSet
from frappe.website.utils import clear_cache
import os,re
import json
from frappe import _

nsm_parent_field = 'parent_product_category'

class ProductCategory(WebsiteGenerator, NestedSet):
	def autoname(self):		
		naming_series = self.naming_series
		self.name = make_autoname(naming_series+'.#####', doc=self)
		
	def validate(self):
		self.product_category_name = self.category_name
		if not self.parent_product_category:
			self.parent_category_name = None

		if not self.parent_product_category and not frappe.flags.in_test:
			if frappe.db.exists("Product Category", _('All Product Categories')):
				self.parent_product_category = _('All Product Categories')
		
		self.make_route()
		if self.product_image_size!=frappe.db.get_value('Product Category',
												  self.name,'product_image_size'):
			frappe.enqueue("go1_commerce.go1_commerce.doctype.\
				product_category.product_category.update_image_thumbnail", doc=self, now=frappe.flags.in_test)
		if not self.meta_title:
			self.meta_title = self.category_name
		if not self.meta_keywords:
			self.meta_keywords = self.category_name.replace(" ", ", ")
		if not self.meta_description:
			self.meta_description="About: "+self.category_name
		

	def on_update(self):
		update_whoose_search(self)
		NestedSet.on_update(self)
		invalidate_cache_for(self)
		self.validate_one_root()
		if self.category_image:
			convert_product_image(self.category_image,45,self.name)
			file_name=self.category_image.split('.')
			self.category_thumbnail=file_name[0]+"_"+str(45)+"x"+str(45)+"."+file_name[len(file_name)-1]			
		if self.is_active==1:
			frappe.enqueue('go1_commerce.go1_commerce.doctype.product_category.product_category.update_category_data_json',queue = 'short',at_front = True,doc = self)


	def on_trash(self):	
		delete_whoose_data(self)	
		NestedSet.on_update(self)
	

	def make_route(self):
		self.route = ''
		if self.parent_product_category:
			parent_product_category = frappe.get_doc('Product Category', 
										 		self.parent_product_category)
			if parent_product_category:
				self.route = self.scrub(parent_product_category.category_name) + '-'
				if parent_product_category.parent_product_category:
					parent_category = frappe.get_doc('Product Category', 
								   parent_product_category.parent_product_category)
					if parent_category :
						self.route = self.scrub(parent_category.category_name) + \
								'-' +self.scrub(parent_product_category.category_name) + '-'
						if parent_category.parent_product_category:
							parent_parent_category = frappe.get_doc('Product Category', 
											parent_category.parent_product_category)
							if parent_parent_category:
								self.route = self.scrub(parent_product_category.category_name) + \
									'-' +self.scrub(parent_category.category_name) + \
									'-'+self.scrub(parent_parent_category.category_name) + '-'
		self.route += self.scrub(self.category_name)
	
	
@frappe.whitelist()
def get_children(doctype, parent=None, is_root=False):
	try:
		if parent == None or parent == "All Categories":
			parent = ""
		if is_root:
			parent = ""
		product_category = frappe.db.sql("""
											SELECT 
								   				name AS value, category_name AS label, 
								   				is_group AS expandable 
											FROM `tabProduct Category` 
											WHERE IFNULL(`parent_product_category`, '') = %(parent)s 
											
											ORDER BY name
										""", {'parent': parent}, as_dict=1)

		return product_category
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.product_category.get_children") 
	
 
@frappe.whitelist()
def add_customer_withparent(data, parent):
	data = json.loads(data)
	new_doc = frappe.new_doc('Product Category')
	new_doc.parent_product_category= data['parent_product_category']
	new_doc.category_name = data['category_name']
	new_doc.is_group = data['is_group']
	new_doc.flags.ignore_permissions=True
	new_doc.insert()
	return new_doc


@frappe.whitelist()
def add_node():	
	try:
		args = make_cat_tree_args(**frappe.form_dict)	
		if args.is_root:
			args.parent_product_category = None
		frappe.get_doc(args).insert()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.product_category.add_node") 
	
def make_cat_tree_args(**kwarg):
	try:
		del kwarg['cmd']

		doctype = kwarg['doctype']
		parent_field = 'parent_' + doctype.lower().replace(' ', '_')
		name_field = "category_name"
		if kwarg['is_root'] == 'false': kwarg['is_root'] = False
		if kwarg['is_root'] == 'true': kwarg['is_root'] = True

		kwarg.update({
			name_field: kwarg[name_field],
			parent_field: kwarg.get("parent") or kwarg.get(parent_field)
		})

		return frappe._dict(kwarg)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.product_category.make_cat_tree_args") 
	
 
@frappe.whitelist()
def update_image_thumbnail(doc):
	try:
		all_products=frappe.db.sql("""
									SELECT P.name 
									FROM tabProduct P 
									INNER JOIN `tabProduct Category Mapping` CM ON P.name = CM.parent 
									WHERE CM.category = %(category)s 
									GROUP BY P.name
								""", {'category': doc.name}, as_dict=1)

		if all_products:
			for item in all_products:
				product=frappe.get_doc('Product',item.name)
				product.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), 
				   "Error in doctype.product_category.update_image_thumbnail") 

def convert_product_image(image_name,size,productid):
	try:
		image_file=image_name.split('.')
		image_file_name=image_file[0]+"_"+str(size)+"x"+str(size)+"."+image_file[1]
		org_file_doc = frappe.get_doc("File", {
					"file_url": image_name,
					"attached_to_doctype": "Product Category",
					"attached_to_name": productid
				})
		if org_file_doc:
			org_file_doc.make_thumbnail(set_as_thumbnail=False,width=size,
							   height=size,suffix=str(size)+"x"+str(size))
	except Exception:
		frappe.log_error(frappe.get_traceback(), 
				   "Error in doctype.product_category.convert_product_image") 

def invalidate_cache_for(doc, product_category=None):
	if not product_category:
		product_category = doc.name

	for d in get_parent_product_categories(product_category):
		product_category_name = frappe.db.get_value("Product Category", d.get('name'))
		if product_category_name:
			clear_cache(frappe.db.get_value('Product Category', product_category_name, 'route'))

		
def get_parent_product_categories(item_group_name):
	base_parents = [{"name": frappe._("Home"), "route":"/"}]
	if not item_group_name:
		return base_parents
	item_group = frappe.get_doc("Product Category", item_group_name)
	parent_groups = frappe.db.sql("""
									SELECT name, route 
									FROM `tabProduct Category`
									WHERE lft <= %(lft)s 
									AND rgt >= %(rgt)s
									AND is_active = 1
									ORDER BY lft ASC
								""", {'lft': item_group.lft, 'rgt': item_group.rgt}, as_dict=True)

	return base_parents + parent_groups


def get_child_groups(product_category_name):
	product_category = frappe.get_doc("Product Category", product_category_name)
	return frappe.db.sql("""
							SELECT name
							FROM `tabProduct Category` 
							WHERE lft >= %(lft)s 
							AND rgt <= %(rgt)s
							AND is_active = 1
						""", {'lft': product_category.lft, 'rgt': product_category.rgt})


@frappe.whitelist()
def get_parent_category(txt):
	condition=''
	if txt:
		condition += ' and (name like "%{txt}%" or category_name like "%{txt}%")'.format(txt=txt)

	return frappe.db.sql("""
							SELECT name, category_name 
							FROM `tabProduct Category` 
							WHERE is_group = 1 {condition}
						""".format(condition=condition))

def save_cdn_to_local(org_image,title,size,column_name,id):
	import base64
	import requests
	url=org_image
	content = base64.b64encode(requests.get(url+"?height="+str(size)).content)
	decode_content = base64.decodebytes(content)
	res = frappe.get_doc({"doctype": "File","attached_to_field":"mini_cart",
					   "attached_to_doctype": "Product Image","attached_to_name": id,
					   "file_name": title,"is_private":0,"content": decode_content})
	res.save(ignore_permissions=True)


@frappe.whitelist()
def update_category_data_json(doc):
	from frappe.utils import get_files_path	
	path = get_files_path()
	cat_route = doc.route
	cat_route = cat_route.replace("/","-")
	if not os.path.exists(os.path.join(path,cat_route+"-"+doc.name)):
		frappe.create_folder(os.path.join(path,cat_route+"-"+doc.name))
	from go1_commerce.go1_commerce.v2.category import get_category_filters_json
	filters_resp = get_category_filters_json(category=doc.name)
	if filters_resp.get("attribute_list"):
		with open(os.path.join(path,(cat_route+"-"+doc.name), 'attributes.json'), "w") as f:
			content = json.dumps(filters_resp.get("attribute_list"), separators=(',', ':'))
			f.write(content)
	if filters_resp.get("brand_list"):
		with open(os.path.join(path,(cat_route+"-"+doc.name), 'brands.json'), "w") as f:
			content = json.dumps(filters_resp.get("brand_list"), separators=(',', ':'))
			f.write(content)
	if filters_resp.get("category_list"):
		with open(os.path.join(path,(cat_route+"-"+doc.name), 'categories.json'), "w") as f:
			content = json.dumps(filters_resp.get("category_list"), separators=(',', ':'))
			f.write(content)

			
def update_whoose_search(self):
	try:
		from go1_commerce.go1_commerce.v2.whoosh import insert_update_search_data
		send__data = []
		dict__ = {}
		dict__['name'] = self.name
		dict__['title'] = self.category_name
		dict__['route'] = self.route
		dict__['type'] = "Product Category"
		dict__['search_keyword'] = self.category_name
		send__data.append(dict__)
		insert_update_search_data(send__data)
	except Exception:
		frappe.log_error(title="Error in update product search data",message = frappe.get_traceback())

def delete_whoose_data(self):
	try:
		from go1_commerce.go1_commerce.v2.whoosh import remove_deleted_data
		remove_deleted_data([self.name])
	except Exception:
		frappe.log_error(title="Error in delete product search data",message = frappe.get_traceback())