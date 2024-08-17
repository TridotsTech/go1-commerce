# Copyright (c) 2023, Tridots Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from go1_commerce.go1_commerce.v2.product import get_attributes_combination
from frappe.query_builder import DocType, Order

def execute(filters=None):
	columns, data = get_columns(), get_datas(filters)
	return columns, data

def get_columns():
	col = []	
	col.append(_("Product ID")+":Link/Product:100")
	col.append(_("Product Name")+":Data:300")
	col.append(_("Variant ID")+":Data:220")
	col.append(_("Variant")+":Data:350")
	col.append(_("SKU")+":Data:100")
	return col
def get_datas(filters):
	Product = DocType('Product')
	VariantCombination = DocType('Product Variant Combination')
	query = (
		frappe.qb.from_(Product)
		.inner_join(VariantCombination)
		.on(Product.name == VariantCombination.parent)
		.select(
			Product.name.as_("product_id"),
			Product.item.as_("product_name"),
			VariantCombination.attribute_id.as_("variant_id"),
			frappe.qb.from_(f"''").as_("variant"),
			VariantCombination.sku
		)
		.where(Product.has_variants == 1)
		.where(VariantCombination.attribute_id.isnotnull())
		.where(VariantCombination.disabled == 0)
		.where(VariantCombination.show_in_market_place == 1)
	)
	
	if filters and filters.get('product_id'):
		query = query.where(Product.name == filters.get('product_id'))
	
	query = query.orderby(Product.creation, order=Order.desc)
	
	response = query.run(as_dict=True)
	for res in response:
		combination_txt_resp = get_attributes_combination(res.variant_id)
		if combination_txt_resp:
			res.variant = combination_txt_resp[0].combination_txt
		if res.variant_id:
			res.variant_id = res.variant_id.replace("\n","\\n")
	return response