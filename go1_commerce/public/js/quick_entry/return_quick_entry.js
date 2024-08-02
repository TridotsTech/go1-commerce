quick_entry_return = function(cur_frm){
	quick_entry("Return Policy", 
	function(){}, 
	{});
}

quick_entry_attribute = function(cur_frm){
	quick_entry("Specification Attribute", 
	function(){}, 
	{});
}

quick_entry_variant = function(){
	quick_entry("Product Attribute", 
	function(){}, 
	{});
}

quick_entry = function(doctype, success, fields_map={}) {
	frappe.model.with_doctype(doctype, function() {
		var mandatory = [];

		if (!fields_map == {}) {
			$.each(fields_map, function(k,v) {
				doc_field = frappe.meta.get_docfield(doctype, k)
				mandatory.push(doc_field);
			});
		} else {
			mandatory = $.map(frappe.get_meta(doctype).fields,
			function(d) { return (d.reqd || d.bold && !d.read_only) ? d : null });
		}

		var meta = frappe.get_meta(doctype);
		var doc = frappe.model.get_new_doc(doctype, null, null, true);

		var title = __("New {0}", [doctype])
		
		if(doctype=="Product Attribute"){
			title = __("New Variant")
		}
		var dialog = new frappe.ui.Dialog({
			title: title,
			fields: mandatory,
		});

		var update_doc = function() {
			var data = dialog.get_values(true);
			$.each(data, function(key, value) {
				if(key==='__name') {
					dialog.doc.name = value;
				} else {
					if(!is_null(value)) {
						dialog.doc[key] = value;
					}
				}
			});
			return dialog.doc;
		}

		var open_doc = function() {
			dialog.hide();
			update_doc();
			frappe.set_route('Form', doctype, doc.name);
		}

		dialog.doc = doc;

		dialog.refresh();

		dialog.set_primary_action(__('Save'), function() {
			if(dialog.working) return;
			var data = dialog.get_values();

			if(data) {
				dialog.working = true;
				values = update_doc();
				
			
				frappe.call({
					method: "frappe.client.insert",
					args: {
						doc: values
					},
					callback: function(r) {
						dialog.hide();
						frappe.model.clear_doc(dialog.doc.doctype, dialog.doc.name);
						var doc = r.message;
						if(success) {
							success(doc);
						}
						frappe.ui.form.update_calling_link(doc.name);
						if(dialog.doc.doctype=="Specification Attribute" || dialog.doc.doctype=="Product Attribute"){
							cur_frm.events.build_multi_selector(cur_frm, cur_frm.possible_val);
						}
						if(dialog.doc.doctype=="Return Policy"){
							cur_frm.events.multiselect_items(cur_frm, cur_frm.possible_val);
						}
					},
					error: function() {
						open_doc();
					},
					always: function() {
						dialog.working = false;
					},
					freeze: true
				});
			}
			
			
		});

		dialog.wrapper.keydown(function(e) {
			if((e.ctrlKey || e.metaKey) && e.which==13) {
				if(!frappe.request.ajax_count) {
					dialog.get_primary_btn().trigger("click");
				}
			}
		});

		dialog.show();

		if (fields_map != {}) {
			console.log(dialog.fields_dict)
			$.each(dialog.fields_dict, function(fieldname, field) {
				console.log(field)
				console.log(fieldname)
				field.set_input(fields_map[fieldname]);
			});
		} else {
			$.each(dialog.fields_dict, function(fieldname, field) {
				console.log(field)
				field.doctype = doc.doctype;
				field.docname = doc.name;
				if(!is_null(doc[fieldname])) {
					field.set_input(doc[fieldname]);
				}
			});
		}
	});
}