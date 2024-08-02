frappe.provide("go1_commerce.go1_commerce");
var currency = frappe.boot.sysdefaults.currency;
var symbol = "";
frappe.call({
    method: 'frappe.client.get_value',
    args: {
        'doctype': "Currency",
        'filters': { 'name': frappe.boot.sysdefaults.currency },
        'fieldname': "symbol"
    },
    callback: function (r) {
        if (r.message) {
            symbol = r.message.symbol;
            
        }
    }
});

$(document).ready(function () {
});

function validateNumber(event) {
    this.value = this.value.replace(/[^0-9\.]/g, '');
};

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
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, JSON.stringify(arr));
            $('.' + cls + ' #myInput').val('');
            
            if (actual_value) {
                arr.push({"idx": parseInt(idx), "name":actual_value, "label": val_label, "product": val_product});
            }
        } else {
            let arr = JSON.parse(cur_row[field]);
            frappe.model.set_value(doctype_name, cur_frm.selected_doc.name, field, JSON.stringify(arr));
            $('.' + cls + ' #myInput').val('');

            if (actual_value) {
                arr.push({"idx":parseInt(idx), "name":actual_value, "label": val_label, "product": val_product});
            }
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

function pick_color(e){
    var option_value = $(e).attr("data-id");
    var option_name = $(e).attr("data-option-name");
    var index = $(e).attr("data-index");
    var product_title = $(e).attr("data-product_title");
    var parent_control_type = $(e).attr("data-parent-control-type");
    var display_order = $(e).attr("data-display_order");
    var is_pre_selected = $(e).attr("data-is_pre_selected");
    var attribute_color = $(e).attr("data-attribute_color");
    var disable = $(e).attr("data-disable");
    var variant_option = cur_frm.doc.attribute_options.filter( x =>  x.attribute == cur_frm.doc.product_attributes[index].product_attribute && x.attribute_id == cur_frm.doc.product_attributes[index].name);
    if (!variant_option){
             variant_option = []
           }
    if(parent_control_type=="Color Boxes" ){
        let dialog_fields =[]
        dialog_fields.push({fieldtype:'Section Break', label: __('')})
        dialog_fields.push({
            "fieldtype": "Color",
            "label": __("Color"),
            "description": "Color is applied based on 'Control Type(Color Boxes)' field.",
            "fieldname": "attribute_color",
            "default":attribute_color
        });
        const dialog = new frappe.ui.Dialog({
            title: __("Choose Color"),
            fields: dialog_fields,
            primary_action: function() {
                var args = dialog.get_values();
                if(args){
                    let optionindex = cur_frm.doc.attribute_options.findIndex((obj => obj.option_value == option_val && obj.attribute == cur_frm.doc.product_attributes[index].product_attribute && obj.attribute_id == cur_frm.doc.product_attributes[index].name));
                    cur_frm.doc.attribute_options[optionindex]["attribute_color"]=args.attribute_color
                    $(e).attr("data-attribute_color", args.attribute_color);
                    cur_frm.refresh_field("attribute_options");
                    dialog.hide()
                }
            }
        })
        dialog.show()
    }
}

 function edit_attribute_combination_details(e){
     const dialog = new frappe.ui.Dialog({
        title: __("PRODUCT ATTRIBUTE COMBINATION"),
        fields: [
            {fieldtype:'Section Break', label: __('')},
           {
                    fieldtype:'HTML',
                    fieldname:"attribute_html",
                    label: __('Attribute Html')
                }
        ],
        primary_action: function() {
            var args = dialog.get_values();
            
        },
        primary_action_label: __('Save')
    });
    dialog.show();
}

 function choose_display_types(e){
    var control = $(e).attr("data-control_type");
    var name = $(e).attr("data-name");
    var idx = $(e).attr("data-idx");

    var contol_types = ["Dropdown List", "Radio Button List", "Checkbox List", "Color Boxes", "Text Box", "Table", "Multi Line Text"];
    var defaulthtml ='<div class="row"><div class="col-md-6" style="border-right: 1px solid #e0e0e1;">'
    $(contol_types).each(function (k, v) {
        var checkedcls =''
        if(v==control){
            checkedcls="checked"
        }
        defaulthtml += '<label class="container"><span style="padding-left: 5px;font-weight: 400;">'+v+'</span>'
        defaulthtml +='<input type="radio" name="control_type" value="'+v+'" '+checkedcls+' style="float: left;"><span class="check"></span></label>'
    })
    defaulthtml += '</div><div class="col-md-6"><div id="controltype-img"></div></div></div>'
    const dialog = new frappe.ui.Dialog({
        title: __("Choose Display Type"),
        fields: [
            {fieldtype:'Section Break', label: __('')},
            {fieldtype:'HTML', fieldname:'controltype_html'},
        ],
        primary_action_label: __('Save'),
        primary_action: function() {
            var args = dialog.get_values();
            var index = cur_frm.attribute_items.findIndex(x => x.idx == idx);
            var val = cur_dialog.fields_dict["controltype_html"].$wrapper.find('input[name="control_type"]:checked').val();
            cur_frm.doc.product_attributes[index]["control_type"] = val
            $('#attributeWithOptions #productAttributeBody').find('tr[data-id="'+idx+'"]').find('.control_type_html a').text(val)
            $('#attributeWithOptions #productAttributeBody').find('tr[data-id="'+idx+'"]').find('.option_html a').attr("data-parent-control-type", val);
            cur_frm.refresh_field("product_attributes")
            cur_frm.dirty()
            cur_frm.save()
            dialog.hide()
        }
    })
    dialog.show();
    var default_control=""
    if(control=="Radio Button List"){
        default_control ='<img src="/assets/go1_commerce/images/radio-button.png" style="width:125px" />'
    }
    if(control=="Checkbox List"){
        default_control ='<img src="/assets/go1_commerce/images/checkbox.png" style="width:125px"/>'
    }
    if(control=="Dropdown List"){
        default_control ='<img src="/assets/go1_commerce/images/list.png" style="width:125px"/>'
    }
    if(control=="Color Boxes"){
        default_control ='<img src="/assets/go1_commerce/images/color-boxes.png" style="width:125px"/>'
    }
    if(control=="Text Box"){
        default_control ='<img src="/assets/go1_commerce/images/text-box.png" style="width:260px"/>'
    }
    if(control=="Table"){
        default_control ='<img src="/assets/go1_commerce/images/table.png" style="width:260px;"/>'
    }
    if(control=="Multi Line Text"){
        default_control ='<img src="/assets/go1_commerce/images/multiline.png" style="width:260px"/>'
    }
    dialog.fields_dict["controltype_html"].$wrapper.html(defaulthtml);
    dialog.fields_dict["controltype_html"].$wrapper.find("#controltype-img").html(default_control);
    dialog.fields_dict["controltype_html"].$wrapper.find('input[name="control_type"]').on("click", function(){
        var val = $(this).val();
        var html =""
      
        if(val=="Radio Button List"){
            html ='<img src="/assets/go1_commerce/images/radio-button.png" style="width:125px"/>'
        }
        if(val=="Checkbox List"){
            html ='<img src="/assets/go1_commerce/images/checkbox.png" style="width:125px"/>'
        }
        if(val=="Dropdown List"){
            html ='<img src="/assets/go1_commerce/images/list.png" style="width:125px"/>'
        }
        if(val=="Color Boxes"){
            html ='<img src="/assets/go1_commerce/images/color-boxes.png" style="width:125px"/>'
        }
        if(val=="Text Box"){
            html ='<img src="/assets/go1_commerce/images/text-box.png" style="width:260px"/>'
        }
        if(val=="Table"){
            html ='<img src="/assets/go1_commerce/images/table.png" style="width:260px"/>'
        }
        if(val=="Multi Line Text"){
            html ='<img src="/assets/go1_commerce/images/multiline.png" style="width:260px"/>'
        }
       dialog.fields_dict["controltype_html"].$wrapper.find("#controltype-img").html(html)
    });
}

function edit_rolebased_pricing(e){
    var cdt = $(e).attr("data-cdt");
    var cdn = $(e).attr("data-cdn");
    let row = frappe.get_doc(cdt, cdn)
    let data = JSON.parse(row.role_based_pricing)||[];
    let args = {
            'dt': 'Order Settings',
            'business': cur_frm.doc.restaurant
        };
    let order = cur_frm.events.get_settings(cur_frm, args);
    if(data.length<=0 && order.franchise_role){
        data = [{"role": order.franchise_role, "price":0, "idx":1}]
    }
    const dialog = new frappe.ui.Dialog({
        title: __("Pricing Rule"),
        fields: [
            {fieldtype:'Section Break', label: __('')},
            {
                fieldname: "pricing_rule", fieldtype: "Table", cannot_add_rows: false,
                in_place_edit: true, data: data,
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
                args=[]
            }
           
            frappe.model.set_value(cdt, cdn, "role_based_pricing", JSON.stringify(args))
            dialog.hide();
             let row = frappe.get_doc(cdt, cdn);
        if(!row.role_based_pricing){
            row.role_based_pricing="[]"
        }
        let data = args
        var pricing_html='<table class="table table-bordered"><thead style="background-color:#f7fafc;"><tr><th></th><th style="">Role</th><th style="">Price</th></tr></thead><tbody>';
       
        if(data.length>0){
            $.each(data, function (i, f) {

             pricing_html += '<tr data-id="'+f.idx+'"><td>'+f.idx+'</td><td>'+f.role+'</td><td style="">'+parseFloat(f.price).toFixed(2)+' '+symbol+'</td></tr>'
                  
            })
     }else{
        pricing_html += '<tr data-type="noitems"><td colspan="3">Records Not Found!</td></tr>'     
     }
      pricing_html += '</tbody></table>';
     
        frappe.model.set_value(cdt, cdn, "pricing_html", pricing_html)
        frappe.meta.get_docfield(cdt, "pricing_html",
                    cur_frm.doc.name).options = pricing_html;
        },
        primary_action_label: __('Save')
    });
    dialog.show()
    }

function update_attroption(e){
   
    var option_value = $(e).attr("data-id");
    var attribute = $(e).attr("data-attribute");
    var optionid = $(e).attr("data-option_name");
    var index = $(e).attr("data-index");
    var parentindex = $(e).attr('data-parentidx');
    var optionhtml = '<div class="form-group option-group" style="margin-bottom: 0px;"><div class="control-input-wrapper"> <div class="control-input form-control table-multiselect" style="background-color:unset !important;" id="table-multiselect">'
    var varient_options  = cur_frm.doc.attribute_options.filter( x =>  x.attribute == cur_frm.doc.product_attributes[index].product_attribute && x.attribute_id == cur_frm.doc.product_attributes[index].name);
    let objIndex = cur_frm.doc.attribute_options.findIndex((obj => obj.option_value == option_value && obj.attribute == cur_frm.doc.product_attributes[index].product_attribute && obj.attribute_id == cur_frm.doc.product_attributes[index].name));
    
    $(cur_frm.doc.attribute_options).each(function(i, f){
       if(objIndex==i && f.attribute == cur_frm.doc.product_attributes[index].product_attribute && f.attribute_id == cur_frm.doc.product_attributes[index].name){
           
           frappe.model.set_value("Product Attribute Option", f.name, "is_pre_selected", 1);
           cur_frm.doc.attribute_options[i].is_pre_selected=1
           f.is_pre_selected =1
          var comb_index = f.display_order
         
         var btn_cls = 'btn-info';
         optionhtml += '<div class="btn-group tb-selected-value" id="multi_input_updatevalue" style="display: inline-block;margin-right: 5px;margin-bottom: 5px;" data-value="'+f.option_value+'" data-name="'+f.name+'" data-index="'+index+'">'
        optionhtml += '<a class="btn '+btn_cls+' btn-xs btn-link-to-form" data-parentidx="'+parentindex+'" data-id="'+f.option_value+'" data-attribute="'+cur_frm.doc.product_attributes[index]["product_attribute"]+'" data-index="'+index+'" data-display_order="'+comb_index+'" data-option_name="'+f.name+'" data-is_pre_selected="'+cur_frm.doc.attribute_options[objIndex].is_pre_selected+'" data-product_title="'+f.product_title+'"  data-disable="'+f.disable+'" data-parent-control-type="'+cur_frm.doc.product_attributes[index]["control_type"]+'" ondblclick="update_attroption($(this))"><img src="/assets/go1_commerce/images/section-icon.svg" style="height:10px;cursor: all-scroll;position: relative;">'+f.option_value+'</a>'
        optionhtml += '<a class="btn '+btn_cls+' btn-xs btn-remove" data-id="'+f.option_value+'" onclick="remove_attroption($(this))"><i class="fa fa-remove text-muted"></i> </a></div>'     
       }

       if (objIndex!=i && f.attribute == cur_frm.doc.product_attributes[index].product_attribute && f.attribute_id == cur_frm.doc.product_attributes[index].name){
           
           frappe.model.set_value("Product Attribute Option", f.name, "is_pre_selected", 0);
           cur_frm.doc.attribute_options[i].is_pre_selected=0
            f.is_pre_selected = 0
          var comb_index = f.display_order
          
        var btn_cls = 'btn-default';
         optionhtml += '<div class="btn-group tb-selected-value" id="multi_input_updatevalue" style="display: inline-block;margin-right: 5px;margin-bottom: 5px;" data-value="'+f.option_value+'" data-name="'+f.name+'" data-index="'+index+'">'
        optionhtml += '<a class="btn '+btn_cls+' btn-xs btn-link-to-form" data-parentidx="'+parentindex+'" data-id="'+f.option_value+'" data-attribute="'+cur_frm.doc.product_attributes[index]["product_attribute"]+'" data-index="'+index+'" data-display_order="'+comb_index+'" data-option_name="'+f.name+'" data-is_pre_selected="'+cur_frm.doc.attribute_options[objIndex].is_pre_selected+'" data-product_title="'+f.product_title+'"  data-disable="'+f.disable+'" data-parent-control-type="'+cur_frm.doc.product_attributes[index]["control_type"]+'" ondblclick="update_attroption($(this))"><img src="/assets/go1_commerce/images/section-icon.svg" style="height:10px;cursor: all-scroll;position: relative;">'+f.option_value+'</a>'
        optionhtml += '<a class="btn '+btn_cls+' btn-xs btn-remove" data-id="'+f.option_value+'" onclick="remove_attroption($(this))"><i class="fa fa-remove text-muted"></i> </a></div>'     
      }
      })
    optionhtml  += '<div class="link-field ui-front" style="position: relative; line-height: 1;"><div class="awesomplete"><input placeholder="Separate options with a comma" style="padding: 6px 10px 8px;font-size: 11px;width: 178px;font-weight: 400;" type="text" id="select_options'+parentindex+'" keydown="add_option_totable($(this))" class="input-with-feedback bold" data-fieldtype="Table MultiSelect" data-fieldname="display_options" placeholder="" data-doctype="Product" data-target="Product" autocomplete="off" aria-owns="awesomplete_list_45" role="combobox" aria-activedescendant="awesomplete_list_45_item_0"></div> </div>'
    optionhtml += '</div></div>'

    $(e).parent().parent().parent().parent().html(optionhtml);
    cur_frm.refresh_field("attribute_options");
    cur_frm.dirty()
   
}

function update_attroption1(e){
    var option_value = $(e).attr("data-id");
    var option_name = $(e).attr("data-option-name");
    
    var index = $(e).attr("data-index");
    var product_title = $(e).attr("data-product_title");
    var parent_control_type = $(e).attr("data-parent-control-type");
    var display_order = $(e).attr("data-display_order");
    var is_pre_selected = $(e).attr("data-is_pre_selected");
    var disable = $(e).attr("data-disable");
    let args = {
            'dt': 'Catalog Settings',
            'business': cur_frm.doc.restaurant
        };
    cur_frm.catalog_settings = cur_frm.events.get_settings(cur_frm, args);
    let dialog_fields =[
            {fieldtype:'Section Break', label: __('')},
            {
             fieldtype:'Data',
            fieldname:"option_value",
            placeholder: 'Option Value',
            default: option_value,
            read_only: 1,
            label: __('Option Value')
            },
            { "fieldname": "disable", "fieldtype": "Check", "label": "Disable", "default": disable },
            {
             fieldtype:'Check',
            fieldname:"is_pre_selected",
            placeholder: 'Is Pre Selected',
            read_only: 0,
            default: is_pre_selected,
            label: __('Is Pre Selected')
            },  
            
            {fieldtype:'Column Break', label: __('')},
            
            {
             fieldtype:'Data',
            fieldname:"product_title",
            placeholder: 'Product Title',
            read_only: 0,
            default: product_title,
            label: __('Product Title')
            }, 
            {
             fieldtype:'Int',
            fieldname:"display_order",
            placeholder: 'Display Order',
            read_only: 0,
            default: display_order,
            label: __('Display Order'),
            hidden:1
            },
        ]
        dialog_fields.push({fieldtype:'Section Break', label: __('')})
        dialog_fields.push({
            "fieldtype": "Float",
            "label": __("Weight Adjustment"),
            "fieldname": "weight_adjustment",
            "reqd": 0
        });
        dialog_fields.push({fieldtype:'Column Break', label: __('')})
        if(parent_control_type=="Color Boxes"){
            dialog_fields.push({
                "fieldtype": "Color",
                "label": __("Color"),
                "description": "Color is applied based on 'Control Type(Color Boxes)' field.",
                "fieldname": "attribute_color"
            });
        }
    const dialog = new frappe.ui.Dialog({
        title: __("Option Detail"),
        fields: dialog_fields,
        primary_action: function() {
            var args = dialog.get_values();
            if(args){
                let check_data = cur_frm.attribute_items[index]["attroptions"].find(obj => obj.option_value == option_value);
                let optionindex = cur_frm.attribute_items[index]["attroptions"].findIndex(obj => obj.option_value == option_value);
                cur_frm.attribute_items[index]["attroptions"][optionindex]["product_title"]=args.product_title
                cur_frm.attribute_items[index]["attroptions"][optionindex]["is_pre_selected"]=args.is_pre_selected
                cur_frm.attribute_items[index]["attroptions"][optionindex]["display_order"]=args.display_order
               
                dialog.hide()
            }
        }
    })
    dialog.show()
}

function remove_attroption(e){
    var data = $(e).attr("data-id");
    var index = $(e).attr("data-index");
    var opt_name = $(e).parent().attr("data-name");
    console.log(data,opt_name)
    frappe.confirm(__("Do you want to delete this Option,it will remove the combination associated with this option after saving the document?"), () => {

    $(cur_frm.doc.attribute_options).each(function(i, v) {
        if (v.option_value == data){
            if(cur_frm.get_field("attribute_options").grid.grid_rows){
                cur_frm.get_field("attribute_options").grid.grid_rows[i].remove()
            } else{
                cur_frm.doc.attribute_options.splice(i, 1);
            }
        }
    })
    if(cur_frm.doc.variant_combination){
        for(var c=0;c<cur_frm.doc.variant_combination.length;c++){
            var attr_ids= cur_frm.doc.variant_combination[c].attribute_id.split('\n');
            for(var a=0;a<attr_ids.length;a++){
                if(attr_ids[a]==opt_name){
                    cur_frm.doc.variant_combination[c].disabled=1;
                }
            }
        }
    }
    $(e).parent().remove();
     cur_frm.refresh_field("attribute_options");
     cur_frm.refresh_field("variant_combination");
      cur_frm.dirty()
    })
}

function remove_attroption1(e){
    var data = $(this).attr("data-value")
    let obj = cur_frm.attribute_items.filter(o => o.option_value != data);
    $(obj).each(function(k, v) {
        v.idx = (k + 1);
    })
    cur_frm.attribute_items = obj
    $(e).parent().remove();
}

function new_combination_details(){
 
            if (cur_frm.doc.product_attributes && cur_frm.doc.product_attributes.length > 0) {
                let fields = [];
                let image = false;
                let attribute_color = false;
                let img_html = '';
                let color_html = '';
                if (cur_frm.all_attributes) {
                    console.log(cur_frm.all_attributes)
                    $(cur_frm.all_attributes).each(function (k, v) {
                        let f = {};
                        f.fieldname = v.attribute_unique_name;
                        f.label = v.attribute;
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
                            } else {
                                options += '<li><label><input type="' + control_type + '" name="item-' + v.name + '" value="' + j.option_value + '" /> ' + j.option_value + '</label></li>'
                            }
                            if (j.image) {
                                image = true;
                                img_html += '<li><img src="' + j.image + '" style="height:75px;" /></li>'
                            }
                            if (j.attribute_color != "-" && j.attribute_color != null && j.attribute_color != '') {
                                attribute_color = true;
                                color_html += '<li>\
                                                <span class="choice-box-content tooltip-toggle" title="' + j.option_value + '" data-id="' + j.attribute_color + '">\
                                                <span class="choice-box-element" style="background-color: ' + j.attribute_color + ';"></span>\
                                                </span>\
                                                </li>'
                            }
                        })
                        if (v.control_type == 'Dropdown List') {
                            f.fieldtype = 'Select';
                            f.options = options;
                            f.reqd = reqd;
                        } else {
                            f.fieldtype = 'HTML';
                            f.options = '<div><label>' + f.label + '</label><ul class="attributeOptions">' + options + '</ul></div>'
                        }
                        fields.push(f)
                    })
                }
                if (image) {
                    fields.push({
                        "fieldname": "pictures",
                        "fieldtype": "HTML",
                        "options": "<div><label>Pictures</label><ul class='attributeImages'>" + img_html + "</ul></div>"
                    })
                }
                if (attribute_color != false) {
                    fields.push({
                        "fieldname": "colors",
                        "fieldtype": "HTML",
                        "options": "<div><label>Colors</label><ul class='attributeColors'>" + color_html + "</ul></div>"
                    })
                }
                fields.push({
                    "fieldtype": "Column Break",
                    "fieldname": "sc"
                }, {
                    "fieldname": "stock",
                    "fieldtype": "Float",
                    "label": "Stock Qty",
                    'hidden':1,
                }, {
                    "fieldname": "price",
                    "fieldtype": "Currency",
                    'hidden':1,

                    "label": "Price"
                }, {
                    "fieldname": "weight",
                    "fieldtype": "Float",
                    'hidden':1,

                    "label": "Weight"
                })
                let attr_dialog = new frappe.ui.Dialog({
                    title: __("Attribute Combination"),
                    fields: fields
                })
                attr_dialog.show();
                attr_dialog.$wrapper.find('.modal-dialog').css("width", "1030px");
                attr_dialog.$wrapper.find('.attributeImages li').click(function () {
                    let cls = $(this).attr('class');
                    if (cls == 'active')
                        $(this).removeClass('active');
                    else
                        $(this).addClass('active')
                })
                attr_dialog.$wrapper.find('.attributeColors li').click(function () {
                    let cls = $(this).attr('class');
                    if (cls == 'active')
                        $(this).removeClass('active');
                    else
                        $(this).addClass('active')
                })
                var variant_txt = "";
                attr_dialog.set_primary_action(__("Add"), function () {
                    let values = attr_dialog.get_values();
                    let attr_comb = ''
                    let attr_id = ''
            let attributes_json=[];
            $(cur_frm.all_attributes).each(function (k, v) {
                if (v.control_type == 'Dropdown List') {
                    if (values[v.name]) {
                            attr_comb += '<div data-name="'+v.name+'" class="btn btn-default btn-xs btn-link-to-form" style="border: 1px solid #d1d8dd;margin: 2px;min-width: 50px;text-align: left;"><p style="text-align: left;margin: 0px;font-size: 11px;">'+v.attribute+'</p> <span style="font-weight: 700;">Red</span></div>';
                        attr_comb += '<td>' + values[v.name] + '</td></tr>'
                        let id = v.options.find(obj => obj.option_value == values[v.name])
                        attr_id += id.name + '\n';
                        attributes_json.push(id.name);

                    }
                } else {
                    if (v.control_type == 'Checkbox List') {
                        $('input[name="item-' + v.name + '"]:checked').each(function () {
                                attr_comb += '<div data-name="'+v.name+'" class="btn btn-default btn-xs btn-link-to-form" style="border: 1px solid #d1d8dd;margin: 2px;min-width: 50px;text-align: left;"><p style="text-align: left;margin: 0px;font-size: 11px;">'+v.attribute+'</p> <span style="font-weight: 700;">'+$(this).attr('value')+'</span></div>';
                            
                            let id = v.options.find(obj => obj.option_value == $(this).attr('value'))
                            attr_id += id.name + '\n';
                            attributes_json.push(id.name);
                        })
                    } else if (v.control_type == 'Color Boxes') {
                        $('input[name="item-' + v.name + '"]:checked').each(function () {
                            attr_comb += '<div data-name="'+v.name+'" class="btn btn-default btn-xs btn-link-to-form" style="border: 1px solid #d1d8dd;margin: 2px;min-width: 50px;text-align: left;"><p style="text-align: left;margin: 0px;font-size: 11px;">'+v.attribute+'</p> <span style="font-weight: 700;">'+$(this).attr('value')+'</span></div>';
                            let id = v.options.find(obj => obj.option_value == $(this).attr('value'))
                            attr_id += id.name + '\n';
                            attributes_json.push(id.name);
                        })
                    } else {
                        let val = $('input[name="item-' + v.name + '"]:checked').val();
                        attr_comb += '<div data-name="'+v.name+'" class="btn btn-default btn-xs btn-link-to-form" style="border: 1px solid #d1d8dd;margin: 2px;min-width: 50px;text-align: left;"><p style="text-align: left;margin: 0px;font-size: 11px;">'+v.attribute+'</p> <span style="font-weight: 700;">'+val+'</span></div>';
                        let id = v.options.find(obj => obj.option_value == val)
                        attr_id += id.name + '\n';
                        attributes_json.push(id.name);
                        variant_txt += val+" / "
                    }
                }
            
            })
            let check = cur_frm.doc.variant_combination.find(ob => ob.attribute_id == attr_id);
    
            if (check) {
                frappe.throw('This combination of attributes already exists')
            }
            let row = frappe.model.add_child(cur_frm.doc, "Product Variant Combination", "variant_combination");
            row.attribute_html = '<table>' + attr_comb + '</table>';
            row.attribute_id = attr_id;
            row.attributes_json = JSON.stringify(attributes_json);
            row.stock = values.stock;
            row.price = values.price;
            row.weight = values.weight;
            console.log(variant_txt)
            var vtext = cur_frm.doc.item+" - "+variant_txt;
            console.log(vtext.substr(0, vtext.length - 1))
            row.product_title = vtext.toString().slice(0,-1);

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
            // frm.reload_doc();
        })
    } else {
        frappe.throw('Please add attributes before creating its combination')
    }
}

function save_attribute_and_options(){
    if(cur_frm.attribute_items){
            
        frappe.call({
        method: 'go1_commerce.go1_commerce.doctype.product.product.insert_product_attribute_and_options',
        args: {doc: cur_frm.attribute_items},
        callback: function (data) {
            refresh_field('product_attributes');
            cur_frm.refresh_fields('product_attributes');
            refresh_field('attribute_options');
            cur_frm.refresh_fields('attribute_options');
                if (cur_frm.attribute_items && cur_frm.attribute_items.length > 0) {
                    frappe.confirm(
                        'Would you like to combine all attributes? Existing combinations will be deleted!',
                        function () {
                            if (cur_frm.attribute_items) {
                                frappe.call({
                                    method: 'go1_commerce.go1_commerce.doctype.product.product.create_variant_combinations',
                                    args: {
                                        attributes: cur_frm.attribute_items
                                    },
                                    callback: function (r) {
                                        if (r.message) {
                                            combination_weight_collect(r.message)
                                        }
                                    }
                                })
                            }
                        }
                    )
                } else {
                    frappe.throw('Please add attributes before creating its combination')
                }
                cur_frm.trigger('get_all_attributes_and_options')
            }
        })
    }
}
function combination_weight_collect(combinations){
    console.log(combinations);
    let random = Math.random() * 100;
    let weight_dialog = new frappe.ui.Dialog({
        title: 'Variant Combinations',
        fields: [{
            "fieldname": "comb_weight_html",
            "fieldtype": "HTML",
            "label":""
        }],
        
    });
    weight_dialog.$wrapper.find('.modal-content').css("max-width","700px !important");
    weight_dialog.$wrapper.find('.modal-content').css("width","700px !important");
	weight_dialog.show();
    var show_price ="";
    if(cur_frm.doc.is_template==1){
        show_price ="display:none;"
    }
    var tbl_id = "tbl_cweight_"+parseInt(random);
    var combination_html = "<table id='"+tbl_id+"' style='margin-top:0' class='table table-bordered'><thead><th style='width:50%'>Combination</th><th>Weight</th><th style='"+show_price+"'>Price</th><th class='var_stock' style='"+show_price+"'>Stock</th></thead><tbody>";
    if(combinations){
        for(var k=0;k<combinations.length;k++){
            combination_html+="<tr data-id='"+combinations[k].attribute_id+"'><td>"+combinations[k].attribute_html+"</td><td><input type='number' class='form-control c_weight' value='0'></td><td style='"+show_price+"'><input type='number' class='form-control c_price' value='0' ></td><td class ='var_stock' style='"+show_price+"'><input type='number' class='form-control c_stock' value='0' ></td></tr>";
        }
    }
    if(combinations.length==0){
        combination_html+="<tr><td colspan='2'>No new combination found.</td></tr>";
        weight_dialog.$wrapper.find('.modal-footer').hide();
    }
    combination_html+="</tbody></table>";
    weight_dialog.$wrapper.find('div[data-fieldname="comb_weight_html"]').append(combination_html)
    weight_dialog.set_primary_action(__('Save'), function () {
        var is_valid = 1;
        $("#"+tbl_id+" tbody").find("tr").each(function(){
            console.log($(this).find(".c_weight").val())
            if(!(parseFloat($(this).find(".c_weight").val())>0)){
                frappe.msgprint("Please enter the weight for the combination "+$(this).find("td:eq(0)").html())
                is_valid = 0;
                return;
            }
            if(cur_frm.doc.is_template==0){
                if(!(parseFloat($(this).find(".c_price").val())>0)){
                    frappe.msgprint("Please enter the price for the combination "+$(this).find("td:eq(0)").html())
                    is_valid = 0;
                    return;
                }
            }
        })
        if(is_valid==1){
            for(var p=0;p<cur_frm.doc.variant_combination.length;p++){
                var disabled = 0;
                if(cur_frm.doc.variant_combination[p].disabled==0){
                    $(combinations).each(function (k, v) {
                        if((v.attribute_id.split('\n')).length!=(cur_frm.doc.variant_combination[p].attribute_id.split('\n')).length){
                            disabled = 1;
                        }
                    });
                }
                else{
                    disabled = 1;
                }
                cur_frm.doc.variant_combination[p].disabled = disabled
            }
            $(combinations).each(function (k, v) {
                var weight = 0;
                var price = 0;
                var stock = 0;
                $("#"+tbl_id+" tbody").find("tr").each(function(){
                    if($(this).attr("data-id")==v.attribute_id){
                        weight = parseFloat($(this).find(".c_weight").val());
                        price = parseFloat($(this).find(".c_price").val());
                        stock = parseFloat($(this).find(".c_stock").val());
                    }
                });
                v.weight = weight;
                v.price = price;
                v.stock = stock;
                create_attribute_combination(cur_frm, v);
            })
            cur_frm.refresh_field("variant_combination");
            cur_frm.dirty();
            cur_frm.save();
            weight_dialog.hide()
        }
    });
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
    row.stock = v.stock;
    row.price = v.price;
    row.weight = v.weight;
    row.product_title = v.product_title;
    row.sku = v.sku;
    row.attributes_json = JSON.stringify(v.attributes_json);
    cur_frm.refresh_field("variant_combination")
    new generate_variant_combination_html({
        frm:frm,
        items_list: frm.doc.variant_combination,
        cdt: frm.doctype,
        cdn: frm.docname
    });
     frm.dirty();
}
function get_variant_combination(evt, e) {
  
    var combination = $(e).attr("data-id");
    var i, tabcontent, tablinks;tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(combination).style.display = "block";
    evt.currentTarget.className += " active";
}

function edit_media_details(e){
    var doc_type = $(e).attr("data-cdt");
    var docname = $(e).attr("data-cdn");
    let dialog_fields =[]
    dialog_fields.push({fieldtype:'Section Break', label: __('Image Gallery')})
    dialog_fields.push({
        "fieldtype": "Button",
        "label": __("Add / Edit Image"),
        "fieldname": "add_combination_image"
    });
    dialog_fields.push({
    'fieldname': 'attribute_image_html',
    'fieldtype': 'HTML'
    });
    if(cur_frm.catalog_settings.enable_product_video){
        dialog_fields.push({fieldtype:'Section Break', label: __('Video Gallery')})
        $.merge(dialog_fields, [
            { "fieldtype": "Button", "label": __("Add Video Link"), "fieldname": "add_combination_video"},
            { "fieldtype": "Button", "label": __("Upload Video"), "fieldname": "upload_combination_video" },
            { 'fieldname': 'attribute_video', 'fieldtype': 'HTML' }
            
        ])    
    }
    const dialog = new frappe.ui.Dialog({
        title: __("Gallery"),
        fields: dialog_fields,
        primary_action_label: __('Save'),
        primary_action: function() {
            var args = dialog.get_values();
            if(args){
            }
        }
    })
     
    if(dialog.fields_dict.add_combination_image){
        dialog.fields_dict.add_combination_image.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
        dialog.fields_dict.add_combination_image.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
    }
    if(dialog.fields_dict.add_combination_video){
        dialog.fields_dict.add_combination_video.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
        dialog.fields_dict.add_combination_video.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
    }
    if(dialog.fields_dict.upload_combination_video){
        dialog.fields_dict.upload_combination_video.$wrapper.find('button').removeClass('btn-xs').addClass('btn-sm');
        dialog.fields_dict.upload_combination_video.$wrapper.find('button').removeClass('btn-default').addClass('btn-primary');
    }   
    if(dialog.fields_dict.add_combination_image){
        dialog.fields_dict.add_combination_image.input.onclick = function () {
            var attributeId = docname;
            if (attributeId) {
                let attribute_info = frappe.get_doc(doc_type, docname);
                localStorage.setItem('randomuppy', ' ');
                cur_frm.events.generate_attribute_image_html(cur_frm, 'Product Variant Combination', attributeId, attribute_info)
                cur_frm.events.image_upload(cur_frm, 'Product Variant Combination', attributeId, "combination_images", 'Product Variant Combination', attributeId)
            } else {
                frappe.throw('Please save the document and then try uploading images')
            }
        }
    }
    if(dialog.fields_dict.add_combination_video){
        dialog.fields_dict.add_combination_video.input.onclick = function () {
            var attributeId1 = docname;
            if (attributeId1) {
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
                            "options": "Youtube\nVimeo\nOther",
                            "default": "Youtube"
                        }],
                        primary_action_label: __('Close')
                    });
                    video_dialog.show();
                    video_dialog.set_primary_action(__('Add'), function () {
                        var html = '<table class="table table-bordered" id="OptionsData1"><thead style="background: #F7FAFC;"><tr><th width="65%">Video url</th><th>Type</th><th>Actions</th></tr></thead>';
                        let values = video_dialog.get_values();
                        frappe.call({
                            method: "go1_commerce.go1_commerce.doctype.product.product.insert_attribute_option_video",
                            args: {
                                "option_id": attributeId1,
                                "video_id": values.video_id,
                                "video_type": values.video_type
                            },
                            callback: function (r) {
                                if (r.message != undefined) {
                                    $.each(r.message, function (i, j) {
                                        html += '<tr id="tr-' + j.name + '"><td><i class="fa fa-file-video-o" aria-hidden="true"></i><span style="padding-left: 5px;">' + j.youtube_video_id + '</span></td><td>' + j.video_type + '</td>';
                                        html += ' <td><a class="btn btn-xs btn-danger" style="margin-left:10px;" onclick=DeleteAttributeOptionVideo("' + j.name + '","' + j.option_id + '")>Delete</a></td></tr>';
                                    });
                                } else {
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
            } else {
                frappe.throw('Please save the document and then try add video id')
            }
        }
    }
    if(dialog.fields_dict.upload_combination_video){
        dialog.fields_dict.upload_combination_video.input.onclick = function () {
            var attributeId = docname;
            if (attributeId) {
                
                localStorage.setItem('randomuppy', ' ');
                cur_frm.events.video_upload(cur_frm, 'Product Variant Combination', attributeId, "combination_youtube_video_id", 'Product Attribute Option Video', attributeId)
            } else {
                frappe.throw('Please save the document and then try uploading images')
            }
        }
    }
    dialog.show();
    get_attribute_images(docname, doc_type)
    get_attribute_videos(docname)
}

var generate_variant_combination_html = Class.extend({
    init: function(opts) {
        this.frm = opts.frm;
        this.frm.doc.variant_combination = opts.frm.doc.variant_combination
        this.cdt = opts.cdt;
        this.cdn = opts.cdn;
        this.make_add_option()
        this.make();
    },
    make: function() {
        let me = this;
        this.frm.fields_dict["product_variant_combination_html"].$wrapper.empty();
        let wrapper = this.frm.fields_dict["product_variant_combination_html"].$wrapper;
        var option_list = '<th style="width:25%">Attribute</th>'
        var show_price = "";
        if(this.frm.doc.is_template==1){
            show_price="display:none;"
        }
        let table = $(`<div class="wrapper product_variant_combination_cls" style=""><table class="table table-bordered">
                <thead>
                    <tr>
                        <th style="width: 5%;"></th>
                       ${option_list}
                        
                        <th style="width: 17%">${__("Weight (In KG)")}</th>
                       
                        <th style="width:17%">${__("SKU")}</th>
                         <th style="width:17%;${show_price}">${__("Price")}</th>
                        <th style="width:19%;display:none;">${__("Show In Market Place?")}</th>
                        <th style="width: 17%;">${__("Actions")}</th>
                       
                        
                    </tr>
                   
                </thead>
                <tbody style=""></tbody>
            </table></div><style>.product_variant_combination_cls>table>thead {
                display: table;
                width: calc(100%); 
              }
              ._6m9uU {
                z-index: 30;
                position: -webkit-sticky;
                position: sticky;
                right: .1rem;
                padding: 0 2rem;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: var(--p-surface,#fff);
                word-break: keep-all;
            }
              .product_variant_combination_cls>table>tbody {
                display: block; 
              
              }
              div[data-fieldname="product_variant_combination_html"] td div .frappe-control {
  margin-bottom: 0px !important;min-height: 32px !important;} div[data-fieldname="product_variant_combination_html"] td div input{border-radius: 4px !important;} div[data-fieldname="product_variant_combination_html"] .table > tbody > tr > td{padding: 5px;vertical-align: middle;}div[data-fieldname="product_variant_combination_html"] .table-bordered > thead > tr > th{border-bottom-width: 0px;} div[data-fieldname="product_variant_combination_html"] td div .frappe-control {
  margin-bottom: 0px !important;min-height: 32px !important;} div[data-fieldname="product_variant_combination_html"] td div input{border-radius: 4px !important;}</style>`).appendTo(wrapper);

  if(me.frm.doc.variant_combination && me.frm.doc.variant_combination.length>0){
        var bthide=""
        var c_index = 0;
             $.each(me.frm.doc.variant_combination, function (i, f) {
                if(f.disabled==0){
                  var comb_sku = ""
                
                    if(f.sku){
                         comb_sku = f.sku

                    }
                        var rows = $(`<tr data-id="${f.name}" data-name="${f.name}" data-cdt="${f.doctype}" data-cdn="${f.name}">
                                <td style="text-align: center;width: 3.2%;">${f.idx}</td>
                                <td style="">${__(f.attribute_html)}</td>
                               
                                <td style="">${__(f.weight)}</td>
                               
                                  <td style="">${__(comb_sku)}</td>
                                   <td style="display:none;">${__(f.show_in_market_place)}</td>
                                   <td style=""><button class="btn btn-primary btn-xs" style="margin-right: 8px;margin: 3px;" data-cdt="${f.doctype}" data-cdn="${f.name}" onclick="edit_media_details($(this))">Media</button><button class="btn btn-primary btn-xs" style="margin-right: 8px;margin: 3px;" data-cdt="${f.doctype}" data-cdn="${f.name}" onclick="edit_rolebased_pricing($(this))">Add/Edit Role Based Pricing</button></td>
                            </tr>`);
                        table.find('tbody').append(rows);
                        me.update_row(wrapper, table, f.name,c_index);
                        c_index = c_index+1;
            }
            
        })
        }
        else{
            table.find('tbody').append(`<tr data-type="noitems"><td colspan="7" style="width: 1% !important;">Records Not Found!</td></tr>`);
        }
    },
    make_add_option: function(){
        let html = `<div class="row"><div class="col-md-6"><button class="btn btn-xs btn-secondary"  id="addNewCombination" style="margin-right:10px;margin-bottom: 10px;display:none;"><span class="octicon octicon-plus"></span> Add Combination</button>
        <button class="btn btn-xs btn-secondary" onclick="save_attribute_and_options()" id="generateAllCombination" style="margin-bottom: 10px;"><span class="octicon octicon"></span>Generate Combination</button></div></div>`;
        $('div[data-fieldname="add_combination"]').html(html);
        $('#addNewCombination').click(function () {
            new_combination_details()
        })
    },
    update_row: function(wrapper, table, idx,sno){
        var btnhide=""
        let me = this;
        table.find('tbody').find('tr[data-id="'+idx+'"]').empty();
        let index = me.frm.doc.variant_combination.findIndex(x => x.name == idx);
         var show_price = "";
       if(me.frm.doc.is_template==1){
           show_price="display:none;"
       }
        let new_row = $(` <td style="text-align: center;width: 5%;">${sno+1}</td>
                <td style="width: 25%;"><div class="attribute_html"></div></td> 
             
                <td style="width: 17%;"><div class="weight"></div></td> 
                
                  <td style="width:17%"><div class="sku"></div></td> 
                  <td style="width: 17%;${show_price}"><div class="price"></div></td> 
                  <td style="width:19%;text-align:center;display:none;"><div class="show_in_market_place"></div></td> 
                  <td style="width: 17%;"><button class="btn btn-info btn-sm" style="border-radius:3px;margin-right: 8px;margin: 3px;" data-cdt="${me.frm.doc.variant_combination[index]["doctype"]}" data-cdn="${me.frm.doc.variant_combination[index]["name"]}" data-idx="${me.frm.doc.variant_combination[index]["idx"]}" onclick="edit_combination_details($(this))">Edit</button><a class="btn btn-danger btn-xs" data-cdt="${me.frm.doc.variant_combination[index]["doctype"]}" data-cdn="${me.frm.doc.variant_combination[index]["name"]}" data-idx="${me.frm.doc.variant_combination[index]["idx"]}"><span class="fa fa-trash"></span></a></td>
                                  
              
            `);
         table.find('tbody').find('tr[data-id="'+idx+'"]').html(new_row);
        
        let input0 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __("Product Attribute"),
                "fieldname": "attribute_html"
            },
            parent: new_row.find('.attribute_html'),
            only_input: true,
           
        })
        input0.$wrapper.append(me.frm.doc.variant_combination[index]["attribute_html"])
        let input1 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "Float",
                "label": __("Weight(In KG)"),
                "fieldname": "weight",
                "placeholder": "",
                "options":"",
                "default": me.frm.doc.variant_combination[index]["weight"],
                "read_only":0,
                "reqd":1,
                "onchange": function() {
                        var prev = me.frm.doc.variant_combination[index]["weight"];
                        let val = this.get_value();
                         if(prev!=val){
                          
                          me.frm.doc.variant_combination[index]["weight"] = val
                          frappe.model.set_value(me.frm.doc.variant_combination[index]["doctype"], me.frm.doc.variant_combination[index]["name"], "weight",val);
                           me.frm.dirty()  
                        }
                    }
            },
            parent: new_row.find('.weight'),
            only_input: true,
            value: me.frm.doc.variant_combination[index]["weight"]
        })
        input1.make_input();
        input1.set_value(me.frm.doc.variant_combination[index]["weight"]);

         var comb_sku = ""
        if(me.frm.doc.variant_combination[index]["sku"]){
             comb_sku = me.frm.doc.variant_combination[index]["sku"]

        }
        let input3 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "Data",
                "label": __("SKU"),
                "fieldname": "sku",
                "placeholder": "",
                "options":"",
                "default": comb_sku,
        "read_only":1,
                "onchange": function() {
                        var prev = me.frm.doc.variant_combination[index]["sku"];
                        let val = this.get_value();
                        if(prev!=val){
                         
                        me.frm.doc.variant_combination[index]["sku"] = val;
                        frappe.model.set_value(me.frm.doc.variant_combination[index]["doctype"], me.frm.doc.variant_combination[index]["name"], "sku",val);
                        
                           me.frm.dirty()  
                        }
                    }
            },
            parent: new_row.find('.sku'),
            only_input: true,
            value: comb_sku
        })
        input3.make_input();
        input3.set_value(comb_sku);
         let input2 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "Currency",
                "label": __("Price"),
                "fieldname": "price",
                "placeholder": "",
                "options":"",
                "default": me.frm.doc.variant_combination[index]["price"],
                "read_only":0,
                "hidden":(me.frm.doc.is_template==1)?1:0,
                "onchange": function() {
                        var prev = me.frm.doc.variant_combination[index]["price"];
                        let val = this.get_value();
                        if(prev!=val){
                        
                        me.frm.doc.variant_combination[index]["price"] = val;
                        frappe.model.set_value(me.frm.doc.variant_combination[index]["doctype"], me.frm.doc.variant_combination[index]["name"], "price",val);
                        
                           me.frm.dirty()  
                        }
                    }
            },
            parent: new_row.find('.price'),
            only_input: true,
            value: me.frm.doc.variant_combination[index]["price"]
        })
        input2.make_input();
        input2.set_value(me.frm.doc.variant_combination[index]["price"]);
      let input4 = frappe.ui.form.make_control({
            df: {
                "fieldtype": "Check",
                "label": __("Show In Market Place?"),
                "fieldname": "show_in_market_place",
                "placeholder": "",
                "options":"",
                "default":  me.frm.doc.variant_combination[index]["show_in_market_place"],
                "read_only":1,
                "onchange": function() {
                        var prev = me.frm.doc.variant_combination[index]["show_in_market_place"];
                        let val = this.get_value();
                        if(prev!=val){
                         
                        me.frm.doc.variant_combination[index]["show_in_market_place"] = val;
                        frappe.model.set_value(me.frm.doc.variant_combination[index]["doctype"], me.frm.doc.variant_combination[index]["name"], "show_in_market_place",val);
                        
                           me.frm.dirty()  
                        }
                    }
            },
            parent: new_row.find('.show_in_market_place'),
            only_input: true,
            value: me.frm.doc.variant_combination[index]["show_in_market_place"]
        })
        input4.make_input();
        input4.set_value(me.frm.doc.variant_combination[index]["show_in_market_place"]);
        new_row.find('.btn-success').click(function() {
            
            show_alert("Row saved.")
            me.make()
        })
         new_row.find('input[data-fieldname="sku"]').attr("disabled","disabled");
        new_row.find('.btn-danger').click(function() {
            let obj = me.frm.doc.variant_combination.filter(o => o.name != idx);
            var dt =$(this).attr("data-cdt");
            var dn =$(this).attr("data-cdn");
            let conf_html = '<ul style="padding: 0;margin: 0;">'
            conf_html +='<li style="list-style: none;"><b>'
            conf_html += cur_frm.doc.variant_combination.filter(o => o.name == idx)[0].attribute_html
            conf_html += '</b></li>'
            conf_html+='</ul>';
            frappe.warn("Do you want to delete the following combination?", conf_html,function () {
                frappe.call({
                    method: 'go1_commerce.go1_commerce.doctype.product.product.delete_combination',
                    args: {"dt":dt, "dn":dn},
                    async: false,
                    callback: function(r) {
                        $(obj).each(function(k, v) {
                            v.idx = (k + 1);
                        })
                        me.frm.doc.variant_combination = obj;
                        me.make()
                        me.frm.dirty()
                    }
                })
            },'Continue',true)
        });
    }
})

function save_combination_video(attributeId1) {
}

function edit_combination_details(e){

    let args = {'dt': 'Catalog Settings','business': cur_frm.doc.restaurant};
    cur_frm.catalog_settings = cur_frm.events.get_settings(cur_frm, args);
    if(!cur_frm.doc.__islocal){
        new go1_commerce.MakeVarientCombinationDialog({
            frm: cur_frm,
            items_list: cur_frm.doc.variant_combination,
            cdt: cur_frm.doctype,
            cdn: cur_frm.docname,
            combination_table: $(e).attr("data-cdt"),
            combination:$(e).attr("data-cdn")
        })
    }else{
        frappe.throw('Please add attributes before creating its combination')
    }
}

go1_commerce.MakeVarientCombinationDialog = Class.extend({
    init: function(opts) {
        this.frm = opts.frm;
        this.items_list = opts.items_list
        this.cdt = opts.cdt;
        this.cdn = opts.cdn;
        this.combination_table = opts.combination_table;
        this.combination = opts.combination;
        let me = this
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.get_order_settings',
            args: {},
            async:false,
            callback: function(d) {
                if(d.message){
                    me.order_setting = d.message.order_settings;
                }
            }
        })
        me.make();
    },
    make: function() {
        var me = this;
        me.make_fields();
        me.make_dialog();
        me.make_dialog_style();
        me.set_dialog_primary_action();
        me.dialog.show();
        me.dialog_events();
    },
    make_fields: function(){
        let me = this;
        let args = {
            'dt': 'Catalog Settings',
            'business': cur_frm.doc.restaurant
        };
        cur_frm.catalog_settings = cur_frm.events.get_settings(cur_frm, args);
        me.dialog_fields =[{fieldtype:'HTML', fieldname:"varient_tab"}]
      },
      make_dialog: function(){
        let me = this;
        me.dialog = new frappe.ui.Dialog({
            title: __("Edit Variant"),
            fields: me.dialog_fields,
            primary_action_label: __('Save'),
        })
        me.dialog.set_primary_action(__('Save'), function () { 
            console.log("---save---")
            me.dialog.hide();
            if(me.frm.doc.variant_combination){
                cur_frm.save(); 
            }
        })
    },
    make_dialog_style: function(){
      let me = this;
      let height = String($(window).height() - 40) + "px"
      let scrollheight = ($(window).height() - 40) - 200
      $(me.dialog.$wrapper).find('.modal-dialog').css("width", "calc(100% - 50px)");
      $(me.dialog.$wrapper).find('.modal-dialog').css("max-width", "80%");
      $(me.dialog.$wrapper).find('.modal-content').css("height", "auto");
      var p_height = $(window).height()-200+"px";
      $(me.dialog.$wrapper).find('.modal-body').css("height", p_height);
      $(me.dialog.$wrapper).find('.modal-body').css("background-color", "#f6f6f7");
      $(me.dialog.$wrapper).find('.form-section').css('padding', '0 7px');
      $(me.dialog.$wrapper).find('div[data-fieldname="varient_tab"]').css("margin-bottom","0px");
      $(me.dialog.$wrapper).find('input[data-fieldname="sku"]').attr("disabled","disabled");
      $(me.dialog.$wrapper).find('div[data-fieldname="varient_tab"]').parent().parent().parent().parent().css('border-bottom', 'none')
      $(me.dialog.$wrapper).find('div[data-fieldname="varient_tab"]').parent().parent().parent().parent().css('padding', '0px')
    },
    dialog_events: function(){
        let me = this;
        var pcr_height = $(window).height()-310+"px";
        var varient = me.dialog.fields_dict["varient_tab"].$wrapper.empty();
        if(me.frm.doc.variant_combination){
            var var_len = me.frm.doc.variant_combination.length;
        }else{
            var var_len = 0;
        }
        var image = '<div class="col-md-6" style="';
        if(me.frm.doc.image){
            image +='display: flex;justify-content: center;align-items: center;width: 76px;padding: 10px 0;float: left;">';
            image += '<img src="'+me.frm.doc.image+'"  style="max-height:76px"/>';
        }else{
            image +='width: 100px;height: 80px;display: flex;justify-content: center;align-items: center;border-radius: var(--p-border-radius-base,3px);border: 1px solid #dbdbdc;background: var(--p-surface,#f9fafb);margin-top: 10px;float: left;">';
            image += '<svg viewBox="0 0 20 20" class="_3vR36 _3DlKx"><path d="M2.5 1A1.5 1.5 0 0 0 1 2.5v15A1.5 1.5 0 0 0 2.5 19h15a1.5 1.5 0 0 0 1.5-1.5v-15A1.5 1.5 0 0 0 17.5 1h-15zm5 3.5c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2zM16.499 17H3.497c-.41 0-.64-.46-.4-.79l3.553-4.051c.19-.21.52-.21.72-.01L9 14l3.06-4.781a.5.5 0 0 1 .84.02l4.039 7.011c.18.34-.06.75-.44.75z"></path></svg>';
        }
        image +='</div>';

        $(`<div class="row" style="background: #f6f6f7;margin-right: 0px;margin-top: -10px;"><div class="col-md-4" style="height: 435px;"><div class="col-md-12" style="background: #ffffff;margin-top: 15px;
        margin-bottom: 15px;height: 100px;border-radius: 5px;padding:0;"><div class="card" style="    border: none;">
        <div class="card-body" style="padding:0">
        ${image}
        <div class="col-md-6" style="width:calc(100% - 76px);padding-right:0;float: left;padding-top: 10px;">
          <h5 class="card-title">${me.frm.doc.item}</h5>
          <p class="card-text" style="color: #8d99a6;font-weight: 600;">${var_len} Variants</p>
         </div>
        </div>
      </div></div><div class="col-md-12" id="bodyAttribute" style="border-radius: 5px;padding: 0px;background-color: rgb(255 255 255);
        "><h4 style="text-align: center;">Combinations</h4><ul class="list-group" style="height: ${pcr_height};overflow-y: auto;"></ul></div></div>
        <div class="col-md-2 " id="bodyOption" style="display:none;overflow-y: auto;padding:0px;border-right: 1px solid rgb(221, 221, 221);">
        <h4 style="text-align: center;">Options</h4><ul class="list-group" style="margin-bottom: 0px;">
        </ul></div><div class="col-md-8 parentDiv" id="optionTablediv" style="padding: 0px;height:252px;"><div class="insideParentDiv" style="display:none;"><h4 style="text-align: center;margin: 0px;
        padding: 10px;background: white;">Edit Variant</h4><div class="save_option_html" style="margin-top: -35px;display:none;"></div></div>
        
        <div class="col-md-12" id="optionTable1">
          <div class="dialog-heading"><h4 class="form-section-heading uppercase">Variant Detail</h4></div>
            <div class="col-md-4"><label class="opt-label" style="margin-top:10px">Product Title</label>
            <div class="product_title_html"></div></div>
            <div class="col-md-4"><label class="opt-label" style="margin-top:10px">Stock</label>
            <div class="stock_html"></div></div>
            <div class="col-md-4"><label class="opt-label" style="margin-top:10px">SKU</label><div class="sku_html"></div></div>
            <div class="col-md-4"><label class="opt-label" style="margin-top:10px">Price</label>
            <div class="price_html"></div></div>
            <div class="col-md-4"><label class="opt-label" style="margin-top:10px">MRP</label>
            <div class="old_price_html"></div></div>
            <div class="col-md-4"><label class="opt-label" style="margin-top:10px">Weight(In KG)</label>
            <div class="weight_html"></div></div>
            <div class="col-md-4">   
              
            </div>
             <div class="col-md-4"><label class="opt-label" style="margin-top:10px">Height(in cm)</label>
            <div class="height_html"></div></div>
             <div class="col-md-4"><label class="opt-label" style="margin-top:10px">Width(in cm)</label>
            <div class="width_html"></div></div>
             <div class="col-md-4"><label class="opt-label" style="margin-top:10px">Length(in cm)</label>
            <div class="length_html"></div></div>
             <div class="col-md-4"><label class="opt-label" style="margin-top:10px">Show In Market Place?</label>
            <div class="show_market_place"></div></div>
        </div>
        

        <div class="col-md-12" id="optionTable3">
        <div  class="dialog-heading"><h4 class="form-section-heading uppercase">Role Based Pricing</h4></div>
            <div class="col-md-8"><div class="role_based_pricing_html"></div></div>
            <div class="col-md-4"></div>
        </div>

        <div class="col-md-12" id="optionTable4">
        <div  class="dialog-heading"><h4 class="form-section-heading uppercase">Image Gallery</h4></div>
            <div class="col-md-3" style="    float: left;">
            <div class="add_combination_image_html" style="    float: left;">
            <div class="col-md-6" style="float:left;width: 250px;height: 10rem;display: flex;justify-content: center;align-items: center;border-radius: var(--p-border-radius-base,3px);border: .2rem dashed #a4a9ad;background: var(--p-surface,#f9fafb);">
            <img width="40" style="position: absolute;" src="data:image/svg+xml,%3csvg fill='none' xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'%3e%3cpath fill-rule='evenodd' clip-rule='evenodd' d='M20 10a10 10 0 11-20 0 10 10 0 0120 0zM5.3 8.3l4-4a1 1 0 011.4 0l4 4a1 1 0 01-1.4 1.4L11 7.4V15a1 1 0 11-2 0V7.4L6.7 9.7a1 1 0 01-1.4-1.4z' fill='%235C5F62'/%3e%3c/svg%3e" alt="">
           <button class="btn btn-default btn-xs" data-fieldtype="Button" id="add_combination_image_html_id" data-fieldname="add_combination_image" style="font-size: 10px;margin-top:62px;">Add / Edit Image</button>
            </div></div>
            </div>
            <div class="col-md-9"><div class="attribute_image_html"></div></div>
        </div>

        <div class="col-md-12" id="optionTable5" style="text-align :left;">
        <div class="dialog-heading"><h4 class="form-section-heading uppercase ">Video Gallery</h4></div>
        <div class="col-md-12"><div class="attribute_video_html"></div></div>
        <div class="col-md-3"><div class="add_combination_video_html" style="display:none"></div>
        <div class="upload_combination_video_html"></div></div>
        
    </div>
        </div><div class="" id="bodyCombination" style="display:none;padding: 0px;"><h4 style="text-align: center;">Linked Combinations</h4><ul class="list-group" style="height:252px;margin-bottom: 0px;">
        </ul></div></div><style>.dialog-heading>.form-section-heading{border-bottom: 1px solid #e2e5e9;}.dialog-heading{text-align: left; padding-left: 16px;}.btn:focus, .btn:active:focus{outline: 0px;outline-offset:0px;}#optionTable1{border-radius: 5px;background: #ffff; margin-top: 15px;padding: 8px;}
        #optionTable5{border-radius: 5px;background: #ffff; margin-top: 15px;padding: 8px;text-align: center; vertical-align: middle;}
        #optionTable4{border-radius: 5px;background: #ffff; margin-top: 15px;padding: 8px;text-align: center;vertical-align: middle;}
        #optionTable3{border-radius: 5px;background: #ffff; margin-top: 15px;padding: 8px;}.insidefootParentDiv{position:fixed;width: 65%;}.insideParentDiv{width: 100%;}#optionTablediv {overflow-y:scroll;overflow-x:hidden;}.save_option_html{float: right;}.opt-label{font-weight: 400;font-size: 13px;}.list-group-item{background-color: #fff;
        border: 1px solid #eee;} #optionTable{border: 0px;}#optionTable>tbody>tr>td{border: 0px;}#optionTable>thead>tr>th{border: 0px;}
        ._3DlKx { width: 2.8rem; height: 2.8rem;}._3vR36 {display: block;fill: var(--p-icon,#a4a9ad);color: transparent;}
       #optionTablediv .col-2xl, .col-2xl-auto, .col-2xl-12, .col-2xl-11, .col-2xl-10, .col-2xl-9, .col-2xl-8, .col-2xl-7, .col-2xl-6, .col-2xl-5, .col-2xl-4, .col-2xl-3, .col-2xl-2, .col-2xl-1, .col-xl, .col-xl-auto, .col-xl-12, .col-xl-11, .col-xl-10, .col-xl-9, .col-xl-8, .col-xl-7, .col-xl-6, .col-xl-5, .col-xl-4, .col-xl-3, .col-xl-2, .col-xl-1, .col-lg, .col-lg-auto, .col-lg-12, .col-lg-11, .col-lg-10, .col-lg-9, .col-lg-8, .col-lg-7, .col-lg-6, .col-lg-5, .col-lg-4, .col-lg-3, .col-lg-2, .col-lg-1, .col-md, .col-md-auto, .col-md-12, .col-md-11, .col-md-10, .col-md-9, .col-md-8, .col-md-7, .col-md-6, .col-md-5, .col-md-4, .col-md-3, .col-md-2, .col-md-1, .col-sm, .col-sm-auto, .col-sm-12, .col-sm-11, .col-sm-10, .col-sm-9, .col-sm-8, .col-sm-7, .col-sm-6, .col-sm-5, .col-sm-4, .col-sm-3, .col-sm-2, .col-sm-1, .col, .col-auto, .col-12, .col-xs-12, .col-11, .col-xs-11, .col-10, .col-xs-10, .col-9, .col-xs-9, .col-8, .col-xs-8, .col-7, .col-xs-7, .col-6, .col-xs-6, .col-5, .col-xs-5, .col-4, .col-xs-4, .col-3, .col-xs-3, .col-2, .col-xs-2, .col-1, .col-xs-1{float:left;}
       .list-group-item.active {background-color: #f9f9f9 !important;
    border-color: #f9f9f9  !important;} </style>`).appendTo(varient)

 if(me.order_setting.role_based_pricing==0){
                    varient.find('#optionTable3').css("display", "none");
                }else{
                     varient.find('#optionTable3').css("display", "block");
                }
        varient.find('#bodyOption').css("height",($(window).height()-52));
         var pr_height = $(window).height()-220+"px";
         varient.find('#optionTablediv').css("height",pr_height);
            $(me.frm.doc.variant_combination).each(function (k, f) {
                var title_json = f.attribute_html
            var combination_html = $.parseHTML("<div>"+title_json+"</div>");
           
            $(combination_html).find(".btn.btn-default.btn-xs.btn-link-to-form").attr("style","border: 1px solid #d1d8dd;margin: 2px;min-width: 50px;text-align: left;width: calc(33.3333% - 4px);");
            $(combination_html).find(".btn.btn-default.btn-xs.btn-link-to-form span").attr("style","font-weight: 700;white-space: normal;");
            var attrli = $(`<li data-idx="${k}" data-name="${f.name}" class="list-group-item d-flex justify-content-between align-items-center" style="cursor:pointer;margin: 0px 10px 0px 10px;">
            ${$(combination_html).html()}
                <span class="badge badge-primary badge-pill" style="display:none;position: absolute;right: 0;top: 0;background-color: #ffa00a;color: #fff;margin:5px;">Stock : ${f.stock}</span>
            </li>
            `).appendTo(varient.find('#bodyAttribute ul'));
            
            attrli.click(function() {
                if(me.order_setting.role_based_pricing==0){
                    varient.find('#optionTable3').css("display", "none");
                }else{
                     varient.find('#optionTable3').css("display", "block");
                }
                me.combination=f.name;
                me.dialog.header.find("h4").text("Edit Variant");
                var option_foot =  varient.find('#optionTablediv .insideParentDiv');
                var option_tab1 =  varient.find('#optionTable1');
                var option_tab3 =  varient.find('#optionTable3');
                var option_tab4 =  varient.find('#optionTable4');
                var option_tab5 =  varient.find('#optionTable5');
                varient.find('#bodyAttribute').find(".active").removeClass("active");
                attrli.addClass("active");
                
                option_tab1.find('.product_title_html').empty();
                option_tab1.find('.stock_html').empty();
                option_tab1.find('.sku_html').empty();
                option_tab1.find('.price_html').empty();
                option_tab1.find('.old_price_html').empty();
                option_tab1.find('.weight_html').empty();
                option_tab1.find('.length_html').empty();
                option_tab1.find('.width_html').empty();
                option_tab1.find('.height_html').empty();
                option_tab1.find('.show_market_place').empty();
                option_tab1.find('.show_market_place').parent().hide();
                option_tab3.find('.role_based_pricing_html').empty();
                option_tab4.find('.attribute_image_html').empty();
                option_tab5.find('.add_combination_video_html').empty();
                option_tab5.find('.upload_combination_video_html').empty();
                option_tab5.find('.attribute_video_html').empty();

                option_foot.find('.save_option_html').empty();

                let input_foot = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "Button",
                        "label": __("Save"),
                        "fieldname": "save_option"
                    },
                    parent: option_foot.find('.save_option_html'),
                })
                input_foot.make_input();
                input_foot.$wrapper.find('button').addClass("btn-primary");
                input_foot.$wrapper.find('button').addClass("btn-sm");
                input_foot.$wrapper.find('button').text("Save");
              let ptitle = cur_frm.doc.item
              if(f.product_title){
                ptitle = f.product_title
              }
                let product_title = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "Data",
                        "label": __("Product Title"),
                        "fieldname": "product_title",
                        "default": ptitle,
                        "onchange": function() {
                            let val = this.get_value();
                           
                            f.product_title = val;
                        }
                    },
                    parent: option_tab1.find('.product_title_html'),
                    only_input: true,
                    value: ptitle
                })
                product_title.make_input();
                product_title.set_value(ptitle);
                let stock = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "Int",
                        "label": __("Stock"),
                        "fieldname": "stock",
                        "default": f.stock,
                        "hidden":cur_frm.doc.is_template==0?0:1,
                        "onchange": function() {
                            let val = this.get_value();
                            f.stock = val;
                           }
                    },
                    parent: option_tab1.find('.stock_html'),
                    only_input: true,
                    value: f.stock
                })
                stock.make_input();
                stock.set_value(f.stock);
               
                let weight = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "Data",
                        "label": __("Weight(In KG)"),
                        "fieldname": "weight",
                        "default": f.weight,
                        "onchange": function() {
                            let val = this.get_value();
                            f.weight = val;
                           }
                    },
                    parent: option_tab1.find('.weight_html'),
                    only_input: true,
                    value: f.weight
                })
                weight.make_input();
                weight.set_value(f.weight);
                let height = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "Float",
                        "label": __("Height"),
                        "fieldname": "height",
                        "default": f.height,
                        "onchange": function() {
                            let val = this.get_value();
                            f.height = val;
                           }
                    },
                    parent: option_tab1.find('.height_html'),
                    only_input: true,
                    value: f.height
                })
                height.make_input();
                height.set_value(f.height);
                let show_market_place = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "Check",
                        "label": __("Show In Market Place?"),
                        "fieldname": "show_in_market_place",
                        "default": f.show_in_market_place,
                        "onchange": function() {
                            let val = this.get_value();
                            f.show_in_market_place = val;
                           }
                    },
                    parent: option_tab1.find('.show_market_place'),
                    only_input: true,
                    value: f.show_in_market_place
                })
                show_market_place.make_input();
                show_market_place.set_value(f.show_in_market_place);
                let width = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "Float",
                        "label": __("Width"),
                        "fieldname": "width",
                        "default": f.width,
                        "onchange": function() {
                            let val = this.get_value();
                            f.width = val;
                           }
                    },
                    parent: option_tab1.find('.width_html'),
                    only_input: true,
                    value: f.width
                })
                width.make_input();
                width.set_value(f.width);
                let length = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "Float",
                        "label": __("Length"),
                        "fieldname": "length",
                        "default": f.length,
                        "onchange": function() {
                            let val = this.get_value();
                            f.length = val;
                           }
                    },
                    parent: option_tab1.find('.length_html'),
                    only_input: true,
                    value: f.length
                })
                length.make_input();
                length.set_value(f.length);
                let price = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "Int",
                        "label": __("Price"),
                        "fieldname": "price",
                        "default": f.price,
                          "hidden":1,
                        "onchange": function() {
                            let val = this.get_value();
                            f.price = val;
                           }
                    },
                    parent: option_tab1.find('.price_html'),
                    only_input: true,
                    value: f.price
                })
                price.make_input();
                price.set_value(f.price);
                let old_price = frappe.ui.form.make_control({
                    df: {

                        "fieldtype": "Int",
                        "label": __("MRP"),
                        "fieldname": "old_price",
                        "default": f.old_price,
                          "hidden":1,
                        "onchange": function() {
                            let val = this.get_value();
                            f.old_price = val;
                           }
                    },
                    parent: option_tab1.find('.old_price_html'),
                    only_input: true,
                    value: f.old_price
                })
                old_price.make_input();
                old_price.set_value(f.old_price);
                let sku = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "Data",
                        "label": __("SKU"),
                        "fieldname": "sku",
                        "default": f.sku,
                        "read_only":1,
                        "onchange": function() {
                            let val = this.get_value();
                            f.sku = val;
                           }
                    },
                    parent: option_tab1.find('.sku_html'),
                    only_input: true,
                    value: f.sku
                })
                sku.make_input();
                sku.set_value(f.sku);
                me.pricing_html(f)
               $(me.dialog.$wrapper).find('input[data-fieldname="sku"]').attr("disabled","disabled");
                
                let attribute_image_html = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "HTML",
                        "label": __(""),
                        "fieldname": "attribute_image_html"
                    },
                    parent: option_tab4.find('.attribute_image_html'),
                    only_input: true
                })
               
                let upload_combination_video = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "Button",
                        "label": __("Upload Video"),
                        "fieldname": "upload_combination_video"
                    },
                    parent: option_tab5.find('.upload_combination_video_html'),
                    only_input: true
                })
                upload_combination_video.make_input();
                upload_combination_video.$wrapper.find('button').addClass("btn-primary");
                upload_combination_video.$wrapper.find('button').addClass("btn-sm");
                upload_combination_video.$wrapper.find('button').text("Upload Video");
                let attribute_video_html = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "HTML",
                        "label": __(""),
                        "fieldname": "attribute_video"
                    },
                    parent: option_tab5.find('.attribute_video_html'),
                    only_input: true
                })
                option_tab1.find('.stock_html').parent().hide();
                option_tab1.find('.price_html').parent().hide();
                
                if(!cur_frm.doc.is_template){
                    option_tab1.find('.stock_html').parent().show();
                    option_tab1.find('.price_html').parent().show();
                }
                option_tab4.find('.add_combination_image_html').find('#add_combination_image_html_id').attr("data-doctype", f.doctype);
                option_tab4.find('.add_combination_image_html').find('#add_combination_image_html_id').attr("data-name", f.name);
               
                    option_tab5.find('.upload_combination_video_html').find('button[data-fieldname="upload_combination_video"]').click(function() {   
                        var attributeId = f.name;
                        if (attributeId) {
                            localStorage.setItem('randomuppy', ' ');
                            cur_frm.events.video_upload(cur_frm, 'Product Variant Combination', attributeId, "combination_youtube_video_id", 'Product Attribute Option Video', attributeId)
                        } 
                        else {
                            frappe.throw('Please save the document and then try uploading images')
                        }
                    })
                get_attribute_images(me.combination, me.combination_table)
                get_attribute_videos(me.combination)
            });

            
            if(me.combination){
                if(f.name== me.combination){
                    attrli.click(); 
                }
            }else{
                me.new_from()
            }
        })
        varient.find('#optionTable4').find('.add_combination_image_html').find('#add_combination_image_html_id').on("click",function() {   
           
           var attrDoc = $(this).attr("data-doctype");
            var attributeId =  $(this).attr("data-name");
                if (attributeId) {
                    let attribute_info = frappe.get_doc(attrDoc, attributeId);
                    localStorage.setItem('randomuppy', ' ');
                    cur_frm.events.generate_combination_image_html(cur_frm, 'Product Variant Combination', attributeId, attribute_info)
                    cur_frm.events.image_upload(cur_frm, 'Product Variant Combination', attributeId, "combination_images", 'Product Variant Combination', attributeId)
                } else {
                    frappe.throw('Please save the document and then try uploading images')
                }
            })
    },
    set_dialog_primary_action: function() {
        var me = this;
        me.dialog.set_primary_action(__('Save'), function() {
                me.dialog.hide();
                 new generate_variant_combination_html({
                    frm:me.frm,
                    items_list: me.frm.doc.variant_combination,
                    cdt: me.frm.doctype,
                    cdn: me.frm.docname
                });
                 me.frm.dirty();
        });
    },
    construct_video_dialog: function(target) {
            var me = this;
            if ( me.optionid) {
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
                        "options": "Youtube\nVimeo\nOther",
                        "default": "Youtube"
                    }],
                    primary_action_label: __('Close')
                });
                video_dialog.show();
                video_dialog.set_primary_action(__('Add'), function () {
                    var html = '<table class="table table-bordered" id="OptionsData1"><thead style="background: #F7FAFC;"><tr><th>Video url</th><th>Type</th><th>Actions</th></tr></thead>';
                    let values = video_dialog.get_values();
                    frappe.call({
                        method: "go1_commerce.go1_commerce.doctype.product.product.insert_attribute_option_video",
                        args: {
                            "option_id":  me.optionid,
                            "video_id": values.video_id,
                            "video_type": values.video_type
                        },
                        callback: function (r) {
                            if (r.message != undefined) {
                                $.each(r.message, function (i, j) {
                                    html += '<tr id="tr-' + j.name + '"><td>' + j.youtube_video_id + '</td><td>' + j.video_type + '</td>';
                                    html += ' <td>';
                                    html+='<a class="btn btn-xs btn-danger" style="margin-left:10px;" onclick=DeleteAttributeOptionVideo("' + j.name + '","' + j.option_id + '")>Delete</a></td></tr>';
                                });
                            } else {
                                html += '<tr><td colspan="6" align="center">No Records Found.</td></tr>';
                            }
                            html += '</tbody>';
                            html += '</table>';
                            target.find('.attribute_video_html').find('div[data-fieldname="attribute_video_html"]').html(html);
                            video_dialog.hide();
                    }
                })
            })
        }
    },
    new_from: function(){
        let me = this;
        var varient = me.dialog.fields_dict["varient_tab"].$wrapper;
        me.dialog.header.find("h4").text("Add Variant");
        var f = {"product_title":"","stock":"", "weight":"", "price":"", "sku":"", "doctype":"Product Variant Combination", "name":"", "idx":  me.frm.doc.variant_combination.length+1}
        var option_foot =  varient.find('#optionTablediv .insideParentDiv');
        var option_tab1 =  varient.find('#optionTable1');
        var option_tab3 =  varient.find('#optionTable3');
        var option_tab4 =  varient.find('#optionTable4');
        var option_tab5 =  varient.find('#optionTable5');
        varient.find('#bodyAttribute').find(".active").removeClass("active");
        option_tab1.find('.product_title_html').empty();
        option_tab1.find('.stock_html').empty();
        option_tab1.find('.sku_html').empty();

        option_tab1.find('.price_html').empty();
        option_tab1.find('.old_price_html').empty();
        option_tab1.find('.weight_html').empty();
        option_tab1.find('.length_html').empty();
        option_tab1.find('.width_html').empty();
        option_tab1.find('.height_html').empty();
        option_tab1.find('.show_market_place').empty();
        option_tab3.find('.role_based_pricing_html').empty();
        option_tab4.find('.attribute_image_html').empty();
        option_tab5.find('.upload_combination_video_html').empty();
        option_tab5.find('.attribute_video_html').empty();

        option_foot.find('.save_option_html').empty();

        let input_foot = frappe.ui.form.make_control({
            df: {
                "fieldtype": "Button",
                "label": __("Save"),
                "fieldname": "save_option"
            },
            parent: option_foot.find('.save_option_html'),
        })
        input_foot.make_input();
        input_foot.$wrapper.find('button').addClass("btn-primary");
        input_foot.$wrapper.find('button').addClass("btn-sm");
        input_foot.$wrapper.find('button').text("Save");
        let product_title = frappe.ui.form.make_control({
            df: {
                "fieldtype": "Data",
                "label": __("Product Title"),
                "fieldname": "product_title",
                "default": f.product_title,
                "onchange": function() {
                    let val = this.get_value();
                    f.product_title = val;
                }
            },
            parent: option_tab1.find('.product_title_html'),
            only_input: true,
            value: f.product_title
        })
        product_title.make_input();
        product_title.set_value(f.product_title);
        let stock = frappe.ui.form.make_control({
            df: {
                "fieldtype": "Data",
                "label": __("Stock"),
                "fieldname": "stock",
                "default": f.stock,
                "onchange": function() {
                    let val = this.get_value();
                    f.stock = val;
                }
            },
            parent: option_tab1.find('.stock_html'),
            only_input: true,
            value: f.stock
        })
        stock.make_input();
        stock.set_value(f.stock);
        let weight = frappe.ui.form.make_control({
            df: {
                "fieldtype": "Data",
                "label": __("Weight(In KG)"),
                "fieldname": "weight",
                "default": f.weight,
                "onchange": function() {
                    let val = this.get_value();
                    f.weight = val;
                }
            },
            parent: option_tab1.find('.weight_html'),
            only_input: true,
            value: f.weight
        })
        weight.make_input();
        weight.set_value(f.weight);
        let price = frappe.ui.form.make_control({
            df: {
                "fieldtype": "Data",
                "label": __("Price"),
                "fieldname": "price",
                "default": f.price,
                "onchange": function() {
                    let val = this.get_value();
                    f.price = val;
                }
            },
            parent: option_tab1.find('.price_html'),
            only_input: true,
            value: f.price
        })
        price.make_input();
        price.set_value(f.price);
        let sku = frappe.ui.form.make_control({
            df: {
                "fieldtype": "Data",
                "label": __("SKU"),
                "fieldname": "sku",
                "default": f.sku,
                "read_only":1,
                "onchange": function() {
                    let val = this.get_value();
                    f.sku = val;
                }
            },
            parent: option_tab1.find('.sku_html'),
            only_input: true,
            value: f.sku
        })
        sku.make_input();
        sku.set_value(f.sku);
        // let data = JSON.parse(f.role_based_pricing)||[];
        
            me.pricing_html(f)
       

        let attribute_image_html = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __(""),
                "fieldname": "attribute_image_html"
            },
            parent: option_tab4.find('.attribute_image_html'),
            only_input: true
        })

        let upload_combination_video = frappe.ui.form.make_control({
            df: {
                "fieldtype": "Button",
                "label": __("Upload Video"),
                "fieldname": "upload_combination_video"
            },
            parent: option_tab5.find('.upload_combination_video_html'),
            only_input: true
        })
        upload_combination_video.make_input();
        upload_combination_video.$wrapper.find('button').addClass("btn-primary");
        upload_combination_video.$wrapper.find('button').addClass("btn-sm");
        upload_combination_video.$wrapper.find('button').text("Upload Video");

        // let add_combination_video = frappe.ui.form.make_control({
        //     df: {
        //         "fieldtype": "Button",
        //         "label": __("Add / Edit Video"),
        //         "fieldname": "add_combination_video"
        //     },
        //     parent: option_tab5.find('.add_combination_video_html'),
        //     only_input: true
        // })
        // add_combination_video.make_input();
        // add_combination_video.$wrapper.find('button').addClass("btn-primary");
        // add_combination_video.$wrapper.find('button').addClass("btn-sm");
        // add_combination_video.$wrapper.find('button').text("Add / Edit Video");

        let attribute_video_html = frappe.ui.form.make_control({
            df: {
                "fieldtype": "HTML",
                "label": __(""),
                "fieldname": "attribute_video"
            },
            parent: option_tab5.find('.attribute_video_html'),
            only_input: true
        })
        option_tab4.find('.add_combination_image_html').find('button[data-fieldname="add_combination_image"]').click(function() {   
            var attributeId = f.name;
            if (attributeId) {
                let attribute_info = frappe.get_doc(f.doctype, f.name);
                localStorage.setItem('randomuppy', ' ');
                cur_frm.events.generate_combination_image_html(cur_frm, 'Product Variant Combination', attributeId, attribute_info)
                cur_frm.events.image_upload(cur_frm, 'Product Variant Combination', attributeId, "combination_images", 'Product Variant Combination', attributeId)
            } else {
                frappe.throw('Please save the document and then try uploading images')
            }
        })

        // option_tab5.find('.add_combination_video_html').find('button[data-fieldname="add_combination_video"]').click(function() {   
        //         var attributeId1 = f.name;
        //         if (attributeId1) {
        //             if (attributeId1) {

        //                 let video_dialog = new frappe.ui.Dialog({
        //                     title: 'Attribute Video',
        //                     fields: [{
        //                         "fieldname": "video_id",
        //                         "fieldtype": "Data",
        //                         "label": __("Video url")
        //                     }, {
        //                         "fieldname": "video_type",
        //                         "fieldtype": "Select",
        //                         "label": __("Video Type"),
        //                         "options": "Youtube\nVimeo\nOther",
        //                         "default": "Youtube"
        //                     }],
        //                     primary_action_label: __('Close')
        //                 });
        //                 video_dialog.show();
        //                 video_dialog.set_primary_action(__('Add'), function () {
        //                     var html = '<table class="table table-bordered" id="OptionsData1"><thead style="background: #F7FAFC;"><tr><th width="65%">Video url</th><th>Type</th><th>Actions</th></tr></thead>';
        //                     let values = video_dialog.get_values();
        //                     frappe.call({
        //                         method: "go1_commerce.go1_commerce.doctype.product.product.insert_attribute_option_video",
        //                         args: {
        //                             "option_id": attributeId1,
        //                             "video_id": values.video_id,
        //                             "video_type": values.video_type
        //                         },
        //                         callback: function (r) {
        //                             if (r.message != undefined) {
        //                                 $.each(r.message, function (i, j) {
        //                                     html += '<tr id="tr-' + j.name + '"><td><i class="fa fa-file-video-o" aria-hidden="true"></i><span style="padding-left: 5px;">' + j.youtube_video_id + '</span></td><td>' + j.video_type + '</td>';
        //                                     // html += ' <td><button class="btn btn-xs btn-success editbtn"  data-fieldtype="Button" onclick=EditAttributeOptionVideo("' + j.name + '","' + j.option_id + '")>Edit</button><a class="btn btn-xs btn-danger" style="margin-left:10px;" onclick=DeleteAttributeOptionVideo("' + j.name + '")>Delete</a></td></tr>';
        //                                     html += ' <td><a class="btn btn-xs btn-danger" style="margin-left:10px;" onclick=DeleteAttributeOptionVideo("' + j.name + '")>Delete</a></td></tr>';
        //                                 });
        //                             } else {
        //                                 html += '<tr><td colspan="6" align="center">No Records Found.</td></tr>';
        //                             }
        //                             html += '</tbody>';
        //                             html += '</table>';
        //                             dialog.fields_dict.attribute_video.$wrapper.html(html);
        //                             video_dialog.hide();
        //                         }
        //                     })
        //                 })
        //             }
        //         } else {
        //             frappe.throw('Please save the document and then try add video id')
        //         }
        //     })

        option_tab5.find('.upload_combination_video_html').find('button[data-fieldname="upload_combination_video"]').click(function() {   
            new AttributeVideoUploader({
                frm: cur_frm,
                attributeId: f.name
            })
        })
        get_attribute_images(me.combination, me.combination_table)
        get_attribute_videos(me.combination)
    },
    pricing_html: function(f) {
        let me = this;
        let data;
        
        if(f.role_based_pricing){
            data = JSON.parse(f.role_based_pricing);
        }else{
            data = [];
        }
       
        let index = me.frm.doc.variant_combination.findIndex(x => x.idx == f.idx);
        var varient = me.dialog.fields_dict["varient_tab"].$wrapper
        var option_tab3 =  varient.find('#optionTable3');
        let wrapper = option_tab3.find('.role_based_pricing_html').empty();
        let table = $(`<table class="table table-bordered">
                <thead style="background: #F7FAFC;">
                    <tr>
                        <th>Role</th>
                        <th>Price</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table><div><button class="btn btn-primary btn-sm" name="add_item" id="add_row_item">Add Row</button></div>`).appendTo(wrapper);
            if (data.length <= 0) {
                let args = {
                    'dt': 'Order Settings',
                    'business': cur_frm.doc.restaurant
                };
                let order = cur_frm.events.get_settings(cur_frm, args);
               
                if(order && order.franchise_role){
                    data.push({"role":order.franchise_role, "price":0, "idx":1});
                }
            }
          
            if (data && data.length > 0) {
            data.map(f => {
                let role = f.role;
                let price = f.price;
                // <td>${__(role)}</td>
                // <td>${__(price)}</td>
                let row = $(`<tr data-idx="${f.idx}"">
                        <td><div class="slide-input"></div></td>
                        <td><div class="slide-price-input"></div></td>
                        <td style="width: 10%;"><button class="btn btn-danger btn-xs"><span class="fa fa-times"></span></button></td>
                    </tr>`);
                let input = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "Link",
                        "label": __("Role"),
                        "fieldname": "role",
                        "placeholder": __(`Select Role`),
                        "options": "Role",
                        "default": role,
                        "onchange": function() {
                            let val = this.get_value();
                            if (val) {
                                data[f.idx-1]['role']=val;
                                me.frm.doc.variant_combination[index]["role_based_pricing"]=JSON.stringify(data);    
                            }
                        }
                    },
                    "get_query": function() { 
                        return {
                            query: "go1_commerce.go1_commerce.doctype.product.product.get_role_list",
                            filters: {}
                        };
                    },
                    parent: row.find('.slide-input'),
                    only_input: true,
                    value: role
                });
                input.make_input();
                input.set_value(role);

                let input1 = frappe.ui.form.make_control({
                    df: {
                        "fieldtype": "Currency",
                        "label": __("Price"),
                        "fieldname": "price",
                        "options": "",
                        "default": price,
                        "onchange": function() {
                            let val = this.get_value();
                          
                            if (val) {
                                data[f.idx-1]['price']=val;
                                me.frm.doc.variant_combination[index]["role_based_pricing"]=JSON.stringify(data);
                                
                            }
                        }
                    },
                    "get_query": function() {},
                    parent: row.find('.slide-price-input'),
                    only_input: true,
                    value: price
                });
                input1.make_input(); 
                input1.set_value(price);
                table.find('tbody').append(row);

                row.find('.btn-danger').click(function() {
                    let obj = data.filter(o => o.idx != f.idx);
                    $(obj).each(function(k, v) {
                        v.idx = (k + 1);
                    })
                    data = obj;
                    me.frm.doc.variant_combination[index]["role_based_pricing"]=JSON.stringify(data)
                    
                        me.pricing_html(data);
                    
                });
            })
        } else {
            table.find('tbody').append(`<tr data-type="noitems"><td colspan="3">Records Not Found!</td></tr>`);
        }
        table.find('#add_row_item').on("click",function() {
            let idx = data.length + 1;
            let arr = {};
            arr["role"] = "";
            arr["price"] = 0;
            arr['idx'] = idx;
            data.push(arr);
            let cur_index = data.findIndex(x => x.idx == idx);
            let values = {};
            let new_row = $(`<tr data-idx="${idx}">
                    <td><div class="slide-input"></div></td>
                    <td><div class="slide-price-input"></div></td>                    
                    <td><button class="btn btn-danger btn-xs"><span class="fa fa-times"></span></button></td>
                </tr>`);
            let input = frappe.ui.form.make_control({
                df: {
                    "fieldtype": "Link",
                    "label": __("Role"),
                    "fieldname": "role",
                    "placeholder": __(`Select Role`),
                    "options": "Role",
                    "onchange": function() {
                        let val = this.get_value();
                        if (val) {
                           data[cur_index]['role']=val
                            me.frm.doc.variant_combination[index]["role_based_pricing"]=JSON.stringify(data)
                               
                        }
                    }
                },
                "get_query": function() { 
                        return {
                            query: "go1_commerce.go1_commerce.doctype.product.product.get_role_list",
                            filters: {}
                        };
                    },
                parent: new_row.find('.slide-input'),
                only_input: true,
            });
            table.find('tr[data-type="noitems"]').remove();
            table.find('tbody').append(new_row);
            input.make_input();

            let input1 = frappe.ui.form.make_control({
                df: {
                    "fieldtype": "Currency",
                    "label": __("Price"),
                    "fieldname": "price",
                    "options": "",
                    "onchange": function() {
                        let val = this.get_value();
                        if (val) {
                            data[cur_index]['price']=val
                            me.frm.doc.variant_combination[index]["role_based_pricing"]=JSON.stringify(data)
                        }
                    }
                },
                "get_query": function() {},
                parent: new_row.find('.slide-price-input'),
                only_input: true,
            });
            table.find('tr[data-type="noitems"]').remove();
         
            table.find('tbody').append(new_row);
            input1.make_input(); 
           
            new_row.find('.btn-danger').click(function() {
                let obj = data.filter(o => o.idx != idx);
                $(obj).each(function(k, v) {
                    v.idx = (k + 1);
                })
                data = obj;
                me.frm.doc.variant_combination[index]["role_based_pricing"]=JSON.stringify(data)
                table.find('tbody').find('tr[data-idx="'+idx+'"]').remove();
                if(data.length==0){
                    table.find('tbody').append(`<tr data-type="noitems"><td colspan="3">Records Not Found!</td></tr>`);
                }
            });
        })
    }
})
$(document).ready(function(){
    $('[data-fieldname="establishment_year"]').keyup(function(e)
                                {
  if (/\D/g.test(this.value))
  {
    // Filter non-digits from input value.
    this.value = this.value.replace(/\D/g, '');
  }
});
})

function DeleteAttributeOptionVideo(video_id,optionId){
    frappe.call({
        method: 'go1_commerce.go1_commerce.doctype.product.product.delete_product_attribute_option_video',
        args: {
            name:video_id
        },
        callback: function (r) {
           if(r && r.message && r.message.status == "Success"){
                frappe.show_alert({
                    message:__('Video deleted successfully.'),
                    indicator:'green'
                }, 5);
                let tr_length = $(`.attribute_video_html [data-fieldname="attribute_video"] [id="tr-${video_id}"]`).parent().find('tr').length
                if(tr_length == 1){
                   $(`.attribute_video_html [data-fieldname="attribute_video"] [id="tr-${video_id}"]`).parent().html('<tr><td colspan="6" align="center">No Records Found.</td></tr>');
                }
                else{
                    $(`.attribute_video_html [data-fieldname="attribute_video"] [id="tr-${video_id}"]`).remove();
                }
           }
           else{
                frappe.msgprint("Something went wrong.")
           }
        }
    });
}