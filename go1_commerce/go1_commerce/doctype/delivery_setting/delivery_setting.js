// Copyright (c) 2021, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Delivery Setting', {
	refresh: function(frm) {
       var category_lists = ""
         frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.delivery_setting.delivery_setting.check_category_exist_or_not',
            args: {},
            callback: function(r){
                if(r.message){
                    category_lists = r.message
                }
            }
        });
        frm.set_query("delivery_slot_category", function() {
            console.log(frm.doc.category)
            return {
                "filters": {
                    "name": ["not in", category_lists]
                }
            }
        })
	}
});
