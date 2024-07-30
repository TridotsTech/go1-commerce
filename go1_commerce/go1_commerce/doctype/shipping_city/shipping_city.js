
// Copyright (c) 2019, Tridots Tech and contributors
// For license information, please see license.txt
frappe.require("assets/go1_commerce/css/toggle-slider.css");
frappe.ui.form.on('Shipping City', {
	refresh: function(frm) {
		if( frappe.session.user == 'Administrator' || frappe.user.has_role('Admin')) {
            frm.set_df_property('business', 'hidden', 0);
        } 
        else {
            frm.set_df_property('business', 'hidden', 1);
        }
		frm.trigger('generate_area_html')
		$('button[data-fieldname="add_area"]').css({"background":"#1b8fdb", "color":"white",
                "padding":"5px 10px"});
		$('button[data-fieldname="add_newarea"]').css({"background":"#1b8fdb", "color":"white",
                "padding":"5px 10px","float":"right","position":"absolute","right":"15px","top":"0px"});
	},
	generate_area_html: function(frm){
		frappe.areas = []
		frappe.zipcodes = []
		frappe.run_serially([
			() => {
            	if (!frm.doc.__islocal) {
                	frm.trigger('get_entered_zipcodes')
                }
            },
            () => {
            	if (!frm.doc.__islocal) {
                	frm.trigger('get_all_areas')
                }
            },
            () => {
            	let wrapper = $(frm.get_field('area_table_html').wrapper).empty();
        		let table_html = ""
	        		table_html = $(`<table class="table table-bordered" style="cursor:pointer; margin:0px;">
		                <thead>
		                    <tr>
		                        <th style="width: 8%;">S.no</th>
		                        <th>Area</th>
		                        <th style="width:35%;">Zipcode</th>
		                    </tr>
		                </thead>
		                <tbody></tbody>
		            </table>`).appendTo(wrapper);
		            if (frappe.areas.length > 0) {
		            	var s_no = 0;
			            frappe.areas.map(f => {
			                s_no += 1;
			                f.s_no = s_no;
			                let row_data = ""
			                    row_data = $(`<tr data-id="${f.name}" data-idx="${f.idx}">
			                        <td>${f.s_no}</td>
			                        <td>${f.area}</td>
			                        <td>${f.zipcode}</td>
			                    </tr>`);
			                table_html.find('tbody').append(row_data);
			            });
			        } else {
			            table_html.find('tbody').append(`<tr><td colspan="3" align="center">No records found!</td></tr>`);
			        }
                
            }
        ])

	},
	get_entered_zipcodes: function(frm){
  		var existing_codes = cur_frm.doc.zipcode_range;
        frappe.zipcodes = existing_codes.split(',');
	},
	get_all_areas: function(frm){
        if(frm.doc.zipcode_range){
            frappe.call({
                        method: "go1_commerce.go1_commerce.doctype.shipping_city.shipping_city.get_areas_fromziprange",
                        args: {
                            "ziprange": frm.doc.zipcode_range
                        },
                        async: false,
                        callback: function(res) {
                            if(res.message){
                                frappe.areas = res.message
                            }
                        }
            });
        }
	},
	add_newarea: function(frm){
		var doc = frappe.model.get_new_doc('Area');
        window.open(window.location.origin+`/app/area/${doc.name}`, '_blank');
	},
	add_area: function(frm) {
        frappe.run_serially([
            () => {
            },
            () => {
                $('.modal').empty();
                $('.modal').removeClass('in');
                area_dialog(frm)
            }
        ])
    },
	build_multi_selector(frm, possible_val) {
        $.each(possible_val, function(i, c) {
            var ref_fields = unescape(c.reference_fields)
            var ref_method = c.reference_method
            var field = c.tab_field
            var url = '/api/method/' + ref_method
            $.ajax({
                type: 'POST',
                Accept: 'application/json',
                ContentType: 'application/json;charset=utf-8',
                url: window.location.origin + url,
                data: {
                    "reference_doc": c.reference_doc,
                    "reference_fields": ref_fields,
                    "city": cur_frm.doc.core_city
                },
                dataType: "json",
                async: false,
                headers: {
                    'X-Frappe-CSRF-Token': frappe.csrf_token
                },
                success: function(r) {
                    var list_name = r.message.list_name;
                    if(list_name){
                        var drp_html = `
                            <button class="btn btn-default btn-xs" id="add_newarea" 
                                style="background: rgb(240, 244, 247); color: #36414c; padding: 5px 10px; 
                                    float: right;height: 28px;margin-bottom: 10px;">Add New Area
                            </button>
                            <div class="${c.cls}" style="padding: 0px;"> 
                                <div class="awesomplete"> 
                                    <input type="text"  class="multi-drp" id="myInput" autocomplete="nope" 
                                        onfocus="select_list_detail($(this))" onfocusout="disable_select_list($(this))" 
                                        onkeyup="selected_lists_values($(this))" placeholder="${c.title}" 
                                        title="${c.title}" style="background-position: 10px 12px;background-repeat: no-repeat;
                                        width: 100%;font-size: 16px;padding: 10px 15px 10px 10px;border: 1px solid #d1d8dd;
                                        border-radius: 4px !important;;margin: 0px;" data-class="${c.cls}" data-field="${c.tab_field}" 
                                        data-doctype="${c.doctype}" data-child="${c.is_child}" data-linkfield="${c.link_name}" 
                                        data-reference_doc="${c.reference_doc}" data-reference_fields="${c.reference_fields}" 
                                        data-search_fields="${c.search_fields}" data-reference_method="${c.reference_method}" 
                                        data-child_link="${c.child_tab_link}">
                                <div style="margin:10px 0px;float:left;width:100%">
                                    <span style="float:right;padding: 2px 10px;">
                                        <input type="checkbox" id="selectAll" name="selectAll" 
                                            style="">
                                    </span>
                                    <span style="float:right;">
                                        <label for="selectAll" style="font-weight:400;">
                                            Select all available areas
                                        </label>
                                    </span>
                                </div>
                                <h4 style="padding: 10px 10px;border: 1px solid #ddd;border-bottom: none;margin: 40px 0px 0px 0px;
                                    background: #f8f8f8;">${c.label}
                                </h4>
                                <ul role="listbox" id="assets" class= "assets" style="list-style-type: none;
                                    position: absolute;width: 100%;margin: 0;background: rgb(255, 255, 255);
                                    min-height:270px;height:270px;box-shadow:none;">
                            `
                        var k = 0
                        $.each(list_name, function(i, v) {
                            if (v[c.link_name]) {
                                k += 1
                                let arr;
                                if (parseInt(v[c.is_child]) == 1) {
                                    var cur_row = frappe.get_doc(doctype_name, selected);
                                    arr = JSON.parse(cur_row[field]);
                                }
                                else {
                                    arr = JSON.parse(cur_dialog.fields_dict[field].get_value());
                                }
                                if ($.inArray(v[c.link_name], arr) == -1) {
                                    drp_html += '<li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;"><a style="display: none;"><strong>' + v[c.link_name] + '</strong></a><label class="switch" style="float:right; margin:0px; cursor:pointer;"><input type="checkbox" class="popupCheckBox" name="vehicle1" value="0" id="' + v[c.link_name] + '" data-doctype="' + c.doctype + '" data-child="' + c.is_child + '" data-reference_doc="' + c.reference_doc + '" data-reference_fields="' + c.reference_fields + '" data-search_fields="' + c.search_fields + '"  data-business="' + c.business + '" data-child_link="' + c.child_tab_link + '" onchange="selected_multiselect_lists($(this))"><span class=" slider round"></span></label><p style="font-size: 14px;">';
                                    if (v["parent_categories"]) {
                                        drp_html += '' + v["parent_categories"] + '</span></p></li>';                                 
                                    } 
                                    else {
                                        drp_html += '' + v[c.search_fields] + '</span></p></li>';                                  
                                    }
                                } else {
                                    drp_html += '<li style="display: block; border-bottom: 1px solid #dfdfdf; cursor:auto;"><a style="display: none;"><strong>' + v[c.link_name] + '</strong></a><label class="switch" style="float:right; margin:0px; cursor:pointer;"><input type="checkbox" class="popupCheckBox" name="vehicle1" value="0" id="' + v[c.link_name] + '" data-doctype="' + c.doctype + '" data-child="' + c.is_child + '" data-reference_doc="' + c.reference_doc + '" data-reference_fields="' + c.reference_fields + '" data-search_fields="' + c.search_fields + '"  data-business="' + c.business + '" data-child_link="' + c.child_tab_link + '" onchange="selected_multiselect_lists($(this))" checked><span class=" slider round"></span></label><p style="font-size: 14px;">';
                                    if (v["parent_categories"]) {
                                        drp_html += '' + v["parent_categories"] + '</span></p></li>';                   
                                    } 
                                    else {
                                        drp_html += '' + v[c.search_fields] + '</span></p></li>';                                 
                                    }
                                }
                            } else {
                                drp_html += '<li></li>';
                            }
                        })
                        drp_html += '</ul>';
                        drp_html += '</div></div><p class="help-box small text-muted hidden-xs">' + c.description + '</p>';
                        cur_dialog.fields_dict["area_html1"].$wrapper.append(drp_html);
                        cur_dialog.fields_dict["area_html1"].$wrapper.find('button#add_newarea').on('click', function() {
                            var doc = frappe.model.get_new_doc('Area');
                            window.open(window.location.origin+`/app/area/${doc.name}`, '_blank');
                        });
                        select_unselect_all(field)
                    }
                    else{
                        cur_dialog.fields_dict["area_html1"].$wrapper.append(`
                            <div class="no-data" style="position:relative;height:300px;">
                                <div class="no-records" style="position:absolute;left:45%;top:50%;">    
                                    <p>No Records Found..!</P>
                                </div>
                            </div>`);
                    }
                }
            })
        });
    }
});

function select_unselect_all(field){
    cur_dialog.fields_dict["area_html1"].$wrapper.find('input#selectAll').on('click', function() {
        let arr = JSON.parse(cur_dialog.fields_dict[field].get_value());
        if($(this).prop("checked") == true){       
            cur_dialog.fields_dict["area_html1"].$wrapper.find('input[name="vehicle1"]').each(function() {
                if($(this).prop("checked") == false){
                    $(this).prop("checked", true);
                    var values = $(this).attr('id');
                    if(values){
                        arr.push(values);
                        cur_dialog.get_field('area_json').set_value(JSON.stringify(arr));
                    }
                }
            });
        }
        else if($(this).prop("checked") == false){
            cur_dialog.fields_dict["area_html1"].$wrapper.find('input[name="vehicle1"]').each(function() {
                if($(this).prop("checked") == true){
                    $(this).prop("checked", false);
                    var values = $(this).attr('id');
                    if (jQuery.inArray(values, arr) != -1) {
                        arr = arr.filter(function(elem){
                        return elem != values; 
                        });
                        cur_dialog.get_field('area_json').set_value(JSON.stringify(arr));
                    }
                }
            });
        }
    });
}

function area_dialog(frm) {
    frm.possible_val = [{
        "cls": "custom-shipping-area",
        "tab_html_field": "area_html",
        "tab_field": "area_json",
        "link_name": "zipcode",
        "title": "Search area here...",
        "label": "Choose Area",
        "doctype": "Shipping City",
        "business": cur_frm.doc.business,
        "reference_doc": "Area",
        "reference_fields": escape(JSON.stringify(["name", "area", "city", "zipcode"])),
        "search_fields": "area",
        "reference_method": "go1_commerce.go1_commerce.doctype.shipping_city.shipping_city.get_area_list",
        "is_child": 0,
        "description": "Please select the areas.",
        "child_tab_link": "",
        "height": "180px"
    }];
    let categoryDialog;
    var content = []
    categoryDialog = new frappe.ui.Dialog({
        title: __('Select Areas'),
        fields: [{
                label: "Select Area",
                fieldtype: 'Table MultiSelect',
                fieldname: 'area_list',
                options: 'Area',
                hidden: 1
            },
            {
                label: "Select Area",
                fieldtype: 'HTML',
                fieldname: 'area_html1',
                options: ''
            },
            {
                label: "Select Area",
                fieldtype: 'Code',
                fieldname: 'area_json',
                options: '',
                read_only: 1,
                hidden: 1
            }
        ],
        primary_action_label: __('Close'),
    });
    if(frappe.zipcodes.length > 0){
	    $.each(frappe.zipcodes, function(i, s) {
	        content.push(s.toString())
	    })
	}
    categoryDialog.get_field('area_json').set_value(JSON.stringify(content));
    categoryDialog.get_field('area_json').refresh();
    categoryDialog.show();
    setTimeout(function() {
        frm.events.build_multi_selector(frm, frm.possible_val);
    }, 1000)
    categoryDialog.set_primary_action(__('Submit'), function() {
        var cat = categoryDialog.get_values();
        var cat_json = JSON.parse(cat.area_json);
        var zipcodes = '';
        $(cat_json).each(function(k, v) {
            zipcodes += v+','
        })
        zipcodes = zipcodes.replace(/,\s*$/, "");
        if (cat_json.length <= 0) {
            frappe.throw(__('Please select any one of the Area.'))
        } else {
        	cur_frm.set_value('zipcode_range', zipcodes)
            frm.refresh_field('zipcode_range')
            categoryDialog.hide();
            if (!frm.doc.__islocal)
                cur_frm.save();
        }
    })
    categoryDialog.$wrapper.find('.modal-dialog').css("min-width", "1000px");
    categoryDialog.$wrapper.find('.modal-content').css("min-height", "575px");
}
