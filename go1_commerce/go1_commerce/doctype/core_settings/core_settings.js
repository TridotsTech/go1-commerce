// Copyright (c) 2019, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Core Settings', {
	refresh: function(frm) {
		if(frappe.session.user=="Administrator"){
			frm.add_custom_button(__('Set Default'), function() {
				frappe.call({
					method: 'go1_commerce.go1_commerce.doctype.core_settings.core_settings.set_global_defaults',
					args: {"val":"inventory_management"},
					callback: function(r) {
						frappe.show_alert("Global default set.")
					}
			    })
		
			});
		}
	}
});
