# Copyright (c) 2023, Tridots Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from go1_commerce.go1_commerce.v2.product import get_attributes_combination

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
	condition = ''
	combination_txt = ''
	if filters and filters.get('product_id'):
		condition += f"AND P.name = '{filters.get('product_id')}'"


	query = f''' SELECT P.name product_id,P.item product_name,PVC.attribute_id AS variant_id,
				 "" AS variant,
				 PVC.sku
				 FROM `tabProduct` P
				 INNER JOIN `tabProduct Variant Combination` PVC ON PVC.parent = P.name 
				 WHERE P.has_variants = 1 AND PVC.attribute_id IS NOT NULL AND PVC.disabled=0 
				 AND PVC.show_in_market_place=1 {condition} ORDER BY P.creation DESC
			'''
	response = frappe.db.sql(query,as_dict=1)
	for res in response:
		combination_txt_resp = get_attributes_combination(res.variant_id)
		if combination_txt_resp:
			res.variant = combination_txt_resp[0].combination_txt
		if res.variant_id:
			res.variant_id = res.variant_id.replace("\n","\\n")
	return response