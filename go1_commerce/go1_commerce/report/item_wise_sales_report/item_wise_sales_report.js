// Copyright (c) 2016, Tridots Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Wise Sales Report"] = {
	"filters": [
		
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": __("From Date"),
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "business",
			"fieldtype": "Link",
			"label": __("Business"),
			"options": "Business"
		},
	],
	"onload": function() {
		var business_filter = frappe.query_report.get_filter('business');
		if(frappe.session.user != 'Administrator' && has_common(['Vendor'], frappe.user_roles)){
			business_filter.df.hidden = 1;
			business_filter.refresh();
		}
	}
};
