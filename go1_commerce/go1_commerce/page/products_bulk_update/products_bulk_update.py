# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe, json
from frappe import _
from go1_commerce.utils.setup import get_settings_from_domain, get_theme_settings

@frappe.whitelist()
def get_all_products_with_attributes(category=None, brand=None, item_name=None, active=None, featured=None, business=None, page_start=0, page_end=20):
	try:
		lists=[]
		subcat=get_products(category=category, brand=brand, item_name=item_name, active=active, featured=featured, business=business, page_start=page_start, page_end=page_end)
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
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.page.products_bulk_update.get_all_products_with_attributes") 
	
@frappe.whitelist()
def get_product_attributes(name):	
	try:
		query = '''select AO.name as docname,concat_ws(' - ', PA.attribute, AO.parent_option) as name,AO.option_value as item, AO.parent_option,AO.price_adjustment as price,AO.attribute from `tabProduct Attribute Option` AO inner join `tabProduct Attribute Mapping` PA on AO.attribute_id=PA.name where PA.parent="{parent}" order by PA.display_order, name'''.format(parent=name)
		s= frappe.db.sql(query,as_dict=1)
		return s
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.page.products_bulk_update.get_product_attributes") 

@frappe.whitelist()
def get_products(category=None,brand=None,cat_doctype=None,brand_doctype=None,item_name=None,active=None,featured=None, business=None, page_start=0, page_end=20):
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
		query = '''select P.name,P.item,P.price,P.sku,P.old_price,P.stock,P.inventory_method,P.name as docname,CASE WHEN P.is_active>0 THEN 'Yes' ELSE 'No' END as is_active,CASE WHEN P.display_home_page>0 THEN 'Yes' ELSE 'No' END as display_home_page,P.name as id,P.name as name1 from `tabProduct` P {joins} where P.name!='' {condition} limit {start}, {limit}'''.format(start=page_start, limit=page_end, condition=filters, joins=joins)
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
		query = '''select P.name,P.item,P.price,P.sku,P.old_price,P.stock,P.inventory_method,P.name as docname,CASE WHEN P.is_active>0 THEN 'Yes' ELSE 'No' END as is_active,CASE WHEN P.display_home_page>0 THEN 'Yes' ELSE 'No' END as display_home_page,P.name as id,P.name as name1 from `tabProduct` P where P.name!= '' {condition} limit {start}, {limit}'''.format(start=page_start, limit=page_end, condition=filters)
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
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.page.products_bulk_update.update_bulk_data") 
