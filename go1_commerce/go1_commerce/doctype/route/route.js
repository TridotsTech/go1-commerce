// Copyright (c) 2023, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Route", {
	refresh(frm) {
        $('div[data-fieldname="route_se"] .grid-add-row').text('Add SE');
        frm.set_query("se", function() {
            return {
                "filters": {
                    "role": "Sales Team",
                }
            };
        });
	},
    centre:function(frm){
       frm.fields_dict['route_se'].grid.get_field('se').get_query =
            function() {
                return {
                    filters: {
                        "centre": frm.doc.centre,
                        "role": "Sales Team",
                    }
                }
            }
    },
});

