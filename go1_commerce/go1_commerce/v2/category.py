from frappe import _
import frappe
from go1_commerce.utils.utils import other_exception
from go1_commerce.utils.setup import get_settings_value



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

@frappe.whitelist(allow_guest=True)
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
		order_by="mega_menu_column, display_order",
		limit=limit)
	if show_count:
		for category in child_categories:
			category.products_count = len(get_category_products_count(category.name))
	for category in child_categories:
		category.child = get_child_categories(category.name, show_count, limit=limit)
	return child_categories

def get_categories_sidemenu(category):
	try:
		frappe.log_error("get_categories_sidemenu",category)
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

@frappe.whitelist(allow_guest=True)
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
				from go1_commerce.go1_commerce.v2.category \
				import get_child_categories
				child_categories = get_child_categories(category)
				if child_categories:
					category_filter = ','.join(['"' + x.name + '"' for x in child_categories])
			p_ids = get_category_product_ids(category_filter)
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

@frappe.whitelist(allow_guest=True)
def get_category_filters(category=None, brands='', ratings='', min_price='', max_price='',route=None):
	""" Retrieves meta information and filter data for a given product category.
		Args:
			category (str, optional): The name of the category.
			route (str, optional): The route of the category.
			centre (str, optional): The centre.
			seller_classify (str, optional): The seller classification.
			Default is "All Stores".
		Returns:
			dict: A dictionary containing meta information and filter data. """
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
				"meta_description":meta_description}
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

def brands_not_equals_empty(brands):
	brandsfilter = ''
	if brands:
		brandarray = brands.split(',')
		if len(brandarray) > 1:
			for b in brandarray:
				brandsfilter += "'"
				brandsfilter += b
				if not brandarray.index(b) == len(brandarray) - 1:
					brandsfilter += "',"
				else:
					brandsfilter += "'"
		else:
			brandsfilter += "'" + brands + "'"
	condition += 'and name in(select parent from `tabProduct Brand Mapping` \
					 where unique_name in(' + brandsfilter + ')'
def get_attribute_conditions(ratings, brands, min_price, max_price, searchTxt=''):
	condition = ' parent in(select name  from`tabProduct` where is_active=1 and status="Approved"'
	if ratings and ratings != '':
		condition += ' and approved_total_reviews>=' + ratings
	if min_price and min_price != '':
		condition += ' and price>=' + min_price
	if max_price and max_price != '':
		condition += ' and price<=' + max_price
	if searchTxt != '':
		condition += ' and ('
		txt = '"%' + searchTxt + '%"'
		catalog_settings = get_settings_value('Catalog Settings')
		if catalog_settings.search_fields:
			for item in catalog_settings.search_fields:
				condition += '%s like %s or ' % (item.fieldname, txt)
			condition = condition[:-3]
		else:
			condition += 'item like %s' % txt
		condition += ')'
	if brands != '':
		brands_not_equals_empty(brands)
	condition += ') '
	return condition

def get_category_option_query(products_filter, attributes):
	for x in attributes:
		
		products_filter_list = products_filter.strip('[]').split(',')
		x.options = (frappe.qb.from_("tabProduct Attribute Option") 
			.select(
				"PAO.unique_name",
				"PAO.option_value",
				frappe.qb.fn.CountDistinct("P.name").as_("item_count")
			) 
			.inner_join("tabProduct Attribute Mapping as PAM")
			.on("PAO.parent = P.name")
			.and_on("PAO.attribute = PAM.product_attribute") 
			.inner_join("tabProduct as P")
			.on("P.name = PAM.parent") 
			.where(
				(frappe.qb.col("PAO.parent").is_in(products_filter_list)) &
				(frappe.qb.col("PAO.attribute") == attribute_id)
			) 
			.groupby("PAO.unique_name")
			.run(as_dict=True))
		 
		
	return attributes


def get_category_item_attribute_filter(product_ids):
	products_filter = ""
	if product_ids:
		products_filter = ','.join(['"' + x.product + '"' 
						  for x in product_ids])
		
		products_filter_list = products_filter.strip('[]').split(',')
		attributes = (frappe.qb.from_("tabProduct Attribute Mapping as PA") 
			.select(
				"PA.attribute",
				"PA.product_attribute",
				"PA.attribute_unique_name"
			) 
			.inner_join("tabProduct Attribute as AT") 
			.on("AT.name = PA.product_attribute") 
			.where(
				frappe.qb.col("PA.parent").is_in(products_filter_list)
			) 
			.groupby("PA.product_attribute")
			.run(as_dict=True))
		attribute = get_category_option_query(products_filter, attributes)
		return attributes
	return []

def get_category_product_ids(category_filter):
	category_filter_list = category_filter.strip('[]').split(',')
	result = (frappe.qb.from_("tabProduct as P") 
		.inner_join("tabProduct Category Mapping as CM") 
		.on("CM.parent = P.name") 
		.inner_join("tabProduct Category as pc") 
		.on("CM.category = pc.name") 
		.select("P.name as product") 
		.where(
			(frappe.qb.col("P.is_active") == 1) &
			(frappe.qb.col("P.status") == 'Approved') &
			(frappe.qb.col("CM.category").is_in(category_filter_list))
		)
		.run(as_dict=True))
	return result

def get_category_brands_filter(product_ids):
	products_filter = ""
	if product_ids:
		products_filter = ','.join(['"' + x.product + '"' 
						  for x in product_ids])

		query = f""" SELECT 
						BR.name as brand,BR.brand_name,BR.unique_name,
							COUNT(P.name) AS item_count
						FROM `tabProduct` P 
						INNER JOIN 
						`tabProduct Brand` BR ON P.brand = BR.name
						WHERE 
							P.name IN({products_filter}) 
						GROUP BY 
							BR.name,BR.brand_name,BR.unique_name """.format(products_filter=products_filter[:-1])
		return frappe.db.sql(query,as_dict=1)
	return []

Copy code
def get_category_brands_filter(product_ids):
	
	product_names = [x['product'] for x in product_ids]

	if not product_names:
		return []
	result = (frappe.qb.from_("tabProduct as P") 
		.inner_join("tabProduct Brand as BR") 
		.on("P.brand = BR.name") 
		.select(
			"BR.name as brand",
			"BR.brand_name",
			"BR.unique_name",
			frappe.qb.func.count("P.name").as_("item_count")
		) 
		.where(frappe.qb.col("P.name").is_in(product_names)) 
		.groupby("BR.name", "BR.brand_name", "BR.unique_name")
		.run(as_dict=True))
	
	return result