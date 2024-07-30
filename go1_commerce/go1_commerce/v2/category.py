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
		category_product_counts = frappe.db.sql(
					   '''SELECT 
							COUNT(P.name) AS COUNT 
						  FROM `tabProduct` P 
						  INNER JOIN 
							`tabProduct Category Mapping` CM ON P.name=CM.parent 
						  WHERE 
							P.is_active=1 AND P.status='Approved'
							AND CM.category IN(%s) 
						  GROUP BY 
							P.name'''%(category_filter),
					   as_dict=1)
		return category_product_counts
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
				"mega_menu_column",
				"category_name",
				"mobile_image",
				"show_attributes_inlist",
				"products_per_row_for_mobile_app",
				"full_description",
				"default_view",
				"type_of_category",
				"route",
				"products_per_row_in_list",
				"enable_left_side_panel",
			],
			filters={"parent_product_category": "", "is_active": 1},
			order_by="mega_menu_column, display_order",
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
			query = 'select name from `tabProduct Category` where is_active = 1 and disable_in_website = 0 and lft <= {lft} and rgt >= {rgt}'.format(lft=count.lft, rgt=count.rgt)
			return frappe.db.sql('''{query}'''.format(query=query), as_dict=1)
		else:
			return []
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'Error in category.get_parent_categorie')

def get_child_categories(parent_category_name, show_count=0, limit=500):
	""" Retrieves child categories for a given parent recursively."""
	child_categories = frappe.get_all(
		"Product Category",
		fields=[
			"mega_menu_column",
			"category_image",
			"name",
			"category_name",
			"mobile_image",
			"show_attributes_inlist",
			"products_per_row_for_mobile_app",
			"full_description",
			"default_view",
			"type_of_category",
			"route",
			"products_per_row_in_list",
			"enable_left_side_panel",
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
		p_ids = get_category_product_ids(category)
		brand_filters = get_category_brands_filter(p_ids)
		attribute_filters = get_category_item_attribute_filter(p_ids)
		category_list = get_categories_sidemenu(category)
		category_info = frappe.get_doc("Product Category",category)
		meta_info = {"meta_title":category_info.meta_title,
					"meta_keywords":category_info.meta_keywords,
					"meta_description":category_info.meta_description}
		return {'meta_info':meta_info,'attribute_list': attribute_filters, 
				'brand_list': brand_filters, 'category_list': category_list}
	except Exception as e:
		other_exception("Error in v2.category.get_category_filters")
		return {'meta_info':[],'attribute_list': [], 'brand_list': [], 'category_list': []}

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
			'attribute_list': filter_data.get('attribute_filters', []),
			'brand_list': filter_data.get('brand_filters', []),
			'category_list': filter_data.get('category_list', [])
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
	if route and category:
		import os,json	
		category_path = (route.replace("/","-")+"-"+category)
		for file_name in ["attributes.json", "brands.json", "categories.json"]:
			file_path = os.path.join(category_path, file_name)
			if os.path.exists(file_path):
				try:
					with open(file_path, 'r') as f:
						filter_data[file_name.replace(".json", "")] = json.load(f)
				except (IOError, json.JSONDecodeError) as e:
					frappe.log_error(title=_("Error reading JSON file"), 
									message=f"Error reading {file_name}: {str(e)}")
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
		optionquery = """SELECT 
					PAO.unique_name,PAO.option_value,
					COUNT(distinct P.name) AS item_count 
				FROM `tabProduct` P 
				INNER JOIN 
					`tabProduct Attribute Mapping` PAM ON P.name = PAM.parent 
				INNER JOIN 
					`tabProduct Attribute Option` PAO ON PAO.parent=P.name AND PAO.attribute=PAM.product_attribute 
				WHERE 
					PAO.parent IN  ({products_filter}) 
					AND PAO.attribute='{attribute_id}'
				GROUP BY PAO.unique_name
				""".format(products_filter=products_filter,attribute_id=x.product_attribute)
		x.options = frappe.db.sql(optionquery,as_dict=1)
	return optionquery


def get_category_item_attribute_filter(product_ids):
	products_filter = ""
	if product_ids:
		products_filter = ','.join(['"' + x.product + '"' 
						  for x in product_ids])
		attributes = []
		query = """SELECT 
						attribute, product_attribute, 
						PA.attribute_unique_name as attribute_unique_name
					FROM `tabProduct Attribute Mapping`	PA
					INNER JOIN 
						`tabProduct Attribute` AT ON AT.name = PA.product_attribute
					WHERE 
						parent IN ({products_filter}) 
					GROUP BY product_attribute""".format(products_filter=products_filter)
		
		attributes = frappe.db.sql(query,as_dict=1)
		get_category_option_query(products_filter, attributes)
		return attributes
	return []

def get_category_product_ids(category_filter):
	query = """ SELECT 
					P.name AS product 
				FROM `tabProduct` P 
				INNER JOIN 
					`tabProduct Category Mapping` CM ON CM.parent=p.name
				INNER JOIN 
					`tabProduct Category` pc ON CM.category=pc.name 
				WHERE 
					P.is_active=1 AND P.status='Approved'
					AND CM.category IN(%s) """% (category_filter)
	return frappe.db.sql(query,as_dict=1)

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
