//get multiselect values
// input field onfocuse
function load_more_items(e) {

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
    build_load_list(row_id, cls, field, linkedfield, doctype_name, is_child, reference_doc, reference_fields, reference_method, child_tab_link, search_fields, tab_html_field, hasimage,imagefield, link_field,business, txtValue);
    if (parseInt(is_child) == 1) {
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets').css('display', 'block');
    } else {
        $('.' + cls + ' #assets').css('display', 'block');
    }


}
function build_load_list(selected, cls, field, linkedfield, doctype_name, is_child, reference_doc, reference_fields, reference_method, child_tab_link, search_fields, tab_html_field,hasimage, imagefield, link_field, business, txtValue) {
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
           
            var drp_html = '';
            var item = r.message.list_name;
            if (item.length > 0) {
                $('.' + cls + ' #assets').find('button[data-fieldname="more_btn"]').remove();
                var k = 0
                $.each(item, function(i, v) {
                    if (v[linkedfield]) {
                        //is child table
                        let business_div = '';
                        if(v.business && has_common(frappe.user_roles, ['Admin', 'System Manager']))
                            business_div = '(' + (v.business || '') + ')';
                        let arr;
                        if (parseInt(is_child) == 1) {
                            var cur_row = frappe.get_doc(doctype_name, selected);
                            arr = JSON.parse(cur_row[field]);
                        }
                        //not child table
                        else {
                            // arr = JSON.parse(cur_frm.doc[field]);
                            arr = JSON.parse(cur_dialog.fields_dict[field].get_value());
                        }

                        if ($.inArray(v[linkedfield], arr) == -1) {
                            k += 1;
                            drp_html += '<li style="border-radius: 0px;display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;"><a style="display: none;"><strong>' + v[linkedfield] + '</strong></a><label class="switch" style="float:right; margin:0px; cursor:pointer;"><input type="checkbox" class="popupCheckBox" name="vehicle1" value="0" id="' + v[linkedfield] + '" data-doctype="' + doctype_name + '" data-child="' + is_child + '" data-child_link="' + child_tab_link + '" onclick="selected_multiselect_lists($(this))"><span class=" slider round"></span></label>';
                            if((hasimage==1 || hasimage=="1") && imagefield){
                                    var img_field = v[imagefield]
                                   
                                    if(!imagefield || !v[imagefield] || imagefield=="null" || v[imagefield]=="null" || v[imagefield]==null || v[imagefield]==undefined){
                                        img_field = "/assets/go1_commerce/images/no-image-60x50.png"
                                        
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
                            drp_html += '<li style="border-radius: 0px;display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;"><a style="display: none;"><strong>' + v[linkedfield] + '</strong></a><label class="switch" style="float:right; margin:0px; cursor:pointer;"><input type="checkbox" class="popupCheckBox" name="vehicle1" value="0" id="' + v[linkedfield] + '" data-doctype="' + doctype_name + '" data-child="' + is_child + '" data-child_link="' + child_tab_link + '" onclick="selected_multiselect_lists($(this))" checked><span class=" slider round"></span></label>';
                            if((hasimage==1 || hasimage=="1") && imagefield){
                                    var img_field = v[imagefield]
                                   
                                    if(!imagefield || !v[imagefield] || imagefield=="null" || v[imagefield]=="null" || v[imagefield]==null || v[imagefield]==undefined){
                                        img_field = "/assets/go1_commerce/images/no-image-60x50.png"
                                        
                                    }
                                    
                                    drp_html += '<img src="'+img_field+'" alt=""  style="float: left;width: 35px;padding: 5px;height: 35px;">';
                                }
                            drp_html += '<p style="font-size: 14px;">';
                            if (v[link_field]) {
                                // if (frappe.boot.active_domains.includes(frappe.boot.sysdefaults.domain_constants.restaurant)) {
                                //     drp_html += '' + v[link_field] + ' (' + v.name + ') '+ business_div +'</p></li>';
                                // } else {
                                    drp_html += '' + v[link_field] + ' ' + business_div + '</p></li>';
                                // }
                            } else {
                                // if (frappe.boot.active_domains.includes(frappe.boot.sysdefaults.domain_constants.restaurant)) {
                                //     drp_html += '' + v[search_fields] + ' (' + v.name + ') '+ business_div +'</p></li>';
                                // } else {
                                    drp_html += '' + v[search_fields] + ' ' + business_div + '</p></li>';
                                // }
                            }
                        }
                    }
                })
                var morebtn = ""
                morebtn = '<button class="btn btn-default btn-xs" style="float:right;background-color: #ccc;margin: 8px;" data-fieldtype="Button" data-fieldname="more_btn" onclick="load_more_items($(this))">Load more...</button>'
                drp_html += morebtn
            } else {
                drp_html += '<li></li>';
            }
           
            if (parseInt(is_child) == 1) {
                $('div[data-name="' + selected + '"]').find('.' + cls + ' #assets').append(drp_html);
            } else {
                $('.' + cls + ' #assets').append(drp_html)
            }

        }
    })

}
function get_multiselect_values_forpdt(cls, field, linkedfield, doctype_name, is_child, child_tab_link) {
    if (parseInt(is_child) == 1) {
        var cur_row = frappe.get_doc(doctype_name, cur_frm.selected_doc);
        if (!cur_row[field]) {
            frappe.model.set_value(doctype_name, cur_row.name, field, '[]')
        }
        cur_frm.fields_dict[child_tab_link].$wrapper.find('.' + cls + ' .control-input-wrapper').remove();
        if (typeof(cur_row[field]) == "string") {
            var arr = JSON.parse(cur_row[field]);
        } else {
            var arr = cur_row[field];
        }
        var added_html = '<div class="control-input-wrapper"><div class="control-input form-control table-multiselect" style="display: flex;align-items: center;flex-wrap: wrap;height: auto;padding: 10px;padding-bottom: 5px;border-top: 0px !important;">';
        if (arr) {
            $.each(arr, function(i, v) {
                added_html += '<div class="btn-group tb-selected-value" data-value="' + v.name + '" style="display: inline-block;margin-right: 5px;margin-bottom: 5px;">';
                added_html += '<span class="btn btn-default btn-xs btn-link-to-form" style="text-overflow: ellipsis;overflow: hidden;white-space: nowrap;max-width: 180px;">' + v.label + '</span>';
                added_html += '<button class="btn btn-default btn-xs btn-remove" id="' + v.name + '" data-label="' + v.label + '" onclick="remove_selected_forpdt($(this))" data-class="' + cls + '" data-doctype="' + doctype_name + '" data-child="' + is_child + '" data-child_link="' + child_tab_link + '">';
                added_html += '<i class="fa fa-remove text-muted"></i>';
                added_html += '</button></div>';
            })
        }

        added_html += '</div></div>';
        cur_frm.fields_dict[child_tab_link].$wrapper.find('.' + cls).append(added_html)
    } else {
        if (!cur_frm.doc[field]) {
            cur_frm.set_value(field, '[]')
        }
        $('.' + cls + ' .control-input-wrapper').remove();
        var added_html = '<div class="control-input-wrapper"><div class="control-input form-control table-multiselect" style="display: flex;align-items: center;flex-wrap: wrap;height: auto;padding: 10px;padding-bottom: 5px;border-top: 0px !important;">';
        let arr;
        if (typeof(cur_frm.doc[field]) == "string") {
            arr = JSON.parse(cur_frm.doc[field]);
        } else {
            arr = cur_frm.doc[field];
        }
        if (arr) {
            $.each(arr, function(i, v) {
                added_html += '<div class="btn-group tb-selected-value" data-value="' + v.name + '" style="display: inline-block;margin-right: 5px;margin-bottom: 5px;">';
                added_html += '<span class="btn btn-default btn-xs btn-link-to-form" style="text-overflow: ellipsis;overflow: hidden;white-space: nowrap;max-width: 180px;">' + v.label + '</span>';
                added_html += '<button class="btn btn-default btn-xs btn-remove" id="' + v.name + '" data-label="' + v.label + '" onclick="remove_selected_forpdt($(this))" data-class="' + cls + '" data-doctype="' + doctype_name + '" data-child="' + is_child + '" data-child_link="' + child_tab_link + '">';
                added_html += '<i class="fa fa-remove text-muted"></i>';
                added_html += '</button></div>';
            })
        }
        added_html += '</div></div>';
        $('.' + cls).append(added_html)
    }

}

function select_all_lists(e){
     console.log(e)
      var cls = $(e).parent().parent().parent().attr('class');
      console.log(cls)
      console.log($('.' + cls).find("ul#assets").find("input"))
      console.log($('.' + cls + ' #myInput'))
    if ($(e).is(':checked')) {
        console.log("---1---")
            let arr = [];
            $('.' + cls).find("ul#assets").find("input").each(function () {
            console.log($(this))
            $(this).prop("checked", true);
                if ($(this).attr("id")) {
                    arr.push($(this).attr("id"));
                }
        })
        cur_dialog.get_field("subarea_json").set_value(JSON.stringify(arr));
        cur_dialog.get_field("subarea_json").refresh();
           
    } else {
        $('.' + cls).find("ul#assets").find("input").each(function () {
            console.log($(this))
            $(this).prop("checked", false);
            cur_dialog.fields_dict["subarea_json"].set_value("[]");
        })
       
    }
}
function selected_multiselect_listlabel(e) {
    var ehtml =$(e).find("input")
    var actual_value = ehtml.attr('id');
     var link_doctype = ehtml.attr('data-reference_doc');
    var doctype_name = ehtml.attr('data-doctype');
    var is_child = ehtml.attr('data-child');
    var child_tab_link = ehtml.attr('data-child_link');
    var row_id = cur_frm.selected_doc.name
    var cls = ehtml.parent().parent().parent().parent().parent().attr('class');
    var field = $('.' + cls + ' #myInput').attr('data-field');
    var linkedfield = $('.' + cls + ' #myInput').attr('data-linkfield');
    var table_html = $('.' + cls + ' #myInput').attr('data-tab_html_field');
    if (ehtml.is(':checked')) {
        ehtml.find('input').prop("checked", false);
        if(link_doctype!="Sub Area"){
        afterSelectlist(ehtml.parent().parent().find('a').text(), cls, field, linkedfield, doctype_name, is_child, child_tab_link, actual_value)
            }
    } else {
       
        ehtml.find('input').prop("checked", true);
        if(link_doctype!="Sub Area"){
        afterDeselectlist(actual_value, cls, field, linkedfield, doctype_name, is_child, child_tab_link)
       }
       
        
    }

    if (parseInt(is_child) == 1) {
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #myInput').attr('data-id', ehtml.attr('id'))
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets').css('display', 'none')
    } else {
        $('.' + cls + ' #myInput').attr('data-id', ehtml.attr('id'))
        // $('.'+cls+' #assets').css('display','none')

    }

}
function selected_multiselect_lists(e) {
    console.log(e)
    var actual_value = $(e).attr('id');
    var doctype_name = $(e).attr('data-doctype');
    var is_child = $(e).attr('data-child');
    var child_tab_link = $(e).attr('data-child_link');
    var row_id = cur_frm.selected_doc.name
    var cls = $(e).parent().parent().parent().parent().parent().attr('class');
    var field = $('.' + cls + ' #myInput').attr('data-field');
    var linkedfield = $('.' + cls + ' #myInput').attr('data-linkfield');
    var table_html = $('.' + cls + ' #myInput').attr('data-tab_html_field');
    if ($(e).is(':checked')) {
        afterSelectlist($(e).parent().parent().find('a').text(), cls, field, linkedfield, doctype_name, is_child, child_tab_link, actual_value)
    } else {
        afterDeselectlist(actual_value, cls, field, linkedfield, doctype_name, is_child, child_tab_link)
        if(cur_dialog.fields_dict["area_html1"]){
        if (cur_dialog.fields_dict["area_html1"].$wrapper.find('input#selectAll')) {
            cur_dialog.fields_dict["area_html1"].$wrapper.find('input#selectAll').prop("checked", false);
        }}
    }

    if (parseInt(is_child) == 1) {
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #myInput').attr('data-id', $(e).attr('id'))
        $('div[data-name="' + row_id + '"]').find('.' + cls + ' #assets').css('display', 'none')
    } else {
        $('.' + cls + ' #myInput').attr('data-id', $(e).attr('id'))
        // $('.'+cls+' #assets').css('display','none')

    }

}

// input field onfocuse
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

function afterSelectlist(values, cls, field, linkedfield, doctype_name, is_child, child_tab_link, actual_value) {
    if (parseInt(is_child) == 1) {
        var cur_row = frappe.get_doc(doctype_name, cur_frm.selected_doc);
        if (!cur_row[field] || cur_row[field] == undefined || cur_row[field] == "") {
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, '[]');
            var row_val = frappe.model.get_value(doctype_name, cur_frm.selected_doc.name, field);

            let arr = JSON.parse(row_val);
            // if(values){
            //     arr.push(values);
            // }
            if (actual_value) {
                arr.push(actual_value);
            }
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, JSON.stringify(arr));
            $('.' + cls + ' #myInput').val('');
        } else {
            let arr = JSON.parse(cur_row[field]);
            // if(values){
            //     arr.push(values);
            // }
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
            // cur_dialog.fields_dict[field].set_value(JSON.stringify(arr));

            $('.' + cls + ' #myInput').val('');
        }
    }
    // setTimeout(function(){
    // get_multiselect_values(cls, field, linkedfield, doctype_name, is_child, child_tab_link)
    //  }, 500);

}

//after deselect

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

    // get_multiselect_values(cls, field, linkedfield, doctype_name, is_child, child_tab_link)
}
