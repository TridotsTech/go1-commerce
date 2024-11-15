# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe, json
from frappe import _
from go1_commerce.utils.setup import get_settings_from_domain, get_theme_settings
from frappe.query_builder import DocType

@frappe.whitelist()
def get_all_products_with_attributes(category=None, brand=None, item_name=None, active=None, featured=None, page_start=0, page_end=20):
	try:
		lists=[]
		subcat=get_products(category=category, brand=brand, item_name=item_name, active=active, featured=featured, page_start=page_start, page_end=page_end)
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
		ProductAttributeOption = DocType('Product Attribute Option')
		ProductAttributeMapping = DocType('Product Attribute Mapping')
		query = (
			frappe.qb.from_(ProductAttributeOption)
			.inner_join(ProductAttributeMapping).on(ProductAttributeOption.attribute_id == ProductAttributeMapping.name)
			.select(
				ProductAttributeOption.name.as_("docname"),
				frappe.qb.concat_ws(' - ', ProductAttributeMapping.attribute, ProductAttributeOption.parent_option).as_("name"),
				ProductAttributeOption.option_value.as_("item"),
				ProductAttributeOption.parent_option,
				ProductAttributeOption.price_adjustment.as_("price"),
				ProductAttributeOption.attribute
			)
			.where(ProductAttributeMapping.parent == name)
			.orderby(ProductAttributeMapping.display_order, "name")
		)
		return query.run(as_dict=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.page.products_bulk_update.get_product_attributes") 

@frappe.whitelist()
def get_products(category=None, brand=None, cat_doctype=None, brand_doctype=None, item_name=None, active=None, featured=None, page_start=0, page_end=20):
	try:
		Product = DocType('Product')
		ProductCategoryMapping = DocType('Product Category Mapping')
		ProductBrandMapping = DocType('Product Brand Mapping')
		ProductImage = DocType('Product Image')
		query = frappe.qb.from_(Product).select(
			Product.name,
			Product.item,
			Product.price,
			Product.sku,
			Product.old_price,
			Product.stock,
			Product.inventory_method,
			Product.name.as_("docname"),
			frappe.qb.case().when(Product.is_active > 0, 'Yes').else_('No').as_("is_active"),
			frappe.qb.case().when(Product.display_home_page > 0, 'Yes').else_('No').as_("display_home_page"),
			Product.name.as_("id"),
			Product.name.as_("name1")
		)
		
		if category:
			query = query.inner_join(ProductCategoryMapping).on(ProductCategoryMapping.parent == Product.name)
			query = query.where(ProductCategoryMapping.category == category)
		
		if brand:
			query = query.inner_join(ProductBrandMapping).on(ProductBrandMapping.parent == Product.name)
			query = query.where(ProductBrandMapping.brand == brand)
		if item_name:
			query = query.where(Product.item.like(f"%{item_name}%"))
		
		if active:
			active = 1 if active == "Yes" else 0
			query = query.where(Product.is_active == active)
		
		if featured:
			featured = 1 if featured == "Yes" else 0
			query = query.where(Product.display_home_page == featured)
		query = query.limit(page_start, page_end)
		products = query.run(as_dict=True)
		for item in products:
			images = (frappe.qb.from_(ProductImage).select(
				ProductImage.detail_thumbnail,
				ProductImage.detail_image
			).where(ProductImage.parent == item['name']).orderby(ProductImage.is_primary, order=Order.desc).run(as_dict=True))
			
			image_html = '<div class="row">'
			for img in images:
				if img['detail_thumbnail']:
					image_html += f'''
						<div class="col-md-4 popup" data-poster="{img['detail_image']}" data-src="{img['detail_image']}" style="margin-bottom:10px;padding-left:0px;padding-right:0px;">
							<a href="{img['detail_image']}">
								<img class="img-responsive" id="myImg" src="{img['detail_thumbnail']}" onclick="showPopup('{img['detail_image']}')">
							</a>
						</div>'''
			image_html += '</div>'
			item['image'] = image_html

		return products
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.page.products_bulk_update.get_products") 



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
