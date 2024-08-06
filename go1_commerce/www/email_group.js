// Copyright (c) 2019, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Email Group', {
	refresh: function(frm) {
		frm.add_custom_button(__("Import From Excel"), function() {			
			frappe.call({
				method: 'go1_commerce.go1_commerce.api.create_data_import',
				args:{
					document_type: 'Email Group Member'
				},
				callback: function(r){
					if(r.message)
						frappe.set_route('Form','Data Import', r.message.name)
				}
			})
		}, __("Action"));
	}
});