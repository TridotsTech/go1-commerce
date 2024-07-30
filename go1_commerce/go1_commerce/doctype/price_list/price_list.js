// Copyright (c) 2023, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Price List', {
	refresh: function(frm) {
		frm.set_query("zone", "zones", function (doc, cdt, cdn) {
            return {
              'filters': {
                    "approval_status" : "Approved",
					"allow_product_listing" : 1,
					"disabled" : 0,
					"fulfillment_center" : 1
                }
            };
        });
	}
});
