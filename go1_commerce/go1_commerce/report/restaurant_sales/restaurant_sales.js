// Copyright (c) 2016, Tridots Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Restaurant Sales"] = {
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
	"onload": function() {
		return frappe.call({
			method: "go1_commerce.go1_commerce.report.total_orders.total_orders.get_years",
			callback: function(r) {
				var year_filter = frappe.query_report.get_filter('year');
				year_filter.df.options = r.message;
				year_filter.df.default = r.message.split("\n")[0];
				year_filter.refresh();
				year_filter.set_input(year_filter.df.default);
			}
		});
		return frappe.call({
			method: "go1_commerce.go1_commerce.report.total_orders.total_orders.get_curmonth",
			callback: function(r) {
				var month_filter = frappe.query_report.get_filter('month');
				month_filter.df.default = r.message.split("\n")[0];
				month_filter.refresh();
				month_filter.set_input(month_filter.df.default);
			}
		});
	}
}



