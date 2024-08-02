// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

frappe.ui.form.LinkSelector.prototype.search = function() {
	var args = {
			txt: this.dialog.fields_dict.txt.get_value(),
			searchfield: "name",
			start: this.start,
			filters:{"is_template":1}
		};
		var me = this;

		if (this.target.set_custom_query) {
			this.target.set_custom_query(args);
		}

		// load custom query from grid
		if (
			this.target.is_grid &&
			this.target.fieldinfo[this.fieldname] &&
			this.target.fieldinfo[this.fieldname].get_query
		) {
			$.extend(args, this.target.fieldinfo[this.fieldname].get_query(cur_frm.doc));
		}

		frappe.link_search(
			this.doctype,
			args,
			function (r) {
				var parent = me.dialog.fields_dict.results.$wrapper;
				if (args.start === 0) {
					parent.empty();
				}
				
				if (r.values.length) {
					$.each(r.values, function (i, v) {
						
						let added_items = -1
						if(cur_frm.doc.items){
							added_items  = cur_frm.doc.items.findIndex((obj => obj.product == v[0]));
						}else{
							added_items = -1
						}
						// console.log(cur_frm.doc.items.indexOf(v[0]))
				       
				        let added = "checkmark"
				        if(added_items<0){
				        	added = ""
				        } 
				        
						var row = $(
							repl(
								'<div class="row link-select-row">\
						<div class="col-xs-4">\
							<b><a href="#">%(name)s</a></b></div>\
						<div class="col-xs-6">\
							<span class="text-muted">%(values)s</span>\
						</div>\
						<div class="col-xs-2">\
							<span class="%(added)s"></span></div>\
						</div><style>.checkmark { display: inline-block; transform: rotate(45deg);  height: 18px; width: 10px; margin-left: 60%;  border-bottom: 3px solid #78b13f; border-right: 3px solid #78b13f; }</style>',
								{
									name: v[0],
									values: v.splice(1).join(", "),
									added: added
								}
							)
						).appendTo(parent);

						row.find("a")
							.attr("data-value", v[0])
							.click(function () {
								var value = $(this).attr("data-value");
								if (me.target.is_grid) {
									// set in grid
									// call search after value is set to get latest filtered results
									me.set_in_grid(value).then(() => me.search());
								} else {
									if (me.target.doctype)
										me.target.parse_validate_and_set_in_model(value);
									else {
										me.target.set_input(value);
										me.target.$input.trigger("change");
									}
									me.dialog.hide();
								}
								return false;
							});
					});
				} else {
					$(
						'<p><br><span class="text-muted">' +
							__("No Results") +
							"</span>" +
							(frappe.model.can_create(me.doctype)
								? '<br><br><a class="new-doc btn btn-default btn-sm">' +
								  __("Create a new {0}", [__(me.doctype)]) +
								  "</a>"
								: "") +
							"</p>"
					)
						.appendTo(parent)
						.find(".new-doc")
						.click(function () {
							frappe.new_doc(me.doctype);
						});
				}

				if (r.values.length < 20) {
					var more_btn = me.dialog.fields_dict.more.$wrapper;
					more_btn.hide();
				}
			},
			this.dialog.get_primary_btn()
		);
}
frappe.ui.form.LinkSelector.prototype.set_in_grid = function(value) {
	return new Promise((resolve) => {
			if (this.qty_fieldname) {
				frappe.prompt(
					{
						fieldname: "qty",
						fieldtype: "Float",
						label: "Qty",
						default: 1,
						reqd: 1,
					},
					(data) => {
						let updated = (this.target.frm.doc[this.target.df.fieldname] || []).some(
							(d) => {
								if (d[this.fieldname] === value) {
									frappe.model
										.set_value(d.doctype, d.name, this.qty_fieldname, data.qty)
										.then(() => {
											frappe.show_alert(
												__("Added {0} ({1})", [
													value,
													d[this.qty_fieldname],
												])
											);
											resolve();
										});
									return true;
								}
							}
						);
						if (!updated) {
							let d = null;
							frappe.run_serially([
								() => (d = this.target.add_new_row()),
								() => frappe.timeout(0.1),
								() => {
									let args = {};
									args[this.fieldname] = value;
									args[this.qty_fieldname] = data.qty;
									return frappe.model.set_value(d.doctype, d.name, args);
								},
								() => frappe.show_alert(__("Added {0} ({1})", [value, data.qty])),
								() => resolve(),
							]);
						}
					},
					__("Set Quantity"),
					__("Set Quantity")
				);
			} else if (this.dynamic_link_field) {
				
				let d = this.target.add_new_row();
				
				frappe.model.set_value(
					d.doctype,
					d.name,
					this.dynamic_link_field,
					this.dynamic_link_reference
				);
				frappe.model.set_value(d.doctype, d.name, this.fieldname, value).then(() => {
					frappe.show_alert(__("{0} {1} added", [this.dynamic_link_reference, value]));
					resolve();
				});
			} else {

				let me = this;
				if(this.target.doctype="Product Mapping Tool Item"){
						frappe.call({
							method: "go1_commerce.go1_commerce.doctype.product_mapping_tool.product_mapping_tool.get_product_detail",
							type: "GET",
							args: {"product": value},
							callback: function (r) {
								
								var data = r.message;
								
								if(data.variant_combination.length>0){
									$.each(data.variant_combination, function (i, v) {
										
										$.each(cur_frm.doc.center, function (j, s) {
											let allEqual =[]
										if(cur_frm.doc.items){
											allEqual = cur_frm.doc.items.filter(val => val.product === value&&val.attribute_id===v.attribute_id && val.center===s.center);
											
										}
											if(allEqual.length<=0){
												let d = me.target.add_new_row();
											    frappe.model.set_value(d.doctype,d.name,"product_name",data.item);
						                        frappe.model.set_value(d.doctype,d.name,"mrp",0);
						                        frappe.model.set_value(d.doctype,d.name,"price",0);
						                        frappe.model.set_value(d.doctype,d.name,"attribute_id",v.attribute_id);
						                        frappe.model.set_value(d.doctype,d.name,"attribute_description",v.combination_text);
						                        frappe.model.set_value(d.doctype,d.name,"center",s.center);
						                        frappe.model.get_value('Warehouse', {'name': s.center}, "warehouse_name",function(e) {
							                         frappe.model.set_value(d.doctype,d.name,"center_name",e.warehouse_name);
							                    })
						                    	frappe.model.set_value(d.doctype, d.name, me.fieldname, value).then(() => {
												frappe.show_alert(__("{0}({1}) - {2} added", [value, v.attribute_html, s.center]));
													resolve();
												});
						                    }else{
						                    	frappe.show_alert(__("{0}({1}) - {2} already added!", [value, v.attribute_html, s.center]));
													
						                    }
					                    })
										
									})
								}else{
									
									$.each(cur_frm.doc.center, function (j, s) {
										
										let allEqual =[]
										if(cur_frm.doc.items){
											allEqual = cur_frm.doc.items.filter(val => val.product === value && val.center===s.center);
											
										}
										
										if(allEqual.length<=0){
											let d = me.target.add_new_row();
											
					                        frappe.model.set_value(d.doctype,d.name,"product_name",data.item);
					                        frappe.model.set_value(d.doctype,d.name,"mrp",0);
					                        frappe.model.set_value(d.doctype,d.name,"price",0);
					                        frappe.model.set_value(d.doctype,d.name,"center",s.center);
										    frappe.model.get_value('Warehouse', {'name': s.center}, "warehouse_name",function(e) {
						                         frappe.model.set_value(d.doctype,d.name,"center_name",e.warehouse_name);
						                    })
											frappe.model.set_value(d.doctype, d.name, me.fieldname, value).then(() => {
												frappe.show_alert(__("{0} - {1} added", [value, s.center]));
												resolve();
											});
										}else{
						                    	frappe.show_alert(__("{0} - {1} already added!", [value, s.center]));
													
						                    }
									})
								}
							}
						});

					}
					else{
					let d = this.target.add_new_row();
				
					frappe.model.set_value(d.doctype, d.name, this.fieldname, value).then(() => {
						frappe.show_alert(__("{0} added", [value]));
						resolve();
					});
				}
			}
		});
}
