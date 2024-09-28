from frappe import _
import frappe
from go1_commerce.utils.utils import other_exception
from go1_commerce.utils.setup import get_settings_value
from frappe.query_builder import DocType, Field, Table

def get_category_products_count(category):
	""" Retrieves the count of active and approved products within a category,
	optionally including subcategories based on catalog settings.

	Args:
		category (str): The name of the category to count products for.

	Returns:
		list: A list of dictionaries, each containing the product name and count."""
	category_filter="'"+category+"'"
	if get_settings_value('Catalog Settings','include_products_from_subcategories') == 1:
		child_categories=get_child_categories(category)
		if len(child_categories)>0:
			category_filter+=","
			for x in child_categories:
				category_filter+="'"+x.name+"'"
				if not child_categories.index(x)==len(child_categories)-1:
					category_filter+=","
	try:
		
		categories = [cat.strip() for cat in category_filter.split(',')]
		product_names = frappe.get_all(
			'Product',
			filters={
				'is_active': 1,
				'status': 'Approved',
				'name': ['in', frappe.get_all(
					'Product Category Mapping',
					filters={'category': ['in', categories]},
					fields=['parent']
				)]
			},
			fields=['name']
		)
		product_count = len(set(item['name'] for item in product_names))
		
		return {'COUNT': product_count}
		
	except Exception:
		frappe.log_error(title=_("Error fetching category product counts"),message=frappe.get_traceback())

@frappe.whitelist()
def get_parent_categories(show_count=0):
	""" Retrieves parent product categories and their children, 
		optionally including product counts. """
	try:
		top_level_categories = frappe.get_all(
			"Product Category",
			fields=[
				"category_image",
				"name",
				"category_name",
				"mobile_image",
				"full_description",
				"route",
			],
			filters={"parent_product_category": "", "is_active": 1},
			order_by="display_order",
			limit=50)
		if show_count:
			for category in top_level_categories:
				category.products_count = len(get_category_products_count(category.name))
		for category in top_level_categories:
			category.child = get_child_categories(category.name, show_count, limit=50)
		return top_level_categories
	except Exception:
		frappe.log_error(title=_("Error in v2.category.get_parent_categories"),message=frappe.get_traceback())
		
def get_parent_categorie(category):
	try:
		count = frappe.db.get_value('Product Category', category, ['lft', 'rgt'], as_dict=True)
		if count:
			result = (frappe.qb.from_("tabProduct Category")
			.select("name")
			.where(
				(frappe.qb.col("is_active") == 1) &
				(frappe.qb.col("disable_in_website") == 0) &
				(frappe.qb.col("lft") <= count.lft) &
				(frappe.qb.col("rgt") >= count.rgt)
			)
			.run(as_dict=True))
		
			
			return result
		else:
			return []
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'Error in category.get_parent_categorie')

def get_child_categories(parent_category_name, show_count=0, limit=500):
	""" Retrieves child categories for a given parent recursively."""
	child_categories = frappe.get_all(
		"Product Category",
		fields=[
			"category_image",
			"name",
			"category_name",
			"mobile_image",
			"full_description",
			"route",
		],
		filters={"parent_product_category": parent_category_name, "is_active": 1},
		order_by="display_order",
		limit=limit)

	if show_count:
		for category in child_categories:
			category.products_count = len(get_category_products_count(category.name))
	for category in child_categories:
		category.child = get_child_categories(category.name, show_count, limit=limit)
		
	return child_categories

def get_categories_sidemenu(category):
	try:
		if category:
			category = category.replace('&amp;', '&')
		current_category = get_current_category(category)
		result = {}
		parent_category = None
		parent_categories = None
		if current_category.parent_product_category and \
				current_category.parent_product_category != 'All Product Category':
			parent_category = get_parent_category(current_category)
			result['parent_category'] = parent_category
			if parent_category.parent_product_category:
				parent_categories = get_parent_category_list(parent_category)
				result['parent_categories'] = parent_categories
		parent_category_child = get_parent_category_child(current_category)
		child_categories = get_child_categories(category)
		result['parent_category_child'] = parent_category_child
		result['child_categories'] = child_categories
		result['current_category'] = current_category
		all_categories = get_all_categories()
		result['all_categories'] = all_categories
		return result
	except Exception as e:
		frappe.log_error(title = 'Error in get_categories_sidemenu',message = _("Error in get_categories_sidemenu: {0}").format(str(e)))
		
def get_parent_category_child(current_category):
	filters = {
		'parent_product_category': current_category.parent_product_category,
		'is_active': 1, 'disable_in_website': 0
	}
	return frappe.get_all('Product Category',
						  fields=['name', 'category_name', 'route'],
						  filters=filters, order_by='display_order', limit_page_length=50)

def get_all_categories():
	filters = {'parent_product_category': '', 'is_active': 1, 'disable_in_website': 0}
	return frappe.get_all('Product Category',
						  fields=['name', 'category_name', 'route'],
						  filters=filters, order_by='display_order', limit_page_length=50)

def get_current_category(category):
	current_category_list = frappe.get_all('Product Category',
										   fields=['name', 'category_name', 'route'],
										   filters={"name": category})
	return current_category_list[0] if current_category_list else None

def get_parent_category(current_category):
	parent_category = frappe.get_doc('Product Category', current_category.parent_product_category)
	parent_category.parent_category_route = parent_category.route
	parent_category.parent_parent_category_route = frappe.db.get_value(
		'Product Category', parent_category.parent_product_category, "route")
	parent_category.parent_parent_category_name = frappe.db.get_value(
		'Product Category', parent_category.parent_product_category, "category_name")
	return parent_category

def get_parent_category_list(parent_category):
	filters = {
		'parent_product_category': parent_category.parent_product_category,
		'is_active': 1, 'disable_in_website': 0
	}
	return frappe.get_all('Product Category',
						  fields=['name', 'category_name', 'route'],
						  filters=filters, order_by='display_order', limit_page_length=50)

@frappe.whitelist()
def get_category_filters_json(category=None, brands='', ratings='', min_price='', max_price='',route=None):
	try:
		if route:
			categories = frappe.db.get_all("Product Category",filters={"route":route})
			if categories:
				category = categories[0].name
		if category:
			catalog_settings = frappe.get_single('Catalog Settings')
			category_filter = "'" + category + "'"

			if catalog_settings.include_products_from_subcategories == 1:
				child_categories = get_child_categories(category)
				frappe.log_error("child_categories",child_categories)
				if child_categories and len(child_categories)>0:
					category_filter = ','.join(['"' + x.name + '"' for x in child_categories])
				else:
					child_categories = []
					child_categories.append(category)
			p_ids = get_category_product_ids(child_categories)
			brand_filters = get_category_brands_filter(p_ids)
			attribute_filters = get_category_item_attribute_filter(p_ids)
			category_list = get_categories_sidemenu(category)
			category_info = frappe.get_doc("Product Category",category)
			meta_info = {"meta_title":category_info.meta_title,
						"meta_keywords":category_info.meta_keywords,
						"meta_description":category_info.meta_description}
			return {'meta_info':meta_info,'attribute_list': attribute_filters, 
					'brand_list': brand_filters, 'category_list': category_list}
		return {'meta_info':{},'attribute_list': [], 'brand_list': [], 'category_list': []}

	except Exception as e:
		other_exception("Error in v2.category.get_category_filters")
		return {'meta_info':{},'attribute_list': [], 'brand_list': [], 'category_list': []}

@frappe.whitelist()
def get_category_filters(category=None, brands='', ratings='', min_price='', max_price='',route=None):
	
	try:
		meta_info = get_category_meta_info(category, route)
	
		filter_data = get_filter_data_from_json_files(category, route)
		
		return {
			'meta_info': meta_info,
			'attribute_list': filter_data.get('attributes', []),
			'brand_list': filter_data.get('brands', []),
			'category_list': filter_data.get('categories', [])
		}
	except Exception as e:
		frappe.log_error(title=_("Error in v2.category.get_category_filters"),message=frappe.get_traceback(), exc_info=True)
		return {
			'meta_info': {"meta_title":"",
						"meta_keywords":"",
						"meta_description":""},
			'attribute_list': [],
			'brand_list': [],
			'category_list': []
		}

def get_category_meta_info(category=None, route=None):
	meta_title = "" 
	meta_keywords = ""
	meta_description = ""
	if route:
		categories = frappe.db.get_all("Product Category",filters={"route":route},
									fields=['meta_title','meta_keywords','meta_description','name'])
		if categories:
			category = categories[0].name
			meta_title = categories[0].meta_title 
			meta_keywords = categories[0].meta_keywords
			meta_description = categories[0].meta_description
		
	if not route and category:
		meta_title,meta_keywords,meta_description = frappe.db.get_value("Product Category",category,
															['meta_title','meta_keywords','meta_description'])
	meta_info = {"meta_title":meta_title,
				"meta_keywords":meta_keywords,
				"meta_description":meta_description,
				"category":category}
	return meta_info

def get_filter_data_from_json_files(category=None, route=None):
	if route:
		categories = frappe.db.get_all("Product Category",filters={"route":route},
										fields=['meta_title','meta_keywords','meta_description','name'])
		if categories:
			category = categories[0].name
	if not route and category:
		route = frappe.db.get_value("Product Category",category,['route'])
	filter_data = {}
	# frappe.log_error("category_path_route",route)
	# frappe.log_error("category_path_category",category)	
	if route and category:
		from frappe.utils import get_files_path
		import os,json
		path = get_files_path()
		category_path = (route.replace("/","-")+"-"+category)
		for file_name in ["attributes.json", "brands.json", "categories.json"]:
			file_path = os.path.join(path,category_path, file_name)
			if os.path.exists(file_path):
				# frappe.log_error("file_path",file_path)
				try:
					with open(file_path, 'r') as f:
						filter_data[file_name.replace(".json", "")] = json.load(f)
				except (IOError, json.JSONDecodeError) as e:
					frappe.log_error(title=_("Error reading JSON file"), 
									message=f"Error reading {file_name}: {str(e)}")
	# frappe.log_error("filter_data",filter_data)
	return filter_data		


def get_category_option_query(products_filter, attributes):
	for x in attributes:
		product = DocType('Product')
		attribute_mapping = DocType('Product Attribute Mapping')
		attribute_option = DocType('Product Attribute Option')
		attribute_id = x.product_attribute
		query = (
			frappe.qb.from_(product)
			.join(attribute_mapping)
			.on(product.name == attribute_mapping.parent)
			.join(attribute_option)
			.on(
				(attribute_option.parent == product.name) & 
				(attribute_option.attribute == attribute_mapping.product_attribute)
			)
			.select(
				attribute_option.unique_name,
				attribute_option.option_value,
			)
			.where(attribute_option.parent.isin(products_filter))
			.where(attribute_option.attribute == attribute_id)
		)

		results = query.run(as_dict=1)
		x.options = results

	return attributes


def get_category_item_attribute_filter(product_ids):
	products_filter = [x.product for x in product_ids]
	if products_filter:
		product_attribute_mapping = DocType('Product Attribute Mapping')
		product_attribute = DocType('Product Attribute')
		query = (
			frappe.qb.from_(product_attribute_mapping)
			.join(product_attribute)
			.on(product_attribute.name == product_attribute_mapping.product_attribute)
			.select(
				product_attribute_mapping.attribute,
				product_attribute_mapping.product_attribute,
				product_attribute_mapping.attribute_unique_name.as_('attribute_unique_name')
			)
			.where(product_attribute_mapping.parent.isin(products_filter))
		)
		results = query.run(as_dict=1)
	else:
		results = []
	get_category_option_query(products_filter, results)
	return results


def get_category_product_ids(category_filter):
	category_filter_list = []
	for x in category_filter:
		category_filter_list.append(x.name)
	# frappe.log_error("category_filter",category_filter_list)
	product = DocType('Product')
	category_mapping = DocType('Product Category Mapping')
	category = DocType('Product Category')
	query = (
		frappe.qb.from_(product)
		.join(category_mapping)
		.on(product.name == category_mapping.parent)
		.join(category)
		.on(category_mapping.category == category.name)
		.select(product.name.as_('product'))
		.where(product.is_active == 1)
		.where(product.status == 'Approved')
		.where(category.name.isin(category_filter_list))
	)
	results = query.run(as_dict=1)
	# frappe.log_error("results_pids",results)
	return results

def get_category_brands_filter(product_ids):
	products_filter = []
	if product_ids:
		for x in product_ids:
			products_filter.append(x.product)
		product = DocType('Product')
		product_brand = DocType('Product Brand')
		query = (
		frappe.qb.from_(product)
		.join(product_brand)
		.on(product_brand.name == product.brand)
		.select(
			product_brand.name.as_('brand'),
			product_brand.brand_name,
			product_brand.unique_name,
		)
		.where(product.name.isin(products_filter))
		.groupby(product_brand.name,product_brand.unique_name,product_brand.brand_name)
		)
		results = query.run(as_dict=1)
		return results
	return []
