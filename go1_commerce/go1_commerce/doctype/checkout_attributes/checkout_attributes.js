// Copyright (c) 2020, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Checkout Attributes', {
	refresh: function(frm) {
		if (has_common(frappe.user_roles, ['Admin', 'System Manager'])) {
            frm.toggle_display(['business'], true);
            if(frm.doc.__islocal)
                frm.set_value('business', '');
        } else {
            frm.toggle_display(['business'], false);
            if(frm.doc.__islocal)
                frm.set_value('business', frappe.boot.user.defaults.business);
        }
        frm.set_query("parent_attribute", function () {
            let filters = {};
            filters.is_group = 1;
            if(frm.doc.business)
                filters.business = frm.doc.business
            return {
                "filters": filters
            }
        });
        frm.trigger('parent_attribute');
        console.log(frm.doc.attribute_options)
        if(frm.doc.attribute_options)
        {
            var options_list = [];
        for (var i = 0; i < frm.doc.attribute_options.length; i++) {
            options_list.push(frm.doc.attribute_options[i].option_value)
        }
        frappe.meta.get_docfield('Checkout Attribute Charges', 'option', frm.doc.name).options = options_list;
        }
	frm.trigger('requirements')
    },
    parent_attribute: function(frm){
        if(frm.doc.parent_attribute){
            frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.checkout_attributes.checkout_attributes.get_options',
                args: {
                    attribute: frm.doc.parent_attribute
                },
                callback: function(r){
                    if(r.message){
                        frm.set_df_property('parent_attribute_option', 'options', r.message);
                    }
                }
            });
        }
    },
    requirements: function(frm) {
        let options = ''
        options = 'Spend x amount\nSpecific price range\nLimit to role\nSpecific Shipping Method\nSpecific Payment Method';
        frappe.meta.get_docfield('Checkout Attribute Requirement', 'requirement_type', cur_frm.doc.name).options = options;
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
        if (frm.doc.checkout_attribute_requirements && frm.doc.checkout_attribute_requirements.length > 0) {
            frm.doc.checkout_attribute_requirements.map(f => {
                let dt = get_doctype_for_requirement(f.requirement_type);
                let dt_txt = dt;
                not_business()
                if (dt != 'Business') {
                    dt = dt + 's'
                }
                let col2 = '';
                if (f.requirement_type == 'Spend x amount') {
                    col2 = '<div class="amount"></div>';
                }
                else if (f.requirement_type == 'Specific price range') {
                    col2 = '<div class="rangeamount"></div>';
                }
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
                    if (frm.doc.checkout_attribute_requirements.length == 1) {
                        wrapper.find('tbody').append(`<tr><td colspan="3">No Records Found!</td></tr>`)
                    }
                }
                row.find('.btn-danger').click(function() {
                    let lists = frm.doc["checkout_attribute_requirements"].filter(obj => obj.name != f.name);
                    frm.doc.checkout_attribute_requirements = lists;
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
        let req_list = get_requirements(limit, check_role);
        req_list.map(f => {
            let cls = 'btn-info';
            if (frm.doc["checkout_attribute_requirements"].length > 0) {
                if (frm.doc["checkout_attribute_requirements"].find(obj => obj.requirement_type == f)) {
                    cls = 'btn-success'
                }
            }
            let btn = $(`<button style="margin-right: 5px;margin-bottom: 5px;" class="btn btn-xs ${cls}">${__(f)}</button>`);
            wrapper.find('.req-list').append(btn);
            btn.click(function() {
                if (btn.attr('class').indexOf('btn-info') != -1) {
                    btn.addClass('btn-success').removeClass('btn-info');
                    if (!frm.doc["checkout_attribute_requirements"].find(obj => obj.requirement_type == f)) {
                        var child = frappe.model.add_child(frm.doc, 'Checkout Attribute Requirement', 'checkout_attribute_requirements', frm.doc.checkout_attribute_requirements.length + 1);
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
        case "Limit to role":
            title = 'Role';
            break;
        case "Specific Shipping Method":
            title = 'Shipping Method';
            break;
	case "Specific Payment Method":
            title = 'Payment Method';
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
	requirements.push('Specific price range');
        if(check_role)
            requirements.push('Limit to role');
        requirements.push('Specific Shipping Method');
	requirements.push('Specific Payment Method');
       
    } else {
        requirements.push('Spend x amount');
        requirements.push('Specific price range');
       
        if (has_common(frappe.user_roles, ['Admin', 'System Manager']))
            requirements.push('Limit to role');
        requirements.push('Specific Shipping Method');
	requirements.push('Specific Payment Method');
       
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

