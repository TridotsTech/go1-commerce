// Copyright (c) 2016, Tridots Tech and contributors
// For license information, please see license.txt
frappe.query_reports["Monthly Sales Report"] = {
	"filters": [
		{
			"fieldname":"year",
			"fieldtype":"Select",
			"label":__("Year"),
			"reqd": 1
		},
		{
			"fieldname": "month",
			"fieldtype": "Select",
			"label": "Month",
			"reqd": 1,
			"options": "January\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember"
		},
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": __("From Date"),
			"default": ""
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": ""
		},
	],
	"onload": function() {
		let today_date = new Date(frappe.datetime.get_today());
		let month_filter = frappe.query_report.get_filter('month');
		month_filter.set_input(today_date.toLocaleString('default', {month: 'long'}));
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
	}
};