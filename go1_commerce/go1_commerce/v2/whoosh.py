import frappe,os
from frappe.utils import get_files_path
from whoosh import query,qparser,sorting
from whoosh.index import create_in,open_dir
from whoosh.fields import Schema, TEXT,ID
from whoosh.qparser import MultifieldParser
from whoosh.query import *
import json

def insert_update_search_data(search__info):
	try:		
		path = get_files_path()	
		file_name = os.path.join(path,'ecommerce_search')
		if not os.path.exists(file_name):
			schema = Schema(name = ID(unique = True),product_image=TEXT(stored = True),
								product_id=TEXT(stored = True),title = TEXT(stored = True),
								route = TEXT(stored = True),type = TEXT(stored = True),
								warehouse = TEXT(stored = True),search_keyword = TEXT(stored = True),
								ir_prime = TEXT(stored = True))
			frappe.create_folder(file_name)
			ix = create_in(file_name, schema)
		else:
			ix = open_dir(file_name)
		for each_data in search__info:
			writer = ix.writer()
			writer.add_document(name = each_data.get('name'),product_image = each_data.get('product_image'),
					   product_id = each_data.get('product_id'),title = each_data.get('title'),
					   route = each_data.get('route'),type = each_data.get('type'),
					   warehouse = each_data.get('warehouse'),search_keyword = each_data.get('search_keyword'),
					   ir_prime = str(each_data.get('ir_prime')) if each_data.get('ir_prime') else "0")
			writer.commit()
	except Exception:
		frappe.log_error(title = 'Error while updating whoose search data',message = frappe.get_traceback())
	finally:
		ix.close()

def remove_deleted_data(r__m_array):
	try:
		path = get_files_path()
		file_name = os.path.join(path,'ecommerce_search')
		if os.path.exists(file_name):
			ix = open_dir(file_name)
			for del__item in r__m_array:	
				writer = ix.writer() 
				query = MultifieldParser(["name"],ix.schema).parse(del__item)
				writer.delete_by_query(query)
				writer.commit()
			ix.close()
	except Exception:
		frappe.log_error(frappe.get_traceback(),"Error in delete whoosh search data")

@frappe.whitelist(allow_guest = True)
def search_product(search_txt,page_no = 1,page_length = 10):
	try:
		results = []
		path = get_files_path()
		file_name = os.path.join(path,'ecommerce_search')
		ix = open_dir(file_name)
		from whoosh import fields, query, sorting
		with ix.searcher() as searcher:
			query1 = MultifieldParser(["search_keyword","title"],ix.schema).parse(search_txt+"*")
			facet = sorting.FieldFacet("title", reverse=False)
			resp_results = searcher.search_page(query1, 1,pagelen = 1000000,sortedby = facet)
			if resp_results:
				for resp in resp_results:
					if not check_value_in_array(results,resp.get("product_id"),"product_id"):
						results.append({
							"product_id":resp.get("product_id"),
							"title":resp.get("title"),
							"route":resp.get("route"),
							"search_keyword":resp.get("search_keyword"),
							})
		p_data = get_paginated_data(results,page_no,page_length)
		p_ids = ""
		for x in p_data:
			p_ids += "'"+x.get("product_id")+"',"
		p_ids = p_ids[:-1]
		p_list = []
		if p_ids:
			Product = DocType('Product')
			ProductBrandMapping = DocType('Product Brand Mapping')
			ProductVariantCombination = DocType('Product Variant Combination')
			p_query = (
			    frappe.qb.from_(Product).select(
			        Product.item.as_('product'),Product.item,
			        Product.image.as_('product_image'),Product.sku,
			        Product.name,Product.route,Product.price,
			        Product.old_price,Product.has_variants,Product.short_description,
			        Product.tax_category,Product.full_description,Product.inventory_method,
			        Product.disable_add_to_cart_button,Product.weight,
			        Product.gross_weight,Product.approved_total_reviews,Product.route.as_('brand_route'),
			        (frappe.qb.from_(ProductBrandMapping)
			         .select(ProductBrandMapping.brand_name)
			         .where(ProductBrandMapping.parent == Product.name)
			         .limit(1)).as_('product_brand'))
			    .where(Product.is_active == 1)
			    .where(Product.show_in_market_place == 1)
			    .where(Product.status == 'Approved')
			    .where((((Product.has_variants == 1) & (frappe.qb.from_(ProductVariantCombination)
			              .select(ProductVariantCombination.name)
			              .where(ProductVariantCombination.show_in_market_place == 1)
			              .where(ProductVariantCombination.disabled == 0)
			              .exists())) |((Product.has_variants == 0) & Product.exists()))))
			p_search_list = p_query.run(as_dict=True)
			from go1_commerce.go1_commerce.v2.product import get_list_product_details
			p_list = get_list_product_details(p_search_list)
		frappe.response.status = "Success"
		return p_list
	except Exception:
		frappe.response.status = 'Failed'
		frappe.response.message = 'something went wrong'
		frappe.log_error('Error in search product api ',frappe.get_traceback())

def get_paginated_data(data_list, page_number, page_size):
    start_index = (int(page_number) - 1) * int(page_size)
    end_index = start_index + int(page_size)
    paginated_data = data_list[start_index:end_index]
    return paginated_data

def check_value_in_array(array, value, property_name):
    for obj in array:
        if obj.get(property_name) == value:
            return True
    return False

@frappe.whitelist()
def update_order_item(doc,method):
	if doc.order_item:
		for x in doc.order_item:
			pr = frappe.get_doc("Product",x.item)
			from go1_commerce.go1_commerce.doctype.product.product \
			import update_whoose_search
			update_whoose_search(pr)

@frappe.whitelist(allow_guest = True)
def update_products(doc):
	for x in doc.get('items'):
		pr_doc = frappe.get_doc("Product",x.get("product"))
		frappe.enqueue('go1_commerce.go1_commerce.doctype.product.product.update_whoose_search',self = pr_doc)
	return {"status":"success"}