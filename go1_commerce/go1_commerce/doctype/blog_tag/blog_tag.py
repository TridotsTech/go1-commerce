# -*- coding: utf-8 -*-
# Copyright (c) 2020, Tridots Tech and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator
from frappe.website.utils import clear_cache
from frappe.query_builder import DocType, Order

class BlogTag(WebsiteGenerator):
	def autoname(self):
		self.name = self.tag_name

	def on_update(self):
		clear_cache()
	
	def validate(self):
		if not self.route:
			self.route = 'RecipeCorner/tag/' + self.scrub(self.name)

	def get_context(self, context):
		filters={"document":self.doctype,"published":1}
		temp = frappe.db.get_value("Web Page Builder",
					filters,["file_path","header_template","footer_template","name", "document"],as_dict=1)
		if temp:
			enable_generate_html=frappe.db.get_single_value("CMS Settings", "generate_html")
			if enable_generate_html or temp.document:
				context.template = temp.file_path
		blog_tag = ""
		blog_tag1 = ""
		tag_item = frappe.db.get_all('Blog Tag Item',fields=['*'],filters={'blog_tag':self.name})
		if tag_item:
			for item in tag_item:
				BlogPost = DocType('Blog Post')
				blog_tag = (
				    frappe.qb.from_(BlogPost)
				    .select('*')
				    .where(BlogPost.name == item.parent)
				    .run(as_dict=True)
				)
			blog_tag1 = blog_tag
		context.BlogList=blog_tag1
		BlogCateogories=frappe.db.get_all('Blog Category',fields=['*'], filters={'published':1})
		context.BlogCateogories=BlogCateogories 


def get_tag_based_blog_list(tag = None, page_no = 1, page_size = 12):
	start = (int(page_no) - 1) * int(page_size)
	BlogPost = DocType('Blog Post')
	BlogTagItem = DocType('Blog Tag Item')
	query = (
	    frappe.qb.from_(BlogPost)
	    .left_join(BlogTagItem).on(BlogTagItem.parent == BlogPost.name)
	    .select(BlogPost.star)
	    .where(
	        (BlogPost.published == 1) &
	        (BlogTagItem.parenttype == "Blog Post") &
	        (BlogTagItem.parentfield == "blog_tag") &
	        (BlogTagItem.blog_tag == tag)
	    )
	    .groupby(BlogPost.name)
	    .orderby(BlogPost.published_on, order=Order.desc)
	    .limit(page_size)
	    .offset(start)
	)
	data = query.run(as_dict=True)
	return data