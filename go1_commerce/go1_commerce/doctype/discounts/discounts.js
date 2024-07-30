// Copyright (c) 2018, info@valiantsystems.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Discounts', {
    setup: function(frm) {
        frm.trigger('help_text');
    },
    refresh: function(frm) {
        frm.set_value('requirement_id', '');
        frm.events.filter_link_fields_data(frm)
        frm.events.hide_recurring_order_sec(frm)
        frm.events.add_custom_buttons(frm)
        frm.events.add_classes_update_css(frm)
        frm.events.requires_coupon_code(frm)
        frm.events.check_for_cashback(frm)
        frm.events.price_or_product_discount(frm)
        frm.events.discount_history_html(frm) 
    },
    help_text: function(frm) {
        let wrapper = $(frm.get_field('help_text').wrapper).empty();
        $(`<table class="table table-bordered" style="background: #f9f9f9;">
                <tbody>
                    <tr>
                        <td>
                            <h4>${__("How Discount is applied?")}</h4>
                            <ol>                                        
                                <li>${__("Discount is applied based on 'Priority' field. Discount with highest priority will be selected first.")}</li>
                                <li>${__('If discounts are created with discount types "Assigned to Product", "Assigned to Categories", for each product any one of these discounts will be applied based on the priority. Not all the three will be applied.')}</li>
                                <li>${__('Discounts with discount type "Assigned to Sub Total" will be applied at the time of checkout. This discount will apply even if the product has already any of the other discounts applied.')}</li>
                            </ol>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <h4>${__("Note:")}</h4>
                            <ol>
                                <li>${__("If discount is applied to products, categories, and requirement is added, then this discount will be applied only at the time of checkout process only.")}</li>
                            </ol>
                        </td>
                    </tr>
                </tbody>
            </table>`).appendTo(wrapper)
    },
    filter_link_fields_data(frm){
        frm.set_query("items", "discount_products", function(doc, cdt, cdn) {
            return {
                'query': 'go1_commerce.go1_commerce.doctype.discounts.discounts.get_products'
            };
        });
        frm.set_query("free_product", function(doc) {
            let lists = frm.doc.discount_products.map(val => val.items)
            return {
                'query': 'go1_commerce.go1_commerce.doctype.discounts.discounts.get_free_item',
                'filters': {
                    'items': lists
                }
            }
        });
    },
    hide_recurring_order_sec(frm){
        frappe.call({
            method: `go1_commerce.go1_commerce.doctype.discounts.discounts.get_shopping_cart_settings`,
            args: {
            },
            callback: function(r) {
                if (r.message) {
                    if(r.message.enable_recurring_order == 0) {
                        frm.set_df_property('recurring_order_section', 'hidden', 1)
                    }
                }
            }
        })
    },
    add_custom_buttons(frm){
        frm.clear_custom_buttons();
        if (frappe.session.user == 'Administrator' && !frm.doc.__islocal) {
            frm.add_custom_button(__('Save as template'), function() {
                frappe.prompt([
                        { "fieldname": "template_name",
                        "fieldtype": "Data",
                        "Label": __("Section Title"), "reqd": 1 }
                    ],
                    function(value) {
                        frappe.call({
                            method: `go1_commerce.go1_commerce.doctype.discounts.discounts.save_as_template`,
                            args: {
                                discount: frm.doc.name,
                                title: value.template_name
                            },
                            callback: function(r) {
                                if (r.message) {
                                    frappe.msgprint(__('Template saved successfully!'))
                                }
                            }
                        })
                    }
                )
            })
        }
        if(!frm.doc.__islocal && frappe.get_module('Notification')) {
            frm.add_custom_button(__('Send Notification'), function() {
                   var dialog = new frappe.ui.Dialog({
                    title: __("Message"),
                    fields: [{ "fieldtype": "Small Text", "fieldname": "notification_message" }]
                });
                dialog.set_primary_action(__("Send"), function() {
                    if($('[data-fieldname="notification_message"]').text()!="")
                    {
                        send_notification(frm.doc.name1,$('[data-fieldname="notification_message"]').text());
                        dialog.hide();
                    }
                    else{
                        alert("Please enter message");
                    }
                })
                dialog.show();
            });
        }
        if (!frm.doc.__islocal) {
            frm.toggle_display(['section_break_1'], false);
            frappe.run_serially([
                () => {
                    frm.trigger('get_templates')
                },
                () => {
                    if (frm.templates_list && frm.templates_list.length > 0) {
                        frm.add_custom_button(__("Edit as wizard"), function() {
                            new DiscountWizard({
                                frm: frm.doc
                            })
                        });
                        frm.custom_buttons[__("Edit as wizard")].addClass('btn-primary')
                    }
                }
            ]);
        } 
        else {
            frm.trigger('choose_template');
        }
    },
    add_classes_update_css(frm){
        $('#discounts-info_tab').addClass("active")
        if(frm.doc.price_or_product_discount == 'Product' && frm.doc.discount_type=="Assigned to Sub Total"){
            frm.set_df_property('same_product', 'hidden', 1);
         }
        else{
            frm.set_df_property('same_product', 'hidden', 0);
        }
    },
    use_percentage: function(frm) {
        frm.trigger('validate_percentage')
    },
    requires_coupon_code: function(frm) {
        frm.set_df_property('coupon_code', 'reqd', 1 ? (frm.doc.requires_coupon_code == 1) : 0)
    },
    discount_type: function(frm) {
        frm.set_df_property('discount_products', 'reqd', 1 ? (frm.doc.discount_type == 'Assigned to Products') : 0);
        frm.set_df_property('discount_categories', 'reqd', 1 ? (frm.doc.discount_type == 'Assigned to Categories') : 0);
        if (!frm.cashback)
            frm.set_df_property('price_or_product_discount', 'hidden', 1 ? 
                    (frm.doc.discount_type != 'Assigned to Products' && frm.doc.discount_type != 'Assigned to Sub Total') : 0)
        if (frm.doc.discount_type != 'Assigned to Products') {
            if (!frm.cashback) {
                if(frm.doc.discount_type!="Assigned to Sub Total"){
                    if (frm.doc.price_or_product_discount != 'Price') {
                        frm.set_value('price_or_product_discount', 'Price')
                    }
                }else{
                    frm.set_df_property('price_or_product_discount', 'options', ['Price', 'Product']);
                }
            } else {
                frm.set_df_property('price_or_product_discount', 'options', ['Price', 'Cashback']);
            }
        } else {
            if (frm.cashback)
                frm.set_df_property('price_or_product_discount', 'options', ['Price', 'Product', 'Cashback']);
            else
                frm.set_df_property('price_or_product_discount', 'options', ['Price', 'Product']);
        }
        if (frm.doc.discount_type == 'Assigned to Sub Total' && frm.doc.percent_or_amount == 'Discount Amount') {
            frm.trigger('check_subtotal_requirement');
        }
        frm.trigger('requirements')
        if (frm.doc.discount_type == 'Assigned to Categories') {
            frm.trigger('check_child_categories');
        }
        if(frm.doc.price_or_product_discount == 'Product' && frm.doc.discount_type=="Assigned to Sub Total"){
            frm.set_df_property('same_product', 'hidden', 1);
             frm.set_value('same_product', 0);
         }else{
            frm.set_df_property('same_product', 'hidden', 0);
        }
        if (!(frm.doc.discount_type == 'Assigned to Sub Total' || frm.doc.discount_type == 'Assigned to Delivery Charges')) {
            frm.set_value('requires_coupon_code',  0);
        }
    },
    percent_or_amount: function(frm) {
        frm.set_df_property('discount_percentage', 'reqd', 1 ? 
            (frm.doc.percent_or_amount == 'Discount Percentage' && frm.doc.price_or_product_discount == 'Price') : 0)
        frm.set_df_property('discount_amount', 'reqd', 1 ? 
            (frm.doc.percent_or_amount == 'Discount Amount' && frm.doc.price_or_product_discount == 'Price') : 0)
        if (frm.doc.discount_type == 'Assigned to Sub Total' && frm.doc.percent_or_amount == 'Discount Amount') {
            frm.trigger('check_subtotal_requirement');
        }
    },
    price_or_product_discount: function(frm) {
        if (frm.doc.price_or_product_discount == 'Cashback') {
            frm.trigger('cashback_type');
            frm.set_value('percent_or_amount', 'Discount Percentage');
            frm.set_value('discount_percentage', 0);
        } 
        else {
            frm.trigger('percent_or_amount');
        }
        if(frm.doc.price_or_product_discount == 'Product' && frm.doc.discount_type=="Assigned to Sub Total"){
            frm.set_df_property('same_product', 'hidden', 1);
            frm.set_value('same_product', 0);
        }
        else{
            frm.set_df_property('same_product', 'hidden', 0);
        }
    },
    check_subtotal_requirement: function(frm) {
        let exists = true;
        let length = 0;
        if (frm.doc.discount_requirements && frm.doc.discount_requirements.length > 0) {
            let check_requirement = frm.doc.discount_requirements.find(obj => obj.discount_requirement == 'Spend x amount');
            if (!check_requirement)
                exists = false;
            length = frm.doc.discount_requirements.length;
        } else {
            exists = false;
        }
        if (!exists) {
            var row = frappe.model.add_child(frm.doc, 'Discount Requirements', 'discount_requirements', length + 1);
            row.amount_to_be_spent = 0;
            frm.trigger('requirement_html');
        }
    },
    check_child_categories: function(frm) {
        if (frm.doc.discount_categories) {
            let child_list = frm.doc.discount_categories.filter(obj => obj.is_child == 1);
            $(child_list).each(function(k, v) {
                $('div[data-name="' + v.name + '"]').addClass('hidden');
            })
        }
    },
    requirements: function(frm) {
        let options = '';
        if (!has_common([frm.doc.discount_type], ['Assigned to Sub Total', 'Assigned to Delivery Charges'])) {
            options = 'Specific Shipping Method\nSpecific Payment Method';
        } if(frm.doc.discount_type == 'Assigned to Delivery Charges') {
            options = 'Spend x amount\nSpend x weight\nLimit to role\nSpecific Shipping Method\nSpecific Payment Method';
        }
        if(frm.doc.discount_type == 'Assigned to Products' || frm.doc.discount_type == 'Assigned to Categories') {
            options = 'Limit to customer'
        } 
        else {
            options = `Spend x amount\nSpend x weight\nSpecific price range\nHas any one product in 
                        cart\nHas all these products in cart\nLimit to role\nSpecific Shipping Method\nSpecific Payment Method`;
        }
        frappe.meta.get_docfield('Discount Requirements', 'discount_requirement', cur_frm.doc.name).options = options;
        frm.trigger('requirement_html');
    },
    choose_template: function(frm) {
        frappe.run_serially([
            () => {
                frm.trigger('get_templates')
            },
            () => {
                if (frm.templates_list && frm.templates_list.length > 0)
                    frm.trigger('templates_html')
                else
                    frm.toggle_display(['section_break_1'], false);
            }
        ]);
    },
    get_templates: function(frm) {
        frappe.call({
            method: `go1_commerce.go1_commerce.doctype.discount_template.discount_template.get_all_templates`,
            args: {},
            async: false,
            callback: function(r) {
                frm.templates_list = r.message;
            }
        })
    },
    templates_html: function(frm) {
        var dialog = new frappe.ui.Dialog({
            title: __("Choose Discount Type"),
            fields: [{ "fieldtype": "HTML", "fieldname": "template_html" }]
        });
        let selected_doc;
        if (frm.templates_list && frm.templates_list.length > 0) {
            let wrapper = dialog.fields_dict.template_html.$wrapper.empty();
            $(`<div class="row" id="templateslist" style="margin: 0;"></div>
                <style>
                div[data-fieldname="template_html"] .section-title{
                    padding: 30% 2%; text-align: center; height: 205px;
                }
                div[data-fieldname="template_html"] .section-item.active{
                    border: 1px solid #0c9e0c; background: #efefef1f; color: #0c9e0c;
                }
                div[data-fieldname="template_html"] .section-img{
                    position: relative; height: 165px;
                }
                div[data-fieldname="template_html"] .section-img img{
                    position: absolute; top: 50%; left: 50%; max-height: 160px;
                    transform: translate(-50%, -50%); vertical-align: middle;
                }
                div[data-fieldname="template_html"] .section-item{
                    margin-bottom: 10px; border: 1px solid #ddd; background: #f3f3f3; cursor:pointer;
                }
                div[data-fieldname="template_html"] .section-item p{
                    text-align: center;
                }
                .pad-5{padding: 0 5px;}
                </style>`).appendTo(wrapper);
            frm.templates_list.map(f => {
                let template = `<div class="section-title">${f.name1}</div>`;
                if (f.image) {
                    template = `<div class="section-img"><img src="${f.image}" /></div><p>${f.name1}</p>`
                }
                let row = $(`<div class="col-md-4 col-sm-6 col-xs-6 pad-5"><div class="section-item">${template}</div></div>`);
                wrapper.find('.row').append(row);
                row.click(function() {
                    selected_doc = f;
                    $(wrapper).find('.section-item').removeClass('active');
                    $(row).find('.section-item').addClass('active');
                })
            })
        }
        dialog.$wrapper.find('.modal-dialog').css("width", "1000px");
        $.getScript("https://raw.github.com/rochal/jQuery-slimScroll/master/jquery.slimscroll.min.js", function() {
            dialog.$wrapper.find('#templateslist').slimScroll({
                height: 450
            });
        })
        dialog.set_primary_action(__("Choose Discount"), function() {
            if (selected_doc) {
                dialog.hide();
                new DiscountWizard({
                    template: selected_doc.name
                })
            } else {
                frappe.throw(__("Please pick any template"));
            }
        })
        dialog.show();
        let close_btn = dialog.get_close_btn();
        close_btn.text(__('Create Discount Manually'));
        close_btn.removeClass('btn-default').addClass('btn-info');
    },
    requirement_html: function(frm) {
        let wrapper = $(frm.get_field("discount_requirements_html").wrapper).empty();
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
        if (frm.doc.discount_requirements && frm.doc.discount_requirements.length > 0) {
            frm.doc.discount_requirements.map(f => {
                let dt = get_doctype_for_requirement(f.discount_requirement);
                let dt_txt = dt;
                if (dt != 'Business') {
                    dt = dt + 's'
                }
                let col2 = '';
                if (f.discount_requirement == 'Spend x amount') {
                    col2 = '<div class="amount"></div>';
                }
                else if (f.discount_requirement == 'Specific price range') {
                    col2 = '<div class="rangeamount"></div>';
                }
                else if (f.discount_requirement == 'Spend x weight') {
                    col2 = '<div class="weightbased"></div>';
                }
                else {
                    let li = [];
                    if (f.items_list)
                        li = JSON.parse(f.items_list);
                    if (li.length > 1)
                        dt_txt = `${dt_txt}s`
                    col2 = `<div>${li.length} ${__(dt_txt)} added
                                <button style="float: right;" class="btn btn-xs btn-default">
                                    Choose ${__(dt)}
                                </button>
                            </div>`;
                }
                let row = $(`<tr>
                    <td style="width: 50%;">${__(f.discount_requirement)}</td>
                    <td style="width: 43%;">${col2}</td>
                    <td style="text-align: center;">
                        <button class="btn btn-danger btn-xs">
                            <span class="fa fa-trash"></span>
                        </button>
                    </td>
                </tr>`);
                let allow = true;
               
                if (allow)
                    wrapper.find('tbody').append(row);
                else {
                    if (frm.doc.discount_requirements.length == 1) {
                        wrapper.find('tbody').append(`<tr><td colspan="3">No Records Found!</td></tr>`)
                    }
                }
                row.find('.btn-danger').click(function() {
                    let lists = frm.doc["discount_requirements"].filter(obj => obj.name != f.name);
                    frm.doc.discount_requirements = lists;
                    if (!f.__islocal)
                        frm.save();
                    else
                        frm.trigger("requirement_html")
                });
                if (f.discount_requirement == 'Spend x amount') {
                    let input = frappe.ui.form.make_control({
                        df: {
                            "fieldtype": "Currency",
                            "label": __("Amount To Be Spent"),
                            "fieldname": "discount_requirement",
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
                else if (f.discount_requirement == 'Specific price range') {
                    let input_min = frappe.ui.form.make_control({
                        df: {
                            "fieldtype": "Currency",
                            "label": __("Minimum Amount To Be Spent"),
                            "fieldname": "min_discount_requirement",
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
                            "fieldname": "max_discount_requirement",
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
                else if (f.discount_requirement == 'Spend x weight') {
                    let wgt_input = frappe.ui.form.make_control({
                        df: {
                            "fieldtype": "Currency",
                            "label": __("Weight For Discount"),
                            "fieldname": "weight_for_discount",
                            "placeholder": __("Weight For Discount"),
                            "reqd": 1
                        },
                        parent: row.find('.weightbased'),
                        only_input: true,
                    });
                    wgt_input.make_input();
                    if (f.weight_for_discount)
                        wgt_input.set_value(f.weight_for_discount)
                    wgt_input.$input.on('change', function() {
                        let val = wgt_input.$input.val();
                        if (val) {
                            frappe.model.set_value(f.doctype, f.name, 'weight_for_discount', val);
                            frm.trigger('requirement_html');
                        }
                    });
                }
                else {
                    row.find('.btn-default').click(function() {
                        let req_dialog = new assign_items({
                            doctype: get_doctype_for_requirement(f.discount_requirement),
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
        let req_list = get_requirements(limit, check_role,frm.doc.discount_type);
        req_list.map(f => {
            let cls = 'btn-info';
            if (cur_frm.doc["discount_requirements"] && frm.doc["discount_requirements"].length > 0) {
                if (frm.doc["discount_requirements"].find(obj => obj.discount_requirement == f)) {
                    cls = 'btn-success'
                }
            }
            let btn = $(`<button style="margin-right: 5px;margin-bottom: 5px;" class="btn btn-xs ${cls}">${__(f)}</button>`);
            wrapper.find('.req-list').append(btn);
            btn.click(function() {
                if (btn.attr('class').indexOf('btn-info') != -1) {
                    btn.addClass('btn-success').removeClass('btn-info');
                    if (!frm.doc["discount_requirements"].find(obj => obj.discount_requirement == f)) {
                        var child = frappe.model.add_child(frm.doc, 'Discount Requirements', 'discount_requirements', frm.doc.discount_requirements.length + 1);
                        child.discount_requirement = f;
                        frm.trigger('requirement_html');
                    }
                }
            })
        })
    },
    cashback_type: function(frm) {
        frm.set_df_property('cashback_percentage', 'reqd', 1 ? 
            (frm.doc.cashback_type == 'Discount Percentage' && frm.doc.price_or_product_discount == 'Cashback') : 0);
        frm.set_df_property('cashback_amount', 'reqd', 1 ? 
            (frm.doc.cashback_type == 'Discount Amount' && frm.doc.price_or_product_discount == 'Cashback') : 0);
    },
    check_for_cashback: function(frm) {
        frappe.xcall('go1_commerce.utils.setup.get_settings_from_domain', 
                { 'dt': 'Shopping Cart Settings'})
            .then(r => {
                if (r && r.enable_cashback == 1) {
                    frm.cashback = 1;
                } else {
                    frm.cashback = 0;
                }
                frm.trigger('discount_type');
            });
    },
    discount_history_html: function(frm) {
        let wrapper = $(frm.get_field("discount_history_html").wrapper).empty();
        let template = $(`<div></div>
            <style>
                div[data-fieldname="discount_history_html"] .accordion .title {
                    border: 1px solid #ddd;
                    padding: 10px;
                    font-size: 13px;
                    margin-bottom: 10px;
                    font-weight: 500;
                    cursor: pointer;
                }
                div[data-fieldname="discount_history_html"] .accordion .ics {
                    float: right;
                    padding: 3px;
                }
                div[data-fieldname="discount_history_html"] .accordion .expanded,
                div[data-fieldname="discount_history_html"] .accordion .result {
                    display: none;
                }
                div[data-fieldname="discount_history_html"] .accordion.active .expanded,
                div[data-fieldname="discount_history_html"] .accordion.active .result {
                    display: inherit;
                }
                div[data-fieldname="discount_history_html"] .accordion.active .collapsed {
                    display: none;
                }
                div[data-fieldname="discount_history_html"] .accordion.active .title {
                    margin-bottom: 0;background: #e4e4e4;
                }
                div[data-fieldname="discount_history_html"] .accordion .table {
                    margin: 0;
                }
                div[data-fieldname="discount_history_html"] .accordion .table tbody {
                    font-size: 12px;
                }
                div[data-fieldname="discount_history_html"] .accordion .result {
                    padding: 10px 10px;
                    border: 1px solid #ddd;
                    border-top: 0;
                    font-size: 13px;
                    margin-bottom: 10px;
                }
            </style>`).appendTo(wrapper)
        if(frm.doc.discount_history && frm.doc.discount_history.length > 0) {
            let slots = frm.doc.discount_history.map(val => val.date_range);
            let slot_items = Array.from(new Set(slots));
            slot_items.map(s => {
                let idx = slot_items.indexOf(s);
                let items = frm.doc.discount_history.filter(obj => obj.date_range == s);
                let slot_name = s;
                if(slot_name) {
                    let dates = slot_name.split(' -- ');
                    if(dates[0] != '') {
                        slot_name = 'From ' + frappe.datetime.str_to_user(dates[0]);
                    }
                    if(dates[1] != '') {
                        slot_name += ' To ' + frappe.datetime.str_to_user(dates[1])
                    }
                    if(slot_name == '') {
                        slot_name == 'Date Range Not Specified';
                    }
                } else {
                    slot_name = 'Date Range Not Specified';
                }
                let row = $(`<div class="accordion ${(idx == 0 && slot_items.length == 1) ? 'active' : ''}" data-id="${idx}">
                        <div class="title">
                            ${slot_name}
                            <span class="ics expanded fa fa-minus"></span>
                            <span class="ics collapsed fa fa-plus"></span>
                        </div>
                        <div class="result">
                            <table class="table table-bordered">
                                <thead>
                                    <tr>
                                        <th>${__("Posting Date")}</th>
                                        <th>${__("Order Id")}</th>
                                        <th>${__("Customer Id")}</th>
                                        <th>${__("Order Total")}</th>
                                    </tr>
                                </thead>
                                <tbody></tbody>
                            </table>
                        </div>
                    </div>`);                
                row.find('.title').click(function() {
                    if($(this).parent().attr('class') == 'accordion') {
                        $(this).parent().addClass('active');
                    } else {
                        $(this).parent().removeClass('active');
                    }
                });
                if(items && items.length > 0) {
                    items.map(it => {
                        row.find('tbody').append(`<tr>
                                <td>${frappe.datetime.str_to_user(it.creation.split(' ')[0])}</td>
                                <td>${it.order_id}</td>
                                <td>${it.customer}</td>
                                <td style="text-align: right;">${frappe.boot.sysdefaults.currency} ${it.order_total}</td>
                            </tr>`);
                    })
                } else {
                    row.find('tbody').append(`<tr><td colspan="3">${__("No Records Found!")}</td></tr>`);
                }
                template.append(row);
            });
        }
    }
});

frappe.ui.form.on("Discount Requirements", "form_render", function(frm, cdt, cdn) {
    var d = locals[cdt][cdn]
    if (cur_frm.selected_doc.discount_requirement != "Spend x amount" || 
            cur_frm.selected_doc.discount_requirement != "Specific price range" || 
            cur_frm.selected_doc.discount_requirement != "Spend x weight") {
        let wrapper = frm.fields_dict[d.parentfield].grid.grid_rows_by_docname[cdn].grid_form.fields_dict['assign_products_html'].wrapper
        let table_html = $(`<table class="table table-bordered" style="cursor:pointer; margin:0px;">
                <thead>
                    <tr>
                        <th style="width: 90%;">${__("Item")}</th>
                        <th style="width:10%;">Action</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>`).appendTo(wrapper);
        let items_list;
        if (d.items_list)
            items_list = JSON.parse(d.items_list);
        if (items_list && items_list.length > 0) {
            let dt = 'Product';
            if (d.discount_requirement == 'Specific Shipping Method')
                dt = 'Shipping Method';
            else if (d.discount_requirement == 'Specific Payment Method')
                dt = 'Payment Method';
            items_list.map(f => {
                let item = f.item_name;
                let row = $(`<tr>
                        <td>${__(item)}</td>
                        <td><button class="btn btn-danger btn-xs"><span class="fa fa-times"></span></button></td>
                    </tr>`);
                table_html.find('tbody').append(row);
                row.find('.btn-danger').click(function() {
                    let obj = items_list.filter(o => o.idx != f.idx);
                    $(obj).each(function(k, v) {
                        v.idx = (k + 1);
                    })
                    items_list = obj;
                    frappe.model.set_value(cdt, cdn, 'items_list', JSON.stringify(items_list));
                    row.remove();
                });
            })
        } else {
            table_html.find('tbody').append(`<tr><td colspan="2" align="center">No Records Found!</td></tr>`);
        }
    }
});

frappe.ui.form.on("Discount Requirements", {
    assign_items: function(frm, cdt, cdn) {
        var requirement = frappe.get_doc(cdt, cdn)
        new assign_items({
            doctype: get_doctype_for_requirement(requirement.discount_requirement),
            items_list: requirement.items_list,
            cdt: cdt,
            cdn: cdn
        });
    },
    discount_requirement: function(frm, cdt, cdn) {
        let items = locals[cdt][cdn];
        if (items.discount_requirement != 'Spend x amount' || items.discount_requirement != 'Specific price range'
            || items.discount_requirement != 'Spend x weight') {
            frappe.model.set_value(cdt, cdn, 'amount_to_be_spent', 0)
            frappe.model.set_value(cdt, cdn, 'min_amount', 0)
            frappe.model.set_value(cdt, cdn, 'max_amount', 0)
            frappe.model.set_value(cdt, cdn, 'weight_for_discount', 0)
            $('div[data-fieldname="assign_products_html"]').html("")
        }
    }
});

frappe.ui.form.on("Discount Products", {
    form_render: function(frm, cdt, cdn){
        let items = locals[cdt][cdn];
       if(items.items){
           frappe.xcall(`go1_commerce.go1_commerce.doctype.discounts.discounts.get_product_attribute`, { "product": items.items})
            .then(r => {
                let option_list = [];
             
                $.each(r, function(i, p){
                    $.each(p.options, function(j, q){
                        var idx = (j + 1);
                        var label = String(p.attribute)+"("+String(q.option_value)+")"
                         var name = String(q.attribute)+"-"+String(q.name)
                        option_list.push({"idx": idx, "name": name,"label":label, "product": q.parent})
                    });
                });
                 var possible_val = [{
                        "cls": "custom-productattr-name",
                        "tab_html_field": "product_attribute_html",
                        "tab_field": "product_attribute_json",
                        "link_name": "name",
                        "title": "Search product attribute here...",
                        "label": "Choose Product Attribute",
                        "doctype": "Discount Products",
                        "reference_doc": "Product",
                        "reference_fields": escape(JSON.stringify(["name", "item"])),
                        "search_fields": "item",
                        "reference_method": `go1_commerce.go1_commerce.doctype.discounts.discounts.get_product_attribute`,
                        "is_child": 0,
                        "description": "Please select the product attribute.",
                        "child_tab_link": "discount_products",
                        "height": "150px"
                    }];
                new MakeMultiSelectToggle({
                    cur_frm: cur_frm,
                    cdt: cdt,
                    cdn: cdn,
                    settings: possible_val,
                    list_array: option_list
                })
            });
       }
    }
})

frappe.ui.form.on("Discount Applied Product", {
    form_render: function(frm, cdt, cdn){
        let items = locals[cdt][cdn];
       if(items.product){
           frappe.xcall(`go1_commerce.go1_commerce.doctype.discounts.discounts.get_product_attribute`, { "product": items.product})
            .then(r => {
                let option_list = []
                $.each(r, function(i, p){
                    $.each(p.options, function(j, q){
                        var idx = (j + 1);
                        var label = String(p.attribute)+"("+String(q.option_value)+")"
                         var name = String(q.attribute)+"-"+String(q.name)
                        option_list.push({"idx": idx, "name": name,"label":label, "product": q.parent})
                    })
                })
                var possible_val = [{
                    "cls": "custom-product-name",
                    "tab_html_field": "product_attribute_html",
                    "tab_field": "product_attribute_json",
                    "link_name": "name",
                    "title": "Search product attribute here...",
                    "label": "Choose Product Attribute",
                    "doctype": "Discount Applied Product",
                    "reference_doc": "Product",
                    "reference_fields": escape(JSON.stringify(["name", "item"])),
                    "search_fields": "item",
                    "reference_method": `go1_commerce.go1_commerce.doctype.discounts.discounts.get_product_attribute`,
                    "is_child": 0,
                    "description": "Please select the product attribute.",
                    "child_tab_link": "discount_applied_product",
                    "height": "150px"
                }];
                new MakeMultiSelectToggle({
                    cur_frm: cur_frm,
                     cdt: cdt,
                    cdn: cdn,
                    settings: possible_val,
                    list_array: option_list
                })
            });
       }
    },
    product: function(frm, cdt, cdn) {
        let items = locals[cdt][cdn];
       if(items.product){
           items.product_attribute_json="[]"
           frappe.xcall(`go1_commerce.go1_commerce.doctype.discounts.discounts.get_product_attribute`, { "product": items.product})
            .then(r => {
                let option_list = []
                $.each(r, function(i, p){
                    $.each(p.options, function(j, q){
                         var idx = (j + 1);
                        var label = String(p.attribute)+"("+String(q.option_value)+")"
                         var name = String(q.attribute)+"-"+String(q.name)
                        option_list.push({"idx": idx, "name": name,"label":label, "product": q.parent})
                    })
                })
                var possible_val = [{
                    "cls": "custom-product-name",
                    "tab_html_field": "product_attribute_html",
                    "tab_field": "product_attribute_json",
                    "link_name": "name",
                    "title": "Search product attribute here...",
                    "label": "Choose Product Attribute",
                    "doctype": "Discount Applied Product",
                    "reference_doc": "Product",
                    "reference_fields": escape(JSON.stringify(["name", "item"])),
                    "search_fields": "item",
                    "reference_method": `go1_commerce.go1_commerce.doctype.discounts.discounts.get_product_attribute`,
                    "is_child": 0,
                    "description": "Please select the product attribute.",
                    "child_tab_link": "discount_applied_product",
                    "height": "240px"
                }];
                new MakeMultiSelectToggle({
                    cur_frm: cur_frm,
                     cdt: cdt,
                    cdn: cdn,
                    settings: possible_val,
                    list_array: option_list
                })
            });
       }
    },
    product_attribute: function(frm, cdt, cdn) {
        let items = locals[cdt][cdn];
    },
});

var get_doctype_for_requirement = function(req) {
    let title = '';
    switch (req) {
        
        case "Limit to customer":
            title = 'Customers';
            break;
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

var get_requirements = function(limit, check_role,discount_type) {
    let requirements = [];
    let allow = false;
    if(discount_type!="Assigned to Products" && discount_type!="Assigned to Categories" && discount_type!="Assigned to Business"){
        if (limit) {
            requirements.push('Limit to customer');
            requirements.push('Spend x amount');
            requirements.push('Spend x weight');
            requirements.push('Specific Shipping Method');
            requirements.push('Specific Payment Method');
        } else {
            requirements.push('Limit to customer');
            requirements.push('Spend x amount');
            requirements.push('Spend x weight');
            requirements.push('Specific price range');
            requirements.push('Has any one product in cart');
            requirements.push('Has all these products in cart');
            if (has_common(frappe.user_roles, ['Admin', 'System Manager'])){
                requirements.push('Limit to role');
            }
            requirements.push('Specific Shipping Method');
            requirements.push('Specific Payment Method');
        }
    }
    else{
        if(discount_type!="Assigned to Business"){
            requirements.push('Limit to customer');
        }
    }
    return requirements;
}

var assign_items = Class.extend({
    init: function(opts) {
        this.dt = opts.doctype;
        let items_list = opts.items_list;
        if (items_list){
            this.items_list = JSON.parse(items_list);
        }else{
            this.items_list = [];
        }
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
            case 'Payment Method':
                title = title + 'Payment Methods';
                break;
            case 'Customers':
                title = title + 'Customer';
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
                            if (me.dt == 'Role')
                                field = 'role_name';
                            if (me.dt == 'Shipping Method')
                                field = 'shipping_method_name';
                            if (me.dt == 'Payment Method')
                                field = 'payment_method';
                            if (me.dt == 'Customers')
                                field = 'full_name';
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

frappe.provide("frappe.ui");
var DiscountWizard = Class.extend({
    init: function(opts) {
        this.template = opts.template;
        this.frm = opts.frm;

        this.make();
    },
    make: function() {
        let me = this;
        frappe.run_serially([
            () => {
                if (me.template)
                    me.get_template_detail();
                else
                    me.template_detail = me.frm;
            },
            () => { me.make_slides() },
            () => { me.make_dialog() }
        ])
    },
    get_template_detail: function() {
        let me = this;
        frappe.call({
            method: `go1_commerce.go1_commerce.doctype.discount_template.discount_template.get_template_info`,
            args: {
                name: me.template
            },
            async: false,
            callback: function(r) {
                me.template_detail = r.message;
            }
        })
    },
    make_slides: function() {
        let slides = [];
        slides.push(this.get_basic_info());
        slides.push(this.get_validations());
        if (has_common([this.template_detail.discount_type], ['Assigned to Products', 'Assigned to Categories'])) {
            slides.push(this.get_items());
        }
        if (this.template_detail.discount_type == 'Assigned to Sub Total' && this.template_detail.requires_coupon_code) {
            slides.push(this.coupon_fields())
        }
        if (this.template_detail.discount_type == 'Assigned to Products' && this.template_detail.price_or_product_discount != 'Price') {
            slides.push(this.get_free_item());
        }
        slides.push(this.requirements());
        this.slides = slides;
    },
    make_dialog: function() {
        this.dialog = new frappe.ui.Dialog({
            title: __("Setup Discount"),
            fields: [{ 'fieldtype': 'HTML', 'fieldname': 'wizard_html' }]
        });
        this.dialog.show();
        this.dialog.$wrapper.find('.modal-dialog').css("width", "750px");
        this.dialog.$wrapper.find('.modal-dialog .row.form-section').css('padding', '0');
        this.dialog.$wrapper.find('.modal-dialog .modal-header').hide();
        this.dialog.$wrapper.find('.modal-dialog').css('margin', '15px auto');
        this.dialog.$wrapper.find('.modal-content').css('box-shadow', 'none');
        this.dialog.$wrapper.find('.modal-content').css('border', 'none');
        this.dialog.$wrapper.find('.modal-content').css('border-radius', '0px');
        this.setup_wizard();
    },
    get_basic_info: function() {
        let me = this;
        let field_name, label;
        if (this.template_detail.percent_or_amount == 'Discount Percentage') {
            field_name = 'discount_percentage';
            label = __("Discount Percentage");
        } else {
            field_name = 'discount_amount';
            label = __("Discount Amount");
        }
        let fields = [{
            "fieldname": "name1",
            "fieldtype": "Data",
            "reqd": 1,
            "label": __("Discount Title")
        }, {
            "fieldname": "priority",
            "fieldtype": "Int",
            "label": __("Priority"),
            "description": __("Higher the number, higher the priority. Discount with highest priority will be applied."),
            "default": 0
        }];
        if (this.template_detail.price_or_product_discount == 'Price')
            fields.push({
                "fieldname": field_name,
                "label": label,
                "fieldtype": "Float",
                "reqd": 1
            });
        if (this.template_detail.discount_type == 'Assigned to Sub Total' && this.template_detail.percent_or_amount == 'Discount Percentage') {
            fields.push({
                "fieldname": "max_discount_amount",
                "label": __("Maximum Discount Amount"),
                "fieldtype": "Currency",
                "reqd": 0
            });
        }
        let slide = {
            "name": "basic",
            "title": "Basic Information",
            "fields": fields,
            "onload": function(s) {
                me.slide_onload(fields, s, me);
            }
        }
        return slide;
    },
    slide_onload: function(fields, slide, me) {
        $(fields).each(function(k, v) {
            slide.get_input(v.fieldname).unbind("change").on("change", function() {
                let val = $(this).val() || "";
                me.wizard.values[v.fieldname] = val;
                if (v.fieldname == 'same_product') {
                    if ($(this).is(':checked')) {
                        slide.form.fields_dict.free_product.$wrapper.hide();
                    } else {
                        slide.form.fields_dict.free_product.$wrapper.show();
                    }
                }
                if (has_common([v.fieldname], ['start_date', 'end_date'])) {
                    me.wizard.values[v.fieldname] = get_formated_date(val);
                }
            });
        });
        if (!me.template) {
            setTimeout(function() {
                $(fields).each(function(k, v) {
                    if (me.wizard.values[v.fieldname]) {
                        slide.get_field(v.fieldname).set_input(me.wizard.values[v.fieldname])
                    }
                })
            }, 500);
        }
    },
    get_validations: function() {
        let me = this;
        let fields = [
            { "fieldname": "start_date", "fieldtype": "Date", "label": __("Valid From") },
            { "fieldname": "end_date", "fieldtype": "Date", "label": __("Valid Till") },
            { "fieldname": "min_qty", "fieldtype": "Int", "label": __("Minimum Quantity Required For Discount To Apply"), "default": 1 },
            { "fieldname": "max_qty", "fieldtype": "Int", "label": __("Maximum Quantity Required For Discount To Apply") }
        ];
        let slide = {
            "name": "validations",
            "title": __("Discount Validations"),
            "fields": fields,
            "onload": function(s) {
                me.slide_onload(fields, s, me);
            }
        }
        return slide;
    },
    get_items: function() {
        let me = this;
        let dt, fieldname, table_name, item_name;
        if (this.template_detail.discount_type == 'Assigned to Products') {
            dt = 'Product';
            fieldname = ['items', 'item_name'];
            table_name = 'discount_products';
            item_name = 'item';
        } else if (this.template_detail.discount_type == 'Assigned to Categories') {
            dt = 'Product Category';
            fieldname = ['category', 'category_name'];
            table_name = 'discount_categories';
            item_name = 'category_name';
        } 
        let fields = [
            { "fieldname": "items_html", "fieldtype": "HTML" },
            { "fieldname": "add_item", "fieldtype": "Button", "label": __("Add Row") }
        ]
        let slide = {
            "name": "assign_to",
            "title": "Assign Discount To",
            "fields": fields,
            "onload": function(s) {
                let slide_scope = this;
                setTimeout(function() {
                    slide_scope.bind_html(s);
                }, 1000);
                s.form.fields_dict.add_item.onclick = function() {
                    let wrapper = s.form.fields_dict.items_html.$wrapper;
                    let new_row = $(`<tr>
                            <td><div class="slide-input"></div></td>
                            <td></td>
                            <td></td>
                        </tr>`);
                    let link_field = frappe.ui.form.make_control({
                        df: {
                            "fieldtype": "Link",
                            "label": __(dt),
                            "fieldname": fieldname[0],
                            "placeholder": __(`Select ${dt}`),
                            "options": dt,
                            onchange: function() {
                                let val = this.get_value();
                                if (val) {
                                    let check = me.wizard.values[table_name].find(obj => obj[fieldname[0]] == val);
                                    if (check) {
                                        link_field.set_value("");
                                        frappe.throw(`This ${__(dt)} is already selected. Please pick any other ${__(dt)}`);
                                    }
                                    frappe.call({
                                        method: 'frappe.client.get_value',
                                        args: {
                                            'doctype': dt,
                                            'filters': { 'name': val },
                                            'fieldname': [item_name]
                                        },
                                        callback: function(r) {
                                            if (r.message) {
                                                new_row.find('td:eq(1)').text(r.message[item_name]);
                                                let arr = {};
                                                arr[fieldname[0]] = val;
                                                arr[fieldname[1]] = r.message[item_name];
                                                arr['idx'] = idx;
                                                me.wizard.values[table_name].push(arr)
                                                slide_scope.bind_html(s);
                                            }
                                        }
                                    })
                                }
                            }
                        },
                        parent: new_row.find('.slide-input'),
                        only_input: true,
                    });
                    let idx = me.wizard.values[table_name].length + 1;
                    link_field.make_input();
                    wrapper.find('tbody tr[data-type="noitem"]').remove();
                    wrapper.find('tbody').append(new_row);
                }
            },
            bind_html: function(s) {
                let wrapper = s.form.fields_dict.items_html.$wrapper.empty();
                $(`<table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>${__(dt)}</th>
                            <th>${__(dt)} Name</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                    </table>`).appendTo(wrapper);
                if (!me.wizard.values[table_name])
                    me.wizard.values[table_name] = [];
                if (me.wizard.values[table_name].length > 0) {
                    me.wizard.values[table_name].map(f => {
                        let row = $(`<tr>
                                <td style="width: 35%;">${__(f[fieldname[0]])}</td>
                                <td>${__(f[fieldname[1]])}</td>
                                <td><button class="btn btn-danger btn-xs"><span class="fa fa-trash"></span></button></td>
                            </tr>`);
                        wrapper.find('tbody').append(row);
                        row.find('.btn-danger').click(function() {
                            let lists = me.wizard.values[table_name].filter(obj => obj.idx != f.idx);
                            $(lists).each(function(k, v) {
                                v.idx = (k + 1);
                            })
                            me.wizard.values[table_name] = lists;
                            row.remove();
                            if (lists.length == 0) {
                                wrapper.find('tbody').append(`<tr data-type="noitem"><td colspan="3">${__("No Records Found!")}</td></tr>`);
                            }
                        })
                    })
                } else {
                    wrapper.find('tbody').append(`<tr data-type="noitem"><td colspan="3">${__("No Records Found!")}</td></tr>`);
                }
                s.form.fields_dict.add_item.$input.removeClass('btn-default').addClass('btn-warning');
                s.form.fields_dict.add_item.$input.removeClass('btn-xs').addClass('btn-sm');
            }
        }
        return slide;
    },
    requirements: function() {
        let me = this;
        let fields = [
            { "fieldname": "requirement_list", "fieldtype": "HTML" },
            { "fieldname": "requirement_html", "fieldtype": "HTML" }
        ]
        let slide = {
            "name": "requirements",
            "title": __("Discount Requirements"),
            "fields": fields,
            "onload": function(s) {
                let slide_scope = this;
                setTimeout(function() {
                    slide_scope.bind_html(s);
                    slide_scope.requirement_list(s)
                }, 1000);
            },
            bind_html: function(s) {
                let slide_scope = this;
                let wrapper = s.form.fields_dict.requirement_html.$wrapper.empty();
                $(`<table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>${__("Requirement Type")}</th>
                            <th></th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                    </table>`).appendTo(wrapper);
                if (!me.wizard.values["discount_requirements"])
                    me.wizard.values["discount_requirements"] = [];
                if (me.wizard.values["discount_requirements"] && me.wizard.values["discount_requirements"].length > 0) {
                    me.wizard.values["discount_requirements"].map(f => {
                        let col2 = '';
                        if (f.discount_requirement == 'Spend x amount') {
                            col2 = '<div class="amount"></div>';
                        } else if (f.discount_requirement == 'Specific price range') {
                            col2 = '<div class="rangeamount"></div>';
                        } else if (f.discount_requirement == 'Spend x weight') {
                            col2 = '<div class="weightbased"></div>';
                        } else {
                            col2 = `<button class="btn btn-xs btn-default">${__("Assign Items")}</button>`;
                        }
                        let row = $(`<tr>
                                <td style="width: 50%;">${__(f.discount_requirement)}</td>
                                <td style="width: 43%;">${col2}</td>
                                <td><button class="btn btn-danger btn-xs"><span class="fa fa-trash"></span></button></td>
                            </tr>`);
                        wrapper.find('tbody').append(row);
                        row.find('.btn-danger').click(function() {
                            let lists = me.wizard.values["discount_requirements"].filter(obj => obj.idx != f.idx);
                            $(lists).each(function(k, v) {
                                v.idx = (k + 1);
                            })
                            me.wizard.values["discount_requirements"] = lists;
                            row.remove();
                            if (lists.length == 0) {
                                wrapper.find('tbody').append(`<tr data-type="noitem"><td colspan="3">${__("No Records Found!")}</td></tr>`);
                            }
                            slide_scope.requirement_list(s)
                        });
                        if (f.discount_requirement == 'Spend x amount') {
                            let input = frappe.ui.form.make_control({
                                df: {
                                    "fieldtype": "Currency",
                                    "label": __("Amount To Be Spent"),
                                    "fieldname": "discount_requirement",
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
                                    $(me.wizard.values["discount_requirements"]).each(function(k, v) {
                                        if (v.idx == f.idx) {
                                            v.amount_to_be_spent = val;
                                        }
                                    });
                                }
                            });
                        }
                        else if (f.discount_requirement == 'Specific price range') {
                            let input_min = frappe.ui.form.make_control({
                                df: {
                                    "fieldtype": "Currency",
                                    "label": __("Minimum Amount To Be Spent"),
                                    "fieldname": "min_discount_requirement",
                                    "placeholder": __("Minimum Amount To Be Spent"),
                                    "reqd": 1
                                },
                                parent: row.find('.rangeamount'),
                                only_input: true,
                            });
                            input_min.make_input();
                            let input_max = frappe.ui.form.make_control({
                                df: {
                                    "fieldtype": "Currency",
                                    "label": __("Maximum Amount To Be Spent"),
                                    "fieldname": "max_discount_requirement",
                                    "placeholder": __("Maximum Amount To Be Spent"),
                                    "reqd": 1
                                },
                                parent: row.find('.rangeamount'),
                                only_input: true,
                            });
                            input_max.make_input();
                            if (f.min_amount)
                                input_min.set_value(f.min_amount)
                            input_min.$input.on('change', function() {
                                let val = input_min.$input.val();
                                if (val) {
                                    $(me.wizard.values["min_discount_requirement"]).each(function(k, v) {
                                        if (v.idx == f.idx) {
                                            v.min_amount = val;
                                        }
                                    });
                                }
                            });
                            if (f.max_amount) {
                                input_max.set_value(f.max_amount)
                            }
                            input_max.$input.on('change', function() {
                                let val = input_max.$input.val();
                                if (val) {
                                    $(me.wizard.values["max_discount_requirement"]).each(function(k, v) {
                                        if (v.idx == f.idx) {
                                            v.max_amount = val;
                                        }
                                    });
                                }
                            });
                        }
                        else if (f.discount_requirement == 'Spend x weight') {
                            let input = frappe.ui.form.make_control({
                                df: {
                                    "fieldtype": "Currency",
                                    "label": __("Weight For Discount"),
                                    "fieldname": "max_weight_for_discount",
                                    "placeholder": __("Weight For Discount"),
                                    "reqd": 1
                                },
                                parent: row.find('.weightbased'),
                                only_input: true,
                            });
                            input.make_input();
                            if (f.weight_for_discount)
                                input.set_value(f.weight_for_discount)
                            input.$input.on('change', function() {
                                let val = input.$input.val();
                                if (val) {
                                    $(me.wizard.values["max_weight_for_discount"]).each(function(k, v) {
                                        if (v.idx == f.idx) {
                                            v.weight_for_discount = val;
                                        }
                                    });
                                }
                            });
                        } else {
                            row.find('.btn-default').click(function() {
                                let req_dialog = new assign_items({
                                    doctype: get_doctype_for_requirement(f.discount_requirement),
                                    items_list: f.items_list || ''
                                });
                                let primary_btn = req_dialog.dialog.get_primary_btn();
                                primary_btn.click(function(e) {
                                    e.preventDefault();
                                    if (req_dialog.items_list.length > 0) {
                                        f.items_list = JSON.stringify(req_dialog.items_list);
                                    }
                                })
                            })
                        }
                    })
                } else {
                    wrapper.find('tbody').append(`<tr data-type="noitem"><td colspan="3">${__("No Records Found!")}</td></tr>`);
                }
            },
            requirement_list: function(s) {
                let slide_scope = this;
                let wrapper = s.form.fields_dict.requirement_list.$wrapper.empty();
                let limit = true;
                if (me.template_detail.discount_type == 'Assigned to Sub Total')
                    limit = false;
                let req_list = get_requirements(limit,false,cur_frm.doc.discount_type);
                $(`<div class="req-list"></div>
                    <style>
                    div[data-fieldname="requirement_list"] .req-list button{
                        margin-bottom: 5px; margin-right: 5px;
                    }
                    </style>`).appendTo(wrapper);
                req_list.map(f => {
                    let cls = 'btn-info';
                    if (me.wizard.values["discount_requirements"] && me.wizard.values["discount_requirements"].length > 0) {
                        if (me.wizard.values["discount_requirements"].find(obj => obj.discount_requirement == f)) {
                            cls = 'btn-success'
                        }
                    }
                    let row = $(`<button class="btn ${cls} btn-xs">${__(f)}</button>`);
                    wrapper.find('.req-list').append(row);
                    row.click(function() {
                        if (row.attr('class').indexOf('btn-info') != -1) {
                            row.addClass('btn-success').removeClass('btn-info');
                            if (!me.wizard.values["discount_requirements"].find(obj => obj.discount_requirement == f)) {
                                me.wizard.values["discount_requirements"].push({
                                    discount_requirement: f,
                                    idx: me.wizard.values["discount_requirements"].length + 1
                                });
                                slide_scope.bind_html(s);
                            }
                        }
                    })
                })
            }
        }
        return slide;
    },
    get_free_item: function() {
        let me = this;
        let fields = [
            { 
                "fieldname": "same_product", 
                "fieldtype": "Check", 
                "label": __("Same Product") 
            },
            { 
                "fieldname": "free_product", 
                "fieldtype": "Link", 
                "label": __("Free Product"), 
                "options": "Product" 
            },
            { "fieldname": "free_qty", 
            "fieldtype": "Int", 
            "label": __("Free Product Quantity"), 
            "default": 1 
        }
        ];
        let slide = {
            "name": "free_item",
            "title": __("Free Product"),
            "fields": fields,
            "onload": function(s) {
                me.slide_onload(fields, s, me);
            }
        }
        return slide;
    },
    coupon_fields: function() {
        let me = this;
        let fields = [
            { 
                "fieldname": "coupon_code", 
                "fieldtype": "Data", 
                "label": __("Coupon Code"), 
                "reqd": 1 
            }
        ];
        let slide = {
            "name": "coupons",
            "title": __("Coupon Code"),
            "fields": fields,
            "onload": function(s) {
                me.slide_onload(fields, s, me);
            }
        }
        return slide;
    },
    setup_wizard: function() {
        let me = this;
        let wrapper = me.dialog.fields_dict.wizard_html.$wrapper.empty();
        this.wizard;
        let slide_type;
        if (me.template)
            slide_type = 'add';
        else
            slide_type = 'edit'
        this.wizard = new SetupWizard({
            parent: wrapper,
            slides: me.slides,
            unidirectional: 0,
            slide_class: SetupWizardSlide,
            frm_action: slide_type,
            before_load: ($footer) => {
                $footer.find('.next-btn').removeClass('btn-default')
                    .addClass('btn-primary');
                $footer.find('.text-right').prepend(
                    $(`<a class="complete-btn btn btn-sm primary">
                ${__("Save")}</a>`));
            }
        });
        if (slide_type == 'add') {
            this.wizard.values['discount_type'] = this.template_detail.discount_type;
            this.wizard.values['price_or_product_discount'] = this.template_detail.price_or_product_discount;
            this.wizard.values['percent_or_amount'] = this.template_detail.percent_or_amount;
            this.wizard.values['naming_series'] = 'D-';
            this.wizard.values['doctype'] = 'Discounts';
            if (this.template_detail.discount_type == 'Assigned to Sub Total' && this.template_detail.requires_coupon_code)
                this.wizard.values['requires_coupon_code'] = 1
        } else {
            this.wizard.values = this.template_detail;
        }
    }
});

var SetupWizard = class SetupWizard extends frappe.ui.Slides {
    constructor(args = {}) {
        super(args);
        $.extend(this, args);
        this.welcomed = true;
    }
    make() {
        super.make();
        this.container.addClass("container setup-wizard-slide with-form");
        this.container.css('padding', '0px');
        this.container.css('margin', '0px auto');
        this.container.css('max-width', '650px');
        this.container.css('border', '0px');
        this.container.css('box-shadow', 'none');
        this.$next_btn.addClass('action');
        this.$footer.css('padding', '10px 70px 20px 70px');
        this.$footer.css('position', 'absolute');
        this.$footer.css('z-index', '-1');
        this.$footer.css('width', '100%');
        this.$footer.css('left', '0');
        this.$footer.css('background', '#fff');
        this.$footer.css('margin-top', '10px');
        this.$complete_btn = this.$footer.find('.complete-btn').addClass('action');
        this.setup_keyboard_nav();
    }
    setup_keyboard_nav() {
        $('body').on('keydown', this.handle_enter_press.bind(this));
    }
    disable_keyboard_nav() {
        $('body').off('keydown', this.handle_enter_press.bind(this));
    }
    handle_enter_press(e) {
        if (e.which === frappe.ui.keyCode.ENTER) {
            var $target = $(e.target);
            if ($target.hasClass('prev-btn')) {
                $target.trigger('click');
            } else {
                this.container.find('.next-btn').trigger('click');
                e.preventDefault();
            }
        }
    }
    show_hide_prev_next(id) {
        super.show_hide_prev_next(id);
        if (!this.$complete_btn)
            this.$complete_btn = this.$footer.find('.complete-btn');
        if (id + 1 === this.slides.length) {
            this.$next_btn.removeClass("btn-primary").hide();
            this.$complete_btn.addClass("btn-primary").show()
                .on('click', this.action_on_complete.bind(this));

        } else {
            this.$next_btn.addClass("btn-primary").show();
            this.$complete_btn.removeClass("btn-primary").hide();
        }
    }
    action_on_complete() {
        if (this.values) {
            if (this.values['start_date']) {
                let date = new Date(this.values['start_date'])
            }
            if (this.values['end_date'])
                this.values['end_date'] = frappe.datetime.obj_to_str(this.values['end_date'])
            if (this.values['same_product'] == 'on')
                if (!this.values['free_qty'])
                    this.values['free_qty'] = 1
            if (this.values['same_product'] == 'on')
                this.values['same_product'] = 1
            if (this.frm_action == 'add') {
                this.add_new_discount();
            } else {
                this.edit_discount();
            }
        }
    }
    add_new_discount() {
        if (!this.values['name1'])
            frappe.throw('Please enter discount title')
        frappe.call({
            method: 'go1_commerce.go1_commerce.api.insert_doc',
            args: {
                doc: this.values
            },
            callback: function(r) {
                if (r.message) {
                    frappe.set_route('Form', 'Discounts', r.message.name);
                    cur_dialog.hide();
                }
            }
        })
    }
    async edit_discount() {
        let datas = {}
        $.each(this.values, function(key, value) {
            if (typeof(value) != 'object') {
                if (!has_common([key], ['__unsaved','creation', 'modified', 'name', 'owner', 'modified_by', 'doctype', 'docstatus', 'idx']))
                    cur_frm.set_value(key, value)
            } else {
                if (key != 'discount_history') {
                    if (key != "__last_sync_on"){
                        if (key in datas){
                            datas[key].push(...value)
                        }
                        else{
                            datas[key] = [...value]
                        }
                    }
                }
            }
        });
        Object.keys(datas).map(c_key =>{
            cur_frm.doc[c_key] = []
            cur_frm.refresh_field(c_key);
        })
        let ch_keys = ['creation','docstatus','doctype','idx','modified','modified_by','name','owner','parent','parentfield','parenttype']
        $.each(datas,(key,value) =>{
            $(value).each((idx,val)=>{
                let new_child = cur_frm.add_child(key)
                Object.keys(val).map(child_key =>{
                    if(!ch_keys.includes(child_key)){
                        new_child[child_key] = val[child_key]
                    }
                })
            })
            cur_frm.refresh_field(key);
        })
        cur_frm.dirty();
        await cur_frm.save();
        cur_dialog.hide();
        cur_frm.reload_doc();
    }
}

var SetupWizardSlide = class SetupWizardSlide extends frappe.ui.Slide {
    constructor(slide = null) {
        super(slide);
    }
    make() {
        super.make();
        this.reset_action_button_state();
    }
};

var get_formated_date = function(date_value) {
    let d_format = frappe.boot.sysdefaults.date_format;
    let d = date_value.split('-');
    let format_split = d_format.split('-');
    let date, month, year;
    $(format_split).each(function(k, v) {
        if (v == 'dd')
            date = d[k];
        else if (v == 'mm')
            month = d[k];
        else if (v == 'yyyy')
            year = d[k];
    })
    return `${year}-${month}-${date}`;
}

var send_notification = function(title, message){
    frappe.call({
        method: "notification.notification.doctype.notification_center.notification_center.get_device_ids",
        args: {
            "party" : "Customers"
        },
        callback: function(r) {
            if (r.message) {
                var devices = '';
                for (var i = 0; i < r.message.length; i++) {
                    devices += r.message[i].device_id + '\n';
                }
                    var a = devices.split("\n");
                var b = a.filter(function(v) { return v !== '' });
                    frappe.call({
                    "method": "frappe.client.get",
                    args: {
                        doctype: "App Alert Settings",
                    },
                    callback: function(r) {
                        if(r.message){
                            $.each(r.message.keys, function(i,k){
                                if(k.app_type == "User App"){
                                    var one_signal_userconfig = {
                                        headers: {
                                            'Content-Type': 'application/json',
                                            "Authorization": "Basic " + k.secret_key
                                        }
                                    };
                                    var info = {};
                                    var user_notification_data = {
                                        "app_id": k.app_id,
                                            "headings": { "en": title, },
                                            "contents": { "en": message, },
                                        "data": { "add_data": message},
                                        "include_player_ids": b
                                    }
                                    user_notification_data['large_icon']=window.location.origin+"/"+$('[rel="shortcut icon"]').attr("href");
                                    user_notification_data['small_icon']=window.location.origin+"/"+$('[rel="shortcut icon"]').attr("href")
                                $.post(r.message.notification_gateway_url, user_notification_data, one_signal_userconfig).done(function(e) { frappe.msgprint('Notification Sent Successfully');});
                                }
                            })
                        }
                    }
                });
            }
        }
    });
}

var MakeMultiSelectToggle = Class.extend({
    init: function(opts) {
        this.cur_frm = opts.cur_frm;
        this.cdt = opts.cdt;
        this.cdn = opts.cdn;
        this.possible_val = opts.settings;
        this.list_array = opts.list_array;
        this.make();
    },
    make: function() {
        this.build_multi_selector()
    },
    build_multi_selector: function() {
        let me = this;
        $.each(me.possible_val, function(i, c) {
            cur_frm.fields_dict[c.child_tab_link].grid.grid_rows_by_docname[me.cdn].grid_form.fields_dict['product_attribute_html'].$wrapper.empty();
            var field = c.tab_field
            var list_name = me.list_array;
            let drp_html = `<div class="${c.cls}" style="padding: 0px;">
                                <div class="awesomplete" style="min-height: 210px;">
                                    <input type="text"  class="multi-drp" id="myInput" autocomplete="nope" 
                                        onfocus="select_list_detail($(this))" onfocusout="disable_select_list($(this))" 
                                        onkeyup="selected_lists_values($(this))" placeholder="${c.title}" title="${c.title}"
                                        style="display:none;background-position: 10px 12px;background-repeat: no-repeat;
                                        width: 100%;font-size: 16px;padding: 10px 15px 10px 10px;border: 1px solid #d1d8dd;
                                        border-radius: 4px !important;;margin: 0px;" data-class="${c.cls}" data-field="${c.tab_field}" 
                                        data-doctype="${c.doctype}" data-child="${c.is_child}" data-linkfield="${c.link_name}" 
                                        data-reference_doc="${c.reference_doc}" data-reference_fields="${c.reference_fields}" 
                                        data-search_fields="${c.search_fields}" data-reference_method="${c.reference_method}" 
                                        data-child_link="${c.child_tab_link}">
                                    <h4 style="padding: 10px 10px;border: 1px solid #ddd;border-bottom: none;
                                        margin: 10px 0px 0px 0px;background: #f8f8f8;">${c.label}
                                    </h4>
                                    <ul role="listbox" id="assets" class= "assets" style="list-style-type: none;position: static;
                                        width: 43%;margin: 0;background: rgb(255, 255, 255);min-height:${c.height};height:${c.height}
                                        box-shadow:none;>
                            `
            var k = 0;
            $.each(list_name, function(i, v) {
                if (v) {
                    k += 1
                    let arr;
                    var cur_row = frappe.get_doc(me.cdt, me.cdn);
                    arr = JSON.parse(cur_row[field]|| '[]');
                    let obj = arr.filter(o => o.idx == k);
                    if(obj.length<=0){
                        drp_html += `<li style="display: block; border-bottom: 1px solid #dfdfdf;cursor:auto;">
                                        <a style="display: none;">
                                            <strong>${v["label"]}</strong>
                                        </a>
                                        <label class="switch" style="float:right; margin:0px; cursor:pointer;">
                                            <input type="checkbox" class="popupCheckBox" name="vehicle1" value="0" id="${v["name"]}"
                                                data-label="${v["label"]}" data-product="${v["product"]}" data-idx="${v["idx"]}" 
                                                data-doctype="${c.doctype}" data-child="${c.is_child}" data-reference_doc="${c.reference_doc}" 
                                                data-reference_fields="${c.reference_fields}" data-search_fields="${c.search_fields}"
                                                data-child_link="${c.child_tab_link}" onclick="selected_discount_multiselect_lists($(this))">
                                            <span class=" slider round" ></span>
                                        </label>
                                        <p style="font-size: 14px;">
                                            <span>
                                                ${v["label"]}
                                            </span>
                                        </p>
                                    </li>`
                    }
                    else{
                        drp_html += `<li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;">
                                        <a style="display: none;">
                                            <strong>
                                                ${v["label"]}
                                            </strong>
                                        </a>
                                        <label class="switch" style="float:right; margin:0px; cursor:pointer;">
                                            <input type="checkbox" class="popupCheckBox" name="vehicle1" value="0" 
                                                id="${v["name"]}" data-label="${v["label"]}" data-product="${v["product"]}"
                                                data-idx="${v["idx"]}" data-doctype="${c.doctype}" data-child="${c.is_child}"
                                                data-reference_doc="${c.reference_doc}" data-reference_fields="${c.reference_fields}"
                                                data-search_fields="${c.search_fields}" data-child_link="${c.child_tab_link}"
                                                onclick="selected_discount_multiselect_lists($(this))" checked>
                                            <span class=" slider round" ></span>
                                        </label>
                                        <p style="font-size: 14px;">
                                        <span>
                                                ${v["label"]}
                                        </span>
                                        </p>
                                    </li>`
                    }
                }
                else {
                    drp_html += '<li></li>';
                }
            })
            drp_html += `</ul>
                        </div>
                        </div>
                    <p class="help-box small text-muted hidden-xs" style="display:none">
                        ${c.description}
                    </p>
                    <style>
                        .awesomplete > ul > li {
                            cursor: pointer;
                            font-size: 12px;
                            padding: 7px 12.8px;
                        }
                        input.popupCheckBox:checked + .slider {
                            background-color: #2196F3;
                        }
                        input.popupCheckBox:focus + .slider {
                            box-shadow: 0 0 1px #2196F3;
                        }
                        input.popupCheckBox:checked + .slider:before {
                            -webkit-transform: translateX(20px);
                            -ms-transform: translateX(20px);
                            transform: translateX(20px);
                        }
                        .switch {
                            position: relative;
                            display: inline-block;
                            width: 45px;height: 28px;
                        }
                        .slider:before {
                            position: absolute;
                            content: "";
                            height: 20px;
                            width: 20px;
                            left: 4px;bottom: 4px;
                            background-color: white;
                            -webkit-transition: .4s;
                            transition: .4s;
                        }
                        .slider.round:before {
                            border-radius: 50%;
                        }
                        .slider {
                            position: absolute;
                            cursor: pointer;
                            top: 0;
                            left: 0;
                            right: 0;
                            bottom: 0;
                            background-color: #ccc;
                            -webkit-transition: .4s;transition: .4s;
                        }
                        .slider.round {
                            border-radius: 28px !important;
                        }
                        .switch input {
                            opacity: 0;
                            width: 0;
                            height: 0;
                        }
                    </style> `;
            let wrapper = cur_frm.fields_dict[c.child_tab_link].grid.grid_rows_by_docname[me.cdn].grid_form.fields_dict['product_attribute_html'].$wrapper;
            $(wrapper).append(drp_html);  
        });
    }
})