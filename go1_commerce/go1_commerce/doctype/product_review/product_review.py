# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt
from frappe.model.naming import make_autoname
from go1_commerce.utils.setup import get_settings
from frappe.query_builder import DocType, Field

class ProductReview(Document):
	def autoname(self):
		self.name = make_autoname(self.naming_series + '.#####', doc=self)

	def validate(self):		
		if self.email:
			customer=frappe.db.get_all('Customers',filters={'email':self.email})
			if customer:
				if self.is_approved:
					self.approve_review_reward(customer[0].name)

	def after_insert(self):
		frappe.publish_realtime('update_menu', {'docname': self.name,'doctype':'Product Review'})
		
	def on_update(self):		
		product=frappe.get_doc("Product",self.product)
		ProductReview = DocType('Product Review')
		review = (
			frappe.qb.from_(ProductReview)
			.select(
				ProductReview.rating.sum().as_('sum'),
				frappe.qb.functions.Count(ProductReview.rating).as_('cnt')
			)
			.where(
				(ProductReview.is_approved == 1) &
				(ProductReview.product == self.product)
			)
		).run(as_dict=True)	
		star=0
		if review:
			if int(review[0].cnt)>0:				
				star=flt(review[0].sum)/flt(review[0].cnt)		
		if star >=0:			
			frappe.db.set_value('Product',product.name,'approved_total_reviews',star)
		media_settings=get_settings('Media Settings')
		list_size=media_settings.list_thumbnail_size
		for review_image in self.review_images:
			file_doc = frappe.get_doc("File", {
					"file_url": review_image.image,
					"attached_to_doctype": "Product Review",
					"attached_to_name": review_image.parent
				})
			if file_doc:
				list_file_doc = frappe.get_doc("File", {
					"file_url": review_image.image,
					"attached_to_doctype": "Product Review",
					"attached_to_name": review_image.parent
				})
				image_file=review_image.image.split('.')
				convert_product_image(review_image.image,list_size,self.name)
				review_image.list_image=image_file[0]+"_"+str(list_size)+"x"+\
											str(list_size)+"."+image_file[len(image_file)-1]
				review_image.save()
				convert_product_image(review_image.image,media_settings.detail_thumbnail_size,self.name)
				review_image.review_thumbnail = image_file[0]+"_"+str(media_settings.\
										detail_thumbnail_size)+"x"+str(media_settings.\
										detail_thumbnail_size)+"."+image_file[len(image_file)-1]
				review_image.save()
					
			
	def on_trash(self):		
		product=frappe.get_doc("Product",self.product)
		ProductReview = DocType('Product Review')
		review = (
			frappe.qb.from_(ProductReview)
			.select(
				ProductReview.rating.sum().as_('sum'),
				frappe.qb.functions.Count(ProductReview.rating).as_('cnt')
			)
			.where(
				(ProductReview.is_approved == 1) &
				(ProductReview.product == self.product)
			)
		).run(as_dict=True)
			
		star=0
		if review:
			if int(review[0].cnt)>1:				
				star=flt(review[0].sum)/flt(review[0].cnt)	
			else:
				frappe.db.set_value('Product',product.name,'approved_total_reviews',star)
			
		if star >=0:			
			frappe.db.set_value('Product',product.name,'approved_total_reviews',star)
		else:
			frappe.db.set_value('Product',product.name,'approved_total_reviews',star)


	def approve_review_reward(self,customer):
		order_settings = get_settings('Order Settings')
		reward=frappe.db.get_all('Reward Points Usage History',fields=['*'],
			filters={'customer_id':customer,'message':'Reward Point for Product Review '+self.name})
		if not reward:
			if order_settings.enabled:
				if order_settings.points_for_product_review:
					result= frappe.get_doc({
						"doctype": "Reward Points Usage History",
						"customer_id":customer,
						"points":order_settings.points_for_product_review,
						"amount":0,
						"message": "Reward Point for Product Review "+self.name
						}).insert(ignore_permissions=True)


def convert_product_image(image_name,size,productid):
	try:
		image_file=image_name.split('.')
		image_file_name=image_file[0]+"_"+str(size)+"x"+str(size)+"."+image_file[1]
		org_file_doc = frappe.get_doc("File", {
					"file_url": image_name,
					"attached_to_doctype": "Product Review",
					"attached_to_name": productid
				})
		if org_file_doc:
			org_file_doc.make_thumbnail(set_as_thumbnail=False,width=size,height=size,
												suffix=str(size)+"x"+str(size))
	except Exception:
		frappe.log_error(frappe.get_traceback(), 
			"Error in doctype.product_review.convert_product_image") 

# updated by Kavitha on 28 Nov 2020
def get_query_condition(user):
	if not user: user = frappe.session.user
	