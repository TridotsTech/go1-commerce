frappe.provide("go1_commerce");
frappe.provide("go1_commerce.utils");

$.extend(go1_commerce, {
	sample: function(company) {
	console.log("-")
	}
})
$.extend(go1_commerce.utils, {
	get_party_name: function(party_type) {
		var dict = {'Customers': 'full_name', 'Shop User': 'full_name'};
		return dict[party_type];
	},
	get_tree_options: function(option) {
		
		let unscrub_option = frappe.model.unscrub(option);
		let user_permission = frappe.defaults.get_user_permissions();
		let options;

		if(user_permission && user_permission[unscrub_option]) {
			options = user_permission[unscrub_option].map(perm => perm.doc);
		} else {
			options = $.map(locals[`:${unscrub_option}`], function(c) { return c.name; }).sort();
		}
		
		return options.filter((value, index, self) => self.indexOf(value) === index);
		
	},
	create_new_doc: function (doctype, update_fields) {
		frappe.model.with_doctype(doctype, function() {
			var new_doc = frappe.model.get_new_doc(doctype);
			for (let [key, value] of Object.entries(update_fields)) {
				new_doc[key] = value;
			}
			frappe.ui.form.make_quick_entry(doctype, null, null, new_doc);
		});
	}
});