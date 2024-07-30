// Copyright (c) 2018, info@valiantsystems.com and contributors
// For license information, please see license.txt

{% include 'go1_commerce/go1_commerce/doctype/product/product_import.js' %}
frappe.provide("go1_commerce.product");

var currency = frappe.boot.sysdefaults.currency;
var symbol = ""

frappe.call({
        method: 'frappe.client.get_value',
        args: {
            'doctype': "Currency",
            'filters': { 'name': frappe.boot.sysdefaults.currency },
            'fieldname': "symbol"
        },
        callback: function (r) {
            if(r.message) {
                symbol = r.message.symbol
            }
        }
    })
    
var is_s3_enabled = 0;
cur_frm.create_combination = 0;

frappe.ui.form.on('Product', {
    onload: function (frm) {
        let args = {
            'dt': 'Catalog Settings'
        };
        frm.events.get_settings(frm,args);
    },
    refresh(frm){
        add_class()
        remove_class()
        frm.events.hide_sections_and_build_attr_html(frm);
        frm.events.render_tags_html(frm);
        frm.events.hide_show_pre_order_section(frm);
        frm.events.update_product_status(frm);
        frm.events.get_all_brands(frm)
        frm.events.multi_upload(frm)
        frm.edit_option = 0;
        frm.events.product_attribute_html(frm)
        frm.events.add_combination_btn(frm)
        frm.events.add_click_event_func(frm)
        frm.events.filter_link_fields_data(frm)
        frm.events.set_product_brand_data(frm)
        frm.events.generate_variant_combinations_html(frm)
    },
    generate_variant_combinations_html(frm){
        new generate_variant_combination_html({
            frm:frm,
            items_list: frm.doc.variant_combination || [],
            cdt: frm.doctype,
            cdn: frm.docname
        });
    },
    get_settings: function(frm,args) {
        frappe.call({
            method: 'go1_commerce.utils.setup.get_settings',
            args: args,
            async: false,
            callback: function(r) {
                frm.catalog_settings = r.message;
            }
        })
    },
    free_shipping(frm){
        if (frm.doc.free_shipping == 1) {
            frm.set_value("additional_shipping_cost", 0);
        }
    },
    set_product_brand_data(frm){
        frm.possible_val = [{  
            "cls":"product-brand-model",
            "tab_html_field": "model_html",
            "tab_field": "model_json",
            "link_name": "name",
            "title": "Select model here...",
            "label": "Model",
            "doctype": "Product Brand Mapping",
            "reference_doc":"Model",
            "reference_fields":escape(JSON.stringify(["name"])),
            "search_fields":"name",
            "reference_method":"go1_commerce.go1_commerce.doctype.product.product.get_models",
            "is_child": 1,
            "description": "Please select the model for this brand.",
            "child_tab_link":"product_brands"}];    
    },
    filter_link_fields_data(frm){
        frm.set_query("product_attribute", "product_attributes", function (doc, cdt, cdn) {
            return {
                'query': 'go1_commerce.go1_commerce.doctype.product.product.get_category_based_attributes',
                'filters': {
                    productId: frm.doc.name,
                    type: "Product Attribute"
                }
            };
        });
        frm.set_query("attribute", "product_specification_attributes", function (doc, cdt, cdn) {
            return {
                'query': 'go1_commerce.go1_commerce.doctype.product.product.get_category_based_attributes',
                'filters': {
                    productId: frm.doc.name,
                    type: "Specification Attribute"
                }
            };
        }); 
    },
    add_click_event_func(frm){
        $('.addProductBrands').click(function () {
            if ($('body').attr('class') == 'skin-blue sidebar-mini')
                brand_dialog(frm)
        })
        $('.addProductImages').click(function () {
            localStorage.setItem('randomuppy', ' ');
            frm.trigger('image_upload')
        })
        $('.addCategories').click(function () {
            if ($('body').attr('class') == 'skin-blue sidebar-mini') {
                frappe.run_serially([
                    () => {
                        frm.trigger('get_all_category_list')
                    },
                    () => {
                        $('.modal').empty();
                        $('.modal').removeClass('in');
                        category_dialog(frm)
                    }
                ])
            }
        })
    },
    multi_upload: function (frm) {
        $(frm.fields_dict['img_html'].wrapper).html("");
        $('button[data-fieldname="add_image"]').addClass('btn-primary')
        if (frm.doc.product_images) {
            var img_html = `<div class="row" id="img-gallery" style="margin-top: -10px;
                                padding-left: 135px;min-height:120px;">`;
            $(frm.doc.product_images).each(function (i, v) {
                var m_top = "5px;"
                if(i > 7){
                    m_top = "20px;"
                }
                img_html += `
                    <div style="width: 12.5% !important;float: left;margin-top:${m_top} 
                            id="div${i}" title="${v.name}" class="sortable-div div_${v.name}"> 
                        <div class="col-md-12" style="margin-bottom: 15px;padding: 0 10px;" id="drag${v.idx}">
                            <div style="height:100px;position:relative;" class="">
                                <img class="img-name" src="${v.list_image}" title="${v.image_name}" id="${v.name1}"
                                    style="border: 1px solid #ddd;float: left;width: 120px;height: 120px;
                                        object-fit: cover;min-width: 120px;margin-top: -5px;
                                        margin: -5px 0 0 0 !important;width: 100% !important;min-width: 100% !important;
                                        border-radius: 5px;cursor:pointer;" 
                                    onclick=show_product_gallery("${v.name}")>
                                <a class="img-close" id="${v.name}" style="display:none;cursor: pointer;font-size: 21px;
                                        float: right;font-weight: bold;line-height: 1;color: #000;text-shadow: 0 1px 0 #fff;
                                        opacity: .2;">×
                                </a>
                                <a data-id="${v.name}" class="edit" style="display:none;font-size:15px;padding:5px;color:#a2a0a0;;">
                                    <i class="fa fa-pencil-square-o" aria-hidden="true"></i>
                                </a>
                                <label style="display:none !important;font-size: 10px;font-weight: 200;">Is Cover Image
                                    <input type="checkbox" data-fieldname="is_cover_image" style="float:left;
                                    margin-right: 6px;margin-top: 0px;display:none !important">
                                </label>
                                <input type="text" data-fieldtype="Data" data-fieldname="image_title" value="${v.name1}" 
                                    style="margin-top: 5px;width: 112px;display:none !important" placeholder="Name">
                                <a class="save" data-id="${v.name}" style="font-size:15px;padding:5px;color:#a2a0a0;display:none">
                                    <i class="fa fa-save" aria-hidden="true"></i>
                                </a>
                            </div>
                        </div>
                    </div>
                    <div class="image-field" data-name="${v.name}" style="display:none;">
                        <span class="placeholder-text"></span>
                        <img data-name="${v.name}" src="${v.product_image}">
                    </div> `;
                            
            })
            img_html += '</div>';
            $(frm.fields_dict['img_html'].wrapper).html(img_html);
        }
        $('.ui-state-highlight').css('background', '#ddd')
        $('.ui-state-highlight').css('height', '50px')
        $('.ui-state-highlight').css('width', '50px')
        frm.dropIndex = '';
        $('.save').on('click', function () {
            let id = $(this).attr('data-id');
            let child_record = frm.doc.item_images.find(obj => obj.name == id);
            if(child_record) {
                let is_cover = 0;
                if ($(this).parent().find('input[data-fieldname="is_cover_image"]:checked').val()) {
                    is_cover = 1;
                }
                let name = $(this).parent().find('input[data-fieldname="image_title"]').val();
                if (name != '') {
                    frappe.model.set_value(child_record.doctype, child_record.name, 'is_cover_image', is_cover)
                    frappe.model.set_value(child_record.doctype, child_record.name, 'name1', name)
                    cur_frm.save();
                    cur_frm.refresh_fields('item_images');
                }
                $(this).parent().find('label').hide();
                $(this).parent().find('input[type="text"]').hide();
                $(this).parent().find('.save').hide();
                $(this).parent().find('.edit').show();
                $(this).parent().find('.img-close').show();
            }
        })
    },
    get_all_brands(frm){
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.get_all_brands',
            args: {},
            callback: function (data) {
                if (data.message) {
                    frm.brands_list = data.message;
                }
            }
        })
    },
    hide_sections_and_build_attr_html(frm){
        if (frm.doc.status != 'Waiting for Approval'){
            frm.set_df_property('status', 'read_only', 1)
        }
        if($(".title-text img").attr("src") == frm.doc.name) {
            $(".title-image").hide();
        } 
        else {
            $(".title-image").show();
        }
        frm.set_df_property("image", "hidden", 1);
        $("#page-Product").find('div[data-fieldname="__section_11"]').hide()
        $("#page-Product").find('div[data-fieldname="__section_13"]').hide()
        $("#page-Product").find('div[data-fieldname="__section_16"]').hide()
        $("#page-Product").find('div[data-fieldname="__section_18"]').hide()
        $("#page-Product").find('div[data-fieldname="__section_21"]').hide()
        $("#page-Product").find('div[data-fieldname="__section_25"]').hide()
        $("#page-Product").find('div[data-fieldname="__section_29"]').hide()
        $("#page-Product").find('div[data-fieldname="__section_32"]').hide()
        $("#page-Product").find('div[data-fieldname="__section_34"]').hide()
        $('div[data-fieldname="option"]').hide();
        $('div[data-fieldname="add_on"] .form-grid .grid-body .rows .grid-row').find('.sortable-handle a').text("Edit");
        $('div[data-fieldname="add_on"] .form-grid .grid-body .rows .grid-row').find('.sortable-handle a').css("color", "#ea1e1b");
        $('div[data-fieldname="add_on"] .form-grid .grid-body .rows .grid-row').find('.sortable-handle a').css("opacity", "5");
        $('div[data-fieldname="add_on"] .form-grid .grid-body .rows .grid-row').find('.sortable-handle a').css("font-size", "15px");
        $('div[data-fieldname="add_on"] .form-grid .grid-body .rows .grid-row').find('.sortable-handle a').css("margin-top", "10px");
        $('div[data-fieldname="add_on"] .form-grid .grid-body .rows .grid-row').find('.sortable-handle a').css("margin-right", "25px");
        $('div[data-fieldname="heading"]').hide();
        $('div[data-fieldname="names"]').hide();
        if(frm.catalog_settings) {
            if(frm.catalog_settings.disable_search_keyword == 1) {
                frm.toggle_display(['product_search_keyword'], false);
            }
            if(!frm.catalog_settings.enable_product_video || frm.catalog_settings.enable_product_video == 0) {
                frm.toggle_display(['product_video'], false);
            }
            if(frm.catalog_settings.enable_returns_system == 0) {
                frm.toggle_display(['sec123'], false);
            }
            frm.events.product_attribute_html(frm);
        }
        if (!frm.doc.__islocal) {
            setTimeout(function() {
            if (has_common(frappe.user_roles, ['Admin'])) {
                $(".main-section [id='page-Form/Product']").find('.page-head .page-actions').find('.menu-btn-group').removeClass('hide');
            }
            },1000)
            cur_frm.page.$title_area.find('.go-backbtn').css('align-self', 'center');
            cur_frm.page.$title_area.find('.indicator').css('align-self', 'center');
        }
        if (frm.doc.__islocal) {
            frm.set_df_property('stock', 'read_only', 0)
            frappe.meta.get_docfield("Product Variant Combination", "stock", cur_frm.docname).read_only = 0;
            $(frm.fields_dict['img_html'].wrapper).html("");
            frm.doc.product_images = []
        }
        else{
            if(frm.doc.inventory_method != "Dont Track Inventory" && frm.doc.stock != 0) {
                if(frm.doc.has_variants && frm.doc.is_template){
                    frm.set_df_property('stock', 'read_only', 1)
                }
                else{
                    frm.set_df_property('stock', 'read_only', 0)
                }
            }
            frappe.meta.get_docfield("Product Variant Combination", "stock", cur_frm.docname).read_only = 1;
        }
        cur_frm.fields_dict.choose_warranty.$wrapper.find("button[data-fieldname='choose_warranty']").
                                                    addClass("btn-secondary").removeClass("btn-default");
        $('.frappe-control[data-fieldname="img_html"]').attr("style","position:unset");
        $("div[data-fieldname='edit_options']").each(function () {
            $(this).click();
            $(this).find(".field-area").css("display", "block !important;");
        });
        $("button[data-fieldname='edit_options']").each(function () {
            $(this).removeClass("btn-default").addClass("btn-primary");
        });
        setTimeout(function () {
            $("div[data-fieldname='edit_options']").each(function () {
                $(this).find(".field-area").css("display", "block !important;");
                $(this).css("padding", "0 !important;");
            });
        }, 3000);
    },
    update_product_status(frm){
        frm.set_value('status', 'Approved')
        frm.set_df_property('status', 'hidden', 1)
    },
    hide_show_pre_order_section(frm){
        frm.set_df_property('preorder_section', 'hidden', 1)
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.get_order_settings',
            args: {},
            async:false,
            callback: function(d) {
                if(d.message){
                    var enable_preorder = d.message.order_settings.enable_preorder;
                    if(enable_preorder==1){
                        frm.set_df_property('preorder_section', 'hidden', 0)
                    }
                    is_s3_enabled = d.message.s3_enable;
                }
            }
        })  
    },
    render_tags_html(frm){
        $(frm.get_field('tag_html').wrapper).empty();
        if (!frm.doc.product_tag) {
            frm.set_value("product_tag", "[]");
        }
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.get_all_tags',
            args: {},
            callback: function (data) {
                if(data.message){
                    frm.tag_multicheck = frappe.ui.form.make_control({
                        parent: frm.fields_dict.tag_html.$wrapper,
                        df: {
                            fieldname: "tag_multicheck",
                            fieldtype: "MultiCheck",
                            get_data: () => {
                                let active_tags = JSON.parse(frm.doc.product_tag);
                                if(data.message && data.message.length > 0) {
                                    frm.toggle_display(['sec_20'], true);
                                }
                                return data.message.map(domain => {
                                    return {
                                        label: domain,
                                        value: domain,
                                        checked: active_tags.includes(domain)
                                    };
                                });
                            }
                        },
                        render_input: true
                    });
                    frm.tag_multicheck.refresh_input();
                }
                else{
                     frm.set_df_property('sec_20', 'hidden', 1)
                }
            }
        });
    },
    product_attribute_html: function (frm) {
        let wrapper = $(frm.get_field('product_attribute_html').wrapper).empty();
        let hide_size_chart = '';
        if(frm.catalog_settings){
            hide_size_chart = (frm.catalog_settings.enable_size_chart == 1) ? '' : 'hide';
        }
        if(frm.catalog_settings && frm.catalog_settings.enable_vendor_based_pricing == 1 ){
            hide_edit_option = 'hide';
        }
        let table_html = $(`<table class="table table-bordered" style="cursor:pointer; margin:0px;">
            <thead>
                <tr>
                    <th>Product Attribute</th>
                    <th>Is Required</th>
                    <th>Control Type</th>
                    <th>Display Order</th>
                    <th class="restaurant">Parent Attribute</th>
                    <th class="restaurant">Attribute Group</th>
                    <th class="not_restaurant ${hide_size_chart}">Size Chart</th>
                    <th>Options</th>
                    <th style="width:15%;"></th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>`).appendTo(wrapper);
        $('.restaurant').hide();
        $('.not_restaurant').show();
        if (frm.doc.product_attributes && frm.doc.product_attributes.length > 0) {
            frm.doc.product_attributes.map(f => {
                var size_chart = '';
                var parent_attribute = f.parent_attribute_name
                if (f.parent_attribute == null || f.parent_attribute == undefined) {
                    parent_attribute = "";
                }
                var attribute_group = f.group_name
                if (f.group_name == null || f.group_name == undefined) {
                    attribute_group = "";
                }
                let row_data = $(`<tr data-id="${f.name}" data-idx="${f.idx}">
                    <td>${f.attribute}</td>
                    <td>${f.is_required}</td>
                    <td>${f.control_type}</td>
                    <td>${f.display_order}</td>
                    <td class="restaurant">${parent_attribute}</td>
                    <td class="restaurant">${attribute_group}</td>
                    <td class="not_restaurant ${hide_size_chart}">${size_chart}</td>
                    <td>
                        <button class="btn btn-xs btn-primary">Edit Options</button>
                    </td>
                    <td>
                        <button class="btn btn-xs btn-warning">Edit</button>
                        <button class="btn btn-xs btn-danger" style="margin-right:10px;">Delete</button>
                    </td>
                </tr>`);
                table_html.find('tbody').append(row_data);
            });
            $('.restaurant').hide();
            $('.not_restaurant').show();
        } 
        else {
            table_html.find('tbody').append(`<tr><td colspan="6">No records found!</td></tr>`);
        }
        $(frm.get_field('product_attribute_html').wrapper).find('tbody .btn-danger').on('click', function () {
            let id = $(this).parent().parent().attr('data-id');
            var msg = "Do you want to delete this option?";
            frappe.confirm(__(msg), () => {
                if (id) {
                    frappe.call({
                        method: 'go1_commerce.go1_commerce.doctype.product.product.delete_option',
                        args: {
                            name: id
                        },
                        callback: function (f) {
                            frm.trigger('product_attribute_html')
                            cur_frm.reload_doc()
                        }
                    })
                }
            });
        })
        $(frm.get_field('product_attribute_html').wrapper).find('tbody .btn-warning').on('click', function () {
            let id = $(this).parent().parent().attr('data-id');
            frm.product_attribute = frm.doc.product_attributes.find(obj => obj.name == id);
            frm.edit_option = 1;
            frm.trigger('add_product_attributes');
        })
        $(frm.get_field('product_attribute_html').wrapper).find('tbody .btn-primary').on('click', function () {
            let id = $(this).parent().parent().attr('data-id');
            if(!id.startsWith('New Product Attribute Mapping')) {
                frm.attribute = frm.doc.product_attributes.find(obj => obj.name == id);
                frm.trigger('edit_options');
            } 
            else {
                frappe.msgprint('Please save the attribute to add options');
            }                
        })
        var attribute_list = []
        $(frm.doc.product_attributes).each(function (k, v) {
            var attroptions = {}
            frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.product.product.get_parent_product_attribute_options',
                args: {"attribute": v.product_attribute, "product":frm.doc.name},
                async:false,
                callback: function (data) {
                    if(data.message){
                        var opt = ""
                        $(data.message).each(function (k, v) {
                            if(opt){
                                opt +=", "
                            }
                            opt += v.option_value
                        })
                        attroptions["attroptions"]=data.message
                        attroptions["options"] = opt
                    }
                }
            })
            attribute_list.push({"idx":v.idx, "name": v.name, "product_attribute":v.product_attribute, "product":frm.doc.name, "display_order": v.display_order, "attribute":v.attribute, "quantity": v.quantity, "attribute_unique_name":v.attribute_unique_name, "is_required": v.is_required, "control_type":v.control_type, "options": attroptions["options"], "attroptions": attroptions["attroptions"]})
        })
        frm.attribute_items = attribute_list
        new generate_variant_html({
             frm:frm,
             items_list: attribute_list,
             cdt: cur_frm.doctype,
             cdn: cur_frm.docname
         });
        
    },
    after_save: function(frm) {
        if(is_s3_enabled == 1){
            frm.reload_doc();
        }
    },
    choose_template: function(frm) {
        frappe.run_serially([
            () => {
                frm.trigger('get_templates')
            },
            () => {
                if (frm.templates_list && frm.templates_list.length > 0){
                    frm.trigger('templates_html')
                }
                else{
                    frm.toggle_display(['section_break_1'], false);
                }
            }
        ]);
    },
    get_templates: function(frm) {
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.get_product_templates',
            args: {business:frm.vendor_business},
            async: false,
            callback: function(r) {
                var templates_list = r.message;
                frm.templates_list = templates_list
            }
        })
    },
    templates_html: function(frm) {
        var dialog = new frappe.ui.Dialog({
            title: __("Choose Product Template"),
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
                let template = `<div class="section-title">${f.name}(${f.item})</div>`;
                if (f.image) {
                    template = `<div class="section-img"><img src="${f.image}" /></div><p>${f.item}(${f.name})</p>`
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
        dialog.set_primary_action(__("Choose Product Template"), function() {    
        if (selected_doc) {
            dialog.hide();
            new ProductTemplateWizard({
                template: selected_doc.name,
                frm: frm.doc
            })
        } else {
            frappe.throw(__("Please pick any template"));
        }
        })
        dialog.show();
    },
    set_options_in_table: function (frm) {
        let selected_options = frm.tag_multicheck.get_value();
        frm.set_value("product_tag", JSON.stringify(selected_options))
        refresh_field('product_tag');
    },
    pick_return_policy: function (frm) {
       returnpolicy_dialog(frm)
    },
    choose_warranty: function (frm) {
        warranty_dialog(frm)
    }, 
    choose_replacement_policy: function (frm) {
        replacement_dialog(frm)
    },
    pick_specification_attribute: function (frm) {
        specification_dialog(frm)
    },
    choose_cross_selling: function(frm){
        frm.possible_val = [{
            "cls": "custom-crossselling-product",
            "hasimage":1,
            "imagefield":"image",
            "imagetitlefield":"item",
            "tab_html_field": "cross_selling_html",
            "tab_field": "cross_json",
            "link_name": "name",
            "link_field": "cross_selling_products",
            "title": "Search product here...",
            "label": "Choose Product",
            "doctype": "Product",
            "reference_doc": "Product",
            "reference_fields": escape(JSON.stringify(["name", "item", "sku", "image"])),
            "filters":"",
            "search_fields": "item",
            "reference_method": "go1_commerce.go1_commerce.doctype.product.product.get_returnpolicy_list",
            "is_child": 0,
            "description": "Please select the product",
            "child_tab_link": "",
            "height": "180px"
        }];
        let crossSellingDialog;
        var content = []
        crossSellingDialog = new frappe.ui.Dialog({
            title: __('Select Cross Selling Products'),
            fields: [
            {
                label: "Select Cross Selling Products",
                fieldtype: 'HTML',
                fieldname: 'cross_selling_html',
                options: ''
            },
            {
                label: "Selected Product",
                fieldtype: 'Code',
                fieldname: 'cross_json',
                options: '',
                read_only: 1,
                hidden: 1
            }
            ],
            primary_action_label: __('Close')
        });
        $.each(cur_frm.doc.cross_selling_products, function (i, s) {
            content.push(s.product)
        })
        crossSellingDialog.get_field('cross_json').set_value(JSON.stringify(content));
        crossSellingDialog.get_field('cross_json').refresh();
        crossSellingDialog.show();
        setTimeout(function () {
            frm.events.build_multi_selector(frm, frm.possible_val);
        }, 1000)
        crossSellingDialog.set_primary_action(__('Add'), function () {
            var cat = crossSellingDialog.get_values();
            var cat_json = JSON.parse(cat.cross_json)
            cur_frm.doc.cross_selling_products = [];
            $(cat_json).each(function (k, v) {
                frappe.db.get_value("Product",v,'item').then(r=>{
                    let row = frappe.model.add_child(frm.doc, "Cross Selling Products", "cross_selling_products");
                    row.product = v;
                    row.product_name = r.message.item;
                    frm.refresh_field('cross_selling_products')
                })
            })
            if (cat_json.length <= 0) {
                frappe.throw(__('Please select any one product.'))
            } else {
                refresh_field("cross_selling_products");
                frm.refresh_field('cross_selling_products')
                $('div[data-fieldname="cross_selling_products"] .grid-footer').addClass('hidden')
                crossSellingDialog.hide();
            }
        })
        crossSellingDialog.$wrapper.find('.modal-dialog').css("min-width", "1000px");
        crossSellingDialog.$wrapper.find('.modal-content').css("min-height", "575px");
    },
    choose_related_products: function(frm){
        frm.possible_val = [{
            "cls": "custom-related-products",
            "hasimage":1,
            "imagefield":"image",
            "imagetitlefield":"item",
            "tab_html_field": "related_html",
            "tab_field": "related_json",
            "link_name": "name",
            "link_field": "related_products",
            "title": "Search product here...",
            "label": "Choose Related Products",
            "doctype": "Product",
            "reference_doc": "Product",
            "reference_fields": escape(JSON.stringify(["name", "item", "sku", "image"])),
            "filters":"",
            "search_fields": "item",
            "reference_method": "go1_commerce.go1_commerce.doctype.product.product.get_returnpolicy_list",
            "is_child": 0,
            "description": "Please select the product",
            "child_tab_link": "",
            "height": "180px"
        }];
        let relatedproductDialog;
        var content = []
        relatedproductDialog = new frappe.ui.Dialog({
            title: __('Select Related Products'),
            fields: [
            {
                label: "Select Related Products",
                fieldtype: 'HTML',
                fieldname: 'related_html',
                options: ''
            },
            {
                label: "Selected Related Products",
                fieldtype: 'Code',
                fieldname: 'related_json',
                options: '',
                read_only: 1,
                hidden: 1
            }
            ],
            primary_action_label: __('Close')
        });
        $.each(cur_frm.doc.related_products, function (i, s) {
            content.push(s.product)
        })
        relatedproductDialog.get_field('related_json').set_value(JSON.stringify(content));
        relatedproductDialog.get_field('related_json').refresh();
        relatedproductDialog.show();
        setTimeout(function () {
            frm.events.build_multi_selector(frm, frm.possible_val);
        }, 1000)
        relatedproductDialog.set_primary_action(__('Add'), function () {
            var cat = relatedproductDialog.get_values();
            var cat_json = JSON.parse(cat.related_json)
            cur_frm.doc.related_products = [];
            $(cat_json).each(function (k, v) {
                frappe.db.get_value("Product",v,'item').then(r=>{
                    let row = frappe.model.add_child(frm.doc, "Related Product", "related_products");
                    row.product = v;
                    row.product_name = r.message.item;
                    frm.refresh_field('related_products')
                })
            })
            if (cat_json.length <= 0) {
                frappe.throw(__('Please select any one product.'))
            } else {
                refresh_field("related_products");
                frm.refresh_field('related_products')
                $('div[data-fieldname="related_products"] .grid-footer').addClass('hidden')
                relatedproductDialog.hide();
            }
        })
        relatedproductDialog.$wrapper.find('.modal-dialog').css("min-width", "1000px");
        relatedproductDialog.$wrapper.find('.modal-content').css("min-height", "575px");
    },
    choose_related_categories: function(frm){
        frm.possible_val = [{
            "cls": "custom-related-product-category",
            "hasimage":0,
            "imagefield":"",
            "imagetitlefield":"",
            "tab_html_field": "category_html",
            "tab_field": "category_json",
            "link_name": "name",
            "link_field": "parent_categories",
            "title": "Search product category here...",
            "label": "Choose Category",
            "doctype": "Product",
            "reference_doc": "Product Category",
            "reference_fields": escape(JSON.stringify(["name", "category_name"])),
            "filters":"",
            "search_fields": "category_name",
            "reference_method": "go1_commerce.go1_commerce.doctype.product.product.get_category_list",
            "is_child": 0,
            "description": "Please select the category for this plan.",
            "child_tab_link": "",
            "height": "180px"
        }];
        let relatedcategoryDialog;
        var content = []
        relatedcategoryDialog = new frappe.ui.Dialog({
            title: __('Select Categories'),
            fields: [
            {
                label: "Select Category",
                fieldtype: 'HTML',
                fieldname: 'category_html',
                options: ''
            },
            {
                label: "Selected Category",
                fieldtype: 'Code',
                fieldname: 'category_json',
                options: '',
                read_only: 1,
                hidden: 1
            }
            ],
            primary_action_label: __('Close')
        });
        $.each(cur_frm.doc.related_product_categories, function (i, s) {
            content.push(s.category)
        })
        relatedcategoryDialog.get_field('category_json').set_value(JSON.stringify(content));
        relatedcategoryDialog.get_field('category_json').refresh();
        relatedcategoryDialog.show();
        setTimeout(function () {
            frm.events.build_multi_selector(frm, frm.possible_val);
        }, 1000)
        relatedcategoryDialog.set_primary_action(__('Add'), function () {
            var cat = relatedcategoryDialog.get_values();
            var cat_json = JSON.parse(cat.category_json)
            cur_frm.doc.related_product_categories = [];
            $(cat_json).each(function (k, v) {
                frappe.db.get_value("Product Category",v,'category_name').then(r=>{
                    let row = frappe.model.add_child(frm.doc, "Related Product Category", "related_product_categories");
                    row.category = v;
                    row.category_name  = r.message.category_name
                    frm.refresh_field('related_product_categories')
                })
            })
            if (cat_json.length <= 0) {
                frappe.throw(__('Please select any one category.'))
            } else {
                refresh_field("related_product_categories");
                frm.refresh_field('related_product_categories')
                $('div[data-fieldname="related_product_categories"] .grid-footer').addClass('hidden')
                relatedcategoryDialog.hide();
            }
        })
        relatedcategoryDialog.$wrapper.find('.modal-dialog').css("min-width", "1000px");
        relatedcategoryDialog.$wrapper.find('.modal-content').css("min-height", "575px");
    },
    percentage_or_amount: function(frm) {
        frm.set_df_property('preorder_percent', 'reqd', 1 ? (frm.doc.percentage_or_amount == 'Preorder Percentage') : 0)
        frm.set_df_property('preorder_amount', 'reqd', 1 ? (frm.doc.percentage_or_amount == 'Preorder Amount') : 0)
    },
    add_categories: function (frm) {
        frappe.run_serially([
            () => {
                $('.modal').empty();
                $('.modal').removeClass('in');
                category_newdialog(frm)
            }
        ])
    },
    add_brands: function (frm) {
        frappe.run_serially([
            () => {
                frm.trigger('get_all_brands')
            },
            () => {
                $('.modal').empty();
                $('.modal').removeClass('in');
                brand_newdialog(frm)
            }
        ])
    },
    multiselect_items(frm, possible_val) {
        $.each(possible_val, function (i, c) {
            var ref_fields = unescape(c.reference_fields)
            var ref_method = c.reference_method
            var url = '/api/method/' + ref_method
            frm.page_no=1;
            $.ajax({
                type: 'POST',
                Accept: 'application/json',
                ContentType: 'application/json;charset=utf-8',
                url: window.location.origin + url,
                data: {
                    "reference_doc": c.reference_doc,
                    "reference_fields": ref_fields,
                     "page_no": frm.page_no
                },
                dataType: "json",
                async: false,
                headers: {
                    'X-Frappe-CSRF-Token': frappe.csrf_token
                },
                success: function (r) {
                    var list_name = r.message.list_name;
                    var drp_html = `
                        <div class="${c.cls}" style="padding: 0px;">
                            <div class="awesomplete">
                                <input type="text"  class="multi-drp" id="myInput" autocomplete="nope" 
                                    onfocus="select_return_list($(this))" onfocusout="disable_select_list($(this))" 
                                    onkeyup="selected_return_values($(this))" placeholder="${c.title}" title="${c.title}"
                                        style = "background-position: 10px 12px;background-repeat: no-repeat;
                                    width: 100%;font-size: 16px;padding: 10px 15px 10px 10px;border: 1px solid #d1d8dd;
                                    border-radius: 4px !important;;margin: 0px;" data-class="${c.cls}" data-field="${c.tab_field}"
                                    data-doctype="${c.doctype}" data-child="${c.is_child}" data-linkfield="${c.link_name}"
                                    data-reference_doc="${c.reference_doc}" data-reference_fields="${c.reference_fields}" 
                                    data-search_fields="${c.search_fields}" data-reference_method="${c.reference_method}" 
                                    data-child_link="${c.child_tab_link}" data-tab_html_field="${c.tab_html_field}">
                                <table style="width: 100%;">
                                    <tr>
                                        <td style="width: 8%;">
                                            <h4 style="padding: 10px 10px;border: 0px solid #ddd;
                                                    border-bottom: none;background: #f8f8f8;
                                                    margin:0px;font-size:15px">
                                                Heading
                                            </h4>
                                        </td>
                                        <td style="width: 20%;">
                                            <h4 style="padding: 10px 10px;border: 0px solid #ddd;
                                                border-bottom: none;background: #f8f8f8;margin:0px;
                                                font-size:15px;">
                                                Description
                                            </h4>
                                        </td>
                                    </tr>
                                </table>
                                <ul role="listbox" id="assets" class= "assets" style="padding:0;list-style-type: none;
                                    position: relative;margin: 0;background: rgb(255, 255, 255);min-height:350px;
                                    height:350px;box-shadow:none;"> ` 
                    var k = 0
                    var morebtn = ""
                    if(list_name.length > 20){
                        morebtn = `
                            <button class="btn btn-default btn-xs" style="float:right;background-color: #ccc;
                                    margin: 8px;" data-fieldtype="Button" data-fieldname="more_btn" 
                                    onclick="load_more_items($(this))">
                                Load more...
                            </button>`
                    }
                    $.each(list_name, function (i, v) {
                        if (v[c.link_name]) {
                            k += 1
                            if (v[c.link_name] == cur_frm.doc.return_policy) {
                                var desc = v["description"];
                                drp_html += `
                                    <li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;border-radius:0;">
                                        <a style="display: none;">
                                            <strong>${v[c.link_name]}</strong>
                                        </a>
                                        <label class="switch" style="float:right; width: 60px; margin:0px; cursor:pointer;">
                                            <button class="btn btn-xs btn-danger" name="vehicle1" value="0" id="${v[c.link_name]}"
                                                data-doctype="${c.doctype}" data-child="${c.is_child}" data-reference_doc="${c.reference_doc}" 
                                                data-reference_fields="${c.reference_fields}" data-search_fields="${c.search_fields}" 
                                                data-child_link="${c.child_tab_link}" data-tab_html_field="${c.tab_html_field}" btn-action="Remove" 
                                                onclick="selected_returnpolicy($(this))">Remove
                                            </button>
                                        </label> 
                                        <table style="width: 90%;">
                                            <tr>
                                                <td style="width: 9%;">${v["heading"]}</td>
                                                <td style="width: 20%;padding-left: 10px;">
                                                    ${desc}
                                                </td>
                                            </tr>
                                        </table>
                                    </li> `
                            }
                            else{
                                var desc = v["description"];
                                drp_html += `
                                    <li style="display: block; border-bottom: 1px solid #dfdfdf; 
                                        cursor:auto;border-radius:0;">
                                        <a style="display: none;">
                                            <strong>${v[c.link_name]}</strong>
                                        </a>
                                        <label class="switch" style="float:right;width: 60px; margin:0px; cursor:pointer;">
                                            <button class="btn btn-xs btn-success" name="vehicle1" value="0" id="${v[c.link_name]}"
                                                data-doctype="${c.doctype}" data-child="${c.is_child}" data-reference_doc="${c.reference_doc}" 
                                                data-reference_fields="${c.reference_fields}" data-search_fields="${c.search_fields}" 
                                                data-child_link="${c.child_tab_link}" data-tab_html_field="${c.tab_html_field}" 
                                                btn-action="add" onclick="selected_returnpolicy($(this))">
                                                Select
                                            </button>
                                        </label> 
                                        <table style="width: 90%;">
                                            <tr>
                                                <td style="width: 9%;">${v["heading"]}</td>
                                                <td style="width: 20%;padding-left: 10px;">${desc}</td>
                                            </tr>
                                        </table>
                                    </li>`
                            }
                        } 
                        else {
                            drp_html += '<li></li>';
                        }
                    })
                    drp_html += morebtn
                    drp_html += `       </ul>
                                    </div>
                                </div>`;
                   if(cur_dialog){
                        if(cur_dialog.fields_dict[c.tab_html_field].$wrapper){
                            cur_dialog.fields_dict[c.tab_html_field].$wrapper.empty();
                        }
                        cur_dialog.fields_dict[c.tab_html_field].$wrapper.append(drp_html);
                        cur_dialog.get_field(c.tab_html_field).refresh();
                   }
                }
            })
        });
    },
    get_all_category_list: function (frm) {
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.get_all_category_list',
            args: {},
            async: false,
            callback: function (data) {
                if (data.message) {
                    frm.category_list = data.message;
                }
            }
        })
    },
    generate_attribute_image_html: function (frm, child_doctype, child_name, attribute_info) {
        frappe.call({
            method: 'go1_commerce.go1_commerce.v2.product.get_file_uploaded_imagelist',
            args: {
                child_name: child_name,
                child_doctype: child_doctype,
            },
            async: false,
            callback: function (data) {
                let html = `
                    <div class="uploadFiles">
                        <div class="title" style="font-size: 14px;font-weight:600">Uploaded Files
                            <button id="saveImages" class="btn btn-primary" style="float:right;
                                margin-top: -4px;">Save
                            </button>
                        </div>
                        <ul id="sortable" style="margin-top:20px;padding-left:0">`
                $.each(data.message, function (i, j) {
                    let checked = "";
                    if (j.is_primary == 1){
                        checked = 'checked="checked"'
                    }
                    html += `
                        <li data-id="${j.name}" class="image-element" style="list-style:none; 
                                    margin-bottom: 10px;">
                            <div class="row">
                                <div class="col-md-2 ">
                                    <img src="${j.thumbnail}" style="max-height:120px"/>
                                </div>
                                <div class="col-md-7 img-name">
                                    <div class="imageName">${j.title}</div>
                                    <div class="editImage" style="display:none;">
                                        <div>
                                            <input type="text" name="image_name" placeholder="Image Alternate Text" value="${j.title}" />
                                        </div>
                                        <div>
                                            <label style="font-weight:400;font-size:12px;">
                                                <input type="checkbox" data-id="${j.name}" name="is_primary"
                                                     ${checked}/> 
                                            <span>Mark as Primary?</span></label>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3 img-name">
                                    <a style="background-color:var(--bg-green);color:var(--text-on-green);
                                            padding:5px 8px 5px 10px;border-radius:5px;margin-right:10px;
                                            float:right;" class="img-edit" data-id="${j.name}" 
                                            data-parentdoc="${j.parenttype}" data-parent="${j.parent}">
                                        <span class="fa fa-edit"></span>
                                    </a>
                                    <a style="background-color:var(--bg-orange);color:var(--text-on-orange);
                                            padding:5px 10px;border-radius:5px;float:right;" class="img-close" 
                                            data-id="${j.name}" data-parentdoc="${j.parenttype}" data-parent="${j.parent}">
                                        <span class="fa fa-trash"></span>
                                    </a>
                                </div>
                            </div>
                        </li>`
                })
                html += '</ul></div>';
                frm.files_html = html;
            }
        });
    },
    image_upload: function (frm, link_doctype, link_name, parentfield, doctype, child_docname) {
        localStorage.setItem("upload_tab", "Product Image");
        localStorage.setItem('randomuppy', ' ');
        let imgDialog;
        let randomuppy = Math.random() * 100
        localStorage.setItem('randomuppy', parseInt(randomuppy))
        let template = "<div id='drag-drop-area" + parseInt(randomuppy) + "'><div class='loader'>Loading.....</div></div>";
        imgDialog = new frappe.ui.Dialog({
            title: __('Attachments'),
            fields: [{
                fieldtype: 'HTML',
                fieldname: 'files_list',
                options: frm.files_html
            },
            {
                fieldtype: 'Column Break',
                fieldname: 'clb'
            },
            {
                fieldtype: 'HTML',
                fieldname: 'uploader',
                options: template
            }
            ],
            primary_action_label: __('Close')
        });
        imgDialog.show();
        imgDialog.$wrapper.find('.modal-dialog').attr("style","max-width:1000px !important");
        frappe.require("assets/go1_commerce/js/fileupload.js", function () {
            setTimeout(function () {
                $(imgDialog.$wrapper).find('.loader').remove()
                upload_files(parseInt(randomuppy), link_doctype, link_name, parentfield, doctype, child_docname)
            }, 600)
        });
        imgDialog.get_close_btn().on('click', () => {
            this.on_close && this.on_close(this.item);
        });
        frm.events.image_close_event(frm,imgDialog,child_docname)
        frm.events.save_images_event(frm,imgDialog)
        $(imgDialog.$wrapper).find('.img-edit').click(function () {
            let me = this;
            let imgid = $(me).attr("data-id");
            $(imgDialog.$wrapper).find('#sortable li[data-id="' + imgid + '"]').find('.imageName').hide();
            $(imgDialog.$wrapper).find('#sortable li[data-id="' + imgid + '"]').find('.editImage').show();
        })
        $(imgDialog.$wrapper).find('div[data-fieldname="files_list"] ul').sortable({
            items: '.image-element',
            opacity: 0.7,
            distance: 30
        });
        $(imgDialog.$wrapper).find('input[name="is_primary"]').on('change', function () {
            let id = $(this).attr('data-id');
            $(imgDialog.$wrapper).find('input[name="is_primary"]').each(function () {
                if ($(this).attr('data-id') != id) {
                    $(this).removeAttr('checked')
                }
            })
        })
    },
    image_close_event(frm,imgDialog,child_docname){
        $(imgDialog.$wrapper).find('.img-close').on('click', function () {
            let me = this;
            cur_frm.imgid = $(me).attr("data-id");
            frappe.confirm(__("Do you want to delete the image?"), () => {
                let url = 'go1_commerce.go1_commerce.doctype.product.product.delete_current_img';
                if (child_docname){
                    url = 'go1_commerce.go1_commerce.v2.product.delete_current_attribute_img';
                }
                frappe.call({
                    method: url,
                    args: {
                        childname: cur_frm.imgid,
                        doctype: cur_frm.doctype,
                        docname: $(me).attr("data-parent")
                    },
                    async: false,
                    callback: function (data) {
                        $(imgDialog.$wrapper).find('li[data-id="' + cur_frm.imgid + '"]').remove()
                        $(".menu-btn-group .dropdown-menu li a").each(function () {
                            if ($(this).text() == "Reload") {
                                $(this).click();
                                frappe.show_alert(__("Image deleted !"));
                            }
                        });
                        frm.reload_doc();
                    }
                })
            });
        })
    },
    save_images_event(frm,imgDialog){
        $(imgDialog.$wrapper).find('#saveImages').click(function () {
            let length = $(imgDialog.$wrapper).find('div[data-fieldname="files_list"] ul li').length;
            if (length > 0) {
                let count = 0;
                let items_list = [];
                $(imgDialog.$wrapper).find('div[data-fieldname="files_list"] ul li').each(function () {
                    let childname = $(this).attr('data-id');
                    count = count + 1;
                    let image_url = $(this).find('img').attr('src');
                    let image_name = $(this).find('input[name="image_name"]').val();
                    let primary = $(this).find('input[name="is_primary"]:checked').val()
                    let is_primary = 0;
                    if (primary == 'on') {
                        is_primary = 1;
                        cur_frm.set_value('image', image_url)
                    }
                    frappe.model.set_value('Product Image', childname, 'idx', count)
                    cur_frm.dirty()
                    if (child_docname) {
                        items_list.push({
                            "name": childname,
                            "parent": $(this).attr('data-parent'),
                            "title": image_name,
                            "is_primary": is_primary,
                            "idx": count
                        })
                    } 
                    else {
                        if(image_name) {
                            frappe.model.set_value('Product Image', childname, 'idx', count)
                            frappe.model.set_value('Product Image', childname, 'image_name', image_name)
                            frappe.model.set_value('Product Image', childname, 'is_primary', is_primary)
                        } 
                        else{
                            frappe.throw("Please mention image name.")
                        }
                    }
                })
                if (child_docname && items_list.length>0) {
                    frappe.call({
                        method: 'go1_commerce.go1_commerce.v2.product.update_attribute_option_images',
                        args: {
                            dn: child_docname,
                            docs: JSON.stringify(items_list)
                        },
                        callback: function (r) {
                            imgDialog.hide();
                            EditAttributeOption(child_docname);
                        }
                    })
                } 
                else {
                    cur_frm.dirty();
                    cur_frm.save();
                    imgDialog.hide();
                }
            } 
            else {
                frappe.throw('Please add images to edit them')
            }
        })
    },
    video_upload: function (frm, link_doctype, link_name, parentfield, doctype, child_docname) {
        localStorage.setItem("upload_tab", "Product Image");
        localStorage.setItem('randomuppy', ' ');
        let videoDialog;
        let randomuppy = Math.random() * 100
        localStorage.setItem('randomuppy', parseInt(randomuppy))
        let template = "<div id='drag-drop-area" + parseInt(randomuppy) + "'><div class='loader'>Loading.....</div></div>";
        videoDialog = new frappe.ui.Dialog({
            title: __('Upload Video'),
            fields: [{
                fieldtype: 'HTML',
                fieldname: 'uploader',
                options: template
            }],
            primary_action_label: __('Close')
        });
        videoDialog.$wrapper.find('.modal-dialog').css("width", "780px");
        videoDialog.show();
        frappe.require("assets/go1_commerce/js/videoupload.js", function () {
            setTimeout(function () {
                $(videoDialog.$wrapper).find('.loader').remove()
                video_files(parseInt(randomuppy), link_doctype, link_name, parentfield, doctype, child_docname)
            }, 600)
        });
        videoDialog.get_close_btn().on('click', () => {
            this.on_close && this.on_close(this.item);
        });
    },
    generate_combination_image_html: function (frm, child_doctype, child_name, attribute_info) {
        frappe.call({
            method: 'go1_commerce.go1_commerce.v2.product.get_file_uploaded_imagelist',
            args: {
                child_name: child_name,
                child_doctype: child_doctype,
            },
            async: false,
            callback: function (data) {
                let html = `
                    <div class="uploadFiles">
                        <div class="title" style="font-size: 14px;font-weight:600">Uploaded Files
                            <button id="saveImages" class="btn btn-primary" style="float:right;
                                margin-top: -4px;">Save
                            </button>
                        </div>
                        <ul id="sortable" style="margin-top:20px;padding-left:0">`
                $.each(data.message, function (i, j) {
                    let checked = "";
                    if (j.is_primary == 1){
                        checked = 'checked="checked"'
                    }
                    html += `
                        <li data-id="${j.name}" class="image-element" style="list-style:none;
                                margin-bottom: 10px;">
                            <div class="row">
                                <div class="col-md-2">
                                    <img src="${j.thumbnail}" style="max-height:120px"/>
                                </div>
                                <div class="col-md-7 img-name">
                                    <div class="imageName">${j.title}</div>
                                    <div class="editImage" style="display:none;">
                                        <div>
                                            <input type="text" name="image_name" placeholder="Image Alternate Text" 
                                                value="${j.title}" />
                                        </div>
                                        <div>
                                            <label style="font-weight:400;font-size:12px;"><input type="checkbox" data-id="${j.name}" 
                                                name="is_primary" ${checked}/> 
                                            <span>Mark as Primary?</span></label>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3 img-name">
                                    <a class="img-edit" data-id="${j.name}" data-parentdoc="${j.parenttype}" 
                                            data-parent="${j.parent}">
                                        <span class="fa fa-edit"></span>
                                    </a>
                                    <a class="img-close" data-id="${j.name}"  data-parentdoc="${j.parenttype}" 
                                            data-parent="${j.parent}">
                                        <span class="fa fa-trash"></span>
                                    </a>
                                </div>
                            </div>
                        </li>`
                })
                html += '</ul></div>';
                frm.files_html = html;
            }
        });
    },
    add_combination_btn: function (frm) {
        let html = `
            <div class="row">
                <div class="col-md-6">
                    <button class="btn btn-primary" id="addSingleCombination">
                        <span class="octicon octicon-plus"></span> Add Combination
                    </button>
                </div>
                <div class="col-md-6" style="text-align:right;">
                    <button class="btn btn-danger" id="addMultipleCombination">
                        <span class="octicon octicon-three-bars"></span> Create Mutual Combination
                    </button>
                </div>
            </div>`;
        $('div[data-fieldname="add_combination"]').html(html);
        $('#addSingleCombination').click(function () {
            if (frm.doc.product_attributes && frm.doc.product_attributes.length > 0) {
                let fields = frm.events.get_attr_dialog_fields(frm)
                let attr_dialog = new frappe.ui.Dialog({
                    title: __("Attribute Combination"),
                    fields: fields
                })
                attr_dialog.show();
                frm.events.update_attr_dialog_css_and_events(attr_dialog)
                attr_dialog.set_primary_action(__("Add"), function () {
                    let values = attr_dialog.get_values();
                    let attr_comb = ''
                    let attr_id = ''
                    let attributes_json=[];
                    $(frm.all_attributes).each(function (k, v) {
                        if (v.control_type == 'Dropdown List') {
                            if (values[v.attribute_unique_name]) {
                                attr_comb += `
                                    <tr>
                                        <td>
                                            <label>${v.product_attribute}:</label>
                                        </td>
                                        <td>
                                            ${values[v.attribute_unique_name]}
                                        </td>
                                    </tr>
                                `
                                let id = v.options.find(obj => obj.option_value == values[v.attribute_unique_name])
                                attr_id += id.name + '\n';
                                attributes_json.push(id.name);
                            }
                        } 
                        else{
                            if (v.control_type == 'Checkbox List') {
                                $('input[name="item-' + v.attribute_unique_name + '"]:checked').each(function () {
                                    attr_comb += `
                                        <tr>
                                            <td>
                                                <label>${v.product_attribute}:</label>
                                            </td>
                                            <td style="padding-left:10px;">
                                                ${$(this).attr('value')}
                                            </td>
                                        </tr>
                                    `
                                    let id = v.options.find(obj => obj.option_value == $(this).attr('value'))
                                    attr_id += id.name + '\n';
                                    attributes_json.push(id.name);
                                })
                            } 
                            else if (v.control_type == 'Color Boxes') {
                                $('input[name="item-' + v.attribute_unique_name + '"]:checked').each(function () {
                                    attr_comb += `
                                        <tr>
                                            <td>
                                                <label>${v.product_attribute}:</label>
                                            </td>
                                            <td style="padding-left:10px;">
                                                ${$(this).attr('value')}
                                            </td>
                                        </tr>
                                    `
                                    let id = v.options.find(obj => obj.option_value == $(this).attr('value'))
                                    attr_id += id.name + '\n';
                                    attributes_json.push(id.name);
                                })
                            } 
                            else {
                                let val = $(`input[name="item-${v.attribute_unique_name}"]:checked`).val();
                                attr_comb += `
                                        <tr>
                                            <td>
                                                <label>${v.product_attribute}:</label>
                                            </td>
                                            <td style="padding-left:10px;">
                                                ${val}
                                            </td>
                                        </tr>
                                    `
                                let id = v.options.find(obj => obj.option_value == val)
                                attr_id += id.name + '\n';
                                attributes_json.push(id.name);
                            }
                        }
            
                    })
                    let check = frm.doc.variant_combination.find(ob => ob.attribute_id == attr_id);
                    if (check) {
                        frappe.throw('This combination of attributes already exists')
                    }
                    let row = frappe.model.add_child(frm.doc, "Product Variant Combination", "variant_combination");
                    row.attribute_html = '<table>' + attr_comb + '</table>';
                    row.attribute_id = attr_id;
                    row.attributes_json = JSON.stringify(attributes_json);
                    row.stock = values.stock;
                    row.price = values.price;
                    row.weight = values.weight;
                    let image_html = ''
                    let color_html = ''
                    $('div[data-fieldname="pictures"]').find('.attributeImages li').each(function () {
                        if ($(this).attr('class') == 'active')
                            image_html += $(this).find('img').attr('src') + '\n';
                    })
                    $('div[data-fieldname="colors"]').find('.attributeColors li').each(function () {
                        if ($(this).attr('class') == 'active')
                            color_html += $(this).find('span').attr('data-id') + '\n';
                    })
                    row.image = image_html;
                    cur_frm.refresh_field("variant_combination");
                    cur_frm.save();
                    attr_dialog.refresh();
                    attr_dialog.hide();
                })
            } 
            else {
                frappe.throw('Please add attributes before creating its combination')
            }
        })

        $('#addMultipleCombination').click(function () {
            if (frm.doc.product_attributes && frm.doc.product_attributes.length > 0) {
                if (frm.doc.product_attributes[frm.doc.product_attributes.length - 1].__islocal == 1) {
                    frappe.throw("Please save your document to create the combinations")
                }
                frappe.confirm(
                    'Would you like to combine all attributes? Existing combinations will be deleted!',
                    function () {
                        if (frm.all_attributes) {
                            frappe.call({
                                method: 'go1_commerce.go1_commerce.doctype.product.product.create_variant_combinations',
                                args: {
                                    attributes: frm.all_attributes
                                },
                                callback: function (r) {
                                    if (r.message) {
                                        cur_frm.set_value('variant_combination', [])
                                        $(r.message).each(function (k, v) {
                                            create_attribute_combination(frm, v);
                                        })
                                        cur_frm.refresh_field("variant_combination");
                                        cur_frm.save();
                                    }
                                    else{
                                        frappe.msgprint("Something went wrong.!")
                                    }
                                }
                            })
                        }
                    }
                )
            } 
            else {
                frappe.throw('Please add attributes before creating its combination')
            }
        })
        frm.trigger('get_all_attributes_and_options')
    },
    add_product_attribute: function(frm){
        if(frm.is_new()){
            frappe.throw("Please save the product before adding variant.")
        }
        else{
            frm.possible_val = [{
                "cls": "custom-all-attribute",
                "hasimage":0,
                "imagefield":"image",
                "imagetitlefield":"attribute_name",
                "tab_html_field": "attribute_html",
                "tab_field": "attribute_json",
                "link_name": "name",
                "link_field": "product_attributes",
                "title": "Search variant here...",
                "label": "Variant Name",
                "doctype": "Product",
                "reference_doc": "Product Attribute",
                "business": cur_frm.doc.restaurant,
                "reference_fields": escape(JSON.stringify(["name", "attribute_name"])),
                "filters":JSON.stringify(cur_frm.doc.product_categories),
                "search_fields": "attribute_name",
                "reference_method": "go1_commerce.go1_commerce.doctype.product.product.get_category_attributes",
                "is_child": 0,
                "description": "Please select the variant",
                "child_tab_link": "",
                "height": "180px"
            }];
            let attributeDialog;
            var content = []
            attributeDialog = new frappe.ui.Dialog({
                title: __('Choose Variants'),
                fields: [
                {
                    label: "Add New Variant",
                    fieldtype: 'HTML',
                    fieldname: 'newvariant_html',
                    options: ''
                },
                {
                    label: "Choose Variant",
                    fieldtype: 'HTML',
                    fieldname: 'attribute_html',
                    options: ''
                },
                {
                    label: "Selected Variant",
                    fieldtype: 'Code',
                    fieldname: 'attribute_json',
                    options: '',
                    read_only: 1,
                    hidden: 1
                }
                ],
                primary_action_label: __('Close')
            });
            $.each(cur_frm.doc.product_attributes, function (i, s) {
                content.push(s.product_attribute)
            })
            attributeDialog.get_field('attribute_json').set_value(JSON.stringify(content));
            attributeDialog.get_field('attribute_json').refresh();
            attributeDialog.$wrapper.find('div[data-fieldname="newvariant_html"]').append(`
                <a class="btn btn-xs btn-primary" onclick="quick_entry_variant()" data-fieldtype="Button" 
                    data-fieldname="newvariant_btn" placeholder="" value="" style="float: left;
                    margin-top: -60px;margin-left: 140px;padding: 4px 10px;font-size: 13px;">
                    Add New Variant
                </a>`)
            attributeDialog.fields_dict.newvariant_html.$wrapper.find('a[data-fieldname="newvariant_btn"]').onclick = function () {
                quick_entry_variant(frm)
            };
            attributeDialog.show();
            setTimeout(function () {
                frm.events.build_multi_selector(frm, frm.possible_val);
            }, 1000)
            attributeDialog.set_primary_action(__('Save'), function () {
                var cat = attributeDialog.get_values();
                var cat_json = JSON.parse(cat.attribute_json)
                if (cat_json.length <= 0) {
                    frappe.throw(__('Please select any one variant.'))
                }
                else {
                    $(cat_json).each(function (k, v) {
                        var rowin = cur_frm.doc.product_attributes.findIndex(item => item.product_attribute === v);
                        if(rowin < 0){
                            let row = frappe.model.add_child(cur_frm.doc, "Product Attribute Mapping", "product_attributes");
                            row.product_attribute = v;
                            frappe.model.get_value('Product Attribute', {'name': v}, "attribute_name",function(e) {
                                row.attribute = e.attribute_name  
                            })
                            let req_dialog = new append_variant_html({
                                frm:frm,
                                idx: row.idx,
                                product_attribute: v
                            });
                        }
                    })
                    refresh_field("product_attributes");
                    frm.refresh_field('product_attributes')
                    $('div[data-fieldname="product_attributes"] .grid-footer').addClass('hidden')
                    attributeDialog.hide();
                    if (!frm.doc.__islocal){
                        cur_frm.save();
                    }
                }
            })
            attributeDialog.$wrapper.find('.modal-dialog').css("min-width", "1000px");
            attributeDialog.$wrapper.find('.modal-content').css("min-height", "575px");
        }
    },
    add_product_attributes: function (frm) {
        var on_attribute_name = ''
        let dialog_fields = [
            {
                "fieldtype": "Link",
                "fieldname": "product_attribute",
                "label": __("Product Attribute"),
                "options": "Product Attribute",
                "reqd": 1,
                "onchange": function () {
                    let val = this.get_value();
                    if (val) {
                        frappe.call({
                            method: 'frappe.client.get_value',
                            args: {
                                'doctype': "Product Attribute",
                                'filters': { 'name': val },
                                'fieldname': "attribute_name"
                            },
                            callback: function (r) {
                                if (r.message) {
                                    on_attribute_name = r.message.attribute_name
                                    $(dialog2.$wrapper).find('[data-fieldname="attribute"]').val(on_attribute_name);
                                }
                            }
                        })
                    }
                }
            },
            {
                "fieldtype": "Select", "fieldname": "is_required",
                "label": __("Is Required"), "options": ["Yes", "No"], "reqd": 0, "default": "Yes"
            },
            {
                "fieldtype": "Int", "fieldname": "display_order",
                "label": __("Display Order"), "reqd": 1
            },
            {
                "fieldtype": "Column Break", "fieldname": "cc"
            },
            {
                "fieldtype": "Data", "fieldname": "attribute", "label": __("Attribute Name"), "reqd": 0
            },
            {
                "fieldtype": "Select", "fieldname": "control_type", "label": __("Control Type"),
                "options": ["Dropdown List", "Radio Button List", "Checkbox List", "Color Boxes", "Text Box", "Table", "Multi Line Text"],
                "reqd": 1
            },
            {
                "fieldname": "min_allowed_options",
                "fieldtype": "Int",
                "label": __("Minimum Allowed Options"),
                "hidden": (frappe.boot.active_domains.includes(frappe.boot.sysdefaults.domain_constants.restaurant) ? 0 : 1),
                "depends_on": "eval:  doc.control_type == 'Checkbox List' "
            },
            {
                "fieldname": "max_allowed_options",
                "fieldtype": "Int",
                "label": __("Maximum Allowed Options"),
                "hidden": (frappe.boot.active_domains.includes(frappe.boot.sysdefaults.domain_constants.restaurant) ? 0 : 1),
                "depends_on": "eval:  doc.control_type == 'Checkbox List' "
            }
        ];
        if(frappe.boot.active_domains.includes(frappe.boot.sysdefaults.domain_constants.restaurant)) {
            dialog_fields.push({'fieldtype': 'Column Break', 'fieldname': 'cb_2'});
            dialog_fields.push({
                "fieldtype": "Link", "label": __("Parent Attribute"),
                "fieldname": "parent_attribute", "reqd": 0, "options": "Product Attribute",
                "onchange": function () {
                    let val = this.get_value();
                    if (val) {
                        frappe.call({
                            method: 'frappe.client.get_value',
                            args: {
                                'doctype': "Product Attribute",
                                'filters': { 'name': val },
                                'fieldname': "attribute_name"
                            },
                            callback: function (r) {
                                if (r.message) {
                                    on_attribute_name = r.message.attribute_name
                                    $(dialog2.$wrapper).find('[data-fieldname="parent_attribute_name"]').val(on_attribute_name);
                                }
                            }
                        })
                    }
                }
            });
            dialog_fields.push({
                "fieldtype": "Data", "label": __("Parent Attribute Name"),
                "fieldname": "parent_attribute_name", "reqd": 0
            });
            dialog_fields.push({
                "fieldtype": "Link", "label": __("Attribute Group"),
                "fieldname": "attribute_group", "reqd": 0, "options": "Product Attribute Group",
                "onchange": function () {
                    let val = this.get_value();
                    if (val) {
                        frappe.call({
                            method: 'frappe.client.get_value',
                            args: {
                                'doctype': "Product Attribute Group",
                                'filters': { 'name': val },
                                'fieldname': "group_name"
                            },
                            callback: function (r) {
                                if (r.message) {
                                    on_attribute_name = r.message.group_name
                                    $(dialog2.$wrapper).find('[data-fieldname="group_name"]').val(on_attribute_name);
                                }
                            }
                        })
                    }
                }
            });
            dialog_fields.push({
                "fieldtype": "Data", "label": __("Attribute Group Name"),
                "fieldname": "group_name", "reqd": 0
            });
        } 
        else if(frm.catalog_settings.enable_size_chart) {
            dialog_fields.push({
                "fieldtype": "Link", "label": __("Size Chart"), "fieldname": "size_chart",
                "reqd": 0, "options": "Size Chart"
            });
        }
        let dialog2 = new frappe.ui.Dialog({
            title: __("Product Attribute"),
            fields: dialog_fields
        });
        $(dialog2.$wrapper).find('.modal-dialog').css("width", (frappe.boot.active_domains.includes(frappe.boot.sysdefaults.domain_constants.restaurant) ? "70%" : "60%"));
        dialog2.set_primary_action(__("Save"), function () {
            let values = dialog2.get_values();
            var unique_name1 = '';
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    'doctype': "Product Attribute",
                    'filters': { 'name': values.product_attribute },
                    'fieldname': "unique_name"
                },
                async:false,
                callback: function (r) {
                    if (r.message) {
                        unique_name1 = r.message.unique_name
                    }
                }
            })
            if (frm.edit_option != 1) {
                let child = frappe.model.add_child(frm.doc, "Product Attribute Mapping", "product_attributes");
                child.product_attribute = values.product_attribute;
                child.attribute = values.attribute;
                child.attribute_unique_name = unique_name1;
                child.is_required = values.is_required;
                child.control_type = values.control_type;
                child.display_order = values.display_order;
                child.max_allowed_options = values.max_allowed_options;
                child.min_allowed_options = values.min_allowed_options;
                if (values.size_chart) {
                    child.size_chart = values.size_chart;
                }
                if (values.parent_attribute) {
                    child.parent_attribute = values.parent_attribute;
                    child.parent_attribute_name = values.parent_attribute_name;
                }
                if (values.attribute_group) {
                    child.attribute_group = values.attribute_group;
                    child.group_name = values.group_name;
                }
            }
            else {
                frappe.model.set_value('Product Attribute Mapping', frm.product_attribute.name, 'product_attribute', values.product_attribute)
                frappe.model.set_value('Product Attribute Mapping', frm.product_attribute.name, 'is_required', values.is_required)
                frappe.model.set_value('Product Attribute Mapping', frm.product_attribute.name, 'control_type', values.control_type)
                frappe.model.set_value('Product Attribute Mapping', frm.product_attribute.name, 'display_order', values.display_order)
                frappe.model.set_value('Product Attribute Mapping', frm.product_attribute.name, 'attribute', values.attribute)
                frappe.model.set_value('Product Attribute Mapping', frm.product_attribute.name, 'attribute_unique_name', unique_name1)
                frappe.model.set_value('Product Attribute Mapping', frm.product_attribute.name, 'max_allowed_options', values.max_allowed_options)
                frappe.model.set_value('Product Attribute Mapping', frm.product_attribute.name, 'min_allowed_options', values.min_allowed_options)
                if (values.parent_attribute) {
                    frappe.model.set_value('Product Attribute Mapping', frm.product_attribute.name, 'parent_attribute', values.parent_attribute)
                    frappe.model.set_value('Product Attribute Mapping', frm.product_attribute.name, 'parent_attribute_name', values.parent_attribute_name)
                }
                if (values.size_chart) {
                    frappe.model.set_value('Product Attribute Mapping', frm.product_attribute.name, 'size_chart', values.size_chart)
                }
                if (values.attribute_group) {
                    frappe.model.set_value('Product Attribute Mapping', frm.product_attribute.name, 'attribute_group', values.attribute_group)
                    frappe.model.set_value('Product Attribute Mapping', frm.product_attribute.name, 'group_name', values.group_name)
                }
            }
            cur_frm.refresh_field("product_attributes");
            dialog2.hide();
            if (!frm.doc.__islocal){
                cur_frm.save();
            }
            cur_frm.trigger('product_attribute_html')
        })
        if (frm.edit_option == 1) {
            dialog2.set_value('product_attribute', frm.product_attribute.product_attribute)
            dialog2.set_value('is_required', frm.product_attribute.is_required)
            dialog2.set_value('control_type', frm.product_attribute.control_type)
            dialog2.set_value('display_order', frm.product_attribute.display_order)
            dialog2.set_value('attribute', frm.product_attribute.attribute)
            dialog2.set_value('max_allowed_options', frm.product_attribute.max_allowed_options);
            dialog2.set_value('min_allowed_options', frm.product_attribute.min_allowed_options);
            if (frm.product_attribute.size_chart) {
                dialog2.set_value('size_chart', frm.product_attribute.size_chart)
            }
            if (frm.product_attribute.parent_attribute) {
                dialog2.set_value('parent_attribute', frm.product_attribute.parent_attribute)
                dialog2.set_value('parent_attribute_name', frm.product_attribute.parent_attribute_name)
            }
            if (frm.product_attribute.attribute_group) {
                dialog2.set_value('attribute_group', frm.product_attribute.attribute_group)
                dialog2.set_value('group_name', frm.product_attribute.group_name)
            }
            dialog2.refresh();
        }
        dialog2.show();
    },
    update_attr_dialog_css_and_events(attr_dialog){
        attr_dialog.$wrapper.find('.modal-dialog').css("width", "1030px");
        attr_dialog.$wrapper.find('.attributeImages li').click(function () {
            let cls = $(this).attr('class');
            if (cls == 'active'){
                $(this).removeClass('active');
            }
            else{
                $(this).addClass('active')
            }
        })
        attr_dialog.$wrapper.find('.attributeColors li').click(function () {
            let cls = $(this).attr('class');
            if (cls == 'active'){
                $(this).removeClass('active');
            }
            else{
                $(this).addClass('active')
            }
        })
    },
    get_attr_dialog_fields(frm){
        let fields = [];
        let image = false;
        let attribute_color = false;
        let img_html = '';
        let color_html = '';
        if (frm.all_attributes) {
            $(frm.all_attributes).each(function (k, v) {
                let f = {};
                f.fieldname = v.attribute_unique_name;
                f.label = v.product_attribute;
                let options = '';
                let control_type = ''
                let reqd = 0;
                if (v.control_type == 'Radio Button List' || v.control_type == 'Color Boxes')
                    control_type = 'radio'
                else if (v.control_type == 'Checkbox List')
                    control_type = 'checkbox'
                if (v.is_required == 'Yes')
                    reqd = 1;
                $(v.options).each(function (i, j) {
                    if (v.control_type == 'Dropdown List') {
                        options += '\n' + j.option_value;
                    } 
                    else{
                        options += `
                            <li>
                                <label>
                                    <input type="${control_type}" name="item-${v.attribute_unique_name}" value="${j.option_value}" /> 
                                    ${j.option_value}
                                </label>
                            </li> `
                    }
                    if(j.image) {
                        image = true;
                        img_html += `
                            <li>
                                <img src="${j.image}" style="height:75px;" />
                            </li>`
                    }
                    if (j.attribute_color != "-" && j.attribute_color != null && j.attribute_color != '') {
                        attribute_color = true;
                        color_html += `
                            <li>
                                <span class="choice-box-content tooltip-toggle" title="${j.option_value}" data-id="${j.attribute_color}" >
                                    <span class="choice-box-element" style="background-color:${j.attribute_color}></span>
                                </span>
                            </li>
                        ` 
                    }
                })
                if (v.control_type == 'Dropdown List') {
                    f.fieldtype = 'Select';
                    f.options = options;
                    f.reqd = reqd;
                } else {
                    f.fieldtype = 'HTML';
                    f.options = `
                        <div>
                            <label>${f.label}</label>
                            <ul class="attributeOptions">${options}</ul>
                        </div>
                    `
                }
                fields.push(f)
            })
        }
        if (image) {
            fields.push({
                "fieldname": "pictures",
                "fieldtype": "HTML",
                "options": `
                    <div>
                        <label>Pictures</label>
                        <ul class='attributeImages'>${img_html}</ul>
                    </div>
                `
            })
        }
        if (attribute_color != false) {
            fields.push({
                "fieldname": "colors",
                "fieldtype": "HTML",
                "options": `
                    <div>
                        <label>Colors</label>
                        <ul class='attributeColors'>${color_html}</ul>
                    </div>
                `
            })
        }
        fields.push({
            "fieldtype": "Column Break",
            "fieldname": "sc"
            }, 
            {
                "fieldname": "stock",
                "fieldtype": "Float",
                "label": "Stock Qty",
                "reqd": 1
            },
            {
                "fieldname": "price",
                "fieldtype": "Currency",
                "label": "Price"
            },
            {
                "fieldname": "weight",
                "fieldtype": "Float",
                "label": "Weight"
            })
        return fields
    },
    get_all_attributes_and_options: function (frm) {
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.get_product_attributes_with_options',
            args: {
                product: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    frm.all_attributes = r.message;
                }
            }
        })
    },
    get_edit_option_fields(frm){
        let dialog_fields = [
            { "fieldtype": "Section Break", "fieldname": "sec1", "hidden": 1, "label":"Option Detail" },
            { "fieldtype": "Data", "label": __("Option"), "fieldname": "option_value", "reqd": 1 },
            { "fieldtype": "Int", "label": __("Display Order"), "fieldname": "display_order_no", "reqd": 1 },
            { "fieldtype": "Float", "label": __("Price Adjustment"), "fieldname": "price_adjustment", "reqd": 0, "hidden":1 },
            { "fieldtype": "Column Break", "fieldname": "cc" },
            { "fieldtype": "Data","hidden":1, "label": __("Product Title"), "fieldname": "product_title" },
            { "fieldname": "is_pre_selected", "fieldtype": "Check", "label": "Is Pre Selected" },
            { "fieldname": "disable", "fieldtype": "Check", "label": "Disable" },
        ]
        dialog_fields.push({
            "fieldtype": "Float",
            "label": __("Weight Adjustment"),
            "fieldname": "weight_adjustment",
            "reqd": 0,
            "hidden":1
        });
        if(frm.attribute.control_type !="Color Boxes"){
            dialog_fields.push({
                "fieldtype": "Color",
                "label": __("Color"),
                "description": "Color is applied based on 'Control Type(Color Boxes)' field.",
                "fieldname": "attribute_color",
                "hidden":1
            });
        }
        if(frm.attribute.control_type =="Color Boxes"){
            dialog_fields.push({
                "fieldtype": "Color",
                "label": __("Color"),
                "description": "Color is applied based on 'Control Type(Color Boxes)' field.",
                "fieldname": "attribute_color",
            });
        }
        dialog_fields.push( { "fieldtype": "Section Break", "fieldname": "sec01", "hidden": 1, "label":"Image" })
        dialog_fields.push({
            "fieldtype": "Button",
            "label": __("Add / Edit Image"),
            "fieldname": "add_attribute_image"
        });
        dialog_fields.push({
            'fieldname': 'attribute_image_html',
            'fieldtype': 'HTML'
        });
        $.merge(dialog_fields, [
                { "fieldtype": "Section Break", "fieldname": "sec02", "hidden": 1, "label":"Video" },
            { "fieldtype": "Button", "label": __("Add Video"), "fieldname": "add_attribute_video"},
            { "fieldtype": "Button", "label": __("Upload Video"), "fieldname": "upload_attribute_video" },
            { 'fieldname': 'attribute_video', 'fieldtype': 'HTML' }
        ])    
        $.merge(dialog_fields, [
             { "fieldtype": "Section Break", "fieldname": "sec000", "hidden": 1 },
            { "fieldtype": "Button", "label": __("Save"), "fieldname": "update1" },
            { "fieldtype": "Button", "label": __("Clear"), "fieldname": "clear", "hidden":1},
      
        ])
        $.merge(dialog_fields, [
            { "fieldtype": "Section Break", "fieldname": "sc" },
            { 'fieldname': 'ht', 'fieldtype': 'HTML' }
        ])
        return dialog_fields
    },
    update_edit_option_list_css(frm,dialog){
        $(dialog.$wrapper).find('.modal-dialog').css("width", "992px");
        $(dialog.$wrapper).find('.modal-dialog').css("max-width", "992px");
        dialog.$wrapper.find('.modal-content').css('height', 'auto')
        dialog.fields_dict.update1.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
        dialog.fields_dict.update1.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
        if($(window).width() < 992){
            $(dialog.$wrapper).find('.modal-dialog').css("width", "100%");
        }
        if(dialog.fields_dict.add_attribute_image){
            dialog.fields_dict.add_attribute_image.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
        }
        if(dialog.fields_dict.add_attribute_video){
            dialog.fields_dict.add_attribute_video.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
        }
        if(dialog.fields_dict.upload_attribute_video){
            dialog.fields_dict.upload_attribute_video.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
        } 
        if (frm.attribute.parent_attribute != undefined) {
            frappe.call({
                method: "go1_commerce.go1_commerce.doctype.product.product.get_parent_product_attribute_options",
                args: {
                    "attribute": frm.attribute.parent_attribute,
                    "product": frm.docname,
                },
                callback: function (r) {
                    if (r.message != undefined) {
                        var options = r.message;
                        var parent_options_html = '<option></option>';
                        if (options.length > 0) {
                            for (var i = 0; i < options.length; i++) {
                                parent_options_html += `<option value="${options[i].option_value}">${options[i].option_value}</option>`;
                            }
                            $(dialog.$wrapper).find('[data-fieldname="parent_option"]').find("select").html(parent_options_html);
                        }
                    }
                }
            });
        }
    },
    update_edit_option_click_events(frm,dialog){
        if(dialog.fields_dict.add_attribute_image){
            dialog.fields_dict.add_attribute_image.input.onclick = function () {
                var attributeId = $("#hdnAttributeOptionid").val()
                if (attributeId) {
                    let attribute_info;
                    if (frm.attribute_options) {
                        attribute_info = frm.attribute_options.find(obj => obj.name == attributeId);
                    }
                    localStorage.setItem('randomuppy', ' ');
                    frm.events.generate_attribute_image_html(frm, 'Product Attribute Option', attributeId, attribute_info)
                    frm.events.image_upload(frm, 'Product Attribute Option', attributeId, "attribute_images", 'Product Attribute Option', attributeId)
                } else {
                    frappe.throw('Please save the document and then try uploading images')
                }
            }
        }
        if(dialog.fields_dict.add_attribute_video){
            dialog.fields_dict.add_attribute_video.input.onclick = function () {
                var attributeId1 = $("#hdnAttributeOptionid").val()
                if (attributeId1) {
                    save_attribute_video(attributeId1)
                } else {
                    frappe.throw('Please save the document and then try add video id')
                }
            }
        }
        if(dialog.fields_dict.upload_attribute_video){
            dialog.fields_dict.upload_attribute_video.input.onclick = function () {
                var attributeId = $("#hdnAttributeOptionid").val()
                if (attributeId) {
                    localStorage.setItem('randomuppy', ' ');
                    frm.events.video_upload(frm, 'Product Attribute Option', attributeId, "youtube_video_id", 'Product Attribute Option Video', attributeId)
                } else {
                    frappe.throw('Please save the document and then try uploading images')
                }
            }
        } 
        dialog.fields_dict.update1.input.onclick = function () {
            let values = dialog.get_values();
            var option_value = values.option_value;
            var display_order = values.display_order_no;
            var price_adjustment = 0
            var parent_option = values.parent_option;
            var disable = values.disable;
            var available_datetime = values.available_datetime;
            var weight_adjustment = 0
            if (values.weight_adjustment != undefined && values.weight_adjustment != '') {
                weight_adjustment = values.weight_adjustment;
            }
            var product_title = '-'
            if (values.product_title != undefined && values.product_title != '') {
                product_title = values.product_title;
            }
            var attribute_color = '-';
            if (values.attribute_color != undefined && values.attribute_color != '') {
                attribute_color = values.attribute_color;
            }
            var image = values.image;
            var pre_selected = values.is_pre_selected;
            if(dialog.fields_dict.attribute_image_html)
                dialog.fields_dict.attribute_image_html.$wrapper.empty();
            if(dialog.fields_dict.attribute_video)
                dialog.fields_dict.attribute_video.$wrapper.empty();
            dialog.set_value('is_pre_selected', 0);
            if (option_value == "") {
                frappe.msgprint("Option Value is required");
                return false;
            }
            if(image && image.indexOf('/files/') == -1) {
                let image_url = undefined;
                frappe.run_serially([
                    () => {
                        image_url = upload_attribute_image(image, frm.docname, frm.attribute.product_attribute, image_url, pre_selected);
                    },
                    () => {
                        saveattributeoption(frm.docname, frm.attribute.product_attribute, option_value, display_order, price_adjustment, weight_adjustment, image_url, pre_selected, attribute_color, product_title, parent_option, disable, available_datetime);
                    }
                ])
            }
            else {
                let image = $("div[data-fieldname='image']").find('.attached-file-link').text();
                saveattributeoption(frm.docname, frm.attribute.product_attribute, option_value, display_order, price_adjustment, weight_adjustment, image, pre_selected, attribute_color, product_title, parent_option, disable, available_datetime);
            }
        }
    },
    edit_option_list: function (frm) {
        $("#OptionsData").parent().parent().parent().parent().parent().parent().parent().parent().parent().parent().parent().remove();
        let dialog_fields = frm.events.get_edit_option_fields(frm)
        dialog = new frappe.ui.Dialog({
            title: __("Attribute Options"),
            fields: dialog_fields
        });
        frm.events.update_edit_option_list_css(frm,dialog)       
        frm.events.update_edit_option_click_events(frm,dialog)       
        $(dialog.$wrapper).find('div[data-fieldname="image"]').find('.img-container').next().
            click(function () {
                $('div[data-fieldname="image"]').find('.img-container').find('img').attr('src', '');
        });
        $(dialog.$wrapper).find('div[data-fieldname="image"]').find('.attached-file a.close').
            on("click", function () {
                let option_id = $('#hdnAttributeOptionid').val();
                let image = $("#tr-" + option_id).attr('data-image')
                if (image != undefined && image != null && image != 'null' && image != 0 
                    && image != "") {
                        $("#tr-" + option_id).attr('data-image', '')
                        $("div[data-fieldname='image']").find('.attached-file-link').text("");
                        dialog.get_field('image').set_value("");
                        dialog.get_field('image').refresh();
                }
        })
        $(dialog.$wrapper).find('input[data-fieldname="is_pre_selected"]').on('change', function () {
            let id = $('#hdnAttributeOptionid').val();
            $('div[data-fieldname="ht"]').find('table tbody tr').each(function () {
                if ($(this).attr('id').split("-")[1] != id) {
                    $(this).find('td[id="pre_selected"]').text('0');
                }
            })
        })
        $(dialog.$wrapper).addClass('attributeImage');
        if (frm.attribute.product_attribute && frm.docname) {
            var html = `<input type="hidden" id="hdnAttributeOptionid"/>
                            <input type="hidden" id="hdnSelectedDoc" value = "${frm.attribute.product_attribute}"/>
                            <input type="hidden" id="hdnSelectedId" value="${frm.attribute.name}"/>
                            <table class="table table-bordered" id="OptionsData">
                                <thead style="background: #F7FAFC;">
                                    <tr>
                                        <th style="width:150px">Option</th>
                                        <th>Display Order</th>
                                        <th style="display:none;">Price Adjustment</th>
                                        <th style="display:none">Weight Adjustment</th>
                                        <th style="display:none">Color</th>
                                        <th>Is Pre Selected</th>
                                        <th style="display:none">Product Title</th>
                                        <th>Disable</th>
                                        <th style="width:110px">Actions</th>
                                    </tr>
                                </thead>            
                    ` 
            frappe.call({
                method: "go1_commerce.go1_commerce.doctype.product.product.get_product_attribute_options",
                args: {
                    "attribute": frm.attribute.product_attribute,
                    "product": frm.docname,
                    "attribute_id": frm.attribute.name

                },
                callback: function (r) {
                    html += '<tbody>';
                    if (r.message != undefined) {
                        frm.attribute_options = r.message;
                        $.each(r.message, function (i, d) {
                            html += `
                                <tr id="tr-${d.name}" data-image="${d.image}">
                                    <td>${d.option_value}</td>
                                    <td>${d.display_order}</td> 
                                    <td style="display:none">${d.price_adjustment}</td>
                                    <td style="display:none">${d.weight_adjustment}</td>
                                    <td style="text-align:center;display:none;">${d.attribute_color}</td>
                                    <td id = "pre_selected" data-preselection="${d.is_pre_selected}">
                                        ${d.is_pre_selected}
                                    </td>
                                    <td style="display:none" width="20%">
                                        <div style="width: 165px;overflow: hidden;text-overflow: ellipsis;
                                                white-space: nowrap;">${d.product_title}
                                        </div>
                                    </td>
                                    <td id="disable">${d.disable}</td>
                                    <td width="20%">
                                        <button class="btn btn-xs btn-success editbtn"  data-fieldtype="Button" 
                                                onclick=EditAttributeOptions("${d.name}")>Edit
                                        </button>
                                        <a class="btn btn-xs btn-danger" style="margin-left:10px;" 
                                                onclick=DeleteAttributeOption("${d.name}")>Delete
                                        </a>
                                    </td>
                                </tr>
                            `;
                        });
                    } 
                    else {
                        html += '<tr><td colspan="6" align="center">No Records Found.</td></tr>';
                    }
                    html += `   </tbody>
                            </table>`;
                    dialog.fields_dict.ht.$wrapper.html(html);
                    dialog.show();
                    $("button[data-fieldname='update1']").attr("style", 
                            `padding: 5px 10px;font-size: 12px;line-height: 1.5;border-radius: 3px;
                            color: #fff;background-color: #1d4da5;border-color: #1d4da5;`);
                    $("button[data-fieldname='clear']").removeAttr("class");
                    $("button[data-fieldname='clear']").attr("class", "btn btn-xs btn-danger");
                    $("button[data-fieldname='clear']").attr("style", `padding: 5px 10px;font-size: 12px;line-height: 1.5;
                            border-radius: 3px;color: #fff;margin-left: 10px;position: absolute;bottom: 5.6%;
                            left: 60px;margin-top: -19px;`)

                }
            })
        }
    },
    get_edit_opts_dialog_fields(frm){
        let dialog_fields = [
            { "fieldtype": "Section Break", "fieldname": "sec1", "hidden": 0, "label":"Option Detail" },
            { "fieldtype": "Data", "label": __("Option"), "fieldname": "option_value", "reqd": 1 },
            { "fieldtype": "Int", "label": __("Display Order"), "fieldname": "display_order_no", "reqd": 1 },
            { "fieldtype": "Float", "label": __("Price Adjustment"), "fieldname": "price_adjustment", "reqd": 1 },
            { "fieldtype": "Column Break", "fieldname": "cc" },
            { "fieldtype": "Data", "label": __("Product Title"), "fieldname": "product_title" },
            { "fieldname": "is_pre_selected", "fieldtype": "Check", "label": "Is Pre Selected" },
            { "fieldname": "disable", "fieldtype": "Check", "label": "Disable" },
        ]
        dialog_fields.push({
            "fieldtype": "Float",
            "label": __("Weight Adjustment"),
            "fieldname": "weight_adjustment",
            "reqd": 0
        });
        dialog_fields.push({
            "fieldtype": "Color",
            "label": __("Color"),
            "description": "Color is applied based on 'Control Type(Color Boxes)' field.",
            "fieldname": "attribute_color"
        });
        dialog_fields.push({ "fieldname": "available_datetime", "fieldtype": "Datetime", "label": "Next Available Date & Time", "depends_on": "eval: ((doc.disable==1))" });
        dialog_fields.push( { "fieldtype": "Section Break", "fieldname": "sec01", "hidden": 0, "label":"Image" })
           
        dialog_fields.push({
            "fieldtype": "Button",
            "label": __("Add / Edit Image"),
            "fieldname": "add_attribute_image"
        });
        dialog_fields.push({
        'fieldname': 'attribute_image_html',
        'fieldtype': 'HTML'
        });
        if(frm.catalog_settings.enable_product_video){
            $.merge(dialog_fields, [
                 { "fieldtype": "Section Break", "fieldname": "sec02", "hidden": 0, "label":"Video" },
                { "fieldtype": "Button", "label": __("Add Video"), "fieldname": "add_attribute_video"},
                { "fieldtype": "Button", "label": __("Upload Video"), "fieldname": "upload_attribute_video" },
                { 'fieldname': 'attribute_video', 'fieldtype': 'HTML' }
            ])    
        }
        $.merge(dialog_fields, [
            { "fieldtype": "Section Break", "fieldname": "sec000", "hidden": 0 },
            { "fieldtype": "Column Break", "fieldname": "c1" },
            { "fieldtype": "Column Break", "fieldname": "c1" },
            { "fieldtype": "Column Break", "fieldname": "c1" },
            { "fieldtype": "Column Break", "fieldname": "c1" },
            { "fieldtype": "Column Break", "fieldname": "c1" },
            { "fieldtype": "Column Break", "fieldname": "c1" },
            { "fieldtype": "Column Break", "fieldname": "c1" },
            { "fieldtype": "Column Break", "fieldname": "c1" },
            { "fieldtype": "Column Break", "fieldname": "c1" },
            { "fieldtype": "Column Break", "fieldname": "c1" },
            { "fieldtype": "Column Break", "fieldname": "c1" },
            { "fieldtype": "Button", "label": __("Save"), "fieldname": "update1" },
            { "fieldtype": "Column Break", "fieldname": "c1" },
            { "fieldtype": "Button", "label": __("Clear"), "fieldname": "clear" },
        ])
        $.merge(dialog_fields, [
            { "fieldtype": "Section Break", "fieldname": "sc" },
            { 'fieldname': 'ht', 'fieldtype': 'HTML' }
        ])
        return dialog_fields
    },
    update_edit_opts_dialog_css_properties(frm,dialog){
        $(dialog.$wrapper).find('.modal-dialog').css("width", "992px");
        dialog.$wrapper.find('.modal-content').css('height', 'auto')
        dialog.fields_dict.clear.$wrapper.css('position', 'relative');
        dialog.fields_dict.update1.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
        dialog.fields_dict.clear.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm attr-del');
        dialog.fields_dict.update1.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
        dialog.fields_dict.clear.$wrapper.find('button').removeClass('btn-default').addClass('btn-danger');
        if(dialog.fields_dict.add_attribute_image){
            dialog.fields_dict.add_attribute_image.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
            dialog.fields_dict.add_attribute_image.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
        }
        if(dialog.fields_dict.add_attribute_video){
            dialog.fields_dict.add_attribute_video.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
            dialog.fields_dict.add_attribute_video.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
        }
        if(dialog.fields_dict.upload_attribute_video){
            dialog.fields_dict.upload_attribute_video.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
            dialog.fields_dict.upload_attribute_video.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
        }
        if (frm.attribute.parent_attribute != undefined) {
            frappe.call({
                method: "go1_commerce.go1_commerce.doctype.product.product.get_parent_product_attribute_options",
                args: {
                    "attribute": frm.attribute.parent_attribute,
                    "product": frm.docname,
                },
                callback: function (r) {
                    if (r.message != undefined) {
                        var options = r.message;
                        var parent_options_html = '<option></option>';
                        if (options.length > 0) {
                            for (var i = 0; i < options.length; i++) {
                                parent_options_html += `<option value="${options[i].option_value}">${options[i].option_value}</option>`;
                            }
                            $(dialog.$wrapper).find('[data-fieldname="parent_option"]').find("select").html(parent_options_html);
                        }
                    }
                }
            });
        }        
    },
    update_edit_opts_click_events(frm,dialog){
        if(dialog.fields_dict.add_attribute_image){
            dialog.fields_dict.add_attribute_image.input.onclick = function () {
                var attributeId = $("#hdnAttributeOptionid").val()
                if(attributeId) {
                    let attribute_info;
                    if(frm.attribute_options) {
                        attribute_info = frm.attribute_options.find(obj => obj.name == attributeId);
                    }
                    localStorage.setItem('randomuppy', ' ');
                    frm.events.generate_attribute_image_html(frm, 'Product Attribute Option', attributeId, attribute_info)
                    frm.events.image_upload(frm, 'Product Attribute Option', attributeId, "attribute_images", 'Product Attribute Option', attributeId)
                } 
                else{
                    frappe.throw('Please save the document and then try uploading images')
                }
            }
        }
        if(dialog.fields_dict.add_attribute_video){
            dialog.fields_dict.add_attribute_video.input.onclick = function () {
                var attributeId1 = $("#hdnAttributeOptionid").val()
                if(attributeId1) {
                    save_attribute_video(attributeId1)
                } 
                else {
                    frappe.throw('Please save the document and then try add video id')
                }
            }
        }
        if(dialog.fields_dict.upload_attribute_video){
            dialog.fields_dict.upload_attribute_video.input.onclick = function () {
                var attributeId = $("#hdnAttributeOptionid").val()
                if(attributeId) {
                    localStorage.setItem('randomuppy', ' ');
                    frm.events.video_upload(frm, 'Product Attribute Option', attributeId, "youtube_video_id", 'Product Attribute Option Video', attributeId)
                } 
                else {
                    frappe.throw('Please save the document and then try uploading images')
                }
            }
        }
        dialog.fields_dict.update1.input.onclick = function () {
            let values = dialog.get_values();
            var option_value = values.option_value;
            var display_order = values.display_order_no;
            var price_adjustment = values.price_adjustment;
            var parent_option = values.parent_option;
            var disable = values.disable;
            var available_datetime = values.available_datetime;
            var weight_adjustment = 0
            if (values.weight_adjustment != undefined && values.weight_adjustment != '') {
                weight_adjustment = values.weight_adjustment;
            }
            var product_title = '-'
            if (values.product_title != undefined && values.product_title != '') {
                product_title = values.product_title;
            }
            var attribute_color = '-';
            if (values.attribute_color != undefined && values.attribute_color != '') {
                attribute_color = values.attribute_color;
            }
            var image = values.image;
            var pre_selected = values.is_pre_selected;
            if(dialog.fields_dict.attribute_image_html)
                dialog.fields_dict.attribute_image_html.$wrapper.empty();
            if(dialog.fields_dict.attribute_video)
                dialog.fields_dict.attribute_video.$wrapper.empty();
            dialog.set_value('is_pre_selected', 0);
            if (image && image.indexOf('/files/') == -1) {
                let image_url = undefined;
                frappe.run_serially([
                    () => {
                        image_url = upload_attribute_image(image, frm.docname, frm.attribute.product_attribute, image_url, pre_selected);
                    },
                    () => {
                        if (validateAttributeOptionForm()) {
                            saveattributeoption(frm.docname, frm.attribute.product_attribute, option_value, display_order, price_adjustment, weight_adjustment, image_url, pre_selected, attribute_color, product_title, parent_option, disable, available_datetime);
                        }
                    }
                ])
            }
            else{
                let image = $("div[data-fieldname='image']").find('.attached-file-link').text();
                if (validateAttributeOptionForm()) {
                    saveattributeoption(frm.docname, frm.attribute.product_attribute, option_value, display_order, price_adjustment, weight_adjustment, image, pre_selected, attribute_color, product_title, parent_option, disable, available_datetime);
                }
            }
        }
        dialog.fields_dict.clear.input.onclick = function () {
            dialog.fields_dict.attribute_image_html.$wrapper.empty();
            dialog.set_value('is_pre_selected', 0);
            dialog.set_value('option_value', '');
            dialog.set_value('display_order_no', '');
            dialog.set_value('price_adjustment', '');
            dialog.set_value('weight_adjustment', '');
            dialog.set_value('attribute_color', '');
            dialog.set_value('product_title', '');
            dialog.set_value('disable', 0);
            $("div[data-fieldname='image']").find('.missing-image').show();
            $("div[data-fieldname='image']").find('.img-container').hide();
            $("div[data-fieldname='image']").find('.attached-file').hide();
            $('div[data-fieldname="image"]').find('.attached-file-link').text('')
            $('div[data-fieldname="image"]').find('.img-container').find('img').attr('src', '');
            $("#hdnAttributeOptionid").val('');
            dialog.refresh()
        }
    },
    edit_options: function (frm) {
        $("#OptionsData").parent().parent().parent().parent().parent().parent().parent().parent().parent().parent().parent().remove();
        let dialog_fields = frm.events.get_edit_opts_dialog_fields(frm)
        dialog = new frappe.ui.Dialog({
            title: __("Attribute Options"),
            fields: dialog_fields
        });
        frm.events.update_edit_opts_dialog_css_properties(frm,dialog)
        frm.events.update_edit_opts_click_events(frm,dialog)
        $(dialog.$wrapper).find('div[data-fieldname="image"]').find('.img-container').next().click(function () {
            $('div[data-fieldname="image"]').find('.img-container').find('img').attr('src', '');
        });
        $(dialog.$wrapper).find('div[data-fieldname="image"]').find('.attached-file a.close').on("click", function () {
            let option_id = $('#hdnAttributeOptionid').val();
            let image = $("#tr-" + option_id).attr('data-image')
            if (image != undefined && image != null && image != 'null' && image != 0 && image != "") {
                $("#tr-" + option_id).attr('data-image', '')
                $("div[data-fieldname='image']").find('.attached-file-link').text("");
                dialog.get_field('image').set_value("");
                dialog.get_field('image').refresh();
            }
        })
        $(dialog.$wrapper).find('input[data-fieldname="is_pre_selected"]').on('change', function () {
            let id = $('#hdnAttributeOptionid').val();
            $('div[data-fieldname="ht"]').find('table tbody tr').each(function () {
                if ($(this).attr('id').split("-")[1] != id) {
                    $(this).find('td[id="pre_selected"]').text('0');
                }
            })
        })
        $(dialog.$wrapper).addClass('attributeImage');
        if (frm.attribute.product_attribute && frm.docname) {
            var html = `
                <input type="hidden" id="hdnAttributeOptionid"/>
                    <input type="hidden" id="hdnSelectedDoc" value ="${frm.attribute.product_attribute}"/>
                    <input type="hidden" id="hdnSelectedId" value ="${frm.attribute.name}"/>
                    <table class="table table-bordered" id="OptionsData">
                        <thead style="background: #F7FAFC;">
                            <tr>
                                <th style="width:150px">Option</th>
                                <th>Display Order</th>
                                <th>Price Adjustment</th>
                                <th>Weight Adjustment</th>
                                <th>Color</th>
                                <th>Is Pre Selected</th>
                                <th>Product Title</th>
                                <th>Disable</th>
                                <th style="width:110px">Actions</th>
                            </tr>
                        </thead>
                    
                    `;
            frappe.call({
                method: "go1_commerce.go1_commerce.doctype.product.product.get_product_attribute_options",
                args: {
                    "attribute": frm.attribute.product_attribute,
                    "product": frm.docname,
                    "attribute_id": frm.attribute.name
                },
                callback: function (r) {
                    attributeOptions_html(r,dialog)
                }
            })
        }
    },
    add_specification_attribute: function (frm) {
        window.open('/app/specification-attribute/new-specification-attribute-1', '_blank')
    },
    inventory_method: function (frm) {
        frm.trigger('inventory_display')
        if (frm.doc.inventory_method == 'Track Inventory By Product Attributes') {
            if (frm.doc.product_attributes.length == 0 && frm.doc.variant_combination.length == 0) {
                cur_frm.set_value('inventory_method', "Dont Track Inventory")
                frappe.throw("Please create attributes and attribute combination")
            } else if (frm.doc.variant_combination.length == 0) {
                cur_frm.set_value('inventory_method', "Dont Track Inventory")
                frappe.throw("Please create attribute combination")
            }
        }
    },
    build_multi_selector(frm, possible_val) {
        $.each(possible_val, function (i, c) {
            frm.page_no = 1;
            var ref_fields = unescape(c.reference_fields)
            var ref_method = c.reference_method
            var url = '/api/method/' + ref_method
            var field = c.tab_field
            $.ajax({
                type: 'POST',
                Accept: 'application/json',
                ContentType: 'application/json;charset=utf-8',
                url: window.location.origin + url,
                data: {
                    "reference_doc": c.reference_doc,
                    "reference_fields": ref_fields,
                    "filters":c.filters,
                    "page_no": frm.page_no
                },
                dataType: "json",
                async: false,
                headers: {
                    'X-Frappe-CSRF-Token': frappe.csrf_token
                },
                success: function (r) {
                    var list_name = r.message.list_name;
                    var list_length = r.message.list_len;
                    let drp_html = ` 
                        <div class = '${c.cls}' style = "padding: 0px;">
                            <div class="awesomplete" style="width:100%;position: relative;
                                                            display: inline-block;">
                                <input type="text"  class="multi-drp" id="myInput" autocomplete="nope" 
                                    onkeypress="enterKeyPressed(event, $(this))" placeholder='${c.title}'
                                    title='${c.title}' style="float:left;background-position: 10px 12px;
                                    background-repeat: no-repeat;width: 90%;font-size: 16px;padding: 10px 15px 10px 10px;
                                    border: 1px solid #d1d8dd;border-radius: 4px !important;margin: 0px;"                             
                                    data-class='${c.cls}' data-field='${c.tab_field}' data-doctype='${c.doctype}'                      
                                    data-child='${c.is_child }' data-linkfield='${c.link_name}' data-reference_doc='${c.reference_doc}'                        
                                    data-reference_fields='${c.reference_fields}' data-tab_html_field='${c.tab_html_field}'
                                    data-link_field='${c.link_field}' data-search_fields='${c.search_fields}' 
                                    data-reference_method='${c.reference_method}' data-child_link='${c.child_tab_link}'
                                    data-hasimage='${c.hasimage}' data-imagefield='${c.imagefield}'>
                                <button class="btn btn-default btn-sm" style="float:right;background-color: #ccc;margin: 0px 0px 0px 0px;
                                    padding: 11px 17px 10px 17px;font-size: 15px;" data-fieldtype="Button" data-fieldname="more_btn" 
                                        onclick="search_onbutton($(this))">
                                    Search
                                </button>
                                <h4 style="padding: 10px 10px;border: 1px solid #ddd;border-bottom: none;
                                        margin: 50px 0px 0px 0px;background: #f8f8f8;">
                                    ${c.label}
                                </h4>
                                <ul role="listbox" id="assets" class= "assets" style="border: 1px solid #d1d8dd;
                                        border-radius:0px;padding: 0px;list-style-type: none;position: relative;
                                        width: 100%;margin: 0;background: rgb(255, 255, 255);min-height:320px;
                                        height:320px;box-shadow:none;"> `
                    if(list_name.length > 0){
                        $.each(list_name, function (i, v) {
                            if (v[c.link_name]){       
                                let arr = [];
                                if (parseInt(v[c.is_child]) == 1) {
                                    var cur_row = frappe.get_doc(doctype_name, cur_frm.selected);
                                    arr = JSON.parse(cur_row[field]);
                                } 
                                else {
                                    if(cur_dialog){
                                        arr = JSON.parse(cur_dialog.fields_dict[field].get_value());
                                    }
                                }
                                if ($.inArray(v[c.link_name], arr) == -1) {
                                    drp_html += `<li style="display: block; border-bottom: 1px solid #dfdfdf;cursor:auto;">
                                                    <a style="display: none;">
                                                        <strong>${v[c.link_name]}</strong>
                                                    </a>
                                                    <label class="switch" style="float:right; margin:0px; cursor:pointer;">
                                                        <input type="checkbox" class="popupCheckBox" name="vehicle1" value="0"
                                                            id='${v[c.link_name]}' actual__value_name ='${v[c.search_fields]}' 
                                                            data-doctype='${c.doctype}' data-child='${c.is_child }' data-reference_doc='${c.reference_doc}'
                                                            data-reference_fields='${c.reference_fields}' data-tab_html_field='${c.tab_html_field}' 
                                                            data-search_fields='${c.search_fields}' data-child_link='${c.child_tab_link}' 
                                                            onclick="selected_multiselect_lists($(this))">
                                                        <span class="slider round"></span>
                                                    </label>`; 
                                    if(c.hasimage == 1 && c.imagefield){
                                        var img_src = v[c.imagefield]
                                        if(!c.imagefield || !v[c.imagefield] || c.imagefield=="null" || v[c.imagefield]=="null" || v[c.imagefield]==null || v[c.imagefield]==undefined){
                                            img_src = "/assets/ecommerce_business_store/images/no-image-60x50.png"
                                            
                                        }
                                        drp_html += `<img src="${img_src}" alt="" style="float: left;width: 35px;padding: 5px;height: 35px;">`;
                                    }
                                    drp_html += `   <p style="font-size: 14px;"> ${v[c.search_fields]}</p>
                                                </li>`;
                                }
                                 else {
                                    drp_html += `<li style="border-radius: 0px;display: block; border-bottom: 1px solid #dfdfdf;cursor:auto;">
                                                    <a style="display: none;">
                                                        <strong>${v[c.link_name]}</strong>
                                                    </a>
                                                    <label class="switch" style="float:right; margin:0px; cursor:pointer;">
                                                        <input type="checkbox" class="popupCheckBox" name="vehicle1" value="0" id="${v[c.link_name]}"
                                                            data-doctype="${c.doctype}" data-child="${c.is_child}" data-reference_doc="${c.reference_doc}"
                                                            data-reference_fields="${c.reference_fields}" data-tab_html_field="${c.tab_html_field}"
                                                            data-search_fields="${c.search_fields}" data-child_link="${c.child_tab_link}"
                                                            onclick="selected_multiselect_lists($(this))" checked>
                                                        <span class=" slider round"></span>
                                                    </label>`
                                    if(c.hasimage == 1 && c.imagefield){
                                        var img_src = v[c.imagefield]
                                        if(!c.imagefield || !v[c.imagefield] || c.imagefield=="null" || v[c.imagefield]=="null" || v[c.imagefield]==null || v[c.imagefield]==undefined){
                                            img_src = "/assets/ecommerce_business_store/images/no-image-60x50.png"
                                            
                                        }
                                        drp_html += `<img src="${img_src}" alt="" style="float: left;width: 35px;padding: 5px;height: 35px;">`;
                                    }
                                    drp_html += `   <p style="font-size: 14px;"> ${v[c.search_fields]}</p>
                                                </li>`;
                                }
                            } 
                            else {
                                drp_html += '<li></li>';
                            }
                        })
                    }else{
                        drp_html += '<li>No records found.</li>';
                    }
                    if(list_length > 20 && list_name.length == 20){
                        drp_html += `<button class="btn btn-default btn-xs" style="float:right;background-color: #ccc;
                                        margin: 8px;" data-fieldtype="Button" data-fieldname="more_btn" 
                                            onclick="load_more_items($(this))">Load more...</button>`
                    }
                    drp_html += '</ul></div>';
                    if(cur_dialog){
                        if(cur_dialog.fields_dict[c.tab_html_field].$wrapper){
                            cur_dialog.fields_dict[c.tab_html_field].$wrapper.empty();
                        }
                        cur_dialog.fields_dict[c.tab_html_field].$wrapper.append(drp_html);
                        cur_dialog.get_field(c.tab_html_field).refresh();
                        drp_html +='</div>';
                    }
                }
            })
        });
    },
    upload_product_video: function (frm) {
        if (frm.doc.__islocal){
            frappe.throw('Please save the document and then try uploading videos')
        }
        localStorage.setItem('randomuppy', ' ');
        frappe.run_serially([
            () => {
                frm.events.video_upload(frm, frm.doctype, frm.doc.name, 'demo_video', 'Product Video', undefined);
            }
        ])
    },
    add_product_image: function (frm) {
        if (frm.doc.__islocal){
            frappe.throw('Please save the document and then try uploading images')
        }
        localStorage.setItem('randomuppy', ' ');
        frappe.run_serially([
            () => {
                frm.trigger('generate_image_html')
                frm.product_image_list = frm.doc.product_images;
            },
            () => {
                frm.events.image_upload(frm, frm.doctype, frm.doc.name, 'product_images', 'Product Image', undefined);
            }
        ])
    },
    generate_image_html: function (frm) {
        let html = `
            <div class="uploadFiles">
                <div class="title" style="font-size: 14px;font-weight:600">Uploaded Files
                    <button id="saveImages" class="btn btn-xs btn-primary" style="float:right;
                        margin-top: -4px;">Save</button></div><ul id="sortable" style="margin-top:20px;
                        padding-left:0">`
        $(frm.doc.product_images).each(function (i, j) {
            let checked = "";
            if (j.is_primary == 1){
                checked = 'checked="checked"'
            }
            html += `
                <li data-id="${j.name}" class="image-element" style="list-style:none;margin-bottom: 10px;">
                    <div class="row">
                        <div class="col-md-2 ">
                            <img src="${j.list_image}"style="mac-height:120px"/>
                        </div>
                        <div class="col-md-7 img-name">
                            <div class="imageName">${j.image_name}</div>
                            <div class="editImage" style="display:none;">
                                <div>
                                    <input type="text" name="image_name" placeholder="Image Alternate Text" value="${j.image_name}"/>
                                </div>
                                <div>
                                    <label style="font-weight:400;font-size:12px;">
                                        <input type="checkbox" data-id="${j.name}"
                                            name="is_primary" ${checked}/> 
                                        <span>Mark as Primary?</span>
                                    </label>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3 img-name">
                            <a style="background-color:var(--bg-orange);color:var(--text-on-orange);padding:5px 10px;
                                border-radius:5px;float:right;" class="img-close" data-id="${j.name}">
                                <span class="fa fa-trash"></span>
                            </a>
                            <a style="background-color:var(--bg-green);color:var(--text-on-green);padding:5px 8px 5px 10px;
                                    border-radius:5px;margin-right:10px;float:right;" class="img-edit" data-id="${j.name}">
                                <span class="fa fa-edit"></span>
                            </a>
                        </div>
                    </div>
                </li>
            `
        })
        html += '</ul></div>';
        frm.files_html = html;
    },
    build_multi_selectors(frm, possible_val){
        $.each(possible_val,function(i,c){
        var ref_fields = unescape(c.reference_fields)
        var ref_method = c.reference_method
        var url='/api/method/'+ref_method
          $.ajax({
                type: 'POST',
                Accept: 'application/json',
                ContentType: 'application/json;charset=utf-8',
                url: window.location.origin +url,
                data: { 
                    "reference_doc":c.reference_doc,
                    "reference_fields":ref_fields
                },
                dataType: "json",
                async: false,
                headers: {
                    'X-Frappe-CSRF-Token': frappe.csrf_token
                },
                success: function(r) {
                    var list_name = r.message.list_name;        
                    var drp_html = `
                        <div class="${c.cls}" style="padding: 0px;">
                            <div class="awesomplete">
                                <div class="clearfix">
                                    <label class="control-label" style="padding-bottom: 0px;">
                                        ${c.label}
                                    </label>
                                </div>
                                <input type="text" class="multi-drp" id="myInput" autocomplete="nope" 
                                        onfocus="enable_select_list_forpdt($(this))" onfocusout="disable_select_list_forpdt($(this))" 
                                        onkeyup="select_lists_forpdt($(this))" placeholder="${c.title}" title="${c.title}" 
                                        style="background-position: 10px 12px;background-repeat: no-repeat;width: 100%;
                                        font-size: 16px;padding: 10px 15px 10px 10px;border: 1px solid #d1d8dd;border-radius: 4px !important;
                                        margin: 0px;" data-class="${c.cls}" data-field="${c.tab_field}" data-doctype="${c.doctype}" 
                                        data-child="${c.is_child}" data-linkfield="${c.link_name}" data-reference_doc="${c.reference_doc}" 
                                        data-reference_fields="${c.reference_fields}" data-search_fields="${c.search_fields}'" 
                                        data-reference_method="${c.reference_method}" data-child_link="${c.child_tab_link}">
                                <ul role="listbox" id="assets" class= "assets" style="list-style-type: none;display:none;position: absolute;
                                        width: 43%;margin: 0;background: rgb(255, 255, 255);">`;
                    var k = 0
                    $.each(list_name,function(i,v){
                        if(v[c.link_name]){
                            k += 1
                            if(k > 5){
                                drp_html += `
                                    <li>
                                        <a id="${v[c.link_name]}" data-doctype="${c.doctype}" data-child="${c.is_child}" 
                                                data-reference_doc="${c.reference_doc}" data-reference_fields="${c.reference_fields}"
                                                data-search_fields="${c.search_fields}" data-child_link="${c.child_tab_link}" 
                                                onclick="selected_lists_forpdt($(this))">
                                            <p>
                                                <strong>${v[c.link_name]}</strong>
                                            </p>
                                        </a><br>
                                        <p>
                                            <span>${v[c.search_fields]}</span>
                                        </p>
                                    </li>
                                        
                                `; 
                            }
                            else{
                                drp_html += `
                                    <li style="display: block">
                                        <a id="${v[c.link_name]}" data-doctype="${c.doctype}" data-child="${c.is_child}"
                                                data-reference_doc="${c.reference_doc}" data-reference_fields="${c.reference_fields}" 
                                                data-search_fields="${c.search_fields}" data-child_link="${c.child_tab_link}" 
                                                onclick="selected_lists_forpdt($(this))">
                                            <p>
                                                <strong>${v[c.link_name]}</strong>
                                            </p>
                                        </a><br>
                                        <p>
                                            <span>${v[c.search_fields]}</span>
                                        </p>
                                    </li>
                                `;
                            }
                        }
                        else{
                            drp_html += '<li></li>';
                        }
                    })
                    drp_html += `</ul></div></div>
                                    <p class="help-box small text-muted hidden-xs">${c.description}</p>`;
                    if(c.is_child == 1){
                        frappe.meta.get_docfield(c.doctype, c.tab_html_field,
                        frm.doc.name).options = drp_html;
                    }
                    else{
                        frm.set_df_property(c.tab_html_field,"options",drp_html);
                    }
                }
            })
            var cls =c.cls;
            var field = $('.'+cls+' #myInput').attr('data-field');
            var linkedfield = $('.'+cls+' #myInput').attr('data-linkfield');
             get_multiselect_values_forpdt(cls, field, linkedfield, c.doctype, c.is_child, c.child_tab_link)
        });
    },
})



var generate_variant_html = Class.extend({
    init: function(opts) {
        this.click=true
        this.frm = opts.frm;
        this.items_list = opts.items_list
        this.cdt = opts.cdt;
        this.cdn = opts.cdn;
        this.make();
    },
    make: function(create_combination = 0) {
        cur_frm.create_combination = create_combination
        let me = this;
        this.frm.fields_dict["product_attribute_html"].$wrapper.empty();
        let wrapper = this.frm.fields_dict["product_attribute_html"].$wrapper;
        let table;
        if(this.frm.catalog_settings.enable_size_chart == 0){
            table = $(`<table class="table table-bordered" id="attributeWithOptions">
                    <thead>
                        <tr>
                            <th></th>
                            <th style="display:none;">${__("Variant ID")}</th>
                            <th style="">${__("Variant")}</th>
                            <th >${__("Display Type")}</th>
                            <th style="">${__("Options")}<p style="font-size: 10px;margin: 0px;
                                font-weight: 400;">Choose options from list (OR) Type your custom  options  
                                separated by Comma ( , )</p></th>
                            <th class="btnclm" style="width:5%"></th>
                        </tr>
                    </thead>
                    <tbody id="productAttributeBody"></tbody>
                    <tfoot style="display:none;">
                        <tr>
                            <td colspan="6">
                                <a onclick="save_attribute_and_options()" class="btn btn-xs btn-secondary btn-xs" 
                                    style="display:none;float:right;margin-left:10px;">Generate Combination</a>
                                <a class="btn btn-default btn-primary btn-xs" id="add_new_attribute" style="display:none;
                                    float:right;margin-left:10px;">Add Attribute</a>
                            </td>
                        </tr>
                    </tfoot>
                </table>
                <style> .option-group>.btn:hover{
                            background-color: #ecf7fe !important;}
                        .option-group>.btn:focus, .option-group>
                            .btn:active:focus{
                                outline:none;background-color: #ecf7fe !important;}
                        .custom-sortable-width{
                                width:100px;}
                        div[data-fieldname="product_attribute_html"] td div .frappe-control {
                                            margin-bottom: 0px !important;
                                            min-height: 32px !important;} 
                        div[data-fieldname="product_attribute_html"] td div input{
                                            border-radius: 4px !important;} 
                        div[data-fieldname="product_attribute_html"] .table > tbody > tr > td{
                                            padding: 5px;vertical-align: middle;}
                        div[data-fieldname="product_attribute_html"] .table-bordered >
                                thead > tr > th{border-bottom-width: 0px;}
                </style>`).appendTo(wrapper);
        }
        if(this.frm.catalog_settings.enable_size_chart == 1){
            table = $(`<table class="table table-bordered" id="attributeWithOptions">
                <thead>
                    <tr>
                        <th></th>
                        <th style="display:none;">${__("Variant ID")}</th>
                        <th style="">${__("Variant")}</th>
                        <th >${__("Display Type")}</th>
                        <th style="">${__("Options")}<p style="font-size: 10px;margin: 0px;
                            font-weight: 400;">Choose options from list (OR) Type your custom  options  
                            separated by Comma ( , )</p>
                        </th>
                        <th style="">${__("Size Chart")}</th>
                        <th class="btnclm" style="width:5%"></th>
                    </tr>
                </thead>
                <tbody id="productAttributeBody"></tbody>
                <tfoot style="display:none;"> 
                    <tr>
                        <td colspan="6">
                            <a onclick="save_attribute_and_options()" class="btn btn-xs btn-secondary btn-xs"
                                 style="display:none;float:right;margin-left:10px;">Generate Combination</a>
                            <a class="btn btn-default btn-primary btn-xs" id="add_new_attribute" 
                                style="display:none;float:right;margin-left:10px;">Add Attribute</a>
                        </td>
                    </tr>
                </tfoot>
            </table>
                <style>
                    .option-group>.btn:hover{
                        background-color: #ecf7fe !important;}
                    .option-group>.btn:focus, .option-group>
                        .btn:active:focus{
                            outline:none;background-color: #ecf7fe !important;}
                    .custom-sortable-width{
                        width:100px;}
                    div[data-fieldname="product_attribute_html"] td div 
                        .frappe-control{
                            margin-bottom: 0px !important;min-height: 32px !important;}
                    div[data-fieldname="product_attribute_html"] 
                        td div input{
                            border-radius: 4px !important;}
                    div[data-fieldname="product_attribute_html"] .table > tbody > tr > 
                        td{
                            padding: 5px;vertical-align: middle;}
                    div[data-fieldname="product_attribute_html"] .table-bordered > 
                        thead > tr > th{
                            border-bottom-width: 0px;}
                </style>`).appendTo(wrapper);
        }
        if(cur_frm.doc.product_attributes && cur_frm.doc.product_attributes.length>0){
            var bthide=""
            if(this.frm.catalog_settings.enable_size_chart==0){
                cur_frm.doc.product_attributes.map(f => {
                   
                    let row = $(`<tr data-id="${f.idx}" data-name="${f.name}">
                    <td style="text-align: center;">
                        <img src="/assets/go1_commerce/images/section-icon.svg" 
                            style="height:18px;cursor: all-scroll;position: relative;">
                        ${f.idx}
                    </td>
                    <td style="display:none;">${__(f.product_attribute)}</td>
                    <td style="">${__(f.attribute)}</td>
                    <td >${__(f.control_type)}</td>
                    <td id="optiontag" style="">${__(f.options)}</td>
                    <td class="${bthide}" style="width: 5%;">
                        <button class="btn btn-primary btn-xs" 
                            style="margin-right: 8px;background: var(--bg-green);
                                color: var(--text-on-green);">
                            <span class="fa fa-pencil-square-o" style="display:none;"></span>
                            Edit Options
                        </button>
                        <button class="btn btn-danger btn-xs"><span class="fa fa-trash"></span>
                        </button>
                    </td>
                    </tr>`);
                table.find('tbody').append(row);
                me.update_row(wrapper, table, f.idx);
                })
            }
            else{
                cur_frm.doc.product_attributes.map(f => {
                if(!f.size_chart){
                    f.size_chart=""
                }
                let row = $(`<tr data-id="${f.idx}" data-name="${f.name}">
                        <td style="text-align: center;">
                            <img src="/assets/go1_commerce/images/section-icon.svg" 
                                style="height:18px;cursor: all-scroll;position: relative;">
                            ${f.idx}
                        </td>
                        <td style="display:none;">${__(f.product_attribute)}</td>
                        <td style="">${__(f.attribute)}</td>
                        <td >${__(f.control_type)}</td>
                        <td id="optiontag" style="">${__(f.options)}</td>
                        <td style="">${__(f.size_chart)}</td>
                        <td class="${bthide}" style="width: 5%;">
                            <button class="btn btn-primary btn-xs" style="margin-right: 8px;
                                color: var(--text-on-green);background: var(--bg-green);">
                                <span class="fa fa-pencil-square-o" style="display:none;"></span>
                                Edit Options
                            </button>
                            <button class="btn btn-danger btn-xs">
                                <span class="fa fa-trash"></span>
                            </button>
                        </td>
                    </tr>`);
                table.find('tbody').append(row);
                me.update_row(wrapper, table, f.idx);
                })
            }
        }
        else{
            table.find('tbody').append(`<tr data-type="noitems">
                                            <td colspan="9">Records Not Found!</td>
                                        </tr>`);
        }
        setTimeout(function(){
            $("#productAttributeBody").sortable({
                items: 'tr',
                opacity: 0.7,
                distance: 20,
                update: function(e, ui) {
                    $(cur_frm.$wrapper).find('div[data-fieldname="product_attribute_html"] table tbody tr').each(function(k, v) {
                        frappe.model.set_value('Product Attribute Mapping', $(this).attr('data-name'), 'idx', (k + 1))
                        let objIndex = cur_frm.doc.product_attributes.findIndex((obj => obj.name == $(this).attr('data-name')));
                        cur_frm.doc.product_attributes[objIndex].idx = (k + 1)
                    })
                }
              });
          $('#productAttributeBody').find("tr #optiontag").find("#table-multiselect").sortable({
                items: '.tb-selected-value',
                opacity: 0.7,
                distance: 20,
                classes:{
                    "ui-sortable-handle":"custom-sortable-width"
                },
                start: function(e, ui) {
                    $(ui.item[0]).css("width","100px !important")
                },
                update: function(e, ui) {
                    $(cur_frm.$wrapper).find(`div[data-fieldname="product_attribute_html"] table 
                        tbody tr div[data-fieldname="option_html"] .table-multiselect 
                        .tb-selected-value`).each(function(k, v) {
                            var option_val = $(this).attr("data-value");
                            var attr_index = $(this).attr("data-index");
                            let objIndex = cur_frm.doc.attribute_options.findIndex((obj => 
                                obj.option_value == option_val && 
                                x.attribute == cur_frm.doc.product_attributes[attr_index].product_attribute &&
                                x.attribute_id == cur_frm.doc.product_attributes[attr_index].name));
                            cur_frm.doc.attribute_options[objIndex].idx = (k + 1);
                            cur_frm.doc.attribute_options[objIndex].display_order = (k + 1);
                            $(this).attr("data-display_order", (k + 1));
                            $(this).attr("data-data-index", (k + 1));
                    })
                }
            });
        }, 5000);
    },
    update_row: function(wrapper, table, idx){
        var btnhide=""
        let me = this;
        table.find('tbody').find('tr[data-id="'+idx+'"]').empty();
        let new_row = $(`
                <td style="width:5%;text-align: center;">
                    <img src="/assets/go1_commerce/images/section-icon.svg" 
                    style="height:18px;cursor: all-scroll;position: relative;">
                    ${idx}
                </td>
                <td style="width:15%;display:none;">
                    <div class="product_attribute"></div>
                </td>
                <td style="width:15%;">
                    <div class="attribute"></div>
                </td>
                <td style="width:15%;">
                    <div class="control_type_html"></div>
                </td>
                <td style="width:35%" id="optiontag">
                    <div class="option_html"></div>
                </td>
               <td class="${btnhide}" style="width: 14%;">
                    <a class="btn btn-success btn-xs" style="margin-right: 8px;
                        background: var(--bg-green);color: var(--text-on-green);">
                        <span class="fa fa-floppy-o" style="display:none;"></span>
                    Edit Options</a>
                    <a class="btn btn-danger btn-xs"><span class="fa fa-trash"></span></a>
                </td>
            `);
        if(cur_frm.catalog_settings.enable_size_chart == 1){
            new_row = $(`
                <td style="width:5%;text-align: center;">
                    <img src="/assets/go1_commerce/images/section-icon.svg" 
                    style="height:18px;cursor: all-scroll;position: relative;">
                ${idx}</td>
                <td style="width:15%;display:none;">
                    <div class="product_attribute"></div>
                </td>
                <td style="width:15%;"><div class="attribute"></div></td>
                <td style="width:15%;"><div class="control_type_html"></div></td>
                <td style="width:35%" id="optiontag"><div class="option_html"></div></td>
                <td style="width:15%;" ><div class="size_chart"></div></td>
               <td class="${btnhide}" style="width: 14%;">
                    <a class="btn btn-success btn-xs" style="margin-right: 8px;
                        background: var(--bg-green);color: var(--text-on-green);">
                        <span class="fa fa-floppy-o" style="display:none;"></span>
                    Edit Options</a>
                    <a class="btn btn-danger btn-xs"><span class="fa fa-trash"></span></a></td>
            `);
        }
        table.find('tbody').find('tr[data-id="'+idx+'"]').html(new_row);
        let index = cur_frm.doc.product_attributes.findIndex(x => x.idx == idx);
        var attr_html = '<div class="form-group option-group" style="margin-bottom: 0px;padding: 5px;"><span >'+cur_frm.doc.product_attributes[index]["attribute"]+'</span></div>'
        let input0 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __("Attribute"),
                "fieldname": "attribute"
            },
            parent: new_row.find('.attribute'),
            only_input: true,
            default: attr_html
        })
        input0.set_value(attr_html)
        var docname = "'"+cur_frm.doc.product_attributes[index]["name"]+"'"
        var size_chart_value = "'"+cur_frm.doc.product_attributes[index]["size_chart"]+"'"
        var size_chart_html = '';
        size_chart_html = `
            <div class="form-group option-group" style="margin-bottom: 0px;"> 
                <div class="control-input-wrapper">
                    <div class="control-input form-control table-multiselect" 
                        style="cursor:pointer;" id="table-multiselect" 
                        onclick="change_field(${docname},${size_chart_value})" 
                        id="change_field">
                        <div class="form-group option-group" style="margin-bottom: 0px;
                            padding: 5px;border-radius:1px solid black;">
                            <span>`
        if(cur_frm.doc.product_attributes[index]["size_chart_name"]){
            size_chart_html += cur_frm.doc.product_attributes[index]["size_chart_name"]
        }
        size_chart_html += '</span><div class="control-input-wrapper"></div>'
      if(cur_frm.catalog_settings.enable_size_chart == 1){
        let input11 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __("Size Chart"),
                "fieldname": "size_chart"
            },
            parent: new_row.find('.size_chart'),
            only_input: true,
            default:size_chart_html
        })
        input11.set_value(size_chart_html)
       }
        var controlhtml = `
            <div class="form-group option-group" style="margin-bottom: 0px;">
                <a class="btn btn-sm" style="background: transparent;border-radius: 5px;
                        border: .1rem solid #1b8fdb;box-shadow: none;color: #1b8fdb;"
                        onclick="choose_display_types($(this))" 
                        data-name="${cur_frm.doc.product_attributes[index]["name"]}" 
                        data-index="${index}" data-idx="${idx}" 
                        data-control_type="${cur_frm.doc.product_attributes[index]["control_type"]}">
            `
        if(cur_frm.doc.product_attributes[index]["control_type"]){
            controlhtml += cur_frm.doc.product_attributes[index]["control_type"]
        }
        else{
            controlhtml += "Select"
        }
        controlhtml += '</a></div>'
        let input1 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __("Control Type"),
                "fieldname": "control_type_html"
            },
            parent: new_row.find('.control_type_html'),
            only_input: true,
            default: controlhtml
        })
        input1.set_value(controlhtml)
        var option_data =[]
        var varient_option  = cur_frm.doc.attribute_options.filter( x =>  
            x.attribute == cur_frm.doc.product_attributes[index].product_attribute 
            && x.attribute_id == cur_frm.doc.product_attributes[index].name);
        if (!varient_option){
            varient_option = []
        }
        let optiondatahtml = ""
        $.each(option_data, function (i, s) {
          var  selected = false
            if(i == 0){
                selected = true
            }
            var otindex = varient_option.findIndex(obj => obj.option_value == s.options);
            if(otindex < 0){
                optiondatahtml += `<li aria-selected="${selected}">
                                    <a onclick="option_selection($(this))">
                                        <p><strong>${s.options}</strong>
                                        </p>
                                    </a>
                                </li>`;
            }
        })
        var optionhtml = `<div class="form-group option-group" style="margin-bottom: 0px;">
                            <div class="control-input-wrapper">
                                <div class="control-input form-control table-multiselect" 
                                        id="table-multiselect">`
        if(varient_option){
            varient_option.map(f => {
                var btn_cls = 'btn-default';
                var option_style = "";
                var selected_color = "1px solid var(--dark-border-color)";
                if(f.is_pre_selected == 1){
                    btn_cls = 'btn-info';
                    selected_color = "1px solid var(--text-on-green)";
                    option_style =` style='background: var(--bg-green);
                                            color: var(--text-on-green);
                                            font-weight: 600;'`
                }
                var comb_index = f.display_order
                optionhtml += `
                    <div class="btn-group tb-selected-value" id="multi_input_updatevalue"
                        style="display: inline-block;margin-right: 5px;margin-bottom: 5px;
                        border-radius: 6px;" data-value="${f.option_value}" data-name="${f.name}" 
                        data-index="${index}">
                        <a ${option_style} class="btn ${btn_cls} btn-xs btn-link-to-form" 
                                data-parentidx="${idx}" data-id="${f.option_value}" 
                                data-attribute="${cur_frm.doc.product_attributes[index]["product_attribute"]}" 
                                data-index="${index}" data-display_order="${comb_index}" data-option_name="${f.name}" 
                                data-is_pre_selected="${f.is_pre_selected}" data-product_title="${f.product_title}" 
                                data-disable="${f.disable}" data-parent-control-type="${cur_frm.doc.product_attributes[index]["control_type"]}" 
                                data-attribute_color="`
                if(f.attribute_color){
                    optionhtml += f.attribute_color
                }
                optionhtml +=`
                    " onclick="pick_color($(this))" ondblclick="update_attroption($(this))">
                        <img src="/assets/go1_commerce/images/section-icon.svg" 
                            style="height: 18px;cursor: all-scroll;position: relative;margin-right: 5px;">
                    ${f.option_value} </a>`
                optionhtml += `
                    <a ${option_style} class="btn ${btn_cls} btn-xs btn-remove" data-index="${f.idx}"
                        data-id="${f.option_value}" data-name="${f.name}" onclick="remove_attroption($(this))">
                        <i class="fa fa-remove text-muted" style="font-size:16px"></i>
                    </a>
                    </div>`
            })
        }
        optionhtml += `
            <div class="link-field ui-front" style="position: relative; line-height: 1;">
                <div class="awesomplete">
                    <input placeholder="Type options..." style="padding: 6px 10px 8px;width: 178px;
                        font-size: 11px;font-weight: 400; type="text" id="select_options${idx}"
                        keydown="add_option_totable($(this))" class="input-with-feedback bold" 
                        data-fieldtype="Table MultiSelect" data-fieldname="display_options" 
                        placeholder="" data-doctype="Product" data-target="Product" autocomplete="off" 
                        aria-owns="awesomplete_list_45" role="combobox" 
                        aria-activedescendant="awesomplete_list_45_item_0">`;
        optionhtml += `<ul role="listbox" data-idx ="${idx}" data-index="${index}" 
                            id="awesompletelist_${idx}" style="z-index: 100;display:none;width:272px;">`
        optionhtml += optiondatahtml
        optionhtml += '</ul>'
        optionhtml += '</div> </div>'
        optionhtml += '<style>.awesomplete > ul:empty {display: none;}</style>'
        optionhtml += '</div></div>'
        let input3 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __("options"),
                "fieldname": "option_html",
                "placeholder": "",
                "read_only":0,
                "onchange": function() {
                    let val = this.get_value();
                   }
            },
            parent: new_row.find('.option_html'),
            only_input: true,
            default: optionhtml,
            value: ""
        });
        input3.set_value(optionhtml)
        $('#select_options'+idx).on("focusin", function(event){
            $("#awesompletelist_"+idx).show()
            var varient_options  = cur_frm.doc.attribute_options.filter( x =>  x.attribute == cur_frm.doc.product_attributes[index].product_attribute && x.attribute_id == cur_frm.doc.product_attributes[index].name);
            if (!varient_options){
                varient_options = []
            }
            $(this).next().find('li').each(function() {
                let qoindex =varient_options.findIndex(x => x.option_value == $(this).text());
                if(qoindex>=0){
                    $(this).hide();
                }
                else{
                    $(this).show();
                }
            })
        })
         $('#select_options'+idx).on("focusout", function(event){
             $("#awesompletelist_"+idx).hide()
        })
        $('#select_options'+idx).on("keyup", function(event){
            var val = $(this).val();
            var is_exception = 0;
            if(val.indexOf(",") != -1){
               var val = val.replace(/,(?=\s*$)/, '');
                is_exception = 1;
            }
            me.li_hide_show(val, event,idx, index, this);
            if(event.keyCode==13 ||is_exception==1){
                me.keypress_option(val, event,idx, index, this);
            }
        })
        $('#select_options'+idx).on("keydown", function(event){
            var val = $(this).val();
            if(val.indexOf(",") != -1){
               var val = val.replace(/,(?=\s*$)/, '');
                is_exception = 1;
            }
            if(event.keyCode==9){
                me.keypress_option(val, event,idx, index, this);
            }
        })
        new_row.find('.btn-success').click(function() {
            me.frm.attribute = cur_frm.doc.product_attributes[index]
            me.frm.trigger('edit_option_list');
        })
        new_row.find('.btn-danger').click(function() {
            var op = cur_frm.doc.attribute_options.filter( x =>  x.attribute == cur_frm.doc.product_attributes[index].product_attribute 
                                                                && x.attribute_id == cur_frm.doc.product_attributes[index].name);
            if (!op){
                op = []
            }
            let conf_html = "<p>Removing this variant (<b>"+cur_frm.doc.product_attributes[index].attribute+"</b>) will delete the following <b>"+op.length+"</b> options:<p>";
            conf_html += "<ul>"
            $(op).each(function(j, n){
                conf_html +="<li><b>"+cur_frm.doc.product_attributes[index].attribute+":"+n.option_value+"</b></li>"
            });
            conf_html+="</ul>";
            frappe.warn("Removing varient will also delete options", conf_html,function () {
                var tbl = cur_frm.doc.attribute_options || [];
                    var i = tbl.length;
                    while (i--){
                        if(tbl[i].attribute == cur_frm.doc.product_attributes[index].product_attribute && 
                            tbl[i].attribute_id == cur_frm.doc.product_attributes[index].name){
                                if(cur_frm.get_field("attribute_options").grid.grid_rows){
                                    cur_frm.get_field("attribute_options").grid.grid_rows[i].remove();
                                }
                                else{
                                    cur_frm.doc.attribute_options.splice(i, 1);
                                }
                        }
                    }
                    var varnt = cur_frm.doc.product_attributes;
                    varnt.splice(index, 1);
                    cur_frm.doc.product_attributes = varnt
                    cur_frm.dirty()
                    $(this).parent().parent().empty();
                    frappe.show_alert(__("Row "+idx+" deleted."));
                    cur_frm.create_combination = 1 ;
                    me.make(cur_frm.create_combination);
                },'Continue',true)
        });
    },
    li_hide_show: function(val, event, idx, index,e){
        var input, filter, ul, li, a, i, txtValue, p_text, txtValue_p;
        input = $("#select_options"+idx).val();
        filter = input.toUpperCase();
        li = $("#awesompletelist_"+idx).find("li");
        for (i = 0; i < li.length; i++) {
            a = li[i].getElementsByTagName("a")[0];
            p_text = li[i].getElementsByTagName("p")[0];
            txtValue = a.textContent || a.innerText;
            txtValue_p = p_text.textContent || p_text.innerText;
            if(txtValue.toUpperCase().indexOf(filter) > -1) {
                li[i].style.display = "";
            }
            else if (txtValue_p.toUpperCase().indexOf(filter) > -1) {
                li[i].style.display = "";
            } 
            else {
                li[i].style.display = "none";
            }
        }
    },
    keypress_option: function(val, event, idx, index,e){
        let me = this;
        if(val){
            $(e).attr("data-value", val);
            $(e).attr("data-name", "");
            var option_index = 0;
            var varient_option =  cur_frm.doc.attribute_options.filter( x =>  x.attribute == cur_frm.doc.product_attributes[index].product_attribute && 
                                                                                x.attribute_id == cur_frm.doc.product_attributes[index].name);
            if (!varient_option){
                varient_option = []
            }
            if(varient_option){
                option_index = varient_option.length;
            }
            var pre_selected = 0;
            var btn_cls = 'btn-default';
            if(option_index == 0){
                pre_selected = 1
                btn_cls = 'btn-info';
            }
            if($(e).attr("data-name")){
                let child = frappe.get_doc("Product Attribute Option", $(e).attr("data-name"));
                child.attribute_color = $(e).attr("data-attribute_color")
                child.attribute_id = cur_frm.doc.product_attributes[index]["name"]
                child.display_order = 1
                child.idx = option_index
                child.is_pre_selected = pre_selected
                child.option_value = $(e).attr("data-value")
                child.attribute =cur_frm.doc.product_attributes[index]["product_attribute"];
                cur_frm.refresh_field("attribute_options");
                var optionhtmls = `<div class="btn-group tb-selected-value" id="multi_input_updatevalue" 
                                        style="display: inline-block;margin-right: 5px;margin-bottom: 5px;" 
                                        data-value="${val}" data-name="${child.name}" data-index="${index}">
                                        <a class="btn ${btn_cls} btn-xs btn-link-to-form" data-id="${val}" 
                                            data-attribute="${cur_frm.doc.product_attributes[index]["product_attribute"]}" 
                                            data-index="${index}" data-option_name="${child.name}" 
                                            data-display_order="${cur_frm.doc.product_attributes[index]["display_order"]}" 
                                            data-is_pre_selected="${cur_frm.doc.product_attributes[index]["is_pre_selected"]}" 
                                            data-product_title="${cur_frm.doc.product_attributes[index]["product_title"]}" 
                                            data-disable="${cur_frm.doc.product_attributes[index]["disable"]}" 
                                            data-parent-control-type="${cur_frm.doc.product_attributes[index]["control_type"]}" 
                                            data-attribute_color="
                                    `
            }
            else{
                let child = frappe.model.add_child(cur_frm.doc, "Product Attribute Option", "attribute_options");
                child.attribute_color = $(e).attr("data-attribute_color")
                child.attribute_id = cur_frm.doc.product_attributes[index]["name"]
                child.display_order = 1
                child.idx = option_index
                child.is_pre_selected = pre_selected
                child.option_value = $(e).attr("data-value")
                child.attribute =cur_frm.doc.product_attributes[index]["product_attribute"];
                cur_frm.refresh_field("attribute_options");
                var optionhtmls = `<div class="btn-group tb-selected-value" id="multi_input_updatevalue" 
                                        style="display: inline-block;margin-right: 5px;margin-bottom: 5px;" 
                                        data-value="${val}" data-name="${child.name}" data-index="${index}">
                                        <a class="btn ${btn_cls} btn-xs btn-link-to-form" data-id="${val}" 
                                            data-attribute="${cur_frm.doc.product_attributes[index]["product_attribute"]}" 
                                            data-index="${index}" data-option_name="${child.name}" 
                                            data-display_order="${cur_frm.doc.product_attributes[index]["display_order"]} 
                                            data-is_pre_selected="${cur_frm.doc.product_attributes[index]["is_pre_selected"]}" 
                                            data-product_title="${cur_frm.doc.product_attributes[index]["product_title"]}" 
                                            data-disable="${cur_frm.doc.product_attributes[index]["disable"]}" 
                                            data-parent-control-type="${cur_frm.doc.product_attributes[index]["control_type"]}" 
                                            data-attribute_color="
                                `
            }
            if($(e).attr("data-attribute_color")){
                    optionhtmls += $(e).attr("data-attribute_color")
            }
            optionhtmls +=`" onclick="pick_color($(this))" ondblclick="update_attroption($(this))">
                                <img src="/assets/go1_commerce/images/section-icon.svg" 
                                style="height:10px;cursor: all-scroll;position: relative;">${val}
                            </a>`
            optionhtmls += `<a class="btn ${btn_cls} btn-xs btn-remove" data-id="${val}" data-index="${option_index}" 
                                onclick="remove_attroption($(this))">
                                <i class="fa fa-remove text-muted"></i> 
                            </a></div> `
            $(e).parent().parent().before(optionhtmls);
            $(e).val("");
            me.frm.dirty()
            cur_frm.create_combination = 1 ;
        }
    }
})

var append_variant_html = Class.extend({
    init: function(opts) {
        this.frm = opts.frm;
        this.idx = opts.idx;
        this.product_attribute = opts.product_attribute;
        this.refresh_attribute_row();
    },
    make: function(create_combination=0) {
        cur_frm.create_combination = create_combination
        let me = this;
        this.frm.fields_dict["product_attribute_html"].$wrapper.empty();
        let wrapper = this.frm.fields_dict["product_attribute_html"].$wrapper;
        let table;
        if(this.frm.catalog_settings.enable_size_chart==0){
         table = $(`<table class="table table-bordered" id="attributeWithOptions">
                <thead>
                    <tr>
                        <th></th>
                        <th style="display:none;">${__("Variant ID")}</th>
                        <th style="">${__("Variant")}</th>
                        <th>${__("Display Type")}</th>
                        <th style="">${__("Options")}
                            <p style="font-size: 10px;margin: 0px;font-weight: 400;">
                                Choose options from list (OR) Type your custom  options  separated by Comma ( , )
                            </p>
                        </th>
                        <th class="btnclm" style="width:5%"></th>
                    </tr>
                </thead>
                <tbody id="productAttributeBody"></tbody>
                <tfoot style="display:none;">
                    <tr>
                        <td colspan="6">
                            <a onclick="save_attribute_and_options()" class="btn btn-xs btn-secondary btn-xs" 
                                    style="display:none;float:right;margin-left:10px;">Generate Combination
                            </a>
                            <a class="btn btn-default btn-primary btn-xs" id="add_new_attribute" style="display:none;
                                    float:right;margin-left:10px;">Add Attribute
                            </a>
                        </td>
                    </tr>
                </tfoot>
            </table>
            <style>
                .option-group>.btn:hover{
                    background-color: #ecf7fe !important;}
                .option-group>.btn:focus, .option-group>.btn:active:focus{
                    outline:none;background-color: #ecf7fe !important;}
                .custom-sortable-width{
                    width:100px;}
                div[data-fieldname="product_attribute_html"] td div .frappe-control {
                    margin-bottom: 0px !important;
                    min-height: 32px !important;} 
                div[data-fieldname="product_attribute_html"] td div input{
                    border-radius: 4px !important;} 
                div[data-fieldname="product_attribute_html"] 
                .table > tbody > tr > td{
                    padding: 5px;
                    vertical-align: middle;}
                div[data-fieldname="product_attribute_html"] .table-bordered > thead > tr > th{
                    border-bottom-width: 0px;}
            </style>`).appendTo(wrapper);
        }
        if(this.frm.catalog_settings.enable_size_chart == 1){
            table = $(`
                <table class="table table-bordered" id="attributeWithOptions">
                    <thead>
                        <tr>
                            <th></th>
                            <th style="display:none;">${__("Variant ID")}</th>
                            <th style="">${__("Variant")}</th>
                            <th >${__("Display Type")}</th>
                            <th style="">${__("Options")}
                                <p style="font-size: 10px;margin: 0px;font-weight: 400;">
                                    Choose options from list (OR) Type your custom  options  separated by Comma ( , )
                                </p>
                            </th>
                            <th style="">${__("Size Chart")}</th>
                            <th class="btnclm" style="width:5%"></th>
                        </tr>
                    </thead>
                    <tbody id="productAttributeBody"></tbody>
                    <tfoot style="display:none;">
                        <tr>
                            <td colspan="6">
                                <a onclick="save_attribute_and_options()" class="btn btn-xs btn-secondary btn-xs" 
                                    style="display:none;float:right;margin-left:10px;">Generate Combination
                                </a>
                                <a class="btn btn-default btn-primary btn-xs" id="add_new_attribute" style="display:none;
                                    float:right;margin-left:10px;">Add Attribute
                                </a>
                            </td>
                        </tr>
                    </tfoot>
                </table>
                <style>
                    .option-group>.btn:hover{
                        background-color: #ecf7fe !important;}
                    .option-group>.btn:focus, .option-group>.btn:active:focus{
                        outline:none;background-color: #ecf7fe !important;}
                    .custom-sortable-width{
                        width:100px;}
                    div[data-fieldname="product_attribute_html"] td div .frappe-control {
                        margin-bottom: 0px !important;min-height: 32px !important;} 
                    div[data-fieldname="product_attribute_html"] td div input{
                        border-radius: 4px !important;} 
                    div[data-fieldname="product_attribute_html"] .table > tbody > tr > td{
                        padding: 5px;vertical-align: middle;}
                    div[data-fieldname="product_attribute_html"] .table-bordered > thead > tr > th{
                        border-bottom-width: 0px;}
                </style>`).appendTo(wrapper);
        }
        if(cur_frm.doc.product_attributes.length > 0){
            var bthide = ""
            if(this.frm.catalog_settings.enable_size_chart == 0){
                cur_frm.doc.product_attributes.map(f => {
                    let row = $(`
                        <tr data-id="${f.idx}" data-name="${f.name}">
                            <td style="text-align: center;">
                                <img src="/assets/go1_commerce/images/section-icon.svg" 
                                    style="height:18px;cursor: all-scroll;position: relative;">
                                ${f.idx}
                            </td>
                            <td style="display:none;">${__(f.product_attribute)}</td>
                            <td style="">${__(f.attribute)}</td>
                            <td >${__(f.control_type)}</td>
                            <td id="optiontag" style="">${__(f.options)}</td> 
                            <td class="${bthide}" style="width: 5%;">
                                <button class="btn btn-primary btn-xs" style="margin-right: 8px;
                                    background: var(--bg-green);color: var(--text-on-green);">
                                    <span class="fa fa-pencil-square-o" style="display:none;"></span>Edit Options
                                </button>
                                <button class="btn btn-danger btn-xs"><span class="fa fa-trash"></span></button>
                            </td>
                        </tr>`);
                    table.find('tbody').append(row);
                    me.update_row(wrapper, table, f.idx);
                })
            }
            else{
                cur_frm.doc.product_attributes.map(f => {
                    if(!f.size_chart){
                        f.size_chart = ""
                    }
                    let row = $(`
                        <tr data-id="${f.idx}" data-name="${f.name}">
                            <td style="text-align: center;">
                                <img src="/assets/go1_commerce/images/section-icon.svg" 
                                    style="height:18px;cursor: all-scroll;position: relative;">
                                ${f.idx}
                            </td>
                            <td style="display:none;">${__(f.product_attribute)}</td>
                            <td style="">${__(f.attribute)}</td>
                            <td >${__(f.control_type)}</td>
                            <td id="optiontag" style="">${__(f.options)}</td> 
                            <td style="">${__(f.size_chart)}</td>
                            <td class="${bthide}" style="width: 5%;">
                                <button class="btn btn-primary btn-xs" style="margin-right: 8px;background: var(--bg-green);
                                    color: var(--text-on-green);">
                                    <span class="fa fa-pencil-square-o" style="display:none;"></span>Edit Options
                                </button>
                                <button class="btn btn-danger btn-xs"><span class="fa fa-trash"></span></button>
                            </td>
                        </tr>`);
                    table.find('tbody').append(row);
                    me.update_row(wrapper, table, f.idx);
                })
            }
        }
        else{
            table.find('tbody').append(`<tr data-type="noitems"><td colspan="9">Records Not Found!</td></tr>`);
        }
        setTimeout(function(){ 
            $("#productAttributeBody").sortable({
                items: 'tr',
                opacity: 0.7,
                distance: 20,
                update: function(e, ui) {
                    $(cur_frm.$wrapper).find('div[data-fieldname="product_attribute_html"] table tbody tr').each(function(k, v) {
                        frappe.model.set_value('Product Attribute Mapping', $(this).attr('data-name'), 'idx', (k + 1))
                        let objIndex = cur_frm.doc.product_attributes.findIndex((obj => obj.name == $(this).attr('data-name')));
                        cur_frm.doc.product_attributes[objIndex].idx = (k + 1)
                    })
                }
              });
          $('#productAttributeBody').find("tr #optiontag").find("#table-multiselect").sortable({
                items: '.tb-selected-value',
                opacity: 0.7,
                distance: 20,
                classes:{
                    "ui-sortable-handle":"custom-sortable-width"
                },
                start: function(e, ui) {
                    $(ui.item[0]).css("width","100px !important")
                },
                update: function(e, ui) {
                    $(cur_frm.$wrapper).find(`div[data-fieldname="product_attribute_html"] table tbody tr div[data-fieldname="option_html"] .table-multiselect .tb-selected-value`).each(function(k, v) { 
                        var option_val = $(this).attr("data-value");
                        var attr_index = $(this).attr("data-index");
                        let objIndex = cur_frm.doc.attribute_options.findIndex((obj => obj.option_value == option_val && x.attribute == cur_frm.doc.product_attributes[attr_index].product_attribute && x.attribute_id == cur_frm.doc.product_attributes[attr_index].name));
                        cur_frm.doc.attribute_options[objIndex].idx = (k + 1);
                        cur_frm.doc.attribute_options[objIndex].display_order = (k + 1);
                        cur_frm.refresh_field("attribute_options");
                        $(this).attr("data-display_order", (k + 1));
                        $(this).attr("data-data-index", (k + 1));
                    })
                }
              });
        }, 5000);
    },
    update_row: function(wrapper, table, idx){
        var btnhide=""
        let me = this;
        table.find('tbody').find('tr[data-id="'+idx+'"]').empty();
        let new_row = $(`
                <td style="width:5%;text-align: center;">
                    <img src="/assets/go1_commerce/images/section-icon.svg" style="height:18px;cursor: all-scroll;position: relative;">
                    ${idx}
                </td>
                <td style="width:15%;display:none;">
                    <div class="product_attribute"></div>
                </td> 
                <td style="width:15%;"><div class="attribute"></div></td> 
                <td style="width:15%;"><div class="control_type_html"></div></td> 
                <td style="width:35%" id="optiontag">
                    <div class="option_html"></div>
                </td>              
               <td class="${btnhide}" style="width: 14%;">
                    <a class="btn btn-success btn-xs" style="margin-right: 8px;background: var(--bg-green);
                        color: var(--text-on-green);">
                        <span class="fa fa-floppy-o" style="display:none;"></span>Edit Options
                    </a>
                    <a class="btn btn-danger btn-xs">
                        <span class="fa fa-trash"></span>
                    </a>
                </td>
            `);
        if(cur_frm.catalog_settings.enable_size_chart == 1){
            new_row = $(`
                <td style="width:5%;text-align: center;">
                    <img src="/assets/go1_commerce/images/section-icon.svg" 
                        style="height:18px;cursor: all-scroll;position: relative;">
                                ${idx}
                </td>
                <td style="width:15%;display:none;">
                    <div class="product_attribute"></div>
                </td> 
                <td style="width:15%;">
                    <div class="attribute"></div>
                </td> 
                <td style="width:15%;">
                    <div class="control_type_html"></div>
                </td> 
                <td style="width:35%" id="optiontag">
                    <div class="option_html"></div>
                </td>
                <td style="width:15%;"><div class="size_chart"></div></td>                   
                <td class="${btnhide}" style="width: 14%;">
                    <a class="btn btn-success btn-xs" style="margin-right: 8px;background: var(--bg-green);
                            color: var(--text-on-green);">
                        <span class="fa fa-floppy-o" style="display:none;"></span>Edit Options
                    </a>
                    <a class="btn btn-danger btn-xs"><span class="fa fa-trash"></span></a>
                </td>
            `);
        }
        table.find('tbody').find('tr[data-id="'+idx+'"]').html(new_row);
        let index = cur_frm.doc.product_attributes.findIndex(x => x.idx == idx);
        var attr_html = '<div class="form-group option-group" style="margin-bottom: 0px;padding: 5px;"><span >'+cur_frm.doc.product_attributes[index]["attribute"]+'</span></div>'
        let input0 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __("Attribute"),
                "fieldname": "attribute"
            },
            parent: new_row.find('.attribute'),
            only_input: true,
            default: attr_html
        })
        input0.set_value(attr_html)
        var docname = "'"+cur_frm.doc.product_attributes[index]["name"]+"'" 
        var size_chart_value = "'"+cur_frm.doc.product_attributes[index]["size_chart"]+"'" 
        var size_chart_html = '';
        size_chart_html = `
            <div class="form-group option-group" style="margin-bottom: 0px;">
                <div class="control-input-wrapper">
                    <div class="control-input form-control table-multiselect" style="cursor:pointer;" 
                        id="table-multiselect"  onclick="change_field(${docname},${size_chart_value} )" id="change_field">
                        <div class="form-group option-group" style="margin-bottom: 0px;padding: 5px;border-radius:1px solid black;">
                            <span>
            `
        if(cur_frm.doc.product_attributes[index]["size_chart_name"]){
            size_chart_html += cur_frm.doc.product_attributes[index]["size_chart_name"]
        }
        size_chart_html += '</span><div class="control-input-wrapper"></div>'
      if(cur_frm.catalog_settings.enable_size_chart == 1){
        let input11 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __("Size Chart"),
                "fieldname": "size_chart"
            },
            parent: new_row.find('.size_chart'),
            only_input: true,
            default:size_chart_html
        })
        input11.set_value(size_chart_html)
       }
        var controlhtml = `
            <div class="form-group option-group" style="margin-bottom: 0px;">
                <a class="btn btn-sm" style="background: transparent;border-radius: 5px;border: .1rem solid #1b8fdb;
                    box-shadow: none;color: #1b8fdb;" onclick="choose_display_types($(this))" 
                    data-name="${cur_frm.doc.product_attributes[index]["name"]}" data-index="${index}" 
                    data-idx="${idx}" data-control_type="${cur_frm.doc.product_attributes[index]["control_type"]}">
            `
        if(cur_frm.doc.product_attributes[index]["control_type"]){
            controlhtml+=cur_frm.doc.product_attributes[index]["control_type"]
        }
        else{
            controlhtml+="Select"
        }
        controlhtml+='</a></div>'
        let input1 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __("Control Type"),
                "fieldname": "control_type_html"
            },
            parent: new_row.find('.control_type_html'),
            only_input: true,
            default: controlhtml
        })
        input1.set_value(controlhtml)
        var option_data =[]
        if (!varient_option){
             varient_option = []
           }
        let optiondatahtml=""
        $.each(option_data, function (i, s) { 
          var  selected = false
            if(i == 0){
                selected = true
            }    
            var otindex = varient_option.findIndex(obj => obj.option_value == s.options);  
            if(otindex<0){
            optiondatahtml += `
                <li aria-selected="${selected}">
                    <a onclick="option_selection($(this))">
                        <p>
                            <strong>${s.options}</strong>
                        </p>
                    </a>
                </li>
            `
                }
        })
        var optionhtml = `
            <div class="form-group option-group" style="margin-bottom: 0px;">
                <div class="control-input-wrapper">
                    <div class="control-input form-control table-multiselect" id="table-multiselect">`
        if(varient_option){
            varient_option.map(f => {
                var btn_cls = 'btn-default';
                if(f.is_pre_selected==1){
                    btn_cls = 'btn-info';
                }
                var comb_index = f.display_order
                var optindex = cur_frm.doc.attribute_options.findIndex((obj => obj.option_value == f.option_value && 
                                                                                x.attribute == cur_frm.doc.product_attributes[index].product_attribute && 
                                                                                x.attribute_id == cur_frm.doc.product_attributes[index].name));
                cur_frm.doc.attribute_options[optindex]["display_order"] = comb_index
                optionhtml += `
                    <div class="btn-group tb-selected-value" id="multi_input_updatevalue" 
                            style="display: inline-block;margin-right: 5px;margin-bottom: 5px;" 
                            data-value="${f.option_value}" data-name="${f.name}" data-index="${index}">
                        <a class="btn ${btn_cls} btn-xs btn-link-to-form" data-parentidx="${idx}"
                            data-id="${f.option_value}" data-attribute="${cur_frm.doc.product_attributes[index]["product_attribute"]}' 
                            data-index="${index}" data-display_order="${comb_index}" data-option_name="${f.name}" 
                            data-is_pre_selected="${f.is_pre_selected}" data-product_title="${f.product_title}" 
                            data-disable="${f.disable}" data-parent-control-type="${cur_frm.doc.product_attributes[index]["control_type"]}" 
                            data-attribute_color="
                                `
                if(f.attribute_color){
                    optionhtml += f.attribute_color
                }
                optionhtml +=`
                    " onclick="pick_color($(this))" ondblclick="update_attroption($(this))">
                        <img src="/assets/go1_commerce/images/section-icon.svg" 
                            style="height:10px;cursor: all-scroll;position: relative;">
                            ${f.option_value}
                    </a>
                    <a class="btn ${btn_cls} btn-xs btn-remove" data-id="${f.option_value}"
                        data-name="${f.name}" onclick="remove_attroption($(this))">
                        <i class="fa fa-remove text-muted"></i> 
                    </a>
                </div>
                        `
            })
        }
        cur_frm.refresh_field("attribute_options");
        optionhtml  += `
                        <div class="link-field ui-front" style="position: relative; line-height: 1;">
                            <div class="awesomplete">   
                            <input placeholder="Type options..." style="padding: 6px 10px 8px;width: 178px;font-size: 11px;
                                font-weight: 400;" type="text" id="select_options${idx}" keydown="add_option_totable($(this))" 
                                class="input-with-feedback bold" data-fieldtype="Table MultiSelect" data-fieldname="display_options" 
                                placeholder="" data-doctype="Product" data-target="Product" autocomplete="off" aria-owns="awesomplete_list_45" 
                                role="combobox" aria-activedescendant="awesomplete_list_45_item_0"> 
                            <ul role="listbox" data-idx ="${idx}" data-index="${index}" id="awesompletelist_${idx}" 
                                    style="z-index: 100;display:none;width:272px;">
                    `
        optionhtml += optiondatahtml
        optionhtml += `</ul></div></div> 
                            <style>.awesomplete > ul:empty {display: none;}</style>
                        </div></div>`
        let input3 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __("options"),
                "fieldname": "option_html",
                "placeholder": "",
                "read_only":0,
                "onchange": function() {
                    let val = this.get_value();
                   }
            },
            parent: new_row.find('.option_html'),
            only_input: true,
            default: optionhtml,
            value: ""
        });
        input3.set_value(optionhtml)
        $('#select_options'+idx).on("focusin", function(event){
            $("#awesompletelist_"+idx).show()
            var varient_options  = cur_frm.doc.attribute_options.filter( x =>  x.attribute == cur_frm.doc.product_attributes[index].product_attribute && 
                                                                                x.attribute_id == cur_frm.doc.product_attributes[index].name);
            if(!varient_options){
                varient_options = []
            }
            $(this).next().find('li').each(function() {
                let qoindex = varient_options.findIndex(x => x.option_value == $(this).text());
                if(qoindex >= 0){
                    $(this).hide();
                }
                else{
                     $(this).show();
                }
            })
        })
        $('#select_options'+idx).on("focusout", function(event){
            $("#awesompletelist_"+idx).hide()
        })
        $('#select_options'+idx).on("keyup", function(event){
            var val = $(this).val();
            var is_exception = 0;
            if(val.indexOf(",") != -1){
                var val = val.replace(/,(?=\s*$)/, '');
                is_exception = 1;
            }
            me.li_hide_show(val, event,idx, index, this);
            if(event.keyCode == 13 || is_exception == 1){
                me.keypress_option(val, event,idx, index, this);
            }
        })
        $('#select_options'+idx).on("keydown", function(event){
            var val = $(this).val();
            var is_exception = 0;
            if(val.indexOf(",") != -1){
                var val = val.replace(/,(?=\s*$)/, '');
                is_exception = 1;
            }
            if(event.keyCode == 9){
                me.keypress_option(val, event,idx, index, this);
            }
        })
        new_row.find('.btn-success').click(function() {
            me.frm.attribute = cur_frm.doc.product_attributes[index]
            me.frm.trigger('edit_option_list');
        })
        new_row.find('.btn-danger').click(function() {
            var dn = $(this).parent().parent().attr("data-name");
            var op = JSON.parse(cur_frm.doc.product_attributes[index].attribute_option)
            if (!op){
             op = []
           }
           let conf_html = `<p>Removing this variant (<b>${cur_frm.doc.product_attributes[index].attribute}</b>) 
                                will delete the following <b>${op.length}</b> options:</p>`;
            conf_html += "<ul>"
            $(op).each(function(j, n){
                conf_html +=`
                    <li>
                        <b>${cur_frm.doc.product_attributes[index].attribute}:${n.option_value}</b>
                    </li>`
            });
            conf_html+="</ul>";
            frappe.warn("Removing varient will also delete options", conf_html,function () {
                var varnt = cur_frm.doc.product_attributes;
                varnt.splice(index, 1);
                cur_frm.doc.product_attributes = varnt
                var tbl = cur_frm.doc.attribute_options || [];
                var i = tbl.length;
                while (i--){
                    if(tbl[i].attribute == cur_frm.doc.product_attributes[index].product_attribute && tbl[i].attribute_id == cur_frm.doc.product_attributes[index].name){
                        if(cur_frm.get_field("attribute_options").grid.grid_rows){
                            cur_frm.get_field("attribute_options").grid.grid_rows[i].remove();
                        }
                        else{
                            cur_frm.doc.attribute_options.splice(i, 1);
                        }
                    }
                }
                cur_frm.refresh_field("attribute_options");
                cur_frm.dirty()  
                $(this).parent().parent().empty();
                show_alert("Row "+idx+" deleted.")
                cur_frm.create_combination = 1 ;
                me.make(cur_frm.create_combination);    
                },'Continue',true)
        });
    },
    refresh_attribute_row: function(){
        var btnhide = ""
        let wrapper = this.frm.fields_dict["product_attribute_html"].$wrapper;
        let table = wrapper.find("table#attributeWithOptions")
        let me = this;
        var idx = me.idx
        let index = cur_frm.doc.product_attributes.findIndex(x => x.product_attribute == this.product_attribute);
        table.find('tbody').find('tr[data-type="noitems"]').empty();
        var s = ""
        let new_row = $(
            `<tr data-id="${cur_frm.doc.product_attributes[index].idx}" data-attr="${cur_frm.doc.product_attributes[index].attribute}" 
                    data-name="${cur_frm.doc.product_attributes[index].name}">
                <td style="width:5%;text-align: center;">
                    <img src="/assets/go1_commerce/images/section-icon.svg" style="height:18px;
                            cursor: all-scroll;position: relative;">${idx}
                </td>
                <td style="width:15%;display:none;"><div class="product_attribute"></div></td> 
                <td style="width:15%;"><div class="attribute"></div></td> 
                <td style="width:15%;"><div class="control_type_html"></div></td> 
                <td style="width:35%" id="optiontag"><div class="option_html"></div></td>
                <td class="${btnhide}" style="width: 14%;">
                    <a class="btn btn-success btn-xs" 
                        style="margin-right: 8px;background: var(--bg-green);color: var(--text-on-green);">
                        <span class="fa fa-floppy-o" style="display:none;"></span>Edit Options
                    </a>
                    <a class="btn btn-danger btn-xs"><span class="fa fa-trash"></span></a>
                </td>
            </tr>`);
        if(cur_frm.catalog_settings.enable_size_chart == 1){
            new_row = $(`
                <tr data-id="${cur_frm.doc.product_attributes[index].idx}" data-attr="${cur_frm.doc.product_attributes[index].attribute}" 
                    data-name="${cur_frm.doc.product_attributes[index].name}">
                    <td style="width:5%;text-align: center;">
                        <img src="/assets/go1_commerce/images/section-icon.svg" 
                            style="height:18px;cursor: all-scroll;position: relative;">${idx}
                    </td>
                    <td style="width:15%;display:none;"><div class="product_attribute"></div></td> 
                    <td style="width:15%;"><div class="attribute"></div></td> 
                    <td style="width:15%;"><div class="control_type_html"></div></td> 
                    <td style="width:35%" id="optiontag"><div class="option_html"></div></td>
                    <td style="width:15%;" ><div class="size_chart"></div></td>                   
                    <td class="${btnhide}" style="width: 14%;">
                        <a class="btn btn-success btn-xs" style="margin-right: 8px;background: var(--bg-green);
                                color: var(--text-on-green);">
                            <span class="fa fa-floppy-o" style="display:none;"></span>Edit Options
                        </a>
                        <a class="btn btn-danger btn-xs"><span class="fa fa-trash"></span></a>
                    </td>
                </tr> `);
        }
        table.find('tbody').append(new_row);
        var attr_html = `
            <div class="form-group option-group" style="margin-bottom: 0px;padding: 5px;">
                <span>${cur_frm.doc.product_attributes[index].attribute}</span>
            </div>`
        let input0 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __("Attribute"),
                "fieldname": "attribute"
            },
            parent: new_row.find('.attribute'),
            only_input: true,
            default: attr_html
        })
        input0.set_value(attr_html)
        frappe.model.get_value('Product Attribute', {'name': cur_frm.doc.product_attributes[index].product_attribute}, "attribute_name",function(d) {
            cur_frm.doc.product_attributes[index].attribute =  d.attribute_name;
            s = d.attribute_name;
            new_row.find('.attribute').find("span").text(s)
        })
        var docname = "'"+cur_frm.doc.product_attributes[index].name+"'" 
        var size_chart_value = "'"+cur_frm.doc.product_attributes[index].size_chart+"'" 
        var size_chart_html = '';
        size_chart_html = `
            <div class="form-group option-group" style="margin-bottom: 0px;">
                <div class="control-input-wrapper"> 
                    <div class="control-input form-control table-multiselect" style="cursor:pointer;" 
                            id="table-multiselect" onclick="change_field(${docname},${size_chart_value})" 
                            id="change_field">
                        <div class="form-group option-group" style="margin-bottom: 0px;padding: 5px;border-radius:1px solid black;">
                            <span>
            `     
        if(cur_frm.doc.product_attributes[index].size_chart_name){
            size_chart_html += cur_frm.doc.product_attributes[index].size_chart_name
        }
        size_chart_html += '</span><div class="control-input-wrapper">'
        size_chart_html +='</div>'
      if(cur_frm.catalog_settings.enable_size_chart == 1){
        let input11 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __("Size Chart"),
                "fieldname": "size_chart"
            },
            parent: new_row.find('.size_chart'),
            only_input: true,
            default:size_chart_html
        })
        input11.set_value(size_chart_html)
       }
        var controlhtml = `
            <div class="form-group option-group" style="margin-bottom: 0px;">
                <a class="btn btn-sm" style="background: transparent;border-radius: 5px;
                    border: .1rem solid #1b8fdb;box-shadow: none;color: #1b8fdb;" 
                    onclick="choose_display_types($(this))" data-name="${cur_frm.doc.product_attributes[index].name}" 
                    data-index="${index}" data-idx="${idx}" data-control_type="${cur_frm.doc.product_attributes[index].control_type}">
            `
        if(cur_frm.doc.product_attributes[index].control_type){
            controlhtml += cur_frm.doc.product_attributes[index].control_type
        }
        else{
            controlhtml += "Select"
        }
        controlhtml += '</a></div>'
       
        let input1 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __("Control Type"),
                "fieldname": "control_type_html"
            },
            parent: new_row.find('.control_type_html'),
            only_input: true,
            default: controlhtml
        })
        input1.set_value(controlhtml)
        let optiondatahtml = ""
        var option_data = []
        var varient_option  = cur_frm.doc.attribute_options.filter( x => x.attribute == cur_frm.doc.product_attributes[index].product_attribute && 
                                                                         x.attribute_id == cur_frm.doc.product_attributes[index].name);
        if (!varient_option){
             varient_option = []
           }
        $.each(option_data, function (i, s) { 
            var selected = false
            if( i == 0){
                selected = true
            } 
            var otindex = varient_option.findIndex(obj => obj.option_value == s.options);  
            if(otindex < 0){            
            optiondatahtml += `
                <li aria-selected="${selected}">
                    <a onclick="option_selection($(this))">
                        <p>
                            <strong>${s.options}</strong>
                        </p>
                    </a>
                </li>`;
            }
        })
        var optionhtml = `
            <div class="form-group option-group" style="margin-bottom: 0px;">
                <div class="control-input-wrapper">
                    <div class="control-input form-control table-multiselect" id="table-multiselect">
            `
        if(cur_frm.doc.product_attributes){
            varient_option.map(f => {
                var btn_cls = 'btn-default';
                if(f.is_pre_selected==1){
                    btn_cls = 'btn-info';
                }
                var comb_index = f.display_order
                let objIndex = cur_frm.doc.attribute_options.findIndex((obj => obj.option_value == f.option_value && f.attribute == cur_frm.doc.product_attributes[index].product_attribute && f.attribute_id == cur_frm.doc.product_attributes[index].name));
               
                cur_frm.doc.attribute_options[objIndex].display_order = comb_index
                optionhtml += `
                    <div class="btn-group tb-selected-value" id="multi_input_updatevalue" style="display: inline-block;
                            margin-right: 5px;margin-bottom: 5px;" data-value="${f.option_value}" data-name="${f.name}" 
                            data-index="${index}">
                        <a class="btn ${btn_cls} btn-xs btn-link-to-form" data-parentidx="${idx}" data-id="${f.option_value}" 
                            data-attribute="${cur_frm.doc.product_attributes[index].product_attribute}" data-index="${index}" 
                            data-display_order="${comb_index}" data-option_name="${f.name}" data-is_pre_selected="${f.is_pre_selected}" 
                            data-product_title="${f.product_title}" data-disable="${f.disable}" 
                            data-parent-control-type="${cur_frm.doc.product_attributes[index].control_type}"
                            data-attribute_color="
                    `
                if(f.attribute_color){
                    optionhtml += f.attribute_color
                }
                optionhtml +=`
                    " onclick="pick_color($(this))" ondblclick="update_attroption($(this))">
                        <img src="/assets/go1_commerce/images/section-icon.svg" 
                            style="height:10px;cursor: all-scroll;position: relative;">${f.option_value}
                        </a>    
                        <a class="btn ${btn_cls} btn-xs btn-remove" data-id="${f.option_value}"
                            data-index="${objIndex}" onclick="remove_attroption($(this))">
                            <i class="fa fa-remove text-muted"></i> 
                        </a></div>
                    `
            })
            cur_frm.refresh_field("attribute_options");
        }
        optionhtml += `
            <div class="link-field ui-front" style="position: relative; line-height: 1;">
                <div class="awesomplete">
                    <input placeholder="Type options..." style="padding: 6px 10px 8px;width: 178px;
                        font-size: 11px;font-weight: 400;" type="text" id="select_options${this.product_attribute}
                        keydown="add_option_totable($(this))" class="input-with-feedback bold" data-fieldtype="Table MultiSelect" 
                        data-fieldname="display_options" placeholder="" data-doctype="Product" data-target="Product" 
                        autocomplete="off" aria-owns="awesomplete_list_45" role="combobox" aria-activedescendant="awesomplete_list_45_item_0">
                    <ul role="listbox" data-index="${index}" data-idx ="${idx}" id="awesompletelist_${this.product_attribute}"
                        style="z-index: 100;display:none;width:272px;">
            `   
        optionhtml += optiondatahtml
        optionhtml += '</ul>'
        optionhtml += '</div> </div>'
        optionhtml += '<style>.awesomplete > ul:empty {display: none;}</style>'
        optionhtml += '</div></div>'
        let input3 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __("options"),
                "fieldname": "option_html",
                "placeholder": "",
                "read_only":0,
                "onchange": function() {
                    let val = this.get_value();
                   }
            },
            parent: new_row.find('.option_html'),
            only_input: true,
            default: optionhtml,
            value: ""
        });
        input3.set_value(optionhtml)
        $('#select_options'+this.product_attribute).on("focusin", function(event){
              $(this).next().show()
        })
         $('#select_options'+this.product_attribute).on("focusout", function(event){

              $(this).next().hide()
        })
        $('#select_options'+this.product_attribute).on("keyup", function(event){
            var val = $(this).val();
            var is_exception = 0;
            if(val.indexOf(",") != -1){
                var val = val.replace(/,(?=\s*$)/, '');
                is_exception = 1;
            }
            me.li_hide_show(val, event,idx, index, this);
            if(event.keyCode == 13 || is_exception == 1){
                me.keypress_option(val, event,idx, index, this);
            }
        })
        $('#select_options'+this.product_attribute).on("keydown", function(event){
            var val = $(this).val();
            var is_exception = 0;
            if(val.indexOf(",") != -1){
                var val = val.replace(/,(?=\s*$)/, '');
                is_exception = 1;
            }
            if(event.keyCode == 9){
                me.keypress_option(val, event,idx, index, this);
            }
        })
        new_row.find('.btn-success').click(function() {
            me.frm.trigger('edit_option_list');
        })
        new_row.find('.btn-danger').click(function() {
            var td = $(this).parent().parent();
            var len = 0;
            if(varient_option){
                len = varient_option.length
            }
            let conf_html = `
                <p>Removing this attribute (<b>${cur_frm.doc.product_attributes[index].attribute}</b>)
                     will delete <b>${len}</b> variants with the following options:
                </p>`;
            conf_html += "<ul>"
            $(varient_option).each(function(j, n){
                conf_html +="<li><b>"+cur_frm.doc.product_attributes[index].attribute+":"+n.option_value+"</b></li>"
            });
            conf_html+="</ul>";
            frappe.warn("Removing varient will also delete options", conf_html,function () { 
                $(td).empty();
                show_alert("Row "+idx+" deleted.")
                cur_frm.doc.product_attributes.splice(index, 1);
                var tbl = cur_frm.doc.attribute_options || [];
                var i = tbl.length;
                while (i--){
                    if(tbl[i].attribute == cur_frm.doc.product_attributes[index].product_attribute && 
                        tbl[i].attribute_id == cur_frm.doc.product_attributes[index].name){
                        if(cur_frm.get_field("attribute_options").grid.grid_rows){
                            cur_frm.get_field("attribute_options").grid.grid_rows[i].remove();
                        }
                        else{
                            cur_frm.doc.attribute_options.splice(i, 1);
                        }
                    }
                }
                cur_frm.refresh_field("attribute_options");
                cur_frm.dirty()  
            },'Continue',true)
        });
    },
    li_hide_show: function(val, event, idx, index,e){
        var input, filter, ul, li, a, i, txtValue, p_text, txtValue_p;
        input = $("#select_options"+this.product_attribute).val();
        filter = input.toUpperCase();
        li = $("#awesompletelist_"+this.product_attribute).find("li");
        for (i = 0; i < li.length; i++) {
            a = li[i].getElementsByTagName("a")[0];
            p_text = li[i].getElementsByTagName("p")[0];
            txtValue = a.textContent || a.innerText;
            txtValue_p = p_text.textContent || p_text.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                li[i].style.display = "";
            } else if (txtValue_p.toUpperCase().indexOf(filter) > -1) {
                li[i].style.display = "";
            } else {
                li[i].style.display = "none";
            }
        }
    },
    keypress_option: function(val, event, idx, index,e){
        var varient_option  = cur_frm.doc.attribute_options.filter( x =>  x.attribute == cur_frm.doc.product_attributes[index].product_attribute && 
                                                                          x.attribute_id == cur_frm.doc.product_attributes[index].name);
        if (!varient_option){
             varient_option = []
           }
        if(val){
            $(e).attr("data-value", val);
            $(e).attr("data-name", "");
            var attr_arr = [];
            var attr_arr_val = "";
            var option_index = 0;
            var pre_selected = 0;
            var btn_cls = 'btn-default';
            if(varient_option){
                option_index = varient_option.length;
            }
            if(option_index == 0){
                pre_selected=1
                btn_cls = 'btn-info';
            }  
            let child = frappe.model.add_child(cur_frm.doc, "Product Attribute Option", "attribute_options");
            child.attribute_id = cur_frm.doc.product_attributes[index]["name"]
            child.display_order = 0
            child.price_adjustment = 0
            child.option_value = $(e).attr("data-value")
            child.attribute = cur_frm.doc.product_attributes[index]["product_attribute"];
            cur_frm.refresh_field("attribute_options");
            var optionhtmls = `
                <div class="btn-group tb-selected-value" id="multi_input_updatevalue" style="display: inline-block;
                    margin-right: 5px;margin-bottom: 5px;" data-value="${val}" data-name="" data-index="${index}">
                    <a class="btn ${btn_cls} btn-xs btn-link-to-form" data-id="${val}" 
                        data-attribute="${cur_frm.doc.product_attributes[index]["product_attribute"]}" data-index="${index}" 
                        data-option_name="" data-display_order="${cur_frm.doc.product_attributes[index]["display_order"]}"
                        data-is_pre_selected="${cur_frm.doc.product_attributes[index]["is_pre_selected"]}"
                        data-product_title="${cur_frm.doc.product_attributes[index]["product_title"]}"  
                        data-disable="${cur_frm.doc.product_attributes[index]["disable"]}"
                        data-parent-control-type="${cur_frm.doc.product_attributes[index]["control_type"]}" 
                        data-attribute_color="
                    `
            if($(e).attr("data-attribute_color")){
                optionhtmls += $(e).attr("data-attribute_color")
            }
            optionhtmls +=`
                " onclick="pick_color($(this))" ondblclick="update_attroption($(this))">
                    <img src="/assets/go1_commerce/images/section-icon.svg" 
                        style="height:10px;cursor: all-scroll;position: relative;">${val}</a>
                <a class="btn ${btn_cls} btn-xs btn-remove" data-id="${val}" data-index="${child.idx}"
                    onclick="remove_attroption($(this))">
                        <i class="fa fa-remove text-muted"></i> 
                </a></div>
                        `
            $(e).parent().parent().before(optionhtmls);
            $(e).parent().parent().parent().find("input").val("");    
            $(e).parent().parent().parent().find('.tb-selected-value').each(function() {  
                var option_index=0;
                if(varient_option){
                    option_index = varient_option.length;
                }
                var doc = {"doctype":"Product Attribute Option",
                            "attribute": cur_frm.doc.product_attributes[index].product_attribute,
                            "attribute_color": $(this).attr("data-attribute_color"),
                            "attribute_id": cur_frm.doc.product_attributes[index].name,
                            "disable": 0,"display_order": 1,"idx": option_index,"image": "",
                            "image_list": null,"is_pre_selected": 0,"option_value": $(this).attr("data-value"),
                            "parent": cur_frm.doc.name,"parentfield": "attribute_options",
                            "parenttype": "Product","parent_option":"",
                            "price_adjustment": 0,"product_title": "-","quantity": 0,"unique_name": "", 
                            "name":$(this).attr("data-name")}
                attr_arr.push(doc);
                if(attr_arr_val){
                    attr_arr_val += ", "
                }
                attr_arr_val += $(e).attr("data-value");
            })
        }
    }
})

frappe.provide("frappe.ui");

var ProductTemplateWizard = Class.extend({
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
            method: 'go1_commerce.go1_commerce.doctype.product.product.get_product_templates',
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
        slides.push(this.update_inventory());
        slides.push(this.update_variant());
        this.slides = slides;
    },
    make_dialog: function() {
        this.dialog = new frappe.ui.Dialog({
            title: __("Setup Product"),
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
        let fields = [
       
        {
            "fieldname": "price",
            "fieldtype": "Currency",
            "reqd": 1,
            "label": __("Price")
        }];
       
        let slide = {
            "name": "basic",
            "title": "Product Information",
            "fields": fields,
            "onload": function(s) {
              
                me.slide_onload(fields, s, me);
            }
        }
        return slide;
    },
     update_inventory: function() {
        let me = this;
        let fields = [
       { "fieldname": "stock", "fieldtype": "Int", "label": __("Stock") },
          ];
        let slide = {
            "name": "inventory",
            "title": __("Product Inventory"),
            "fields": fields,
            "onload": function(s) {
                me.slide_onload(fields, s, me);
            }
        }
        return slide;
    },
    update_variant: function() {
        let me = this;
        let fields = [
            { "fieldname": "product_variant_combination_html", "fieldtype": "HTML", "label": __("Product Combination") },
          ];
        let slide = {
            "name": "variant_combination",
            "title": __("Variant Combination"),
            "fields": fields,
            "onload": function(s) {
                let slide_scope = this;
                setTimeout(function() {
                    slide_scope.bind_html(s);
                }, 1000);
                
            },
            bind_html: function(s) {
                let wrapper = s.form.fields_dict.product_variant_combination_html.$wrapper.empty();
                $(`<table class="table table-bordered">
                    <thead>
                        <tr>
                        <th>${__("Combination")}</th>
                            <th>${__("Stock")}</th>
                            <th>${__("Price")} Name</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                    </table>`).appendTo(wrapper);
                if(me.template_detail) {
                    me.template_detail.variant_combination.map(f => {
                        let rows = frappe.model.add_child(me.template_detail, "Multi Vendor Variant Pricing", "vendor_variant_pricing");
                        rows.combination_html = f.attribute_html;
                        rows.combination = f.attribute_id;
                        rows.vendor_id = cur_frm.vendor_business
                        let row = $(`<tr>
                                    <td style="width: 35%;">${__(f.attribute_html)}</td>
                                    <td><div class="stock_html"></div></td>
                                    <td><div class="price_html"></div></td>
                                 </tr>`);
                        let stock = frappe.ui.form.make_control({
                            df: {
                                "fieldtype": "Int",
                                "label": __("Stock"),
                                "fieldname": "stock",
                                "default": 0,
                                "onchange": function() {
                                    let val = this.get_value();
                                    rows.stock = val;
                                    }
                            },
                            parent: row.find('.stock_html'),
                            only_input: true,
                            value: 0
                        })
                        stock.make_input();
                        stock.set_value(0)
                        let price = frappe.ui.form.make_control({
                            df: {
                                "fieldtype": "Currency",
                                "label": __("Price"),
                                "fieldname": "price",
                                "default": 0,
                                "onchange": function() {
                                    let val = this.get_value();
                                    rows.price = val;
                                    }
                            },
                            parent: row.find('.price_html'),
                            only_input: true,
                            value: 0
                        })
                        price.make_input();
                        price.set_value(0)
                        cur_frm.refresh_field("vendor_variant_pricing");
                        wrapper.find('tbody').append(row);
                    })
                } 
                else {
                    wrapper.find('tbody').append(`<tr data-type="noitem"><td colspan="3">${__("No Records Found!")}</td></tr>`);
                }
               
            }
        }
        return slide;
    },
    slide_onload: function(fields, slide, me) {
        $(fields).each(function(k, v) {
            slide.get_input(v.fieldname).unbind("change").on("change", function() {
                let val = $(this).val() || "";
                me.wizard.values[v.fieldname] = val;
                if(v.fieldname=="price"){
                     me.wizard.values[v.fieldname] = parseFloat(val);
                }
                 if(v.fieldname=="stock"){
                     me.wizard.values[v.fieldname] = parseInt(val);
                }
            });
        });
        if (!me.template) {
            setTimeout(function() {
                $(fields).each(function(k, v) {
                    if (me.wizard.values[v.fieldname]) {
                        slide.get_field(v.fieldname).set_input(me.wizard.values[v.fieldname])
                        if(v.fieldname=="price"){
                             slide.get_field(v.fieldname).set_input(parseFloat(me.wizard.values[v.fieldname]))
                        }
                         if(v.fieldname=="stock"){
                             slide.get_field(v.fieldname).set_input(parseInt(me.wizard.values[v.fieldname]))
                        }
                    }
                })
            }, 500);
        }
    },
    get_validations: function() {
        let me = this;
        let fields = [
            { "fieldname": "price", "fieldtype": "Currency", "label": __("Price") }
        ];
        let slide = {
            "name": "validations",
            "title": __("Product Validations"),
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
        if (me.template){
            slide_type = 'add';
        }
        else{
            slide_type = 'edit'
        }
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
            this.wizard.values = this.template_detail;
            let rows = frappe.model.add_child(this.template_detail, "Multi Vendor Pricing", "pricing_details");
            rows.vendor_id = cur_frm.vendor_business
            rows.price = parseFloat(this.template_detail.price);
            rows.stock = parseInt(this.template_detail.stock);
            this.wizard.values["pricing_details"].push(rows)
        } 
        else {
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
            if (this.frm_action == 'add') {
                this.add_new_product();
            } else {
                this.edit_product();
            }
        }
    }
    add_new_product() {
        if (!this.values['price']){
            frappe.throw('Please enter price value')
        }
        frappe.call({
            method: 'go1_commerce.go1_commerce.v2.product.update_doc',
            args: {
                doc: this.values
            },
            callback: function(r) {
                if (r.message) {
                    frappe.set_route('Form', 'Product', r.message.name);
                    cur_dialog.hide();
                }
            }
        })
    }
    edit_product() {
        cur_frm.save();
        cur_dialog.hide();
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

var UppyUploadComponent = Class.extend({
    init: function(opts) {
        this.frm = opts.frm;
        this.htmlfield = opts.htmlfield;
        this.parentfield = opts.parentfield;
        this.childdoctype = opts.childdoctype;
        this.childdocname = opts.childdocname;
        this.img_field = opts.img_field
        this.make();
    },
    make: function() {
        this.image_dialog();
    },
    image_dialog: function() {
        let me = this;
        frappe.run_serially([
            () => { 
                me.get_image_album(me.frm.doctype, me.frm.docname); 
            },
            () => { me.show_img_dialog(); }
        ])
    },
    show_img_dialog: function() {
        let me = this;
        this.imagedialog = new frappe.ui.Dialog({
            title: __("Image Gallery"),
            fields: [
                { "fieldname": "tab_html", "fieldtype": "HTML" },
                { "fieldname": "sec_1", "fieldtype": "Section Break" },
                { "fieldname": "upload_img", "fieldtype": "HTML" },
                { "fieldname": "sec_2", "fieldtype": "Section Break" },
                { "fieldname": "image_gallery", "fieldtype": "HTML" }
            ]
        });
        this.imagedialog.set_primary_action(__('Save'), function() {
            let active_tab = me.imagedialog.fields_dict.tab_html.$wrapper.find('li.active').attr('data-id');
            let image = "";
            if (active_tab == '2') {
                image = me.picked_image;
            } else if (active_tab == '1') {
                image = me.uploaded_image;
            }
            $(me.list_section_data).each(function(k, v) {
                if (v.idx == rec.idx) {
                    v.image = image;
                }
            });
            me.imagedialog.hide();
        });
        this.imagedialog.show();
        this.gallery_tab_html();
        this.uploader_component();
        this.gallery_html();
        this.imagedialog.$wrapper.find('.modal-dialog').css("width", "800px");
        this.imagedialog.$wrapper.find('.form-section').css("border-bottom", "0");
    },
    get_doc_files: function(dt, dn) {
        let me = this;
        frappe.call({
            method: 'ecommerce_business_store.ecommerce_business_store.doctype.product.product.get_doc_images',
            args: {
                dt: dt,
                dn: dn
            },
            async: false,
            callback: function(r) {
                if (r.message) {
                    me.doc_files = r.message;
                } else {
                    me.doc_files = [];
                }
            }
        })
        
    },
    get_image_album: function(dt, dn) {
        let me = this;
        frappe.call({
            method: 'frappe.core.doctype.file.file.get_files_in_folder',
            args: {
               folder:"Home"
            },
            async: false,
            callback: function(r) {
                me.folder_name="Home"
                if (r.message) {
                    me.gallery_data = r.message;
                } else {
                    me.gallery_data = [];
                }
            }
        })
        
    },
    gallery_tab_html: function() {
        let me = this;
        let tab_html = this.imagedialog.fields_dict.tab_html.$wrapper.empty();
        $(`<div class="gal-tabs">
            <ul>
                <li class="active" data-id="1">${__("Upload Image")}</li>
                <li data-id="2">${__("Media Library")}</li>
            </ul>
        </div>
        <style>
            div[data-fieldname="tab_html"]{ margin-bottom: 0; }
            div[data-fieldname="tab_html"] .gal-tabs{ text-align: left; }
            div[data-fieldname="tab_html"] .gal-tabs ul{display: inline-flex;list-style:none;padding-left:0px;}
            div[data-fieldname="tab_html"] .gal-tabs ul li{padding: 5px 25px;cursor: pointer;font-size: 15px;font-weight: 500;}
            div[data-fieldname="tab_html"] .gal-tabs ul li.active{border-bottom: 2px solid #1b8fdb}
        </style>`).appendTo(tab_html);
        this.imagedialog.fields_dict.sec_2.wrapper.hide();
        tab_html.find('li').click(function() {
            tab_html.find('li').removeClass('active');
            if ($(this).attr('data-id') == '1') {
                me.imagedialog.fields_dict.sec_2.wrapper.hide();
                me.imagedialog.fields_dict.sec_1.wrapper.show();
                tab_html.find('li[data-id="1"]').addClass('active');
            } else {
                me.imagedialog.fields_dict.sec_1.wrapper.hide();
                me.imagedialog.fields_dict.sec_2.wrapper.show();
                tab_html.find('li[data-id="2"]').addClass('active');
            }
        });
    },
    gallery_html: function() {
        let me = this;
        let gallery_html = this.imagedialog.fields_dict.image_gallery.$wrapper.empty();
        var folders = me.folder_name.split("/");
        var nav = '<div class="">'
        $(folders).each(function (k, v) {
           var nav_sub ='<a id="folder-values" data-name="'+v+'">'+v+'</a>'
            nav += nav_sub 
        })
        nav += '</div>'
        if (this.gallery_data && this.gallery_data.length > 0) {
            $(`
                ${nav}<div class="gallery row" style=""></div>
                    <style>
                        div[data-fieldname="image_gallery"] .gallery.row{
                            padding-right: 20px;padding-left: 20px;
                        }
                        div[data-fieldname="image_gallery"] .gallery .gal-items{
                            position: relative;}
                        div[data-fieldname="image_gallery"] .gallery .gal-items img{
                            position: absolute; top: 50%; left: 50%; vertical-align: middle;
                            transform: translate(-50%, -50%); width: auto; height: 90%;
                        }
                        div[data-fieldname="image_gallery"] .gallery .gal-items.active{
                            border: 1px solid #0bc50b;}
                        input[type="checkbox"]:checked:before {
                            font-size: 15px;color: #2ec508;margin-top: -5px;margin-left: -1px;}
                    </style>`).appendTo(gallery_html);
            this.gallery_data.map(f => {
                if(f.is_folder==0){
                    let row = $(`<div class="col-md-3 gal-items" style="margin-bottom: 10px; height: 100px;padding: 0px;width: 15%;"><input type="checkbox" name="selected_file" style="border: 0px;display:none;"/><img src="${f.file_url}" style="width: 85px;
                    height: 75px;"/></div>`);
                    gallery_html.find('.gallery').append(row);
                    row.click(function() {
                        gallery_html.find('.gal-items').removeClass('active');
                        gallery_html.find('.gal-items').find('input[type="checkbox"]').prop("checked", false);
                        gallery_html.find('.gal-items').find('input[type="checkbox"]').css("display", "none");
                        row.addClass('active');
                        row.find('input[type="checkbox"]').prop("checked", true);
                        row.find('input[type="checkbox"]').css("display", "block");
                        me.picked_image = f.file_url;
                    });
                }
                else{
                let row = $(`<div class="col-md-3 gal-items" style="cursor: pointer;margin-bottom: 10px;width: 15%; height: 100px;padding: 0px;">
                                <img src="/assets/ecommerce_business_store/images/folder.png" style="width: 85px;height: 75px;"/>
                                    <span style="float: center;text-align: center;position: absolute;
                                        margin: 43px;margin-left: 22px;font-size: 11px;font-weight: 500;">
                                        ${f.file_name}
                                    </span>
                            </div>`);
                gallery_html.find('.gallery').append(row);
                row.click(function() {
                    me.folder_name = f.name;
                    frappe.call({
                        method: 'frappe.core.doctype.file.file.get_files_in_folder',
                        args: {
                           folder:f.name
                        },
                        async: false,
                        callback: function(r) {
                           
                            if (r.message) {
                                me.gallery_data = r.message;
                            } else {
                                me.gallery_data = [];
                            }
                            me.gallery_html()
                        }
                    }) 
                });
            }
            });
            gallery_html.find('.gallery').slimScroll({
                height: 300
            })
            $('#folder-values').click(function() {
                me.folder_name=$(this).attr("data-name");
              
                me.get_folder_items(me.folder_name);
            })
        } 
        else {
            gallery_html.append(`<div style="text-align: center;background: #ddd;padding: 10%;font-size: 20px;border: 1px solid #ccc;border-radius: 4px;">No images found!</div>`)
        }
    },
    uploader_component: function() {
        let me = this;
        me.get_doc_files(me.childdoctype, me.childdocname);
        let uploader = this.imagedialog.fields_dict.upload_img.$wrapper.empty();
        let random = parseInt(Math.random() * 10000);
        uploader.append(`
            <div id="uploaded_docfile_list"></div>
            <div id="uploader${random}"></div>
            <div id="progress${random}" style="display:none"></div>
            <button class="btn btn-info" id="upload-btn-uppy" style="display:none;width: 115px;">Upload</button>
            <style> 
                .uppy-DragDrop-inner {
                    padding: 0px;font-size: 10px;}
                .uppy-DragDrop-label{
                    display:none;}
                .uppy-DragDrop-inner svg{
                    display:none;}
                .uppy-StatusBar:before {
                         width: 38%; }
                .uppy-StatusBar-progress{width: 38%;}
                .uppy-StatusBar-content{width: 38%;}
                .uppy-StatusBar.is-waiting .uppy-StatusBar-actions {width: 62%;}
                .uppy-StatusBar.is-waiting .uppy-StatusBar-actionBtn--upload {
                    font-size:10px;line-height: 0;}
                .uppy-StatusBar.is-waiting .uppy-StatusBar-actions {height: 50%;
            }</style>`);
        setTimeout(function() {
            uploader.find('#uploader'+random+' .uppy-Root.uppy-DragDrop-container').css({"width": "10%", "padding": "8px"});
            uploader.find('#uploader'+random+' .uppy-Root.uppy-DragDrop-container .uppy-DragDrop-inner').
                        prepend('<img id="upload-input" src="/assets/ecommerce_business_store/images/icons8-plus-+-50.png" style="cursor: pointer" />');
            uploader.find('#upload-input').on("click", function(){
                uploader.find('input.uppy-DragDrop-input').click();
            })
        }, 1000);
        $(`<div class="docgallery" style=""></div>`).appendTo(uploader.find("#uploaded_docfile_list"));
        this.doc_files.map(f => {
            let row = $(`<div class="col-md-3 gal-items" style="margin-bottom: 10px; height: 100px;padding: 0px;width: 15%;">
                            <input type="checkbox" name="selected_file" style="border: 0px;display:none;"/>
                                <img src="${f.product_image}" style="width: 85px;
                                        height: 75px;"/></div>`);
            uploader.find(".docgallery").append(row);
        });
        setTimeout(function() {
            me.upload_component(`#uploader${random}`, `#progress${random}`);
        }, 500);
    },
    upload_component: function(target, progress) {
        let me = this;
        var uppy = Uppy.Core({
                restrictions: {
                    maxFileSize: 1000000,
                    maxNumberOfFiles: 3,
                    allowedFileTypes:['image/*','.jpg','.png','.jpeg','.gif', '.webp']
                },
                meta: {
                    doctype: me.frm.doctype,
                    docname: me.frm.docname,
                    child_doc: me.childdoctype,
                    child_name: me.childdocname,
                    attached_to_field: me.parentfield,
                    img_field: me.img_field
                }
            })
            .use(Uppy.DragDrop, {
                target: target,
                inline: true,
                locale:{
                    strings:{
                        dropPaste:  '%{browse}'
                    }                    
                },
                width:"15%",
                height:"15%"
            })
            .use(Uppy.XHRUpload, {
                endpoint: window.location.origin + '/api/method/go1_commerce.go1_commerce.doctype.product.product.upload_galleryimg',
                method: 'post',
                formData: true,
                fieldname: 'file',
                headers: {
                    'X-Frappe-CSRF-Token': frappe.csrf_token
                }
            })
            .on('upload-success', function(file, response) {
                if (response.status == 200) {
                    me.uploader_component();
                }
            });
            let uploader = this.imagedialog.fields_dict.upload_img.$wrapper;
            uppy.on('file-added', (file) => {
                uploader.find(target+' .uppy-Root.uppy-DragDrop-container .uppy-DragDrop-inner img').remove();
                $(uppy.getFiles()).each(function (k, v) {
                    var reader = new FileReader();
                    reader.readAsDataURL(v.data);
                    reader.onload = function (e) {
                        var items = ''
                        items +='<img src="'+e.target.result+'" style="width: 50px;height: 50px;padding:2px;" />'
                        uploader.find(target+' .uppy-Root.uppy-DragDrop-container .uppy-DragDrop-inner').prepend(items);
                    };
                })
                uploader.find('button#upload-btn-uppy').css("display", "block");
                uploader.find(target+' .uppy-Root.uppy-DragDrop-container .uppy-DragDrop-inner #upload-input').css("display", "none");
              })
            uploader.find('#upload-btn-uppy').on("click", function(){
                uppy.upload();
            })
    },
    isFile: function(input) {
        if ('File' in window && input instanceof File)
           return true;
        else return false;
     },
    isBlob: function(input) {
         if ('Blob' in window && input instanceof Blob)
             return true;
         else return false;
     },
    get_folder_items: function(folder){
        let me = this;
        me.folder_name = folder;
        frappe.call({
            method: 'frappe.core.doctype.file.file.get_files_in_folder',
            args: {
               folder:folder
            },
            async: false,
            callback: function(r) {
               
                if (r.message) {
                    me.gallery_data = r.message;
                } else {
                    me.gallery_data = [];
                }
                me.gallery_html()
            }
        })
    }
})



frappe.ui.form.on("Product Attribute Mapping", {
    product_attribute: function (frm, cdt, cdn) {
        var d = frappe.get_doc(cdt, cdn);
        if (d.product_attribute) {
            for (var i = 0; i < frm.doc.product_attributes.length; i++) {
                if (frm.doc.product_attributes[i].name != d.name) {
                    if ((frm.doc.product_attributes[i].product_attribute) == (d.product_attribute)) {
                        frappe.throw("Product Attribute already exists")
                        frm.set_value('product_attribute', '');
                    }
                }
            }
        }
    },
    before_product_attributes_remove: function (frm, cdt, cdn) {
        let items = locals[cdt][cdn];
        if (!items.__islocal) {
            frappe.call({
                method: "go1_commerce.go1_commerce.doctype.product.product.show_attribute_deletion_err",
                args: {
                    'row_id': cdn,
                    'item': frm.doc.name
                },
                async: false,
                always: function (r) {
                    if (r.message == "Failed") {
                        var att = attribute_name = frappe.get_doc("Product Attribute Mapping", cdn)
                        frappe.throw("Cannot delete because Product Attribute " + att.product_attribute + " is linked with Product Attribute Combination")
                        throw "cannot delete attribute options";
                    } 
                    else {
                        frappe.call({
                            method: 'go1_commerce.go1_commerce.doctype.product.product.delete_attribute_options',
                            args: {
                                dt: cdt,
                                dn: cdn
                            },
                            async: false,
                            callback: function (r) {
                                if(r.message.status != 'success') {
                                    throw "cannot delete attribute options";
                                } 
                            }
                        })
                    }
                }
            })
        }
    },
    product_attributes_remove: function (frm, cdt, cdn) {
        frm.save();
    },
    edit_options: function (frm, cdt, cdn){
        var dialog;
        let item = locals[cdt][cdn];
        if (item.__islocal){
            frappe.throw('Please save the document and then try to edit options')
        }
        $("#OptionsData").parent().parent().parent().parent().parent().parent().parent().parent().parent().parent().parent().remove();
        dialog = new frappe.ui.Dialog({
            title: __("Attribute Options"),
            fields: [{
                "fieldtype": "Button",
                "label": __("Save as Template"),
                "fieldname": "save_template"
                }, {
                    "fieldtype": "Button",
                    "label": __("Get Options from Template"),
                    "fieldname": "get_option_template"
                }, {
                    "fieldtype": "Data",
                    "label": __("Option"),
                    "fieldname": "option_value",
                    "reqd": 1
                },
                {
                    "fieldtype": "Int",
                    "label": __("Display Order"),
                    "fieldname": "display_order_no",
                    "reqd": 1
                },
                {
                    "fieldtype": "Float",
                    "label": __("Price Adjustment"),
                    "fieldname": "price_adjustment",
                    "reqd": 1
                },
                {
                    "fieldtype": "Select",
                    "label": __("Parent Option"),
                    "fieldname": "parent_option",
                    "reqd": 0,
                    "options": parent_options,
                    "depends_on": ""
                },
                {
                    "fieldtype": "Float",
                    "label": __("Weight Adjustment"),
                    "fieldname": "weight_adjustment",
                    "reqd": 0,
                    "depends_on": ""
                },
                {
                    "fieldtype": "Color",
                    "label": __("Color"),
                    "description": "Color is applied based on 'Control Type(Color Boxes)' field.",
                    "fieldname": "attribute_color",
                    "depends_on": ""
                },
        
                {
                    "fieldtype": "Button",
                    "label": __("Save"),
                    "fieldname": "update1"
                },
                {
                    "fieldtype": "Button",
                    "label": __("Clear"),
                    "fieldname": "clear"
                },
                {
                    "fieldtype": "Column Break",
                    "fieldname": "cc"
                },
                {
                    "fieldtype": "Data",
                    "label": __("Product Title"),
                    "fieldname": "product_title"
                },
                {
                    "fieldname": "is_pre_selected",
                    "fieldtype": "Check",
                    "label": "Is Pre Selected"
                },
                {
                    "fieldname": "disable",
                    "fieldtype": "Check",
                    "label": "Disable"
                },
                {
                    "fieldname": "available_html",
                    "fieldtype": "HTML",
                    "label": "Next Available Date & Time",
                    "depends_on": "eval: ((doc.disable==1))"
                },
                {
                    "fieldtype": "Button",
                    "label": __("Add / Edit Image"),
                    "fieldname": "add_attribute_image",
                    "depends_on": ""
                },
                {
                    'fieldname': 'attribute_image_html',
                    'fieldtype': 'HTML'
                },
                {
                    "fieldtype": "Button",
                    "label": __("Add Video"),
                    "fieldname": "add_attribute_video",
                    "depends_on": ""
                },
                {
                    "fieldtype": "Button",
                    "label": __("Upload Video"),
                    "fieldname": "upload_attribute_video",
                    "depends_on": ""
                },
                {
                    'fieldname': 'attribute_video',
                    'fieldtype': 'HTML'
                },
        
                {
                    "fieldtype": "Section Break",
                    "fieldname": "sc"
                },
                {
                    'fieldname': 'ht',
                    'fieldtype': 'HTML'
                },
            ]
        });
        $(dialog.$wrapper).find('.modal-dialog').css("width", "992px");
        if($(window).width() < 992){
            $(dialog.$wrapper).find('.modal-dialog').css("width", "100%");
        }
        dialog.fields_dict.save_template.$wrapper.attr("style", "margin-bottom:0px !important;");
        dialog.fields_dict.get_option_template.$wrapper.attr("style", "margin-bottom:0px !important;");
        dialog.fields_dict.option_value.$wrapper.attr("style", "margin-top:-19px !important;");
        dialog.fields_dict.save_template.$wrapper.find('button').attr("style", "float: right;margin-top: -80px;margin-right: -94%;padding: 5px 6px;border-radius: 0px !important;");
        dialog.fields_dict.get_option_template.$wrapper.find('button').attr("style", "float: right;margin-top: -90px;margin-right: -66%;padding: 5px 6px;border-radius: 0px !important;");
        dialog.fields_dict.get_option_template.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
        dialog.fields_dict.save_template.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
        dialog.fields_dict.clear.$wrapper.css('position', 'relative');
        dialog.fields_dict.update1.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
        dialog.fields_dict.clear.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm attr-del');
        dialog.fields_dict.update1.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
        dialog.fields_dict.clear.$wrapper.find('button').removeClass('btn-default').addClass('btn-danger');
        dialog.fields_dict.add_attribute_image.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
        dialog.fields_dict.add_attribute_image.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
        dialog.fields_dict.add_attribute_video.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
        dialog.fields_dict.add_attribute_video.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
        dialog.fields_dict.upload_attribute_video.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
        dialog.fields_dict.upload_attribute_video.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
        var parent_options = [];
        if (item.parent_attribute != undefined) {
            frappe.call({
                method: "go1_commerce.go1_commerce.doctype.product.product.get_parent_product_attribute_options",
                args: {
                    "attribute": item.parent_attribute,
                    "product": frm.docname,
                },
                callback: function (r) {
                    if (r.message != undefined) {
                        var options = r.message;
                        var parent_options_html = '<option></option>';
                        if (options.length > 0) {
                            for (var i = 0; i < options.length; i++) {
                                parent_options_html += '<option value="' + options[i].option_value + '">' + options[i].option_value + '</option>';
                            }
                            $(dialog.$wrapper).find('[data-fieldname="parent_option"]').find("select").html(parent_options_html);
                        }
                    }
                }
            });
        }
        dialog.fields_dict.add_attribute_image.input.onclick = function () {
            var attributeId = $("#hdnAttributeOptionid").val()
            if (attributeId) {
                let attribute_info;
                if(frm.attribute_options) {
                    attribute_info = frm.attribute_options.find(obj => obj.name == attributeId);
                }
                localStorage.setItem('randomuppy', ' ');
                frm.events.generate_attribute_image_html(frm, 'Product Attribute Option', attributeId, attribute_info)
                frm.events.image_upload(frm, 'Product Attribute Option', attributeId, "attribute_images", 'Product Attribute Option', attributeId)
            } 
            else {
                frappe.throw('Please save the document and then try uploading images')
            }
        }
        dialog.fields_dict.add_attribute_video.input.onclick = function () {
            var attributeId1 = $("#hdnAttributeOptionid").val()
            if (attributeId1) {
                save_attribute_video(attributeId1)
            } 
            else {
                frappe.throw('Please save the document and then try add video id')
            }
        }
        dialog.fields_dict.upload_attribute_video.input.onclick = function () {
            var attributeId = $("#hdnAttributeOptionid").val()
            if (attributeId) {
                localStorage.setItem('randomuppy', ' ');
                frm.events.video_upload(frm, 'Product Attribute Option', attributeId, "youtube_video_id", 'Product Attribute Option Video', attributeId)
            } 
            else {
                frappe.throw('Please save the document and then try uploading images')
            }
        }
        dialog.fields_dict.save_template.input.onclick = function () {
            frappe.call({
                method: "go1_commerce.go1_commerce.doctype.product.product.get_product_attribute_options",
                args: {
                    "attribute": frm.selected_doc.product_attribute,
                    "product": frm.docname,
                    "attribute_id": frm.selected_doc.name
                },
                callback: function (r) {
                    var message = r.message;
                    if (r.message.length > 0) {
                        frappe.call({
                            method: "go1_commerce.go1_commerce.doctype.product.product.insert_attribute_template",
                            args: {
                                "attribute": frm.selected_doc.product_attribute,
                                "product_attr": frm.selected_doc.attribute,
                                "message": message
                            },
                            callback: function (data) {
                                frappe.msgprint(__('Template saved successfully!'))
                            }
                        })
                    }
                    else {
                        frappe.msgprint(__(' Please insert the options and save template.'))
                    }
                }
            })
        }
        dialog.fields_dict.get_option_template.input.onclick = function () {
            var dialog1 = new frappe.ui.Dialog({
                title: __('Options Template'),
                fields: [{ 
                    fieldtype: "Link", label: __("Template"), 
                    fieldname: "attribute_template", options: "Product Attribute Template" }
                ],
                primary_action_label: __('Close')
            });
            dialog1.set_primary_action(__('Save'), function () {
                var html = `
                    <input type="hidden" id="hdnAttributeOptionid"/>
                        <input type="hidden" id="hdnSelectedDoc" value="${frm.selected_doc.product_attribute}"/>
                        <input type="hidden" id="hdnSelectedId" value = "${frm.selected_doc.name}"/>
                        <table class="table table-bordered" id="OptionsData">
                            <thead style="background: #F7FAFC;">
                                <tr>
                                    <th>Option</th>
                                    <th>Display Order</th>
                                    <th>Price Adjustment</th>
                                    <th>Weight Adjustment</th><th>Color</th>
                                    <th>Is Pre Selected</th>
                                    <th>Product Title</th>
                                    <th>Disable</th>
                                    <th>Next Available Date & Time</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>           
                    `;
                var value = dialog1.get_values();
                if (value) {
                    frappe.call({
                        method: 'go1_commerce.go1_commerce.doctype.product.product.select_attribute_template',
                        args: {
                            "template_name": value.attribute_template,
                            "attribute": frm.selected_doc.product_attribute,
                            "product": frm.docname,
                            "attribute_id": frm.selected_doc.name
                        },
                        async: false,
                        callback: function (data) {
                            if (data.message) {
                                dialog1.hide();
                                frappe.msgprint(__('Options inserted successfully!'))
                                html += '<tbody>';
                                if (data.message != undefined) {
                                    $.each(data.message, function (i, d) {
                                        html += '<tr id="tr-' + d.name + '" data-image="' + d.image + '"><td>' + d.option_value + '</td> ';
                                        html += ' <td>' + d.display_order + '</td> ';
                                        html += ' <td>' + d.price_adjustment + '</td> ';
                                        html += ' <td>' + d.weight_adjustment + '</td> ';
                                        html += ' <td style="text-align:center;">' + d.attribute_color + '</td> ';
                                        html += ' <td id = "pre_selected" data-preselection= "' + d.is_pre_selected + '">' + d.is_pre_selected + '</td> ';
                                        html += ' <td width="20%"><div style="width: 165px;overflow: hidden;text-overflow: ellipsis;white-space: nowrap;">' + d.product_title + '</div></td> ';
                                        html += ' <td id="disable">' + d.disable + '</td> ';
                                        html += `
                                            <td style="width:20%">
                                                <button class="btn btn-xs btn-success editbtn" data-fieldtype="Button" 
                                                    onclick=EditAttributeOptions("${d.name}")>Edit
                                                </button>
                                                <a class="btn btn-xs btn-danger" style="margin-left:10px;" 
                                                    onclick=DeleteAttributeOption("${d.name }")>Delete</a></td></tr>';
                                            ` 
                                    });
                                }
                                else {
                                    html += '<tr><td colspan="9" align="center">No Records Found.</td></tr>';
                                }
                                html += '</tbody>';
                                html += '</table>';
                                dialog.fields_dict.ht.$wrapper.html(html);
                            }
                        }
                    })
                } else {
                    frappe.throw('Choose Template')
                }
                cur_frm.refresh_fields();
                frm.reload_doc();
            });
            dialog1.show();
        }
        dialog.fields_dict.update1.input.onclick = function () {
            let values = dialog.get_values();
            var option_value = values.option_value;
            var display_order = values.display_order_no;
            var price_adjustment = values.price_adjustment;
            var parent_option = values.parent_option;
            var disable = values.disable;
            var available_datetime = dialog.fields_dict.available_html.$wrapper.find('input').val();
            var weight_adjustment = 0
            if (values.weight_adjustment != undefined && values.weight_adjustment != '') {
                weight_adjustment = values.weight_adjustment;
            }
            var product_title = '-'
            if (values.product_title != undefined && values.product_title != '') {
                product_title = values.product_title;
            }
            var attribute_color = '-';
            if (values.attribute_color != undefined && values.attribute_color != '') {
                attribute_color = values.attribute_color;
            }
            var image = values.image;
            var pre_selected = values.is_pre_selected;
            dialog.fields_dict.attribute_image_html.$wrapper.empty();
            dialog.fields_dict.attribute_video.$wrapper.empty();
            dialog.set_value('is_pre_selected', 0);
            if (image && image.indexOf('/files/') == -1) {
                let image_url = undefined;
                frappe.run_serially([
                    () => {
                        image_url = upload_attribute_image(image, frm.docname, frm.selected_doc.product_attribute, image_url, pre_selected);
                    },
                    () => {
                        if (validateAttributeOptionForm()) {
                            saveattributeoption(frm.docname, frm.selected_doc.product_attribute, option_value, display_order, price_adjustment, weight_adjustment, image_url, pre_selected, attribute_color, product_title, parent_option, disable, available_datetime);
                        }
                    }
                ])
            } else {
                let image = $("div[data-fieldname='image']").find('.attached-file-link').text();
                if (validateAttributeOptionForm()) {
                    saveattributeoption(frm.docname, frm.selected_doc.product_attribute, option_value, display_order, price_adjustment, weight_adjustment, image, pre_selected, attribute_color, product_title, parent_option, disable, available_datetime);
                }
            }
        }
        dialog.fields_dict.clear.input.onclick = function () {
            dialog.fields_dict.attribute_image_html.$wrapper.empty();
            dialog.set_value('is_pre_selected', 0);
            dialog.set_value('option_value', '');
            dialog.set_value('display_order_no', '');
            dialog.set_value('price_adjustment', '');
            dialog.set_value('weight_adjustment', '');
            dialog.set_value('attribute_color', '');
            dialog.set_value('product_title', '');
            dialog.set_value('disable', 0);
            $("div[data-fieldname='image']").find('.missing-image').show();
            $("div[data-fieldname='image']").find('.img-container').hide();
            $("div[data-fieldname='image']").find('.attached-file').hide();
            $('div[data-fieldname="image"]').find('.attached-file-link').text('')
            $('div[data-fieldname="image"]').find('.img-container').find('img').attr('src', '');
            $("#hdnAttributeOptionid").val('');
            dialog.refresh()
        }
        $(dialog.$wrapper).find('div[data-fieldname="image"]').find('.img-container').next().click(function () {
            $('div[data-fieldname="image"]').find('.img-container').find('img').attr('src', '');
        });
        $(dialog.$wrapper).find('div[data-fieldname="image"]').find('.attached-file a.close').on("click", function () {
            let option_id = $('#hdnAttributeOptionid').val();
            let image = $("#tr-" + option_id).attr('data-image')
            if (image != undefined && image != null && image != 'null' && image != 0 && image != "") {
                $("#tr-" + option_id).attr('data-image', '')
                $("div[data-fieldname='image']").find('.attached-file-link').text("");
                dialog.get_field('image').set_value("");
                dialog.get_field('image').refresh();
            }
        })
        $(dialog.$wrapper).find('input[data-fieldname="is_pre_selected"]').on('change', function () {
            let id = $('#hdnAttributeOptionid').val();
            $('div[data-fieldname="ht"]').find('table tbody tr').each(function () {
                if ($(this).attr('id').split("-")[1] != id) {
                    $(this).find('td[id="pre_selected"]').text('0');
                }
            })
        })
    
        $(dialog.$wrapper).addClass('attributeImage');
        if (frm.selected_doc.product_attribute && frm.docname) {
            var html = `
                <input type="hidden" id="hdnAttributeOptionid"/>
                <input type="hidden" id="hdnSelectedDoc" value="${frm.selected_doc.product_attribute}"/>
                <input type="hidden" id="hdnSelectedId" value = "${frm.selected_doc.name}"/>
                <table class="table table-bordered" id="OptionsData">
                    <thead style="background: #F7FAFC;">
                        <tr>
                            <th>Option</th>
                            <th>Display Order</th>
                            <th>Price Adjustment</th>
                            <th>Weight Adjustment</th><th>Color</th>
                            <th>Is Pre Selected</th>
                            <th>Product Title</th>
                            <th> Disable </th>
                            <th> Available Date & Time</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    ` 
            frappe.call({
                method: "go1_commerce.go1_commerce.doctype.product.product.get_product_attribute_options",
                args: {
                    "attribute": frm.selected_doc.product_attribute,
                    "product": frm.docname,
                    "attribute_id": frm.selected_doc.name
    
                },
                callback: function (r) {
                    html += '<tbody>';
                    if (r.message != undefined) {
                        frm.attribute_options = r.message;
                        $.each(r.message, function (i, d) {
                            html += `
                                <tr id="tr-${d.name}" data-image="${d.image}">
                                    <td>${d.option_value}</td>
                                    <td>${d.display_order}</td>
                                    <td>${d.price_adjustment}</td>
                                    <td>${d.weight_adjustment}</td>
                                    <td style="text-align:center;">
                                        ${d.attribute_color}
                                    </td>
                                    <td id = "pre_selected" data-preselection= "${d.is_pre_selected}">
                                        ${d.is_pre_selected}
                                    </td>
                                    <td width="20%">
                                        <div style="width: 165px;overflow: hidden;text-overflow: ellipsis;white-space: nowrap;">
                                            ${d.product_title}
                                        </div>
                                    </td>
                                    <td id="disable">${d.disable}</td>
                                    <td style="width:20%">
                                        <button class="btn btn-xs btn-success editbtn"  data-fieldtype="Button" 
                                            onclick=EditAttributeOptions("${d.name}")>Edit
                                        </button>
                                        <a class="btn btn-xs btn-danger" style="margin-left:10px;" 
                                            onclick=DeleteAttributeOption("${d.name}")>Delete
                                        </a>
                                    </td>
                                </tr>
                            ` 
                        });
                    } else {
                        html += '<tr><td colspan="6" align="center">No Records Found.</td></tr>';
                    }
                    html += '</tbody></table>';
                    dialog.fields_dict.ht.$wrapper.html(html);
                    dialog.show();
                    $("button[data-fieldname='update1']").attr("style", `padding: 5px 10px;font-size: 12px;
                                                        line-height: 1.5;border-radius: 3px;color: #fff;
                                                        background-color: #1d4da5;border-color: #1d4da5;`);
                    $("button[data-fieldname='clear']").removeAttr("class");
                    $("button[data-fieldname='clear']").attr("class", "btn btn-xs btn-danger");
                    $("button[data-fieldname='clear']").attr("style", `padding: 5px 10px;font-size: 12px;line-height: 1.5;
                                                        border-radius: 3px;color: #fff;margin-left: 10px;position: absolute;
                                                        bottom: 5.6%;left: 60px;margin-top: -19px;`)
    
                }
            })
        }

    }
});

frappe.ui.form.on("Product Variant Combination", {
    form_render: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if(!row.role_based_pricing){
            row.role_based_pricing = "[]"
        }
        let data = JSON.parse(row.role_based_pricing);
        var pricing_html = `
            <table class="table table-bordered">
                <thead style="background-color:#f7fafc;">
                    <tr>
                        <th></th>
                        <th style="">Role</th>
                        <th style="">Price</th>
                    </tr>
                </thead>
                <tbody>`;
        if(data.length > 0){
            $.each(data, function (i, f) {
            pricing_html += `
                <tr data-id="${f.idx}">
                    <td>${f.idx}</td>
                    <td>${f.role}</td>
                    <td style="">${parseFloat(f.price).toFixed(2)}${symbol}</td>
                </tr>
             `
            })
     }else{
        pricing_html += `<tr data-type="noitems">
                            <td colspan="3">Records Not Found!</td>
                        </tr>`     
     }
        pricing_html += '</tbody></table>';
        cur_frm.fields_dict["variant_combination"].grid.grid_rows_by_docname[cdn].get_field("pricing_html").$wrapper.empty();
        let wrapper = cur_frm.fields_dict["variant_combination"].grid.grid_rows_by_docname[cdn].get_field("pricing_html").$wrapper
        $(pricing_html).appendTo(wrapper);
        cur_frm.refresh_fields();
    },
    edit_pricing: function (frm, cdt, cdn) {
        var cdt = cdt;
        var cdn = cdn;
        let row = frappe.get_doc(cdt, cdn)
        let data = JSON.parse(row.role_based_pricing)||[];
        let args = {
                'dt': 'Order Settings'
            };
        let order = cur_frm.events.get_settings(cur_frm, args);
        if(data.length <= 0 && order.franchise_role){
            data = [{"role": order.franchise_role, "price":0, "idx":1}]
        }
        const dialog = new frappe.ui.Dialog({
            title: __("Pricing Rule"),
            fields: [
                {
                    fieldtype:'Section Break',
                    label: __('')
                },
                {
                    fieldname: "pricing_rule",
                    fieldtype: "Table", 
                    cannot_add_rows: false,
                    in_place_edit: true,
                    data: data,
                    get_data: () => {
                        return data;
                },
                    fields: [{
                        fieldtype:'Link',
                        fieldname:"role",
                        options: 'Role',
                        in_list_view: 1,
                        read_only: 0,
                        label: __('Role')
                    },{
                        fieldtype:'Currency',
                        fieldname:"price",
                        default: 0,
                        read_only: 0,
                        in_list_view: 1,
                        label: __('Price')
                    }]
                },
            ],
            primary_action_label: __('Save'),
            primary_action: function() {
                var args = dialog.get_values()["pricing_rule"];
                if(!args){
                    args = []
                }
                frappe.model.set_value(cdt, cdn, "role_based_pricing", JSON.stringify(args))
                dialog.hide();
                let row = frappe.get_doc(cdt, cdn);
                if(!row.role_based_pricing){
                    row.role_based_pricing = "[]"
                }
                let data = args
                var pricing_html=`
                    <table class="table table-bordered">
                        <thead style="background-color:#f7fafc;">
                            <tr>
                                <th></th>
                                <th style="">Role</th>
                                <th style="">Price</th>
                            </tr>
                        </thead>
                        <tbody>`;
                if(data.length > 0){
                    $.each(data, function (i, f) {
                    pricing_html += `
                        <tr data-id="${f.idx}">
                            <td>${f.idx}</td>
                            <td>${f.role}</td>
                            <td style="">${parseFloat(f.price).toFixed(2)}${symbol}</td>
                        </tr>
                    `
                    })
                }
                else{
                    pricing_html += '<tr data-type="noitems"><td colspan="3">Records Not Found!</td></tr>'     
                }
                pricing_html += '</tbody></table>';
                cur_frm.fields_dict["variant_combination"].grid.grid_rows_by_docname[cdn].get_field("pricing_html").$wrapper.empty();
                let wrapper = cur_frm.fields_dict["variant_combination"].grid.grid_rows_by_docname[cdn].get_field("pricing_html").$wrapper;
                $(pricing_html).appendTo(wrapper);
            },
            primary_action_label: __('Save')
        });
        dialog.show()
    },
    price: function (frm, cdt, cdn) {
        var d = frappe.get_doc(cdt, cdn);
        if (d.price < frm.doc.price) {
            frappe.throw("Attribute combination price should be greater than or equal to base price")
        }
    },
    before_variant_combination_remove: function (frm, cdt, cdn) {
        if (cur_frm.doc.inventory_method == "Track Inventory By Product Attributes") {
            frappe.msgprint("Please change inventory method and then delete attributes")
            throw "Please change inventory method and then delete attributes"
        }
   }
});

frappe.ui.form.on("Product Brand Mapping", {
    form_render: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if(!row.model_json){
            row.model_json = "[]"
        }
        frm.events.build_multi_selectors(frm, frm.possible_val);
    }
});
