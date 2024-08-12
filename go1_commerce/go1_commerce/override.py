import frappe
from frappe import _
import frappe, json, os
from frappe.model.document import Document
from frappe.core.doctype.file.file import File
from frappe.core.doctype.file.utils import *
from urllib.error import HTTPError
from requests.exceptions import SSLError
from builtins import OSError
from typing import Type, Union
from PIL import Image,ImageOps
from frappe.query_builder import DocType, Interval


class CustomFile(File):
	def make_thumbnail(
			self,
			set_as_thumbnail: bool = True,
			width: int = 300,
			height: int = 300,
			suffix: str = "small",
			crop: bool = False,updated_doc=None,updated_name=None,updated_column=None,
		) -> str:
			if not self.file_url:
				return

			try:
				if self.file_url.startswith(("/files", "/private/files")):
					image, filename, extn = get_local_image(self.file_url)
				else:
					image, filename, extn = get_web_image(self.file_url)
			except (HTTPError, SSLError, OSError, TypeError):
				frappe.log_error("error", frappe.get_traceback())
				return

			size = width, height
			if crop:
				image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
			else:
				image.thumbnail(size, Image.Resampling.LANCZOS)

			thumbnail_url = f"{filename}_{suffix}.{extn}"
			path = os.path.abspath(frappe.get_site_path("public", thumbnail_url.lstrip("/")))

			try:
				image.save(path)
				if set_as_thumbnail:
					self.db_set("thumbnail_url", thumbnail_url)

			except OSError:
				frappe.msgprint(_("Unable to write file format for {0}").format(path))
				return
			return thumbnail_url

class PageSection(Document):
	
	def section_data(self, customer=None, add_info=None):
	 
		json_obj = {}
		json_obj['section'] = self.name
		json_obj['class_name'] = self.class_name
		json_obj['section_name'] = self.section_title
		json_obj['section_type'] = self.section_type
		json_obj['content_type'] = self.content_type
		json_obj['reference_document'] = self.reference_document
		json_obj['no_of_records'] = self.no_of_records
		json_obj['view_type'] = self.view_type
		json_obj['view_more_redirect_to'] = self.view_more_redirect_to
		json_obj['mobile_app_template'] = self.mobile_app_template
		json_obj['login_required'] = self.is_login_required
		json_obj['dynamic_data'] = self.dynamic_data
		json_obj['is_full_width'] = self.is_full_width
		json_obj['layout_json'] = self.layout_json
		if self.section_type == 'Predefined Section' and not self.is_login_required:
			if self.predefined_section=="Recommended Items":
				json_obj['data'] = get_recommended_products(self.query, self.reference_document, self.no_of_records, customer=customer, add_info=add_info)
				json_obj['reference_document'] = self.reference_document
			else:
				json_obj['data'] = get_data_source(self.query, self.reference_document, self.no_of_records, customer=customer, add_info=add_info)
				json_obj['reference_document'] = self.reference_document
		elif self.section_type == 'Custom Section':
			
			if self.content_type == 'Static':
				if self.reference_document == 'Product Category':
					json_obj['route'] = frappe.db.get_value(self.reference_document, self.reference_name, "route")
				json_obj['data'] = json.loads(self.custom_section_data)
			else:
				
				if self.reference_document == 'Product Category' and self.dynamic_data==0:
					json_obj['data'] = json.loads(self.custom_section_data)
				else:
					json_obj['reference_document'] = self.reference_document
					json_obj['reference_name'] = self.reference_name
					json_obj['data'] = get_dynamic_data_source(self, customer=customer)
					
					json_obj['fetch_product'] = self.fetch_product
					if len(json_obj['data']) > 0 and self.reference_name:
						field = None
						if self.reference_document == 'Product Category':
							field = 'category_name'
						if self.reference_document == 'Product Brand':
							field = 'brand_name'
						if self.reference_document == 'Subscription Plan':
							field = 'name'
						if self.reference_document == 'Author':
							field = 'name'
						if self.reference_document == 'Publisher':
							field = 'name'
						if field:
							json_obj['title'] = frappe.db.get_value(self.reference_document, self.reference_name, field)
							if self.reference_document == 'Product Category':
								json_obj['route'] = frappe.db.get_value(self.reference_document, self.reference_name, "route")
		
		elif self.section_type == 'Tabs' and self.reference_document == 'Custom Query':
			if self.reference_document == 'Custom Query':
				data = json.loads(self.custom_section_data)
				for item in data:
					no_of_records = 10
					if item.get('no_of_records'):
						no_of_records = item.get('no_of_records')
					item['name'] = item.get('tab_item').lower().replace(' ', '_')
					
					query_item = frappe.db.get_value(self.reference_document, item.get('tab_item'), 'query')
					EmailCampaign = DocType('Email Campaign') 
					qb = frappe.qb.from_(EmailCampaign)
					qb = qb.select(query_item)
					qb = qb.limit(no_of_records)
					result = qb.run(as_dict=True)

					result = get_product_details(result, customer=customer)
					item['products'] = result
					org_datas = []
					org_datas = get_products_json(result)
					item['products'] = org_datas
				json_obj['data'] = data

		elif self.section_type == 'Lists':
			if 'erp_ecommerce_business_store' in frappe.get_installed_apps():
				from erp_ecommerce_business_store.erp_ecommerce_business_store.page_section import get_list_data
				json_obj['data'] = get_list_data(self, customer=None, add_info=None)

		
		if self.content:
			for item in self.content:
				if item.field_type != 'List':
					json_obj[item.field_key] = item.content
				else:
					json_obj[item.field_key] = json.loads(item.content) if item.content else []

		return json_obj
