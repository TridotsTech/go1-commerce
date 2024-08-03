function select_allbusiness(frm,possible_val){
    if($("#select-all").prop("checked") == true){
        $("#assets input[type='checkbox']").prop("checked",true);
    }
    else{
         $("#assets input[type='checkbox']").prop("checked",false);
    }
     $("#assets input[type='checkbox']").each(function(){
        selected_multiselect_lists($(this));
    });

 }

function product_pricing_tool(){
    frappe.set_route('Form', 'Product Pricing Tool', 'Product Pricing Tool')
}
function walletDialog(e) {}

function make_settlement() {
    let d = {
        'page_no': 1,
        'page_len': 10
    }
    cur_frm.order_list = [];
    new go1_commerce.WalletOrders({
        page_len: 10,
        user: cur_frm.doc.user,
        type: "Settlement"
    })
}

function mark_as_received() {
    cur_frm.trigger('add_fund_vendor')
}

function view_vendor_payment() {
    if (cur_frm.doc.user != "Service Provider") {
        frappe.set_route('List', 'Payment Entry', { "party": cur_frm.doc.user });
    } else {
        frappe.set_route('List', 'Payment Entry', { "type": cur_frm.doc.user });
    }
}
// add transalation
function add_translation() {
    var source_name = cur_frm.doctype
    var source_value = cur_frm.docname
    this.data = [];
    var field_option = [];
    frappe.call({
        method: 'go1_commerce.go1_commerce.api.get_fields_label_with_options',
        args: { doctype: source_name },
        async: false,
        callback: function(r, rt) {
            if (r.message) {
                $.each(r.message, function(i, v) {
                    field_option.push({ "lable": v.label, 'fieldname': v.fieldname })
                })

            }
        }
    });

    this.dialog = new frappe.ui.Dialog({
        fields: this.get_fields(source_name, source_value),
        title: __('Translate {0}', [source_name]),
        no_submit_on_enter: true,
        primary_action_label: __('Update Translations'),
        primary_action: (values) => this.update_translations(this.dialog.get_values())
            .then(() => {
                this.dialog.hide();

                this.data = [];

                frappe.msgprint({
                    title: __('Success'),
                    message: __('Successfully updated translations'),
                    indicator: 'green'
                });
            })
    });
    this.get_translations_data(source_value)
        .then(data => {
            var result = []
            var reference = []
            if (data) {
                $.each(data, function(r, k) {

                    var x = r + 1
                    var curnt = cur_frm.doc[k.field_translate]
                    reference.push(k.field_translate)
                    if (curnt == k.source_name) {
                        result.push({
                            'id': x,
                            'name': k.name,
                            'source': k.source_name,
                            'language': k.language,
                            'field_translate': k.field_translate,
                            'translation': k.target_name
                        });
                    } else {
                        result.push({
                            'id': x,
                            'name': k.name,
                            'source': k.source_name,
                            'language': k.language,
                            'field_translate': k.field_translate,
                            'translation': ""
                        });
                    }

                })
                var data_len = data.length
                $.each(frappe.boot.sysdefaults.translation_settings.language, function(i, v) {
                    $.each(field_option, function(j, s) {
                        var val = s.fieldname
                        var res = cur_frm.doc[val]
                        if ($.inArray(val, reference) == -1) {
                            result.push({
                                'id': data_len + 1,
                                'name': "batch " + data_len + 1,
                                'field_translate': val,
                                'source': res,
                                'language': v.language,
                                'translation': ""
                            });
                        }
                    })
                })
            } else {
                var lang = 0
                $.each(frappe.boot.sysdefaults.translation_settings.language, function(i, v) {
                    $.each(field_option, function(j, s) {
                        lang = j + 1
                        var val = s.fieldname
                        var res = cur_frm.doc[val]
                        result.push({
                            'id': lang,
                            'name': "batch " + lang,
                            'field_translate': val,
                            'source': res,
                            'language': v.language,
                            'translation': ""
                        });

                    })
                })
            }
            this.data.push(...(result || []));
            this.dialog.refresh();
            this.dialog.show();
            this.dialog.$wrapper.find('.modal-dialog').css('width', '1050px');
            this.dialog.refresh();
            var cls = this.dialog
            var error = "<ul>"
            var is_throw = 0
            $.each(field_option, function(i, v) {
                if (!cur_frm.doc[v.fieldname]) {
                    cls.hide();
                    error += "<li>" + v.lable + "</li>";
                    is_throw = 1
                }
            })
            error += "</ul>";
            if (is_throw == 1 && error) {
                frappe.throw(__(`Please fill the field ${error}`));
            }

        });
}

function get_translations_data(source_value) {
    return frappe.db.get_list('DocType Translation', {
        fields: ['idx', 'field_translate', 'source_name', 'language', 'target_name', 'name', 'parent'],
        filters: {
            parent: source_value,
        },
        parent: "Custom Doc Translation",
        ignore_permissions: true
    });
}

function get_fields(source_name, source_value) {

    var fields = [{
            label: __('Page'),
            fieldname: 'source',
            fieldtype: 'Data',
            read_only: 1,
            bold: 1,
            default: source_name
        },
        {
            label: __('Title'),
            fieldname: 'source_value',
            fieldtype: 'Data',
            read_only: 1,
            bold: 1,
            default: source_value
        },
        {
            label: __('Translations'),
            fieldname: 'translation_data',
            fieldtype: 'Table',
            fields: [{
                    label: __('Field'),
                    fieldname: 'field_translate',
                    fieldtype: 'Data',
                    read_only: 1,
                    in_list_view: 0,
                },
                {
                    label: __('Original Text'),
                    fieldname: 'source',
                    fieldtype: 'Data',
                    read_only: 1,
                    in_list_view: 1,
                    option: "",
                    default: "",
                    columns: 4
                },
                {
                    label: 'Language',
                    fieldname: 'language',
                    fieldtype: 'Link',
                    options: 'Language',
                    in_list_view: 1,
                    read_only: 1,
                    columns: 1
                },
                {
                    label: 'Translated Text',
                    fieldname: 'translation',
                    fieldtype: 'Text',
                    in_list_view: 1,
                    columns: 5
                }
            ],
            data: this.data,
            get_data: () => {
                return this.data;
            }
        }
    ];

    return fields;
}

function update_translations(data) {
    return frappe.call({
        method: 'go1_commerce.go1_commerce.api.update_translations_for_docpage',
        btn: this.dialog.get_primary_btn(),
        args: {
            source: data.source,
            source_value: data.source_value,
            translation_dict: data.translation_data
        }
    }).fail(() => {
        frappe.msgprint({
            title: __('Something went wrong'),
            message: __('Please try again'),
            indicator: 'red'
        });
    });
}

function option_selection(e){
    var val = $(e).text();
    var idx = parseInt($(e).parent().parent().attr("data-idx"));
    var index = parseInt($(e).parent().parent().attr("data-index"));

    $(e).parent().parent().prev("#select_options"+idx).val(val)
   
    let me = this;
     $(e).parent().hide();
    if(val){

        $(e).attr("data-value", val);
        $(e).attr("data-name", "");
        var attr_arr=[];
        var attr_arr_val ="";
        var option_index=0;
        var varient_options  = cur_frm.doc.attribute_options.filter( x =>  x.attribute == cur_frm.doc.product_attributes[index].product_attribute && x.attribute_id == cur_frm.doc.product_attributes[index].name);
        if (!varient_options){
         varient_options = []
       }
        let oindex =varient_options.findIndex(x => x.option_value == val);
  
        if(varient_options){

            option_index = varient_options.length;
        }
       
        var pre_selected=0;
        var btn_cls = 'btn-default';
        if(option_index==0){
            pre_selected=1
            btn_cls = 'btn-info';
        }
       if(oindex<0){
        let child = frappe.model.add_child(cur_frm.doc, "Product Attribute Option", "attribute_options");
       
        child.attribute_id = cur_frm.doc.product_attributes[index]["name"]
        child.display_order = 0
        child.idx = option_index
        child.is_pre_selected = pre_selected
        child.option_value = $(e).attr("data-value")
        child.attribute =cur_frm.doc.product_attributes[index]["product_attribute"];
        cur_frm.refresh_field("attribute_options");

        var optionhtmls = '<div class="btn-group tb-selected-value" id="multi_input_updatevalue" style="display: inline-block;margin-bottom: 5px;" data-value="'+val+'" data-name="" data-index="'+index+'">'
        optionhtmls += '<a class="btn '+btn_cls+' btn-xs btn-link-to-form" data-id="'+val+'" data-attribute="'+cur_frm.doc.product_attributes[index]["product_attribute"]+'" data-index="'+index+'" data-option_name="" data-display_order="'+cur_frm.doc.product_attributes[index]["display_order"]+'" data-is_pre_selected="'+cur_frm.doc.product_attributes[index]["is_pre_selected"]+'" data-product_title="'+cur_frm.doc.product_attributes[index]["product_title"]+'"  data-disable="'+cur_frm.doc.product_attributes[index]["disable"]+'" data-parent-control-type="'+cur_frm.doc.product_attributes[index]["control_type"]+'" data-attribute_color="'
        if($(e).attr("data-attribute_color")){
            optionhtmls += $(e).attr("data-attribute_color")
        }
        optionhtmls +='" onclick="pick_color($(this))" ondblclick="update_attroption($(this))"><img src="/assets/go1_commerce/images/section-icon.svg" style="height:10px;cursor: all-scroll;position: relative;">'+val+'</a>'
        optionhtmls += '<a class="btn '+btn_cls+' btn-xs btn-remove" data-id="'+val+'" onclick="remove_attroption($(this))"><i class="fa fa-remove text-muted"></i> </a></div>'
        $(e).parent().parent().parent().parent().before(optionhtmls);
        $(e).parent().parent().parent().find("input").val("");
        $(e).val("");

        }else{
            show_alert("Option "+val+" already added.")
            $(e).parent().parent().parent().find("input").val("");
        }
        $(e).parent().parent().parent().parent().parent().find('.tb-selected-value').each(function() {
            var option_index=0;
            if(varient_options){
                option_index = varient_options.length;
            }
            var doc = {"doctype":"Product Attribute Option","attribute": cur_frm.doc.product_attributes[index]["product_attribute"],"attribute_color": $(this).attr("data-attribute_color"),
            "attribute_id": cur_frm.doc.product_attributes[index]["name"],"disable": 0,"display_order": 1,"idx": option_index,"image": "",
            "image_list": null,"is_pre_selected": 0,"option_value": $(this).attr("data-value"),
            "parent": cur_frm.doc.name,"parentfield": "attribute_options","parenttype": "Product","parent_option":"",
            "price_adjustment": 0,"product_title": "-","quantity": 0,"unique_name": "", "name":$(this).attr("data-name")}
            attr_arr.push(doc);
            if(attr_arr_val){
                attr_arr_val +=", "
            }
            attr_arr_val += $(e).attr("data-value");
        })

        cur_frm.dirty()
        cur_frm.create_combination = 1 ;
    }
    $("#awesompletelist_"+idx).show()
}



function clearAction(e) {
    if (cur_frm) {
        $('body').find('.modal').each(function() {
            $(this).remove()
        })
        frappe.confirm(__('Do you want to clear this form?'), () => {
            frappe.run_serially([
                () => {
                    cur_frm.reload_doc()
                    frappe.show_alert(__("Form Cancelled!"));
                    frappe.set_route("List", cur_frm.doctype);
                }
            ])
        });
    }
}

function selected_multiselect_lists(e) {
    var actual_value = $(e).attr('id');
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var child_tab_link = $(e).attr('data-child_link');
    var row_id = cur_frm.selected_doc.name
    var cls = $(e).parent().parent().parent().parent().parent().attr('class');
    var field = $('.' + cls + ' #myInput').attr('data-field');
    var linkedfield = $('.' + cls + ' #myInput').attr('data-linkfield');
    if ($(e).is(':checked')) {
        afterSelectlist($(e).parent().parent().find('a').text(), cls, field, linkedfield, doctype_name, is_child, child_tab_link, actual_value)
    } else {
        afterDeselectlist(actual_value, cls, field, linkedfield, doctype_name, is_child, child_tab_link)
    }

    if (parseInt(is_child) == 1) {
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #myInput').attr('data-id', $(e).attr('id'))
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets').css('display', 'none')
    } else {
        $('.' + cls + ' #myInput').attr('data-id', $(e).attr('id'))
    }
}

function select_list_detail(e) {
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var row_id = cur_frm.selected_doc.name
    var cls = $(e).attr('data-class');
    var field = $(e).attr('data-field');
    var linkedfield = $(e).attr('data-linkfield');
    var reference_doc = $(e).attr('data-reference_doc');
    var business = unescape($(e).attr('data-business'));
    var reference_fields = unescape($(e).attr('data-reference_fields'));
    var search_fields = $(e).attr('data-search_fields');
    var reference_method = $(e).attr('data-reference_method');
    var child_tab_link = $(e).attr('data-child_link');
    var input, ul, txtValue;
    build_filter_list(row_id, cls, field, linkedfield, doctype_name, is_child, reference_doc, reference_fields, reference_method, child_tab_link, search_fields, business);
    if (parseInt(is_child) == 1) {
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets').css('display', 'block');
    } else {
        $('.' + cls + ' #assets').css('display', 'block');
    }


}

function afterDeselectlist(values, cls, field, linkedfield, doctype_name, is_child, child_tab_link) {
    if (parseInt(is_child) == 1) {
        var cur_row = frappe.get_doc(doctype_name, cur_frm.selected_doc);
        if (!cur_row[field] || cur_row[field] == undefined || cur_row[field] == "") {
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, '[]')
        } else {
            let arr = JSON.parse(cur_row[field]);
            var index = arr.indexOf(values);
            if (index >= -1) {
                arr.splice(index, 1);
            }
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, JSON.stringify(arr))
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
            cur_dialog.fields_dict[field].set_value(JSON.stringify(arr))

        }
    }

}

function build_filter_list(selected, cls, field, linkedfield, doctype_name, is_child, reference_doc, reference_fields, reference_method, child_tab_link, search_fields, tab_html_field,hasimage, imagefield, link_field, business, txtValue) {
    var url = '/api/method/' + reference_method
    cur_frm.page_no = cur_frm.page_no+1
   var filters=""
    if(reference_doc=="Product Attribute"){
        filters = JSON.stringify(cur_frm.doc.product_categories)
    }
    $.ajax({
        type: 'POST',
        Accept: 'application/json',
        ContentType: 'application/json;charset=utf-8',
        url: window.location.origin + url,
        data: {
            "reference_doc": reference_doc,
            "reference_fields": reference_fields,
             "filters": filters,
             "page_no": cur_frm.page_no,
            "business": business,
            "search_txt": txtValue,
            "search_field": search_fields
        },
        dataType: "json",
        async: false,
        headers: {
            'X-Frappe-CSRF-Token': frappe.csrf_token
        },
        success: function(r) {
            console.log(r.message)
            var drp_html = '';
            var item = r.message.list_name;
            if (parseInt(is_child) == 1) {
                $('div[data-name="' + selected + '"]').find('.' + cls + ' #assets').empty();
            } else {
                $('.' + cls + ' #assets').empty();
            }
            if (item.length > 0) {
                var k = 0
                $.each(item, function(i, v) {
                    if (v[linkedfield]) {
                        let business_div = '';
                        if(v.business && has_common(frappe.user_roles, ['Admin', 'System Manager']))
                            business_div = '(' + (v.business || '') + ')';
                        let arr;
                        if (parseInt(is_child) == 1) {
                            var cur_row = frappe.get_doc(doctype_name, selected);
                            arr = JSON.parse(cur_row[field]);
                        }
                        else {
                            arr = JSON.parse(cur_dialog.fields_dict[field].get_value());
                        }
                        if ($.inArray(v[linkedfield], arr) == -1) {
                            k += 1;
                            drp_html += '<li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;"><a style="display: none;"><strong>' + v[linkedfield] + '</strong></a><label class="switch" style="float:right; margin:0px; cursor:pointer;"><input type="checkbox" class="popupCheckBox" name="vehicle1" value="0" id="' + v[linkedfield] + '" data-doctype="' + doctype_name + '" data-child="' + is_child + '" data-child_link="' + child_tab_link + '" onclick="selected_multiselect_lists($(this))"><span class=" slider round"></span></label>';
                            if((hasimage==1 || hasimage=="1") && imagefield){
                                    var img_field = v[imagefield]
                                    if(!imagefield || !v[imagefield] || imagefield=="null" || v[imagefield]=="null" || v[imagefield]==null || v[imagefield]==undefined){
                                        img_field = "/assets/erp_ecommerce_business_store/images/no-image-60x50.png"
                                        
                                    }
                                    
                                    drp_html += '<img src="'+img_field+'" alt=""  style="float: left;width: 35px;padding: 5px;height: 35px;">';
                                }
                            drp_html += '<p style="font-size: 14px;">';

                            if (v[link_field]) {
                               
                                    drp_html += '' + v[link_field] + ' ' + business_div + '</p></li>';
                            } else {
                                
                                    drp_html += '' + v[search_fields] + ' ' + business_div + '</p></li>';
                            }
                        } else {
                            k += 1;
                            drp_html += '<li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;"><a style="display: none;"><strong>' + v[linkedfield] + '</strong></a><label class="switch" style="float:right; margin:0px; cursor:pointer;"><input type="checkbox" class="popupCheckBox" name="vehicle1" value="0" id="' + v[linkedfield] + '" data-doctype="' + doctype_name + '" data-child="' + is_child + '" data-child_link="' + child_tab_link + '" onclick="selected_multiselect_lists($(this))" checked><span class=" slider round"></span></label>';
                            if((hasimage==1 || hasimage=="1") && imagefield){
                                    var img_field = v[imagefield]
                                    if(!imagefield || !v[imagefield] || imagefield=="null" || v[imagefield]=="null" || v[imagefield]==null || v[imagefield]==undefined){
                                        img_field = "/assets/erp_ecommerce_business_store/images/no-image-60x50.png"
                                        
                                    }
                                    
                                    drp_html += '<img src="'+img_field+'" alt=""  style="float: left;width: 35px;padding: 5px;height: 35px;">';
                                }
                            drp_html += '<p style="font-size: 14px;">';
                            if (v[link_field]) {
                               
                                    drp_html += '' + v[link_field] + ' ' + business_div + '</p></li>';
                            } else {
                                
                                    drp_html += '' + v[search_fields] + ' ' + business_div + '</p></li>';
                            }
                        }
                    }
                })
            } else {
                drp_html += '<li></li>';
            }

            if (parseInt(is_child) == 1) {
                $('div[data-name="' + selected + '"]').find('.' + cls + ' #assets').html(drp_html);
            } else {
                $('.' + cls + ' #assets').html(drp_html)
            }

        }
    })

}

function enterKeyPressed(event, e) {
      if (event.keyCode == 13) {

         search_focuson_detail(e)
      } 
   }

function search_onbutton(e){
    console.log(e)
    console.log($(e).prev())
        search_focuson_detail($(e).prev())
}

function search_focuson_detail(e) {
   
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var row_id = cur_frm.selected_doc.name
    var cls = $(e).attr('data-class');
    var field = $(e).attr('data-field');
    var linkedfield = $(e).attr('data-linkfield');
    var link_field = $(e).attr('data-link_field');
    var reference_doc = $(e).attr('data-reference_doc');
    var business = unescape($(e).attr('data-business'));
    var reference_fields = unescape($(e).attr('data-reference_fields'));
    var search_fields = $(e).attr('data-search_fields');
    var reference_method = $(e).attr('data-reference_method');
    var child_tab_link = $(e).attr('data-child_link');
    var tab_html_field = $(e).attr('data-tab_html_field');
    var hasimage = $(e).attr('data-hasimage');
    var imagefield = $(e).attr('data-imagefield');
    
    var input, ul;
    var txtValue = $(e).val();
    cur_frm.page_no = 0
    build_filter_list(row_id, cls, field, linkedfield, doctype_name, is_child, reference_doc, reference_fields, reference_method, child_tab_link, search_fields, tab_html_field, hasimage,imagefield, link_field,business, txtValue);
    if (parseInt(is_child) == 1) {
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets').css('display', 'block');
    } else {
        $('.' + cls + ' #assets').css('display', 'block');
    }
}

function search_focusout_detail(e) {
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var row_id = cur_frm.selected_doc.name
    var cls = $(e).attr('data-class');
    var field = $(e).attr('data-field');
    var linkedfield = $(e).attr('data-linkfield');
    var link_field = $(e).attr('data-link_field');
    var reference_doc = $(e).attr('data-reference_doc');
    var business = unescape($(e).attr('data-business'));
    var reference_fields = unescape($(e).attr('data-reference_fields'));
    var search_fields = $(e).attr('data-search_fields');
    var reference_method = $(e).attr('data-reference_method');
    var child_tab_link = $(e).attr('data-child_link');
    var tab_html_field = $(e).attr('data-tab_html_field');
    var hasimage = $(e).attr('data-hasimage');
    var imagefield = $(e).attr('data-imagefield');
    
    var input, ul;
    var txtValue = $(e).val();
    cur_frm.page_no = 0
    build_filter_list(row_id, cls, field, linkedfield, doctype_name, is_child, reference_doc, reference_fields, reference_method, child_tab_link, search_fields, tab_html_field, hasimage,imagefield, link_field,business, txtValue);
    if (parseInt(is_child) == 1) {
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets').css('display', 'block');
    } else {
        $('.' + cls + ' #assets').css('display', 'block');
    }
}


function disable_select_list(e) {
    setTimeout(function() {
        var row_id = cur_frm.selected_doc.name
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
        var row_id = cur_frm.selected_doc.name
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
    var row_id = cur_frm.selected_doc.name
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

function afterSelectlist(values, cls, field, linkedfield, doctype_name, is_child, child_tab_link, actual_value) {
    if (parseInt(is_child) == 1) {
        var cur_row = frappe.get_doc(doctype_name, cur_frm.selected_doc);
        if (!cur_row[field] || cur_row[field] == undefined || cur_row[field] == "") {
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, '[]');
            var row_val = frappe.model.get_value(doctype_name, cur_frm.selected_doc.name, field);
            let arr = JSON.parse(row_val);
            if (actual_value) {
                arr.push(actual_value);
            }
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, JSON.stringify(arr));
            $('.' + cls + ' #myInput').val('');
        } else {
            let arr = JSON.parse(cur_row[field]);
            if (actual_value) {
                arr.push(actual_value);
            }
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, JSON.stringify(arr));
            $('.' + cls + ' #myInput').val('');
        }
    } else {
        var dialog_val = cur_dialog.fields_dict[field].get_value();
        if (!dialog_val || dialog_val == undefined || dialog_val == "") {
            cur_dialog.fields_dict[field].set_value('[]');
            var row_val = cur_dialog.fields_dict[field].get_value();
            let arr = JSON.parse(row_val);
            if (actual_value) {
                arr.push(actual_value);
            }
            cur_dialog.fields_dict[field].set_value(JSON.stringify(arr));
            $('.' + cls + ' #myInput').val('');
        } else {
            let arr = JSON.parse(cur_dialog.fields_dict[field].get_value());
            if (actual_value) {
                arr.push(actual_value);
            }
            cur_dialog.get_field(field).set_value(JSON.stringify(arr));
            cur_dialog.get_field(field).refresh();
            $('.' + cls + ' #myInput').val('');
        }
    }
}


function afterDeselectlist(values, cls, field, linkedfield, doctype_name, is_child, child_tab_link) {
    if (parseInt(is_child) == 1) {
        var cur_row = frappe.get_doc(doctype_name, cur_frm.selected_doc);
        if (!cur_row[field] || cur_row[field] == undefined || cur_row[field] == "") {
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, '[]')
        } else {
            let arr = JSON.parse(cur_row[field]);
            var index = arr.indexOf(values);
            if (index >= -1) {
                arr.splice(index, 1);
            }
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, JSON.stringify(arr))
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
            cur_dialog.fields_dict[field].set_value(JSON.stringify(arr))

        }
    }

}


function select_lists_forpdt(e) {
    var cls = $(e).attr('data-class');
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var child_tab_link = $(e).attr('data-child_link');
    var field = $('.' + cls + ' #myInput').attr('data-field');
    var linkedfield = $('.' + cls + ' #myInput').attr('data-linkfield');
    var ids = $(e).attr('id');
    if (parseInt(is_child) == 1) {
        var row_id = cur_frm.selected_doc.name
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

    get_multiselect_values_forpdt(cls, field, linkedfield, doctype_name, is_child, child_tab_link)
}


function selected_lists_forpdt(e) {
    var actual_value = $(e).attr('id');
    var item_label = $(e).text();
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var child_tab_link = $(e).attr('data-child_link');
    var row_id = cur_frm.selected_doc.name
    var cls = $(e).parent().parent().parent().parent().attr('class');
    var field = $('.' + cls + ' #myInput').attr('data-field');
    var linkedfield = $('.' + cls + ' #myInput').attr('data-linkfield');
    afterSelectpdt(item_label, cls, field, linkedfield, doctype_name, is_child, child_tab_link, actual_value)
    if (parseInt(is_child) == 1) {
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #myInput').attr('data-id', $(e).attr('id'))
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets').css('display', 'none')
    } else {
        $('.' + cls + ' #myInput').attr('data-id', $(e).attr('id'))
        $('.' + cls + ' #assets').css('display', 'none')

    }

}


function afterSelectpdt(value_label, cls, field, linkedfield, doctype_name, is_child, child_tab_link, actual_value) {
    if (parseInt(is_child) == 1) {
        var cur_row = frappe.get_doc(doctype_name, cur_frm.selected_doc);
        if (!cur_row[field] || cur_row[field] == undefined || cur_row[field] == "") {
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, '[]');
            var row_val = frappe.model.get_value(doctype_name, cur_frm.selected_doc.name, field);
            if (typeof(row_val) == "string") {
                var arr = JSON.parse(row_val);
            } else {
                var arr = row_val;
            }

            if (actual_value) {
                arr.push({ "name": actual_value, "label": value_label });
                var index = arr.indexOf({ "name": actual_value, "label": value_label });
            }
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, JSON.stringify(arr));
            $('.' + cls + ' #myInput').val('');
        } else {
            if (typeof(cur_row[field]) == "string") {
                var arr = JSON.parse(cur_row[field]);
            } else {
                var arr = cur_row[field];
            }
            if (actual_value) {
                arr.push({ "name": actual_value, "label": value_label });
            }
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, JSON.stringify(arr));
            $('.' + cls + ' #myInput').val('');
        }
    } else {
        if (!cur_frm.doc[field] || cur_frm.doc[field] == undefined || cur_frm.doc[field] == "") {
            cur_frm.set_value(field, '[]');
            var row_val = cur_frm.doc[field];
            var arr = JSON.parse(row_val);
            if (actual_value) {
                arr.push({ "name": actual_value, "label": value_label });
            }
            cur_frm.set_value(field, JSON.stringify(arr));
            $('.' + cls + ' #myInput').val('');
        } else {
            let arr = JSON.parse(cur_frm.doc[field]);
            if (actual_value) {
                arr.push({ "name": actual_value, "label": value_label });
            }
            cur_frm.set_value(field, JSON.stringify(arr));
            $('.' + cls + ' #myInput').val('');
        }
    }

    get_multiselect_values_forpdt(cls, field, linkedfield, doctype_name, is_child, child_tab_link)
}


function afterDeselectpdt(values, data_label, cls, field, linkedfield, doctype_name, is_child, child_tab_link) {
    if (parseInt(is_child) == 1) {
        var cur_row = frappe.get_doc(doctype_name, cur_frm.selected_doc);
        if (!cur_row[field] || cur_row[field] == undefined || cur_row[field] == "") {
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, '[]')
        } else {
            let arr;
            if (typeof(cur_row[field]) == "string") {
                arr = JSON.parse(cur_row[field]);
            } else {
                arr = cur_row[field];
            }
            var data = { "name": values, "label": data_label }
            var index = arr.indexOf(data);
            if (index >= -1) {
                arr.splice(index, 1);
            }
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, JSON.stringify(arr))
        }
    } else {

        if (!cur_frm.doc[field] || cur_frm.doc[field] == undefined || cur_frm.doc[field] == "") {
            cur_frm.set_value(field, '[]')
        } else {
            let arr;
            if (typeof(cur_frm.doc[field]) == "string") {
                arr = JSON.parse(cur_frm.doc[field]);
            } else {
                arr = cur_frm.doc[field];
            }
            var data = { "name": values, "label": data_label }
            var index = arr.indexOf(data);
            if (index >= -1) {
                arr.splice(index, 1);
            }
            cur_frm.set_value(field, JSON.stringify(arr))
        }
    }

    get_multiselect_values_forpdt(cls, field, linkedfield, doctype_name, is_child, child_tab_link)
}



function build_filter_list_forpdt(selected, cls, field, linkedfield, doctype_name, is_child, reference_doc, reference_fields, reference_method, child_tab_link, search_fields) {
    var url = '/api/method/' + reference_method
    $.ajax({
        type: 'POST',
        Accept: 'application/json',
        ContentType: 'application/json;charset=utf-8',
        url: window.location.origin + url,
        data: {
            "reference_doc": reference_doc,
            "reference_fields": reference_fields
        },
        dataType: "json",
        async: false,
        headers: {
            'X-Frappe-CSRF-Token': frappe.csrf_token
        },
        success: function(r) {
            var drp_html = '';
            var item = r.message.list_name;
            if (parseInt(is_child) == 1) {
                $('div[data-name="' + selected + '"]').find('.' + cls + ' #assets').empty();
            } else {
                $('.' + cls + ' #assets').empty();
            }
            if (item.length > 0) {
                var k = 0
                $.each(item, function(i, v) {
                    if (v[linkedfield]) {
                        let arr;
                        if (parseInt(is_child) == 1) {
                            var cur_row = frappe.get_doc(doctype_name, selected);
                            if (typeof(cur_row[field]) == "string") {
                                arr = JSON.parse(cur_row[field]);
                            } else {
                                arr = cur_row[field];
                            }
                        }
                        else {
                            if (typeof(cur_frm.doc[field]) == "string") {
                                arr = JSON.parse(cur_frm.doc[field]);
                            } else {
                                arr = cur_row[field];
                            }
                        }
                        var data = { "name": v[linkedfield], "label": v[linkedfield] + "(" + v[search_fields] + ")" }
                        var index = arr.indexOf(data);
                        if ($.inArray(data, arr) == -1) {
                            k += 1
                            if (k > 5) {
                                drp_html += '<li><a id="' + v[linkedfield] + '" data-doctype="' + doctype_name + '" data-child="' + is_child + '" data-reference_doc="' + reference_doc + '" data-reference_fields="' + reference_fields + '" data-search_fields="' + search_fields + '" data-child_link="' + child_tab_link + '" onclick="selected_lists_forpdt($(this))"><p><strong>' + v[linkedfield] + '</strong>(' + v[search_fields] + ')</a></li>';

                            } else {
                                drp_html += '<li style="display: block"><a id="' + v[linkedfield] + '" data-doctype="' + doctype_name + '" data-child="' + is_child + '" data-reference_doc="' + reference_doc + '" data-reference_fields="' + reference_fields + '" data-search_fields="' + search_fields + '" data-child_link="' + child_tab_link + '" onclick="selected_lists_forpdt($(this))"><strong>' + v[linkedfield] + '</strong>(' + v[search_fields] + ')</a></li>';
                            }
                        }
                    }
                })
            } else {
                drp_html += '<li></li>';
            }

            if (parseInt(is_child) == 1) {
                $('div[data-name="' + selected + '"]').find('.' + cls + ' #assets').html(drp_html);
            } else {
                $('.' + cls + ' #assets').html(drp_html)
            }

        }
    })

}


$(document).keyup(function(e) {
    if (e.keyCode == 27) {
        $('#assets.assets').hide();
    }

});

$(document).ready(function() {
    frappe.require("/assets/go1_commerce/css/ui/jodit.min.css");
    frappe.require("/assets/go1_commerce/js/ui/jodit.min.js");
    let doctypes_list = get_doctypes_list();
    $(document).bind('form-refresh', function() {
          let fields = frappe.get_meta(cur_frm.doc.doctype).fields
          let editors= fields.filter(obj => obj.fieldtype == "Text Editor");
          if(editors){
               $.each(editors, function(i, v) {
                     var editor = cur_frm.fields_dict[v.fieldname].$wrapper.find('.control-input-wrapper .control-input div#custom-note-editor');
                     if(editor){
                        var html = ""
                        if (cur_frm.doc[v.fieldname]){
                            html = cur_frm.doc[v.fieldname]
                        }
                         $(editor).find('.note-editable').html(html);
                       
                     }
                 })
         }
        let check_doc = doctypes_list.find(obj => obj.doctype == cur_frm.doctype);
        if (check_doc) {
            frappe.ui.form.on(cur_frm.doctype, {
                refresh: function(frm) {
                    frm.set_df_property(check_doc.field, 'hidden', 0)
                },
                load_custom_editor: function(frm) {
                    if (!Jodit.instances.jeditor_webpage) {
                        $(frm.get_field('jodit_editor').wrapper).empty();
                        $('<div class="clearfix"><label class="control-label" style="padding-right: 0px;">' + __(check_doc.title) + '</label></div><textarea id="jeditor_webpage"></textarea>').appendTo(frm.fields_dict.jodit_editor.wrapper);
                        var ele = document.getElementById('jeditor_webpage');
                       
                        var editor = new Jodit(ele, {
                            colorPickerDefaultTab: 'color',
                             colors: ['#ff0000', '#00ff00', '#0000ff'],
                             filebrowser: {
                                 isSuccess: function (resp) {
                                      console.log(resp)
                                        return resp.length !== 0;
                                    },
                                    getMsg: function (resp) {
                                        console.log(resp)
                                        return resp;
                                    },
                                    ajax: {
                                        url: 'ajax.php',
                                        method: 'GET',
                                        dataType: 'text',
                                        headers: {
                                            'X-CSRF-Token': frappe.csrf_token
                                        },
                                        data: {
                                            someparameter: 1
                                        },
                                        prepareData: function (data) {
                                            data.someparameter++;
                                             console.log(data)
                                            return data;
                                        },
                                        process: function (resp) {
                                            console.log(resp)
                                            return resp.split('|'); 
                                        },
                                    }
                             },
                            uploader: {
                                url: window.location.origin + '/api/method/uploadfile',
                                format: 'json',
                                pathVariableName: 'path',
                                filesVariableName: 'images',
                                prepareData: function (data) {
                                    console.log(data)
                                    return data;
                                },
                                isSuccess: function (resp) {
                                    console.log(resp)
                                    return !resp.error;
                                },
                                getMsg: function (resp) {
                                    console.log(resp)
                                    return resp.msg.join !== undefined ? resp.msg.join(' ') : resp.msg;
                                },
                                process: function (resp) {
                                    console.log(resp)
                                    console.log(this.options.uploader.filesVariableName)
                                    console.log(resp[this.options.uploader.filesVariableName])
                                    return {
                                        files: resp[this.options.uploader.filesVariableName] || [],
                                        path: resp.path,
                                        baseurl: resp.baseurl,
                                        error: resp.error,
                                        msg: resp.msg
                                    };

                                },
                                error: function (e) {
                                    console.log(e)
                                    this.events.fire('errorPopap', [e.getMessage(), 'error', 4000]);
                                },
                                defaultHandlerSuccess: function (data, resp) {
                                     console.log(resp)
                                      console.log(data)
                                    var i, field = this.options.uploader.filesVariableName;
                                    if (data[field] && data[field].length) {
                                        for (i = 0; i < data[field].length; i += 1) {
                                            this.selection.insertImage(data.baseurl + data[field][i]);
                                        }
                                    }
                                },
                                defaultHandlerError: function (resp) {
                                     console.log(resp)
                                    this.events.fire('errorPopap', [this.options.uploader.getMsg(resp)]);
                                }
                            },
                            filebrowser: {
                                ajax: {
                                    url: window.location.origin + '/api/method/uploadfile'
                                }
                            }
                        });
                        editor.setEditorValue('<p>start</p>')

                        editor.value = frm.doc[check_doc.field] || " ";
                        ele.addEventListener('change', function() {
                             
                            frm.set_value(check_doc.field, this.value);
                        });
                        $('.jodit_toolbar_btn-fullsize').hide();
                    }
                }
            })
        }
    });
})

function get_doctypes_list() {
    return [
        { 'doctype': 'Web Page', 'field': 'main_section', 'content': 'Section' },
        { 'doctype': 'Newsletter', 'field': 'message', 'title': 'Message' },
        { 'doctype': 'Product', 'field': 'full_description', 'title': 'Description' },
        { 'doctype': 'Product', 'field': 'helpful_hints_and_cooking_tricks', 'title': 'Helpful Hints and Cooking Tricks' },
        { 'doctype': 'Pages', 'field': 'content','title': 'Content' }
    ]
}

var help_template = '';
var displayed1 = 0;
var displayed = 0;
frappe.ui.form.Layout.prototype.refresh_sections = function() {
    var cnt = 0;
    if(!has_common(frappe.user_roles, ['System Manager']))
            cur_page.page.page.hide_menu();
    this.wrapper.find(".form-section:not(.hide-control)").each(function() {
        var $this = $(this).removeClass("empty-section")
            .removeClass("visible-section")
            .removeClass("shaded-section");
        if (!$this.find(".frappe-control:not(.hide-control)").length &&
            !$this.hasClass('form-dashboard')) {
            var dashhide = $(this).find('.form-dashboard.hidden')
            if (dashhide.length > 0) {
                $this.addClass("empty-section");
            }
        } else {
            $this.addClass("visible-section");

            if (cnt % 2) {
                $this.addClass("shaded-section");
            }
            cnt++;
        }
    });
    var module_name = ''
   
    if(cur_list){
        var docs = cur_list.doctype
        module_name = cur_list.meta.module
        let help_articles_info = frappe.boot.sysdefaults[module_name];
        let active_domains = frappe.boot.active_domains;
        if(help_articles_info){
            $.each(help_articles_info[docs], function(i, v) {
                $.each(active_domains, function(t, u) {
                    if(u==v.domain_name || !v.domain_name){
                        if(v.doctype==docs && (v.category=="List" || v.category=="List & Detail")){
                            if(v.published==1 && displayed == 0){
                                displayed = 1
                                var btn_html = '<button class="btn btn-secondary btn-default btn-sm hidden-xs" data-doctype="'+cur_list.page_name+'" data-label="Help" onclick="show_help_popup($(this))" style="background: transparent;"><span class="fa fa-question-circle" aria-hidden="true" style="font-size: 16px;" title="Help"></span></button>'
                                    help_template = v.content
                                    $('div[data-page-route="'+cur_list.page_name+'"] .page-head .page-actions').prepend(btn_html);
                                    var html = '<div class="modal help_modal fade" style="overflow: auto;display:none;margin-top: 25px;" tabindex="-1" aria-hidden="false"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button><div class="flex justify-between"><div class="fill-width flex"><span class="indicator hidden"></span><h4 class="modal-title" style="font-weight: bold;">'+v.title+'</h4></div><div></div></div></div><div class="modal-body ui-front" style="text-align: justify;">'
                                    html += v.content
                                    html+= '</div></div></div></div>'
                                    $('div[data-page-route="'+cur_list.page_name+'"] .page-head .page-actions').append(html);
                            }
                        }
                    }
                })
            })
        }
    }
    if(cur_frm){
        
        var docs = cur_frm.doc.doctype
        let active_domains = frappe.boot.active_domains;
        module_name = cur_frm.meta.module
        let help_articles_info = frappe.boot.sysdefaults[module_name];
        if(help_articles_info){
            $.each(help_articles_info[docs], function(i, v) {
                $.each(active_domains, function(t, u) {
                    if(u==v.domain_name || !v.domain_name){
                    if(v.doctype==docs && (v.category=="Detail" || v.category=="List & Detail")){
                        if(v.published==1 && displayed1 == 0){
                            displayed1 = 1
                            var btn_html = '<button class="btn btn-secondary btn-default btn-sm hidden-xs" data-doctype="Form/'+cur_frm.doc.doctype+'" data-label="Help" onclick="show_help_popup($(this))" style="background: transparent;"><span class="fa fa-question-circle" aria-hidden="true" style="font-size: 16px;" title="Help"></span></button>'
                                help_template = v.content
                                $('div[data-page-route="Form/'+cur_frm.doc.doctype+'"] .page-head .page-actions').prepend(btn_html);
                                var html = '<div class="modal help_modal fade" style="overflow: auto;display:none;margin-top: 25px;" tabindex="-1" aria-hidden="false"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button><div class="flex justify-between"><div class="fill-width flex"><span class="indicator hidden"></span><h4 class="modal-title" style="font-weight: bold;">'+v.title+'</h4></div><div></div></div></div><div class="modal-body ui-front" style="text-align: justify;">'
                                html += v.content
                                html+= '</div></div></div></div>'
                                $('div[data-page-route="Form/'+cur_frm.doc.doctype+'"] .page-head .page-actions').append(html);
                        }
                    }
                }
            })
            })
        }
    }
    
}

function goto_driver(e) {
    var name = $(e).attr('data-id');
    var url = "/desk#Form/Drivers/" + name
    window.location.href = window.location.origin + url;
}

function show_help_popup(e){
    var name = $(e).attr('data-doctype');
    $('div[data-page-route="'+name+'"] .help_modal').modal('show');
}

function selected_discount_multiselect_lists(e) {
    var actual_value = $(e).attr('id');
    var idx = $(e).attr('data-idx');
    var val_label = $(e).attr('data-label');
    var val_product = $(e).attr('data-product');
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var child_tab_link = $(e).attr('data-child_link');
    var row_id = cur_frm.selected_doc.name
    var cls = $(e).parent().parent().parent().parent().parent().attr('class');
    var field = $('.' + cls + ' #myInput').attr('data-field');
    var linkedfield = $('.' + cls + ' #myInput').attr('data-linkfield');
    var values = $(e).parent().parent().find('a').text();
    
    if ($(e).is(':checked')) {   
                var cur_row = frappe.get_doc(doctype_name, cur_frm.selected_doc); 
                if (!cur_row[field] || cur_row[field] == undefined || cur_row[field] == "") {
                    frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, '[]');
                    var row_val = frappe.model.get_value(doctype_name, cur_frm.selected_doc.name, field);

                    let arr = JSON.parse(row_val);
                  
                    if (actual_value) {
                        arr.push({"idx": parseInt(idx), "name":actual_value, "label": val_label, "product": val_product});
                    }
                   
                    frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, JSON.stringify(arr));
                   
                    $('.' + cls + ' #myInput').val('');
                } else {
                    let arr = JSON.parse(cur_row[field]);
                   
                    if (actual_value) {
                       arr.push({"idx":parseInt(idx), "name":actual_value, "label": val_label, "product": val_product});
                    }
                  
                    frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, JSON.stringify(arr));
                    $('.' + cls + ' #myInput').val('');
                }
            
    } else {
        
                var cur_row = frappe.get_doc(doctype_name, cur_frm.selected_doc);
               
                if (!cur_row[field] || cur_row[field] == undefined || cur_row[field] == "") {
                    frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, '[]')
                } else {
                    
                     let arr;
                    if (typeof(cur_row[field]) == "string") {
                        arr = JSON.parse(cur_row[field]);
                    } else {
                        arr = cur_row[field];
                    }
                    var data = {"idx": parseInt(idx), "name":actual_value, "label": val_label, "product": val_product}
                    // var index = arr.indexOf(values);
                    var index = arr.indexOf(data);
                    if (index >= -1) {
                        arr.splice(index, 1);
                    }
                   
                    frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, JSON.stringify(arr))
                }
            
    }

    if (parseInt(is_child) == 1) {
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #myInput').attr('data-id', $(e).attr('id'))
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets').css('display', 'none')
    } else {
        $('.' + cls + ' #myInput').attr('data-id', $(e).attr('id'))

    }
}


    function crop_default_uploaderimage(field_name){
       
        let selected_image_list = [];
        let random = Math.random() * 100;
        localStorage.setItem("upload_tab", "");
        localStorage.setItem('randomuppy', ' ');
        let imgDialog;
        doctype=cur_frm.doc.doctype
        link_doctype = ""
        link_name = ""
        parentfield=""
        child_docname=""
        let randomuppy = Math.random() * 100
        localStorage.setItem('randomuppy', parseInt(randomuppy))
        let template = "<div id='drag-drop-area" + parseInt(randomuppy) + "'><div class='loader'>Loading.....</div></div>";
        imgDialog = cur_dialog
        imgDialog.disable_primary_action()
        imgDialog.$wrapper.find('.file-uploader').html(template)
        imgDialog.show();
                $(imgDialog.$wrapper).find('.loader').remove()
                upload_image(parseInt(randomuppy), link_doctype, link_name, parentfield, doctype, child_docname, field_name)
        imgDialog.get_close_btn().on('click', () => {
            this.on_close && this.on_close(this.item);
        });
        $(imgDialog.$wrapper).find('.img-close').on('click', function () {
            let me = this;
            cur_frm.imgid = $(me).attr("data-id");
            frappe.confirm(__("Do you want to delete the image?"), () => {
                let url = 'go1_commerce.go1_commerce.api.delete_current_img';
                if (child_docname)
                    url = 'go1_commerce.go1_commerce.api.delete_current_attribute_img';
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
                    if (child_docname) {
                        items_list.push({
                            "name": childname,
                            "parent": $(this).attr('data-parent'),
                            "title": image_name,
                            "is_primary": is_primary,
                            "idx": count
                        })
                    } else {
                        if (image_name) {
                            frappe.model.set_value('Product Image', childname, 'idx', count)
                            frappe.model.set_value('Product Image', childname, 'image_name', image_name)
                            frappe.model.set_value('Product Image', childname, 'is_primary', is_primary)
                        } else {
                            frappe.throw("Please mention image name.")
                        }
                    }
                })
                if (child_docname) {
                    frappe.call({
                        method: 'go1_commerce.go1_commerce.api.update_attribute_option_images',
                        args: {
                            dn: child_docname,
                            docs: JSON.stringify(items_list)
                        },
                        callback: function (r) {
                            imgDialog.hide();
                            EditAttributeOption(child_docname);
                        }
                    })
                } else {
                    cur_frm.save();
                    cur_frm.reload_doc();
                    imgDialog.hide();
                }
            } else {
                frappe.throw('Please add images to edit them')
            }
        })
        $(imgDialog.$wrapper).find('.img-edit').click(function () {
            let me = this;
            let imgid = $(me).attr("data-id");
            let check_data = frm.doc.product_images.find(obj => obj.name == imgid);
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
    
      function upload_image(random, link_doctype, link_name, parentfield, image_doctype, child_docname, field_name){
          $.getScript('https://transloadit.edgly.net/releases/uppy/v1.18.0/uppy.min.js', function () {
        var uppy = Uppy.Core({
                restrictions:{
                    maxFileSize: 1000000,
                    allowedFileTypes:['image/*','.jpg','.png','.jpeg','.gif','.svg']
                }
            })
            .use(Uppy.Dashboard, {
                inline: true,
                target: '#drag-drop-area' + random,
                disablePageScrollWhenModalOpen: true,
                disableInformer: false,
                height: 450,
                hideRetryButton: false,
                animateOpenClose: true,
                closeModalOnClickOutside: false,
                replaceTargetContent:false,
                showProgressDetails:true,
                hideProgressAfterFinish:true,
                disableStatusBar:false,
                theme:"light",
               
                proudlyDisplayPoweredByUppy:false,
                fileManagerSelectionType: 'files',
                note: 'Images only, up to 1 MB',
                locale:{
                    strings:{
                        dropPaste: 'Drop files here or %{browse}',
                    }                    
                },
                 metaFields: [
                { id: 'name', name: 'Name', placeholder: 'File Name' },
               
              ]                
            })
       
        uppy.use(Uppy.ImageEditor, {
          target: Uppy.Dashboard,
          quality: 0.8,
          cropperOptions: {
            viewMode: 1,
            background: false,
            autoCropArea: 1,
            responsive: true,
            croppedCanvasOptions: {},
          },
          actions: {
            revert: true,
            rotate: true,
            granularRotate: true,
            flip: true,
            zoomIn: true,
            zoomOut: true,
            cropSquare: true,
            cropWidescreen: true,
            cropWidescreenVertical: true,
          },
        })
        var filelists = [];
        uppy.on('upload', (data) => {
         
            $("<h4 class='msg'>Uploading. Please wait.......</h4>").appendTo(".uppy-Informer");
            $('.uppy-Dashboard-progressindicators').find('.uppy-Informer p').css("display", "none");

            let files_count=uppy.getFiles().length;
            let count=0;
            let all_files=uppy.getFiles();
            $.each(all_files, function (i, check_deleted) {
            
                    $('.uppy-Dashboard-progressindicators').find('.uppy-Informer p').css("display", "none");
                    var reader = new FileReader();
                  
                    let date = new Date();
                    let datetime = date.toLocaleString().replace(/ /g, '');
                    let cur_time = datetime.replace(/\//g, '-');
                    let filename = check_deleted.name.split('.' + check_deleted.extension)[0] + '-' + cur_time + '.' + check_deleted.extension;
                    
                    
                    reader.readAsDataURL(check_deleted.data);
                    reader.onload = function (e) {
                       
                        $('.uppy-Dashboard-progressindicators').find('.uppy-Informer p').css("display", "none");
                        var upload_doc = localStorage.getItem("upload_tab");
                        frappe.call({
                            method: 'uploadfile',
                            args: {
                                from_form: 1,
                                doctype: cur_frm.doctype,
                                docname: cur_frm.docname,
                                is_private: 0,
                                filename: filename,
                                file_url: '',
                                docfield: field_name,
                                file_size: check_deleted.size,
                                filedata: e.target.result,
                                upload_doc: upload_doc
                            },
                            async: false,
                            callback: function (r) {
                               cur_frm.set_value(field_name, r.message.file_url);
                               cur_dialog.hide();
                               setTimeout(function() {
                                   cur_frm.save();
                               },1000);
                            }
                        })
                    };
                    
                    uppy.reset();
              
            });
        })
        uppy.upload().then((result) => {
          console.info('Successful uploads:', result.successful);
          
        })
        uppy.on('file-added', (file) => {            
            $('.uppy-DashboardContent-addMore').css('display','none');
        })
        $(document).ready(function () {
            $('.uppy-DashboardAddFiles-info').find('.uppy-Dashboard-poweredBy').css("display", "none");
            $('.uppy-Dashboard-progressindicators').find('.uppy-StatusBar-actions button').attr("id", "uploadbtn");
            $('.uppy-Dashboard-progressindicators').find('.uppy-Informer p').css("display", "none");
            $('.uppy-DashboardAddFiles').on('drop',function(e){
                $("input[type=file]").prop("files", e.originalEvent.dataTransfer.files);
                $("input[type=file]").trigger('change')
                $('.uppy-DashboardContent-addMore').css('display','none');
            })
            $('.uppy-DashboardContent-addMore').css('display','none');
        });
        $('input[type=file]').change(function () {
            filelists.push($(this))
            var input = $(this);
        });
    })
      }



function selected_warranty(e) {
    var actual_value = $(e).attr('id');
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var child_tab_link = $(e).attr('data-child_link');
    var row_id = cur_frm.selected_doc.name
    var cls = $(e).parent().parent().parent().parent().parent().attr('class');
    var field = $('.' + cls + ' #myInput').attr('data-field');
    var linkedfield = $('.' + cls + ' #myInput').attr('data-linkfield');
    var action_type = $(e).attr("btn-action")
    console.log(actual_value)
    console.log($(e).find(".btn-success"))
    console.log($(e).find(".btn-danger"))
    if(actual_value){
        if(action_type && action_type == "Remove"){
            cur_frm.set_value("warranty_name", "");
            refresh_field("warranty_name")
            $(e).removeClass("btn-danger");
            $(e).addClass("btn-success");
            $(e).text("Remove");
        }
        else{
            cur_frm.set_value("warranty_name", actual_value);
            refresh_field("warranty_name")
            $(e).removeClass("btn-success");
            $(e).addClass("btn-danger");
            $(e).text("Remove");
        }
        cur_dialog.hide();
    }
}
function selected_replacement(e) {
    var actual_value = $(e).attr('id');
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var child_tab_link = $(e).attr('data-child_link');
    var row_id = cur_frm.selected_doc.name
    var cls = $(e).parent().parent().parent().parent().parent().attr('class');
    var field = $('.' + cls + ' #myInput').attr('data-field');
    var linkedfield = $('.' + cls + ' #myInput').attr('data-linkfield');
    var action_type = $(e).attr("btn-action")
    console.log(actual_value)
    console.log($(e).find(".btn-success"))
    console.log($(e).find(".btn-danger"))
    if(actual_value){
        if(action_type && action_type == "Remove"){
            cur_frm.set_value("replacement_name", "");
            refresh_field("replacement_name")
            $(e).removeClass("btn-danger");
            $(e).addClass("btn-success");
            $(e).text("Remove");
        }
        else{
            cur_frm.set_value("replacement_name", actual_value);
            refresh_field("replacement_name")
            $(e).removeClass("btn-success");
            $(e).addClass("btn-danger");
            $(e).text("Remove");
        }
        cur_dialog.hide();
    }
}


function load_more_warranty_items(e) {
    console.log("eee--")
    var doctype_name = $(e).parent().parent().find("#myInput").attr('data-doctype');
    var is_child = $(e).parent().parent().find("#myInput").attr('data-child');
    var row_id = cur_frm.selected_doc.name
    var cls = $(e).parent().parent().find("#myInput").attr('data-class');
    var field = $(e).parent().parent().find("#myInput").attr('data-field');
    var linkedfield = $(e).parent().parent().find("#myInput").attr('data-linkfield');
    var link_field = $(e).parent().parent().find("#myInput").attr('data-link_field');
    var reference_doc = $(e).parent().parent().find("#myInput").attr('data-reference_doc');
    var business = unescape($(e).parent().parent().find("#myInput").attr('data-business'));
    var reference_fields = unescape($(e).parent().parent().find("#myInput").attr('data-reference_fields'));
    var search_fields = $(e).parent().parent().find("#myInput").attr('data-search_fields');
    var reference_method = $(e).parent().parent().find("#myInput").attr('data-reference_method');
    var child_tab_link = $(e).parent().parent().find("#myInput").attr('data-child_link');
    var tab_html_field = $(e).parent().parent().find("#myInput").attr('data-tab_html_field');
    var hasimage = $(e).parent().parent().find("#myInput").attr('data-hasimage');
    var imagefield = $(e).parent().parent().find("#myInput").attr('data-imagefield');
    var input, ul;
    var txtValue = $(e).parent().parent().find("#myInput").val();
    cur_frm.page_no = cur_frm.page_no+1
    build_warranty_load_list(row_id, cls, field, linkedfield, doctype_name, is_child, reference_doc, reference_fields, reference_method, child_tab_link, search_fields, tab_html_field, hasimage,imagefield, link_field,business, txtValue);
    if (parseInt(is_child) == 1) {
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets').css('display', 'block');
    } else {
        $('.' + cls + ' #assets').css('display', 'block');
    }
}


function build_warranty_load_list(selected, cls, field, linkedfield, doctype_name, is_child, reference_doc, reference_fields, reference_method, child_tab_link, search_fields, tab_html_field,hasimage, imagefield, link_field, business, txtValue) {
    var url = '/api/method/' + reference_method
    var filters=""
    if(reference_doc=="Product Attribute"){
        filters = JSON.stringify(cur_frm.doc.product_categories)
    }
    $.ajax({
        type: 'POST',
        Accept: 'application/json',
        ContentType: 'application/json;charset=utf-8',
        url: window.location.origin + url,
        data: {
            "reference_doc": reference_doc,
            "reference_fields": reference_fields,
            "filters": filters,
             "page_no": cur_frm.page_no,
            "business": business,
             "search_txt": txtValue,
            "search_field": search_fields
        },
        dataType: "json",
        async: false,
        headers: {
            'X-Frappe-CSRF-Token': frappe.csrf_token
        },
        success: function(r) {
            if(cur_dialog){
                cur_dialog.fields_dict[tab_html_field].$wrapper.find(`button#more__btn`).remove()
            }
            var list_name = r.message.list_name;
            var drp_html = ''
            var k = 0
            var morebtn = ""
            if(list_name.length>20){
                morebtn = '<button id="more__btn" class="btn btn-default btn-xs" style="float:right;background-color: #ccc;margin: 8px;" data-fieldtype="Button" data-fieldname="more_btn" onclick="load_more_warranty_items($(this))">More</button>'
            }
            $.each(list_name, function (i, v) {
               console.log(list_name)
                if (v[link_name]) {
                    k += 1
                    var args = {
                        txt: "",
                        searchfield: "name",
                        filters: {
                            "name": v[link_name]
                        }
                    };
                    let arr =cur_frm.doc.warranty_name;
                    let business_div = '';
                    if(v.business && has_common(frappe.user_roles, ['Admin', 'System Manager']))
                        business_div = '(' + (v.business || '') + ')';
                    console.log(v[link_name])
                    console.log(arr)
                     if (v[link_name] == arr) {
                       
                        drp_html += '<li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;"><a style="display: none;"><strong>' + v[link_name] + '</strong></a><label class="switch" style="float:right; width: 60px; margin:0px; cursor:pointer;"><button class="btn btn-xs btn-danger" name="vehicle1" value="0" id="' + v[link_name] + '" data-doctype="' + doctype + '" data-child="' + is_child + '" data-reference_doc="' + reference_doc + '" data-reference_fields="' + reference_fields + '" data-search_fields="' + search_fields + '"  data-business="' + business + '" data-child_link="' + child_tab_link + '" data-tab_html_field="'+tab_html_field+'" btn-action="Remove" onclick="selected_warranty($(this))">Remove</button></label>';
                        drp_html +='<table style="width: 90%;"><tr><td style="font-size:14px;width: 12%;">'+v["title"]+'</td><td style="font-size:14px;width: 20%;">'+v["description"]+'</td></tr></table>'
                       
                        drp_html += '</li>'
                    } else {
                        
                        drp_html += '<li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;"><a style="display: none;"><strong>' + v[link_name] + '</strong></a><label class="switch" style="float:right;width: 60px; margin:0px; cursor:pointer;"><button class="btn btn-xs btn-success" name="vehicle1" value="0" id="' + v[link_name] + '" data-doctype="' + doctype + '" data-child="' + is_child + '" data-reference_doc="' + reference_doc + '" data-reference_fields="' + reference_fields + '" data-search_fields="' + search_fields + '"  data-business="' + business + '" data-child_link="' + child_tab_link + '" data-tab_html_field="'+tab_html_field+'" btn-action="add" onclick="selected_warranty($(this))">Select</button></label>';
                        
                        drp_html +='<table style="width: 90%;"><tr><td style="font-size:14px;width: 12%;">'+v["title"]+'</td><td style="font-size:14px;width: 20%;">'+v["description"]+'</td></tr></table>'
                        drp_html += '</li>'
                       
                    }
                   
                } else {
                    drp_html += '<li></li>';
                }
            })
            drp_html += morebtn
           if(cur_dialog){
            cur_dialog.fields_dict[tab_html_field].$wrapper.find(`div.${cls} table ul#assets`).append(drp_html);
            cur_dialog.get_field(tab_html_field).refresh();
           }
        }
    })

}



function select_return_list(e){
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var row_id = cur_frm.selected_doc.name
    var cls = $(e).attr('data-class');
    var field = $(e).attr('data-field');
    var linkedfield = $(e).attr('data-linkfield');
    var reference_doc = $(e).attr('data-reference_doc');
    var business = unescape($(e).attr('data-business'));
    var reference_fields = unescape($(e).attr('data-reference_fields'));
    var search_fields = $(e).attr('data-search_fields');
    var reference_method = $(e).attr('data-reference_method');
    var child_tab_link = $(e).attr('data-child_link');
    var tab_html_field = $(e).attr('data-tab_html_field');
    var input, ul, txtValue;
    var url = '/api/method/' + reference_method
    $.ajax({
        type: 'POST',
        Accept: 'application/json',
        ContentType: 'application/json;charset=utf-8',
        url: window.location.origin + url,
        data: {
            "reference_doc": reference_doc,
            "reference_fields": reference_fields,
            "business": business
        },
        dataType: "json",
        async: false,
        headers: {
            'X-Frappe-CSRF-Token': frappe.csrf_token
        },
        success: function(r) {
           
            var drp_html = '';
            var item = r.message.list_name;
           
            if (parseInt(is_child) == 1) {
                $('div[data-name="' + selected + '"]').find('.' + cls + ' #assets').empty();
            } else {
                $('.' + cls + ' #assets').empty();
            }
            if (item.length > 0) {
                var k = 0
                $.each(item, function (i, v) {
                       
                        if (v[linkedfield]) {

                            k += 1
                            var args = {
                                txt: "",
                                searchfield: "name",
                                filters: {
                                    "name": v[linkedfield]
                                }
                            };
                            let arr =cur_frm.doc.return_policy;
                            let business_div = '';
                            if(v.business && has_common(frappe.user_roles, ['Admin', 'System Manager']))
                                business_div = '(' + (v.business || '') + ')';
                             if (v[linkedfield] == arr) {
                               
                                drp_html += '<li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;"><a style="display: none;"><strong>' + v[linkedfield] + '</strong></a><label class="switch" style="float:right; width: 60px; margin:0px; cursor:pointer;"><button class="btn btn-xs btn-danger" name="vehicle1" value="0" id="' + v[linkedfield] + '" data-doctype="' + doctype_name+ '" data-child="' + is_child + '" data-reference_doc="' + reference_doc + '" data-reference_fields="' + reference_fields + '" data-search_fields="' + search_fields + '"  data-business="' + business + '" data-child_link="' + child_tab_link + '" data-tab_html_field="'+tab_html_field+'" btn-action="Remove" onclick="selected_returnpolicy($(this))">Remove</button></label>';
                                drp_html +='<table style="width: 90%;"><tr><td style="width: 12%;">'+v["heading"]+'</td><td style="width: 20%;">'+v["description"]+'</td></tr></table>'
                               
                                drp_html += '</li>'
                            } else {
                                
                                drp_html += '<li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;"><a style="display: none;"><strong>' + v[linkedfield] + '</strong></a><label class="switch" style="float:right;width: 60px; margin:0px; cursor:pointer;"><button class="btn btn-xs btn-success" name="vehicle1" value="0" id="' + v[linkedfield] + '" data-doctype="' + doctype_name+ '" data-child="' + is_child + '" data-reference_doc="' + reference_doc + '" data-reference_fields="' + reference_fields + '" data-search_fields="' + search_fields + '"  data-business="' + business + '" data-child_link="' + child_tab_link + '" data-tab_html_field="'+tab_html_field+'" btn-action="add" onclick="selected_returnpolicy($(this))">Select</button></label>';
                                
                                drp_html +='<table style="width: 90%;"><tr><td style="width: 12%;">'+v["heading"]+'</td><td style="width: 20%;">'+v["description"]+'</td></tr></table>'
                                drp_html += '</li>'
                               
                            }
                           
                        } else {
                            drp_html += '<li></li>';
                        }
                    })
                   
            } else {
                drp_html += '<li></li>';
            }

            if (parseInt(is_child) == 1) {
                $('div[data-name="' + selected + '"]').find('.' + cls + ' #assets').html(drp_html);
            } else {
                $('.' + cls + ' #assets').html(drp_html)
            }

        }
    })
}

function selected_returnpolicy(e) {
   
    var actual_value = $(e).attr('id');
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var child_tab_link = $(e).attr('data-child_link');
    var row_id = cur_frm.selected_doc.name
    var cls = $(e).parent().parent().parent().parent().parent().attr('class');
    var field = $('.' + cls + ' #myInput').attr('data-field');
    var linkedfield = $('.' + cls + ' #myInput').attr('data-linkfield');
    var action_type = $(e).attr("btn-action")

    console.log(actual_value)
    if(actual_value){
        console.log(action_type)
        if(action_type && action_type == "Remove"){
            cur_frm.set_value("return_policy", "");
            refresh_field("return_policy")
            $(e).removeClass("btn-danger");
            $(e).addClass("btn-success");
            $(e).text("Remove");
        }
        else{
            cur_frm.set_value("return_policy", actual_value);
            refresh_field("return_policy")
            $(e).removeClass("btn-success");
            $(e).addClass("btn-danger");
            $(e).text("Remove");
        }
        cur_dialog.hide();
    }
}

function show_product_gallery(e) {
    var me = this;
    this.gallery = new frappe.views.GalleryView({
        doctype: this.doctype,
        items: cur_frm.doc.product_images,
        wrapper:cur_frm.fields_dict.img_html.wrapper,
        images_map: cur_frm.doc.product_images
    });
    var name = $(this).data().name;
    name = decodeURIComponent(e);
    me.gallery.show(name);
    return false;
}


frappe.views.GalleryView = Class.extend({
    init: function(opts) {
        $.extend(this, opts);
        var me = this;

        this.lib_ready = this.load_lib();
        this.lib_ready.then(function() {
            me.prepare();
        });
    },
    prepare: function() {
        this.pswp_root = $("body > .pswp");
        if (this.pswp_root.length === 0) {
            var pswp = frappe.render_template("photoswipe_dom");
            this.pswp_root = $(pswp).appendTo("body");
        }
    },
    prepare_pswp_items: function(_items, _images_map) {
        var me = this;

        if (_items) {
            this.items = this.items.concat(_items);
            this.images_map = _images_map;
        }

        return new Promise(resolve => {
            const items = this.items.map(function(i) {
                const query = 'img[data-name="' + i.name + '"]';
                let el = $(me.wrapper).find(query).get(0);

                let width, height;
                if (el) {
                    width = el.naturalWidth;
                    height = el.naturalHeight;
                }

                if (!el) {
                    el = $(me.wrapper)
                        .find('.image-field[data-name="' + i.name + '"]')
                        .get(0);
                    width = el.getBoundingClientRect().width;
                    height = el.getBoundingClientRect().height;
                }

                return {
                    src: i.product_image,
                    msrc: i._image_url,
                    name: i.name,
                    w: width,
                    h: height,
                    el: el
                };
            });
            this.pswp_items = items;
            resolve();
        });
    },
    show: function(docname) {
        this.lib_ready
            .then(() => this.prepare_pswp_items())
            .then(() => this._show(docname));
    },
    _show: function(docname) {
        const me = this;
        const items = this.pswp_items;
        const item_index = items.findIndex(item => item.name === docname);

        var options = {
            index: item_index,
            getThumbBoundsFn: function(index) {
                const query = 'img[data-name="' + items.name + '"]';
                let thumbnail = $(me.wrapper).find(query).get(0);

                if (!thumbnail) {
                    return;
                }

                var pageYScroll =
                        window.pageYOffset ||
                        document.documentElement.scrollTop,
                    rect = thumbnail.getBoundingClientRect();

                return {
                    x: rect.left,
                    y: rect.top + pageYScroll,
                    w: rect.width
                };
            },
            history: false,
            shareEl: false,
            showHideOpacity: true
        };

        this.pswp = new PhotoSwipe(
            this.pswp_root.get(0),
            PhotoSwipeUI_Default,
            items,
            options
        );
        this.browse_images();
        this.pswp.init();
    },
    
    browse_images: function() {
        const $more_items = this.pswp_root.find(".pswp__more-items");
        console.log("$more_items",$more_items)
        const images_map = this.images_map;
        let last_hide_timeout = null;

        this.pswp.listen("afterChange", function() {
            const images = images_map[this.currItem.image__video];
            if (!images || images.length === 1) {
                $more_items.html("");
                return;
            }
            hide_more_items_after_2s();
            const html = images.map(img_html).join("");
            $more_items.html(html);
         
        });

        this.pswp.listen("beforeChange", hide_more_items);
        this.pswp.listen("initialZoomOut", hide_more_items);
        this.pswp.listen("destroy", () => {
            $(document).off("mousemove", hide_more_items_after_2s);
        });

        $more_items.on("click", ".pswp__more-item", e => {
            const img_el = e.target;
            const index = this.pswp.items.findIndex(
                i => i.name === this.pswp.currItem.name
            );

            this.pswp.goTo(index);
            this.pswp.items.splice(index, 1, {
                src: img_el.src,
                w: img_el.naturalWidth,
                h: img_el.naturalHeight,
                name: this.pswp.currItem.name
            });
            this.pswp.invalidateCurrItems();
            this.pswp.updateSize(true);
        });

        $(document).on("mousemove", hide_more_items_after_2s);

        function hide_more_items_after_2s() {
            clearTimeout(last_hide_timeout);
            show_more_items();
            last_hide_timeout = setTimeout(hide_more_items, 2000);
        }

        function show_more_items() {
            $more_items.show();
        }

        function hide_more_items() {
            $more_items.hide();
        }

        function img_html(src) {
            console.log("ist calling")
            return `<div class="pswp__more-item">
                <img src="${src}">
            </div>`;
        }
    }, 
    load_lib: function() {
        return new Promise(resolve => {
            var asset_dir = "assets/frappe/js/lib/photoswipe/";
            frappe.require(
                [
                    asset_dir + "photoswipe.css",
                    asset_dir + "default-skin.css",
                    asset_dir + "photoswipe.js",
                    asset_dir + "photoswipe-ui-default.js"
                ],
                resolve
            );
        });
    }
});