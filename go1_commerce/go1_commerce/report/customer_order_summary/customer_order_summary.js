// Copyright (c) 2023, Tridots Tech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer Order Summary"] = {
	"filters": [
			{
				"fieldname":"from_date",
				"fieldtype":"Date",
				"label":__("From Date"),
				"default":""
			},
			{
				"fieldname":"to_date",
				"fieldtype":"Date",
				"label":__("To Date"),
				"default":""
			}
	]
};
