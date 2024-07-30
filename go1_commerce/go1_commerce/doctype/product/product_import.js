let js_import_path = "assets/go1_commerce/js/product/"
let css_import_path = "assets/go1_commerce/css/product/"
let common_path_js = "assets/go1_commerce/js/"
let common_path_css = "assets/go1_commerce/css/"

frappe.require(`${common_path_js}uppy.min.js`);
frappe.require(`${common_path_js}ui/product_func_class.js`);
frappe.require(`${common_path_js}frappe-datatable.min.js`);
frappe.require(`${js_import_path}uppy_upload_component.js`);
frappe.require(`${js_import_path}core_script.js`);
frappe.require(`${js_import_path}jquery-ui.js`);

frappe.require(`${common_path_css}frappe-datatable.min.css`);
frappe.require(`${common_path_css}uppy.min.css`);
frappe.require(`${common_path_css}toggle-slider.css`);
frappe.require(`${css_import_path}uppy-editor.min.css`);
frappe.require(`${css_import_path}jquery-ui.css`);



function add_class(){
    setTimeout(function(){
        $('button[data-fieldname="add_product_image"]').html('<i class="fi fi-rr-plus"></i><br>Add / Edit Image');
    },1000);
    $('button[data-fieldname="add_product_image"]').css("height", "27px");
    $('button[data-fieldname="add_product_image"]').css("background-color", "#1d8fdb");
    $('button[data-fieldname="add_product_image"]').css("color", "#f7f1f1");
    $('button[data-fieldname="add_product_image"]').attr("style",`height: 27px;background-color: #fff;
        color: #222;position: absolute;height: 120px;width: 120px;border: 1px solid #ddd;top: 0;
        border-radius: 5px;`);
    $('div[data-fieldname="product_brands"] .grid-add-row').addClass('hide')
    $('[class="btn btn-xs btn-secondary grid-add-row"]').hide()
    $('div[data-fieldname="product_brands"] .grid-add-multiple-rows').addClass('addProductBrands')
    $('div[data-fieldname="add_product_image"] .grid-add-multiple-rows').addClass('addProductImages')
    $('div[data-fieldname="product_categories"] .grid-footer .grid-add-row').addClass('hide')
    $('div[data-fieldname="product_categories"] .grid-footer .grid-add-multiple-rows').addClass('addCategories')
    $('button[data-fieldname="add_specification_attribute"]').addClass('btn-secondary')
    $('button[data-fieldname="add_product_attribute"]').addClass('btn-secondary')
    $('button[data-fieldname="add_categories"]').addClass('btn-xs')
    $('button[data-fieldname="add_categories"]').addClass('btn-secondary')
    $('button[data-fieldname="add_brands"]').addClass('btn-xs')
    $('button[data-fieldname="add_brands"]').addClass('btn-secondary')
    $('button[data-fieldname="upload_product_video"]').addClass('btn-xs')
    $('button[data-fieldname="upload_product_video"]').addClass('btn-secondary')
    $('button[data-fieldname="pick_return_policy"]').addClass('btn-secondary')
    $('button[data-fieldname="pick_return_policy"]').addClass('btn-xs')
    $('button[data-fieldname="add_return_policy"]').addClass('btn-xs')
    $('button[data-fieldname="add_return_policy"]').addClass('btn-secondary')
    $('button[data-fieldname="pick_specification_attribute"]').addClass('btn-xs')
    $('button[data-fieldname="pick_specification_attribute"]').addClass('btn-secondary')
    $('button[data-fieldname="choose_cross_selling"]').addClass('btn-xs')
    $('button[data-fieldname="choose_cross_selling"]').addClass('btn-secondary')
    $('button[data-fieldname="choose_related_products"]').addClass('btn-xs')
    $('button[data-fieldname="choose_related_products"]').addClass('btn-secondary')
    $('button[data-fieldname="choose_related_categories"]').addClass('btn-xs')
    $('button[data-fieldname="choose_related_categories"]').addClass('btn-secondary')
    $('button[data-fieldname="add_product_attribute"]').addClass('btn-xs')
}

function remove_class(){
    $('div[data-fieldname="product_brands"] .grid-add-multiple-rows').removeClass('hide')
    $('div[data-fieldname="add_product_image"] .grid-add-multiple-rows').removeClass('hide')
    $('div[data-fieldname="add_product_image"] .grid-add-multiple-rows').text('Add / Edit')
    $('div[data-fieldname="product_brands"] .grid-add-multiple-rows').text('Add / Edit')
    $('div[data-fieldname="product_categories"] .grid-footer .grid-add-multiple-rows').removeClass('hide')
    $('div[data-fieldname="product_categories"] .grid-footer .grid-add-multiple-rows').text('Add / Edit')
    $('button[data-fieldname="add_specification_attribute"]').removeClass('btn-xs')
    $('button[data-fieldname="add_specification_attribute"]').removeClass('btn-default')
    $('button[data-fieldname="add_product_attribute"]').removeClass('btn-xs')
    $('button[data-fieldname="add_product_attribute"]').removeClass('btn-default')
    $('button[data-fieldname="add_categories"]').removeClass('btn-default')
    $('button[data-fieldname="add_brands"]').removeClass('btn-default')
    $('button[data-fieldname="upload_product_video"]').removeClass('btn-default')
    $('button[data-fieldname="pick_return_policy"]').removeClass('btn-default')
    $('button[data-fieldname="add_return_policy"]').removeClass('btn-default')
    $('button[data-fieldname="pick_specification_attribute"]').removeClass('btn-default')
    $('button[data-fieldname="choose_cross_selling"]').removeClass('btn-default')
    $('button[data-fieldname="choose_related_products"]').removeClass('btn-default')
    $('button[data-fieldname="choose_related_categories"]').removeClass('btn-default')
}

function attributeOptions_html(r,dialog){
    html += '<tbody>';
    if (r.message != undefined) {
        frm.attribute_options = r.message;
        $.each(r.message, function (i, d) {
            html += `<tr id="tr-${d.name}" data-image="${d.image}">
                        <td>${d.option_value}</td>
                        <td>${d.display_order}</td> 
                        <td>${d.price_adjustment}</td>
                        <td>${d.weight_adjustment}</td>
                        <td style="text-align:center;">
                            ${d.attribute_color}
                        </td>
                        <td id = "pre_selected" data-preselection="${d.is_pre_selected}">
                            ${d.is_pre_selected}
                        </td>
                        <td width="20%">
                            <div style="width: 165px;overflow: hidden;text-overflow: ellipsis;white-space: nowrap;">
                                ${d.product_title}
                            </div>
                        </td>
                        <td id="disable">${d.disable}</td>
                        <td style="width:20%">
                            <button class="btn btn-xs btn-success editbtn"  
                                data-fieldtype="Button" onclick=EditAttributeOptions("${d.name}")>Edit
                            </button>
                            <a class="btn btn-xs btn-danger" style="margin-left:10px;" 
                                onclick=DeleteAttributeOption("${d.name}")>Delete
                            </a>
                        </td>
                    </tr> `;
        });
    } 
    else {
        html += '<tr><td colspan="9" align="center">No Records Found.</td></tr>';
    }
    html += '</tbody>';
    html += '</table>';
    dialog.fields_dict.ht.$wrapper.html(html);
    dialog.show();
    $("button[data-fieldname='update1']").attr("style", `padding: 5px 10px;font-size: 12px;line-height: 1.5;
                            border-radius: 3px;color: #fff;background-color: #1d4da5;border-color: #1d4da5;`);
    $("button[data-fieldname='clear']").removeAttr("class");
    $("button[data-fieldname='clear']").attr("class", "btn btn-xs btn-danger");
    $("button[data-fieldname='clear']").attr("style", `padding: 5px 10px;font-size: 12px;line-height: 1.5;
                            border-radius: 3px;color: #fff;margin-left: 10px;position: absolute;bottom: 5.6%;
                            left: 60px;margin-top: -19px;`)
}

function render_datepicker(frm) {
    let datenight = moment();
    var wrappe = frm.fields_dict["htmlpopulate"].wrapper
    var field = [{ fieldtype: "Datetime", label: "Date Night!", fieldname: "datenight", default: datenight }]
    make_fieldgroup(wrappe, field);
}

function make_fieldgroup(parent, ddf_list) {
    let fg = new frappe.ui.FieldGroup({
        "fields": ddf_list,
        "parent": parent
    });
    fg.make();
}

function create_attribute_combination(frm, v) {
    var combination_price = 0
    var price = 0;
    if (frm.doc.price) {
        combination_price = v.price + frm.doc.price
    }
    if (combination_price >= frm.doc.price) {
        price = combination_price
    }
    let row = frappe.model.add_child(frm.doc, "Product Variant Combination", "variant_combination");
    row.attribute_html = v.attribute_html;
    row.attribute_id = v.attribute_id;
    row.stock = 1;
    row.price = price;
    row.weight = 0;
    row.product_title = v.product_title;
    row.attributes_json = JSON.stringify(v.attributes_json);
}

function brand_dialog(frm) {
    let random = Math.random() * 100;
    let brand_dialog = new frappe.ui.Dialog({
        title: 'Select Brands',
        fields: [{
            "fieldname": "brand_html",
            "fieldtype": "HTML",
            "options": '<div id="brand_list' + parseInt(random) + '"></div>'
        }]
    });
    let selected_brands_list = [];
    brand_dialog.set_primary_action(__('Add'), function () {
        $(selected_brands_list).each(function (k, v) {
            let b;
            if(frm.doc.product_brands) {
                b = frm.doc.product_brands.find(obj => obj.brand == v.brand)
            } 
            else{
                b = null;
            }
            if (b == undefined || b == '' || b == null) {
                let row = frappe.model.add_child(frm.doc, "Product Brand Mapping", "product_brands");
                row.brand = v.brand;
                row.brand_name = v.brand_name;
            }
        })
        cur_frm.refresh_field("product_brands");
        $('div[data-fieldname="product_brands"] .grid-add-row').addClass('hide')
        if (!frm.doc.__islocal){
            cur_frm.save();
        }
        brand_dialog.hide();
    });
    $('.modal[data-types="brand"').each(function () {
        $(this).remove();
    })
    brand_dialog.show()
    new DataTable('#brand_list' + parseInt(random), {
        columns: [{
            name: 'Logo',
            width: 80,
            editable: false,
            format: (value) => {
                if (value){
                    return `<img src="${value}" style="height:30px;" />`
                }
                else{
                    return ''
                }
            }
        },
        {
            'name': 'Brand',
            'width': 129,
            editable: false
        },
        {
            name: 'Brand Name',
            width: 204,
            editable: false
        },
        {
            'name': 'Status',
            editable: false,
            width: 70,
            format: (value) => {
                if (value == 1){
                    return 'Active'
                }
                else{
                    return 'Inactive'
                }
            }
        }],
        data: frm.brands_list,
        inlineFilters: true,
        checkboxColumn: true,
        dynamicRowHeight: true,
        events: {
            onCheckRow: (row) => {
                let brand = row[3].content;
                let check_data = selected_brands_list.find(obj => obj.brand == brand)
                if (check_data) {
                    let arr = [];
                    $(selected_brands_list).each(function (k, v) {
                        if (v.brand == brand) { } else {
                            arr.push(v)
                        }
                    })
                    selected_brands_list = arr;
                } else {
                    selected_brands_list.push({
                        'brand': brand,
                        'brand_name': row[4].content
                    })
                }
            },
            onSortColumn: (column) => {
                $('.datatable .dt-row-header input[type=checkbox]').hide();
                $('.datatable .dt-header .dt-row-filter').show()
                $('.datatable .dt-cell--header').css('background', '#f7f7f7')
            }
        }
    });
    $('.datatable .dt-row-header input[type=checkbox]').hide();
    $('.datatable .dt-header .dt-row-filter').show()
    $('.datatable .dt-cell--header').css('background', '#f7f7f7')
    brand_dialog.$wrapper.find('div[data-fieldname="brand_html"]').css('max-height', '400px')
    brand_dialog.$wrapper.find('div[data-fieldname="brand_html"]').css('overflow-y', 'scroll')
    if (frm.doc.product_brands) {
        $('div[data-fieldname="brand_html"]').find('.dt-cell__content--col-6').each(function () {
            let brand = $(this).text();
            let check_data = frm.doc.product_brands.find(obj => obj.category == brand.trim());
            if (check_data) {
                $(this).parent().parent().find('input[type=checkbox]').trigger('click')
            }
        })
    }
    $(brand_dialog.$wrapper).attr('data-types', 'brand')
}


function category_newdialog(frm) {
    frm.possible_val = [{
        "cls": "custom-product-category",
        "tab_html_field": "category_html",
        "tab_field": "category_json",
        "link_name": "name",
        "title": "Search product category here...",
        "label": "Choose Category",
        "doctype": "Product",
        "reference_doc": "Product Category",
        "reference_fields": escape(JSON.stringify(["name", "category_name"])),
        "search_fields": "category_name",
        "reference_method": "go1_commerce.go1_commerce.doctype.product.product.get_category_list",
        "is_child": 0,
        "description": "Please select the category for this plan.",
        "child_tab_link": "",
        "height": "180px"
    }];
    let categoryDialog;
    var content = []
    categoryDialog = new frappe.ui.Dialog({
        title: __('Select Categories'),
        fields: [{
            label: "Select Category",
            fieldtype: 'Table MultiSelect',
            fieldname: 'category_list',
            options: 'Product Category Mapping',
            hidden: 1
        },
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
    $.each(cur_frm.doc.product_categories, function (i, s) {
        content.push(s.category)
    })
    categoryDialog.get_field('category_json').set_value(JSON.stringify(content));
    categoryDialog.get_field('category_json').refresh();
    categoryDialog.show();
    setTimeout(function () {
        frm.events.build_multi_selector(frm, frm.possible_val);
    }, 1000)
    categoryDialog.set_primary_action(__('Add'), async function () {
        var cat = categoryDialog.get_values();
        var cat_json = JSON.parse(cat.category_json)
        cur_frm.doc.product_categories = [];
        await $(cat_json).each(function (k, v) {
            frappe.db.get_value("Product Category",v,'category_name').then(r =>{
                let row = frappe.model.add_child(frm.doc, "Product Category Mapping", "product_categories");
                row.category = v;
                row.category_name= r.message.category_name;
                frm.refresh_field('product_categories')
            });
        })
        if (cat_json.length <= 0) {
            frappe.throw(__('Please select any one category.'))
        } 
        else {
            refresh_field("selected_category_list");
            frm.refresh_field('product_categories')
            $('div[data-fieldname="product_categories"] .grid-footer .grid-add-row').addClass('hidden')
            categoryDialog.hide();
            if (!frm.doc.__islocal){
                setTimeout(()=>{
                    cur_frm.dirty()
                    cur_frm.save();
                },1000)  
            }
        }
    })
    categoryDialog.$wrapper.find('.modal-dialog').css("min-width",  "70%");
}

function brand_newdialog(frm) {
    frm.possible_val = [{
        "cls": "custom-product-brand",
        "tab_html_field": "category_html",
        "tab_field": "brand_json",
        "link_name": "name",
        "title": "Search product brand here...",
        "label": "Choose Brand",
        "doctype": "Product",
        "reference_doc": "Product Brand",
        "reference_fields": escape(JSON.stringify(["name", "brand_name"])),
        "search_fields": "brand_name",
        "reference_method": "go1_commerce.go1_commerce.doctype.product.product.get_brand_list",
        "is_child": 0,
        "description": "Please select the brand for this product.",
        "child_tab_link": "",
        "height": "180px"
    }];
    let categoryDialog;
    let random = Math.random() * 100;
    var content = []
    categoryDialog = new frappe.ui.Dialog({
        title: __('Select Brands'),
        fields: [{
            label: "Select Brand",
            fieldtype: 'Table MultiSelect',
            fieldname: 'brand_list',
            options: 'Product Brand Mapping',
            hidden: 1
        },
        {
            label: "Select Brand",
            fieldtype: 'HTML',
            fieldname: 'category_html',
            options: ''
        },
        {
            label: "Select Brand",
            fieldtype: 'Code',
            fieldname: 'brand_json',
            options: '',
            read_only: 1,
            hidden: 1
        }
        ],
        primary_action_label: __('Close')
    });
    $.each(cur_frm.doc.product_brands, function (i, s) {
        content.push(s.brand)
    })
    categoryDialog.get_field('brand_json').set_value(JSON.stringify(content));
    categoryDialog.get_field('brand_json').refresh();
    categoryDialog.show();
    setTimeout(function () {
        frm.events.build_multi_selector(frm, frm.possible_val);
    }, 1000)
    categoryDialog.set_primary_action(__('Add'), function () {
        var cat = categoryDialog.get_values();
        var cat_json = JSON.parse(cat.brand_json)
        cur_frm.doc.product_brands = [];
        $(cat_json).each(function (k, v) {
            let row = frappe.model.add_child(frm.doc, "Product Brand Mapping", "product_brands");
            frappe.db.get_value("Product Brand",v,'brand_name').then(r=>{
                row.brand = v;
                row.brand_name= r.message.brand_name;
                frm.refresh_field('product_brands')
            })
        })
        if (cat_json.length <= 0) {
            frappe.throw(__('Please select any one brand.'))
        } else {
            frm.refresh_field('product_brands')
            $('div[data-fieldname="product_brands"] .grid-footer').addClass('hidden')
            categoryDialog.hide();
        }
    })
    categoryDialog.$wrapper.find('.modal-dialog').css("min-width", "1000px");
    categoryDialog.$wrapper.find('.modal-content').css("min-height", "575px");
}

function category_dialog(frm) {
    let categoryDialog;
    let random = Math.random() * 100;
    categoryDialog = new frappe.ui.Dialog({
        title: __('Categories'),
        fields: [{
            fieldtype: 'HTML',
            fieldname: 'category_list',
            options: '<div id="mainCategoryList"><div id="category_list' + parseInt(random) + '"></div></div>'
        }],
        primary_action_label: __('Close')
    });
    let selected_category_list = [];
    categoryDialog.set_primary_action(__('Add'), function () {
        frm.set_value('product_categories', []);
        $(selected_category_list).each(function (k, v) {
            let row = frappe.model.add_child(frm.doc, "Product Category Mapping", "product_categories");
            row.category = v.category;
            row.category_name = v.category_name;
        })
        if((selected_category_list) == 0) {
            frappe.throw(__('Please select any one category.'))
        }
        else {
            refresh_field("selected_category_list");
            frm.refresh_field('product_categories')
            $('div[data-fieldname="product_categories"] .grid-footer .grid-add-row').addClass('hide')
            categoryDialog.hide();
            if (!frm.doc.__islocal){
                cur_frm.save();
            }
        }
    });
    var table = new DataTable('#category_list' + parseInt(random), {
        columns: [{
                'name': 'Category',
                'id': 'category_name',
                'width': 220,
                editable: false
            },
            {
                id: 'category_image',
                width: 150,
                editable: false,
                name: 'Image',
                format: (value) => {
                    if (value){
                        return `<img src="${value}" style="height:30px;" />`
                    }
                    else{
                        return ''
                    }
                }
            },
            {
                'name': 'Parent',
                'id': 'parent_category_name',
                'width': 220,
                editable: false
            },
            {
                'name': 'Status',
                'width': 135,
                'id': 'is_active',
                editable: false,
                format: (value) => {
                    if (value == 1){
                        return 'Active'
                    }
                    else{
                        return 'Inactive'
                    }
                }
            },
            {
                'name': 'Name',
                'width': 134,
                'id': 'name',
                editable: false
            }
        ],
        data: frm.category_list,
        treeView: true,
        inlineFilters: true,
        checkboxColumn: true,
        dynamicRowHeight: true,
        pageLength: 5000,
        events: {
            onCheckRow: (row) => {
                let check_data = selected_category_list.find(obj => obj.category == row[6].content)
                if (check_data) {
                    let arr = [];
                    $(selected_category_list).each(function (k, v) {
                        if (v.category == row[6].content) { } else {
                            arr.push(v)
                        }
                    })
                    selected_category_list = arr;
                } 
                else {
                    selected_category_list.push({
                        'category': row[6].content,
                        'category_name': row[2].content
                    })
                }
            },
            onSortColumn: (column) => {
                $('.datatable .dt-row-header input[type=checkbox]').hide();
                $('.datatable .dt-header .dt-row-filter').show()
                $('.datatable .dt-cell--header').css('background', '#f7f7f7')
            }
        }
    });
    $('.datatable .dt-row-header input[type=checkbox]').hide();
    $('.datatable .dt-header .dt-row-filter').show()
    $('.datatable .dt-cell--header').css('background', '#f7f7f7')
    $('.datatable').find('.dt-paste-target').css('position', 'relative')
    $('.datatable').find('.dt-paste-target').css('display', 'none')
    categoryDialog.$wrapper.find('div[data-fieldname="category_list"]').css('max-height', '400px')
    categoryDialog.$wrapper.find('div[data-fieldname="category_list"]').css('overflow-y', 'scroll')
    categoryDialog.get_close_btn().on('click', () => {
        $('.modal').removeClass('in');
        $('.modal').attr('aria-hidden', 'true')
        $('.modal').css('display', 'none')
        this.on_close && this.on_close(this.item);
    });
    categoryDialog.$wrapper.find('.modal-dialog').css("min-width", "1000px");
    $('.modal[data-types="category"').each(function () {
        $(this).remove();
    })
    categoryDialog.show();
    if (frm.doc.product_categories) {
        $('div[data-fieldname="category_list"]').find('.dt-cell__content--col-6').each(function () {
            let category = $(this).text();
            let check_data = frm.doc.product_categories.find(obj => obj.category == category.trim());
            if (check_data) {
                $(this).parent().parent().find('input[type=checkbox]').trigger('click')
            }
        })
    }
    $(categoryDialog.$wrapper).attr('data-types', 'category')
}

function upload_attribute_image(image, product, attribute) {
    let img_url = undefined;
    if (image) {
        frappe.call({
            method: 'uploadfile',
            args: {
                from_form: 1,
                doctype: cur_frm.doctype,
                docname: cur_frm.docname,
                is_private: 0,
                filename: image.split(',data')[0],
                file_url: '',
                filedata: 'data:' + image.split(',data:')[1]
            },
            async: false,
            callback: function (r) {
                if (r.message) {
                    img_url = r.message.file_url;
                }
            }
        })
    }
    return img_url;
}

function save_attribute_video(attributeId1) {
    if (attributeId1) {
        let video_dialog = new frappe.ui.Dialog({
            title: 'Attribute Video',
            fields: [{
                "fieldname": "video_id",
                "fieldtype": "Data",
                "label": __("Video url")
            }, {
                "fieldname": "video_type",
                "fieldtype": "Select",
                "label": __("Video Type"),
                "options": ["Youtube,Vimeo,Other"],
                "default": "Youtube"
            }],
            primary_action_label: __('Close')
        });
        video_dialog.show();
        video_dialog.set_primary_action(__('Add'), function () {
            var html = `<table class="table table-bordered" id="OptionsData1">
                            <thead style="background: #F7FAFC;">
                                <tr>
                                    <th>Video url</th>
                                    <th>Type</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>`;
            let values = video_dialog.get_values();
            frappe.call({
                method: `go1_commerce.go1_commerce.doctype.product.product.insert_attribute_option_video`,
                args: {
                    "option_id": attributeId1,
                    "video_id": values.video_id,
                    "video_type": values.video_type
                },
                callback: function (r) {
                    if(r.message != undefined) {
                        $.each(r.message, function (i, j) {
                            html += `
                                <tr id="tr-${j.name}">
                                    <td>${j.youtube_video_id}</td>
                                    <td>${j.video_type}</td>
                                    <td style="width:20%">
                                        <button class="btn btn-xs btn-success editbtn"  data-fieldtype="Button" 
                                            onclick=EditAttributeOptionVideo("${j.name},${j.option_id}")>Edit
                                        </button>
                                        <a class="btn btn-xs btn-danger" style="margin-left:10px;" 
                                                onclick=DeleteAttributeOptionVideo("${j.name}")>Delete
                                        </a>
                                    </td>
                                </tr>
                            `;
                        });
                    } 
                    else {
                        html += '<tr><td colspan="6" align="center">No Records Found.</td></tr>';
                    }
                    html += '</tbody>';
                    html += '</table>';
                    dialog.fields_dict.attribute_video.$wrapper.html(html);
                    video_dialog.hide();
                }
            })
        })
    }

}

function saveattributeoption(product, attribute, option, display_order, price_adjustment,
                            weight_adjustment, image, pre_selected, attribute_color, product_title, 
                            parent_option, disable, available_datetime) {
    if ($("#hdnAttributeOptionid").val() != "") {
        if(attribute) {
            attribute = attribute
        }
        else{
            attribute = $("#hdnSelectedDoc").val();
        }
        let objectIndex = cur_frm.doc.product_attributes.findIndex((obj => obj.product_attribute == attribute));
        var varient_options  = cur_frm.doc.attribute_options.filter( x =>  x.attribute == cur_frm.doc.product_attributes[objectIndex].product_attribute 
                                                                    && x.attribute_id == cur_frm.doc.product_attributes[objectIndex].name);
        if (!variant_option){
             variant_option = []
           }
        let optindex = cur_frm.doc.attribute_options.findIndex((obj => obj.option_value == option && 
                                                obj.attribute == cur_frm.doc.product_attributes[objectIndex].product_attribute && 
                                                obj.attribute_id == cur_frm.doc.product_attributes[objectIndex].name));
       if(optindex >= 0){
            cur_frm.doc.attribute_options[optindex].is_pre_selected = pre_selected
            cur_frm.doc.attribute_options[optindex].display_order = display_order
            cur_frm.doc.attribute_options[optindex].product_title = product_title
            cur_frm.doc.attribute_options[optindex].disable = disable
            cur_frm.doc.attribute_options[optindex].image = image
            cur_frm.doc.attribute_options[optindex].price_adjustment = price_adjustment
            cur_frm.doc.attribute_options[optindex].weight_adjustment = weight_adjustment
            cur_frm.doc.attribute_options[optindex].attribute_color = attribute_color
            if (disable == 1){
                cur_frm.doc.attribute_options[optindex].available_datetime = available_datetime
            }
        }
        else{
            let child = frappe.model.add_child(cur_frm.doc, "Product Attribute Option", "attribute_options");
            child.attribute_id = $("#hdnSelectedId").val()
            child.display_order = display_order
            child.is_pre_selected = pre_selected
            child.price_adjustment = price_adjustment
            child.option_value = option
            child.attribute =attribute
            child.weight_adjustment = weight_adjustment
            child.attribute_color = attribute_color
            child.product_title = product_title
            child.image = image
            child.disable = disable
            if (disable == 1){
                child.available_datetime = available_datetime
            }
        }
        cur_frm.refresh_field("attribute_options");
        $("input[data-fieldname='option_value']").val('');
        $("input[data-fieldname='display_order_no']").val('');
        $("input[data-fieldname='price_adjustment']").val('');
        $("input[data-fieldname='weight_adjustment']").val('');
        $("input[data-fieldname='attribute_color']").val('');
        $("input[data-fieldname='attribute_color']").attr('style', '');
        $("input[data-fieldname='product_title']").val('');
        $("input[data-fieldname='available_datetime']").val('');
        $("input[data-fieldname='disable']").removeAttr('checked');
        $("div[data-fieldname='image']").find('.missing-image').show();
        $("div[data-fieldname='image']").find('.img-container').hide();
        $("div[data-fieldname='image']").find('.attached-file').hide();
        $('div[data-fieldname="image"]').find('.attached-file-link').text('')
        $('div[data-fieldname="image"]').find('.img-container').find('img').attr('src', '')
        $("#hdnAttributeOptionid").val('');
        $('select[data-fieldname="parent_option"]').val('');
        var field1 = cur_dialog.get_field("sec1")
        field1.df.hidden = 1;
        field1.refresh();
        var field2 = cur_dialog.get_field("sec01")
        field2.df.hidden = 1;
        field2.refresh();
        var field3 = cur_dialog.get_field("sec02")
        if(field3){
            field3.df.hidden = 1;
            field3.refresh();
        }
        var field4 = cur_dialog.get_field("sec000")
        field4.df.hidden = 1;
        field4.refresh();
        var html = '';
        var varient_options  = cur_frm.doc.attribute_options.filter( x =>  x.attribute == cur_frm.doc.product_attributes[objectIndex].product_attribute &&
                                                                        x.attribute_id == cur_frm.doc.product_attributes[objectIndex].name);
        if (varient_options) {
            $.each(varient_options, function (i, d) {
                html += `
                    <tr id="tr-${d.name} data-image="${d.image}">
                        <td>${d.option_value}</td>
                        <td>${d.display_order}</td>
                        <td id = "pre_selected" data-preselection= "${d.is_pre_selected}">
                            ${d.is_pre_selected}
                        </td>
                        <td id="disable">${d.disable}</td>
                        <td style="width:20%">
                            <button class="btn btn-xs btn-success editbtn"  data-fieldtype="Button" 
                                onclick=EditAttributeOptions("${d.name}")>Edit
                            </button>
                            <a class="btn btn-xs btn-danger" 
                                style="margin-left:10px;" onclick=DeleteAttributeOption("${d.name}")>Delete
                            </a>
                        </td>
                    </tr> `;
            });
        }
        $("#OptionsData tbody").html(html);
        let wrapper = cur_frm.fields_dict["product_attribute_html"].$wrapper;
        let table = wrapper.find("table#attributeWithOptions")
        if(cur_frm.doc.product_attributes){
            var optionhtml = ""
            let index = cur_frm.doc.product_attributes.findIndex((obj => obj.product_attribute == attribute));
            var variant_option  = cur_frm.doc.attribute_options.filter( x =>  x.attribute == cur_frm.doc.product_attributes[index].product_attribute && 
                                                                        x.attribute_id == cur_frm.doc.product_attributes[index].name);
            if (!variant_option){
                variant_option = []
            }
            var btn_cls = 'btn-default';
            if(pre_selected == 1){
                btn_cls = 'btn-info';
            }
            var comb_index = display_order
            var idx = 1
            optionhtml += `
                <div class="btn-group tb-selected-value" id="multi_input_updatevalue" style="display: inline-block;
                        margin-right: 5px;margin-bottom: 5px;" data-value="${option}" data-name="${name}" data-index="${index}">
                    <a class="btn ${btn_cls} btn-xs btn-link-to-form" data-parentidx="${idx}" data-id="${option}"
                        data-attribute='${cur_frm.doc.product_attributes[index]["product_attribute"]}' data-index="${index}" 
                        data-display_order="${comb_index}" data-option_name="${name}" data-is_pre_selected="${pre_selected}" 
                        data-product_title="${product_title}" data-disable="${disable}" data-parent-control-type="${cur_frm.doc.product_attributes[index]["control_type"]}" 
                        data-attribute_color="
                `
            if(attribute_color){
                optionhtml += attribute_color
            }
            optionhtml +=`
                " onclick="pick_color($(this))" ondblclick="update_attroption($(this))">
                    <img src="/assets/go1_commerce/images/section-icon.svg" 
                        style="height:10px;cursor: all-scroll;position: relative;">${option}</a>
                    <a class="btn ${btn_cls} btn-xs btn-remove" data-id="${option}' data-index="${idx}" 
                        onclick="remove_attroption($(this))"><i class="fa fa-remove text-muted"></i> 
                    </a></div>
                `
            table.find('tbody').find('tr[data-id="'+index+1+'"]').find("#optiontag").
                                        find("#table-multiselect").append(optionhtml)
        }
        cur_frm.dirty();
        cur_frm.save()
    } 
    else {
        if (attribute) {
            attribute = attribute
        } 
        else {
            attribute = $("#hdnSelectedDoc").val();
        }
        let objectIndex = cur_frm.doc.product_attributes.findIndex((obj => obj.product_attribute == attribute));
        var variant_option  = cur_frm.doc.attribute_options.filter( x =>  x.attribute == cur_frm.doc.product_attributes[objectIndex].product_attribute && 
                                                                    x.attribute_id == cur_frm.doc.product_attributes[objectIndex].name);
         
        let optindex = cur_frm.doc.attribute_options.findIndex((obj => obj.option_value == option && x.attribute == cur_frm.doc.product_attributes[objectIndex].product_attribute 
                                                                && x.attribute_id == cur_frm.doc.product_attributes[objectIndex].name));
        if(optindex >= 0){
                cur_frm.doc.attribute_options[optindex].is_pre_selected = pre_selected
                cur_frm.doc.attribute_options[optindex].display_order = display_order
                cur_frm.doc.attribute_options[optindex].product_title = product_title
                cur_frm.doc.attribute_options[optindex].disable = disable
                cur_frm.doc.attribute_options[optindex].image = image
                cur_frm.doc.attribute_options[optindex].price_adjustment = price_adjustment
                cur_frm.doc.attribute_options[optindex].weight_adjustment = weight_adjustment
                cur_frm.doc.attribute_options[optindex].attribute_color = attribute_color
                if (disable == 1){
                    cur_frm.doc.attribute_options[optindex].available_datetime = available_datetime
                }
            }
        else{
            let child = frappe.model.add_child(cur_frm.doc, "Product Attribute Option", "attribute_options");
            child.attribute_id = $("#hdnSelectedId").val()
            child.display_order = display_order
            child.is_pre_selected = pre_selected
            child.price_adjustment = price_adjustment
            child.option_value = option
            child.attribute =attribute
            child.weight_adjustment = weight_adjustment
            child.attribute_color = attribute_color
            child.product_title = product_title
            child.image = image
            child.disable = disable
            if (disable == 1){
                child.available_datetime = available_datetime
            }
        }
        cur_frm.refresh_field("attribute_options");
        $("input[data-fieldname='option_value']").val('');
        $("input[data-fieldname='display_order_no']").val('');
        $("input[data-fieldname='price_adjustment']").val('');
        $("input[data-fieldname='weight_adjustment']").val('');
        $("input[data-fieldname='attribute_color']").val('');
        $("input[data-fieldname='attribute_color']").attr('style', '');
        $("input[data-fieldname='product_title']").val('');
        $("input[data-fieldname='available_datetime']").val('');
        $("input[data-fieldname='disable']").removeAttr('checked');
        $("div[data-fieldname='image']").find('.missing-image').show();
        $("div[data-fieldname='image']").find('.img-container').hide();
        $("div[data-fieldname='image']").find('.attached-file').hide();
        $('div[data-fieldname="image"]').find('.attached-file-link').text('')
        $('div[data-fieldname="image"]').find('.img-container').find('img').attr('src', '')
        $("#hdnAttributeOptionid").val('');
        $('select[data-fieldname="parent_option"]').val('');
        var html = '';
        var variant_option  = cur_frm.doc.attribute_options.filter( x =>  x.attribute == cur_frm.doc.product_attributes[objectIndex].product_attribute && x.attribute_id == cur_frm.doc.product_attributes[objectIndex].name);
        if (variant_option) {
            $.each(variant_option, function (i, d) {
                html += '<tr id="tr-' + d.name + '" data-image="' + d.image + '"><td>' + d.option_value + '</td> ';
                html += ' <td>' + d.display_order + '</td> ';
                html += ' <td id = "pre_selected" data-preselection= "' + d.is_pre_selected + '">' + d.is_pre_selected + '</td> ';
                html += ' <td id="disable">' + d.disable + '</td> ';
                html += ' <td style="width:20%"><button class="btn btn-xs btn-success editbtn"  data-fieldtype="Button" onclick=EditAttributeOptions("' + d.name + '")>Edit</button><a class="btn btn-xs btn-danger" style="margin-left:10px;" onclick=DeleteAttributeOption("' + d.name + '")>Delete</a></td></tr>';
            });
        }
        $("#OptionsData tbody").html(html);
        cur_frm.dirty();
        cur_frm.save()
    }
}

function mySort(a, b){
    var x = a.idx;
    var y = b.idx;
    return ((x < y) ? -1 : ((x > y) ? 1 : 0));
}

function warranty_dialog (frm) {
    frm.possible_val = [{
        "cls": "custom-warranty",
        "hasimage":0,
        "imagefield":"",
        "imagetitlefield":"",
        "tab_html_field": "warranty_html",
        "tab_field": "warranty_json",
        "link_name": "name",
        "link_field": "",
        "title": "Search warranty here...",
        "label": "Pick Warranty",
        "doctype": "Product",
        "reference_doc": "Product Warranty",
        "reference_fields": escape(JSON.stringify(["name", "title", "description"])),
        "filters":"",
        "search_fields": "title",
        "reference_method": "go1_commerce.go1_commerce.doctype.product.product.get_returnpolicy_list",
        "is_child": 0,
        "description": "",
        "child_tab_link": "",
        "height": "180px"
    }];
    let categoryDialog;
    var content = []
    categoryDialog = new frappe.ui.Dialog({
        title: __('Pick Warranty Policy'),
        fields: [
        {
            label: "Pick Warranty Policy",
            fieldtype: 'HTML',
            fieldname: 'warranty_html',
            options: ''
        },
        {
            label: "Pick Warranty Policy",
            fieldtype: 'Data',
            fieldname: 'warranty_json',
            options: '',
            read_only: 1,
            hidden: 1
        }
        ],
        primary_action_label: __('Close')
    });
    frm.doc.warranty_name ? content.push(frm.doc.warranty_name):''
    categoryDialog.get_field('warranty_json').set_value(JSON.stringify(content))
    categoryDialog.get_field('warranty_json').refresh();
    categoryDialog.show();
    setTimeout(function () {
        multiselect_items_warranty(frm, frm.possible_val);
    }, 1000)
    categoryDialog.$wrapper.find('.modal-dialog').css("min-width", "1000px");
    categoryDialog.$wrapper.find('.modal-content').css("min-height", "575px");
}

function replacement_dialog (frm) {
    frm.possible_val = [{
        "cls": "custom-warranty",
        "hasimage":0,
        "imagefield":"",
        "imagetitlefield":"",
        "tab_html_field": "replacement_html",
        "tab_field": "replacement_json",
        "link_name": "name",
        "link_field": "",
        "title": "Search Replacement here...",
        "label": "Pick Replacement",
        "doctype": "Product",
        "reference_doc": "Replacement Policy",
        "reference_fields": escape(JSON.stringify(["name", "heading", "description"])),
        "filters":"",
        "search_fields": "heading",
        "reference_method": "go1_commerce.go1_commerce.doctype.product.product.get_returnpolicy_list",
        "is_child": 0,
        "description": "",
        "child_tab_link": "",
        "height": "180px"
    }];
    let categoryDialog;
    var content = []
    categoryDialog = new frappe.ui.Dialog({
        title: __('Pick Replacement Policy'),
        fields: [
        {
            label: "Pick Replacement Policy",
            fieldtype: 'HTML',
            fieldname: 'replacement_html',
            options: ''
        },
        {
            label: "Pick Replacement Policy",
            fieldtype: 'Data',
            fieldname: 'replacement_json',
            options: '',
            read_only: 1,
            hidden: 1
        }
        ],
        primary_action_label: __('Close')
    });
    frm.doc.warranty_name ? content.push(frm.doc.warranty_name):''
    categoryDialog.get_field('replacement_json').set_value(JSON.stringify(content))
    categoryDialog.get_field('replacement_json').refresh();
    categoryDialog.show();
    setTimeout(function () {
        multiselect_items_replacement(frm, frm.possible_val);
    }, 1000)
    categoryDialog.$wrapper.find('.modal-dialog').css("min-width", "1000px");
    categoryDialog.$wrapper.find('.modal-content').css("min-height", "575px");
}

function multiselect_items_replacement(frm, possible_val) {
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
                                onkeyup="selected_return_values($(this))" placeholder="Search replacement policy here..."
                                title="${c.heading}" style="background-position: 10px 12px;background-repeat: no-repeat;width: 100%;
                                font-size: 16px;padding: 10px 15px 10px 10px;border: 1px solid #d1d8dd;border-radius: 4px !important;
                                margin: 0px;margin-bottom: 10px; data-class="${c.cls}" data-field="${c.tab_field}" data-doctype="${c.doctype}"
                                data-child="${c.is_child}" data-linkfield="${c.link_name}" data-reference_doc="${c.reference_doc}" 
                                data-reference_fields="${c.reference_fields}" data-search_fields="${c.search_fields}" 
                                data-reference_method="${c.reference_method}" data-child_link="${c.child_tab_link}" 
                                data-tab_html_field="${c.tab_html_field}">
                            <table style="width: 100%;">
                                <tr>
                                    <td style="width: 28%;">
                                        <h4 style="padding: 10px 10px;border: 0px solid #ddd;border-bottom: none;
                                            background: #f8f8f8;margin:0px;font-size: 15px !important;">
                                            Title
                                        </h4>
                                    </td>
                                    <td style="">
                                        <h4 style="padding: 10px 10px;border: 0px solid #ddd;
                                            border-bottom: none;background: #f8f8f8;margin:0px;font-size: 15px !important;">
                                            Description
                                        </h4>
                                    </td>
                                </tr>
                            </table>
                            <ul role="listbox" id="assets" class= "assets" style="padding: 0;list-style-type: none;
                                position: relative;margin: 0;background: rgb(255, 255, 255);min-height:350px;height:350px;
                                box-shadow:none;">
                    `
                var k = 0
                var morebtn = ""
                $.each(list_name, function (i, v) {
                    if (v[c.link_name]) {
                        k += 1
                        let arr = cur_frm.doc.replacement_name;
                        if (v[c.link_name] == arr) {
                            var desc = v["description"]; 
                            if(desc == null){
                                desc = "";
                            }
                            drp_html += `
                                <li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;border-radius:0;">
                                    <a style="display: none;">
                                        <strong>${v[c.link_name]}</strong>
                                    </a>
                                    <label class="switch" style="float:right; width: 60px; margin:0px; cursor:pointer;">
                                        <button class="btn btn-xs btn-danger" name="vehicle1" value="0" id="${v[c.link_name]}"
                                            data-doctype="${c.doctype}" data-child="${c.is_child}" data-reference_doc="${c.reference_doc}" 
                                            data-reference_fields="${c.reference_fields}" data-search_fields="${c.search_fields}" 
                                            data-child_link="${c.child_tab_link}" data-tab_html_field="${c.tab_html_field}" 
                                            btn-action="Remove" onclick="selected_replacement($(this))">Remove
                                        </button>
                                    </label>
                                    <table style="width: 90%;">
                                        <tr>
                                            <td style="width: 9%;">
                                                ${v["heading"]}
                                            </td>
                                            <td style="width: 20%;padding-left: 10px;">
                                                ${desc}
                                            </td>
                                        </tr>
                                    </table>
                                </li>`
                        } 
                        else {
                            var desc = v["description"];
                            if(desc == null){
                                desc = "";
                            }
                            drp_html += `
                                <li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;border-radius:0;">
                                    <a style="display: none;">
                                        <strong>${v[c.link_name]}</strong>
                                    </a>
                                    <label class="switch" style="float:right;width: 60px; margin:0px; cursor:pointer;">
                                        <button class="btn btn-xs btn-success" name="vehicle1" value="0" id="${v[c.link_name]}"
                                            data-doctype="${c.doctype}" data-child="${c.is_child}" data-reference_doc="${c.reference_doc}" 
                                            data-reference_fields="${c.reference_fields}" data-search_fields="${c.search_fields}" 
                                            data-child_link="${c.child_tab_link }" data-tab_html_field="${c.tab_html_field}" 
                                            btn-action="add" onclick="selected_replacement($(this))">Select
                                        </button>
                                    </label>
                                    <table style="width: 90%;">
                                        <tr>
                                            <td style="width: 9%;">
                                                ${v["heading"]}
                                            </td>
                                            <td style="width: 20%;padding-left: 10px;">
                                                ${desc}
                                            </td>
                                        </tr>
                                    </table>
                                </li>
                            `;  
                        }
                    } 
                    else {
                        drp_html += '<li></li>';
                    }
                })
                drp_html += morebtn
                drp_html += '</ul></div></div>';
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
}

function multiselect_items_warranty(frm, possible_val) {
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
                                onkeyup="selected_return_values($(this))" placeholder="${c.title}" 
                                title="${c.title}" style="background-position: 10px 12px;background-repeat: no-repeat;width: 100%;
                                font-size: 16px;padding: 10px 15px 10px 10px;border: 1px solid #d1d8dd;border-radius: 4px !important;
                                margin: 0px;margin-bottom: 10px;"
                                data-class="${c.cls}" data-field="${c.tab_field}" data-doctype="${c.doctype}" data-child="${c.is_child}" 
                                data-linkfield="${c.link_name}" data-reference_doc="${c.reference_doc}" data-reference_fields="${c.reference_fields}" 
                                data-search_fields="${c.search_fields}" data-reference_method="${c.reference_method}" data-child_link="${c.child_tab_link}"
                                data-tab_html_field="${c.tab_html_field}">
                            <table style="width: 100%;">
                                <tr>
                                    <td style="width: 33%;">
                                        <h4 style="padding: 10px 10px;border: 0px solid #ddd;border-bottom: none;
                                                background: #f8f8f8;margin:0px;font-size: 16px !important;">
                                            Title
                                        </h4>
                                    </td>
                                    <td style="">
                                        <h4 style="padding: 10px 10px;border: 0px solid #ddd;border-bottom: none;
                                            background: #f8f8f8;margin:0px;font-size: 16px !important;">
                                            Description
                                        </h4>
                                    </td>
                                </tr>
                            </table>
                            <ul role="listbox" id="assets" class= "assets" style="padding: 0;list-style-type: none;position: relative;
                                margin: 0;background: rgb(255, 255, 255);min-height:350px;height:350px;box-shadow:none;">
                    ` 
                var k = 0
                var morebtn = ""
                $.each(list_name, function (i, v) {  
                    if (v[c.link_name]) {
                        k += 1
                        let arr =cur_frm.doc.warranty_name;
                        if (v[c.link_name] == arr) {
                            drp_html += `
                                <li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;border-radius:0;">
                                    <a style="display: none;">
                                        <strong>${v[c.link_name]}</strong>
                                    </a>
                                    <label class="switch" style="float:right; width: 60px; margin:0px; cursor:pointer;">
                                        <button class="btn btn-xs btn-danger" name="vehicle1" value="0" id="${v[c.link_name]}"
                                            data-doctype="${c.doctype}" data-child="${c.is_child}" data-reference_doc="${c.reference_doc}" 
                                            data-reference_fields="${c.reference_fields}" data-search_fields="${c.search_fields}" 
                                            data-child_link="${c.child_tab_link}" data-tab_html_field="${c.tab_html_field}" 
                                            btn-action="Remove" onclick="selected_warranty($(this))">Remove
                                        </button>
                                    </label>
                                    <table style="width: 90%;">
                                        <tr>
                                            <td style="font-size:14px;width: 9%;">
                                                ${v["title"]}
                                            </td>
                                            <td style="font-size:14px;width: 20%;padding-left: 10px;">
                                                ${v["description"]}
                                            </td>
                                        </tr>
                                    </table>
                                </li>
                            ` 
                        } 
                        else{
                            drp_html += `
                                <li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;">
                                    <a style="display: none;">
                                        <strong>${v[c.link_name]}</strong>
                                    </a>
                                    <label class="switch" style="float:right;width: 60px; margin:0px; cursor:pointer;">
                                        <button class="btn btn-xs btn-success" name="vehicle1" value="0" id="${v[c.link_name]}"
                                            data-doctype="${c.doctype}" data-child="${c.is_child}" data-reference_doc="${c.reference_doc}" 
                                            data-reference_fields="${c.reference_fields}" data-search_fields="${c.search_fields}" 
                                            data-child_link="${c.child_tab_link}" data-tab_html_field="${c.tab_html_field}" 
                                            btn-action="add" onclick="selected_warranty($(this))">Select
                                        </button>
                                    </label>
                                    <table style="width: 90%;">
                                        <tr>
                                            <td style="font-size:14px;width: 9%;">
                                                ${v["title"]}
                                            </td>
                                            <td style="font-size:14px;width: 20%;padding-left: 10px;">
                                                ${v["description"]}
                                            </td>
                                        </tr>
                                    </table>
                                    </li>
                            `;
                           
                        }
                       
                    } else {
                        drp_html += '<li></li>';
                    }
                })
                drp_html += morebtn
                drp_html += '</ul></div></div>';
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
}

function returnpolicy_dialog(frm) {
    frm.possible_val = [{
        "cls": "custom-return-policy",
        "hasimage":0,
        "imagefield":"",
        "imagetitlefield":"",
        "tab_html_field": "returnpolicy_html",
        "tab_field": "returnpolicy_json",
        "link_name": "name",
        "link_field": "",
        "title": "Search return policy here...",
        "label": "Pick Return Policy",
        "doctype": "Product",
        "reference_doc": "Return Policy",
        "reference_fields": escape(JSON.stringify(["name", "heading", "description"])),
        "filters":"",
        "search_fields": "category_name",
        "reference_method": "go1_commerce.go1_commerce.doctype.product.product.get_returnpolicy_list",
        "is_child": 0,
        "description": "",
        "child_tab_link": "",
        "height": "180px"
    }];
    let categoryDialog;
    categoryDialog = new frappe.ui.Dialog({
        title: __('Pick Return Policy'),
        fields: [
        {
            label: "Pick Return Policy",
            fieldtype: 'HTML',
            fieldname: 'returnpolicy_html',
            options: ''
        },
        {
            label: "Pick Return Policy",
            fieldtype: 'Data',
            fieldname: 'returnpolicy_json',
            options: '',
            read_only: 1,
            hidden: 1
        }
        ],
        primary_action_label: __('Close')
    });
    categoryDialog.get_field('returnpolicy_json').set_value(frm.doc.returnpolicy_json)
    categoryDialog.get_field('returnpolicy_json').refresh();
    categoryDialog.show();
    setTimeout(function () {
        frm.events.multiselect_items(frm, frm.possible_val);
    }, 1000)
    categoryDialog.set_primary_action(__('New Return Policy'), function () {
        quick_entry_return(frm)
    })
    categoryDialog.$wrapper.find('.modal-dialog').css("min-width", "1000px");
    categoryDialog.$wrapper.find('.modal-content').css("min-height", "575px");
}

function specification_dialog(frm) {
    frm.possible_val = [{
        "cls": "custom-specification-attribute",
        "hasimage":0,
        "imagefield":"",
        "imagetitlefield":"",
        "tab_html_field": "specification_html",
        "tab_field": "specification_json",
        "link_name": "name",
        "link_field": "product_specification_attributes",
        "title": "Search specification attribute here...",
        "label": "Pick Specification Attribute",
        "doctype": "Product",
        "reference_doc": "Specification Attribute",
        "reference_fields": escape(JSON.stringify(["name", "attribute_name"])),
        "filters":"",
        "search_fields": "attribute_name",
        "reference_method": "go1_commerce.go1_commerce.doctype.product.product.get_specification_list",
        "is_child": 0,
        "description": "",
        "child_tab_link": "",
        "height": "180px"
    }];
    let categoryDialog;
    var content = []
    categoryDialog = new frappe.ui.Dialog({
        title: __('Pick Specification Attribute'),
        fields: [
        {
            label: "New Specification Attribute",
            fieldtype: 'Button',
            fieldname: 'newspecification_btn',
            options: ''
        },
        {
            label: "Pick Specification Attribute",
            fieldtype: 'HTML',
            fieldname: 'specification_html',
            options: ''
        },
        {
            label: "Pick Specification Attribute",
            fieldtype: 'Code',
            fieldname: 'specification_json',
            options: '',
            read_only: 1,
            hidden: 1
        }
        ],
    });
    $.each(cur_frm.doc.product_specification_attributes, function (i, s) {
        content.push(s.attribute)
    })
    categoryDialog.fields_dict.newspecification_btn.$wrapper.attr("style", "margin-bottom:0px !important;");
    categoryDialog.fields_dict.newspecification_btn.$wrapper.find('button').attr("style", "float: left;margin-top: -75px;margin-left: 225px;padding: 4px 10px;font-size: 13px;");
    categoryDialog.fields_dict.newspecification_btn.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
    categoryDialog.get_field('specification_json').set_value(JSON.stringify(content));
    categoryDialog.get_field('specification_json').refresh();
    categoryDialog.show();
    setTimeout(function () {
        frm.events.build_multi_selector(frm, frm.possible_val);
    }, 1000)
    categoryDialog.fields_dict.newspecification_btn.input.onclick = function () {
        quick_entry_attribute(frm)
     };
   categoryDialog.set_primary_action(__('Submit'), function () {
        var cat = categoryDialog.get_values();
        var cat_json = JSON.parse(cat.specification_json)
        cur_frm.doc.product_specification_attributes = [];
        $(cat_json).each(function (k, v) {
            let row = frappe.model.add_child(frm.doc, "Product Specification Attribute Mapping", "product_specification_attributes");
            row.attribute = v;
            frappe.model.get_value('Specification Attribute', {'name': v}, "attribute_name",function(e) {
                row.specification_attribute = e.attribute_name
                refresh_field("product_specification_attributes");
             })
        })
        if (cat_json.length <= 0) {
            frappe.throw(__('Please select any one Specification Attribute.'))
        } 
        else {
            refresh_field("selected_category_list");
            refresh_field("product_specification_attributes");
            frm.refresh_field('product_specification_attributes')
            $('div[data-fieldname="product_categories"] .grid-footer').addClass('hidden')
            categoryDialog.hide();
            $('[class="btn btn-xs btn-secondary grid-add-row"]').hide()
        }
    })
    categoryDialog.$wrapper.find('.modal-dialog').css("min-width", "1000px");
    categoryDialog.$wrapper.find('.modal-content').css("min-height", "575px");
}

function imgDialog_setup(imgDialog){
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
}

var addEvent = (function () {
    if (document.addEventListener) {
        return function (el, type, fn) {
            if (el && el.nodeName || el === window) {
                el.addEventListener(type, fn, false);
            } 
            else if (el && el.length) {
                for (var i = 0; i < el.length; i++) {
                    addEvent(el[i], type, fn);
                }
            }
        };
    } 
    else {
        return function (el, type, fn) {
            if (el && el.nodeName || el === window) {
                el.attachEvent('on' + type, function () {
                    return fn.call(el, window.event);
                });
            } 
            else if (el && el.length) {
                for (var i = 0; i < el.length; i++) {
                    addEvent(el[i], type, fn);
                }
            }
        };
    }
})();

var dragItems;
updateDataTransfer();
var dropAreas = document.querySelectorAll('[droppable=true]');
function cancel(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    return false;
}

function updateDataTransfer() {
    dragItems = document.querySelectorAll('[draggable=true]');
    for (var i = 0; i < dragItems.length; i++) {
        addEvent(dragItems[i], 'dragstart', function (event) {
            event.dataTransfer.setData('obj_id', this.id);
            return false;
        });
    }
}

addEvent(dropAreas, 'dragover', function (event) {
    if (event.preventDefault) event.preventDefault();
    this.style.borderColor = "#000";
    return false;
});

addEvent(dropAreas, 'dragleave', function (event) {
    if (event.preventDefault) event.preventDefault();
    this.style.borderColor = "#ccc";
    return false;
});

addEvent(dropAreas, 'dragenter', cancel);
addEvent(dropAreas, 'drop', function (event) {
    if (event.preventDefault) event.preventDefault();
    var iObj = event.dataTransfer.getData('obj_id');
    var oldObj = document.getElementById(iObj);
    var oldSrc = oldObj.childNodes[0].src;
    oldObj.className += 'hidden';
    var oldThis = this;
    setTimeout(function () {
        oldObj.parentNode.removeChild(oldObj);
        oldThis.innerHTML += '<a id="' + iObj + '" draggable="true"><img src="' + oldSrc + '" /></a>';
        updateDataTransfer();
        oldThis.style.borderColor = "#ccc";
    }, 500);
    return false;
});


