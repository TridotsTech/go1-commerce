// Copyright (c) 2019, sivaranjani and contributors
// For license information, please see license.txt


frappe.require("assets/go1_commerce/css/select_list.css");


frappe.ui.form.on('Return Request', {
	onload: function(frm) {
		frm.add_fetch("price_list", "buying", "buying");
		frm.add_fetch("price_list", "selling", "selling");
		frm.add_fetch("price_list", "currency", "currency");
        frm.trigger('attach_attr_opts')
	},
    refresh(frm){
        frm.events.filter_link_field_data(frm)
        frm.events.add_status_custom_btn_and_ship_rocket(frm)
        frm.trigger('shipments')
        frm.trigger('set_order_item_query')
    },
    filter_link_field_data(frm){
        frm.set_query("order_id", function() {
            return {
                'query': "go1_commerce.go1_commerce.doctype.return_request.return_request.get_eliglible_orders",
                "filters": {
                    "return_type": frm.doc.type
                }
            }
        });
        frm.fields_dict['items'].grid.get_field('order_item').get_query = function(doc, cdt, cdn) {
            return{
                'query': "go1_commerce.go1_commerce.doctype.return_request.return_request.get_order_items",
                "filters": {
                    "order_id":frm.doc.order_id,
                    "return_type": frm.doc.type,
                    "return_created":0
                }
            }  
         }
    },
    add_status_custom_btn_and_ship_rocket(frm){
		if (!frm.doc.__islocal){
			if(frm.doc.next_status_level){
                frappe.call({
                    method: "go1_commerce.go1_commerce.doctype.return_request.return_request.get_nextstatus",
                    args: {
                        next_status_level: frm.doc.next_status_level
                    },
                    callback: function(data) {
                        console.log(data.message)
                        if(data.message){
                            frm.clear_custom_buttons();
                            $.each(data.message, function (i, c) {
                                frm.add_custom_button(__(c.name), function() {
                                    frappe.db.set_value('Return Request', frm.doc.name, 'status', c.name)
                                    .then(r => {
                                        cur_frm.reload_doc()
                                    })
                                })
                            })
                        }
                    }
                })
            }

		}
    },
    shipments: function(frm) {
		let allow = true;
		let show_shipment = 0;
		frappe.call({
		    method: 'go1_commerce.go1_commerce.doctype.return_request.return_request.get_returnorder_shipments',
		    args: { "name": frm.doc.name},
		    async: false,
		    callback: function(data) {
		        if (data.message && data.message.length>0){
		            show_shipment = 1;
		        }
		    }
		});
		if (show_shipment == 1 && allow == true && frm.doc.docstatus == 1) {
		    frm.toggle_display(['section_break_104'], true)
		    frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.return_request.return_request.get_returnshipments',
                args: {'document_type': frm.doctype,'document_name': frm.doc.name},
                async: false,
                callback: function(r) {
                    if(r.message) {
                        let wrapper = $(frm.get_field('shipments').wrapper).empty();
                        let html = $(`<table class="table table-bordered">
                            <thead>
                                <tr>
                                    <th>${__("Tracking Details")}</th>
                                    <th>${__("Shipped Date")}</th>
                                //  <th >${__("Delivered Date")}</th>
                                    <th>${__("Status")}</th>
                                </tr>
                            </thead>
                            <tbody></tbody>
                            </table>`).appendTo(wrapper);
                        let f = r.message
                        let shipped_date = frappe.datetime.get_datetime_as_string(f.shipped_date);
                        let delivered_date = ''
                        let driver = '';
                        let tracking_number = '';
                        let tracking_link = '';
                        if(f.delivered_date){
                            delivered_date = frappe.datetime.get_datetime_as_string(f.delivered_date);
                        }
                        if(f.driver){
                            driver = `<div><b>Driver</b>: ${f.driver || ''}</div>`;
                        }
                        if(f.tracking_number){
                            tracking_number = `<div><b>Tracking Number</b>: ${f.tracking_number}</div>`;
                        }
                        if(f.tracking_link){
                            tracking_link = `<div><b>Tracking Link</b>: ${f.tracking_link}</div>`;
                        }
                        let row = $(`<tr>
                                <td>
                                    ${tracking_number}
                                    ${tracking_link}
                                    ${driver}
                                </td>
                                <td>${shipped_date}</td>
                                //<td >${delivered_date}</td>
                                <td>${f.status}</td>
                            </tr>`)
                        html.find('tbody').append(row);
                    
                    }
                }
		    })
		} 
        else {
		    frm.toggle_display(['section_break_104'], false)
		}
	},
    set_order_item_query(frm){
        frm.set_query("order_item", () => {
            return{
                'query': "go1_commerce.go1_commerce.doctype.return_request.return_request.get_order_items",
                "filters": {
                    "order_id":frm.doc.order_id,
                    "return_type": frm.doc.type,
                    "return_created":0
                }
            }    
        });
    },
    attach_attr_opts(frm){
        if(cur_frm.doc.attribute_description){
            $('[id="page-Return Request"] [data-fieldname="attribute_html"]').html(cur_frm.doc.attribute_description)
        }
        else{
            $('[id="page-Return Request"] [data-fieldname="attribute_html"]').empty()
        }
    },
    attribute_id:function(frm){
        if(frm.doc.attribute_id && frm.doc.order_id && frm.doc.product){
            frappe.call({
                method: "go1_commerce.go1_commerce.doctype.return_request.return_request.get_attributes_combination_html",
                args: {
                    product: frm.doc.product,
                    orderid:frm.doc.order_id,
                    attribute: frm.doc.attribute_id
                },
                callback: function(r) {
                    if(r.message){
                        if(r.message[0]){
                            frm.set_value('attribute_description',r.message[0])
                            refresh_field('attribute_description')
                            frm.trigger('attache_attr_opts')
                        }
                        if(r.message[1]){
                            frm.set_value("quantity", r.message[1])
                        }   
                    } 
                }
            });
        }
    },
    order_item(frm){
        if(frm.doc.order_item){
            frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.return_request.return_request.get_order_item_info',
                args: {order_item:frm.doc.order_item},
                async: false,
                callback: function(d) {
                    if(d && d.status == 'success'){
                        frm.set_value('customer',d.message.customer)
                        refresh_field('customer')
                        frm.set_value('product',d.message.item)
                        refresh_field('product')
                        frm.set_value('product_name',d.message.item_name)
                        refresh_field('product_name')
                        frm.set_value('customer_email',d.message.customer_email)
                        refresh_field('customer_email')
                        frm.set_value('attribute_id',d.message.attribute_ids)
                        refresh_field('attribute_id')
                        frm.set_value('attribute_description',d.message.attribute_description)
                        refresh_field('attribute_description')
                        frm.set_value('customer_name',d.message.customer_name)
                        refresh_field('customer_name')
                        frm.set_value('quantity',d.message.quantity)
                        refresh_field('quantity')
                    }
                    else{
                        if(d){
                            frappe.msgprint(d.message)
                        }
                        else{
                            frappe.msgprint('Something went wrong not able to fetch <b>Product</b> details..!')
                        }
                    }
                }
            })
        }
        else{
            frm.events.delete_field_values(frm,'Order Item')
        }
    },
    delete_field_values(frm,type__){
        if(type__ == 'Order ID'){
            frm.set_value('order_item','')
            refresh_field('order_item')    
        }
        frm.set_value('customer','')
            refresh_field('customer')
        frm.set_value('product','')
            refresh_field('product')
        frm.set_value('product_name','')
            refresh_field('product_name')
        frm.set_value('customer_email','')
            refresh_field('customer_email')
        frm.set_value('attribute_id','')
            refresh_field('attribute_id')
        frm.set_value('attribute_description','')
            refresh_field('attribute_description')
        frm.set_value('customer_name','')
            refresh_field('customer_name')
        $('[id="page-Return Request"] [data-fieldname="attribute_html"]').empty()
    },
    order_id: function(frm){
        frm.events.delete_field_values(frm,'Order ID')
	},
    select_shipment_method: function(frm) {
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.return_request.return_request.get_return_order_items',
            args: { "returnId": frm.doc.name, 'fntype': "shipped"},
            async: false,
            callback: function(data) {
                if (data.message) {
                    frm.shipped_items_list = data.message;
                }
            }
        })
        let shipment_dialog = new frappe.ui.Dialog({
            title: 'Shipping Providers',
            fields: [
                {
                "fieldname": "shipping_providers_html",
                "fieldtype": "HTML"
                }],
            primary_action_label: __('Close')
        });
        shipment_dialog.show();
        setTimeout(function(){
            cur_frm.trigger('get_shipment_providers');
        }, 500);  
    },
    get_shipment_providers: function(){
        cur_dialog.fields_dict["shipping_providers_html"].$wrapper.html('');
        var drp_html ='<div class="select_list">'
        frappe.call({
            method: "shipping_providers.shipping_providers.api.shipping_providers_list",
            args: {},
            async: false,
            callback: function(r) {
                if(r && r.message != "no providers found"){
                    if(r.message.length>0){
                            var groups = {};
                            var myArray = r.message
                            for (var i = 0; i < myArray.length; i++) {
                              var groupName = myArray[i].type;
                              if (!groups[groupName]) {
                                groups[groupName] = [];
                              }
                              groups[groupName].push(myArray[i].provider_name);
                            }
                            myArray = [];
                            for (var groupName in groups) {
                              myArray.push({group: groupName, provider_name: groups[groupName]});
                            }
                            for (var i = 0; i < myArray.length; i++) {
                                drp_html += '<h4>'+myArray[i].group+'</h4><ul>'
                                var provider_type = (myArray[i].group).replace(" ","_")
                                var providers = myArray[i].provider_name
                                for (var j = 0; j < providers.length; j++) {
                                    let providerid = providers[j].replace(" ","_")
                                    drp_html += '<li>'+providers[j]+'<span data-id='+providerid+' data-type='+provider_type+' class="tick"><button class="btn info">Select</button></span></li>'
                                    if(j == providers.length-1){
                                        drp_html +='</ul>'
                                    }
                                }
                            }
                        }
                        else{
                            cur_dialog.$wrapper.remove()
                            frappe.throw("No shipping providers configured")
                        }
                    }
                    else{
                        cur_dialog.$wrapper.remove()
                        frappe.throw("No shipping providers configured")
                        }
                }
            });
            drp_html +='</div>'
            cur_dialog.fields_dict["shipping_providers_html"].$wrapper.append(drp_html);
            var tick_buttons = cur_dialog.fields_dict["shipping_providers_html"].$wrapper.find('span.tick');
            if (tick_buttons){
                for (var k = 0; k < tick_buttons.length; k++) {
                  tick_buttons[k].addEventListener("click", function() {
                    var shipping_provider_id = $(this).attr('data-id')
                    let provider_type = $(this).attr('data-type').replace("_"," ")
                    frappe.shipping_provider = (shipping_provider_id).replace("_"," ")
                        frappe.confirm(__("Are you sure want to proceed shipping with '"+frappe.shipping_provider+"'?"), () => {
                            if(provider_type == "Shipping Aggregator"){
                                cur_frm.trigger('check_shipment_provider');
                            }
                            else{
                                cur_frm.trigger('select_shipping_driver');
                            }
                        });
                  });
                }
            }
    },
    check_shipment_provider: function(frm){
        frappe.call({
            method: 'shipping_providers.shipping_providers.api.check_provider_settings',
            args: {'provider':frappe.shipping_provider,'orderid':cur_frm.doc.name},
            callback: function(d) {
                if(d.message=="success"){
                    cur_frm.trigger('use_shipment_provider');
                }
            }
        });
    },
    use_shipment_provider: function(frm){
        var settings_doctype = doctype.replace(" ","_")
        var method = 'shipping_providers.shipping_providers.doctype.'+settings_doctype+'.'+settings_doctype+'.make_returnshipment';
        frappe.call({
            method: method,
            args: {'returnId':cur_frm.doc.name},
            callback: function(r) {
                if(!r.exc_type) {
                    cur_dialog.$wrapper.remove();
                    cur_frm.trigger('insert_shipment');
                }
            }
        });
    },
    select_shipping_driver(frm){
        cur_dialog.$wrapper.remove()
        let shipment_dialog = new frappe.ui.Dialog({
                title: 'Shipping Drivers',
                fields: [
                    {
                    "fieldname": "drivers_html",
                    "fieldtype": "HTML"
                    }
                    ],
                primary_action_label: __('Close')
            });
            shipment_dialog.show();
            setTimeout(function(){
                cur_frm.trigger('generate_drivers_html');
            }, 500);
    },
    generate_drivers_html(frm){
        let wrapper = $(cur_dialog.get_field('drivers_html').wrapper).empty();
        let table_html = $(`<table class="table table-bordered" style="cursor:auto; margin:0px;">
            <thead style="background-color: #f0f4f7;">
                <tr>
                    <th style="width: 40%">Driver</th>
                    <th>Status</th>
                    <th align="center" style="width:8%;">Select</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
        <a style="float:right;padding-top:10px;" id="without_driver">Proceed without selecting driver >></a>`).appendTo(wrapper);
        frappe.call({
            method: 'shipping_providers.shipping_providers.api.get_drivers',
            args: {'name':frappe.shipping_provider},
            async: false,
            callback: function(d) {
                if (d && d.message.length > 0) {
                    d.message.map(f => {
                        if (f) {
                            if (f.working_status == "Available"){
                                let row_data = $(`<tr>
                                    <td>${f.driver_name}</td>
                                    <td>${f.working_status}</td>
                                    <td align="center"><span data-id="${f.name}" style="cursor:pointer" class="select_list"><button class="btn info">Select</button></span></td>
                                </tr>`);
                                table_html.find('tbody').append(row_data);
                            }else{
                                let row_data = $(`<tr>
                                    <td>${f.driver_name}</td>
                                    <td>${f.working_status}</td>
                                    <td align="center"></td>
                                </tr>`);
                                table_html.find('tbody').append(row_data);
                            }
                            
                        }
                    })
                }else{
                    let row_data = $(`<tr>
                        <td colspan="3" align="center">No drivers mapped for this provider</td>
                        </tr>`);
                    table_html.find('tbody').append(row_data);
                }
            }
        });
        frappe.shipping_driver = ''
        var driver_buttons = cur_dialog.fields_dict["drivers_html"].$wrapper.find('span.select_list');
        if (driver_buttons){
            for (var k = 0; k < driver_buttons.length; k++) {
              driver_buttons[k].addEventListener("click", function() {
                var shipping_driver_id = $(this).attr('data-id')
                    frappe.confirm(__("Are you sure want to assign this driver?"), () => {
                        frappe.shipping_driver = shipping_driver_id
                        cur_frm.trigger('return_readyto_shipped');
                    });
              });
            }
        }
        var link = cur_dialog.fields_dict["drivers_html"].$wrapper.find('a#without_driver')
        link.click(function() {
            frappe.confirm(__("Are you sure want to proceed without driver?"), () => {
                cur_frm.trigger('return_readyto_shipped');
            });
        });
    },
    
});

frappe.ui.form.on("Return Request Item", {
    order_item: function(frm, cdt, cdn) {
        var child = locals[cdt][cdn];
         frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.return_request.return_request.get_order_item_info',
                args: {order_item:child.order_item},
                async: false,
                callback: function(d) {
                    if(d && d.status == 'success'){
                        frappe.model.set_value(cdt, cdn, "product", d.message.item);
                        frappe.model.set_value(cdt, cdn, "product_name", d.message.item_name);
                        frappe.model.set_value(cdt, cdn, "attribute_description", d.message.attribute_description);
                        frappe.model.set_value(cdt, cdn, "attribute_id", d.message.attribute_ids);
                        frappe.model.set_value(cdt, cdn, "quantity", d.message.quantity);
                    }
                    else{
                        if(d){
                            frappe.msgprint(d.message)
                        }
                        else{
                            frappe.msgprint('Something went wrong not able to fetch <b>Product</b> details..!')
                        }
                    }
                }
            })
    }
});