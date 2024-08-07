from __future__ import unicode_literals, print_function
import frappe, json, requests
from frappe import _
from frappe.utils import flt, getdate, nowdate, get_url,add_days
from datetime import datetime
from urllib.parse import unquote, urlencode
from pytz import timezone
import pytz
from six import string_types
from go1_commerce.utils.setup import get_settings_value,get_settings
from go1_commerce.go1_commerce.v2.category \
    import get_parent_categories,get_parent_categorie,get_child_categories
from go1_commerce.utils.utils import get_customer_from_token, other_exception

try:
	catalog_settings = get_settings('Catalog Settings')
	no_of_records_per_page = catalog_settings.no_of_records_per_page
except Exception as e:
	catalog_settings = None
	no_of_records_per_page = 10

class Product:
	def get_category_products(self,category, sort_by, page_no,page_size,
								brands, rating,min_price, max_price,attributes,
								productsid,customer,route):
		if route:
			categories = frappe.db.get_value("Product Category",{"route":route},"name")
			if categories:
				category = categories
		default_sort_order = get_settings_value('Catalog Settings','default_product_sort_order')
		sort_order = get_sorted_columns(default_sort_order)
		if sort_by:
			sort_order = sort_by
		category_products = self.get_sorted_category_products(category, sort_order, page_no, 
							page_size,brands, rating, min_price, max_price, attributes,productsid)
		if category_products:
			category_products = get_list_product_details(category_products, customer=customer)
		return category_products
	
	def get_product_list_columns(self):
		return """ P.item, P.price, P.old_price, P.short_description,P.has_variants,
				P.sku, P.name, P.route, P.inventory_method, P.is_gift_card, P.image AS product_image,
				P.minimum_order_qty, P.maximum_order_qty, P.disable_add_to_cart_button, 
				P.weight, P.approved_total_reviews,(CONCAT("/pr/",P.route)) AS b_route,P.brand_name AS brand,
				P.brand_unique_name AS brand_route,P.route,P.brand_name AS product_brand """
	
	def get_sorted_category_products(self,category, sort_by, page_no, page_size, brands,
										ratings, min_price,max_price, attributes,productsid = None):
		catalog_settings = frappe.get_single('Catalog Settings')
		(conditions, sort) = get_conditions_sort(brands, ratings, sort_by, min_price, max_price, attributes)
		category_filter = "'" + category + "'"
		if catalog_settings.include_products_from_subcategories == 1:
			from go1_commerce.go1_commerce.v2.category \
			import get_child_categories
			child_categories = get_child_categories(category)
			if child_categories:
				category_filter = ','.join(['"' + x.name + '"' for x in child_categories])
		if productsid:
			conditions += ' and P.name!="{name}"'.format(name=productsid)
		list_columns = self.get_product_list_columns()
		query = f"""SELECT DISTINCT {list_columns}
					FROM `tabProduct` P
					INNER JOIN `tabProduct Category Mapping` CM ON CM.parent=P.name
					INNER JOIN `tabProduct Category` pc ON CM.category=pc.name
					WHERE P.is_active = 1 
						AND P.status='Approved' 
						AND CM.category IN ({category_filter}) {conditions}
					GROUP BY P.name {sort}
					LIMIT {(int(page_no) - 1)* int(page_size)},{int(page_size)}"""
		result = frappe.db.sql(query, as_dict=True)
		return result
 
@frappe.whitelist(allow_guest=True)
def get_parent_categories():
	try:
		filters = {'parent_product_category': '', 'is_active': 1}
		
		item_group = frappe.db.get_all('Product Category',
				fields=['category_image', 'name', 'category_name', 'mobile_image', 'show_attributes_inlist', 'products_per_row_for_mobile_app','full_description','default_view','type_of_category'], filters=filters,
				order_by='mega_menu_column,display_order', limit_page_length=50)
		if item_group:
			for item in item_group:
				filter1 = {'parent_product_category': item.name, 'is_active': 1}
				if business:
					filter1 = {'parent_product_category': item.name, 'is_active': 1, 'business': business}
				if business:
					child = frappe.db.sql('''SELECT * from `tabProduct Category` where parent_product_category=%(parent_category)s and is_active=1 and business=%(business)s  order by mega_menu_column,display_order''',{'parent_category':item.name,'business':business},as_dict=1)
				else:
					child = frappe.db.sql('''SELECT * from `tabProduct Category` where parent_product_category=%(parent_category)s and is_active=1  order by mega_menu_column,display_order''',{'parent_category':item.name},as_dict=1)

				if child:
					for cat in child:
						filter2 = {'parent_product_category': cat.name, 'is_active': 1}
						if business:
							filter2 = {'parent_product_category': cat.name, 'is_active': 1, 'business': business}
						cat.child = frappe.db.get_all('Product Category', fields=['category_image', 'name', 'category_name', 'mobile_image', 'show_attributes_inlist', 'products_per_row_for_mobile_app','full_description','default_view','type_of_category'],
								filters=filter2, order_by='mega_menu_column,display_order', limit_page_length=50)
				item.child = child
		ItemGroupList = item_group
		return ItemGroupList
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.api.get_parent_categories')



@frappe.whitelist(allow_guest=True)
def get_customer_recently_viewed_products(customer=None, domain=None, isMobile=0,business=None):
	products = []
	if not customer:
		if frappe.request.cookies.get('customer_id'):
			customer = unquote(frappe.request.cookies.get('customer_id'))
	if customer:
		cond = ''
		if domain:
			business = get_business_from_web_domain(domain)
			if business:
				cond = ' and p.restaurant = "{0}"'.format(business)
		if business:
			cond = ' and p.restaurant = "{0}"'.format(business)


		recently_viewed_products = frappe.db.sql('''select c.product from `tabCustomer Viewed Product` c inner join tabProduct p on p.name = c.product where c.parent = %(parent)s {cond} order by viewed_date desc'''.format(cond=cond),{'parent': customer}, as_dict=1)
		books_join_query = ''
		books_columns_query = ''
		conditions = ''
		if recently_viewed_products:
			conditions += ' and p.name in('
		installed_apps = frappe.db.sql(''' select * from `tabModule Def` where app_name='book_shop' ''', as_dict=True)
		for x in recently_viewed_products:
			conditions += "'" + x.product + "',"
		if recently_viewed_products:
			conditions = conditions[:-1]
			conditions += ' )'
		if cond:
			conditions += cond
		if len(installed_apps) > 0:
			books_columns_query = ',AU.author_name,AU.route as author_route,PU.publisher_name,PU.route as publisher_route'
			books_join_query = '  left join `tabAuthor` AU on AU.name=p.author left join `tabPublisher` PU on PU.name=p.publisher'

		query = "select p.item,p.restaurant,p.price,p.old_price,p.short_description,p.tax_category,p.full_description,p.sku,p.name,p.route,p.inventory_method,p.stock,p.minimum_order_qty,p.maximum_order_qty,p.disable_add_to_cart_button,CM.category,\
									(select list_image from `tabProduct Image` where parent=p.name order by is_primary desc limit 1) as product_image,\
									(select brand_name from `tabProduct Brand Mapping` where parent=p.name limit 1) as product_brand,\
									(select B.route from `tabProduct Brand Mapping` MP\
									inner join `tabProduct Brand` B on MP.brand=B.name\
									where MP.parent=p.name and B.published=1 limit 1) as brand_route" \
			+ books_columns_query + ' from `tabProduct` p ' \
			+ books_join_query \
			+ " inner join `tabProduct Category Mapping` CM on CM.parent=p.name\
									where p.is_Active=1 and p.status='Approved'  %s group by p.name limit %d" \
			% (conditions, 12)
		products = frappe.db.sql(query, as_dict=True)


		if products:
			products = get_product_details(products, isMobile=isMobile)
			
	return products


@frappe.whitelist(allow_guest=True)
def get_product_other_info(item, domain=None, isMobile=0, business=None):
	'''
		To get additional product information to show in product detail page

		param: item: product id
	'''
	if domain:
		business = None
		business = get_business_from_web_domain(domain)

	customer_bought = best_sellers = related_products = []
	categories_list = frappe.db.sql('''select category, category_name, (select route from `tabProduct Category` c where c.name = pcm.category) as route from `tabProduct Category Mapping` pcm where parent = %(parent)s order by idx limit 1''', {'parent': item}, as_dict=1)
	if catalog_settings.customers_who_bought:
		customer_bought = get_products_bought_together(item, business=business, isMobile=isMobile)
	if catalog_settings.enable_best_sellers:
		if categories_list and categories_list[0].category:
			best_sellers = get_category_based_best_sellers(categories_list[0].category, item, business=business, isMobile=isMobile)
	if catalog_settings.enable_related_products:
		if categories_list:
			related_products = get_category_products(categories_list[0].category, productsid=item, page_size=18, domain=domain, isMobile=isMobile)
	return {
		'best_seller_category': best_sellers,
		'related_products': related_products,
		'products_purchased_together': customer_bought,
		'product_category': (categories_list[0] if categories_list else {}),
		}

def get_products_bought_together(item, business=None, isMobile=0):
	cond = ''
	if business:
		cond = ' and p.restaurant = "{0}"'.format(business)
	items = frappe.db.sql('''SELECT p.item, p.tax_category, p.price, p.old_price, p.restaurant,
		p.short_description, p.full_description, p.sku, p.name, p.route, p.inventory_method,
		p.minimum_order_qty, p.maximum_order_qty, p.stock, p.disable_add_to_cart_button,p.approved_total_reviews, 
		(select list_image from `tabProduct Image` i where parent=p.name order by is_primary desc limit 1) as product_image, 
		(select detail_thumbnail from `tabProduct Image` i where parent=p.name order by is_primary desc limit 1) as detail_thumbnail,
		(select brand_name from `tabProduct Brand Mapping` where parent=p.name limit 1) as product_brand,(select category from `tabProduct Category Mapping` where parent=p.name limit 1) as category, 
		(select B.route from `tabProduct Brand Mapping` MP inner join `tabProduct Brand` B on MP.brand=B.name 
		where MP.parent=p.name and B.published=1 limit 1) as brand_route from `tabProduct` p 
		inner join `tabOrder Item` oi on p.name = oi.item and oi.order_item_type = "Product" 
		left join `tabOrder` o on o.name = oi.parent where o.docstatus = 1 and o.status <> "Cancelled" 
		and o.name in (select distinct oi1.parent from `tabOrder Item` oi1 where oi1.item = %(item)s and 
		oi1.parenttype = "Order") and p.name <> %(item)s and oi.is_free_item = 0 {cond} group by p.name'''.format(cond=cond),{'item': item}, as_dict=1)
	if items:
		items = get_product_details(items, isMobile=isMobile)
	return items

def get_category_based_best_sellers(category, item, isMobile=0):
	cond = ''
	best_sellers = frappe.db.sql('''SELECT p.item, p.tax_category, p.price, p.old_price, p.restaurant,
		p.short_description, p.full_description, p.sku, p.name, p.route, p.inventory_method,
		p.minimum_order_qty, p.maximum_order_qty, p.stock, p.disable_add_to_cart_button,p.approved_total_reviews,  
		(select list_image from `tabProduct Image` i where parent=p.name order by is_primary desc limit 1) as product_image, 
		(select detail_thumbnail from `tabProduct Image` i where parent=p.name order by is_primary desc limit 1) as detail_thumbnail,
		(select brand_name from `tabProduct Brand Mapping` where parent=p.name limit 1) as product_brand, 
		(select B.route from `tabProduct Brand Mapping` MP inner join `tabProduct Brand` B on MP.brand=B.name 
		where MP.parent=p.name and B.published=1 limit 1) as brand_route, 
		sum(oi.quantity) as qty, pcm.category from ((`tabProduct` p inner join `tabOrder Item` oi on oi.item=p.name) inner join 
		`tabProduct Category Mapping` pcm on pcm.parent=p.name) where pcm.category = "{category}" and p.is_active=1 and p.name <> %(item)s {cond}
		group by p.name order by qty desc limit 18'''.format(category=category, cond=cond), {'item': item}, as_dict=1)
	if best_sellers:
		best_sellers = get_product_details(best_sellers, isMobile=isMobile)
	return best_sellers

@frappe.whitelist(allow_guest=True)
def get_category_products_count(category):
	category_filter="'"+category+"'"
	if catalog_settings.include_products_from_subcategories==1:
		child_categories=get_child_categories(category)
		if len(child_categories)>0:
			category_filter+=","
			for x in child_categories:
				category_filter+="'"+x.name+"'"
				if not child_categories.index(x)==len(child_categories)-1:
					category_filter+=","
	category_product = frappe.db.sql('''select count(*) as count from `tabProduct` p inner join `tabProduct Category Mapping` cm on p.name=cm.parent where p.is_active=1 and p.status='Approved' and cm.category in(%s) group by p.name'''%(category_filter),as_dict=1)
	if category_product:
		return category_product


def delete_attribute_image(deleted_doc):
	try:
		if deleted_doc:
			if deleted_doc.get('thumbnail'):
				delete_thumb_file(deleted_doc.get('thumbnail'))
			if deleted_doc.get('detail_thumbnail'):
				delete_thumb_file(deleted_doc.get('detail_thumbnail'))
			file = frappe.get_doc('File', deleted_doc.get('name'))
			file.delete()
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.api.delete_attribute_image')

def delete_thumb_file(path):
	import os
	if path:
		parts = os.path.split(path.strip('/'))
		if parts[0] == 'files':
			path = frappe.utils.get_site_path('public', 'files', parts[-1])
		else:
			path = frappe.utils.get_site_path('private', 'files', parts[-1])
		path = encode(path)
		if os.path.exists(path):
			os.remove(path)
 
def get_list_product_details(products,customer = None):
	if products:
		today_date = get_today_date(replace=True)
		discount_list =frappe.db.sql(""" SELECT name FROM `tabDiscounts` WHERE 
											(discount_type = 'Assigned to Products' OR 
											discount_type = 'Assigned to Categories' OR 
											discount_type = 'Assigned to Business')
										AND (
											CASE WHEN 
												start_date IS NOT NULL 
											THEN 
												start_date <= "{today}"ELSE 1 = 1 end) AND
										(CASE WHEN 
											end_date IS NOT NULL 
											THEN
												end_date >= "{today}"
											ELSE 1 = 1 END)""".format(today=today_date),as_dict=1)
		currency = catalog_settings.default_currency
		currency_symbol = frappe.db.get_value("Currency",catalog_settings.default_currency,"symbol")
		for x in products:
			x["actual_price"] = x.get("price")
			x["actual_old_price"] = x.get("old_price")
			x["item_title"] = x.get("item")
			price_details = None
			if discount_list:
				price_details = get_product_price(x, customer=customer)
			product_price = x.get("price")
			if price_details:
				x["discount_rule"] = price_details.get('discount_rule')
				x["discount_label"] = price_details.get('discount_label')
				discount_info = frappe.db.get_all("Discounts",
									filters={"name":price_details.get('discount_rule')},
									fields=['percent_or_amount','discount_percentage','discount_amount',
											'discount_type'])
				discount_requirements = frappe.db.get_all("Discount Requirements",
										filters={"parent":price_details.get('discount_rule')},
										fields=['items_list','discount_requirement'])
				customer_list = []
				if discount_requirements:
					for dr in discount_requirements:
						if dr.discount_requirement== "Limit to customer":
							items = json.loads(dr.items_list)
							customer_list = [i.get('item') for i in items]
				is_allowed = 1			
				if customer_list:
					if customer not in customer_list:
						is_allowed = 0
				if discount_info and is_allowed==1:
					if discount_info[0].percent_or_amount == "Discount Percentage":
						value = discount_info[0].discount_percentage
						x["product_price"] = flt(x.get("price")) - flt(x.get("price"))*flt(value)/100
						x["old_price"] = x.get("price")
						x["discount_percentage"] = discount_info[0].discount_percentage
					else:
						x["product_price"] = flt(x.get("price")) - flt(discount_info[0].discount_amount)
						x["old_price"] = x.get("price")
						x["discount_percentage"] = round((flt(discount_info[0].discount_amount)/value)*100,2)
			if x["price"] != product_price:
				x["old_price"] = x.get("price")
				x["price"] = product_price
			if float(x.get("old_price")) > 0 and float(x.get("price")) < float(x.get("old_price")):
				x["discount_percentage"]= int(round((flt(str(x.get("old_price"))) - flt(str(x.get("price")))) / 
										flt(str(x.get("old_price"))) * 100, 0))
			x["formatted_price"] = frappe.utils.fmt_money(x["price"],currency=currency_symbol)
			x["formatted_old_price"] = frappe.utils.fmt_money(x["old_price"],currency=currency_symbol)
	return products

def get_customer_recently_viewed_products(customer=None):
	products = []
	if not customer:
		if frappe.request.cookies.get('customer_id'):
			customer = unquote(frappe.request.cookies.get('customer_id'))
	if customer:
		cond = ''
		recently_viewed_products = frappe.db.sql('''select C.product 
													from `tabCustomer Viewed Product` C 
													inner join `tabProduct` P on P.name = c.product 
													where C.parent = %(parent)s {cond} 
													order by viewed_date desc'''.format(cond=cond),
													{'parent': customer}, as_dict=1)
		conditions = ''
		if recently_viewed_products:
			conditions += ' and P.name in('
		for x in recently_viewed_products:
			conditions += "'" + x.product + "',"
		if recently_viewed_products:
			conditions = conditions[:-1]
			conditions += ' )'
		if cond:
			conditions += cond
	return recently_viewed_query(conditions,products,customer=customer)

def recently_viewed_query(conditions,products,customer=None):
	count = 12
	list_columns = get_product_list_columns()
	query = f""" SELECT 
					{list_columns}
				FROM 
					`tabProduct` P
				INNER JOIN 
					`tabProduct Category Mapping` CM ON CM.parent = P.name
				WHERE 
					P.is_active=1 
					AND 
						P.status='Approved' {conditions} 
				GROUP BY 
					P.name 
				LIMIT {count} """
	products = frappe.db.sql(query, as_dict=True)
	if products:
		products = get_list_product_details(products,customer=customer)
	return products

@frappe.whitelist(allow_guest=True)
def get_product_details(route):
	try:
		customer_id = get_customer_from_token()
		query = "SELECT * from `tabProduct` P WHERE  P.route = '{route}'" .format(route=route)
		product = frappe.db.sql(query, as_dict=1)
		if not product:
			return {"status":"Failed","message":"Product not found."}
		if product:
			product = get_products_info(product)
			if product[0].product_attribute:
				for attribute in product[0].product_attributes:
					if attribute.size_chart:
						attribute.size_charts = frappe.db.get_all('Size Chart',
												filters={'name':attribute.size_chart},
												fields=['size_chart_image'])
						size_chart = frappe.db.sql( ''' SELECT TRIM(attribute_values) AS attribute_values,
															chart_title,chart_value,name 
														FROM `tabSize Chart Content` 
														WHERE parent = %(parent)s 
														ORDER BY display_order''',
														{'parent': attribute.size_chart}, as_dict=True)
						unique_sizes = list(set([x.chart_title for x in size_chart]))
						unique_attr = []
						for uni in size_chart:
							if uni.attribute_values not in unique_attr:
								unique_attr.append(uni.attribute_values)
						size_chart_list = []
						for attr in unique_attr:
							sizes_list = list(filter(lambda x: x.attribute_values == attr, size_chart))
							arr = {}
							if sizes_list:
								arr['attribute'] = attr
								for sz in unique_sizes:
									check = next((x for x in sizes_list if x.chart_title == sz), None)
									if check:
										arr[sz] = check.chart_value
									else:
										arr[sz] = ''
								size_chart_list.append(arr)
						attribute.size_chart = size_chart_list
						attribute.size_chart_params = unique_sizes
			product_brand_image_list(product)
			product = product_details(product,customer_id)
			return product[0]
	except Exception as e:
		other_exception("Error in v2.product.get_product_details")

def product_brand_image_list(product):
	product[0].brands = frappe.db.sql('''SELECT B.name, B.brand_name, B.brand_logo, B.route, 
												B.warranty_information, B.description 
										FROM 
											`tabProduct Brand` B 
										INNER JOIN 
											`tabProduct Brand Mapping` PBM ON B.name = PBM.brand 
										WHERE 
											PBM.parent = %(parent)s 
										GROUP BY B.name 
										ORDER BY B.name''', {'parent': product[0].name}, as_dict=True)
	product[0].images = frappe.db.sql('''SELECT detail_thumbnail, title, is_primary, 
											image_name, product_image, detail_image 
										FROM 
											`tabProduct Image` 
										WHERE 
											parent = %(parent)s 
										ORDER BY 
											is_primary DESC, idx''', 
											{'parent': product[0].name}, as_dict=True)

@frappe.whitelist()
def fun():
	birthday_club_settings = frappe.get_single('BirthDay Club Setting')
	return birthday_club_settings

def product_details(product,customer_id):
	from go1_commerce.go1_commerce.doctype.product.product \
	 import get_product_reviews_list
	product[0].reviews = get_product_reviews_list(product[0].name, 0, 5)
	product_reviews = frappe.db.sql('''SELECT IFNULL(COUNT(*), 0) AS review_count,
											IFNULL(AVG(rating), 0) AS rating 
									FROM 
										`tabProduct Review` 
									WHERE 
										product = %(product)s''', {'product': product[0].name}, as_dict=True)
	advance_amount = 0
	if product[0].enable_preorder_product == 1:
		if product[0].percentage_or_amount=="Preorder Percentage":
			advance_amount += flt(product[0].price) * flt(product[0].preorder_percent) / 100
		else:
			advance_amount += flt(product[0].preorder_amount)
	product[0].advance_amount = advance_amount
	if product_reviews:
		product[0].rating = product_reviews[0].rating
		product[0].review_count = product_reviews[0].review_count
	if customer_id:
		product[0].recently_viewed = get_customer_recently_viewed_products(customer_id)
	category = frappe.db.sql('''SELECT C.category, C.name, C.category_name, PC.type_of_category 
								FROM 
									`tabProduct Category Mapping` C 
								INNER JOIN 
									`tabProduct Category` PC ON C.category = PC.name 
								LEFT JOIN 
									`tabProduct` P ON P.name = C.parent 
								WHERE P.name = %(product)s 
								ORDER BY C.idx LIMIT 1 ''', {'product': product[0].name}, as_dict=True)
	product[0].product_categories = category
	related_products = frappe.db.sql(f""" SELECT RP.name,RP.product_name,RP.product,P.Item,P.price,
												P.item,P.short_description,P.image,P.route, P.old_price
											FROM 
												`tabRelated Product` RP 
											INNER JOIN 
												`tabProduct` P ON P.name = RP.product 
											WHERE RP.parent = '{product[0].name}' """, as_dict = 1)
	return product


@frappe.whitelist(allow_guest=True)
def check_user_location_delivery(zipcode,state=None, country=None):
	'''To check customer location for delivery
		param: zipcode: zipcode / postal code of the customer's address or user input zipcode
		param: state: state of customer address
		param: country: country of customer address'''
	default_shipping_method = frappe.db.get_all('Shipping Rate Method', 
                                            	fields=["name", "shipping_rate_method"], 
                                            	filters={'is_active': 1})
	doctype = None
	if len(default_shipping_method)>0:
		frappe.log_error("1",1)
		if default_shipping_method[0].shipping_rate_method == 'Shipping By Total':
			doctype = 'Shipping By Total Charges'
		elif default_shipping_method[0].shipping_rate_method == 'Fixed Rate Shipping':
			doctype = 'Shipping By Fixed Rate Charges'
		elif default_shipping_method[0].shipping_rate_method == 'Shipping By Weight':
			doctype = 'Shipping By Weight Charges'
	if doctype:
		shipping_zones = frappe.db.sql(	f"""SELECT Z.name, Z.to_city, Z.state, Z.country, 
											(SELECT P.no_of_days 
												FROM 
													`tabDelivery Process Time` P 
												WHERE P.name = Z.name) AS delivery_days 
											FROM 
												`tabShipping Zones` Z 
											INNER JOIN 
												`tab{doctype}` S ON S.shipping_zone = Z.name 
											ORDER BY Z.name""",as_dict=True)
		response = False
		delivery_days = 0
		delivery_date = None
		if shipping_zones:
			for zone in shipping_zones:
				if not response:
					if zone.to_city:
						response = check_city_ziprange(zone.to_city, zipcode)
					else:
						if zone.state and state and zone.state == state:
							response = True
						elif zone.country and country and zone.country == country:
							response = True
					if response:
						delivery_days = zone.delivery_days
						from_date = getdate(nowdate())
						if not delivery_days:
							delivery_days=0
						to_date = add_days(from_date, int(delivery_days))
						delivery_date = '{0}'.format(to_date.strftime('%a, %b %d'))
		return {'allow': response, 
          		'delivery_days': delivery_days, 
				'delivery_date': delivery_date}

def check_city_ziprange(city, zipcode):
	shipping_city = frappe.get_doc('Shipping City', city)
	return shipping_zip_matches(zipcode, shipping_city.zipcode_range)
	 
@frappe.whitelist(allow_guest=True)
def shipping_zip_matches(zip, ziprange):
	zipcoderanges = []
	returnValue = False
	if ziprange.find(',') > -1:
		zipcoderanges = ziprange.split(',')
		for x in zipcoderanges:
			if x.find('-') > -1:
				zipcoderanges_after = x.split('-')
				for zipcode in range(int(zipcoderanges_after[0]), int(zipcoderanges_after[1]) + 1):
					if str(zipcode).lower() == str(zip).lower():
						returnValue = True
			else:
				if str(x).lower().replace(" ","") == str(zip).lower().replace(" ",""):
					returnValue = True
	elif ziprange.find('-') > -1:
		zipcoderanges_after = ziprange.split('-')
		for zipcode in range(int(zipcoderanges_after[0]), int(zipcoderanges_after[1]) + 1):
			if str(zipcode).lower() == str(zip).lower():
				returnValue = True
	else:
		if str(ziprange).lower() == str(zip).lower():
			returnValue = True
	return returnValue


def not_valid_customer():
	frappe.local.response.http_status_code = 403
	frappe.local.response.status = "Failed"
	frappe.local.response.message = "You are not permitted"


def get_discount_list(today_date):
    discount_list = frappe.db.sql(f"""  SELECT name 
										FROM 
											`tabDiscounts` 
										WHERE 
											(discount_type = 'Assigned to Products' OR 
											discount_type = 'Assigned to Categories' OR 
											discount_type = 'Assigned to Business')
										AND (CASE WHEN 
												start_date IS NOT NULL 
											THEN start_date <= "{today_date}"ELSE 1 = 1 end) AND
										(CASE WHEN 
											end_date IS NOT NULL 
											THEN end_date >= "{today_date}"
										ELSE 1 = 1 END)""",as_dict=1)
    return discount_list

def get_products_info(product, current_category=None):
	customer = get_customer_from_token()
	media_settings = frappe.get_single('Media Settings')
	catalog_settings = frappe.get_single('Catalog Settings')
	if product:
		today_date = get_today_date(replace=True)
		discount_list = get_discount_list(today_date)
		for x in product:
			price_details = product_price_details(x, discount_list, media_settings,customer)
			mapped_category_result = product_mapped_category(x)
			show_attributes = 0
			product_attributes = product_attributes_data(x, customer, show_attributes)
			product_variant = get_product_variant(x)
			specification_attribute = product_specification_attribute(x)
			tax_category = product_tax_category(show_attributes,x, catalog_settings, 
												current_category=current_category)
			review_and_video = product_review_and_video(x)
	return product


def product_mapped_category(x):
	mapped_category = frappe.db.get_all('Product Category Mapping', 
											filters={'parent': x.name},
											fields=['category'],order_by="idx desc")
	x.category_mapping = mapped_category
	show_attributes = 0
	if mapped_category:
		product_category = frappe.db.get_all('Product Category',
												fields=["name","route","category_name"], 
												filters={"name":mapped_category[0].category},
												order_by="display_order",limit_page_length=1)
		if product_category:
			x.item_categories = product_category[0]
	if mapped_category and len(mapped_category) > 0:
		for category in mapped_category:
			child_categories = get_child_categories(category.category)
			if child_categories and len(child_categories) > 0:
				for cat in child_categories:
					item_category = frappe.get_doc('Product Category', cat.name)
					if item_category and item_category.show_attributes_inlist == 1:
						if show_attributes == 0:
							show_attributes += item_category.show_attributes_inlist
	return show_attributes


def product_price_details(x, discount_list, media_settings, customer):
	x.actual_price = x.price
	x.actual_old_price = x.old_price
	x.item_title = x.item
	x.role_based_price = 0
	price_details = None
	if discount_list:
		price_details = get_product_price(x, customer=customer)
	product_price = x.price
	if price_details:
		if price_details.get('discount_amount'):
			product_price = price_details.get('rate')
		x.discount_rule = price_details.get('discount_rule')
		x.discount_label = price_details.get('discount_label')
		discount_info = frappe.db.get_all("Discounts",
							filters={"name":price_details.get('discount_rule')},
							fields=['percent_or_amount','discount_percentage','discount_amount','discount_type'])
		# discount_requirements = product_discount_requirements(x,price_details,customer,discount_info)
	if x.price != product_price:
		x.old_price = x.price
		x.price = product_price
	if float(x.old_price) > 0 and float(x.price) < float(x.old_price):
		x.discount_percentage = int(round((x.old_price - x.price) / x.old_price * 100, 0))
	if not x.product_image:
		if media_settings.list_thumbnail:
			x.product_image = media_settings.list_thumbnail

def product_discount_requirements(x,price_details,customer,discount_info):
	discount_requirements = frappe.db.get_all("Discount Requirements",
								filters={"parent":price_details.get('discount_rule')},
								fields=['items_list','discount_requirement'])
	customer_list = []
	if discount_requirements:
		for dr in discount_requirements:
			if dr.discount_requirement== "Limit to customer":
				items = json.loads(dr.items_list)
				customer_list = [i.get('item') for i in items]
	for vp in x["vendor_price_list"]:
		is_allowed = 1
		if customer_list:
			if not customer:
				is_allowed = 0
			if customer not in customer_list:
				is_allowed = 0
		if is_allowed==1:
			if vp.get("variants"):
				for v in vp.get("variants"):
					v_price = v.product_price
					if discount_info[0].percent_or_amount == "Discount Percentage":
						v["product_price"] = flt(v_price) - flt(v_price)*flt(discount_info[0].discount_percentage)/100
						v["old_price"] = v_price
						v["discount_percentage"] = discount_info[0].discount_percentage
					else:
						v["product_price"] = flt(v_price) - flt(discount_info[0].discount_amount)
						v["old_price"] = v_price
						v["discount_percentage"] = round((flt(discount_info[0].discount_amount)/v_price)*100,2)
			vp_price = vp.product_price
			if discount_info[0].percent_or_amount == "Discount Percentage":
				vp["product_price"] = flt(vp_price) - flt(vp_price)*flt(discount_info[0].discount_percentage)/100
				vp["old_price"] = vp_price
				vp["discount_percentage"] = discount_info[0].discount_percentage
			else:
				vp["product_price"] = flt(vp_price) - flt(discount_info[0].discount_amount)
				vp["old_price"] = vp_price
				vp["discount_percentage"] = round((flt(discount_info[0].discount_amount)/vp_price)*100,2)


def product_attributes_data(x,customer,show_attributes):
	product_attributes = frappe.db.get_all('Product Attribute Mapping',
								 fields=['*'],
								 filters={'parent': x.name},
								 order_by='idx',
								 limit_page_length=50)
	check_stock = False
	if len(product_attributes) > 0 and x.has_variants:
		if x.inventory_method == 'Track Inventory By Product Attributes' and len(product_attributes) == 1:
			check_stock = True
			combination = frappe.db.get_all('Product Variant Combination', 
							filters={'parent': x.name}, limit_page_length=500)
		attribute_ids = ''
		attribute = ''
		attribute_price=0
		attribute_old_price = 0
		for attribute in product_attributes:
			attribute.options = frappe.db.get_all('Product Attribute Option',
								fields=['option_value', 'price_adjustment',
										'display_order', 'name','image_list',
										'is_pre_selected','attribute_color',
										'product_title'], 
								filters={'parent': x.name, 
											'attribute': attribute.product_attribute, 
											'attribute_id': attribute.name},
								order_by='display_order', limit_page_length=500)
			if attribute.options:
				count = 1
				for op in attribute.options:
					attribute.options = attribute_options(attribute,x,op,count,attribute_ids,customer,
															has_attr_stock=x.has_attr_stock)
		if show_attributes==1:
			from go1_commerce.go1_commerce.v2.cart \
			import validate_attributes_stock
			x.variant_price = validate_attributes_stock(x.name,attribute_ids,
								attribute,x.minimum_order_qty,add_qty=None)
			x.attribute_price = attribute_price
			x.attribute_old_price = attribute_old_price
		x.have_attribute = 1
		x.product_attributes = product_attributes
	else:
		x.have_attribute = 0
		x.product_attributes = product_attributes


def attribute_options(attribute,x,op,count,attribute_ids,customer,has_attr_stock):
	if x.inventory_method == 'Track Inventory' or x.inventory_method == 'Dont Track Inventory':
		op.attr_itemprice = float(op.price_adjustment) + float(x.actual_price)
		x.price = op.attr_itemprice
		if op.is_pre_selected==1:
			attribute_ids+=op.name+'\n'
			attribute_price=float(op.attr_itemprice)
			if type(x.old_price) != str:
				attribute_old_price = float(op.price_adjustment) + float(x.old_price)
		else:
			if count == 1:
				attribute_ids+=op.name+'\n'
				attribute_price=float(op.attr_itemprice)
				if type(x.old_price) != str:
					attribute_old_price = float(op.price_adjustment) + float(x.old_price)
		price_detail = get_product_price(x, customer=customer)
		if price_detail and price_detail.get('discount_amount'):
			product_price1 = price_detail.get('rate')
			if x.price != product_price1:
				x.old_price = x.actual_price
				x.price = product_price1
				op.attr_itemprice = product_price1
				if op.is_pre_selected==1:
					attribute_price=float(product_price1)
					attribute_old_price = float(op.price_adjustment) + float(x.old_price)
				else:
					if count == 1:
						attribute_price=float(product_price1)
						attribute_old_price = float(op.price_adjustment) + float(x.old_price)
		count+=1
		if  type(x.old_price) != str and float(x.old_price) > 0:
			op.attr_oldprice = float(op.price_adjustment) + float(x.old_price)
	if x.inventory_method == 'Track Inventory By Product Attributes':
		attribute_ids=op.name+'\n'
		from go1_commerce.go1_commerce.v2.cart import validate_attributes_stock
		variant_comb = validate_attributes_stock(x.name,attribute_ids,attribute,x.minimum_order_qty,
                                           			add_qty=None).get('status') == 'True'
		op.attr_itemprice = float(variant_comb['price'])
		op.attr_oldprice = float(variant_comb['old_price'])
		if variant_comb.get('discount'):
			if 'rate' in variant_comb['discount']:
				op.attr_itemprice = float(variant_comb['discount']['rate'])
				op.attr_oldprice = float(variant_comb['price'])
		op.status = variant_comb['status']
		if variant_comb['status'] == "Success":
			if op.stock and int(op.stock) > 0:
				op.has_attr_stock = True
			else:
				op.has_attr_stock = False
		else:
			op.has_attr_stock = False
		if op.is_pre_selected == 1:
			if op.has_attr_stock  == False:
				has_attr_stock = False
	op.videos = frappe.get_all('Product Attribute Option Video',
								filters={"option_id":op.name},
								fields=["youtube_video_id","video_type"])
	if op.image_list:
		op.images = json.loads(op.image_list)
	else:
		op.images = []
	return has_attr_stock


def get_product_variant(x):
	product_variant = frappe.db.sql(f'''SELECT name, price, role_based_pricing, stock, weight 
										FROM 
											`tabProduct Variant Combination` 
										WHERE 
											parent = '{x.name}'
										AND disabled=0 
										AND show_in_market_place=1''', as_dict=1)
	for v_comb in product_variant:
		v_comb.video_list = frappe.db.sql(
							""" SELECT name 
								FROM 
									`tabProduct Attribute Option Video` 
								WHERE 
									option_id = %(option_id)s""", 
								{"option_id": v_comb.name},as_dict = 1)
	x.product_variant = product_variant


def product_specification_attribute(x):
	specification_group = []
	specification_attribute = frappe.db.sql_list('''SELECT DISTINCT 
														SAM.spec_group_name,SG.display_order 
													FROM 
														`tabSpecification Group` SG 
													INNER JOIN 
														`tabProduct Specification Attribute Mapping` SAM
													ON SG.name=SAM.spec_group_name1 
													WHERE 
														SAM.parent=%(name)s 
													ORDER BY 
														SG.display_order''',{'name':x.name})
	if specification_attribute:
		for item in specification_attribute:
			groups = frappe.db.get_all('Product Specification Attribute Mapping',
						fields=['specification_attribute','options'], 
						filters={"parent":x.name,'spec_group_name':item},
						order_by='idx')
			specification_group.append({"name":item, "groups":groups})
	else:
		groups = frappe.db.get_all('Product Specification Attribute Mapping',
					fields=['specification_attribute','options'], 
					filters={"parent":x.name},order_by='idx')
		if groups:
			specification_group.append({"name":"", "groups":groups})
	x.product_specification = specification_group
	if not x.product_brand:
		x.product_brand = ''
	else:
		if len(x.product_brand) > 30:
			x.product_brand = x.product_brand[:15] + '...'
	highlights = frappe.db.get_all('Highlights', 
					fields=['highlights'], 
					filters={'parent': x.name})
	x.highlights = highlights
	if x.return_description:
		x.return_policy = x.return_description


def product_tax_category(show_attributes,x,catalog_settings,current_category):
	if x.tax_category:
		tax_template = frappe.get_doc('Product Tax Template', x.tax_category)
		x.tax_template = tax_template
		item_tax= 0
		tax_value = 0
		tax_type = None
		tax_splitup = []
		included_tax = catalog_settings.included_tax
		if included_tax:
			tax_type = 'Incl. Tax'
		else:
			tax_type = 'Excl. Tax'
		if tax_template:
			if tax_template.tax_rates:
				for tax in tax_template.tax_rates:
					if included_tax:
						tax_value = flt(x.price) * tax.rate / (100 + tax.rate)
					else:
						tax_value = flt(x.price) * tax.rate / 100
					item_tax = item_tax + tax_value
					tax_splitup.append({'type': tax.tax,
										'rate': tax.rate, 
										'amount': tax_value,
										'tax_type': tax_type })
		x.tax_splitup = tax_splitup
		x.total_tax_amount = item_tax
		x.tax_type = tax_type
	if current_category:
		x.products_per_row = frappe.db.get_value('Product Category', current_category, 'products_per_row_in_list')
	if x.category:
		category1 = frappe.get_doc('Product Category', x.category)
		if category1:
			x.category1 = category1.type_of_category
			x.show_attributes_inlist = show_attributes

def product_review_and_video(x):
	product_reviews = frappe.db.sql('''SELECT 
											IFNULL(COUNT(*), 0) AS review_count,
											IFNULL(AVG(rating), 0) AS rating 
										FROM 
											`tabProduct Review` 
										WHERE 
											product=%(product)s''', 
									{'product': x.name}, 
									as_dict=1)
	x.rating = product_reviews[0].rating if product_reviews else 0
	x.review_count = product_reviews[0].review_count if product_reviews else 0
	x.product_video = frappe.db.get_all('Product Video', 
										fields=['display_order', 'video_type', 'video_link', 'name'], 
										filters={'parent': x.name}, order_by='display_order')
	product_tag = frappe.db.get_value('Product', x.name, 'product_tag')
	if product_tag:
		tags = json.loads(product_tag)
		x.product_tags = frappe.db.get_all(
			'Product Tag', 
			filters={'name': ('in', tags)}, 
			fields=['title', 'icon'])
	else:
		x.product_tags = []
	

@frappe.whitelist(allow_guest=True)
def get_conditions_sort(brands, ratings, sort_by, min_price, max_price,attributes):
	try:
		condition = ''
		if brands:
			brandarray = brands.split(',')
			if len(brandarray) > 1:
				condition += f"""AND P.name IN 
									(SELECT M.parent FROM 
										`tabProduct Model Mapping` M 
									INNER JOIN 
										`tabProduct Brand` B ON B.name=M.brand 
									WHERE B.unique_name IN("""
				for b in brandarray:
					condition += "'"
					condition += b
					if not brandarray.index(b) == len(brandarray) - 1:
						condition += "',"
					else:
						condition += "'"
				condition += '))'
			else:
				condition += """ AND P.name IN(SELECT M.parent 
								FROM 
									`tabProduct Model Mapping` M 
								INNER JOIN 
									`tabProduct Brand` B 
									ON 
										B.name=M.brand 
								WHERE
									B.unique_name='"{ brandarray[0] }"' )"""
		return get_sub_conditions_sort(ratings,sort_by,min_price,max_price,attributes,condition)
	except Exception:
		other_exception("Error in v2.product.get_conditions_sort")


def get_sub_conditions_sort(ratings,sort_by,min_price,max_price, attributes,condition):
	sort = ""
	if ratings:
		if int(ratings) > 0:
			condition += ' AND P.approved_total_reviews>=' + str(ratings)
	if min_price:
		condition += ' AND PP.price>=' + min_price
	if max_price:
		condition += ' AND PP.price<=' + max_price
	attr_condition = sub_conditions_sort_attributes(attributes)
	condition += attr_condition
	if sort_by:
		if sort_by.lower() == 'modified DESC':
			sort = 'ORDER BY P.display_order,stock DESC'
		if sort_by.lower() == 'relevance':
			sort = ' ORDER BY stock DESC,P.modified DESC'
		if sort_by.lower() == 'name ASC' or sort_by.lower() == 'name_asc':
			sort = ' ORDER BY TRIM(P.item) ASC'
		if sort_by.lower() == 'name DESC' or sort_by.lower() == 'name_desc':
			sort = ' ORDER BY TRIM(P.item) DESC'
		if sort_by.lower() == 'price ASC' or sort_by.lower() == 'price_asc':
			sort = ' ORDER BY price ASC'
		if sort_by.lower() == 'price DESC' or sort_by.lower() == 'price_desc':
			sort = ' ORDER BY price  DESC'
	return (condition, sort)


def sub_conditions_sort_attributes(attributes):
	attr_condition = ""
	if attributes:
		if type(attributes) is dict:
			attr_condition += ' AND P.name IN(SELECT parent \
								FROM `tabProduct Attribute Option` \
								WHERE unique_name IN('
			counter = 0
			if not counter == 0:
				attr_condition += ','
			option_values = attributes['value'].split(',')
			for option in option_values:
				attr_condition += "'"
				attr_condition += option
				if not option_values.index(option) == len(option_values) - 1:
					attr_condition += "',"
				else:
					attr_condition += "'"
			counter = counter + 1
			attr_condition += '))'
		else:
			if isinstance(attributes, string_types):
				attributes = json.loads(attributes)
			if len(attributes) > 0:
				attr_condition += ' AND P.name IN(SELECT parent \
									FROM `tabProduct Attribute Option` \
									WHERE unique_name IN('
				counter = 0
				for x in attributes:
					if not counter == 0:
						attr_condition += ','
					option_values = x['value'].split(',')
					for option in option_values:
						attr_condition += "'"
						attr_condition += option
						if not option_values.index(option) == len(option_values) - 1:
							attr_condition += "',"
						else:
							attr_condition += "'"
					counter = counter + 1
				attr_condition += '))'
	return attr_condition


def get_product_price(product, qty=1, rate=None,attribute_id=None, customer=None):
	try:
		if isinstance(attribute_id, list):
			if len(attribute_id)==1:
				attribute_id = attribute_id[0]
		cust = customer
		if frappe.request:
			cust = frappe.request.cookies.get('customer_id')
		cart_items=None
		if cust:
			cart = frappe.db.exists("Shopping Cart", {"customer": cust})
			if cart:
				doc = frappe.get_doc("Shopping Cart", cart)
				cart_items = ','.join('"{0}"'.format(r.product) for r in doc.items)
		from go1_commerce.go1_commerce.doctype.discounts.discounts import get_product_discount
		res = get_product_discount(product, qty, rate, customer_id=customer, attribute_id=attribute_id,
			  product_array=cart_items)
		return res
	except Exception:
		other_exception("Error in v2.product.get_product_price")

@frappe.whitelist(allow_guest=True)
def get_bestsellers(limit=None, isMobile=0):
	try:
		if not limit:
			limit = catalog_settings.no_of_best_sellers
		if catalog_settings.display_best_seller_products:
			books_join_query = ''
			books_columns_query = ''
			installed_apps = frappe.db.sql(''' select * from `tabModule Def` where app_name='book_shop' ''', as_dict=True)
			if len(installed_apps) > 0:
				books_columns_query = ',AU.author_name,AU.route as author_route,PU.publisher_name,PU.route as publisher_route'
				books_join_query = '  left join `tabAuthor` AU on AU.name=p.author left join `tabPublisher` PU on PU.name=p.publisher'
			query = "select p.item,p.tax_category,p.price,p.old_price,p.short_description,p.full_description,p.sku,p.name,p.route,p.inventory_method,p.minimum_order_qty,p.maximum_order_qty,p.stock,p.disable_add_to_cart_button,\
				(select list_image from `tabProduct Image` i where parent=p.name order by is_primary desc\
				limit 1) as product_image, (select detail_thumbnail from `tabProduct Image` i where parent=p.name order by is_primary desc\
				limit 1) as detail_thumbnail,(select brand_name from `tabProduct Brand Mapping` where parent=p.name\
				limit 1) as product_brand,\
				(select B.route from `tabProduct Brand Mapping` MP\
									inner join `tabProduct Brand` B on MP.brand=B.name\
									where MP.parent=p.name and B.published=1 limit 1) as brand_route,\
				sum(oi.quantity) as qty " + books_columns_query + " from `tabProduct` p inner join `tabOrder Item` oi\
				on oi.item=p.name " + books_join_query + ' where p.is_active=1 group by p.name order by qty desc limit ' + str(limit)
			Items = frappe.db.sql(query, as_dict=True)

			if Items:
				Items = get_product_details_(Items, isMobile)
			return Items
		else:
			return []
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.api.get_bestsellers')

def get_product_details_(product, isMobile=0, customer=None, current_category=None):
	media_settings = get_settings('Media Settings','Media Settings')
	catalog_settings = get_settings('Catalog Settings','Catalog Settings')
	if product:
		for x in product:
			x.actual_price = x.price
			x.actual_old_price = x.old_price
			x.item_title = x.item
			x.role_based_price = 0
			price_details = get_product_price(x, customer=customer)
			product_price = x.price
			if price_details:
				if price_details.get('discount_amount'):
					product_price = price_details.get('rate')
				x.discount_rule = price_details.get('discount_rule')
				x.discount_label = price_details.get('discount_label')
			
			if x.price != product_price:
				x.old_price = x.price
				x.price = product_price
			if float(x.old_price) > 0 and float(x.price) < float(x.old_price):
				x.discount_percentage = int(round((x.old_price - x.price) / x.old_price * 100, 0))
			if isMobile == 0:
				if float(x.price) > 100000:
					short_amt = float(x.price) / 100000
					x.price = str('%.2f' % short_amt) + 'L'
				else:
					x.price = str('%.2f' % x.price)
				if x.old_price > 0:
					if x.old_price > 100000:
						short_amt = float(x.old_price) / 100000
						x.old_price = str('%.2f' % short_amt) + 'L'
					else:
						x.old_price = str('%.2f' % x.old_price)
				else:
					x.old_price = str('%.2f' % x.old_price)
			if not x.product_image:
				if media_settings.list_thumbnail:
					x.product_image = 1
			show_attributes = 0
			mapped_category = frappe.db.get_all('Product Category Mapping', filters={'parent':x.name}, fields=['category'])
			if mapped_category and len(mapped_category) > 0:
				for category in mapped_category:
					child_categories = get_parent_categorie(category.category)
					if child_categories and len(child_categories) > 0:
						for cat in child_categories:
							item_category = frappe.get_doc('Product Category', cat.name)
							if item_category and item_category.show_attributes_inlist==1:
								if show_attributes==0:
									show_attributes += item_category.show_attributes_inlist
			product_attributes = frappe.db.get_all('Product Attribute Mapping', fields=['*'],
								  filters={'parent': x.name},  order_by='idx', limit_page_length=50)
			check_stock = False
			has_attr_stock = True
			if len(product_attributes) > 0:
				if x.inventory_method == 'Track Inventory By Product Attributes' and len(product_attributes) == 1:
					check_stock = True
					combination = frappe.db.get_all('Product Variant Combination', filters={'parent': x.name}, limit_page_length=500)
				attribute_ids = ''
				attribute_ids1 = ''
				attribute = ''
				attribute_price=0
				attribute_old_price = 0
				for attribute in product_attributes:
					attribute.options = frappe.db.get_all('Product Attribute Option',
							fields=['option_value', 'price_adjustment', 'display_order', 'name','image_list','is_pre_selected','attribute_color','product_title'], 
							filters={'parent': x.name, 'attribute': attribute.product_attribute, 'attribute_id': attribute.name},
							order_by='display_order', limit_page_length=50)
					if attribute.options:
						count = 1
						for op in attribute.options:
							if show_attributes==1:
								if x.inventory_method == 'Track Inventory' or x.inventory_method == 'Dont Track Inventory':
									op.attr_itemprice = float(op.price_adjustment) + float(x.actual_price)
									x.price = op.attr_itemprice
									if op.is_pre_selected==1:
										attribute_ids+=op.name+'\n'
										attribute_price=float(op.attr_itemprice)
										attribute_old_price = float(op.price_adjustment) + float(x.old_price)
									else:
										if count == 1:
											attribute_ids+=op.name+'\n'
											attribute_price=float(op.attr_itemprice)
											attribute_old_price = float(op.price_adjustment) + float(x.old_price)
									price_detail = get_product_price(x, customer=customer)
									if price_detail and price_detail.get('discount_amount'):
										
										product_price1 = price_detail.get('rate')
										if x.price != product_price1:
											x.old_price = x.actual_price
											x.price = product_price1
											op.attr_itemprice = product_price1
											if op.is_pre_selected==1:
												attribute_price=float(product_price1)
												attribute_old_price = float(op.price_adjustment) + float(x.old_price)
											else:
												if count == 1:
													attribute_price=float(product_price1)
													attribute_old_price = float(op.price_adjustment) + float(x.old_price)
									count+=1
									if float(x.old_price) > 0:
										op.attr_oldprice = float(op.price_adjustment) + float(x.old_price)
								if x.inventory_method == 'Track Inventory By Product Attributes':
									attribute_ids=op.name+'\n'
									from go1_commerce.go1_commerce.v2.cart \
																import validate_attributes_stock
									variant_comb = validate_attributes_stock(x.name,attribute_ids,attribute,x.minimum_order_qty,add_qty=None)
									if variant_comb:
										op.attr_itemprice = float(variant_comb['price'])
										op.attr_oldprice = float(variant_comb['old_price'])
										if variant_comb.get('discount'):
											op.attr_itemprice = float(variant_comb['discount']['rate'])
											op.attr_oldprice = float(variant_comb['price'])
										op.status = variant_comb['status']
										if variant_comb['status'] =="Success":
											if op.stock and int(op.stock) > 0:
												op.has_attr_stock = True
											else:
												op.has_attr_stock = False
										else:
											op.has_attr_stock = False
										if op.is_pre_selected == 1:
											if op.has_attr_stock  == False:
												has_attr_stock = False
							op.videos = frappe.get_all('Product Attribute Option Video',filters={"option_id":op.name},fields=["youtube_video_id","video_type"])
							if op.image_list:
								op.images = json.loads(op.image_list)
							else:
								op.images = []
				if show_attributes==1:
					from go1_commerce.go1_commerce.v2.cart \
																import validate_attributes_stock
					x.variant_price = validate_attributes_stock(x.name,attribute_ids,attribute,x.minimum_order_qty,add_qty=None)
					x.attribute_price = attribute_price
					x.attribute_old_price = attribute_old_price
				x.have_attribute = 1
				x.product_attributes = product_attributes
			else:
				x.have_attribute = 0
				x.product_attributes = product_attributes
			x.has_attr_stock = has_attr_stock
			product_variant = frappe.db.sql('''select name, attribute_html, attribute_id, stock, price, weight, image, sku, role_based_pricing from `tabProduct Variant Combination` where parent = %(parent)s''',{'parent': x.name}, as_dict=1)
			x.product_variant = product_variant
			specification_group = []
			specification_attribute = frappe.db.sql_list('''select distinct sam.spec_group_name,sg.display_order from `tabSpecification Group` sg inner join `tabProduct Specification Attribute Mapping` sam on sg.name=sam.spec_group_name1 where sam.parent=%(name)s order by sg.display_order''',{'name':x.name})
			if specification_attribute:
				for item in specification_attribute:
					groups = frappe.db.get_all('Product Specification Attribute Mapping',fields=['specification_attribute','options'], filters={"parent":x.name,'spec_group_name':item},order_by='idx')
					specification_group.append({"name":item, "groups":groups})
			else:
				groups = frappe.db.get_all('Product Specification Attribute Mapping',fields=['specification_attribute','options'], filters={"parent":x.name},order_by='idx')
				if groups:
					specification_group.append({"name":"", "groups":groups})
					
			x.product_specification = specification_group
			if not x.product_brand:
				x.product_brand = ''
			else:
				if len(x.product_brand) > 30:
					x.product_brand = x.product_brand[:15] + '...'
			highlights = frappe.db.get_all('Highlights', fields=['highlights'], filters={'parent': x.name})
			x.highlights = highlights
			if x.return_description:
				x.return_policy = x.return_description
			if x.tax_category:
				tax_template = frappe.get_doc('Product Tax Template', x.tax_category)
				x.tax_template = tax_template
			if current_category:
				x.products_per_row = frappe.db.get_value('Product Category', current_category, 'products_per_row_in_list')
			if x.category:
				category1 = frappe.get_doc('Product Category', x.category)
				if category1:
					x.category1 = category1.type_of_category
					x.show_attributes_inlist = show_attributes
			product_reviews = frappe.db.sql('''select ifnull(count(*), 0) as review_count,ifnull(avg(rating), 0) as rating from `tabProduct Review` where product=%(product)s''', {'product': x.name}, as_dict=1)
			if product_reviews:
				x.rating = product_reviews[0].rating
				x.review_count = product_reviews[0].review_count
			product_video = frappe.db.get_all('Product Video', fields=['display_order', 'video_link', 'name', 'video_type'], filters={'parent': x.name}, order_by='display_order')
			x.product_video = product_video
			x.product_tag = frappe.db.get_value('Product', x.name, 'product_tag')
			if x.product_tag:
				tags = json.loads(x.product_tag)
				x.product_tags = frappe.db.get_all('Product Tag', filters={'name': ('in', tags)}, fields=['title', 'icon'])
			custom_values = None
			if catalog_settings.display_custom_fields == 1:
				if frappe.db.get_all("Custom Field",filters={"dt":"Product"}):
					custom_fields = frappe.db.sql('''SELECT fieldname FROM `tabCustom Field` WHERE dt = "Product" AND fieldtype<> "Table" AND fieldtype<> "Section Break" AND fieldtype<> "Column Break" AND fieldtype<> "HTML"  AND fieldtype<> "Check" AND fieldtype<> "Text Editor" ''',as_dict=1)
					query = "SELECT "
					for field in custom_fields:
						query += field.fieldname+","
					query = query[:-1]
					query += " FROM `tabProduct` WHERE name='{0}'".format(x.name)
					columns = ','.join([str(field.fieldname) for field in custom_fields])
					custom_values = frappe.db.sql(query,as_dict=1)
					if custom_values:
						custom_values = custom_values[0]
			x.custom_values = custom_values
	return product

@frappe.whitelist(allow_guest=True)
def get_enquiry_product_detail(product_id):
	cur_category = frappe.db.sql('''select PC.category from `tabProduct`p inner join `tabProduct Category Mapping`PC  where p.name=%(name)s and PC.parent=p.name''', {'name': product_id}, as_dict=1)
	if cur_category:
		for cat in cur_category:
			get_cat = frappe.db.sql('''select parent_product_category,type_of_category from `tabProduct Category` where name=%(name)s''', {'name': cat.category}, as_dict=1)
			if get_cat[0]['type_of_category'] == 'Enquiry Product':
				return get_cat[0]['type_of_category']
			else:
				if get_cat[0]['parent_product_category']:
					get_cat1 = frappe.db.sql('''select parent_product_category,type_of_category from `tabProduct Category` where name=%(name)s''',{'name': get_cat[0]['parent_product_category']}, as_dict=1)
					if get_cat1[0]['type_of_category'] == 'Enquiry Product':
						return get_cat1[0]['type_of_category']
					else:
						if get_cat1[0]['parent_product_category']:
							get_cat2 = frappe.db.sql('''select parent_product_category,type_of_category from `tabProduct Category` where name=%(name)s''',{'name': get_cat1[0]['parent_product_category']}, as_dict=1)
							if get_cat2[0]['type_of_category'] == 'Enquiry Product':
								return get_cat2[0]['type_of_category']
							else:
								return get_cat2[0]['type_of_category']
						else:
							return get_cat1[0]['type_of_category']
				else:
					return get_cat[0]['type_of_category']

@frappe.whitelist(allow_guest=True)
def get_search_products(customer= None,search_text=None, sort_by=None, page_no=1, page_size=12, brands=None,
	rating=None,min_price=None,	max_price=None,	attributes=None, as_html=None, is_list = 0):
	try:
		catalog_settings = frappe.get_single('Catalog Settings')
		if catalog_settings.enable_whoosh_search == 1:
			from go1_commerce.go1_commerce.v2.whoosh \
				import search_product
			return search_product(search_txt=search_text,page_no=page_no,page_length=page_size)
		sort_order = get_sorted_columns(catalog_settings.default_product_sort_order)
		if sort_by:
			sort_order = sort_by
		search_results = get_search_results(search_text,sort_order,page_no,page_size,
						 brands,rating,min_price,max_price,attributes,
						 customer=customer)
		if search_results and is_list == 1:
			search_results = get_list_product_details(search_results,customer)
		return search_results
	except Exception:
		other_exception("Error in v2.product.get_search_products")
		

def get_search_results(search_text, sort_by, page_no, page_size, brands, ratings, 
	min_price,max_price,attributes,customer=None):
	try:
		from frappe.website.utils import cleanup_page_name
		search_text = unquote(search_text)
		queryText = cleanup_page_name(search_text).replace('_', '-')
		catalog_settings = frappe.get_single('Catalog Settings')
		(conditions, sort) = get_conditions_sort(brands, ratings, sort_by, min_price,max_price, attributes)
		searchKey = '"%' + search_text + '%"'
		search_query = ' AND ('
		select_query = ''
		count = 0
		queryKey = '"%' + queryText + '%"'
		if catalog_settings.search_fields:
			select_query = ', (CASE '
			for item in catalog_settings.search_fields:
				search_query += 'P.%s LIKE %s OR ' % (item.fieldname, searchKey)
				select_query += ' WHEN P.%s LIKE %s THEN %s' % (item.fieldname, searchKey, count)
				count = count + 1
			search_query = search_query[:-3]
			select_query += ' ELSE -1 END) AS sort_order'
			sort += ' ORDER BY sort_order ASC'
		if catalog_settings.enable_full_text_search == 1:
			search_text = search_text.replace(" ","-")
			tex1 = []
			text1 = search_text.split()
			for tx in text1:
				tex = '+' + tx + '*'
				tex1.append(tex)
			tex1 = tex1
			l = [item for value in tex1 for item in value]
			l = ''.join(l)
			search_query += " OR S.search_route LIKE '{}' OR MATCH(P.search_words) AGAINST('{}' IN BOOLEAN MODE)".format(queryKey, l)
		else:
			if catalog_settings.search_fields:
				search_query += '   OR S.search_route LIKE %s OR S.search_keywords LIKE %s' % (queryKey,queryKey)
			else:
				search_query += ' S.search_route LIKE %s OR S.search_keywords LIKE %s' % (queryKey,queryKey)
		search_query += ' OR S.search_route LIKE %s' % searchKey
		search_query += ')'
		output = get_search_data(select_query,search_text,page_no,page_size,customer,brands,attributes,
							 conditions,sort,search_query)
		return output
	except Exception:
		other_exception("Error in v2.product.get_search_results")


def get_search_data(select_query,search_text,page_no,page_size,customer,brands,attributes,
							 conditions,sort,search_query):
		try:
			start_with_condition = " and (P.item like '{}%%')".format(search_text)
			list_columns = get_product_list_columns()
			start_with_items  = f"""SELECT DISTINCT 
										{list_columns}
									FROM `tabProduct` P
									LEFT JOIN `tabProduct Search Keyword` S ON S.parent = P.name 
									WHERE P.is_active = 1 
										AND P.status = 'Approved' {select_query}
										{start_with_condition} {conditions} {sort}
									LIMIT 
										{(int(page_no) - 1) * int(page_size)}, {int(page_size)}"""
			query = f"""SELECT DISTINCT 
							{list_columns}
						FROM `tabProduct` P
						LEFT JOIN `tabProduct Search Keyword` s ON S.parent=P.name
						WHERE P.is_active = 1 
							AND P.status = 'Approved' 
							AND (P.route LIKE '%{search_text}%') 
						LIMIT {(int(page_no) - 1) * int(page_size)},{int(page_size)}"""
			data = get_search_result(start_with_items,query,page_size)
			return data
		except Exception:
			frappe.log_error(message=frappe.get_traceback(), 
			title='v2.product.get_search_results')


def get_search_result(start_with_items,query,page_size):
	result = frappe.db.sql(start_with_items, as_dict=1)

	if len(result) < int(page_size) or not result:
		other_items = frappe.db.sql(query, as_dict=1)
		frappe.log_error("other_items",other_items)
		for x in other_items:
			if result:
				allowed = 1
				for old_item in result:
					if old_item.name == x.name:
						allowed = 0
				if allowed == 1 and len(result) <= int(page_size):
					result.append(x)
			else:
				if len(result) <= int(page_size):
					result.append(x)
		frappe.log_error("result",result)
		return result


@frappe.whitelist(allow_guest=True)
def get_sorted_columns(sort_by):
	switcher = { 'Relevance': 'modified desc',
				'Name: A to Z': 'name asc',
				'Name: Z to A': 'name desc',
				'Price: Low to High': 'price asc',
				'Price: High to Low': 'price desc',
				'Newest Arrivals': 'creation desc',
				'Date: Oldest first': 'creation asc'
				}
	return switcher.get(sort_by, 'Invalid value')


@frappe.whitelist(allow_guest=True)
def get_category_page_data(	category = None, sort_by = None, page_no = 1, 
							customer = None,route = None, page_size = no_of_records_per_page,
							brands = None,rating = None, min_price = None,max_price = None,
							attributes = None, as_html = None,productsid = None,view_by = None
						):
	products = get_category_products(category, sort_by, page_no, page_size,brands,rating, 
									min_price, max_price, attributes,as_html,productsid, 
									view_by,customer,route)
	filters = get_category_page_filters(category, brands = brands, ratings= rating,
										min_price = min_price, max_price = max_price)
	return {"products":products,
			"filters":filters}


@frappe.whitelist(allow_guest=True)
def get_category_page_filters(category, brands='', ratings='', min_price='', max_price='', domain=None):
	'''
		To get all available filters in category list page

		param: category: category id
		param: brands: list of brand ids in comma seperated. eg: "brand 1, brand2"
		param: ratings: based on product rating. Ranges from 1 to 4
		param: min_price: minimum price from which products should display
		param: max_price: maximum price upto which products must display
		param: domain: to get data based on the current doamin (for saas model)		 
	'''
	business = None
	if domain:		
		business = get_business_from_web_domain(domain)
	from ecommerce_business_store.ecommerce_business_store.api import item_attribute_filters, get_brands_category_based, get_categories_sidemenu
	attribute_filters = item_attribute_filters(category, brands, ratings, min_price, max_price, business=business)
	brand_filters = get_brands_category_based(category, '', ratings, min_price, max_price, '', business=business)
	category_list = get_categories_sidemenu(category)
	return {'attribute_list': attribute_filters, 'brand_list': brand_filters, 'category_list': category_list}


@frappe.whitelist(allow_guest=True)
def get_brand_based_products(brand=None, sort_by=None, page_no=1,page_size=no_of_records_per_page,
							brands=None, rating=None,min_price=None, max_price=None,attributes=None,
							productsid=None, view_by=None, customer=None,route=None):
	try:
		if route:
			p_brands = frappe.db.get_all("Product Brand",filters={"brand_name":brands})
			if p_brands:
				brand = p_brands[0].name
		default_sort_order = get_settings_value('Catalog Settings','default_product_sort_order')
		sort_order = get_sorted_columns(default_sort_order)
		if sort_by:
			sort_order = sort_by
		brand_products = get_sorted_brand_products(brand, sort_order, page_no, 
													page_size, rating, min_price, max_price, attributes,
													productsid,route)
		if brand_products:
			brand_products = get_list_product_details(brand_products["product"], customer=customer)
		return brand_products
	except Exception:
		other_exception("Error in v2.product.get_brand_based_products")


def get_sorted_brand_products(brand, sort_by, page_no, page_size,route,
								ratings, min_price,max_price, attributes,productsid=None):
	try:
		(conditions, sort) = get_conditions_sort(brand, ratings, sort_by, min_price,max_price, attributes)
		brand_filter = ""
		if brand:
			brand_filter = "'" + brand + "'"
		if productsid:
			conditions += ' and P.name!="{name}"'.format(name=productsid)
		return {"product" : get_sorted_brand_products_query(page_size,conditions,brand_filter,brand,route,
										   		sort_by,page_no,ratings,min_price, max_price, attributes)}
	except Exception:
		other_exception("Error in v2.product.get_sorted_brand_products")


def get_sorted_brand_products_query(page_size,conditions,brand_filter,sort_by,brand,route,
									   page_no,ratings,min_price, max_price, attributes):
	try:
		(conditions, sort) = get_conditions_sort(brand_filter, ratings, sort_by, min_price, max_price, attributes)
		list_columns = get_product_list_columns()
		frappe.log_error("brand_filter",brand_filter)
		query = f"""SELECT DISTINCT {list_columns}
				FROM `tabProduct` P
				LEFT JOIN `tabProduct Search Keyword` s ON s.parent = P.name
				WHERE P.is_active = 1 
					AND P.status = 'Approved' 
					AND (P.brand = {brand_filter})
				ORDER BY P.modified DESC
				LIMIT {(int(page_no) - 1) * int(page_size)},{int(page_size)}"""
		result = frappe.db.sql(query, as_dict=True)
		return result
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'api.get_sorted_brand_products')

@frappe.whitelist(allow_guest=True)
def get_category_products(category=None, sort_by=None, page_no=1,page_size=no_of_records_per_page,
							brands=None, rating=None,min_price=None, max_price=None,attributes=None,
							productsid=None,customer=None,route=None):
	try:
		get_cp_obj = Product()
		return get_cp_obj.get_category_products(category, sort_by, page_no,page_size,
										brands, rating,min_price, max_price,attributes,
										productsid,customer,route)
	except Exception:
		other_exception("Error in v2.product.get_category_products")

def get_sorted_category_products(category, sort_by, page_no, page_size, brands,
	ratings, min_price,max_price, attributes,productsid=None):
	try:
		catalog_settings = frappe.get_single('Catalog Settings')
		(conditions, sort) = get_conditions_sort(brands, ratings, sort_by, min_price, max_price, attributes)
		# frappe.log_error("conditions",conditions)
		category_filter = "'" + category + "'"
		if catalog_settings.include_products_from_subcategories == 1:
			from go1_commerce.go1_commerce.v2.category \
			import get_child_categories
			child_categories = get_child_categories(category)
			if child_categories:
				category_filter = ','.join(['"' + x.name + '"' for x in child_categories])
		if productsid:
			conditions += ' and P.name!="{name}"'.format(name=productsid)
		list_columns = get_product_list_columns()
		query = f"""SELECT DISTINCT {list_columns}
					FROM `tabProduct` P
					INNER JOIN `tabProduct Category Mapping` CM ON CM.parent=P.name
					INNER JOIN `tabProduct Category` pc ON CM.category=pc.name
					WHERE P.is_active = 1 
						AND P.status='Approved' 
						AND CM.category IN ({category_filter}) {conditions}
					GROUP BY P.name {sort}
					LIMIT {(int(page_no) - 1)* int(page_size)},{int(page_size)}"""
		result = frappe.db.sql(query, as_dict=True)
		return result
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'Error in api.get_sorted_category_products')

 
def get_product_list_columns():
	return """P.item, P.price, P.old_price, P.short_description,P.has_variants,
			P.sku, P.name, P.route, P.inventory_method, P.is_gift_card, P.image AS product_image,
			P.minimum_order_qty, P.maximum_order_qty, P.disable_add_to_cart_button, 
			P.weight, P.approved_total_reviews,
			P.brand_unique_name AS brand_route,P.route,P.brand_name AS product_brand"""
   
@frappe.whitelist(allow_guest=True)
def insert_stockavail_notification(data):
	try:
		now = getdate(nowdate())
		response = json.loads(data)
		result = frappe.get_doc({
				 'doctype': 'Product Availability Notification',
				 'email': response.get('sender_email'),
				 'user_name': response.get('sender_name'),
				 'created_date': now,
				 'product': response.get('product'),
				 'attribute_id': response.get('attributeId'),
				 }).insert(ignore_permissions=True)
		return result
	except Exception:
		other_exception("Error in v2.product.insert_stockavail_notification")


@frappe.whitelist(allow_guest=True)
def insert_review(data):
	try:
		val=json.loads(data)
		if catalog_settings.enable_captcha and catalog_settings.review_popup:
			captcha_message = validate_captcha(val.get('private_key'),val.get('captcha_response'))			
			if captcha_message == "Success":
				result = review_captcha_validation(data)
				return result
		else:
			result = review_captcha_validation(data)
			return result
	except Exception:
		other_exception("Error in v2.product.insert_review")


@frappe.whitelist(allow_guest=True)
def validate_captcha(secret, response):
	VERIFY_SERVER="www.google.com"
	params = {
	  'secret': secret,
	  'response': response,
	  'remoteip': get_url()
	}
	url = "https://%s/recaptcha/api/siteverify?%s" % (VERIFY_SERVER, urlencode(params))
	response = requests.get(url)
	return_values = response.json()
	return_code = return_values ["success"]
	if (return_code == True):
		return "Success"
	else:
		return "Failed"


def get_today_date(time_zone=None, replace=False):
	'''
		get today  date based on selected time_zone
	'''
	if not time_zone:
		time_zone = frappe.db.get_single_value('System Settings', 'time_zone')
	currentdatezone = datetime.now(timezone(time_zone))
	if replace:
		return currentdatezone.replace(tzinfo=None)
	else:
		return currentdatezone


@frappe.whitelist(allow_guest=True)
def review_captcha_validation(data):
	try:
		response = json.loads(data)
		review = frappe.new_doc('Product Review')
		review.customer = response.get('user_name')
		review.email = response.get('customer_email')
		review.rating = response.get('rating')/5
		review.review_title = response.get('title')
		review.image = response.get('image')
		review.product = response.get('item')
		review.product_name = frappe.db.get_value('Product', response.get('item'), 'item')
		review.review_message = response.get('message')
		if catalog_settings.product_reviews_to_be_approved:
			review.is_approved = 0
		else:
			review.is_approved = 1
		review.save(ignore_permissions=True)
		review.creation = getdate(review.creation).strftime('%b %d, %Y')
		return review.as_dict()
	except Exception:
		other_exception("Error in v2.product.review_captcha_validation")


def get_bought_together(customer):
	list_columns = get_product_list_columns()
	items = frappe.db.sql(f"""SELECT 
								{list_columns}
							FROM `tabProduct` P
							INNER JOIN `tabOrder Item` OI ON P.name = OI.item 
							LEFT JOIN `tabOrder` O ON O.name = OI.parent 
							WHERE O.docstatus = 1 
								AND O.status <> "Cancelled" 
								AND O.name IN (
												SELECT DISTINCT OI1.parent 
												FROM `tabOrder Item` OI1 
												WHERE OI1.parenttype = "Order") 
								AND OI.is_free_item = 0  
							GROUP BY P.name 
							LIMIT 10""", as_dict = 1)
	if items:
		items = get_list_product_details(items,customer=customer)
	return items


def get_attributes_combination(attribute):
	try:
		combination=frappe.db.get_all('Product Variant Combination',
										filters={'attribute_id':attribute},fields=['*'])
		for item in combination:
			if item and item.get('attribute_id'):
				variant = item.get('attribute_id').split('\n')
				attribute_html = ""
				for obj in variant:
					if obj:
						if attribute_html:
							attribute_html +=", "
						if frappe.db.get_all("Product Attribute Option",filters={"name":obj}):
							option_value, attribute = frappe.db.get_value("Product Attribute Option", obj, 
                                                    					["option_value","attribute"])
							attribute_name = frappe.db.get_value("Product Attribute", attribute, "attribute_name")
							attribute_html += attribute_name+" : "+option_value
				item["combination_txt"] = attribute_html
		return combination
	except Exception:
		frappe.log_error(title=f' Error in v2.product.get_attributes_combination',
		message=frappe.get_traceback())
  
  
@frappe.whitelist(allow_guest=True)
def search_data(content,page_no=1,page_length=20):
	import os
	from frappe.utils import get_files_path
	from whoosh import sorting
	from whoosh.index import open_dir
	from whoosh.qparser import MultifieldParser
	try:
		path = get_files_path()
		file_name = os.path.join(path,'whoosh_search')
		ix = open_dir(file_name)
		with ix.searcher() as searcher:
			query1 = MultifieldParser(["title", "search_keyword"],ix.schema).parse(content)
			facet = sorting.FieldFacet("title", reverse=False)
			results = searcher.search_page(query1, page_no,pagelen=page_length)
			return results
	except Exception as e:
		frappe.log_error(message = frappe.get_traceback(), 
						 title='v2.product.api.search_data')
		return {
				"status":"failed",
				"message":"There is no data here"
				}
  
@frappe.whitelist()
def update_to_file(file_name, upload_doc, file_type, file_path, docname, name, total_files,
	current_file, doctype, parentfield, image_doctype='Product Image'):
	try:
		if doctype == 'Business':
			image_doctype = 'Business Images'
		if doctype == 'Deity':
			image_doctype = 'Photo Gallery'
		items = frappe.new_doc(image_doctype)
		items.image_name = file_name
		items.title = file_name
		file = frappe.get_doc("File",name)
		file_path = file.file_url
		if doctype == 'Product':
			items.product_image = file.file_url
		elif doctype == 'Recipe':
			items.recipe_image = file_path
			items.list_image = file_path
		elif doctype == 'Deity':
			items.product_image = file.file_url
		else:
			items.business_image = file_path
		items.parenttype = doctype
		items.parentfield = parentfield
		items.parent = docname
		items.flags.ignore_mandatory = True

		items.save(ignore_permissions=True)
		if image_doctype == "Product Image":
			product = frappe.get_doc("Product",items.parent)
			media_settings=get_settings('Media Settings')
			convert_thumbnails(items,media_settings)

		if image_doctype == "Photo Gallery":
			product = frappe.get_doc("Deity",items.parent)
			media_settings=get_settings('Media Settings')
			convert_deity_thumbnails(items,media_settings)
		if int(total_files) == int(current_file):
			doc = frappe.get_doc(doctype, docname)
			doc.save(ignore_permissions=True)
		return items.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'Error in api.update_to_file')


@frappe.whitelist()
def convert_thumbnails(product_image,media_settings):
	file_doc = frappe.db.exists("File", {
					"file_url": product_image.product_image,
					"attached_to_doctype": "Product",
					"attached_to_name": product_image.parent
				})
	if file_doc:
		img_files=product_image.product_image.split('/')
		image_file=img_files[len(img_files)-1].split('.')
		converted_file_name = image_file[0]
		product_categories = frappe.get_all("Product Category Mapping",order_by="idx",filters={"parent":product_image.parent},fields=['category'])
		list_size=media_settings.list_thumbnail_size
		if product_categories:
			for p_category in product_categories:
				check_list_size=frappe.db.get_value('Product Category',p_category.category,'product_image_size')
				if check_list_size>0:
					list_size = check_list_size
					break
		if product_image.product_image.startswith("/files"):
			converted_file_name = product_image.product_image.split('.')[0]
		convert_product_thumbnail_image(product_image.product_image,list_size,product_image.parent,'list_image',product_image.name)
		product_image.list_image=converted_file_name+"_"+str(list_size)+"x"+str(list_size)+"."+image_file[len(image_file)-1]
		convert_product_thumbnail_image(product_image.product_image,media_settings.detail_thumbnail_size,product_image.parent,'detail_thumbnail',product_image.name)
		convert_product_thumbnail_image(product_image.product_image,media_settings.email_thumbnail_size,product_image.parent,'email_thumbnail',product_image.name)
		convert_product_thumbnail_image(product_image.product_image,media_settings.detail_image_size,product_image.parent,'detail_image',product_image.name)
		convert_product_thumbnail_image(product_image.product_image,media_settings.mini_cart_image_size,product_image.parent,'mini_cart',product_image.name)
		convert_product_thumbnail_image(product_image.product_image,media_settings.cart_thumbnail_size,product_image.parent,'cart_thumbnail',product_image.name)
		apps = frappe.get_installed_apps()
		disabled_s3 = 1
		if 'frappe_s3_attachment' in apps:
			disabled_s3 = 0
			s3_settings = frappe.get_doc('S3 File Attachment','S3 File Attachment')
			if s3_settings.disable_s3_file_attachment==1:
				disabled_s3 = 1
		if not 'frappe_s3_attachment' in apps or disabled_s3:
			product_image.detail_thumbnail=converted_file_name+"_"+str(media_settings.detail_thumbnail_size)+"x"+str(media_settings.detail_thumbnail_size)+"."+image_file[len(image_file)-1]
			product_image.save()

			product_image.email_thumbnail=converted_file_name+"_"+str(media_settings.email_thumbnail_size)+"x"+str(media_settings.email_thumbnail_size)+"."+image_file[len(image_file)-1]
			product_image.save()
		
			product_image.detail_image=converted_file_name+"_"+str(media_settings.detail_image_size)+"x"+str(media_settings.detail_image_size)+"."+image_file[len(image_file)-1]
			product_image.save()
		
			product_image.mini_cart = converted_file_name + "_" + str(media_settings.mini_cart_image_size)+"x"+str(media_settings.mini_cart_image_size)+"."+image_file[len(image_file)-1]
			product_image.save()
		
			product_image.cart_thumbnail=converted_file_name+"_"+str(media_settings.cart_thumbnail_size)+"x"+str(media_settings.cart_thumbnail_size)+"."+image_file[len(image_file)-1]                    
			product_image.save()


@frappe.whitelist()
def convert_product_thumbnail_image(image_name, size, productid, updated_column = None, updated_name = None):
	try:		
		org_file_doc = frappe.get_doc("File", {
					"file_url": image_name,
					"attached_to_doctype": "Product",
					"attached_to_name": productid
				})
		if org_file_doc:
			return_url = org_file_doc.make_thumbnail(
													set_as_thumbnail = False,
													width = size,
													height = size,
													suffix = str(size) + "x" + str(size),
													updated_doc = "Product Image",
													updated_name = updated_name,
													updated_column = updated_column
												)
			return return_url
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in v2.product.convert_product_image") 



@frappe.whitelist()
def convert_deity_thumbnails(product_image,media_settings):
	
	file_doc = frappe.db.exists("File", {
					"file_url": product_image.product_image,
					"attached_to_doctype": "Deity",
					"attached_to_name": product_image.parent
				})
	if file_doc:
		img_files=product_image.product_image.split('/')
		image_file=img_files[len(img_files)-1].split('.')
		converted_file_name = image_file[0]
		if product_image.product_image.startswith("/files"):
			converted_file_name = product_image.product_image.split('.')[0]
		convert_deity_thumbnail_image(
										product_image.product_image,
										media_settings.list_thumbnail_size,
										product_image.parent,
										'list_image',
										product_image.name
									)
		product_image.list_image=converted_file_name+"_"+str(media_settings.list_thumbnail_size)+"x"+str(media_settings.list_thumbnail_size)+"."+image_file[len(image_file)-1]
		convert_deity_thumbnail_image(
										product_image.product_image,
										media_settings.detail_thumbnail_size,
										product_image.parent,
										'detail_thumbnail',
										product_image.name
									)
		convert_deity_thumbnail_image(
										product_image.product_image,
										media_settings.detail_image_size,
										product_image.parent,'detail_image',
										product_image.name
									)
		
		apps = frappe.get_installed_apps()
		disabled_s3 = 1
		if 'frappe_s3_attachment' in apps:
			disabled_s3 = 0
			s3_settings = frappe.get_doc('S3 File Attachment','S3 File Attachment')
			if s3_settings.disable_s3_file_attachment==1:
				disabled_s3 = 1
		if not 'frappe_s3_attachment' in apps or disabled_s3:
			product_image.detail_thumbnail=converted_file_name+"_"+str(media_settings.detail_thumbnail_size)+"x"+str(media_settings.detail_thumbnail_size)+"."+image_file[len(image_file)-1]
			product_image.save()
	
			product_image.detail_image=converted_file_name+"_"+str(media_settings.detail_image_size)+"x"+str(media_settings.detail_image_size)+"."+image_file[len(image_file)-1]
			product_image.save()
		

@frappe.whitelist()
def convert_deity_thumbnail_image(image_name,size,productid,updated_column=None,updated_name=None):
	try:
		
		org_file_doc = frappe.get_doc("File", {
					"file_url": image_name,
					"attached_to_doctype": "Deity",
					"attached_to_name": productid
				})
		frappe.log_error(size,"size")
		if org_file_doc:
			return_url = org_file_doc.make_thumbnail(set_as_thumbnail=False,width=size,height=size,suffix=str(size)+"x"+str(size),updated_doc="Photo Gallery",updated_name=updated_name,updated_column=updated_column)
			
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in v2.common.convert_deity_thumbnail_image") 

@frappe.whitelist(allow_guest=True)
def delete_current_attribute_img(docname, childname):
	doc = frappe.get_doc('Product Attribute Option', docname)
	if doc.image_list:
		img_list = json.loads(doc.image_list)
		deleted_doc = next((x for x in img_list if x.get('name') == childname), None)
		images = list(filter(lambda x: x.get('name') != childname, img_list))
		doc.image_list = json.dumps(images)
		doc.save(ignore_permissions=True)
		delete_attribute_image(deleted_doc)


@frappe.whitelist()
def update_attribute_option_images(dn, docs):
	docs = json.loads(docs)
	doc = frappe.get_doc('Product Attribute Option', dn)
	if doc.image_list:
		images_list = json.loads(doc.image_list)
		for item in images_list:
			check = next(x for x in docs if x.get('name')
						 == item.get('name'))
			if check:
				item['is_primary'] = check['is_primary']
				item['idx'] = check['idx']
				if check['title']:
					item['title'] = check['title']
		images_list = sorted(images_list,key=lambda x:x.get('idx'),reverse=False)
		doc.image_list = json.dumps(images_list)
		doc.save(ignore_permissions=True)
		frappe.db.commit()


@frappe.whitelist(allow_guest=True)
def get_file_uploaded_imagelist(child_name, child_doctype):
	attribute = frappe.get_doc(child_doctype, child_name)
	if attribute.image_list:
		return json.loads(attribute.image_list)
	return []

@frappe.whitelist(allow_guest=True)
def get_file_uploaded_imagelist1(name, product, device_type,image_position, child_table=None):
	try:
		image_list = []
		video_list = []
		child_doc = 'Product Attribute Option'
		if child_table:
			child_doc = child_table
		attribute = frappe.get_doc(child_doc, name)
		attr_product_title = ''
		if attribute.product_title:
			attr_product_title = attribute.product_title
		if attribute.image_list:
			images = json.loads(attribute.image_list)
			for im in images:
				image_list.append({'original_image': im.get('image'),
								  'detail_image': im.get('detail_thumbnail'),
								  'detail_thumbnail': im.get('thumbnail')})
		attribute_video = frappe.get_all('Product Attribute Option Video', filters={'option_id': name}, fields=['youtube_video_id','video_type'])
		if attribute_video:
			for video in attribute_video:
				if video.youtube_video_id:
					video_list.append({'video_link': video.youtube_video_id,'video_type':video.video_type})
		
		if device_type == 'Desktop':
			if len(image_list) > 0 or len(video_list) > 0:
				image_template = frappe.render_template('/templates/pages/DetailPage/productimages.html'
						, {'attr_image': image_list, 'demo_video': video_list,'image_position':image_position})
				return {'image_template':image_template, 'product_title':attr_product_title}
			else:
				return {'product_title':attr_product_title}
		else:
			return {'attr_image': image_list, 'demo_video': video_list, 'product_title':attr_product_title}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'Error in v2.product.get_file_uploaded_imagelist1')


@frappe.whitelist()
def update_attribute_images(name, dt, dn):
	doc = frappe.get_doc(dt, dn)
	is_primary = 1
	if not doc.image_list:
		image_list = []
	else:
		image_list = json.loads(doc.image_list)
		check_primary = next((x for x in image_list if x.get('is_primary') == 1), None)
		if check_primary:
			is_primary = 0
	file = frappe.get_doc('File', name)
	media_settings = get_settings('Media Settings')
	(thumbnail, detail_thumbnail) = (None, None)
	image_file = file.file_name.split('.')
	if media_settings.detail_image_size:
		size = media_settings.detail_image_size
		detail_thumbnail = file.make_thumbnail(
												set_as_thumbnail = False, 
												width = size, 
												height = size, 
												suffix = str(size) + 'x' + str(size)
											)
	if media_settings.detail_thumbnail_size:
		size1 = media_settings.detail_thumbnail_size
		thumbnail = file.make_thumbnail(set_as_thumbnail=False, width=size1, height=size1, suffix=str(size1) + 'x' + str(size1))
	obj = {
		'name': name,
		'is_primary': is_primary,
		'title': file.file_name,
		'image': file.file_url,
		'thumbnail': thumbnail,
		'detail_thumbnail': detail_thumbnail,
		'parent': doc.name,
		'parenttype': dt,
		}
	image_list.append(obj)
	doc.image_list = json.dumps(image_list)
	doc.save(ignore_permissions=True)
	return image_list
 
@frappe.whitelist()
def update_videoto_file(file_name, upload_doc, file_type, file_path, docname, name, total_files,
	current_file, doctype, parentfield, video_doctype='Product Video', video_field=None):
	try:
		if doctype == 'Deity':
			video_doctype = 'Video Gallery'
		items = frappe.new_doc(video_doctype)
		items.image_name = file_name
		items.title = file_name
		if doctype == 'Product':
			items.video_link = file_path
			items.video_type = "Other"
		if doctype == 'Deity':
			items.video_link = file_path
			items.video_type = "Other"
		items.parenttype = doctype
		items.parentfield = parentfield
		items.parent = docname
		items.flags.ignore_mandatory = True
		items.save(ignore_permissions=True)
		if int(total_files) == int(current_file):
			doc = frappe.get_doc(doctype, docname)
			doc.save(ignore_permissions=True)
		return items.name
	except Exception:
		frappe.log_error('Error in v2.common.update_videoto_file', frappe.get_traceback())