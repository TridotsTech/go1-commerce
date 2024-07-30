// Copyright (c) 2016, Tridots Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Total Orders"] = {
	"filters": [
		{
			"fieldname":"year",
			"fieldtype":"Select",
			"label":__("Year")
		},
		{
			"fieldname":"month",
			"fieldtype":"Select",
			"options":"\nJanuary\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
			"label":__("Month")
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": "",
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": "",
			"reqd": 1
		},
		{
			"fieldname":"restaurant",
			"label":__("Business"),
			"fieldtype":"Link",
			"options":"Business"			
		},
		{
			"fieldname":"status",
			"label":__("Order Status"),
			"fieldtype":"Select",
			"options":"\nPlaced\nProcessing\nCompleted\nCancelled"			
		},
		{
			"fieldname":"payment_status",
			"label":__("Payment Status"),
			"fieldtype":"Select",
			"options":"\nPending\nPaid\nCancelled"			
		}
		
	],
	"onload": function() {
		return frappe.call({
			method: "go1_commerce.go1_commerce.report.total_orders.total_orders.get_years",
			callback: function(r) {
				console.log(r.message)
				var year_filter = frappe.query_report_filters_by_name.year;
				year_filter.df.options = r.message;
				year_filter.df.default = r.message.split("\n")[0];
				year_filter.refresh();
				year_filter.set_input(year_filter.df.default);
			}
		});
	}
}
