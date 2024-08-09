
// Copyright (c) 2018, info@valiantsystems.com and contributors
// For license information, please see license.txt


frappe.ui.form.on('Customers', {
    refresh: function(frm) {
        frm.events.update_css_and_events(frm)
        frm.events.filter_link_fields(frm)
        frm.events.customer_order(frm)
        frm.events.add_custom_buttons(frm)
        frm.events.render_dashboard(frm)		
	},
	after_save:function(frm){
		cur_frm.reload_doc();
	},
    set_roles_in_table: function (frm) {
        let selected_options = frm.role_multicheck.get_value();
        frm.set_value("role_list", JSON.stringify(selected_options))
        refresh_field('role_list');
    },
    update_css_and_events(frm){
        if(frappe.get_module('Loyalty')){
			frm.set_df_property('parent_level', 'hidden', 0);
        }
		else{
			frm.set_df_property('parent_level', 'hidden', 1);
        }
        if (frm.doc.__islocal) {
            $('[data-fieldname="__newname"]').parent().parent().parent().parent().hide()
            $('.form-dashboard').hide();
            $('.empty-section').hide();
            frm.set_df_property('customer_dashboard', 'hidden', 1);
        }
        else {
            $('.form-dashboard').show();
            $('.empty-section').show();
            $('.form-section-heading').hide();
        }
        $('div[data-fieldname="customer_identity_proof"] .grid-add-row').text('Add Personal KYC');
        $('div[data-fieldname="customer_address_proof"] .grid-add-row').text('Add Personal KYC');
        $('div[data-fieldname="customer_business_document"] .grid-add-row').text('Add Business KYC');
        $('div[data-fieldname="table_6"] .form-grid .grid-body').find('.grid-row .row-index').
            find("[data-fieldname='zipcode']").keyup(function() {
			    $(this).val($(this).val().replace(/^(\d{3})(\d{3})(\d{3})/, "($1)$2-$3"));
		});
		$('div[data-fieldname="table_6"] .form-grid .grid-body').find('.grid-row .row-index').
            find("[data-fieldname='phone']").keyup(function() {
			    $(this).val($(this).val().replace(/^(\d{3})(\d{3})(\d{3})/, "($1)$2-$3"));
		});
		$('div[data-fieldname="table_6"] .form-grid .grid-body').find("[data-fieldname='phone']").
            keyup(function() {
			    $(this).val($(this).val().replace(/^(\d{3})(\d{3})(\d{3})/, "($1)$2-$3"));
		});
    },
    filter_link_fields(frm){
        frm.set_query("center", function() {
            return {
                "filters": {
                    "approval_status" : "Approved",
                    "allow_product_listing" : 1,
                    "disabled" : 0,
                    "fulfillment_center" : 1
                }
            };
        });
    },
    add_custom_buttons(frm){
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.customers.customers.get_order_settings',
            async: false,
            callback: function(d) {
                if(d.message.impersonate_customer == 1){
                    frm.add_custom_button(__("Impersonate Customer"), function() {
                        frm.trigger('impersonate_customer')
                    });
                    $('button[data-label="Impersonate%20Customer"]').attr("class","btn btn-xs btn-primary");
                    $('button[data-label="Impersonate%20Customer"]').html("<i class='fa fa-user' style='margin-right:5px'></i> Impersonate Customer");
                }
                if(d.message.allow_multiple_address==1){
                    frm.set_value("allow_multiple_address",1);
                }
              
                if(d.message.auto_customer_approval==1){
                    frm.set_value("customer_status","Approved");
                }
            }
        })
    },
    render_dashboard(frm){
        if (!frm.doc.__islocal) {
            frappe.call({
                method: 'go1_commerce.go1_commerce.doctype.customers.customers.make_customers_dashboard',
                args: {
                    name: frm.doc.name
                },
                callback: function(r) {
                    $('.form-dashboard').removeClass('hidden')
                    let source = '';
                    if(r.message){
                        if(r.message.source){
                            if(r.message.source.length>0){
                                source = r.message.source
                            }
                        }
                    }
                    $(frm.fields_dict['customer_dashboard'].wrapper).html(
                        frappe.render_template("customer_dashboard", 
                                                { 
                                                    customer_id:frm.doc.name,
                                                    today_orders_count: r.message.today_orders_count,
                                                    all_count: r.message.all_count, 
                                                    currency:r.message.rupee, 
                                                    source:source,
                                                    loyalty_dashboard:r.message.loyalty_dashboard,
                                                    total_available_points:r.message.total_available_points
                                                }))
                    frm.set_df_property('customer_dashboard', 'hidden', 0);
                }
            })
        }
    },
    country:function(frm){
        frm.set_query("state", function() {
            return {
                "filters": {
                    "country": frm.doc.country,
                }
            };
        });
    },
    state:function(frm){
        frm.set_query("city", function() {
            return {
                "filters": {
                    "state": frm.doc.state,
                }
            };
        });
        
    },

    
    impersonate_customer:function(frm){
        var confirm_result = confirm("Are you sure want to Impersonate the customer?")
        if(confirm_result){
            frappe.call({
            args:{customer_id:frm.doc.name},
            method: 'go1_commerce.go1_commerce.doctype.customers.customers.impersonate_customer',
            async: false,
            callback: function(d) {
                  window.location.href="/";
                }
            })
        }
    },
    customer_order: function(frm) {
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.customers.customers.get_customer_orders',
            args: {
                customer_id: frm.doc.name
            },
            callback: function(r) {
                let val = r.message.order_detail
                if(val.length>0){
                let currency = r.message.currency
                let wrapper = $(frm.get_field('recent_orders').wrapper).empty();
                let html = $(`
                    <div style="border-radius: 2px;font-size: 16px;padding: 10px 13px;
                                border: 1px solid #ebebeb;border-bottom: 0px;font-weight: 600;
                                width: calc(100% );margin-left: 0px;background-color: #f5f5f5;">
                        <span style="font-size: 15px;">Recent Orders</span>
                        <span style="float: right;text-align: right;">
                            <a class="view_orders btn btn-sm btn-primary" style="display: block;
                                    color: #fff;margin-top: -5px;margin-right: -5px;">
                                <i class="fa fa-eye" style="margin-right: 5px;"></i>
                                View All Orders
                            </a>
                        </span>
                    </div>
                    <div class="items" style=" width: calc(100%);">
                        <table class="table table-bordered" style="cursor:pointer;margin:0px;
                                                                    border: 1px solid #ebebeb;">
                            <thead>
                                <tr>                       
                                    <th style="padding:10px 14px;border:0px;">Order ID</th>
                                    <th style="padding:10px 14px;border:0px;">Date</th>                    
                                    <th style="padding:10px 14px;border:0px;">Status</th>
                                    <th style="padding:10px 14px;border:0px;">Payment Method</th>
                                    <th style="padding:10px 14px;border:0px;">Payment Status</th>
                                    <th style="padding:10px 14px;border:0px;text-align:right;">Total</th>
                                </tr>
                            </thead> 
                            <tbody> </tbody>
                        </table>
                    </div>
                    <div class="page-list"></div>`).appendTo(wrapper);
                $(cur_frm.$wrapper).find('.page-list').attr("style", "float:right;margin-top:10px;")
                $('.table .recent_orders td').css('padding','10px 14px');
                var s_no = 0;
                $('.view_orders').click(function(){
                        window.open('/app/order?customer='+frm.doc.name, '_blank')
                   
                })
                if (val.length > 0) {
                    $('.view_orders').css('display','block')
                    val.map(f => {
                        s_no += 1;
                        f.s_no = s_no;
                        if (f.payment_status == "Pending") {
                            f.payment = '<span class="indicator red">Pending</span>'
                        }
                        if (f.payment_status == "Authorized") {
                            f.payment = '<span class="indicator grey">Authorized</span>'
                        }
                         if (f.payment_status == "Partially Paid") {
                            f.payment = '<span class="indicator green">Partially Paid</span>'
                        }
                        if (f.payment_status == "Paid") {
                            f.payment = '<span class="indicator green">Paid</span>'
                        }
                        let row_data = $(`
                            <tr class ="recent_orders" data-id="${f.name}" data-idx="${f.idx}">
                                <td style="padding:10px 14px;border-top: 1px solid #ebebeb !important;
                                            border:0px;">
                                    ${f.name}
                                </td>
                                <td style="padding:10px 14px;border-top: 1px solid #ebebeb !important;
                                            border:0px;">
                                    ${f.order_date}
                                </td>
                                <td style="padding:10px 14px;border-top: 1px solid #ebebeb !important;
                                            border:0px;">
                                    ${f.status}
                                </td>
                                <td style="padding:10px 14px;border-top: 1px solid #ebebeb !important;
                                            border:0px;">
                                    ${f.payment_method_name}
                                </td>
                                <td style="padding:10px 14px;border-top: 1px solid #ebebeb !important;
                                            border:0px;">
                                    ${f.payment}
                                </td>
                                <td style="padding:10px 14px;border-top: 1px solid #ebebeb !important;
                                            border:0px;text-align:right;">
                                    ${currency} ${f.total_amount.toFixed(2)}
                                </td>
                            </tr>`);
                        html.find('tbody').append(row_data);
                    });
                } else {
                    html.find('tbody').append(`<tr>
                                                    <td colspan="5">
                                                        No orders found
                                                    </td>
                                                </tr>`)
                }
            }
        }
        })
    },
	build_html: function(frm){
		 $(frm.get_field('role_html').wrapper).empty();
        if (!frm.doc.role_list) {
            frm.set_value("role_list", "[]");
        }
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.customers.customers.get_all_roles',
            args: {},
            callback: function (data) {
               console.log(data.message)
                if(data.message){
                    frm.role_multicheck = frappe.ui.form.make_control({
                        parent: frm.fields_dict.role_html.$wrapper,
                        df: {
                            fieldname: "role_multicheck",
                            fieldtype: "MultiCheck",
                            get_data: () => {
                                let active_tags = JSON.parse(frm.doc.role_list);
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
                    frm.role_multicheck.refresh_input();
                }
                else{
                     frm.set_df_property('sec_20', 'hidden', 1)
                }
            }
        });
	}
});