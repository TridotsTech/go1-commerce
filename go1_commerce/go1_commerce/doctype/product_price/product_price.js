// Copyright (c) 2022, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Product Price', {
	onload: function(frm) {
        frm.events.get_attributes_combination(frm)
		frm.add_fetch("price_list", "buying", "buying");
		frm.add_fetch("price_list", "selling", "selling");
		frm.add_fetch("price_list", "currency", "currency");
	},
    get_attributes_combination(frm){
        if (frm.doc.product) {
            frappe.call({
                method: "go1_commerce.go1_commerce.doctype.product_price.product_price.get_attributes_combination",
                args: {
                    product: frm.doc.product
                },
                callback: function(data) {
                    var options = [];
                    if(data.message){
                        (data.message[0]).forEach(function(row) {
                            if(row){
                                options.push({"value":row.attribute_id,"label":row.combination_txt}) 
                            }
                        })
                    }
                    if(options.length>0){
                        cur_frm.set_df_property("attribute_id", "hidden", 0)
                        cur_frm.set_df_property("attribute_id", "options", options)
                    }
                    else{
                        cur_frm.set_df_property("attribute_id", "hidden", 1)
                        cur_frm.set_value("attribute_id", "")
                    }
                }
            })
        }
    },
    product: function(frm){
        if (frm.doc.product) {
            frappe.call({
                method: "go1_commerce.go1_commerce.doctype.product_price.product_price.get_attributes_combination",
                args: {
                    product: frm.doc.product
                },
                callback: function(data) {
                    var options = [];
                    if(data.message){
                        (data.message[0]).forEach(function(row) {
                            if(row){
                                options.push({"value":row.attribute_id,
                                    "label":row.combination_txt}) 
                            }
                        })
                    }
                    if(options.length>0){
                        cur_frm.set_df_property("attribute_id", "hidden", 0)
                        cur_frm.set_df_property("attribute_id", "options", options)
                    }
                    else{
                        cur_frm.set_df_property("attribute_id", "hidden", 1)
                        cur_frm.set_value("attribute_id", "")
                    }
                    cur_frm.refresh();
                }
            })
        }
    }
});

frappe.ui.form.on("Product Price Detail", "pricing_add", function(frm, cdt,cdn){
    let len = frm.doc.pricing.length;
    var row = locals[cdt][cdn];
    if(len>1){
        let last = frm.doc.pricing[len-2];
        if(last.last_unit!="Inf"){
            row.first_unit = parseInt(last.last_unit)+1
            row.last_unit = "Inf"
            cur_frm.refresh_field("pricing");
        }
    }
    else{
        row.first_unit = 1
        row.last_unit = "Inf"
        cur_frm.refresh_field("pricing");
    }
});