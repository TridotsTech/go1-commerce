// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

frappe.listview_settings['Customers'] = {
	refresh: function(doclist){
		doclist.page.add_inner_button(__("Tree View"), function() {
	       frappe.set_route('Tree', 'Customers','List');
	    });
	},
	
};