// Copyright (c) 2018, info@valiantsystems.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Method', {
	refresh: function(frm) {
		frm.trigger('display_text');
        frm.trigger('requirements')
	},
	payment_method: function(frm){
		if(frm.doc.payment_method){
			frm.set_value('display_name', frm.doc.payment_method)
		}
	},
	display_text: function(frm){
		let wrapper = $(frm.get_field('display_text').wrapper).empty();
		$(`<p>${__('Display text of each payment type based on shipping method.')}</p>`).appendTo(wrapper);
		let button = $(`<button class="btn btn-primary">Add Text</button>`).appendTo(wrapper);
		let table = $(`
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>${__('Shipping Method')}</th>
                        <th>${__('Payment Method Text')}</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>`).appendTo(wrapper);
		let values = frm.doc.display_text;
		let display_text = [];
		if(values && values != ''){
			display_text = JSON.parse(frm.doc.display_text);
			if(display_text.length > 0){
				display_text.map(f=>{
					let row = $(`<tr data-id="${f.idx}">
						<td>${__(f.shipping_method_name)}</td>
						<td>${f.display_text}</td>
						<td><button class="btn btn-xs btn-danger">Delete</button></td>
					</tr>`);
					table.find('tbody').append(row);
				})
			} 
            else{
				table.find('tbody').append(`<tr><td colspan="3">${__("No records found")}</td></tr>`);
			}				
		} else{
			table.find('tbody').append(`<tr><td colspan="3">${__("No records found")}</td></tr>`);
		}
		button.on('click', () => {
			let dialog = new frappe.ui.Dialog({
				title: __("Payment Method Text"),
				fields:[
					{
						"fieldname": "shipping_method",
						"label": __("Shipping Method"),
						"fieldtype": "Link",
						"options": "Shipping Method",
						"reqd": 1,
						onchange: function(){
							let val = this.get_value();
							if(val){
								frappe.call({
	                                method: 'frappe.client.get_value',
	                                args: {
	                                    'doctype': "Shipping Method",
	                                    'filters': { 'name': val },
	                                    'fieldname': ["shipping_method_name"]
	                                },
	                                callback: function(r) {
	                                    if (r.message) {
	                                        dialog.set_value('shipping_method_name', r.message.shipping_method_name)
	                                    }
	                                }
	                            })
							}
						}
					},
					{
						"fieldname": "shipping_method_name",
						"label": __("Shipping Method Name"),
						"fieldtype": "Data",
						"read_only": 1
					},
					{
						"fieldname": "display_text",
						"label": __("Display Text"),
						"fieldtype": "Data",
						"reqd": 1
					}
				]
			});
			dialog.set_primary_action(__('Save'), function() {
	            let data = dialog.get_values();
	            data.idx = (display_text.length + 1);
	            display_text.push(data)
	            dialog.hide();
	            frm.set_value('display_text', JSON.stringify(display_text));
	            if(!frm.doc.__islocal)
	            	frm.save();
	        });
	        dialog.show();
		});
		$(wrapper).find('.btn-danger').click(function(){
			let idx = $(this).parent().parent().attr('data-id');
			let obj = display_text.filter(obj => obj.idx != idx);
			cur_frm.set_value('display_text', JSON.stringify(obj));
		})
	},
	requirements: function(frm) {
        let options = 'Spend x amount\nSpecific price range\nHas any one product in cart\nHas all these products in cart\nLimit to role\nSpecific Shipping Method';
        frappe.meta.get_docfield('Payment Method Requirement', 'requirement_type', cur_frm.doc.name).options = options;
        frm.trigger('requirement_html');
    },
	 requirement_html: function(frm) {
        let wrapper = $(frm.get_field("requirements_html").wrapper).empty();
        $(`<div class="req-list"></div>
            <table class="table table-bordered">
            <thead>
                <tr>
                    <th>${__("Requirement Type")}</th>
                    <th></th>
                    <th></th>
                </tr>
            </thead>
            <tbody></tbody>
            </table>`).appendTo(wrapper);
        if (frm.doc.payment_method_requirements && frm.doc.payment_method_requirements.length > 0) {
            frm.doc.payment_method_requirements.map(f => {
                let dt = get_doctype_for_requirement(f.requirement_type);
                let dt_txt = dt;
                if (dt != 'Business') {
                    dt = dt + 's'
                }
                let col2 = '';
                if (f.requirement_type == 'Spend x amount') {
                    col2 = '<div class="amount"></div>';
                }
                //updated by sivaranjani
                else if (f.requirement_type == 'Specific price range') {
                    col2 = '<div class="rangeamount"></div>';
                }
                //end
                else {
                    let li = [];
                    if (f.items_list)
                        li = JSON.parse(f.items_list);
                    if (li.length > 1)
                        dt_txt = `${dt_txt}s`
                    col2 = `<div>${li.length} ${__(dt_txt)} added<button style="float: right;" class="btn btn-xs btn-default">Choose ${__(dt)}</button></div>`;
                }
                let row = $(`<tr>
                    <td style="width: 50%;">${__(f.requirement_type)}</td>
                    <td style="width: 43%;">${col2}</td>
                    <td style="text-align: center;"><button class="btn btn-danger btn-xs"><span class="fa fa-trash"></span></button></td>
                </tr>`);
                let allow = true;
                if (allow)
                    wrapper.find('tbody').append(row);
                else {
                    if (frm.doc.payment_method_requirements.length == 1) {
                        wrapper.find('tbody').append(`<tr><td colspan="3">No Records Found!</td></tr>`)
                    }
                }
                row.find('.btn-danger').click(function() {
                    let lists = frm.doc["payment_method_requirements"].filter(obj => obj.name != f.name);
                    frm.doc.payment_method_requirements = lists;
                    if (!f.__islocal)
                        frm.save();
                    else
                        frm.trigger("requirement_html")
                });
                if (f.requirement_type == 'Spend x amount') {
                    let input = frappe.ui.form.make_control({
                        df: {
                            "fieldtype": "Currency",
                            "label": __("Amount To Be Spent"),
                            "fieldname": "requirement_type",
                            "placeholder": __("Amount To Be Spent"),
                            "reqd": 1
                        },
                        parent: row.find('.amount'),
                        only_input: true,
                    });
                    input.make_input();
                    if (f.amount_to_be_spent)
                        input.set_value(f.amount_to_be_spent)
                    input.$input.on('change', function() {
                        let val = input.$input.val();
                        if (val) {
                            frappe.model.set_value(f.doctype, f.name, 'amount_to_be_spent', val);
                            frm.trigger('requirement_html');
                        }
                    });
                }
                //updated by sivaranjnai
                else if (f.requirement_type == 'Specific price range') {
                    let input_min = frappe.ui.form.make_control({
                        df: {
                            "fieldtype": "Currency",
                            "label": __("Minimum Amount To Be Spent"),
                            "fieldname": "min_requirement_type",
                            "placeholder": __("Minimum Amount To Be Spent"),
                            "reqd": 1
                        },
                        parent: row.find('.rangeamount'),
                        only_input: true,
                    });
                    let input_max = frappe.ui.form.make_control({
                        df: {
                            "fieldtype": "Currency",
                            "label": __("Maximum Amount To Be Spent"),
                            "fieldname": "max_requirement_type",
                            "placeholder": __("Maximum Amount To Be Spent"),
                            "reqd": 1
                        },
                        parent: row.find('.rangeamount'),
                        only_input: true,
                    });
                    input_min.make_input();
                    input_max.make_input();
                    if (f.min_amount)
                        input_min.set_value(f.min_amount)
                    input_min.$input.on('change', function() {
                        let val = input_min.$input.val();
                        if (val) {
                            frappe.model.set_value(f.doctype, f.name, 'min_amount', val);
                            frm.trigger('requirement_html');
                        }
                    });
                    if (f.max_amount) {
                        input_max.set_value(f.max_amount)
                    }
                    input_max.$input.on('change', function() {
                        let val = input_max.$input.val();
                        if (val) {
                            frappe.model.set_value(f.doctype, f.name, 'max_amount', val);
                            frm.trigger('requirement_html');
                        }
                    });
                }
                //end
                else {
                    row.find('.btn-default').click(function() {
                        let req_dialog = new assign_items({
                            doctype: get_doctype_for_requirement(f.requirement_type),
                            items_list: f.items_list || '',
                            cdt: f.doctype,
                            cdn: f.name
                        });
                    })
                }
            })
        } else {
            wrapper.find('tbody').append(`<tr><td colspan="3">No Records Found!</td></tr>`)
        }
        let limit = true;
        let check_role = true;
        if (frm.doc.discount_type == 'Assigned to Sub Total')
            limit = false;
        if(frm.doc.discount_type == 'Assigned to Delivery Charges')
            check_role = true;
        let req_list = get_requirements(limit, check_role);
        req_list.map(f => {
            let cls = 'btn-info';
            if (frm.doc["payment_method_requirements"].length > 0) {
                if (frm.doc["payment_method_requirements"].find(obj => obj.requirement_type == f)) {
                    cls = 'btn-success'
                }
            }
            let btn = $(`<button style="margin-right: 5px;margin-bottom: 5px;" class="btn btn-xs ${cls}">${__(f)}</button>`);
            wrapper.find('.req-list').append(btn);
            btn.click(function() {
                if (btn.attr('class').indexOf('btn-info') != -1) {
                    btn.addClass('btn-success').removeClass('btn-info');
                    if (!frm.doc["payment_method_requirements"].find(obj => obj.requirement_type == f)) {
                        var child = frappe.model.add_child(frm.doc, 'Payment Method Requirement', 'payment_method_requirements', frm.doc.payment_method_requirements.length + 1);
                        child.requirement_type = f;
                        frm.trigger('requirement_html');
                    }
                }
            })
        })
    },
});

var get_doctype_for_requirement = function(req) {
    let title = '';
    switch (req) {
        case "Limit to business":
            title = 'Business';
            break;
        case "Limit to role":
            title = 'Role';
            break;
        case "Specific Shipping Method":
            title = 'Shipping Method';
            break;
        default:
            title = 'Product';
            break;
    }
    return title;
}
var get_requirements = function(limit, check_role) {
    let requirements = [];
    let allow = false;
    if (limit) {
        requirements.push('Spend x amount');
        if(check_role){
            requirements.push('Limit to role');
        }
        requirements.push('Specific Shipping Method');
        requirements.push('Specific price range');
        requirements.push('Has any one product in cart');
        requirements.push('Has all these products in cart');
    } 
    else {
        requirements.push('Spend x amount');
        requirements.push('Specific price range');
        requirements.push('Has any one product in cart');
        requirements.push('Has all these products in cart');
        
        if (has_common(frappe.user_roles, ['Admin', 'System Manager'])){
            requirements.push('Limit to role');
        }
        requirements.push('Specific Shipping Method');
    }
    return requirements;
}
var assign_items = Class.extend({
    init: function(opts) {
        this.dt = opts.doctype;
        let items_list = opts.items_list;
        if (items_list)
            this.items_list = JSON.parse(items_list);
        else
            this.items_list = [];
        this.cdt = opts.cdt;
        this.cdn = opts.cdn;

        this.make();
    },
    make: function() {
        let me = this;
        this.dialog = new frappe.ui.Dialog({
            title: this.get_title(),
            fields: this.get_fields()
        });
        this.dialog.set_primary_action(__('Save'), function() {
            if (me.items_list.length > 0) {
                if (me.cdt && me.cdn) {
                    frappe.model.set_value(me.cdt, me.cdn, 'items_list', JSON.stringify(me.items_list));
                    if (!cur_frm.doc.__islocal)
                        cur_frm.save();
                }
                me.dialog.hide();
            }
        });
        this.dialog.$wrapper.find('button[data-fieldname="add_item"]').addClass('btn-primary');
        this.dialog.$wrapper.find('button[data-fieldname="add_item"]').addClass('btn-sm');
        this.dialog.show();

        this.save_action();
        this.items_html();
    },
    get_title: function() {
        let title = 'Select ';
        switch (this.dt) {
            case 'Product':
                title = title + 'Products'
                break;
            case 'Shipping Method':
                title = title + 'Shipping Methods';
                break;
            case 'Business':
                title = title + 'Business';
                break;
            case 'Payment Method':
                title = title + 'Payment Methods';
                break;
            default:
                title = 'Select Items'
        }
        return __(title);
    },
    get_fields: function() {
        let me = this;
        let fields = [];
        fields.push({ "fieldtype": "HTML", "fieldname": "item_html" });
        fields.push({ "fieldtype": "Button", "fieldname": "add_item", "label": __("Add Item") });
        return fields;
    },
    save_action: function() {
        let me = this;
        this.dialog.fields_dict.add_item.onclick = function() {
            let values = {};
            let wrapper = me.dialog.fields_dict.item_html.$wrapper;
            let new_row = $(`<tr>
                    <td><div class="slide-input"></div></td>                    
                    <td></td>
                </tr>`);
            let input = frappe.ui.form.make_control({
                df: {
                    "fieldtype": "Link",
                    "label": __(me.dt),
                    "fieldname": "item",
                    "placeholder": __(`Select ${me.dt}`),
                    "options": me.dt,
                    "onchange": function() {
                        let val = this.get_value();
                        if (val) {
                            let check = me.items_list.find(obj => obj.item == val);
                            if (check) {
                                input.set_value("");
                                frappe.throw(`This ${__(me.dt)} is already selected. Please pick any other ${__(me.dt)}`);
                            }
                            let field = 'item';
                            if (me.dt == 'Business')
                                field = 'restaurant_name';
                            if (me.dt == 'Role')
                                field = 'role_name';
                            if (me.dt == 'Shipping Method')
                                field = 'shipping_method_name';
                            if (me.dt == 'Payment Method')
                                field = 'payment_method';
                            frappe.call({
                                method: 'frappe.client.get_value',
                                args: {
                                    'doctype': me.dt,
                                    'filters': { 'name': val },
                                    'fieldname': [field]
                                },
                                callback: function(r) {
                                    if (r.message) {
                                        let arr = {};
                                        arr["item"] = val;
                                        arr["item_name"] = r.message[field];
                                        arr['idx'] = idx;
                                        me.items_list.push(arr);
                                        me.items_html();
                                    }
                                }
                            })
                        }
                    }
                },
                "get_query": function() {
                    if (me.dt == 'Product')
                        return "go1_commerce.go1_commerce.doctype.discounts.discounts.get_products"
                },
                parent: new_row.find('.slide-input'),
                only_input: true,
            });
            wrapper.find('tr[data-type="noitems"]').remove();
            wrapper.find('tbody').append(new_row);
            let idx = me.items_list.length + 1;
            input.make_input();
        }
    },
    items_html: function() {
        let me = this;
        let wrapper = this.dialog.fields_dict.item_html.$wrapper.empty();
        let table = $(`<table class="table table-bordered">
                <thead>
                    <tr>
                        <th>${__(me.dt)}</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>`).appendTo(wrapper);
        if (this.items_list && this.items_list.length > 0) {
            this.items_list.map(f => {
                let item = f.item_name;
                let row = $(`<tr>
                        <td>${__(item)}</td>
                        <td style="width: 10%;"><button class="btn btn-danger btn-xs"><span class="fa fa-times"></span></button></td>
                    </tr>`);
                table.find('tbody').append(row);
                row.find('.btn-danger').click(function() {
                    let obj = me.items_list.filter(o => o.idx != f.idx);
                    $(obj).each(function(k, v) {
                        v.idx = (k + 1);
                    })
                    me.items_list = obj;
                    me.items_html();
                });
            })
        } else {
            table.find('tbody').append(`<tr data-type="noitems"><td colspan="2">Records Not Found!</td></tr>`);
        }
    }
});

