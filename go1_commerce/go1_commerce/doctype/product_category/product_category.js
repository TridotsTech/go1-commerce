// Copyright (c) 2018, info@valiantsystems.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Product Category', {
    refresh: function(frm) {
        frm.events.filter_link_field_data(frm)
        frm.events.change_field_property(frm)
    },
    onload: function(frm) {
        frm.list_route = "Tree/Product Category";
        frm.fields_dict['parent_product_category'].get_query = function(doc, cdt, cdn) {
            return {
                filters: [
                    ['Product Category', 'is_group', '=', 1],
                    ['Product Category', 'name', '!=', doc.product_category_name]
                ]
            }
        }
    },
    filter_link_field_data(frm){
        frm.set_query("parent_product_category", function() {
            return {
                "query": "go1_commerce.go1_commerce.doctype.product_category.product_category.get_parent_category"
            };
        });
        
    },
    change_field_property(frm){
        if (frappe.session.user == "Administrator") {
            frm.set_df_property('route', 'read_only', 0)
        } 
        else {
            frm.set_df_property('route', 'read_only', 1)
        }
        frappe.call({
            method: 'go1_commerce.utils.setup.get_settings_from_domain',
            args: {
                dt: 'Catalog Settings'
            },
            async: false,
            callback: function(r) {
                if(r.message){
                    if(r.message.enable_megamenu != 1) {
                        frm.toggle_display(['mega_menu_column', 'menu_image'], false);
                    }
                }
            }
        })
    }
})
