// Copyright (c) 2018, info@valiantsystems.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Review', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on("Review Score Value", {
	rating: function(frm) {
		var total_amount = 0;
		var Count = frm.doc.score_value.length;
		for(var i = 0; i < frm.doc.score_value.length ; i++) {
			total_amount += frm.doc.score_value[i].rating;
		}
		var Final = total_amount / Count;
		frm.set_value("overall__rating", Final);
	}
});
