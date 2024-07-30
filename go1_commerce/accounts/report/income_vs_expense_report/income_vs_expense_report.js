// Copyright (c) 2016, Tridots Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Income Vs Expense Report"] = {
	"filters": [
		
		{
			"fieldname": "year",
			"fieldtype": "Select",
			"label": __("Year"),
			"options": "2021\n2020",
			"reqd": 1
		}
	],
	"onload": function() {
		
		frappe.call({
			method: 'go1_commerce.accounts.report.income_vs_expense_report.income_vs_expense_report.get_year_list',
			args: {},
			callback: function(r) {
				if(r.message && r.message.length > 0) {
					let year_filter = frappe.query_report.get_filter('year');
					year_filter.df.options = r.message;
					year_filter.refresh();
					frappe.query_report.set_filter_value('year', r.message[0]);
				}
			}
		})
	}
};
