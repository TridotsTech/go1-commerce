// Copyright (c) 2016, Tridots Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Daily Sales Report"] = {
	"filters": [
		{
			"fieldname":"date",
			"label": __("Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		}
	],
	"onload": function(){
		var business_filter = frappe.query_report.get_filter('business');
		if(frappe.session.user != 'Administrator' && has_common(['Vendor'], frappe.user_roles)){
			business_filter.df.hidden = 1;
			business_filter.refresh();
		}
	}
};
