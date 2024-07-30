# -*- coding: utf-8 -*-
# Copyright (c) 2020, Tridots Tech and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator
from frappe.website.utils import clear_cache


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
			if temp.header_template:
				context.header_file = frappe.db.get_value('Header Template', temp.header_template, 'route')
			if temp.footer_template:
				context.footer_file = frappe.db.get_value('Footer Template', temp.footer_template, 'route')
			enable_generate_html=frappe.db.get_single_value("CMS Settings", "generate_html")
			if enable_generate_html or temp.document:
				context.template = temp.file_path
		blog_tag = ""
		blog_tag1 = ""
		tag_item = frappe.db.get_all('Blog Tag Item',fields=['*'],filters={'blog_tag':self.name})
		if tag_item:
			for item in tag_item:
				blog_tag = frappe.db.sql('''select * from `tabBlog Post` where name=%(name)s''',
							 					{'name':item.parent},as_dict=1)
			blog_tag1 = blog_tag
		context.BlogList=blog_tag1
		BlogCateogories=frappe.db.get_all('Blog Category',fields=['*'], filters={'published':1})
		context.BlogCateogories=BlogCateogories 


@frappe.whitelist(allow_guest=True)
def get_tag_based_blog_list(tag = None, page_no = 1, page_size = 12):
	start = (int(page_no) - 1) * int(page_size)
	data = frappe.db.sql(f"""SELECT B.* 
							FROM `tabBlog Post` B 
							LEFT JOIN `tabBlog Tag Item` C ON C.parent = B.name 
							WHERE B.published = 1 
								AND C.parenttype = "Blog Post" 
								AND C.parentfield = "blog_tag" 
								AND C.blog_tag = '{tag}' 
							GROUP BY B.name 
							ORDER BY B.published_on DESC 
							LIMIT {start}, {page_size}
						""")
	return data