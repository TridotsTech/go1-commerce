// Copyright (c) 2016, sivaranjani and contributors
// For license information, please see license.txt

frappe.query_reports["Customer Order"] = {
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
			"fieldtype":"Select",
			"options":"\nPlaced\nProcessing\nCompleted\nCancelled"			
		},
		{
			"fieldname":"payment_status",
			"label":__("Payment Status"),
			"fieldtype":"Select",
			"options":"\nPending\nPaid\nCancelled"			
		},
		{
			"fieldname":"order_from",
			"label":__("Order From"),
			"fieldtype":"Select",
			"options":"\nWebsite\nAndroid Mobile App\nIOS Mobile App\nPOS"			
		},	
	],
	"onload": function() {
		var order_from_filter = frappe.query_report.get_filter('order_from');
			order_from_filter.df.hidden = 1;
			order_from_filter.refresh();
	}
}