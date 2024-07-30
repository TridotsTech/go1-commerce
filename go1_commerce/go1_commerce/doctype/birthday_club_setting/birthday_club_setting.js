// Copyright (c) 2021, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('BirthDay Club Setting', {
	refresh: function(frm) {
		 if(frappe.modules.Loyalty==undefined){
		 	frm.set_df_property('beneficiary_method', 'options', ['Discount', 'Wallet']); 
		 	frm.refresh_field('beneficiary_method');
		 }
	}
});
