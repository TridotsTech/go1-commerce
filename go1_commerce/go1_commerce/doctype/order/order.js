// Copyright (c) 2018, info@valiantsystems.com and contributors
// For license information, please see license.txt

// frappe.require("assets/go1_commerce/css/select_list.css"); 
// frappe.require("assets/go1_commerce/js/frappe-datatable.min.js");
// frappe.require("assets/go1_commerce/js/frappe-datatable.min.css");


frappe.ui.form.on('Order', {
    refresh: function(frm) {
        if (frm.doc.status =="Delivered" && frm.doc.payment_status == "Paid" && frm.doc.outstanding_amount ==0){
            frm.set_value("status","Completed");
            frm.save('Update');
        }
        order_detail_html_render(frm);
        validate_order_items(frm);
        validate_shipping_method(frm)
        validate_workflow(frm)
        validate_status(frm)
        validate_check_order_settings(frm)
        if (cur_frm.is_new()) {
            frm.set_df_property('commission_information_section', 'hidden', 1);
                if (frm.check_order_settings.allow_admin_to_create_order) {
                    frm.trigger('order_edit_options')
                }
        }
        if (!frm.invoiceid) {
            frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.order.order.get_order_settings',
                args: { "order_id": frm.doc.name, 'doctype': frm.doc.doctype },
                async: false,
                callback: function(d) {
                    if (d.message) {
                        data = d.message;
                        if (data.order_settings.enable_invoice == 1 && data.order_settings.automate_invoice_creation == 0 && frm.doc.docstatus == 1) {
                            frm.remove_custom_button('Make Invoice');
                            frm.add_custom_button("Make Invoice", function() {
                                frm.trigger("make_invoice");
                            });
                            $('button[data-label="Make%20Invoice"]').removeAttr("class");
                            $('button[data-label="Make%20Invoice"]').attr("class", "btn btn-xs btn-primary");
                            $('button[data-label="Make%20Invoice"]').html("<i class='fa fa fa-plus-circle' style='margin-right:5px'></i> Make Invoice");
                        }
                    }
                }
            })
            if (!frm.doc.__islocal) {
                frappe.call({
                    method: 'go1_commerce.go1_commerce.doctype.order.order.get_order_settings',
                    args: { "order_id": frm.doc.name, 'doctype': frm.doc.doctype },
                    callback: function(d) {
                        if (d.message) {
                            if (d.message.order_settings.allow_admin_to_edit_order) {
                                var allow_edit_order = 0;
                                if (d.message.order_settings.admin_order_edit_status.length > 0) {
                                    for (var i = 0; i < d.message.order_settings.admin_order_edit_status.length; i++) {
                                        if (d.message.order_settings.admin_order_edit_status[i].status == frm.doc.status) {
                                            allow_edit_order = 1;
                                        }
                                    }
                                }
                                if (allow_edit_order == 1) {
                                    frm.add_custom_button(__('Edit Order'), function() {
                                        frm.trigger('order_edit_options')
                                    });
                                    $('button[data-label="Edit%20Order"]').removeAttr("class");
                                    $('button[data-label="Edit%20Order"]').attr("class", "btn btn-xs btn-success");
                                    $('button[data-label="Edit%20Order"]').html("<i class='fa fa-pencil' style='margin-right:5px'></i> Edit Order");
                                    if (frm.doc.checkout_attributes.length > 0) {
                                        frm.add_custom_button(__('Edit Questionaries'), function() {
                                            frappe.run_serially([
                                                () => { frm.trigger('get_available_checkout_attributes'); },
                                                () => { frm.trigger('edit_order_checkout_attributes') }
                                            ]);
                                        });
                                        $('button[data-label="Edit%20Questionaries"]').removeAttr("class");
                                        $('button[data-label="Edit%20Questionaries"]').attr("class", "btn btn-xs btn-warning");
                                        $('button[data-label="Edit%20Questionaries"]').html("<i class='fa fa-question' style='margin-right:5px'></i> Edit Questionaries");
                                    }
                                }
                            }
                        }
                    }
                })
            }
        } else {
            frm.add_custom_button("View Invoice", function() {
                frappe.set_route('Form', "Sales Invoice", frm.invoiceid)
            });
            $('button[data-label="View%20Invoice"]').removeAttr("class");
            $('button[data-label="View%20Invoice"]').attr("class", "btn btn-xs btn-primary");
            $('button[data-label="View%20Invoice"]').html("<i class='fa fa fa-eye' style='margin-right:5px'></i> View Invoice");
        }
        if (frm.doc.docstatus == 1) {
            if (frm.doc.status == 'Delivered') {
                if (frm.order_settings.enable_invoice == 0) {
                    frm.remove_custom_button('Make Payment');
                    frm.add_custom_button("Make Payment", function() {
                        frm.trigger("make_payment");
                    });
                    $('button[data-label="Make%20Payment"]').removeAttr("class");
                    $('button[data-label="Make%20Payment"]').attr("class", "btn btn-xs btn-primary");
                    $('button[data-label="Make%20Payment"]').html("<i class='fa fa fa-plus-circle' style='margin-right:5px'></i> Make Payment");
                }
            } else {
                frm.remove_custom_button('Make Payment');
                $('button[data-label="Make%20Payment"]').removeAttr("class");
                $('button[data-label="Make%20Payment"]').attr("class", "btn btn-xs btn-primary");
                $('button[data-label="Make%20Payment"]').html("<i class='fa fa fa-plus-circle' style='margin-right:5px'></i> Make Payment");
            }
            if (cur_frm.doc.is_shipment_bag_item==1){
                frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.order.order.get_shipment_bag_id',
                args: {"order_id":cur_frm.doc.name},
                async: false,
                callback: function(d) {
                    if(d.message.status=="success"){
                        frm.add_custom_button("View Shipment Bag", function() {
                            window.location.href="/desk#Form/Shipment%20Bag/"+d.message.shipment_id;
                        });
                        $('button[data-label="View%20Shipment%20Bag"]').removeAttr("class");
                        $('button[data-label="View%20Shipment%20Bag"]').attr("class", "btn btn-xs btn-danger");
                        $('button[data-label="View%20Shipment%20Bag"]').html("<i class='fa fa-suitcase' style='margin-right:5px'></i>View Shipment Bag");
                        }
                    }
                })
            }
            
            if (frm.doc.status == 'Completed') {
                frappe.call({
                    method: 'go1_commerce.go1_commerce.doctype.order.order.get_order_settings',
                    args: { "order_id": frm.doc.name, 'doctype': frm.doc.doctype },
                    callback: function(d) {
                        if (d.message) {
                            if (d.message.order_settings.enable_returns_system) {
                                let returns = frm.doc.order_item.filter(obj => obj.return_created != 1);
                                if (returns && returns.length > 0) {
                                    frm.add_custom_button(__('Create Return'), function() {
                                        frm.trigger('create_return')
                                    });
                                    $('button[data-label="Create%20Return"]').attr("class", "btn btn-xs btn-primary");
                                    $('button[data-label="Create%20Return"]').html("<i class='fa fa fa-plus-circle' style='margin-right:5px'></i> Create Return");
                                }
                            }
                        }
                    }
                })
            }
            frm.set_df_property('payment_status', 'read_only', 1)
            frm.set_df_property('order_subtotal', 'read_only', 1)
        }
        cur_frm.set_query("status", function(frm) {
            return {
                query: "go1_commerce.go1_commerce.doctype.order.order.get_order_status",
                filters: {
                }
            }
        });
        var allow_admin_to_edit = 0
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.order.order.get_order_settings',
            args: { "order_id": frm.doc.name, 'doctype': frm.doc.doctype },
            async: false,
            callback: function(d) {
                if (d.message) {
                    if (d.message.allow_admin_to_edit_order == 1) {
                        allow_admin_to_edit = 1
                    }
                }
            }
        })
        if (frm.doc.__islocal && allow_admin_to_edit == 1) {
            frm.set_df_property('order_detail_html', 'hidden', 1)
            frm.set_df_property('sec_2', 'hidden', 0)
            frm.set_df_property('billing_section', 'hidden', 0)
            frm.set_df_property('shipping_section', 'hidden', 0)
            frm.set_df_property('sec_br', 'hidden', 0)
            frm.set_df_property('ec', 'hidden', 0)
            frm.set_df_property('order_item', 'readonly', 0)
        }

        if (!frm.doc.__islocal) {
            frm.set_df_property('order_item', 'readonly', 1)
        }
        if (frm.doc.__islocal && frm.check_order_settings.allow_admin_to_create_order == 1) {
            frm.set_df_property('order_detail_html', 'hidden', 1)
            frm.set_df_property('sec_2', 'hidden', 0)
            frm.set_df_property('billing_section', 'hidden', 0)
            frm.set_df_property('shipping_section', 'hidden', 0)
            frm.set_df_property('sec_br', 'hidden', 0)
            frm.set_df_property('ec', 'hidden', 0)
            frm.set_df_property('order_item', 'readonly', 0)
            frm.set_df_property('shipping_method_name', 'hidden', 0)
            frm.set_df_property('shipping_method_name', 'readonly', 1)
            frm.set_df_property('order_date', 'hidden', 1)
            frm.set_df_property('discount', 'hidden', 1)
            frm.set_df_property('shipping_method', 'hidden', 0);
            frm.set_df_property('payment_status', 'hidden', 1);
            frm.set_df_property('discount_coupon', 'hidden', 1);
            frm.set_df_property('delivery_date', 'hidden', 0);
            frm.set_df_property('delivery_slot', 'hidden', 0);
            frm.set_value("is_admin_order", 1);
        }
        if (frm.doc.tax_breakup) {
            frm.trigger('show_tax_spliup')
        }
    },
    customer: function(frm) {
        if (frm.doc.customer) {
            frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.order.order.get_doc_single_value',
                args: {
                    'doctype': 'Customer Address',
                    'filters': { 'parent': frm.doc.customer,"is_default":1  },
                    'fieldname': ['first_name', 'phone',
                    'address', 'country', 'state', 'city', 'zipcode', 'landmark','last_name','is_default']
                },
                callback: function(r) {
                    var data = r.message;
                    if (data) {
                        frm.set_value("address", data.address);
                        frm.set_value("city", data.city);
                        frm.set_value("state", data.state);
                        frm.set_value("country", data.country);
                        frm.set_value("zipcode", data.zipcode);
                        frm.set_value("landmark", data.landmark);
                        frm.set_value("last_name",data.last_name)

                        frm.set_value("shipping_first_name", data.first_name);
                        frm.set_value("shipping_last_name",data.last_name)
                        frm.set_value("shipping_shipping_address", data.address);
                        frm.set_value("shipping_city", data.city);
                        frm.set_value("shipping_state", data.state);
                        frm.set_value("shipping_country", data.country);
                        frm.set_value("shipping_zipcode", data.zipcode);
                        frm.set_value("shipping_landmark", data.landmark);
                    }
                }
            })
        }
        if (frm.doc.customer){
            frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.order.order.get_customer_details',
                args: {
                    'doctype': 'Customers',
                    'filters': { 'name': frm.doc.customer},
                    'fields': ['full_name','first_name', 'email','phone','last_name']
                },
                callback: function(r) {
                    var data = r.message;
                    if (data) {
                        frm.set_value('customer_name', data.full_name)
                        frm.set_value('customer_email', data.email)
                        frm.set_value("first_name", data.first_name);
                        frm.set_value("phone", data.phone);
                        frm.set_value("shipping_phone", data.phone);
                    }
                }
            })
        }
    },
    validate: function(frm){
        if (frm.doc.order_item){
            if (frm.doc.order_item.length >0){
                for (var i = 0; i < frm.doc.order_item.length; i++) {
                    if (frm.doc.order_item[i].price <= 0){
                        frappe.throw("<p>Please Enter Price for This Item: "+frm.doc.order_item[i].item_name+"</p>")
                    }
                    if (frm.doc.order_item[i].quantity <= 0){
                        frappe.throw("<p>Please enter quantity for this item: "+frm.doc.order_item[i].item_name+"</p>")
                    }
                } 
            }else{
                frappe.throw("<p>Please choose Items</p>")
            }
        }
    },
    chage_status_shipped(frm){
        frappe.run_serially([
            () => {
                frm.events.get_all_order_items_list(frm, 'shipped')
            },
            () => {
                frappe.call({
                    method: 'go1_commerce.go1_commerce.doctype.order.order.get_order_settings',
                    args: {"order_id":frm.doc.name,'doctype':frm.doc.doctype},
                    async: false,
                    callback: function(d) {
                        if (d.message) {
                            frm.enable_driver_for_shipment = d.message.order_settings.enable_driver_for_shipment;
                        }
                    }
                })
            },
            () => {
                frm.trigger('shipment')
            }
        ])
    },
    shipment: function(frm) {
        if(frm.doc.status == "Packed" || frm.doc.status == "Ready to Ship" || frm.doc.status == "In Process"){
            let dialog;
            let random = Math.random() * 100;
             var shipped = 0;
             frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: 'Shipping Method',
                    fieldname: 'is_deliverable',
                    filters: frm.doc.shipping_method
                },
                async: false,
                callback: function(r) {
                    if(r.message){
                        if(r.message.is_deliverable==1){
                            shipped = 1
                        }
                    }
                }
            });
            let fields = [
                { fieldtype: "Data", label: __("Tracking Number"), fieldname: "tracking_number" },
                { fieldtype: "Data", label: __("Tracking Link"), fieldname: "tracking_link" }
            ]
            if(frm.enable_driver_for_shipment)
                fields.push({ 
                    fieldtype: "Link", 
                    label: __("Driver"), 
                    fieldname: "driver", options: "Drivers",
                    get_query: function() {
                        return {
                            filters: {
                                driver_status: 'Online'
                            }
                        }
                    }
                })
            dialog = new frappe.ui.Dialog({
                title: __('Shipment'),
                fields: fields,
                primary_action_label: __('Close')
            });
            let selected_item_list = []
            frm.items_list.map(f => {
                selected_item_list.push({ 'product': f.item, 'orderid': frm.doc.name })
            });
            dialog.set_primary_action(__('Save'), function() {
                let values = dialog.get_values();
                    console.log("values.driver: ",values.driver);
                    frappe.call({
                        method: 'go1_commerce.go1_commerce.doctype.order.order.update_order_items_status',
                        args: {
                            "Products": selected_item_list,
                            "status": "Shipped",
                            "Tracking_Number": values.tracking_number,
                            "Tracking_Link": values.tracking_link,
                            "OrderId": frm.doc.name,
                            'doctype': cur_frm.doctype,
                            "create_shipment": 1,
                            "driver": values.driver
                        },
                        async: false,
                        callback: function(data) {
                            refresh_field("order_item");
                            dialog.hide();
                            cur_frm.reload_doc();
                        }
                    })
            });
            dialog.show();
            $("input[data-fieldname='tracking_number']").attr("style", "width:315px;")
            $("input[data-fieldname='tracking_link']").attr("style", "width:315px;")
            $("input[data-fieldname='driver']").attr("style", "width:315px;")
            if(shipped==0){
                $("div[data-fieldname='driver']").attr("style", "display:none;")
            }
        }
        else{
            frappe.throw("No products available for shipping")
        }
        },
    get_all_order_items_list: function(frm, type) {
        if(frm.doc.order_item.length<=0){
            frappe.throw("Please choose item.")
        }else{
            frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.order.order._get_order_items_',
                args: { "OrderId": frm.doc.name, 'fntype': type},
                async: false,
                callback: function(data) {
                    if (data.message) {
                        frm.items_list = data.message;
                        refresh_field("order_item");
                    }
                }
            })
        }
    },
    get_all_order_items: function(frm, type) {
       if(frm.doc.order_item.length<=0){
           frappe.throw("Please choose item.")
       }
       else{

            frappe.call({
                    method: 'go1_commerce.go1_commerce.doctype.order.order.get_order_items',
                    args: { "OrderId": frm.doc.name, 'fntype': type },
                    async: false,
                    callback: function(data) {
                        refresh_field("order_item");
                        cur_frm.reload_doc();
                }
            })
       }
   },
    make_payment_refund: function(frm){
        let dialog;
        dialog = new frappe.ui.Dialog({
            title: __('Refund Payment'),
            fields: [
                { 
                    fieldtype: "Currency", 
                    label: __("Paid Amount"), 
                    fieldname: "paid_amount",
                    reqd:0,
                    read_only:1,
                    default:frm.doc.paid_amount
                },
                { 
                    fieldtype: "Currency", 
                    label: __("Amount To Be Refund"), 
                    fieldname: "refund_amount",
                    reqd:1, 
                    default:frm.doc.paid_amount
                },
            ],
            primary_action_label: __('Close')
        });
        dialog.set_primary_action(__('Confirm'), function() {
            var refund = dialog.get_values()
            frappe.call({
                method: "go1_commerce.go1_commerce.doctype.order.order.make_refund",
                args: {"refund_amount": refund.refund_amount, "order": cur_frm.doc.name},
                async: false,
                callback: function(r) {
                    cur_frm.reload_doc()
                    dialog.hide()
                }
            })
        })
        dialog.$wrapper.find('.modal-dialog').css("min-width", "430px");
        dialog.$wrapper.find('.modal-dialog').css("max-width", "430px");
        dialog.show();
    },
    delivery: function(frm) {
        if (frm.doc.delivery) {
            var amount = 0;
            if (frm.doc.total_amount)
                amount = frm.doc.total_amount
            amount = amount + parseFloat(frm.doc.delivery)
            frm.set_value('total_amount', amount)
        }
    },
    
    make_invoice: function() {
        frappe.model.open_mapped_doc({
            method: "go1_commerce.accounts.api.make_sales_invoice",
            frm: cur_frm
        })
    },
    make_payment: function() {
        frappe.model.open_mapped_doc({
            method: "go1_commerce.accounts.api.make_payment",
            frm: cur_frm
        })
    },
    create_return: function(frm) {
        let returns = frm.doc.order_item.filter(obj => obj.return_created != 1);
        let html = `<table id="returnTable" class="table table-bordered">
                        <thead style="background: #F7FAFC;">
                            <tr>
                                <th> </th>
                                <th> Product </th>
                                <th>Quantity</th>
                            </tr>
                        </thead>
                    <tbody>`
        $(returns).each(function(k, v) {
            html += `<tr data-name="${v.name}">
                        <input type="hidden" class="productId" value="${v.item}"/>
                        <td>
                            <input type="checkbox" class="grid-row-check pull-left">
                        </td>
                        <td style="width:70%;">
                            ${v.item_name}
                        </td>
                        <td>
                            <div class="control-input">
                                <input type="text" autocomplete="off" 
                                    class="input-with-feedback form-control" 
                                    data-fieldtype="Int" data-fieldname="quantity" placeholder=""
                                    data-doctype="Order Item" value="${v.quantity}">
                            </div>
                        </td>
                    </tr>`;
        })
        html += `</tbody> 
                </table>`
        frm.return_dialog = new frappe.ui.Dialog({
            title: 'Select Brands',
            fields: [{
                    "fieldname": "return_items",
                    "fieldtype": "HTML",
                    "options": html
                },
                {
                    "fieldname": "sc",
                    "fieldtype": "Section Break"
                },
                {
                    "fieldname": "return_reason",
                    "fieldtype": "Link",
                    "label": "Return Reason",
                    "options": "Return Request Reasons",
                    "reqd": 1
                },
                {
                    "fieldname": "return_action",
                    "fieldtype": "Link",
                    "label": "Return Action",
                    "options": "Return Request Action",
                    "reqd": 1
                },
                {
                    "fieldname": "images",
                    "fieldtype":"Attach Image",
                    "label":"Image",
                    "reqd":1
                },
                {
                    "fieldname": "comments",
                    "fieldtype": "Small Text",
                    "label": "Customer Comments"
                }
            ]
        });
        frm.return_dialog.set_primary_action(__('Create Return'), function() {
            let formData = {};
            let values = frm.return_dialog.get_values();
            let lists = [];
            let allow_form = true;
            let data = {};
            $('#returnTable').find('tbody tr').each(function() {
                if ($(this).find('.grid-row-check:checked').val()) {
                    data.item = $(this).find('.productId').val();
                    data.item_name = $(this).find('td:eq(1)').text()
                    data.quantity = $(this).find('input[data-fieldname="quantity"]').val();
                    let check_data = returns.find(obj => obj.name == $(this).attr('data-name'));   
            
                    if (check_data) {
                        if (check_data.quantity < parseInt(data.quantity)) {
                            allow_form = false;
                            frappe.msgprint('Quantity cannot be greater than ' + data.quantity + ' for item ' + data.item_name, 'Alert')
                        } else {
                            if (data.quantity > 0){
                                data.price = parseFloat(check_data.price)
                                data.amount = parseFloat(check_data.price)*parseInt(data.quantity)
                                data.shipping_charge = parseFloat(check_data.shipping_charges)
                                console.log("data",data);
                                lists.push(data)
                            }
                            else {
                                allow_form = false;
                                frappe.msgprint('Quantity must be greater than 0 for item ' + data.item_name, 'Alert')
                            }
                        }
                    }
                } else {
                    frappe.throw("Please select the Items !")
                }
            })
            data.order_id = frm.doc.name
            formData.order_id = frm.doc.name
            formData.return_reason = values.return_reason
            formData.return_action = values.return_action
            formData.remarks = values.comments
            console.log(values);
            formData.images = values.images
            formData.order_shipping_charge = parseFloat(frm.doc.shipping_charges)
            formData.items = lists
            var val_data = JSON.stringify(formData)
            if (lists.length > 0 && allow_form == true) {
                frappe.call({
                    method: 'go1_commerce.go1_commerce.v2.orders.create_return_request',
                    args: {
                        data : val_data
                    },
                    callback: function(d) {
                        frm.return_dialog.hide()
                        cur_frm.reload_doc()
                    }
                })
            } else {

            }
        });
        frm.return_dialog.show();
    },
    after_save: function(frm) {
        var allow_admin_to_edit = 0
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.order.order.get_order_settings',
            args: { "order_id": frm.doc.name, 'doctype': frm.doc.doctype },
            async: false,
            callback: function(d) {
                if (d.message) {
                    if (d.message.allow_admin_to_edit_order == 1) {
                        allow_admin_to_edit = 1
                    }
                }
            }
        })
        frm.set_df_property('order_detail_html', 'hidden', 0)
        frm.set_df_property('sec_2', 'hidden', 1)
        frm.set_df_property('billing_section', 'hidden', 1)
        frm.set_df_property('shipping_section', 'hidden', 1)
        frm.set_df_property('sec_br', 'hidden', 1)
        frm.set_df_property('ec', 'hidden', 1)
        cur_frm.reload_doc()
    },
    get_available_checkout_attributes: function(frm) {
        frappe.call({
            method: 'go1_commerce.go1_commerce.v2.orders.get_checkout_attributes',
            args: {
                'business': (frm.doc.business || null)
            },
            async: false,
            callback: function(r) {
                frm.__checkout_attributes = r.message;
            }
        })
    },
    edit_order_checkout_attributes: function(frm) { 
        let randomuppy = Math.random() * 100;
        let dialog;
        dialog = new frappe.ui.Dialog({
            title: __('Order Questionaries'),
            fields: [
                { fieldtype: "HTML", label: __("Questionaries"), fieldname: "checkout_attributes" },
            ],
            primary_action_label: __('Close')
        });
        dialog.set_primary_action(__('Save'), function() {
            var attributes = [];
            
            dialog.$wrapper.find('tbody tr').each(function() {
                let obj = {};
                obj.name = $(this).attr('data-id');
                obj.checkout_attribute_id = $(this).attr('data-question');
                let value = $(this).find('textarea').val();
                let que = $(this).find('.attr-title').html();
                obj.attribute_description = `<span class="attr-title">${que}</span> : <span>${value || ''}</span><br>`;
                if((!obj.name || obj.name == "") && value == "") {

                } else {
                    attributes.push(obj);
                }                
            })
            if(attributes.length > 0) {
                frappe.call({
                    method: 'go1_commerce.go1_commerce.doctype.order.order.update_order_checkout_attributes',
                    args: {
                        "order": frm.doc.name,
                        "attributes": attributes
                    },
                    async: false,
                    callback: function(d) {
                        cur_frm.reload_doc();
                        dialog.hide();
                    }
                })
            }                
        });
        var checkout_attributes_html = `<table id="tbl-attributes-${parseInt(randomuppy)}" class="table table-bordered">
                                            <thead>
                                                <tr>
                                                    <th style="width:35%">
                                                        Question
                                                    </th>
                                                    <th>
                                                        Customer Repsonse
                                                    </th>
                                                </tr>
                                            </thead>
                                        <tbody>`;
        $(frm.__checkout_attributes).each((k, v) => {
            let check_row = frm.doc.checkout_attributes.find(obj => obj.attribute_id == v.name);
            let val = '';
            if (check_row) {
                let value = check_row.attribute_description.split(':')[1].split('<br>')[0];
                if (value) {
                    val = $(value).html();
                }
            }
            let row = ` <tr data-id="${(check_row && check_row.name) || ''}" data-question="${v.name}">
                            <td>
                                <span class="attr-title">
                                    ${v.question}
                                </span>
                            </td>
                            <td>
                                <textarea style="width: 100%;border-color: #d3d3d3;">
                                    ${val}
                                </textarea>
                            </td>
                            </tr>`;
            checkout_attributes_html += row;
            if(v.is_group == 1 && v.child_attributes && v.child_attributes.length > 0) {
                $(v.child_attributes).each((key, val) => {
                    let check_child_row = frm.doc.checkout_attributes.find(obj => obj.attribute_id == val.name);
                    let child_val = '';
                    if (check_child_row) {
                        let value = check_child_row.attribute_description.split(':')[1].split('<br>')[0];
                        if (value) {
                            child_val = $(value).html();
                        }
                    }
                    let child_row = `<tr data-id="${(check_child_row && check_child_row.name) || ''}" 
                                                data-question="${val.name}">
                                    <td>
                                        <span class="attr-title">
                                            ${val.question}
                                        </span>
                                    </td>
                                    <td>
                                        <textarea style="width: 100%;border-color: #d3d3d3;">
                                            ${child_val}
                                        </textarea>
                                    </td>
                                    </tr>`;
                    checkout_attributes_html += child_row;
                })
            }
        })
        checkout_attributes_html += `</tbody>
                                    </table>`;
        dialog.fields_dict.checkout_attributes.$wrapper.html(checkout_attributes_html);
        dialog.show();
        dialog.$wrapper.find('.modal-dialog').css("width", "1000px");

    },
    shipping_method: function(frm){
        if(frm.doc.shipping_method){
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    'doctype': 'Shipping Method',
                    'filters': { 'name': frm.doc.shipping_method },
                    'fieldname': ['shipping_method_name']
                },
                callback: function(data) {
                    if (data.message) {
                        frm.set_value('shipping_method_name', data.message.shipping_method_name);
                    }
                }
            })
        }
        if(frm.doc.shipping_method && frm.doc.customer){
           
            frappe.call({
                method: 'go1_commerce.go1_commerce.v2.checkout.get_cart_delivery_slots',
                args: {
                    "customer_id": frm.doc.customer,
                    "shipping_method": frm.doc.shipping_method
                },
                async: false,
                callback: function(d) {
                    if(d.message){
                        if(d.message.length>0 && d.message[0].dates_lists){
                            var options=[];
                            frm.slot_dates_lists = d.message[0].dates_lists;
                            (frm.slot_dates_lists).forEach(function(row) {
                                    if(row){
                                        var deliverydate = new Date(row.date);
                                        var currentDayOfMonth = deliverydate.getDate();
                                        var currentMonth = deliverydate.getMonth(); 
                                        var currentYear = deliverydate.getFullYear();
                                        var delivery = currentYear+ "-" + (currentMonth + 1) + "-" + currentDayOfMonth;
                                        options.push({"value": delivery,"label":row.format_date}) ;
                                    }
                                })
                            cur_frm.set_df_property("delivery_date", "options", options); 
                        }
                    } 
                }
            })
        }
    },
    delivery_date: function(frm){
        if(frm.slot_dates_lists && frm.doc.delivery_date){
            var slot_options=[];
            (frm.slot_dates_lists).forEach(function(row) {
                var deliverydate = new Date(row.date);
                var currentDayOfMonth = deliverydate.getDate();
                var currentMonth = deliverydate.getMonth(); 
                var currentYear = deliverydate.getFullYear();
                var delivery = currentYear+ "-" + (currentMonth + 1) + "-" + currentDayOfMonth;
                
                if(delivery==frm.doc.delivery_date){
                    $(row.slots).each(function (k, x) {
                        slot_options.push({"value":x.from_time+","+x.to_time ,"label":x.time_format}) 
                     })
                }
            })
            cur_frm.set_df_property("delivery_slot", "options", slot_options)
        }
    },
    order_edit_options: function(frm) {
        if (!cur_frm.doc.name.indexOf('ORD-')) {
            if ($('[data-fieldname="order_detail_html"]').css("display") == "block") {
                frm.set_df_property('order_detail_html', 'hidden', 1)
                frm.set_df_property('sec_2', 'hidden', 0)
                frm.set_df_property('billing_section', 'hidden', 0)
                frm.set_df_property('shipping_section', 'hidden', 0)
                frm.set_df_property('sec_br', 'hidden', 0)
                frm.set_df_property('ec', 'hidden', 0)
                frm.set_df_property('order_item', 'readonly', 0)
                frm.set_df_property('shipping_method_name', 'hidden', 0)
                frm.set_df_property('shipping_method_name', 'readonly', 1)
                frm.set_df_property('order_date', 'hidden', 1)
                frm.set_df_property('discount', 'hidden', 1)
                frm.set_df_property('shipping_method', 'hidden', 0);
                frm.set_df_property('payment_status', 'hidden', 1);
                frm.set_df_property('discount_coupon', 'hidden', 1);
                frm.set_df_property('delivery_date', 'hidden', 0);
                frm.set_df_property('delivery_slot', 'hidden', 0);
                $('button.btn.btn-primary.btn-sm.primary-action').removeClass("hide");
                $('button.btn.btn-primary.btn-sm.primary-action').html('<i class="visible-xs octicon octicon-check"></i><span class="hidden-xs" data-label="Update">Update</span>');
                $("button.btn.btn-secondary.btn-default.btn-sm").addClass("hide")
                $('button[data-label="Edit%20Order"]').html("<i class='fa fa-arrow-circle-left' style='margin-right:5px'></i> Back to Order Detail");
                if(frm.doc.order_item){
                    for(var k=0;k<frm.doc.order_item.length;k++){
                        $('#page-Order [data-fieldname="order_item"]').find('.grid-body .grid-row:eq('+k+') .data-row').find('[data-fieldname="varaint_txt"][data-fieldtype="Select"]').click();
                        $('#page-Order [data-fieldname="order_item"]').find('.grid-body .grid-row:eq('+k+') .data-row').find('[data-fieldname="varaint_txt"][data-fieldtype="Select"] .field-area').removeAttr("style");
                    }
                }
            } else {
                frm.set_df_property('order_detail_html', 'hidden', 0)
                frm.set_df_property('sec_2', 'hidden', 1)
                frm.set_df_property('billing_section', 'hidden', 1)
                frm.set_df_property('shipping_section', 'hidden', 1)
                frm.set_df_property('sec_br', 'hidden', 1)
                frm.set_df_property('ec', 'hidden', 1)
                frm.set_df_property('discount', 'hidden', 1)
                frm.set_df_property('shipping_method_name', 'hidden', 1)
                frm.set_df_property('shipping_method', 'hidden', 1)
                $('button[data-label="Edit%20Order"]').html("<i class='fa fa-pencil' style='margin-right:5px'></i> Edit Order");
                cur_frm.reload_doc()
            }
        }
        else{
                frm.set_df_property('order_detail_html', 'hidden', 1)
                frm.set_df_property('sec_2', 'hidden', 0)
                frm.set_df_property('billing_section', 'hidden', 0)
                frm.set_df_property('shipping_section', 'hidden', 0)
                frm.set_df_property('sec_br', 'hidden', 0)
                frm.set_df_property('ec', 'hidden', 0)
                frm.set_df_property('order_item', 'readonly', 0)
                frm.set_df_property('shipping_method_name', 'hidden', 0)
                frm.set_df_property('shipping_method_name', 'readonly', 1)
                frm.set_df_property('order_date', 'hidden', 1)
                frm.set_df_property('discount', 'hidden', 1)
                frm.set_df_property('shipping_method', 'hidden', 0);
                frm.set_df_property('payment_status', 'hidden', 1);
                frm.set_df_property('discount_coupon', 'hidden', 1);
                frm.set_df_property('delivery_date', 'hidden', 0);
                frm.set_df_property('delivery_slot', 'hidden', 0);
                $('button.btn.btn-primary.btn-sm.primary-action').removeClass("hide");
                $('button.btn.btn-primary.btn-sm.primary-action').html('<i class="visible-xs octicon octicon-check"></i><span class="hidden-xs" data-label="Update">Upda<span class="alt-underline">t</span>e</span>');
                $("button.btn.btn-secondary.btn-default.btn-sm").addClass("hide")
                $('button[data-label="Edit%20Order"]').html("<i class='fa fa-arrow-circle-left' style='margin-right:5px'></i> Back to Order Detail");
                if(frm.doc.order_item){
                for(var k=0;k<frm.doc.order_item.length;k++){
                    $('#page-Order [data-fieldname="order_item"]').find('.grid-body .grid-row:eq('+k+') .data-row').find('[data-fieldname="varaint_txt"][data-fieldtype="Select"]').click();
                    $('#page-Order [data-fieldname="order_item"]').find('.grid-body .grid-row:eq('+k+') .data-row').find('[data-fieldname="varaint_txt"][data-fieldtype="Select"] .field-area').removeAttr("style");
                }
            }
        }
    },
    show_tax_spliup: function(frm) {
        let wrapper = $(frm.get_field('tax_splitup').wrapper).empty();
        let table_html = $(
                            `<table class="table table-bordered" style="cursor:pointer; margin:0px;">
                                <thead>
                                    <tr>
                                        <th style="width: 70%">Tax</th>
                                        <th>Tax %</th>
                                        <th>Tax Amount</th>
                                        <th>Tax Type</th>
                                    </tr>
                                </thead>
                                <tbody></tbody>
                            </table>`
                        ).appendTo(wrapper);
        let tax = frm.doc.tax_breakup.split('\n');
        if (tax.length > 0) {
            tax.map(f => {
                if (f) {
                    let tax_type = f.split('-')[0].trim();
                    let tax_percent = f.split('-')[1].trim();
                    let tax_value = f.split('-')[2].trim();
                    let product_tax_type = f.split('-')[3];
                    let row_data = $(`<tr>
                        <td>${tax_type}</td>
                        <td>${frappe.format(tax_percent)}</td>
                        <td>${parseFloat(tax_value).toFixed(2)}</td>
                        <td>${product_tax_type}</td>
                    </tr>`);
                    table_html.find('tbody').append(row_data);
                }
            })
        }
    },
});
frappe.ui.form.on("Order Item", {
    form_render: function(frm, cdt,cdn){
        var d = frappe.get_doc(cdt, cdn);
        if(d.item){
        frappe.call({
            method: "go1_commerce.go1_commerce.doctype.order.order.get_attributes_combination",
            args: {
                product: d.item
            },
            callback: function(data) {
                var options = [];
                var htm ='';
                if(data.message){
                    (data.message[0]).forEach(function(row) {
                        if(row){
                                htm +='<option data-id="'+row.attribute_id+'" value="'+row.combination_txt+'">'+row.combination_txt+'</option>'
                            options.push({"value":row.combination_txt,"label":row.combination_txt}) 
                            }
                        })
                    }
                    frm.fields_dict.order_item.grid.update_docfield_property( "varaint_txt", "options",[""].concat(options));
                    cur_frm.fields_dict["order_item"].grid.grid_rows_by_docname[d.name].get_field("varaint_txt").$wrapper.find("select").html(htm)
                    cur_frm.refresh_fields();
                }
            })
        }
    },
    varaint_txt: function(frm, cdt, cdn) {
        var d = frappe.get_doc(cdt, cdn);
        frappe.call({
            method: "go1_commerce.go1_commerce.doctype.order.order.update_variant_id",
            args: {
                product: d.item,
                v_text: d.varaint_txt,
            },
            async:false,
            callback: function(data) {
                frappe.model.set_value(cdt, cdn, "attribute", data.message);
            }
        });
    },
    item: function(frm, cdt, cdn) {
        var d = frappe.get_doc(cdt, cdn);
        if (d.item) {
             var d = frappe.get_doc(cdt, cdn);
             frappe.call({
                method: "go1_commerce.go1_commerce.doctype.order.order.get_attributes_combination",
                args: {
                    product: d.item
                },
                callback: function(data) {
                    
                    var options = [];
                    var htm =''
                    if(data.message){
                        console.log("MSGGG...",data.message);
                        if (data.message[0].length != 0){
                            htm +=` <select type="text" autocomplete="off" 
                                    class="input-with-feedback form-control ellipsis" 
                                    maxlength="140" data-fieldtype="Select" 
                                    data-fieldname="varaint_txt" placeholder="" 
                                    data-doctype="Order Item">
                                    <option>
                                    </option>`

                            console.log("HHHHH",htm);
                            data.message[0].forEach(function(row) {
                                if(row){
                                    htm +=`<option data-id="${row.attribute_id}" value="${row.combination_txt}">
                                                ${row.combination_txt}
                                            </option>`
                                    options.push({"value":row.combination_txt,"label":row.combination_txt}) 
                                }
                            })
                            htm +='</select>'
                        }
                        
                    }
                    frm.fields_dict.order_item.grid.update_docfield_property("varaint_txt", "options",[""].concat(options));
                    cur_frm.fields_dict["order_item"].grid.grid_rows_by_docname[d.name].get_field("varaint_txt").$wrapper.find("select").html(htm)
                    if(htm !=''){
                        cur_frm.fields_dict["order_item"].grid.grid_rows_by_docname[d.name].get_field("varaint_txt").df.reqd = 1
                    }
                    else{
                        cur_frm.fields_dict["order_item"].grid.grid_rows_by_docname[d.name].get_field("varaint_txt").df.reqd = 0
                    }
                    cur_frm.refresh_fields();
                }
            })
        }
        if(d.item && frm.doc.customer){
              frappe.call({
                method: "go1_commerce.go1_commerce.doctype.order.order.get_product_price",
                args: {"product": d.item,"attribute":d.attribute, "customer":frm.doc.customer},
                async: false,
                callback: function(r) {
                    if( r.message){
                        frappe.model.set_value(cdt, cdn, "price", r.message.price);
                        frappe.model.set_value(cdt, cdn, "amount", r.message.price* d.quantity);
                   }
                }
            })
        }
    },
    attribute: function(frm, cdt, cdn){
        var d = frappe.get_doc(cdt, cdn);
        if(d.item && frm.doc.customer){
              frappe.call({
                method: "go1_commerce.go1_commerce.doctype.order.order.get_product_price",
                args: { "product": d.item, 
                        "attribute":d.attribute, 
                        "customer":frm.doc.customer},
                async: false,
                callback: function(r) {
                    console.log("dddd",r.message);
                    if( r.message){
                        console.log("rrr",r.message.length);
                        frappe.model.set_value(cdt, cdn, "price", r.message.price);
                        frappe.model.set_value(cdt, cdn, "base_price", r.message.price);
                        frappe.model.set_value(cdt, cdn, "amount", r.message.price* d.quantity);
                        frappe.model.set_value(cdt, cdn, "t_amount", r.message.price* d.quantity);
                    }
                    else{
                        frappe.model.set_value(cdt, cdn, "price", '');
                        frappe.model.set_value(cdt, cdn, "base_price", '');
                        frappe.model.set_value(cdt, cdn, "amount", '');
                        frappe.model.set_value(cdt, cdn, "t_amount", '');
                    }
                    
                }
            })
        }
    },
    quantity: function(frm, cdt, cdn) {
        var d = frappe.get_doc(cdt, cdn);
        var pre_amount = d.quantity * d.price;
        frappe.model.set_value(cdt, cdn, "amount", pre_amount);
        if (d.discount_amount) {
            var Remain = pre_amount - d.discount_amount
        } else {
            var Remain = pre_amount
        }
        frappe.model.set_value(cdt, cdn, "t_amount", Remain);
    },
    price: function(frm, cdt, cdn) {
        var d = frappe.get_doc(cdt, cdn);
        var pre_amount = d.quantity * d.price;
        frappe.model.set_value(cdt, cdn, "amount", pre_amount);
        if (d.discount_amount) {
            var Remain = pre_amount - d.discount_amount
        } else {
            var Remain = pre_amount
        }
        frappe.model.set_value(cdt, cdn, "t_amount", Remain);
    },
    discount_amount: function(frm, cdt, cdn) {
        var d = frappe.get_doc(cdt, cdn);
        var amount = d.amount;
        var quantity = d.quantity;
        t_amount = quantity * amount;
        if (d.discount_amount) {
            var Remain = t_amount - d.discount_amount
        } else {
            var Remain = t_amount
        }
        frappe.model.set_value(cdt, cdn, "t_amount", Remain);
    },
    discount: function(frm, cdt, cdn) {
        var d = frappe.get_doc(cdt, cdn);
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                'doctype': 'Discounts',
                'filters': { 'name': d.discount },
                'fieldname': ['name1', 'discount_amount']
            },
            callback: function(data) {
                if (data.message) {
                    frappe.model.set_value(cdt, cdn, "discount_name", data.message.name1);
                    frappe.model.set_value(cdt, cdn, "discount_amount", data.message.discount_amount);
                }
            }
        })
    },
    t_amount: function(frm, cdt, cdn) {
        var total_amount = 0;
        for (var i = 0; i < frm.doc.order_item.length; i++) {
            total_amount += frm.doc.order_item[i].t_amount;
        }
        frm.set_value("total_amount", total_amount);
    },
    before_order_item_remove: function(frm, cdt, cdn) {
        var d = frappe.get_doc(cdt, cdn);
        var amount = frm.doc.total_amount - d.t_amount;
        frm.set_value('total_amount', amount)
    }
})

frappe.ui.form.on("Order Addons", {
    option_amount: function(frm, cdt, cdn) {
        var total_amount = 0;
        for (var i = 0; i < frm.doc.addons.length; i++) {
            total_amount += frm.doc.addons[i].option_amount;
        }
        frm.set_value("add_on_total", total_amount);
    },
    before_addons_remove: function(frm, cdt, cdn) {
        var d = frappe.get_doc(cdt, cdn);
        var amounts = frm.doc.add_on_total - d.option_amount;
        frm.set_value('add_on_total', amounts)
    }
})

var change_status = function(docname, order_status, restaurant_status, driver_status) {
    frappe.call({
        method: 'go1_commerce.go1_commerce.v2.orders.update_order_status',
        args: {
            name: docname,
            order_status: order_status,
            restaurant_status: restaurant_status,
            driver_status: driver_status
        },
        callback: function(data) {
            if (data.message.result == 'Success')
                location.reload();
        }
    })
}
var reload = function(docname) {
    frappe.call({
        method: 'frappe.desk.form.load.getdoc',
        args: {
            doctype: 'Order',
            name: docname
        },
        callback: function(data) {

        }
    })
}
var getMonthName = function(month) {
    var monthName = '';
    switch (month) {
        case 0:
            monthName = "Jan";
            break;
        case 1:
            monthName = "Feb";
            break;
        case 2:
            monthName = "Mar";
            break;
        case 3:
            monthName = "Apr";
            break;
        case 4:
            monthName = "May";
            break;
        case 5:
            monthName = "Jun";
            break;
        case 6:
            monthName = "Jul";
            break;
        case 7:
            monthName = "Aug";
            break;
        case 8:
            monthName = "Sep";
            break;
        case 9:
            monthName = "Oct";
            break;
        case 10:
            monthName = "Nov";
            break;
        case 11:
            monthName = "Dec";
            break;

        default:
            monthName = "";
    }
    return monthName;
}

function order_detail_html_render(frm){
    let wrapper = $(frm.get_field('order_detail_html').wrapper).empty();
    $(frappe.render_template("dynamic_template", { order_details: frm.doc  })).appendTo(wrapper);
    if (cur_frm.is_new()) {
        frm.set_value("is_admin_order", 1);
        frm.set_value("delivery_date", '');
        frm.set_value("delivery_slot", '');
    }
}

function validate_order_items(frm){
    setTimeout(function(){
        if(frm.doc.order_item){
            for(var oi=0;oi<frm.doc.order_item.length;oi++){
               frappe.call({
                method: "go1_commerce.go1_commerce.doctype.order.order.get_attributes_combination",
                args: {
                    product: frm.doc.order_item[oi].item
                },
                async:false,
                    callback: function(data) {
                        var options = [];
                        var htm="";
                        if(data.message){
                            (data.message[0]).forEach(function(row) {
                                if(row){
                                    htm +=` <option data-id="${row.attribute_id}" value="${row.combination_txt}">
                                                ${row.combination_txt}
                                            </option>`
                                    options.push({  "value":row.combination_txt,
                                                    "label":row.combination_txt}) 
                                }
                            })
                        }
                        if (cur_frm.grids[1].grid.grid_rows[oi].columns.varaint_txt){
                            cur_frm.grids[1].grid.grid_rows[oi].columns.varaint_txt.df.options = options;
                        }
                        cur_frm.refresh_fields();
                    }
                })
            }
            frm.refresh_field("order_item")
            // if (frm.doc.__unsaved == 1 && frm.doc.docstatus == 0 && frm.doc.pre_status == "Placed" && !cur_frm.is_new()){
            //     frm.save();
            // }
        }
    },1000);
}

function validate_shipping_method(frm){

    if(frm.doc.shipping_method && frm.doc.customer){
        frappe.call({
            method: 'go1_commerce.go1_commerce.v2.checkout.get_cart_delivery_slots',
            args: {
                "customer_id": frm.doc.customer,
                "shipping_method": frm.doc.shipping_method
            },
            async: false,
            callback: function(d) {
                if(d.message){
                     if(d.message.length>0 && d.message[0].dates_lists){
                        var options=[];
                        frm.slot_dates_lists = d.message[0].dates_lists;
                        (frm.slot_dates_lists).forEach(function(row) {
                                if(row){
                                    var deliverydate = new Date(row.date);
                                    var currentDayOfMonth = deliverydate.getDate();
                                    var currentMonth = deliverydate.getMonth(); 
                                    var currentYear = deliverydate.getFullYear();
                                    var delivery = currentYear+ "-" + (currentMonth + 1) + "-" + currentDayOfMonth;
                                    options.push({"value": delivery,"label":row.format_date}) ;
                                }
                            })
                        cur_frm.set_df_property("delivery_date", "options", options);
                    }
                } 
            }
        })
    }
    frappe.call({
        method: 'go1_commerce.go1_commerce.doctype.order.order.get_order_settings',
        args: {"order_id":frm.doc.name,'doctype':frm.doc.doctype},
        async:false,
        callback: function(d) {
            if(d.message){
                frm.order_settings = d.message.order_settings;
                frm.proccess_status = d.message.proccess_status;
                frm.check_delivery = d.message.allow_shipment;
                frm.has_workflow = d.message.has_workflow;
            }
        }
    })
}

function validate_workflow(frm){
    if (frm.doc.docstatus == 1) {
        let allow = false;
        if (cur_frm.doctype == 'Order') {
            allow = true;
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    'doctype': 'Workflow',
                    'filters': {'document_type': "Order","is_active":1},
                    "fieldname":"name",
                },
                callback: function(r) {
                    if(Object.keys(r.message).length>1){
                        allow = false;
                    }
                    if (allow) {
                        if (frm.doc.status == 'Placed' && frm.proccess_status ==0) {
                            frm.add_custom_button(__("Mark As Packed"), function() {
                                frm.events.get_all_order_items(frm, 'packed')
                            });
                            $('button[data-label="Mark%20As%20Packed"]').attr("class","btn btn-xs btn-primary");
                            $('button[data-label="Mark%20As%20Packed"]').html("<i class='fa fa-truck' style='margin-right:5px'></i> Mark As Packed");
                        }
                        if (frm.doc.status == 'Placed' && frm.proccess_status ==1) {
                            frm.add_custom_button(__("Mark As In Process"), function() {
                                frm.events.change_status_in_process(frm)
                            });
                            $('button[data-label="Mark%20As%20Packed"]').hide();
                            $('button[data-label="Mark%20As%20In%20Process"]').attr("class","btn btn-xs btn-primary");
                            $('button[data-label="Mark%20As%20In%20Process"]').html("<i class='fa fa-spinner' style='margin-right:5px'></i> Mark As In Process");
                        }
                        if(frm.check_delivery == 0 && (frm.doc.status == 'Packed'|| frm.doc.status == 'In Process')){
                            frm.add_custom_button(__("Mark As Ready"), function() {
                                frappe.call({
                                method: 'go1_commerce.go1_commerce.doctype.order.order.mark_as_ready',
                                args: { "order": frm.doc.name},
                                async: false,
                                callback: function(data) {
                                    cur_frm.reload_doc();
                                }
                                })
                            });
                            $('button[data-label="Mark%20As%20Ready"]').attr("class","btn btn-xs btn-primary");
                            $('button[data-label="Mark%20As%20Ready"]').html("<i class='fa fa-thumbs-up' style='margin-right:5px'></i> Mark As Ready");
                        }
                        if ((frm.doc.status == 'Packed' || frm.doc.status == 'In Process') && frm.check_delivery == 1) {
                            frm.add_custom_button(__("Mark As Shipped"), function() {
                                frm.events.chage_status_shipped(frm)
                            });
                            $('button[data-label="Mark%20As%20Shipped"]').attr("class","btn btn-xs btn-primary");
                            $('button[data-label="Mark%20As%20Shipped"]').html("<i class='fa fa-truck' style='margin-right:5px'></i> Mark As Shipped");
                        }
                        if (frm.doc.status == 'Shipped' || frm.doc.status == 'Ready') {
                            frm.add_custom_button(__("Mark As Delivered"), function() {
                                frm.events.get_all_order_items(frm, 'delivered')
                            });
                            $('button[data-label="Mark%20As%20Delivered"]').attr("class","btn btn-xs btn-primary");
                            $('button[data-label="Mark%20As%20Delivered"]').html("<i class='fa fa-truck' style='margin-right:5px'></i> Mark As Delivered");
                        }
                    }
                }
            })
        }
    }
    frm.trigger('shipments')
}

function validate_status(frm){
    if(frm.doc.status == "Completed" || frm.doc.status == "Delivered"){
        $('.page-actions button.btn.btn-secondary.btn-default.btn-sm[data-label="Cancel"]').hide();
    }
    else{
        $('.page-actions button.btn.btn-secondary.btn-default.btn-sm[data-label="Cancel"]').show();
    }
    frappe.call({
        method: 'go1_commerce.go1_commerce.doctype.order.order.check_order_settings',
        args: {},
        async: false,
        callback: function(d) {
            if(d.message.is_restaurant == true && d.message.is_restaurant_driver == 1){
                $(".form-footer").hide();
                $('[data-label="Cancel"]').parent().hide();
                $('[data-page-route="Form/Order"] .row.form-section.visible-section:nth-child(10)').hide();
                $('[data-page-route="Form/Order"] .row.form-section.visible-section:nth-child(17)').hide();
                $(".layout-main-section").hide();
                $(".layout-main-section-wrapper").append('<div class="loading" style="float:left;position: absolute;font-size: 16px;text-align: center;margin-top: 20%;width: 100%;">Loading...</div>')
                setTimeout(function(){ 
                    $(".layout-main-section").show();$(".form-footer").show();
                    $(".layout-main-section-wrapper .loading").hide();
                    frm.set_df_property('commission_info', 'hidden', 0)
                    frm.set_df_property('browser_details', 'hidden', 0);
                    $(".driver-template").show();
                    $(".default-template").hide();
                    $('head').append('<style type="text/css">.form-footer{display:none !important}');
                    $(".form-inner-toolbar button").hide();}, 100);
                }
            else{
                $('[data-fieldname="browser"]').parent().parent().parent().parent().show();
            }
            frm.check_order_settings = d.message.order_settings;
        }
    })
    var payment_type =""
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            'doctype': 'Payment Method',
            'filters': { 'name': frm.doc.payment_method },
            'fieldname': ['payment_type']
        },
        async: false,
        callback: function(data) {
            if (data.message) {
                payment_type = data.message.payment_type
            }
        }
    })
    
}

function validate_check_order_settings(frm){
    if(frm.check_order_settings.enable_refund_option == 1 && frm.doc.payment_status=="Paid" && frm.doc.payment_type=="Online Payment"){
        frm.add_custom_button("Make Payment Refund", function() {
            frm.trigger('make_payment_refund');
        });
        $('button[data-label="Mark as Refunded"]').removeAttr("class");
        $('button[data-label="Mark as Refunded"]').attr("class", "btn btn-xs btn-primary");
        $('button[data-label="Mark as Refunded"]').html("<i class='fa fa fa-eye' style='margin-right:5px'></i> Mark as Refunded");
    }
    if (frm.doc.__unsaved && frm.check_order_settings.allow_admin_to_edit_order == 1 && frm.doc.payment_status !="Paid"){
        frm.set_value('status', "Placed");
        frm.set_value('shipping_status', "");
        frm.set_value('paid_using_wallet', 0);
        
        frm.set_value('advance_amount', 0);
        frm.set_value('discount_coupon', '');
        frm.set_value('transaction_id', '');
        frm.set_value('discount', 0);
    }
    frappe.call({
        method: 'go1_commerce.go1_commerce.doctype.order.order.get_linked_invoice',
        args: { "order": frm.doc.name },
        async: false,
        callback: function(d) {
            frm.invoiceid = d.message;
        }
    })
    if (cur_frm.is_new()) {
        frm.set_df_property('commission_information_section', 'hidden', 1);
            if (frm.check_order_settings.allow_admin_to_create_order) {
                frm.trigger('order_edit_options')
            }
    }
}