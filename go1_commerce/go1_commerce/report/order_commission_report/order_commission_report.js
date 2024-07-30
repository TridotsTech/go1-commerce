// Copyright (c) 2016, Tridots Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Order Commission Report"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(),-1),
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname":"restaurant",
			"label":__("Restaurant"),
			"fieldtype":"Link",
			"options":"Business"			
		},
		{
			"fieldname":"status",
			"label":__("Order Status"),
			"fieldtype":"Link",
			"options":"Order Status",
			get_query:function(){
				return{
					query: "go1_commerce.go1_commerce.doctype.order.order.get_order_status"
				};
			}			
		}
	],
}
