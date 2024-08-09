frappe.provide('core.bulk_edit');
frappe.pages['products-bulk-update'].on_page_load = function(wrapper) {
    core.bulk_edit = new BulkEdit(wrapper);
    $(document).on('uppyUploadComplete', function(){
        core.bulk_edit.get_data();
    })
}

class BulkEdit {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.category;
        this.brand;
        this.item_name;
        this.is_active;
        this.is_featured;
        this.restaurant = false;
        this.page_limit = 20;
        this.doc_count = 0;
        this.setup_page();
    }

    setup_page() {
        this.page = frappe.ui.make_app_page({
            parent: this.wrapper,
            title: 'Product Bulk Update',
            single_column: true
        });
        this.page.set_secondary_action(__("Refresh"), () => {
            this.refresh();
        });
        this.setup_filters();
        this.page.main.append(frappe.render_template("products_bulk_update"));
        this.$table_area = this.page.main.find('#listing');
        this.setup_pagination();
    }

    setup_filters() {
        this.page.add_field({
            fieldname: 'item_name', label: __('Product Name'), fieldtype: 'Data',
            onchange: ()=> {
                this.item_name = this.page.fields_dict.item_name.value;
                this.get_data();
            }
        });
        this.page.add_field({
            fieldname: 'category', label: __('Category'), fieldtype: 'Link', options: 'Product Category',
            onchange: ()=> {
                this.category = this.page.fields_dict.category.value;
                this.get_data();
            }
        });
        if (!this.restaurant) {
            this.page.add_field({
                fieldname: 'brand', label: __('Brand'), fieldtype: 'Link', options: 'Product Brand',
                onchange: ()=> {
                    this.brand = this.page.fields_dict.brand.value;
                    this.get_data();
                }
            });
        }
        this.page.add_field({
            fieldname: 'is_active', label: __('Is Active'), fieldtype: 'Select', options: ['Yes', 'No'],
            onchange: () => {
                this.is_active = this.page.fields_dict.is_active.value;
                this.get_data();
            }

        });
        if (!this.restaurant) {
            this.page.add_field({
                fieldname: 'featured', label: __('Is Featured'), fieldtype: 'Select', options: ['Yes', 'No'],
                onchange: ()=> {
                    this.is_featured = this.page.fields_dict.is_featured.value;
                    this.get_data();
                }
            });
        }
    }

    setup_pagination() {
        let me = this;
        this.$pagination = this.page.main.find('.list-paging-area');
        this.$pagination.find('.btn-paging').click(function() {
            me.page_limit = $(this).attr('data-value');
            me.doc_count = 0;
            me.$pagination.find('.btn-info').removeClass('btn-info');
            $(this).addClass('btn-info');
            me.get_data();
        });
        this.$pagination.find('.btn-more').click(function() {
            me.doc_count = me.doc_count + me.page_limit;
            me.get_data();
        })
    }

    refresh() {
        this.table_data = [];
        this.get_data();
    }

    get_data() {
        if(this.datatable)
            this.datatable.freeze();
        let me = this;
        frappe.call({
            method: 'go1_commerce.go1_commerce.page.products_bulk_update.products_bulk_update.get_all_products_with_attributes',
            args: {
                category: me.category, brand: me.brand, item_name: me.item_name,
                active: me.is_active, featured: me.is_featured,
                page_start: me.doc_count, page_end: me.page_limit
            },
            callback: function(r) {
                if(me.doc_count == 0){
                    me.table_data = r.message ? r.message : [];
                } else {
                    $.merge(me.table_data, (r.message || []));
                }
                let opts = make_products_table(me.table_data, me.datatable);
                if(me.datatable) {
                    me.datatable.unfreeze();
                    if(r.message && r.message.length > 0)
                        me.datatable.refresh(opts.data, opts.columns);
                    else 
                        me.$pagination.find('.btn-more').hide();
                } else {
                    me.datatable = new DataTable(me.$table_area[0], opts);
                }
            }
        })
    }
}

var changedRows = [];
var dt;

function formatMoney(amount, decimalCount = 2, decimal = ".", thousands = ",") {
    try {
        decimalCount = Math.abs(decimalCount);
        decimalCount = isNaN(decimalCount) ? 2 : decimalCount;

        const negativeSign = amount < 0 ? "-" : "";

        let i = parseInt(amount = Math.abs(Number(amount) || 0).toFixed(decimalCount)).toString();
        let j = (i.length > 3) ? i.length % 3 : 0;

        return negativeSign + (j ? i.substr(0, j) + thousands : '') + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + thousands) + (decimalCount ? decimal + Math.abs(amount - i).toFixed(decimalCount).slice(2) : "");
    } catch (e) {
        console.log(e)
    }
};
frappe.pages['products-bulk-update'].refresh = function(wrapper) {
    core.bulk_edit.refresh();
}

function make_products_table(data) {
    var restaurant = false;
    var items = data;
    let cols = [
        { name: 'Id', id: 'name', doctype: 'doctype', docname: 'docname', width: 700, editable: false },
        { name: 'Product', id: 'item', doctype: 'doctype', docname: 'docname', width: 950, editable: true },
        { name: 'Price', id: 'price', doctype: 'doctype', docname: 'docname', width: 500, editable: true, format: value => formatMoney(value) },
    ];
    if (!restaurant) {
        cols.push({ name: 'SKU', id: 'sku', doctype: 'doctype', docname: 'docname', width: 300, editable: true })
    }
    cols.push({ name: 'Old Price', id: 'old_price', doctype: 'doctype', docname: 'docname', width: 500, editable: true, format: value => { if (value != undefined) { return formatMoney(value) } else { return '' } } });
    if (!restaurant) {
        cols.push({ name: 'Stock', id: 'stock', doctype: 'doctype', docname: 'docname', width: 300, editable: true, align: "left" });
        cols.push({ name: 'Image', id: 'image', doctype: 'doctype', docname: 'docname', width: 1000, align: "center", editable: false });
        cols.push({ name: 'Inventory Method', id: 'inventory_method', doctype: 'doctype', docname: 'docname', width: 600, editable: true, align: "left" });
    }
    cols.push({ name: 'Active', width: 300, id: 'is_active', doctype: 'doctype', docname: 'docname', editable: true, align: "left" })
    if (!restaurant) {
        cols.push({ name: 'Featured Product', id: 'display_home_page', doctype: 'doctype', docname: 'docname', width: 300, editable: true, align: "left" });
        cols.push({ name: 'Categories', id: 'name1', width: 680, align: "center", format: value => { if (value != undefined) { return `<button class="btn-primary" onclick="get_category('${value}')" style="padding: 3px 10px !important;border-radius: 3px !important;background: orange !important;border: 1px solid orange !important;">Edit Category</button>` } else { return '' } } });
        cols.push({ name: 'Image', id: 'name1', width: 750, align: "center", format: value => { if (value != undefined) { return `<button class="btn-primary" onclick="get_image('${value}')" style="padding: 3px 10px !important;border-radius: 3px !important;background: blue !important;border: 1px solid blue !important;">Add / Edit Image</button>` } else { return '' } } });
    }
    let options = {
        columns: cols,
        data: data,
        inlineFilters: false,
        treeView: true,
        layout: 'ratio',
        noDataMessage: "No Data Found",
        getEditor(colIndex, rowIndex, value, parent, column, row, data) {
            let $input;
            if (colIndex == 3 || (!restaurant && colIndex == 5) || colIndex == 6) {
                $input = document.createElement('input');
                $input.type = 'number';
                parent.appendChild($input);
            }
            if (colIndex == 2 || colIndex == 4) {
                $input = document.createElement('input');
                $input.type = 'text';
                parent.appendChild($input);
            }
            if (colIndex == 8) {
                $input = document.createElement('select');
                $(['Track Inventory', 'Dont Track Inventory', 'Track Inventory By Product Attributes']).each((k, v) => {
                    let opts = new Option(v, v);
                    if(value == v)
                        opts.setAttribute('selected', 'selected');
                    $input.append(opts);
                });
                
                var drpClass = "InventoryDrp-";
                var changeName = 'InventoryDropUpdate';
                $input.setAttribute("id", drpClass + rowIndex);
                $input.setAttribute("style", 'width:100%;height:26px');
                $input.setAttribute("onchange", changeName + '(' + rowIndex + ')');
                parent.appendChild($input);
            }
            if (colIndex == 9 || colIndex == 10 || (restaurant && colIndex == 5)) {
                $input = document.createElement('select');
                $(['Yes', 'No']).each((k, v) => {
                    let opts = new Option(v, v);
                    if(value == v)
                        opts.setAttribute('selected', 'selected');
                    $input.append(opts);
                });
                var drpClass = "ActiveDrp-";
                var changeName = 'ActiveDropUpdate';
                if (colIndex == 9) {
                    drpClass = "RecomDrp-";
                    changeName = 'RecomDropUpdate';
                }
                $input.setAttribute("id", drpClass + rowIndex);
                $input.setAttribute("style", 'width:100%;height:26px');
                $input.setAttribute("onchange", changeName + '(' + rowIndex + ')');
                parent.appendChild($input);
            }

            return {
                initValue(value) {
                    $input.focus();
                    $input.value = value;
                },
                setValue(value) {
                    let cell = core.bulk_edit.datatable.datamanager.getCell(colIndex, rowIndex);
                    let fieldname = core.bulk_edit.datatable.datamanager.getColumn(colIndex);
                    let docname = data.docname;
                    let doctype = data.doctype;
                    let fieldname1 = cell.column.id;
                    let value1 = value;
                    $input.value = value;
                    frappe.call({
                        method: 'go1_commerce.go1_commerce.page.products_bulk_update.products_bulk_update.update_bulk_data',
                        args: {
                            'doctype': doctype,
                            'docname': docname,
                            'fieldname': fieldname1,
                            'value': value1
                        },
                        async: false,
                        callback: function(data) {

                        }
                    })
                },
                getValue() {
                    return $input.value;
                }
            }
        },
        events: {
            onRemoveColumn(column) {},
            onSwitchColumn(column1, column2) {},
            onSortColumn(column) {},
            onCheckRow(row) {}
        },
    }

    return options;
}

function selected_multiselect_lists1(e) {
    var actual_value = $(e).attr('id');
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var child_tab_link = $(e).attr('data-child_link');
    var row_id = $(e).attr('data-name');
    var cls = $(e).parent().parent().parent().parent().parent().attr('class');
    var field = $('.' + cls + ' #myInput').attr('data-field');
    var linkedfield = $('.' + cls + ' #myInput').attr('data-linkfield');
    if ($(e).is(':checked')) {
        afterSelectlist1($(e).parent().parent().find('a').text(), cls, field, linkedfield, doctype_name, row_id, is_child, child_tab_link, actual_value)
    } else {
        afterDeselectlist1(actual_value, cls, field, linkedfield, doctype_name, row_id, is_child, child_tab_link)
        if (cur_dialog.fields_dict["area_html1"].$wrapper.find('input#selectAll')) {
            cur_dialog.fields_dict["area_html1"].$wrapper.find('input#selectAll').prop("checked", false);
        }
    }
    if (parseInt(is_child) == 1) {
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #myInput').attr('data-id', $(e).attr('id'))
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets').css('display', 'none')
    } else {
        $('.' + cls + ' #myInput').attr('data-id', $(e).attr('id'))
    }
}

function showPopup(image) {
    $(".popup").lightGallery({
        pager: true
    });
    $(".popup a[href='" + image + "'] > img").trigger("click");
}

function closePopup() {
    var modal = document.getElementById("myModal");
    modal.style.display = "none";
}

function afterSelectlist1(values, cls, field, linkedfield, doctype_name, row_id, is_child, child_tab_link, actual_value) {
    if (parseInt(is_child) == 1) {
        var cur_row = frappe.get_doc(doctype_name, row_id);
        if (!cur_row[field] || cur_row[field] == undefined || cur_row[field] == "") {
            frappe.model.set_value(doctype_name, row_id, field, '[]');
            var row_val = frappe.model.get_value(doctype_name, row_id, field);
            let arr = JSON.parse(row_val);
            if (actual_value) {
                arr.push(actual_value);
            }
            frappe.model.set_value(doctype_name, row_id, field, JSON.stringify(arr));
            $('.' + cls + ' #myInput').val('');
        } else {
            let arr = JSON.parse(cur_row[field]);
            if (actual_value) {
                arr.push(actual_value);
            }
            frappe.model.set_value(doctype_name, row_id, field, JSON.stringify(arr));
            $('.' + cls + ' #myInput').val('');
        }
    } else {
        var dialog_val = cur_dialog.fields_dict[field].get_value();
        if (!dialog_val || dialog_val == undefined || dialog_val == "") {
            cur_dialog.fields_dict[field].set_value('[]');
            var row_val = cur_dialog.fields_dict[field].get_value();
            let arr = JSON.parse(row_val);
            if (values) {
                arr.push(values);
            }
            cur_dialog.fields_dict[field].set_value(JSON.stringify(arr));
            $('.' + cls + ' #myInput').val('');
        } else {
            let arr = JSON.parse(cur_dialog.fields_dict[field].get_value());
            if (values) {
                arr.push(values);
            }
            cur_dialog.get_field(field).set_value(JSON.stringify(arr));
            cur_dialog.get_field(field).refresh();
            $('.' + cls + ' #myInput').val('');
        }
    }
}


function afterDeselectlist1(values, cls, field, linkedfield, doctype_name, row_id, is_child, child_tab_link) {
    if (parseInt(is_child) == 1) {
        var cur_row = frappe.get_doc(doctype_name, row_id);
        if (!cur_row[field] || cur_row[field] == undefined || cur_row[field] == "") {
            frappe.model.set_value(doctype_name, row_id, field, '[]')
        } else {
            let arr = JSON.parse(cur_row[field]);
            var index = arr.indexOf(values);
            if (index >= -1) {
                arr.splice(index, 1);
            }
            frappe.model.set_value(doctype_name, row_id, field, JSON.stringify(arr))
        }
    } else {
        var dialog_val = cur_dialog.fields_dict[field].get_value();
        if (!dialog_val || dialog_val == undefined || dialog_val == "") {
            cur_dialog.fields_dict[field].set_value('[]')
        } else {
            let arr = JSON.parse(cur_dialog.fields_dict[field].get_value());
            var index = arr.indexOf(values);
            if (index >= -1) {
                arr.splice(index, 1);
            }
            cur_dialog.fields_dict[field].set_value(JSON.stringify(arr));
        }
    }
}

function set_control_value(doctype, docname, fieldname, value) {
    frappe.call({
        method: 'go1_commerce.go1_commerce.doctype.product.product.insert_bulk_data',
        args: {
            'name': docname,
            'value': value
        },
        async: false,
        callback: function(data) {

        }
    })
}

function ActiveDropUpdate(rowIndex) {
    $(".dt-cell--col-8").removeClass("dt-cell--focus dt-cell--editing");
    core.bulk_edit.datatable.cellmanager.submitEditing();
    core.bulk_edit.datatable.cellmanager.deactivateEditing();
}

function RecomDropUpdate(rowIndex) {
    $(".dt-cell--col-9").removeClass("dt-cell--focus dt-cell--editing");
    core.bulk_edit.datatable.cellmanager.submitEditing();
    core.bulk_edit.datatable.cellmanager.deactivateEditing();
}

function InventoryDropUpdate(rowIndex) {
    $(".dt-cell--col-7").removeClass("dt-cell--focus dt-cell--editing");
    core.bulk_edit.datatable.cellmanager.submitEditing();
    core.bulk_edit.datatable.cellmanager.deactivateEditing();
}

function updatemenuitems() {
    var alldata = core.bulk_edit.datatable.datamanager.getRows();
    var datas = [];
    for (var i = 0; i < changedRows.length; i++) {
        var obj = {
            'data': alldata[parseInt(changedRows[i])],
            'rowIndex': parseInt(changedRows[i])
        }
        datas.push(obj);
    }
    for (var i = 0; i < datas.length; i++) {
        var item = datas[i];
        var itemid = item.data[1].content;
        var itemTitle = item.data[2].content;
        var itemSKU = item.data[3].content;
        var itemPrice = item.data[4].content;
        var itemOldPrice = item.data[5].content;
        var itemStock = item.data[6].content;
        var itemInventoryMethod = item.data[7].content;
        var itemActive = item.data[8].content;
        var itemFeaturedProduct = item.data[9].content;
        frappe.call({
            method: 'go1_commerce.go1_commerce.api.update_products',
            args: {
                name: itemid,
                title: itemTitle,
                sku: itemSKU,
                price: itemPrice,
                oldprice: itemOldPrice,
                stock: itemStock,
                inventorymethod: itemInventoryMethod,
                active: itemActive,
                displayhomepage: itemFeaturedProduct,
            },
            callback: function(r) {
                if (i == datas.length) {

                }
            }
        });

    }
    frappe.msgprint("Successfully updated");
    changedRows = [];
}

function get_category(id) {
    frappe.run_serially([
        () => {
            get_all_category_list()
        },
        () => {
            $('.modal').empty();
            $('.modal').removeClass('in');
            frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.product.product.get_product',
                args: {
                    name: id
                },
                async: false,
                callback: function(data) {
                    if (data.message) {
                        data1 = data.message;
                        category_dialog1(data1)
                    }
                }
            })
        }
    ])
}

function get_all_category_list() {
    frappe.call({
        method: 'go1_commerce.go1_commerce.doctype.product.product.get_all_category_list',
        args: {},
        async: false,
        callback: function(data) {
            if (data.message) {
                category_list = data.message;
            }
        }
    })
}

function category_dialog(data1) {
    let categoryDialog;
    let random = Math.random() * 100;

    categoryDialog = new frappe.ui.Dialog({
        title: __('Categories'),
        fields: [{ fieldtype: 'HTML', fieldname: 'category_list', options: '<div id="mainCategoryList"><div id="category_list' + parseInt(random) + '"></div></div>' }],
        primary_action_label: __('Close')
    });
    let selected_category_list = [];
    categoryDialog.set_primary_action(__('Add'), function() {
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.update_product_categories',
            args: {
                category1: selected_category_list,
                name: data1.name
            },
            async: false,
            callback: function(data) {
                categoryDialog.hide();
            }
        })

    });
    var table = new DataTable('#category_list' + parseInt(random), {
        columns: [
            { 'name': 'Category', 'id': 'category_name', 'width': 220, editable: false },
            {
                id: 'category_image',
                width: 150,
                editable: false,
                name: 'Image',
                format: (value) => {
                    if (value)
                        return `<img src="${value}" style="height:30px;" />`
                    else
                        return ''
                }
            },
            { 'name': 'Parent', 'id': 'parent_category_name', 'width': 220, editable: false },
            {
                'name': 'Status',
                'width': 135,
                'id': 'is_active',
                editable: false,
                format: (value) => {
                    if (value == 1)
                        return 'Active'
                    else
                        return 'Inactive'
                }
            },
            { 'name': 'Name', 'width': 134, 'id': 'name', editable: false }

        ],
        data: category_list,
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
                    $(selected_category_list).each(function(k, v) {
                        if (v.category == row[6].content) {} else {
                            arr.push(v)
                        }
                    })
                    selected_category_list = arr;
                } else {
                    selected_category_list.push({ 'category': row[6].content, 'category_name': row[2].content })
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
    $('.modal[data-types="category"').each(function() {
        $(this).remove();
    })
    categoryDialog.show();
    if (data1.product_categories) {
        $('div[data-fieldname="category_list"]').find('.dt-cell__content--col-6').each(function() {
            let category = $(this).text();
            let check_data = data1.product_categories.find(obj => obj.category == category.trim());
            if (check_data) {
                $(this).parent().parent().find('input[type=checkbox]').trigger('click')
            }
        })
    }
    $(categoryDialog.$wrapper).attr('data-types', 'category')
}


function category_dialog1(data1) {
    data1.possible_val = [{
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
    let random = Math.random() * 100;
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
    $.each(data1.product_categories, function(i, s) {
        content.push(s.category)
    })
    categoryDialog.get_field('category_json').set_value(JSON.stringify(content));
    categoryDialog.get_field('category_json').refresh();
    categoryDialog.show();
    setTimeout(function() {
        build_multi_selector(data1, data1.possible_val);
    }, 1000)
    categoryDialog.set_primary_action(__('Add'), function() {
        var cat = categoryDialog.get_values();
        var cat_json = JSON.parse(cat.category_json)
        data1.product_categories = [];
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.update_product_categories1',
            args: {
                category1: cat_json,
                name: data1.name
            },
            async: false,
            callback: function(data) {
                
            }
        })
        if (cat_json.length <= 0) {
            frappe.throw(__('Please select any one category.'))
        } else {
            refresh_field("selected_category_list");
            $('div[data-fieldname="product_categories"] .grid-footer .grid-add-row').addClass('hidden')
            categoryDialog.hide();
        }
    });
    categoryDialog.$wrapper.find('.modal-dialog').css("min-width", "1000px");
    categoryDialog.$wrapper.find('.modal-content').css("min-height", "575px");
}

function get_image(id) {
    localStorage.setItem('randomuppy', ' ');
    frappe.call({
        method: 'go1_commerce.go1_commerce.doctype.product.product.get_product',
        args: {
            name: id
        },
        async: false,
        callback: function(data) {
            if (data.message) {
                data1 = data.message;
                generate_image_html(data1)
                image_dialog(data1)
            }
        }
    })

}

function build_multi_selector(data1, possible_val) {

    $.each(possible_val, function(i, c) {
        var ref_fields = unescape(c.reference_fields)
        var ref_method = c.reference_method
        var cls = c.cls;
        var field = c.tab_field
        var linkedfield = c.link_name
        var url = '/api/method/' + ref_method
        $.ajax({
            type: 'POST',
            Accept: 'application/json',
            ContentType: 'application/json;charset=utf-8',
            url: window.location.origin + url,
            data: {
                "reference_doc": c.reference_doc,
                "reference_fields": ref_fields
            },
            dataType: "json",
            async: false,
            headers: {
                'X-Frappe-CSRF-Token': frappe.csrf_token
            },
            success: function(r) {
                var list_name = r.message.list_name;
                var drp_html = '<div class="' + c.cls + '" style="padding: 0px;"><div class="awesomplete">';
                drp_html += '<input type="text"  class="multi-drp" id="myInput" autocomplete="nope" onfocus="select_list_detail($(this))" onfocusout="disable_select_list($(this))" onkeyup="selected_lists_values($(this))" ';
                drp_html += 'placeholder="' + c.title + '" title="' + c.title + '" style="background-position: 10px 12px;background-repeat: no-repeat;width: 100%;font-size: 16px;padding: 10px 15px 10px 10px;border: 1px solid #d1d8dd;border-radius: 4px !important;;margin: 0px;" ';
                drp_html += 'data-class="' + c.cls + '" data-field="' + c.tab_field + '" data-doctype="' + c.doctype + '" data-child="' + c.is_child + '" data-linkfield="' + c.link_name + '" data-reference_doc="' + c.reference_doc + '" data-reference_fields="' + c.reference_fields + '" data-search_fields="' + c.search_fields + '" data-reference_method="' + c.reference_method + '" data-child_link="' + c.child_tab_link + '">'
                drp_html += '<h4 style="padding: 10px 10px;border: 1px solid #ddd;border-bottom: none;margin: 30px 0px 0px 0px;background: #f8f8f8;">' + c.label + '</h4>'
                drp_html += '<ul role="listbox" id="assets" class= "assets" style="list-style-type: none;position: absolute;width: 43%;margin: 0;background: rgb(255, 255, 255);min-height:350px;height:350px;box-shadow:none;">'
                var k = 0
                $.each(list_name, function(i, v) {
                    if (v[c.link_name]) {

                        k += 1
                        var args = {
                            txt: "",
                            searchfield: "name",
                            filters: {
                                "name": v[c.link_name]
                            }
                        };
                        let arr;
                        if (parseInt(v[c.is_child]) == 1) {
                            var cur_row = frappe.get_doc(doctype_name, selected);
                            arr = JSON.parse(cur_row[field]);
                        }
                        else {
                            arr = JSON.parse(cur_dialog.fields_dict[field].get_value());
                        }
                        if ($.inArray(v[c.link_name], arr) == -1) {
                            drp_html += '<li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;"><a style="display: none;"><strong>' + v[c.link_name] + '</strong></a><label class="switch" style="float:right; margin:0px; cursor:pointer;"><input type="checkbox" class="popupCheckBox" name="vehicle1" value="0" id="' + v[c.link_name] + '" data-doctype="' + c.doctype + '" data-name="' + c.name + '" data-child="' + c.is_child + '" data-reference_doc="' + c.reference_doc + '" data-reference_fields="' + c.reference_fields + '" data-search_fields="' + c.search_fields + '"  data-child_link="' + c.child_tab_link + '" onclick="selected_multiselect_lists1($(this))"><span class=" slider round"></span></label><p style="font-size: 14px;">';
                            if (v["parent_categories"]) {
                                    drp_html += '' + v["parent_categories"] + '</span></p></li>';
                            } else {
                                    drp_html += '' + v[c.search_fields] + '</span></p></li>';
                            }
                        } else {
                            drp_html += '<li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;"><a style="display: none;"><strong>' + v[c.link_name] + '</strong></a><label class="switch" style="float:right; margin:0px; cursor:pointer;"><input type="checkbox" class="popupCheckBox" name="vehicle1" value="0" id="' + v[c.link_name] + '" data-doctype="' + c.doctype + '" data-name="' + c.name + '" data-child="' + c.is_child + '" data-reference_doc="' + c.reference_doc + '" data-reference_fields="' + c.reference_fields + '" data-search_fields="' + c.search_fields + '" data-child_link="' + c.child_tab_link + '" onclick="selected_multiselect_lists1($(this))" checked><span class=" slider round"></span></label><p style="font-size: 14px;">';
                            if (v["parent_categories"]) {
                                    drp_html += '' + v["parent_categories"] + '</span></p></li>';
                            } else {
                                    drp_html += '' + v[c.search_fields] + '</span></p></li>';
                            }
                        }
                    } else {
                        drp_html += '<li></li>';
                    }
                })
                drp_html += '</ul></div></div><p class="help-box small text-muted hidden-xs">' + c.description + '</p>';
                cur_dialog.fields_dict["category_html"].$wrapper.append(drp_html);
            }
        })
    });

}

function generate_image_html(data1) {
    let html = '<div class="uploadFiles"><div class="title">Uploaded Files<button id="saveImages" class="btn btn-primary" style="float:right;margin-top: -4px;">Save</button></div><ul id="sortable">'
    $(data1.product_images).each(function(i, j) {
        let checked = "";
        if (j.is_primary == 1)
            checked = 'checked="checked"'
        html += '<li data-id="' + j.name + '"><div class="row"><div class="col-md-4 image-element"><img src="' + j.list_image + '" />\
            </div><div class="col-md-6 img-name"><div class="imageName">' + j.image_name + '</div><div class="editImage" style="display:none;"><div>\
            <input type="text" name="image_name" placeholder="Image Alternate Text" value="' + j.image_name + '" /></div><div><label style="font-weight:400;font-size:12px;"><input type="checkbox" data-id="' + j.name + '" name="is_primary" ' + checked + '/> <span>Mark as Primary?</span></label></div></div></div><div class="col-md-2 img-name"><a class="img-edit" data-id="' + j.name + '">\
            <span class="fa fa-edit"></span></a><a class="img-close" data-id="' + j.name + '">\
            <span class="fa fa-trash"></span></a></div></div></li>'
    })
    html += '</ul></div>';
    files_html = html;
}

function image_dialog(data1) {
    let selected_image_list = [];
    let random = Math.random() * 100;
    localStorage.setItem("upload_tab", "Product Image");
    localStorage.setItem('randomuppy', ' ');
    let imgDialog;
    $('body').find('.modal').each(function() {
        $(this).remove()
    })
    let randomuppy = Math.random() * 100
    localStorage.setItem('randomuppy', parseInt(randomuppy))
    let template = "<div id='drag-drop-area" + parseInt(randomuppy) + "'><div class='loader'>Loading.....</div></div>";
    imgDialog = new frappe.ui.Dialog({
        title: __('Attachments'),
        fields: [
            { fieldtype: 'HTML', fieldname: 'files_list', options: files_html },
            { fieldtype: 'Column Break', fieldname: 'clb' },
            { fieldtype: 'HTML', fieldname: 'uploader', options: template }
        ],
        primary_action_label: __('Close')
    });

    imgDialog.$wrapper.find('.modal-dialog').css("width", "1030px");
    $('.modal-dialog').css("width", "1070px !important");
    imgDialog.show();
    frappe.require("assets/frappe/js/page_fileupload.js", function() {
        setTimeout(function() {
            $(imgDialog.$wrapper).find('.loader').remove()
            upload_files(parseInt(randomuppy), 'product_images', image_doctype = "Product Image", doctype = "Product", product = data1.name)
        }, 600)
    });
    imgDialog.get_close_btn().on('click', () => {
        this.on_close && this.on_close(this.item);
    });
    $(imgDialog.$wrapper).find('.img-close').on('click', function() {
        let me = this;
        imgid = $(me).attr("data-id");
        frappe.confirm(__("Do you want to delete the image?"), () => {
            frappe.call({
                method: 'go1_commerce.go1_commerce.api.delete_current_img',
                args: {
                    childname: imgid,
                    doctype: "Product"
                },
                async: false,
                callback: function(data) {
                    $(imgDialog.$wrapper).find('li[data-id="' + imgid + '"]').remove()
                    $(".menu-btn-group .dropdown-menu li a").each(function() {
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
    $(imgDialog.$wrapper).find('#saveImages').click(function() {
        let length = $(imgDialog.$wrapper).find('div[data-fieldname="files_list"] ul li').length;
        if (length > 0) {
            let count = 0;
            $(imgDialog.$wrapper).find('div[data-fieldname="files_list"] ul li').each(function() {
                let childname = $(this).attr('data-id');
                count = count + 1;
                let image_name = $(this).find('input[name="image_name"]').val();
                let primary = $(this).find('input[name="is_primary"]:checked').val()
                let is_primary = 0;
                if (primary == 'on')
                    is_primary = 1;

                frappe.call({
                    method: 'go1_commerce.go1_commerce.doctype.product.product.update_image',
                    args: {
                        count: count,
                        image_name: image_name,
                        primary: is_primary,
                        childname: childname
                    },
                    callback: function(r) {


                        imgDialog.hide();

                    }
                });
            })
        } else {
            frappe.throw('Please add images to edit them')
        }
    })
    $(imgDialog.$wrapper).find('.img-edit').click(function() {
        let me = this;
        let imgid = $(me).attr("data-id");
        let check_data = data1.product_images.find(obj => obj.name == imgid);
        $(imgDialog.$wrapper).find('#sortable li[data-id="' + imgid + '"]').find('.imageName').hide();
        $(imgDialog.$wrapper).find('#sortable li[data-id="' + imgid + '"]').find('.editImage').show();
    })
    $(imgDialog.$wrapper).find('div[data-fieldname="files_list"] ul').sortable({
        items: '.image-element',
        opacity: 0.7,
        distance: 30
    });
    $(imgDialog.$wrapper).find('input[name="is_primary"]').on('change', function() {
        let id = $(this).attr('data-id');
        $(imgDialog.$wrapper).find('input[name="is_primary"]').each(function() {
            if ($(this).attr('data-id') != id) {
                $(this).removeAttr('checked')
            }
        })
    })
}

function update_values(name, value) {
    frappe.call({
        method: 'go1_commerce.go1_commerce.page.products_bulk_update.products_bulk_update.update_bulk_data',
        args: {
            'name': name,
            'value': value
        },
        async: false,
        callback: function(data) {

        }
    })
}


function select_list_detail(e) {
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var row_id = $(e).attr('data-doctype');
    var cls = $(e).attr('data-class');
    var field = $(e).attr('data-field');
    var linkedfield = $(e).attr('data-linkfield');
    var reference_doc = $(e).attr('data-reference_doc');
    var reference_fields = unescape($(e).attr('data-reference_fields'));
    var search_fields = $(e).attr('data-search_fields');
    var reference_method = $(e).attr('data-reference_method');
    var child_tab_link = $(e).attr('data-child_link');
    var input, ul, txtValue;
    build_filter_list(row_id, cls, field, linkedfield, doctype_name, is_child, reference_doc, reference_fields, reference_method, child_tab_link, search_fields);
    if (parseInt(is_child) == 1) {
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets').css('display', 'block');
    } else {
        $('.' + cls + ' #assets').css('display', 'block');
    }
}

function disable_select_list(e) {
    setTimeout(function() {
        var row_id = $(e).attr('data-doctype')
        var cls = $(e).attr('data-class');
        var field = $(e).attr('data-field');
        var linkedfield = $(e).attr('data-linkfield');
        var doctype_name = $(e).attr('data-doctype');
        var is_child = $(e).attr('data-child');
        var reference_doc = $(e).attr('data-reference_doc');
        var reference_fields = unescape($(e).attr('data-reference_fields'));
        var search_fields = $(e).attr('data-search_fields');
        var child_tab_link = $(e).attr('data-child_link');
        var ids = $(e).attr('id');
        if (parseInt(is_child) == 1) {
            $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets.assets').attr('style', "display:none !important;");
        } else {
            
        }
    }, 500);
}

function selected_lists_values(e) {
    var cls = $(e).attr('data-class');
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var child_tab_link = $(e).attr('data-child_link');
    var field = $('.' + cls + ' #myInput').attr('data-field');
    var linkedfield = $('.' + cls + ' #myInput').attr('data-linkfield');
    var ids = $(e).attr('id');
    if (parseInt(is_child) == 1) {
        var row_id = $(e).attr('data-doctype')
        var input, filter, ul, li, a, i, txtValue;
        input = $('div[data-name="' + row_id + '"]').find('.' + cls + ' #myInput').val()
        filter = input.toUpperCase();
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets').css('display', 'block')
        li = $('div[data-name="' + row_id + '"]').find("li");
        for (i = 0; i < li.length; i++) {
            a = li[i].getElementsByTagName("a")[0];
            txtValue = a.textContent || a.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                li[i].style.display = "";
            } else {
                li[i].style.display = "none";
            }
        }
    } else {
        var input, filter, ul, li, a, i, txtValue;
        input = $('.' + cls + ' #myInput').val();
        filter = input.toUpperCase();
        $('.' + cls + ' #assets').css('display', 'block')
        li = $('.' + cls + ' #assets').find("li");
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
    }
}

function remove_selected_list(e) {
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var row_id = $(e).attr('data-doctype')
    var cls = $(e).attr('data-class');
    var field = $('.' + cls + ' #myInput').attr('data-field');
    var linkedfield = $('.' + cls + ' #myInput').attr('data-linkfield');
    var child_tab_link = $(e).attr('data-child_link');
    var ids = $(e).attr('id');
    afterDeselectlist(ids, cls, field, linkedfield, doctype_name, is_child, child_tab_link)
    if (parseInt(is_child) == 1) {
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' .tb-selected-value[data-value=' + ids + ']').remove();
    } else {
        $('.' + cls + ' .tb-selected-value[data-value=' + ids + ']').remove();
    }
}