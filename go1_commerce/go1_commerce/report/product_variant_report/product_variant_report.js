// Copyright (c) 2023, Tridots Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Product Variant Report"] = {
	"filters": [
	{
		"fieldname":"product_id",
		"fieldtype":"Link",
		"options":"Product",
		"label":__("Product ID"),
	}
	]
};