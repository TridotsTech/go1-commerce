// Copyright (c) 2018, info@valiantsystems.com and contributors
// For license information, please see license.txt

frappe.provide("go1_commerce.wallet");
frappe.ui.form.on('Wallet', {
    refresh: function(frm) {
        frm.events.update_css_property(frm)
        if(!frm.doc.__islocal){
            frm.events.get_wallet_settings(frm)
            frm.events.get_counter_apy_counters(frm)
            frm.transaction_list = [];
            if(cur_frm.disable_lockedin == 0){
                cur_frm.set_df_property('locked_in_amount',"in_list_view",0);
            }
            new go1_commerce.WalletOrders({
                page_len: 10,
                counter_page_len:10,
                user: frm.doc.user,
                type:"Transaction"
            })        
        }
        else{
            $(cur_frm.fields_dict['transaction_history'].wrapper).html("");
        }
    },
    update_css_property(frm){
        if(!frm.doc.__islocal){
            if(cur_frm.doc.name1){
                $('.page-container[data-page-route="Form/Wallet"]').find('.page-title').find('.title-text').text(cur_frm.doc.name+'('+cur_frm.doc.user+':'+cur_frm.doc.name1+')')
            }
            else{
                $('.page-container[data-page-route="Form/Wallet"]').find('.page-title').find('.title-text').text(cur_frm.doc.name+'('+cur_frm.doc.user+')')
            }
            cur_frm.$wrapper.find('.form-section').css('padding','0px');
            cur_frm.set_df_property('name1',"hidden",1);
            cur_frm.set_df_property('last_updated',"hidden",1);
            cur_frm.set_df_property('total_wallet_amount',"hidden",1);
            cur_frm.set_df_property('current_wallet_amount',"hidden",1);
            cur_frm.set_df_property('locked_in_amount',"hidden",1);
        }
        frm.set_df_property("restaurant", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("wallet_amount", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("last_updated", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("total_wallet_amount", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("locked_in_amount", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("restaurant_name", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("type", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("current_wallet_amount", "read_only", frm.doc.__islocal ? 0 : 1);
    },
    get_counter_apy_counters(frm){
        if(frm.doc.user){
            frappe.call({
                method: 'go1_commerce.accounts.doctype.wallet.wallet.get_counter_apy_counters',
                args: {"vendor":frm.doc.user},
                async: false,
                callback: function(data) {
                    if(data.message) {
                        if (data.message.length > 0) {
                            cur_frm.counter_pay_counter = data.message[0];
                        }  
                    }
                }
            })
        }
    },
    get_wallet_settings(frm){
        frappe.call({
            method: 'go1_commerce.accounts.doctype.wallet.wallet.get_wallet_settings',
            args: {},
            async: false,
            callback: function(data) {
                if (data.message) {
                    cur_frm.tab_settings = data.message.tab_settings
                    cur_frm.wallet_setting = data.message
                    cur_frm.enable_settlement =  data.message.enable_settlement
                    cur_frm.disable_lockedin =  data.message.disable_locked_in
                }
            }
        })
    },
    add_fund_vendor: function(frm){
        let d = {
            'page_no': 1,
            'page_len': 10
        }
        frm.fund_list = [];
        new go1_commerce.WalletOrders({
            page_len: 10,
            user: frm.doc.user,
            type:"Funds"
        })
    },
    get_orderlist: function(frm) {
        frm.order_list = [];
        new go1_commerce.WalletOrders({
            page_len: 10,
            user: frm.doc.user,
            type:"Settlement"
        })
    }
});

go1_commerce.WalletOrders = Class.extend({
    init: function(opts) {
        this.opts = opts;
        this.order_list = [];
        this.selected_fund_list = [];
        this.fund_list = [];
        this.transaction_list = [];
        this.total_records = 0;
        this.counterpay_transaction_list=[];
        this.couterpay_total_records=0
        this.currency=''
        this.page_no = 1;
        this.cur_frm = cur_frm;
        this.counter_page_no=1;
        this.order_html = '';
        cur_frm.selected_order_list = [];  
        this.already_added_orders = opts.order_list;
        this.setup();
    },

    setup: function() {
        let me = this;
        frappe.run_serially([
         () => {
            me.args = {};
            me.args.page_no = me.page_no;
            me.args.page_len = me.opts.page_len;
            me.args.counter_page_no = me.counter_page_no;
            me.args.counter_page_len = me.opts.counter_page_len;
            me.args.user = me.opts.user;
            if(me.opts.type=="Funds"){
                me.get_commission_list();
            }
            if(me.opts.type=="Transaction"){
               me.get_transaction_list();
            }
            if(me.opts.type=="Settlement"){
                me.get_order_list();
            }
            
          },
        () => {
            if(me.opts.type=="Funds"){
                me.construct_receivable_order_list();
            }
            if(me.opts.type=="Settlement"){
                me.construct_order_list();
            }
            if(me.opts.type=="Transaction"){
                me.construct_transaction_list()
            }
            },
        () => {
            if(me.opts.type=="Funds"){
                me.selected_fund_html();
            }
            if(me.opts.type=="Settlement"){
                me.selected_order_html();
            }
            if(me.opts.type=="Transaction"){
                me.selected_transaction_html();
            }
               
           
        },
         () => {
            if(me.opts.type=="Funds"){
                me.make_fund_dialog();
            }
            if(me.opts.type=="Settlement"){
                me.make_dialog();
            }
            if(me.opts.type=="Transaction"){
                me.transaction_pagination();
            }
              
            }
        ])
    },
    get_transaction_list: function(){
        var me = this;
        frappe.call({
            method: 'go1_commerce.accounts.doctype.wallet.wallet.get_transaction_history',
            args: me.args,
            async: false,
            callback: function(data) {
                if (data.message) {
                        me.transaction_list = data.message.orders;
                        me.total_records = data.message.count
                        me.currency= data.message.currency
                        me.counterpay_transaction_list=data.message.counter_pay
                        me.couterpay_total_records = data.message.counterpay_count
                  
                } else {
                    me.transaction_list = [];
                    me.counterpay_transaction_list=[];
                }
            }
        })
    },
    get_order_list: function() {
        var me = this;
        frappe.call({
            method: 'go1_commerce.accounts.doctype.wallet.wallet.get_all_orders',
            args: me.args,
            async: false,
            callback: function(data) {
                if (data.message) {
                    console.log(data.message)
                    if (data.message.orders.length > 0) {
                        me.order_list = data.message.orders;
                        me.total_records = data.message.count
                        me.currency= data.message.currency
                    }  else {
                        me.order_list = [];
                    }
                } else {
                    me.order_list = [];
                }
            }
        })
    },
    get_commission_list: function() {
        var me = this;
        frappe.call({
            method: 'go1_commerce.accounts.doctype.wallet.wallet.get_commission_list',
            args: me.args,
            async: false,
            callback: function(data) {
                if (data.message) {
                    if (data.message.orders.length > 0) {
                        me.fund_list = data.message.orders;
                        me.total_records = data.message.count
                        me.currency= data.message.currency
                    }  else {
                        me.fund_list = [];
                    }
                } else {
                    me.fund_list = [];
                }
            }
        })
    },
    make_fund_dialog: function() {
        var me = this;
        this.dialog = new frappe.ui.Dialog({
            title: __('To Be Received'),
            fields: [
                { fieldtype: 'HTML', fieldname: 'order_list', options: me.order_html, depends_on: '' },
            ]
        });
        me.set_fund_dialog_primary_action();
        me.dialog_style();
        me.dialog.show();
        me.pagination();
     },
     make_dialog: function() {
        var me = this;
        this.dialog = new frappe.ui.Dialog({
            title: __('To Be Paid'),
            fields: [
                { fieldtype: 'HTML', fieldname: 'order_list', options: me.order_html, depends_on: '' },
            ]
        });
        me.set_dialog_primary_action();
        me.dialog_style();
        me.dialog.show();
        me.pagination();
     },
       set_dialog_primary_action: function() {
        var me = this;
        me.dialog.set_primary_action(__('Confirm'), function() {
            frappe.call({
				method: "go1_commerce.accounts.api.make_withdraw_request",
				args: {
                    source_name: cur_frm.doc.name,
				},
				callback: function(r) {
					if(r.message) {
                        cur_dialog.hide();
                        cur_frm.reload_doc()
                        frappe.show_alert({message: __("Current Wallet amount is debited!"), indicator: 'orange'})
                    }
                }
            })
        });
    },
    set_fund_dialog_primary_action: function() {
        var me = this;
        me.dialog.set_primary_action(__('Confirm'), function() {
            frappe.call({
				method: "go1_commerce.accounts.doctype.wallet.wallet.add_fund_to_wallet",
				args: {
					source_name: cur_frm.doc.name,
				},
				callback: function(r) {
					if(r.message) {
                        cur_dialog.hide();
                        cur_frm.reload_doc()
                        frappe.show_alert({message: __("Commission Received!"), indicator: 'orange'})
                    }
                }
                })
        });
    },
    construct_order_list: function() {
        var me = this;
        let html = $(`
            <p>Payable</p>
            <div class="pickQuestions">
                <table class="table table-bordered" style="cursor:pointer; margin:0px;">
                    <thead>
                        <tr style="background:#e8ebec">
                            <th>ID#</th>
                            <th>Type#</th>
                            <th>For Service Provider</th>                 
                            <th>For ${this.cur_frm.doc.user_type}</th>
                        </tr>
                    </thead> 
                    <tbody></tbody>
                </table>
            </div>
            <div class="page-list"></div>
            <style>
                .page-list{
                    text-align: right;}
                .page-list .active{
                    background: #1d8fdb;}
                .page-list button{
                    margin-left: 5px;}
            </style>`);
        if (me.order_list && me.order_list.length > 0) {
            me.order_list.map(f => {
               
                var commission=parseFloat(f.total_value)-parseFloat(f.amount)
                let row_data = $(`<tr class="lists" data-id="${f.name}">
                    <td>${f.name}</td>
                    <td>${f.reference}</td>
                    
                    <td style="text-align:right">${me.currency} ${commission.toFixed(2)}</td>
                    <td style="text-align:right">${me.currency} ${f.amount}</td>
                           
                </tr>`);
                html.find('tbody').append(row_data);
            });
        } else {
            html.find('tbody').append(`<tr><td colspan="5">No records found!</td></tr>`);
        }
        me.order_html = html;
    },
    construct_receivable_order_list: function() {
        var me = this;
        let html = $(`
            <p>Receivable</p>
            <div class="pickQuestions">
                <table class="table table-bordered" style="cursor:pointer; margin:0px;">
                    <thead>
                        <tr style="background:#e8ebec">
                            <th>ID#</th>
                            <th>Type#</th>              
                            <th>Amount</th>
                        </tr>
                    </thead> 
                    <tbody> 
                    </tbody>
                </table>
            </div>
            <div class="page-list"></div>
            <style>
                .page-list{
                    text-align: right;}
                .page-list .active{
                    background: #1d8fdb;}
                .page-list button{
                    margin-left: 5px;}
            </style>`);
            if (me.fund_list && me.fund_list.length > 0) {
            me.fund_list.map(f => {
                let row_data = $(`<tr class="lists" data-id="${f.name}">
                    <td>${f.name}</td>
                    <td>${f.reference}</td>
                    <td style="text-align:right">${me.currency} ${f.amount}</td>
                           
                </tr>`);
                html.find('tbody').append(row_data);
            });
        } else {
            html.find('tbody').append(`<tr><td colspan="5">No records found!</td></tr>`);
        }
        me.order_html = html;
    },
    construct_transaction_list: function() {
        var me = this;
        var counter_pay_label;
        var app_pay_label;
        var counter_pay_icon;
        var app_pay_icon;
        if(cur_frm.wallet_setting.app_pay_label){
            app_pay_label = cur_frm.wallet_setting.app_pay_label
        }
        else{
            app_pay_label="App Pay"
       }
        if(cur_frm.wallet_setting.counter_pay_label){
            counter_pay_label = cur_frm.wallet_setting.counter_pay_label
        }
        else{
            counter_pay_label="Counter Pay"
        }
        if(cur_frm.wallet_setting.app_pay_icon){
            app_pay_icon = cur_frm.wallet_setting.app_pay_icon
        }
        else{
            app_pay_icon="fa fa-home"
       }
        if(cur_frm.wallet_setting.counter_pay_icon){
            counter_pay_icon = cur_frm.wallet_setting.counter_pay_icon
        }
        else{
            counter_pay_icon="fa fa-home"
        }
        let html=$(`
            <div class="row tabbreak" style="display:none">
                <div class="col-md-12" style="padding-right: 0px;padding-left: 0px;">
                    <div class="card"> 
                        <ul class="nav nav-tabs" role="tablist" style="border-bottom:none">
                            <li role="presentation" id="tablist1" class="tabcont active" style="height: 40px;">
                                <a class="tabcont" href="#tabs1" aria-controls="tabs1" onclick="show_tabcontent('#tabs1')" 
                                    role="tab" data-toggle="tab" aria-expanded="true" style="border-radius: 0px 0px 0 0;
                                    margin-right: 0px;">
                                    <i class="${app_pay_icon}"></i>&nbsp;
                                    <span>${app_pay_label}</span>
                                </a>
                            </li>
                            <li id="tablist2" role="presentation" class="tabcont" style="height: 40px;">
                                <a class="tabcont"  href="#tabs2" onclick="show_tabcontent('#tabs2')" aria-controls="tabs2"
                                    role="tab" data-toggle="tab" aria-expanded="true" style="border-radius: 0px 0px 0 0;
                                    margin-right: 0px;">
                                    <i class="${counter_pay_icon}"></i>&nbsp;
                                    <span>${counter_pay_label}</span>
                                </a>
                            </li>
                        </ul> 
                    </div> 
                </div>
            </div>
            <div class="row active" id="tabs1" style="padding-bottom: 5px;">
                <div class="col-md-12 AppPayButton" style="display:none;text-align: right;
                    background: #f5f7fa;padding:5px;"></div>
                <div class="col-md-12 AppCounter"></div>
                <div class="col-md-12">
                    <div class="pickQuestions">
                        <table class="table table-bordered" style="cursor:pointer; margin:0px;">
                            <thead>
                                <tr style="background:#e8ebec">
                                    <th>ID#</th>
                                    <th>Transaction Date</th>
                                    <th>Credit</th>
                                    <th>Debit</th>   
                                    <th>Transaction Note</th>
                                    <th></th>          
                                </tr>
                            </thead> 
                            <tbody> </tbody>
                        </table>
                    </div>
                    <div class="page-list"></div>
                </div>
            </div>
            <div class="row" id="tabs2" style="display:none;">
                <div class="col-md-12 CounterPayButton" style="text-align: right;
                    background: #f5f7fa;padding:5px;"></div>
                <div class="col-md-12 CounterCounter"></div>
                <div class="col-md-12">
                    <div class="counterPay">
                        <table class="table table-bordered" style="cursor:pointer; margin:0px;">
                            <thead>
                                <tr style="background:#e8ebec">
                                    <th>ID#</th>
                                    <th>Transaction Date</th>
                                    <th>Credit</th>
                                    <th>Debit</th>   
                                    <th>Transaction Note</th>
                                    <th></th>     
                                </tr>
                            </thead> 
                            <tbody> </tbody>
                        </table>
                    </div>
                    <div class="page-list-counter"></div>
                </div>
            </div>
        <style>.page-list{
                text-align: right;}
                .page-list-counter{
                    text-align: right;}
                .nav-tabs>li.active>a{
                    color:#1d8fdb;}
                .page-list .active{
                    background: #1d8fdb;}
                .page-list-counter .active{
                    background: #1d8fdb;}
                .page-list button{
                    margin-left: 5px;}
                .page-list-counter button{
                    margin-left: 5px;}
        </style>`);
        html.find('.AppCounter').html('');
        var data=[];
        setTimeout(function() {
          if(cur_frm.tab_settings == "Enable Both"){
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist1').show();
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist2').show();
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist1').addClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist2').removeClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs1').addClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs2').removeClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs1').css("display","block");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs2').css("display","none");
          }
          else if(cur_frm.tab_settings == "Only App Pay"){
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist1').show();
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist2').hide();
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist1').addClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist2').removeClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs1').addClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs2').removeClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs1').css("display","block");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs2').css("display","none");
          }
          else if(cur_frm.tab_settings == "Only Counter Pay"){
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist1').hide();
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist2').show();
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist1').removeClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist2').addClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs1').removeClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs2').addClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs1').css("display","none");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs2').css("display","block");
         
          }
         else if(cur_frm.tab_settings == "Disable Both"){
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist1').hide();
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist2').hide();
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist1').addClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist2').removeClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs1').addClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs2').removeClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs1').css("display","block");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs2').css("display","none");
          }
          else{
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist1').show();
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist2').show();
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist1').addClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('.tabbreak').find('li#tablist2').removeClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs1').addClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs2').removeClass("active");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs1').css("display","block");
            $(cur_frm.fields_dict['transaction_history'].wrapper).find('div#tabs2').css("display","none");
          }
      },200)

        if(cur_frm.doc.user=="Service Provider"){
            data.push({'name':"total_amount",
                        'title':"Total Amount",
                        "css":"color:#ffffff;background:#d83c6b;",
                        'icon':'fa fa-money',
                        'icon_style':"color:#ffffff;padding: 5px;",
                        'count':cur_frm.doc.total_wallet_amount ? cur_frm.doc.total_wallet_amount.toFixed(2):0})
            data.push({'name':"total_received_amount",
                        'title':"Total Received Amount",
                        "css":"color:#ffffff;background:#27ae60;",
                        'icon':'fa fa-money',
                        'icon_style':"color:#ffffff;padding: 5px;",
                        'count':cur_frm.doc.current_wallet_amount ? cur_frm.doc.current_wallet_amount.toFixed(2):0})
            data.push({'name':"amount_to_be_paid",
                        'title':"Amount To Be Paid",
                        "css":"color:#ffffff;background: #22b3d4;",
                        'icon':'fa fa-money',
                        'icon_style':"color:#ffffff;padding: 5px;",
                        'count':cur_frm.doc.locked_in_amount ? cur_frm.doc.locked_in_amount.toFixed(2):0})
        }
        else{
            data.push({'name':"total_wallet_amount",
                        'title':"Total Wallet Amount",
                        "css":"color:#ffffff;background:#d83c6b;",
                        'icon':'fa fa-money',
                        'icon_style':"color:#ffffff;padding: 5px;",
                        'count':cur_frm.doc.total_wallet_amount ? cur_frm.doc.total_wallet_amount.toFixed(2):0})
            data.push({'name':"current_wallet_amount",'title':"Current Wallet Amount","css":"color:#ffffff;background:#27ae60;",'icon':'fa fa-money','icon_style':"color:#ffffff;padding: 5px;",'count':cur_frm.doc.current_wallet_amount.toFixed(2)})
            if(cur_frm.disable_lockedin == 0){
                data.push({'name':"locked_in_amount",
                            'title':"Locked In Amount",
                            "css":"color:#ffffff;background: #22b3d4;",
                            'icon':'fa fa-money',
                            'icon_style':"color:#ffffff;padding: 5px;",
                            'count':cur_frm.doc.locked_in_amount ? cur_frm.doc.locked_in_amount.toFixed(2):0})
            }
        }
        if(data.length > 0){
            var column = 4; var counter_column = 6; var graph_column = 6;var style =""; 
            var innerstyle = "padding: 20px;"; var innerbox="";var chart_option = "hidden";
            if(data.length == 3){
                column = 4; chart_option = "hidden";
                style="";innerstyle = "padding: 20px;";innerbox = ""
                counter_column = 12;graph_column = 0;
            }
            if(data.length == 2){
                column = 6; chart_option = "hidden";
                style="width:27.333333%;padding: 0px;margin: 10px 20px 10px 180px;";
                innerstyle = "padding: 20px 30px 20px 30px;";
                innerbox = "padding: 0px;";counter_column = 8; graph_column = 4;
            }
            if(data.length == 1){
                column = 12; chart_option = "hidden";style="";innerstyle = "padding: 20px;";
                innerbox = ""; counter_column = 6;graph_column = 6;
            }
            if(data.length == 4){
                column = 3;chart_option = "hidden";style="";innerstyle = "padding: 20px;";
                innerbox = ""; counter_column = 6;graph_column = 6;
            }
            html.find('.AppCounter').html(frappe.render_template("wallet_counter",{ 
                                                                                    content:  data, 
                                                                                    column:column, 
                                                                                    style:style,
                                                                                    innerstyle:innerstyle, 
                                                                                    innerbox:innerbox, 
                                                                                    counter_column:counter_column, 
                                                                                    graph_column:graph_column, 
                                                                                    chart_option:chart_option
                                                                                }));
        }
        html.find('.CounterCounter').html('');
        var data = [];
        if(cur_frm.doc.user == "Service Provider"){
            data.push({'name':"total_amount",
                        'title':"Total Amount",
                        "css":"color:#ffffff;background:#d83c6b;",
                        'icon':'fa fa-money',
                        'icon_style':"color:#ffffff;padding: 5px;",
                        'count':cur_frm.counter_pay_counter && cur_frm.counter_pay_counter.total_amount ? 
                                                    cur_frm.counter_pay_counter.total_amount.toFixed(2):0})
            data.push({'name':"claimed",
                        'title':"Claimed",
                        "css":"color:#ffffff;background:#27ae60;",
                        'icon':'fa fa-money',
                        'icon_style':"color:#ffffff;padding: 5px;",
                        'count':cur_frm.counter_pay_counter && cur_frm.counter_pay_counter.climed_amount ? 
                                                     cur_frm.counter_pay_counter.climed_amount.toFixed(2):0})
            data.push({'name':"to_be_received",
                        'title':"To Be Received",
                        "css":"color:#ffffff;background: #22b3d4;",
                        'icon':'fa fa-money',
                        'icon_style':"color:#ffffff;padding: 5px;",
                        'count':cur_frm.counter_pay_counter && cur_frm.counter_pay_counter.to_be_received ? 
                                                    cur_frm.counter_pay_counter.to_be_received.toFixed(2):0})
        }
        else{
            data.push({'name':"total_amount",
                        'title':"Total Amount",
                        "css":"color:#ffffff;background:#d83c6b;",
                        'icon':'fa fa-money',
                        'icon_style':"color:#ffffff;padding: 5px;",
                        'count':cur_frm.counter_pay_counter && cur_frm.counter_pay_counter.total_amount ? 
                                                    cur_frm.counter_pay_counter.total_amount.toFixed(2):0})
            data.push({'name':"paid_amount",
                       'title':"Paid Amount",
                       "css":"color:#ffffff;background:#27ae60;",
                       'icon':'fa fa-money',
                       'icon_style':"color:#ffffff;padding: 5px;",
                       'count':cur_frm.counter_pay_counter && cur_frm.counter_pay_counter.climed_amount? 
                                                cur_frm.counter_pay_counter.climed_amount.toFixed(2):0})
            if(cur_frm.disable_lockedin == 0){
                data.push({'name':"amount_to_be_paid",
                            'title':"Amount To Be Paid",
                            "css":"color:#ffffff;background: #22b3d4;",
                            'icon':'fa fa-money',
                            'icon_style':"color:#ffffff;padding: 5px;",
                            'count':cur_frm.counter_pay_counter && cur_frm.counter_pay_counter.to_be_received ? 
                                                        cur_frm.counter_pay_counter.to_be_received.toFixed(2):0})
            }
        }
        if(data.length>0){
            var column = 4; var counter_column = 6; var graph_column = 6;
            var style =""; var innerstyle = "padding: 20px;"; 
            var innerbox="";var chart_option = "hidden";
            if(data.length == 3){
                column = 4;chart_option = "hidden";style="";innerstyle = "padding: 20px;";
                innerbox = ""; counter_column = 12;graph_column = 0;
            }
            if(data.length == 2){
                column = 6;chart_option = "hidden";
                style="width:27.333333%;padding: 0px;margin: 10px 20px 10px 180px;";
                innerstyle = "padding: 20px 30px 20px 30px;";
                innerbox = "padding: 0px;";counter_column = 8;graph_column = 4;
            }
            if(data.length == 1){
                column = 12;chart_option = "hidden";
                style="";innerstyle = "padding: 20px;";innerbox = ""; counter_column = 6;
                graph_column = 6;
            }
            if(data.length == 4){
                column = 3;chart_option = "hidden";style="";innerstyle = "padding: 20px;";
                innerbox = ""; counter_column = 6;graph_column = 6;
            }
            html.find('.CounterCounter').html(frappe.render_template("wallet_counter", { content:  data, column:column, style:style, innerstyle:innerstyle, innerbox:innerbox, counter_column:counter_column, graph_column:graph_column, chart_option:chart_option}));
        }
        var custom_btn=''
        if(parseFloat(cur_frm.doc.current_wallet_amount)>0 && cur_frm.doc.user!="Service Provider" && cur_frm.enable_settlement==1){
             custom_btn+='<button class="btn btn-default btn-xs" style="margin-left: 10px; background-color: rgb(29, 143, 219); color: rgb(255, 255, 255); padding: 3px;" onclick="make_settlement()">Make Settlement</button>';
        }
        custom_btn+='<button class="btn btn-default btn-xs" style="margin-left: 10px; background-color: rgb(29, 143, 219); color: rgb(255, 255, 255); padding: 3px;" onclick="view_vendor_payment()">View Payment Entry</button>';
        html.find('.AppPayButton').html(custom_btn);
        if(me.transaction_list && me.transaction_list.length > 0) {
            let row=''
            me.transaction_list.map(f => {
                let reference ="";
                let indicator ="";
                            let trans_date = frappe.datetime.get_datetime_as_string(f.transaction_date)
                            if(f.reference=="Pay" && f.status=="Credited"){
                                reference="Credited"
                                indicator="green"
                            }
                            else if(f.reference=="Pay" && f.status=="Debited"){
                                reference="Debited"
                                indicator="red"
                            }
                            else if(f.reference=="Pay" && f.status=="Locked"){
                                reference="Locked"
                                indicator="darkgrey"
                            }
                            else if(f.reference=="Pay" && f.status=="Pending"){
                                reference="Pending"
                                indicator="orange"
                            }
                            else{
                                reference="Credited"
                                indicator="green"
                            }
                            row += '<tr class="lists" data-id="'+f.name+'"><td><a href="/app/wallet-transaction/'+f.name+'" data-id="'+f.name+'">'+f.name+'</a></td><td>'+trans_date+'</td>'                    
                    if(reference != "Debited"){
                        row+='<td style="text-align:right">'+me.currency+' '+f.amount.toFixed(2)+'</td><td style="text-align:center">---</td>'
                    }
                    else if(reference == "Debited"){
                        row+='<td style="text-align:center">---</td><td style="text-align:right">'+me.currency+' '+f.amount.toFixed(2)+'</td>'
                    }
                    var transnotes= "";
                    if(f.notes!=null){
                        transnotes = f.notes;
                    }
                    row += '<td style="max-width: 400px;">'+transnotes+'</td><td><span class="indicator '+indicator+'"></span>'+reference+'</td></tr>'     
            });
            html.find('.pickQuestions tbody').append(row) 
        } else {
            html.find('.pickQuestions tbody').append(`
                                                    <tr>
                                                        <td colspan="6">No records found!</td>
                                                    </tr>`);
        }
        console.log(me.counterpay_transaction_list)
        if (me.counterpay_transaction_list && me.counterpay_transaction_list.length > 0) {
            if(cur_frm.doc.user!="Service Provider"){
                var custom_counter_btn=`<button class="btn btn-default btn-xs" style="margin-left: 10px; 
                                                background-color: rgb(29, 143, 219); color: rgb(255, 255, 255); 
                                                padding: 3px;" onclick="mark_as_received()">Mark as Received
                                        </button>`
                html.find('.CounterPayButton').html(custom_counter_btn);
            }
           let row = ''
            me.counterpay_transaction_list.map(f => {
                let trans_date=frappe.datetime.get_datetime_as_string(f.transaction_date)
                let reference =""
                let indicator =""
                if(f.reference=="Receive" && f.status=="Debited"){
                    reference="Debited"
                    indicator="red"
                }
                else if(f.reference=="Receive" && f.status=="Credited"){
                    reference="Approved"
                    indicator="green"
                }
                else if(f.reference=="Receive" && f.status=="Pending"){
                    reference="Pending"
                    indicator="orange"
                }
                else{
                    reference="Approved"
                    indicator="green"
                }
                row+='<tr class="lists" data-id="'+f.name+'"><td><a href="#Form/Wallet Transaction/'+f.name+'" data-id="'+f.name+'">'+f.name+'</a></td><td>'+trans_date+'</td>'
                if(cur_frm.doc.user != "Service Provider"){
                    row+='<td style="text-align:center">---</td><td style="text-align:right">'+me.currency+' '+f.amount.toFixed(2)+'</td>'
                }
                else{
                    row += '<td style="text-align:right">'+me.currency+' '+f.amount.toFixed(2)+'</td><td style="text-align:center">---</td>'
                }
                row += '<td style="max-width: 400px;">'+f.notes+'</td><td><span class="indicator '+indicator+'"></span>'+reference+'</td></tr>'      
            });
            html.find('.counterPay tbody').append(row) 
        } else {
            html.find('.counterPay tbody').append(`<tr><td colspan="6">No records found!</td></tr>`);
        }
        me.transaction_html = html;
        $(cur_frm.fields_dict['transaction_history'].wrapper).html(me.transaction_html);
    },
    selected_order_html: function() {
        let me = this;
        me.selected_order_html = $(`<h4>Orders</h4>
        <div class="selectedQuestion">
            <table class="table table-bordered" style="cursor:pointer; margin:0px;background:#f1f1f1;">
                <thead>
                    <tr>            
                        <th>Order</th>
                    </tr>
                </thead> 
                <tbody>
                    <tr id="no-record">
                        <td colspan="2">No Records Found!</td>
                    </tr>
                </tbody>
            </table>
        </div>`);
    },
    selected_fund_html: function() {
        let me = this;
        me.selected_order_html = $(`<h4>Orders</h4>
        <div class="selectedQuestion">
            <table class="table table-bordered" style="cursor:pointer; margin:0px;background:#f1f1f1;">
                <thead>
                    <tr>            
                        <th>Order</th>
                    </tr>
                </thead> 
                <tbody>
                    <tr id="no-record">
                        <td colspan="2">No Records Found!</td>
                    </tr>
                </tbody>
            </table>
        </div>`);
    },
    selected_transaction_html: function() {
        let me = this;
        me.selected_order_html = $(`<h4>Wallet Transaction</h4>
        <div class="selectedQuestion"><table class="table table-bordered" style="cursor:pointer; margin:0px;background:#f1f1f1;">
                <thead>
                    <tr>            
                        <th>ID#</th>
                    </tr>
                </thead> 
                <tbody><tr id="no-record"><td colspan="6">No Records Found!</td></tr></tbody>
        </table></div>`);
      
    },
    dialog_style: function() {
        let me = this;
        let height = String($( window ).height()-40)+"px"
        let scrollheight = ($( window ).height()-40)-200
        $(me.dialog.$wrapper).find('.modal-dialog').css("min-width", "70%");
        $(me.dialog.$wrapper).find('.modal-content').css("height", height);
        $('.modal[data-types="order_list"').each(function() {
            $(this).remove();
        })
        $(me.dialog.$wrapper).attr('data-types', 'order_list')
        $(me.dialog.$wrapper).find('.form-section').css('padding', '0 7px');
        $(me.dialog.$wrapper).attr('data-types', 'order_list')
        $(me.dialog.$wrapper).find('div[data-fieldname="tab_html"]').parent().parent().parent().parent().css('border-bottom', 'none')
        $(me.dialog.$wrapper).find('div[data-fieldname="tab_html"]').parent().parent().parent().parent().css('padding', '0px')
        $(me.dialog.$wrapper).find('div[data-fieldname="question_type"]').parent().parent().removeClass('col-sm-6')
        $(me.dialog.$wrapper).find('div[data-fieldname="question_type"]').parent().parent().addClass('col-sm-2')
        $(me.dialog.$wrapper).find('div[data-fieldname="question_type"]').parent().parent().
            css({"height":String($( window ).height()-99.5)+"px","background-color":"#eee","border-right":"1px solid #ddd"});
        $(me.dialog.$wrapper).find('div[data-fieldname="order_list"]').parent().parent().removeClass('col-sm-6')
        $(me.dialog.$wrapper).find('div[data-fieldname="order_list"]').parent().parent().addClass('col-sm-12')
        $(me.dialog.$wrapper).find('.modal-dialog').css('margin', '15px auto')
        $(me.dialog.$wrapper).find('div[data-fieldname="order_list"] .pickQuestions').slimScroll({
            height: 370
        })
        $(me.dialog.$wrapper).find('div[data-fieldname="selected_question"] .selectedQuestion').slimScroll({
            height: 405
        })
        $(me.dialog.$wrapper).find('div[data-fieldname="order_list"] .pickQuestions').slimScroll({
            height: scrollheight
        })
        $(me.dialog.$wrapper).find('div[data-fieldname="selected_question"] .selectedQuestion').slimScroll({
            height: scrollheight
        })
        $(me.dialog.$wrapper).find('button[data-fieldname="apply_filters"]').removeClass('btn-xs');
        $(me.dialog.$wrapper).find('button[data-fieldname="apply_filters"]').addClass('btn-sm btn-primary');
    },
    pagination: function() {
        var me = this;
        if (me.total_records > 0) {
            let count = me.total_records / me.opts.page_len;
            if (count % 1 === 0) {
                count = count
            } 
            else {
                count = parseInt(count) + 1;
            }
            if (count>1) {
                let page_btn_html = '<button class="btn btn-default prev">Prev</button>';
                for (var i = 0; i < count; i++) {
                    let active_class = '';
                    if ((i + 1) == me.page_no)
                        active_class = 'active'
                    page_btn_html += '<button class="btn btn-info paginate ' + active_class + '" data-id="' + (i + 1) + '">' + (i + 1) + '</button>'
                }
                page_btn_html += '<button class="btn btn-default next">Next</button>';
                $(me.dialog.$wrapper).find('div[data-fieldname="order_list"] .page-list').html(page_btn_html)
                $(me.dialog.$wrapper).find('div[data-fieldname="order_list"] .page-list .paginate').click(function() {
                    if (me.page_no != parseInt($(this).text())) {
                        me.page_no = parseInt($(this).text());
                        me.paginate_orders()
                    }
                })
                $(me.dialog.$wrapper).find('div[data-fieldname="order_list"] .page-list .prev').click(function() {
                    let pg_no = me.page_no - 1;
                    if (me.page_no > 0) {
                        me.page_no = me.page_no - 1;
                        me.paginate_orders()
                    }
                })
                $(me.dialog.$wrapper).find('div[data-fieldname="order_list"] .page-list .next').click(function() {
                    let pg_no = me.page_no + 1;
                    if (pg_no <= count) {
                        me.page_no = me.page_no + 1;
                        me.paginate_orders()
                    }
                })
                if (count > 7) {
                    $(me.dialog.$wrapper).find('div[data-fieldname="order_list"] .page-list .paginate').hide();
                    let arr = [me.page_no, me.page_no + 1, me.page_no + 2, me.page_no + 3, 
                                me.page_no + 4, me.page_no + 5, me.page_no + 6];
                    let pg = 1;
                    for (var i = 0; i < 7; i++) {
                        if (arr[i] > count) {
                            arr[i] = me.page_no - pg;
                            pg = pg + 1;
                        }
                    }
                    $(arr).each(function(k, v) {
                        $(me.dialog.$wrapper).find('div[data-fieldname="order_list"] .page-list .paginate[data-id="' + v + '"]').show();
                    })
                }
            }
        }
    },
    transaction_pagination: function() {
        var me = this;
        if (me.total_records > 0) {
            let count = me.total_records / me.opts.page_len;
            if (count % 1 === 0) {
                count = count
            } else {
                count = parseInt(count) + 1;
            }
            if (count>1) {
                let page_btn_html = '<button class="btn btn-default prev">Prev</button>';
                for (var i = 0; i < count; i++) {
                    let active_class = '';
                    if ((i + 1) == me.page_no)
                        active_class = 'active'
                    page_btn_html += '<button class="btn btn-info paginate ' + active_class + '" data-id="' + (i + 1) + '">' + (i + 1) + '</button>'
                }
                page_btn_html += '<button class="btn btn-default next">Next</button>';
                $(cur_frm.fields_dict['transaction_history'].wrapper).find('.page-list').html(page_btn_html)
                $(cur_frm.fields_dict['transaction_history'].wrapper).find('.page-list .paginate').click(function() {
                    if (me.page_no != parseInt($(this).text())) {
                        me.page_no = parseInt($(this).text());
                        me.paginate_transaction()
                    }
                })
                $(cur_frm.fields_dict['transaction_history'].wrapper).find('.page-list .prev').click(function() {
                    let pg_no = me.page_no - 1;
                    if (me.page_no > 0) {
                        me.page_no = me.page_no - 1;
                        me.paginate_transaction()
                    }
                })
                $(cur_frm.fields_dict['transaction_history'].wrapper).find('.page-list .next').click(function() {
                    let pg_no = me.page_no + 1;
                    if (pg_no <= count) {
                        me.page_no = me.page_no + 1;
                        me.paginate_transaction()
                    }
                })
                if (count > 7) {
                    $(cur_frm.fields_dict['transaction_history'].wrapper).find('.page-list .paginate').hide();
                    let arr = [me.page_no, me.page_no + 1, me.page_no + 2, me.page_no + 3, me.page_no + 4, 
                                me.page_no + 5, me.page_no + 6];
                    let pg = 1;
                    for (var i = 0; i < 7; i++) {
                        if (arr[i] > count) {
                            arr[i] = me.page_no - pg;
                            pg = pg + 1;
                        }
                    }
                    $(arr).each(function(k, v) {
                        $(cur_frm.fields_dict['transaction_history'].wrapper).
                            find('.page-list .paginate[data-id="' + v + '"]').show();
                    })
                }
            }
        }
        if (me.couterpay_total_records > 0) {
            let count = me.couterpay_total_records / me.opts.counter_page_len;
            if (count % 1 === 0) {
                count = count
            } else {
                count = parseInt(count) + 1;
            } 
            if (count) {
                let page_btn_html = '<button class="btn btn-default prev">Prev</button>';
                for (var i = 0; i < count; i++) {
                    let active_class = '';
                    if ((i + 1) == me.counter_page_no)
                        active_class = 'active'
                    page_btn_html += '<button class="btn btn-info paginate ' + active_class + '" data-id="' + (i + 1) + '">' + (i + 1) + '</button>'
                }
                page_btn_html += '<button class="btn btn-default next">Next</button>';
                $(cur_frm.fields_dict['transaction_history'].wrapper).find('.page-list-counter').html(page_btn_html)
                $(cur_frm.fields_dict['transaction_history'].wrapper).find('.page-list-counter .paginate').
                    click(function() {
                        if(me.counter_page_no != parseInt($(this).text())) {
                            me.counter_page_no = parseInt($(this).text());
                            me.paginate_transaction()
                        }
                })
                $(cur_frm.fields_dict['transaction_history'].wrapper).find('.page-list-counter .prev').
                    click(function() {
                        if (me.counter_page_no > 0) {
                            me.counter_page_no = me.counter_page_no - 1;
                            me.paginate_transaction()
                        }
                })
                $(cur_frm.fields_dict['transaction_history'].wrapper).find('.page-list-counter .next').
                    click(function() {
                        let pg_no = me.counter_page_no + 1;
                        if (pg_no <= count) {
                            me.counter_page_no = me.counter_page_no + 1;
                            me.paginate_transaction()
                        }
                })
                if (count > 7) {
                    $(cur_frm.fields_dict['transaction_history'].wrapper).
                        find('.page-list-counter .paginate').hide();
                    let arr = [me.counter_page_no, me.counter_page_no + 1, me.counter_page_no + 2, 
                                me.counter_page_no + 3, me.counter_page_no + 4, me.counter_page_no + 5,
                                me.counter_page_no + 6];
                    let pg = 1;
                    for (var i = 0; i < 7; i++) {
                        if (arr[i] > count) {
                            arr[i] = me.counter_page_no - pg;
                            pg = pg + 1;
                        }
                    }
                    $(arr).each(function(k, v) {
                        $(cur_frm.fields_dict['transaction_history'].wrapper).
                            find('.page-list-counter .paginate[data-id="' + v + '"]').show();
                    })
                }
            }
        }
    },
    paginate_orders: function() {
        let me = this;
        let values = me.dialog.get_values();
        values.page_len = me.opts.page_len;
        values.page_no = me.page_no;
        me.args = values;
        me.get_order();
    },
    paginate_transaction: function() {
        let me = this;
        let values = me.transaction_list;
        values.page_len = me.opts.page_len;
        values.page_no = me.page_no;
        values.user=cur_frm.doc.user
        values.counter_page_no=me.counter_page_no
        values.counter_page_len=me.opts.counter_page_len
        me.args = values;
        me.get_transaction_history();
    },
    get_transaction_history: function() {
        let me = this;
        frappe.run_serially([
            () => {     
                me.get_transaction_list()
            },
            () => {
                let html = $(cur_frm.fields_dict['transaction_history'].wrapper).find('div.pickQuestions').find('tbody');
                html.empty();
                let counter_html = $(cur_frm.fields_dict['transaction_history'].wrapper).find('div.counterPay').find('tbody');
                counter_html.empty();
                if (me.transaction_list.length > 0) {
                    scroll = true;
                    if (me.transaction_list && me.transaction_list.length > 0) {
                        let row=''
                        me.transaction_list.map(f => {
                            let trans_date=frappe.datetime.get_datetime_as_string(f.transaction_date)
                            let reference =""
                            let indicator =""
                            if(f.reference=="Pay" && f.status=="Credited"){
                                reference="Credited"
                                indicator="green"
                            }
                            else if(f.reference=="Pay" && f.status=="Debited"){
                                reference="Debited"
                                indicator="red"
                            }
                            else if(f.reference=="Pay" && f.status=="Locked"){
                                reference="Locked"
                                indicator="darkgrey"
                            }
                            else if(f.reference=="Pay" && f.status=="Pending"){
                                reference="Pending"
                                indicator="orange"
                            }
                            else{
                                reference="Credited"
                                indicator="green"
                            }
                            row+='<tr class="lists" data-id="'+f.name+'"><td><a href="#Form/Wallet Transaction/'+f.name+'" data-id="'+f.name+'">'+f.name+'</a></td><td>'+trans_date+'</td>'     
                            if(reference!="Debited"){
                                row+='<td style="text-align:right">'+me.currency+' '+f.amount.toFixed(2)+'</td><td style="text-align:center">---</td>'
                            }
                            else{
                                row+='<td style="text-align:center">---</td><td style="text-align:right">'+me.currency+' '+f.amount.toFixed(2)+'</td>'
                            }
                            row+='<td style="max-width: 400px;">'+f.notes+'</td><td><span class="indicator '+indicator+'"></span>'+reference+'</td></tr>'              
                        });
                        html.append(row)      
                    }
                } 
                else{
                    html.append(`<tr><td colspan="6">No records found!</td></tr>`);
                }
                if (me.counterpay_transaction_list.length > 0) {
                    scroll = true;
                    if (me.counterpay_transaction_list && me.counterpay_transaction_list.length > 0) {
                        let row=''
                        me.counterpay_transaction_list.map(f => {
                            let trans_date=frappe.datetime.get_datetime_as_string(f.transaction_date)
                            if(f.reference=="Receive" && f.status=="Debited"){
                                reference="Debited"
                                indicator="red"
                            }
                            else if(f.reference=="Receive" && f.status=="Credited"){
                                reference="Approved"
                                indicator="green"
                            }
                            else if(f.reference=="Receive" && f.status=="Pending"){
                                reference="Pending"
                                indicator="orange"
                            }
                            else{
                                reference="Approved"
                                indicator="green"
                            }
                            row+='<tr class="lists" data-id="'+f.name+'"><td><a href="#Form/Wallet Transaction/'+f.name+'" data-id="'+f.name+'">'+f.name+'</a></td><td>'+trans_date+'</td>'
                            if(cur_frm.doc.user!="Service Provider"){
                                    row+='<td style="text-align:center">---</td><td style="text-align:right">'+me.currency+' '+f.amount.toFixed(2)+'</td>'
                            }
                            else{
                                row+='<td style="text-align:right">'+me.currency+' '+f.amount.toFixed(2)+'</td><td style="text-align:center">---</td>'
                                }
                            row+='<td style="max-width: 400px;">'+f.notes+'</td><td><span class="indicator '+indicator+'"></span>'+reference+'</td></tr>'    
                                
                            });
                        counter_html.append(row)     
                    }
                } 
                else {
                    counter_html.append(`<tr><td colspan="6">No records found!</td></tr>`);
                }
                me.transaction_pagination();
            },
        ])
    },
    get_order: function() {
        let me = this;
        frappe.run_serially([
            () => {
                me.get_order_list()
            },
            () => {
                let html = $(me.dialog.$wrapper).find('div[data-fieldname="order_list"]').find('tbody');
                html.empty();
                if (me.order_list.length > 0) {
                    scroll = true;
                    if (me.order_list && me.order_list.length > 0) {
                        me.order_list.map(f => {
                            var commission=parseFloat(f.total_value)-parseFloat(f.amount)
                            let row_data = $(`
                                <tr class="lists" data-id="${f.name}">
                                    <td>${f.name}</td>
                                    <td>${f.reference}</td>
                                    <td style="text-align:right">${me.currency} ${commission.toFixed(2)}</td>
                                    <td style="text-align:right">${me.currency} ${f.amount}</td>            
                                </tr>`);
                            html.append(row_data);
                        });
                    }
                } else {
                    html.append(`<tr><td colspan="5">No records found!</td></tr>`);
                }
                me.pagination();
            },
            () => {
                me.click_events();
            }
        ])
    }
})
