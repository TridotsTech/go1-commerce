// Copyright (c) 2016, Tridots Tech and contributors
// For license information, please see license.txt
/* eslint-disable */
if (has_common(frappe.user_roles, ['Admin'])) {
frappe.query_reports["Driver Earnings"] = {
	"filters": [
		{
			"fieldname": "driver",
			"fieldtype": "Link",
			"label": "Driver",
			"options": "Drivers"
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
		}
	]
};
}
else{
	frappe.query_reports["Driver Earnings"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": __("From Date"),
			"default": "",
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": "",
			"reqd": 1
		}
	]
};
}
