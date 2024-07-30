// Copyright (c) 2018, info@valiantsystems.com and contributors
// For license information, please see license.txt

frappe.require("assets/go1_commerce/css/select_list.css"); 
{% include 'go1_commerce/go1_commerce/doctype/order/order_common.js' %}
frappe.ui.form.on('Order', {
    refresh: function(frm) {
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
                      setTimeout(function(){ $(".layout-main-section").show();$(".form-footer").show();

                      $(".layout-main-section-wrapper .loading").hide();
                      frm.set_df_property('commission_info', 'hidden', 0)
                    frm.set_df_property('browser_details', 'hidden', 0);
                    $(".driver-template").show();
                    $(".default-template").hide();
                    
                    $('head').append('<style type="text/css">.form-footer{display:none !important}');
                    $(".form-inner-toolbar button").hide();
                       }, 100);

                    }
                    
                
                else{
                    $('[data-fieldname="browser"]').parent().parent().parent().parent().show();
                }
                frm.check_order_settings = d.message.order_settings;
            }
        })
       
        if (cur_frm.is_new()) {
              frm.set_df_property('commission_information_section', 'hidden', 1);
            if (frm.check_order_settings.allow_admin_to_create_order) {
                frm.trigger('order_edit_options')
            }
        }
        else{
            frm.set_df_property('commission_information_section', 'hidden', 0);
        }

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
            
        if(frm.check_order_settings.enable_refund_option == 1 && frm.doc.payment_status=="Paid" && payment_type=="Online Payment"){
            frm.add_custom_button("Make Payment Refund", function() {
                frm.trigger('make_payment_refund');
            });
            $('button[data-label="Mark as Refunded"]').removeAttr("class");
            $('button[data-label="Mark as Refunded"]').attr("class", "btn btn-xs btn-primary");
            $('button[data-label="Mark as Refunded"]').html("<i class='fa fa fa-eye' style='margin-right:5px'></i> Mark as Refunded");
        }
        if (frm.doc.__unsaved && frm.check_order_settings.allow_admin_to_edit_order == 1){
            frm.set_value('status', "Placed");
            frm.set_value('payment_status', "Pending");
            frm.set_value('shipping_status', "");
            frm.set_value('paid_using_wallet', 0);
            frm.set_value('status_history', []);
            frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.order.order.check_installed_app',
            args: { "app_name": "loyalty" },
            async: false,
            callback: function(d) {
                if(d.message==true){
                 frm.set_value('loyalty_amount', 0);
                
                frm.set_value('loyalty_points', 0);
                frm.set_value('redeem_loyalty_points', 0);
                    }
                }
              })
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
        if (!frm.invoiceid) {
            frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.order.order.get_order_settings',
                args: { "order_id": frm.doc.name, 'doctype': frm.doc.doctype },

                async: false,
                callback: function(d) {
                    if (d.message) {
                        frm.order_settings = d.message;
                        if (frm.order_settings.enable_invoice == 1 && frm.order_settings.automate_invoice_creation == 0 && frm.doc.docstatus == 1) {
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
        if (frm.doc.__islocal != 1) {

            let img_html = '';
            if (cur_frm.doc.order_from == "Website") {
                img_html = `<i class="fa fa-globe" style="float: left;margin-top: 11px;margin-right: 10px;color:#267db9;margin-bottom: 10px;"></i>`;
            } else if (cur_frm.doc.order_from == "Android Mobile App")

            {
                img_html = `<i class="fa fa-android" style="float: left;margin-top: 11px;margin-right: 10px;color: #28a744;"></i>`;
            } else {
                img_html = `<i class="fa fa-apple" style="float: left;margin-top: 11px;margin-right: 10px;color: #333;"></i>`;
            }
            img_html += '<span style="margin-top: 8px;float: left;"> ' + cur_frm.doc.name + '</span>'
            var creationDate = new Date(cur_frm.doc.creation);
            var customizeDate = getMonthName(creationDate.getMonth()) + " " + pad(creationDate.getDate().toString(), 2) + ", " + creationDate.getFullYear().toString() + " at ";
            var timtype = "AM";
            var hrs = creationDate.getHours();
            if (creationDate.getHours() > 11) {
                timtype = "PM";
                if (creationDate.getHours() > 12) {
                    hrs = hrs - 12;
                }

            }
            customizeDate += pad(hrs.toString(), 2) + ":" + pad(creationDate.getMinutes().toString(), 2) + " " + timtype;
            cur_frm.page.$title_area.find('.indicator').hide();
            cur_frm.page.$title_area.find('.go-backbtn').attr("style", "font-size: 13px;float: left;margin-left: 10px;margin-top: -5px;font-size: 15px;/* position: absolute; */bottom: 5px;/* right: 0; */height: 30px;margin-top: 32px;");

            var payment_status = "Unpaid";
            var statusHtml = '<span class="indicator whitespace-nowrap orange" style="float: left;margin-left: 10px;margin-top: 2px;font-size: 15px;">Un Paid</span>';
            if (cur_frm.doc.payment_status == "Paid") {
                payment_status = "Paid";
                statusHtml = '<span class="indicator whitespace-nowrap green" style="float: left;margin-left: 10px;margin-top: 2px;font-size: 15px;">Paid</span>';
            }
            if (cur_frm.doc.payment_status == "Partially Paid") {
                payment_status = "Partially Paid";
                statusHtml = '<span class="indicator whitespace-nowrap green" style="float: left;margin-left: 10px;margin-top: 2px;font-size: 15px;">Paid</span>';
            }
           
            if (cur_frm.doc.payment_status == "Refunded") {
                payment_status = "Refunded";
                statusHtml = '<span class="indicator whitespace-nowrap darkgrey" style="float: left;margin-left: 10px;margin-top: 2px;font-size: 15px;">Refunded</span>';
            }
            var shipmentHtml='';
            if(cur_frm.doc.is_shipment_bag_item==1){
                shipmentHtml='<span class="btn btn-xs btn-primary" style="float: left;margin-left: 10px;margin-top: 0;">Shipment Bag Item</span>';
            }
            var dateHtml = '<br/><div style="float:left;width:100%"><span style="float: left;margin-right: 5px;margin-top: -5px;font-size: 13px;">' + cur_frm.doc.order_from + ' - </span><span style="font-size:13px;margin-top: -5px;float: left;">' + customizeDate + '</span>' + statusHtml +shipmentHtml+ '</div>';
            setTimeout(function() {
                cur_frm.page.$title_area.find('.title-text').css("max-width", "100%");
                
                if (payment_status == "Paid") {
                    cur_frm.page.$title_area.find('.indicator').removeClass("grey")
                    cur_frm.page.$title_area.find('.indicator').addClass("green")
                }
                else if (payment_status == "Refunded") {
                    cur_frm.page.$title_area.find('.indicator').removeClass("grey")
                    cur_frm.page.$title_area.find('.indicator').addClass("darkgrey")
                    
                } else {
                    cur_frm.page.$title_area.find('.indicator').removeClass("grey")
                    cur_frm.page.$title_area.find('.indicator').addClass("orange")
                }
                cur_frm.page.$title_area.find('.indicator').text(payment_status)
            }, 0)
        }
        if (!frm.doc.__islocal) {
            frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.order.order.get_order_settings',
                args: { "order_id": frm.doc.name, 'doctype': frm.doc.doctype },

                callback: function(r) {
                    if (r.message) {
                        if (has_common(frappe.user_roles, ['Admin', 'Super Admin'])) {
                            $(".main-section [id='page-Form/Order']").find('.page-head .page-actions').find('.menu-btn-group').removeClass('hide');
                        }

                    }
                }
            })

            let wrapper = $(frm.get_field('order_detail_html').wrapper).empty();
            if (frm.doc.order_info) {
                $(cur_frm.doc.order_info).appendTo(wrapper);
                if (cur_frm.get_field('preparation_time').df.hidden == 0) {
                    if (frm.doc.restaurant_status == 'Pending' && !frm.doc.preparation_time) {
                        let html = `<h5>Preparation Time (In minutes)</h5>
                                    <div>
                                        <div class="frappe-control input-max-width" data-fieldtype="Data" data-fieldname="preparation_time" title="preparation_time">
                                            <div class="form-group">
                                                <div class="control-input-wrapper">
                                                    <div class="control-input">
                                                        <input type="text" autocomplete="off" class="input-with-feedback form-control" maxlength="140" data-fieldtype="Data" data-fieldname="preparation_time" placeholder="" data-doctype="Order">
                                                    </div>
                                                    <div class="control-value like-disabled-input" style="display: none;"></div>
                                                    <p class="help-box small text-muted hidden-xs"></p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>`;
                        $("div[data-fieldname='order_detail_html']").find("#order-detail-div #custom-info").append(html);
                        $("div[data-fieldname='order_detail_html']").find("#order-detail-div #custom-info").find('input[data-fieldname="preparation_time"]').change(function() {
                            frm.set_value('preparation_time', this.value);
                        })
                    }
                }
            }
                       
        }
        if (frm.doc.docstatus == 1) {
            if (frm.doc.status != 'Cancelled' && frm.doc.outstanding_amount > 0) {
                if (frm.order_settings.enable_invoice == 0) {
                    frm.remove_custom_button('Make Payment');
                    frm.add_custom_button("Make Payment", function() {
                        frm.trigger("make_payment");
                    });

                    $('button[data-label="Make%20Payment"]').removeAttr("class");
                    $('button[data-label="Make%20Payment"]').attr("class", "btn btn-xs btn-primary");
                    $('button[data-label="Make%20Payment"]').html("<i class='fa fa fa-plus-circle' style='margin-right:5px'></i> Make Payment");
                }
            } else if (frm.doc.status == 'Cancelled' && frm.doc.outstanding_amount > 0) {
                frm.remove_custom_button('Make Payment');
                $('button[data-label="Make%20Payment"]').removeAttr("class");
                $('button[data-label="Make%20Payment"]').attr("class", "btn btn-xs btn-primary");
                $('button[data-label="Make%20Payment"]').html("<i class='fa fa fa-plus-circle' style='margin-right:5px'></i> Make Payment");
            }
            if(cur_frm.doc.is_shipment_bag_item==1){

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
                            if (d.message.enable_returns_system) {
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
            $(frm.fields_dict['customer_payment'].wrapper).html(frappe.render_template("customer_payment", { payments: "", button_enable: 0, order: frm.doc.name }));
            frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.order.order.get_customer_payments',
                args: {
                    'order': frm.doc.name
                },
                async: false,
                callback: function(data) {

                    if (data.message) {
                        if (data.message.length > 0) {
                            $(frm.fields_dict['customer_payment'].wrapper).html(frappe.render_template("customer_payment", { payments: data.message, button_enable: 0, order: frm.doc.name }));
                        }
                    }
                }
            });
            frm.set_df_property('status', 'read_only', 1)
            frm.set_df_property('payment_status', 'read_only', 1)
            frm.set_df_property('restaurant_status', 'read_only', 1)
            frm.set_df_property('driver_status', 'read_only', 1)
            frm.set_df_property('order_subtotal', 'read_only', 1)
        }
        cur_frm.set_query("customer", function(frm) {
            return {
                query: "go1_commerce.go1_commerce.doctype.order.order.get_customers",
                filters: {}
            }
        });
        cur_frm.set_query("business", "order_item", function(frm,cdt, cdn) {
            var d = frappe.get_doc(cdt, cdn);
            return {
                query: "go1_commerce.go1_commerce.doctype.order.order.get_item_business",
                filters: {"item":d.item}
            }
        });
        cur_frm.set_query("item", "order_item", function(frm, cdt,cdn) {
            return {
                "filters": {
                    "status":"Approved"
                }
            }
        });
        cur_frm.set_query("kitchen_status", "order_item", function(frm) {
            return {
                "filters": {

                },
                "order_by": "display_order asc"
            }
        });
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
            frm.set_df_property('addons', 'readonly', 1)
        }

        if (frm.doc.tax_breakup) {
            frm.trigger('show_tax_spliup')
        }
        frm.trigger('show_commission_info');
    },
    validate: function(frm){
        let seller =""
        $.each(frm.doc.order_item, function (i, v) {
            if(!v.business){
                seller+="<li>row #"+(i+1).toString()+": "+v.item+"<b>("+v.item_name+")</b></li>"
            }
        })
        console.log(seller)
        if(seller){
            frappe.throw("<p>Please select seller for the following items:</p> <ul>"+seller+"</ul>")
        }
        
    },
    make_payment_refund: function(frm){

        let dialog;
        dialog = new frappe.ui.Dialog({
            title: __('Refund Payment'),
            fields: [
                { fieldtype: "Currency", label: __("Paid Amount"), fieldname: "paid_amount",reqd:0,read_only:1, default:frm.doc.paid_amount},
                { fieldtype: "Currency", label: __("Amount To Be Refund"), fieldname: "refund_amount",reqd:1, default:frm.doc.paid_amount},
            ],
            primary_action_label: __('Close')
        });
        dialog.set_primary_action(__('Confirm'), function() {
            console.log(dialog)
            var refund = dialog.get_values()
            console.log(refund)
            frappe.call({
                method: "go1_commerce.go1_commerce.doctype.order.order.make_refund",
                args: {"refund_amount": refund.refund_amount, "order": cur_frm.doc.name},
                async: false,
                callback: function(r) {
                    console.log(r.message)
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
    customer: function(frm) {
        if (frm.doc.customer) {
           
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    'doctype': 'Customers',
                    'filters': { 'name': frm.doc.customer },
                    'fieldname': ['full_name', 'email', 'first_name','last_name', 'phone', 'email',
                    'address', 'country', 'state', 'city', 'zipcode', 'landmark','business_name','store_name',
                    'business_address','business_state','business_landmark','business_city','business_country',
                    'business_zip','business_phone']
                },
                callback: function(r) {
                    var data = r.message;
                    console.log(data)
                    if (data) {
                        frm.set_value('customer_name', data.full_name)
                        frm.set_value('customer_email', data.email)

                   
                    frm.set_value("first_name", data.store_name);
                    frm.set_value("address", data.business_address);
                    frm.set_value("city", data.business_city);
                    frm.set_value("state", data.business_state);
                    frm.set_value("country", data.business_country);
                    frm.set_value("zipcode", data.business_zip);
                    frm.set_value("phone", data.business_phone);
                    frm.set_value("landmark", data.business_landmark);

                    frm.set_value("shipping_first_name", data.store_name);
                    frm.set_value("shipping_shipping_address", data.business_address);
                    frm.set_value("shipping_city", data.business_city);
                    frm.set_value("shipping_state", data.business_state);
                    frm.set_value("shipping_country", data.business_country);
                    frm.set_value("shipping_zipcode", data.business_zip);
                    frm.set_value("shipping_phone", data.business_phone);
                     frm.set_value("shipping_landmark", data.business_landmark);
                    }

                }
            })
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
    select_shipment_method: function() {

        let shipment_dialog = new frappe.ui.Dialog({
            title: 'Shipping Providers',
            fields: [
                
                {
                    "fieldname": "shipping_providers_html",
                    "fieldtype": "HTML"
                }
            ],
            primary_action_label: __('Close')
        });
        shipment_dialog.show();
        setTimeout(function() {
            cur_frm.trigger('get_shipment_providers');
        }, 500);
        
    },
    get_shipment_providers: function() {
        cur_dialog.fields_dict["shipping_providers_html"].$wrapper.html('');
        var drp_html = '<div class="select_list">'
        frappe.call({
            method: "shipping_providers.shipping_providers.api.shipping_providers_list",
            args: {},
            async: false,
            callback: function(r) {
                if (r && r.message != "no providers found") {
                    if (r.message.length > 0) {
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
                            myArray.push({ group: groupName, provider_name: groups[groupName] });
                        }
                        for (var i = 0; i < myArray.length; i++) {
                            drp_html += '<h4>' + myArray[i].group + '</h4><ul>'
                            var provider_type = (myArray[i].group).replace(" ", "_")
                            var providers = myArray[i].provider_name
                            for (var j = 0; j < providers.length; j++) {
                                let providerid = providers[j].replace(" ", "_")
                                drp_html += '<li>' + providers[j] + '<span data-id=' + providerid + ' data-type=' + provider_type + ' class="tick"><button class="btn info">Select</button></span></li>'
                                if (j == providers.length - 1) {
                                    drp_html += '</ul>'
                                }
                            }
                        }

                    } else {
                        cur_dialog.$wrapper.remove()
                        frappe.throw("No shipping providers configured")
                    }
                } else {
                    cur_dialog.$wrapper.remove()
                    frappe.throw("No shipping providers configured")
                }
            }
        });
        drp_html += '</div>'
        cur_dialog.fields_dict["shipping_providers_html"].$wrapper.append(drp_html);
        var tick_buttons = cur_dialog.fields_dict["shipping_providers_html"].$wrapper.find('span.tick');
        if (tick_buttons) {
            for (var k = 0; k < tick_buttons.length; k++) {
                tick_buttons[k].addEventListener("click", function() {
                    var shipping_provider_id = $(this).attr('data-id')
                    let provider_type = $(this).attr('data-type').replace("_", " ")
                    frappe.shipping_provider = (shipping_provider_id).replace("_", " ")
                    frappe.confirm(__("Are you sure want to proceed shipping with '" + frappe.shipping_provider + "'?"), () => {
                        if (provider_type == "Shipping Aggregator") {
                            cur_frm.trigger('check_shipment_provider');
                        } else {
                            cur_frm.trigger('select_shipping_driver');
                        }
                    });
                });
            }
        }
    },
    check_shipment_provider: function(frm) {
        frappe.call({
            method: 'shipping_providers.shipping_providers.api.check_provider_settings',
            args: { 'provider': frappe.shipping_provider, 'orderid': cur_frm.doc.name },
            callback: function(d) {
                if (d.message == "success") {
                    cur_frm.trigger('use_shipment_provider');
                }
            }
        });
    },
    use_shipment_provider: function(frm) {
        var doctype = frappe.shipping_provider.toLowerCase() + '_settings';
        var settings_doctype = doctype.replace(" ", "_")
        var method = 'shipping_providers.shipping_providers.doctype.' + settings_doctype + '.' + settings_doctype + '.make_shipment';
        frappe.call({
            method: method,
            args: { 'orderId': cur_frm.doc.name },
            callback: function(d) {

                cur_dialog.$wrapper.remove()
            }
        });
    },
    select_shipping_driver(frm) {
        cur_dialog.$wrapper.remove()
        let shipment_dialog = new frappe.ui.Dialog({
            title: 'Shipping Drivers',
            fields: [{
                "fieldname": "drivers_html",
                "fieldtype": "HTML"
            }],
            primary_action_label: __('Close')
        });
        shipment_dialog.show();
        setTimeout(function() {
            cur_frm.trigger('generate_drivers_html');
        }, 500);
    },
    generate_drivers_html(frm) {
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
            args: { 'name': frappe.shipping_provider },
            async: false,
            callback: function(d) {
                if (d && d.message.length > 0) {
                    d.message.map(f => {
                        if (f) {
                            if (f.working_status == "Available") {
                                let row_data = $(`<tr>
                                    <td>${f.driver_name}</td>
                                    <td>${f.working_status}</td>
                                    <td align="center"><span data-id="${f.name}" style="cursor:pointer" class="select_list"><button class="btn info">Select</button></span></td>
                                </tr>`);
                                table_html.find('tbody').append(row_data);
                            } else {
                                let row_data = $(`<tr>
                                    <td>${f.driver_name}</td>
                                    <td>${f.working_status}</td>
                                    <td align="center"></td>
                                </tr>`);
                                table_html.find('tbody').append(row_data);
                            }
                        }
                    })
                } else {
                    let row_data = $(`<tr>
                        <td colspan="3" align="center">No drivers mapped for this provider</td>
                        </tr>`);
                    table_html.find('tbody').append(row_data);
                }
            }
        });
        frappe.shipping_driver = ''
        var driver_buttons = cur_dialog.fields_dict["drivers_html"].$wrapper.find('span.select_list');
        if (driver_buttons) {
            for (var k = 0; k < driver_buttons.length; k++) {
                driver_buttons[k].addEventListener("click", function() {
                    var shipping_driver_id = $(this).attr('data-id')
                    frappe.confirm(__("Are you sure want to assign this driver?"), () => {
                        frappe.shipping_driver = shipping_driver_id
                        cur_frm.trigger('order_readyto_shipped');
                    });
                });
            }
        }
        var link = cur_dialog.fields_dict["drivers_html"].$wrapper.find('a#without_driver')
        link.click(function() {
            frappe.confirm(__("Are you sure want to proceed without driver?"), () => {
                cur_frm.trigger('order_readyto_shipped');
            });
        });

    },
    order_readyto_shipped: function(frm) {
        var method = 'go1_commerce.go1_commerce.api.order_readyto_shipped';
        frappe.call({
            method: method,
            args: { 'orderid': cur_frm.doc.name, 'shipping_provider': frappe.shipping_provider, 'shipping_driver': frappe.shipping_driver },
            callback: function(d) {
                cur_dialog.$wrapper.remove();
                location.reload();
            }
        });
    },
    use_shiprocket: function() {
        frappe.call({
            method: 'shipping_providers.shipping_providers.api.check_pickuplocation_for_orderitems',
            args: { 'orderId': cur_frm.doc.name },
            callback: function(d) {

            }
        });
    },
    restaurant: function(frm) {

    },
    vat: function(frm) {
        if (frm.doc.vat) {
            var amount = 0;
            if (frm.doc.total_amount)
                amount = frm.doc.total_amount
            amount = amount + parseFloat(frm.doc.vat)
            frm.set_value('total_amount', amount)
        }
    },
    create_return: function(frm) {
        let returns = frm.doc.order_item.filter(obj => obj.return_created != 1);
        let html = '<table id="returnTable" class="table table-bordered"><thead style="background: #F7FAFC;"><tr>\
            <th></th><th>Product</th><th>Quantity</th></tr></thead><tbody>'
        $(returns).each(function(k, v) {
            html += '<tr data-name="' + v.name + '"><input type="hidden" class="productId" value="' + v.item + '"/>\
                <td><input type="checkbox" class="grid-row-check pull-left"></td>\
                <td style="width:70%;">' + v.item_name + '</td><td><div class="control-input">\
                <input type="text" autocomplete="off" class="input-with-feedback form-control" \
                data-fieldtype="Int" data-fieldname="quantity" placeholder="" \
                data-doctype="Order Item" value="' + v.quantity + '"></div></td></tr>';
        })
        html += '</tbody></table>'
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
            $('#returnTable').find('tbody tr').each(function() {
                if ($(this).find('.grid-row-check:checked').val()) {
                    let data = {};
                    data.item = $(this).find('.productId').val();
                    data.item_name = $(this).find('td:eq(1)').text()
                    data.quantity = $(this).find('input[data-fieldname="quantity"]').val();
                    let check_data = returns.find(obj => obj.name == $(this).attr('data-name'));   
            
                    if (check_data) {
                        if (check_data.quantity < parseInt(data.quantity)) {
                            allow_form = false;
                            frappe.msgprint('Quantity cannot be greater than ' + data.quantity + ' for item ' + data.item_name, 'Alert')
                        } else {
                            if (data.quantity > 0)
                            {
                data.price = parseFloat(check_data.price)
                data.amount = parseFloat(check_data.price)*parseInt(data.quantity)
                data.shipping_charge = parseFloat(check_data.shipping_charges)
                                lists.push(data)
                            }
                            else {
                                allow_form = false;
                                frappe.msgprint('Quantity must be greater than 0 for item ' + data.item_name, 'Alert')
                            }
                        }
                    }
                }
            })
            formData.order = frm.doc.name
            formData.return_reason = values.return_reason
            formData.return_action = values.return_action
            formData.comments = values.comments
            formData.order_shipping_charge = parseFloat(frm.doc.shipping_charges)
            formData.products = lists
            if (lists.length > 0 && allow_form == true) {
                frappe.call({
                    method: 'go1_commerce.go1_commerce.api.create_return_request',
                    args: {
                        data: JSON.stringify(formData)
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
            method: 'go1_commerce.go1_commerce.api.get_checkout_attributes',
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
        var checkout_attributes_html = '<table id="tbl-attributes-' + parseInt(randomuppy) + '" class="table table-bordered"><thead><tr><th style="width:35%">Question</th><th>Customer Repsonse</th></tr></thead><tbody>';
        
        $(frm.__checkout_attributes).each((k, v) => {
            let check_row = frm.doc.checkout_attributes.find(obj => obj.attribute_id == v.name);
            let val = '';
            if (check_row) {
                let value = check_row.attribute_description.split(':')[1].split('<br>')[0];
                if (value) {
                    val = $(value).html();
                }
            }
            let row = `<tr data-id="${(check_row && check_row.name) || ''}" data-question="${v.name}">
              <td>
                  <span class="attr-title">${v.question}</span>
              </td>
              <td>
                  <textarea style="width: 100%;border-color: #d3d3d3;">${val}</textarea>
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
                    let child_row = `<tr data-id="${(check_child_row && check_child_row.name) || ''}" data-question="${val.name}">
                      <td>
                          <span class="attr-title">${val.question}</span>
                      </td>
                      <td>
                          <textarea style="width: 100%;border-color: #d3d3d3;">${child_val}</textarea>
                      </td>
                      </tr>`;
                    checkout_attributes_html += child_row;
                })
            }
        })
        checkout_attributes_html += '</tbody></table>';
        dialog.fields_dict.checkout_attributes.$wrapper.html(checkout_attributes_html);
        dialog.show();
        dialog.$wrapper.find('.modal-dialog').css("width", "1000px");

    },
    order_shipping_options: function(frm) {
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.order.order.get_customer_loyaltypoints',
            args: { "order_total": frm.doc.outstanding_amount, 'customer_id': frm.doc.customer},
            async: false,
            callback: function(d) {
                if (d.message) {
                    let dialog;
                     var optionhtml = "<option value='0-0'>Select Points</option>";
                    for (var i = 0; i < d.message.checkout_points.flat_rates.length; i++) {
                        var is_selected = "";
                        if((d.message.checkout_points.flat_rates[i].amount + "-" + d.message.checkout_points.flat_rates[i].noof_points) == (frm.doc.loyalty_amount+"-"+frm.doc.loyalty_points))
                        {
                            is_selected = "selected";
                        }
                        optionhtml += "<option value='" + d.message.checkout_points.flat_rates[i].amount + "-" + d.message.checkout_points.flat_rates[i].noof_points + "' "+is_selected+">" + d.message.checkout_points.flat_rates[i].noof_points + " Points = "+d.message.settings.default_currency + d.message.checkout_points.flat_rates[i].amount + "</option>";
                    }
                    dialog = new frappe.ui.Dialog({
                        title: __('Order Totals'),
                        fields: [
                            { fieldtype: "Currency", label: __("Shipping Charges"), fieldname: "edit_shipping_charges", reqd: 1, default: frm.doc.shipping_charges },
                            { fieldtype: "Currency", label: __("Discount"), fieldname: "edit_discount", reqd: 1 },
                            { fieldtype: "Currency", label: __("Wallet"), fieldname: "edit_wallet", reqd: 1 },
                            { fieldtype: "HTML", label: __("Reward / Loyalty Amount"), fieldname: "edit_loyalty_amount"},
                        ],
                        primary_action_label: __('Close')
                    });
                    dialog.set_primary_action(__('Save'), function() {
                        let values = dialog.get_values();
                        var loyalty_pts = dialog.$wrapper.find("#pointsdrp").val();

                        frappe.call({
                            method: 'go1_commerce.go1_commerce.doctype.order.order.update_order_totals',
                            args: {
                                "order": frm.doc.name,
                                "shipping_charges": values.edit_shipping_charges,
                                "discount_amount": values.edit_discount,
                                "Wallet_amount": values.edit_wallet,
                                "loyalty_amount": loyalty_pts.split('-')[0],
                                "loyalty_points": loyalty_pts.split('-')[1]
                            },
                            async: false,
                            callback: function(d) {
                                cur_frm.reload_doc()
                                dialog.hide()
                            }
                        })

                    });
                    dialog.show();
                    var loyalty_html = '<label class="control-label">Reward / Loyalty Points</label>';
                    dialog.fields_dict["edit_loyalty_amount"].$wrapper.html(loyalty_html+"<select id='pointsdrp' class='form-control'>"+optionhtml+"</select");
                    $('[data-fieldname="edit_shipping_charges"]').val(frm.doc.shipping_charges)
                    dialog.set_value("edit_shipping_charges", frm.doc.shipping_charges)
                    dialog.set_value("edit_discount", frm.doc.discount)
                    dialog.set_value("edit_wallet", frm.doc.paid_using_wallet)
                }
            }
        })
        


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
                        console.log(d.message);
                        if(d.message.length>0 && d.message[0].dates_lists){
                            var options=[];
                            console.log(d.message[0].dates_lists);
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
        console.log(frm.slot_dates_lists)
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
            frm.set_df_property('status', 'hidden', 1);
            frm.set_df_property('payment_status', 'hidden', 1);
            frm.set_df_property('discount_coupon', 'hidden', 1);
            frm.set_df_property('delivery_date', 'hidden', 0);
            frm.set_df_property('delivery_slot', 'hidden', 0);

            
            $('button.btn.btn-primary.btn-sm.primary-action').removeClass("hide");
            $('button.btn.btn-primary.btn-sm.primary-action').html('<i class="visible-xs octicon octicon-check"></i><span class="hidden-xs" data-label="Update">Upda<span class="alt-underline">t</span>e</span>');
            $("button.btn.btn-secondary.btn-default.btn-sm").addClass("hide")
            $('button[data-label="Edit%20Order"]').html("<i class='fa fa-arrow-circle-left' style='margin-right:5px'></i> Back to Order Detail");
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
    },
    show_tax_spliup: function(frm) {
        let wrapper = $(frm.get_field('tax_splitup').wrapper).empty();
        let table_html = $(`<table class="table table-bordered" style="cursor:pointer; margin:0px;">
            <thead>
                <tr>
                    <th style="width: 70%">Tax</th>
                    <th>Tax %</th>
                    <th>Tax Amount</th>
                    <th>Tax Type</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>`).appendTo(wrapper);
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
    show_commission_info: function(frm) {
        let wrapper = $(frm.get_field('commission_info').wrapper).empty();
        let table_html = $(`<table class="table table-bordered" style="cursor:pointer; margin:0px;">
            <thead>
                <tr>
                    <th style="width: 70%">${__("Total Splitup")}</th>
                    <th style="text-align: right;">${__("Amount")}</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>`).appendTo(wrapper);
        table_html.find('tbody').append(`<tr>
            <td>${__("Order Subtotal")}</td>
            <td style="text-align: right;">${parseFloat(frm.doc.order_subtotal).toFixed(2)}</td>
        </tr>`);
        if (frm.doc.vendor_discount && frm.doc.service_provider_discount) {
            table_html.find('tbody').append(`<tr>
                <td>${__("Vendor Discount")}</td>
                <td style="text-align: right;">${parseFloat(frm.doc.vendor_discount).toFixed(2)}</td>
            </tr>`);
            table_html.find('tbody').append(`<tr>
                <td>${__("Service Provider Discount")}</td>
                <td style="text-align: right;">${parseFloat(frm.doc.service_provider_discount).toFixed(2)}</td>
            </tr>`);
        }
        table_html.find('tbody').append(`<tr>
            <td>${__("Discount")}</td>
            <td style="text-align: right;">${parseFloat(frm.doc.discount).toFixed(2)}</td>
        </tr>`);
        if (frm.doc.shipping_charges < frm.doc.actual_shipping_charges) {
            table_html.find('tbody').append(`<tr>
                <td>${__("Delivery Charges")}</td>
                <td style="text-align: right;">
                    <span style="margin-right: 5px;text-decoration: line-through;font-size: 12px;">${parseFloat(frm.doc.actual_shipping_charges)}</span>
                    ${parseFloat(frm.doc.shipping_charges).toFixed(2)}
                </td>
            </tr>`);
        } else {
            table_html.find('tbody').append(`<tr>
                <td>${__("Delivery Charges")}</td>
                <td style="text-align: right;">${parseFloat(frm.doc.shipping_charges).toFixed(2)}</td>
            </tr>`);
        }
    
        table_html.find('tbody').append(`<tr>
            <td>${__("Tax")}</td>
            <td style="text-align: right;">${parseFloat(frm.doc.total_tax_amount).toFixed(2)}</td>
        </tr>`);
        
        table_html.find('tbody').append(`<tr>
            <td>${__("Service Provider Commission")}</td>
            <td style="text-align: right;">${parseFloat(frm.doc.commission_amt).toFixed(2)}</td>
        </tr>`);
        table_html.find('tbody').append(`<tr>
            <td>${__("Amount For Vendors")}</td>
            <td style="text-align: right;">${parseFloat(frm.doc.total_amount_for_vendor).toFixed(2)}</td>
        </tr>`);
        if (frm.doc.driver) {
            table_html.find('tbody').append(`<tr>
                <td>${__("Driver Charges")}</td>
                <td style="text-align: right;">${parseFloat((frm.doc.total_driver_charges || frm.doc.driver_charges)).toFixed(2)}</td>
            </tr>`);
        }
        table_html.find('tbody').append(`<tr>
            <td>${__("Total Amount")}</td>
            <td style="text-align: right;">${parseFloat(frm.doc.total_amount).toFixed(2)}</td>
        </tr>`);
    }
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
                                if(data.message){
                                    (data.message[0]).forEach(function(row) {
                                        if(row){
                                            options.push({"value":row.attribute_id,"label":row.combination_txt}) 
                                        }
                                        
                                    })
                                }
                                frm.fields_dict.order_item.grid.update_docfield_property(
                                    "attribute", "options",
                                    [""].concat(options)
                                );
                                cur_frm.refresh_fields();
                            

                            }
                        })
            }
        },
    item: function(frm, cdt, cdn) {
        var d = frappe.get_doc(cdt, cdn);
        if (d.item) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    'doctype': 'Product',
                    'filters': { 'name': d.item },
                    'fieldname': ['price', 'item']
                },
                callback: function(data) {
                    if (data.message) {
                        frappe.model.set_value(cdt, cdn, "amount", data.message.price);
                        frappe.model.set_value(cdt, cdn, "attribute", "");
                        frappe.model.set_value(cdt, cdn, "item_name", data.message.item);
                    }
                }
            })
           
             var d = frappe.get_doc(cdt, cdn);
             frappe.call({
                        method: "go1_commerce.go1_commerce.doctype.order.order.get_attributes_combination",
                        args: {
                            product: d.item
                        },
                        callback: function(data) {
                            
                            var options = [];
                            var htm =' <select type="text" autocomplete="off" class="input-with-feedback form-control ellipsis" maxlength="140" data-fieldtype="Select" data-fieldname="attribute" placeholder="" data-doctype="Order Item"><option></option>'
                            if(data.message){
                                (data.message[0]).forEach(function(row) {
                                    if(row){
                                        htm +='<option value="'+row.attribute_id+'">'+row.combination_txt+'</option>'
                                        options.push({"value":row.attribute_id,"label":row.combination_txt}) 
                                    }
                                    
                                })
                                htm +='</select>'
                            }
                           
                            frm.fields_dict.order_item.grid.update_docfield_property(
                        "attribute", "options",
                        [""].concat(options)
                        );
                        
                        cur_frm.fields_dict["order_item"].grid.grid_rows_by_docname[d.name].get_field("attribute").$wrapper.find("select").html(htm)
                        cur_frm.refresh_fields();
                           

                        }
                    })
                }
    },
    attribute: function(frm, cdt, cdn){
         var d = frappe.get_doc(cdt, cdn);
        if(d.business && d.item && frm.doc.customer){
              frappe.call({
                method: "go1_commerce.go1_commerce.pricing.get_customer_product_pricing",
                args: {"product": d.item, "attribute":d.attribute, "business": d.business, "customer":frm.doc.customer},
                async: false,
                callback: function(r) {
                    console.log(r.message)
                   if( r.message){
                     if(r.message.length>0){
                        frappe.model.set_value(cdt, cdn, "price", r.message[0].price);
                         frappe.model.set_value(cdt, cdn, "base_price", r.message[0].price);
                         frappe.model.set_value(cdt, cdn, "amount", r.message[0].price* d.quantity);
                         frappe.model.set_value(cdt, cdn, "t_amount", r.message[0].price* d.quantity);
                     }
                     else{
                        frappe.throw("No mapping for product,seller and warehouse")
                     }
                   }

                }
            })
        }
    },
    business: function(frm, cdt, cdn) {
         var d = frappe.get_doc(cdt, cdn);
         if(d.business){
             frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    'doctype': 'Business',
                    'filters': { 'name': d.business },
                    'fieldname': ['restaurant_name']
                },
                callback: function(data) {
                    if (data.message) {
                        frappe.model.set_value(cdt, cdn, "business_name", data.message.restaurant_name);
                    }
                }
                })
         }
         if(!frm.doc.customer){
            frappe.throw("Please select Customer.")
         }
        if(d.business && d.item && frm.doc.customer){
            
              frappe.call({
                method: "go1_commerce.go1_commerce.pricing.get_customer_product_pricing",
                args: {"product": d.item, "attribute":d.attribute, "business": d.business, "customer":frm.doc.customer},
                async: false,
                callback: function(r) {
                    console.log(r.message)
                   if( r.message){
                     if(r.message.length>0){
                        frappe.model.set_value(cdt, cdn, "price", r.message[0].price);
                        frappe.model.set_value(cdt, cdn, "base_price", r.message[0].price);
                         frappe.model.set_value(cdt, cdn, "amount", r.message[0].price* d.quantity);
                     }
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
        method: 'go1_commerce.go1_commerce.api.update_order_status',
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
var notifyDrivers = function(frm) {
    frappe.call({
        method: 'go1_commerce.go1_commerce.api.assign_driver',
        args: {
            order: frm.doc.name
        },
        callback: function(data) {
            location.reload();
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
