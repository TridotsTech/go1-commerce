// Copyright (c) 2019, sivaranjani and contributors
// For license information, please see license.txt

frappe.ui.form.on('Wallet Transaction', {
    setup: function(frm){
        frm.events.filter_link_field_data(frm)
    },
	refresh: function(frm) {
        frm.events.get_wallet_settings(frm);
        frm.events.append_custom_buttons(frm);
    },
    filter_link_field_data(frm){
        frm.set_query("party_type", function() {
			return{
				"filters": {
					"name": ["in", ["Business","Drivers"]]
				}
			}
        });
        frm.set_query("order_type", function() {
			return{
				"filters": {
					"name": ["in", ["Order","Vendor Orders", "Subscription", "Referral Entry"]]
				}
			}
        });
    },
    get_wallet_settings(frm){
        frappe.call({
            method: 'go1_commerce.accounts.doctype.wallet.wallet.get_wallet_settings',
            args: {},
            async: false,
            callback: function(data) {
                if (data.message) {
                    cur_frm.wallet_setting = data.message
                    cur_frm.enable_approval =  data.message.enable_approval
                }
            }
        })
    },
    append_custom_buttons(frm){
        if(cur_frm.enable_approval == 1 && frm.doc.status == "Pending" && frm.doc.docstatus == 1){
            frm.add_custom_button(__("Approved"), function() {
                frappe.call({
                        method: 'go1_commerce.accounts.doctype.wallet_transaction.wallet_transaction.update_docstatus',
                        args: { "status": "Credited", "docid": frm.doc.name, 'doctype': cur_frm.doctype},
                        async: false,
                        callback: function(data) {
                            refresh_field("status");
                            cur_frm.reload_doc();
                        }
                    })
                
                }).css({'background-color':"#1d8fdb",'color':"#fff","padding": "3px 6px 3px 6px"})
                
            frm.add_custom_button(__("Rejected"), function() {
                frm.set_value("status", "Cancelled");
                frappe.call({
                            method: 'go1_commerce.accounts.doctype.wallet_transaction.wallet_transaction.update_docstatus',
                            args: { "status": "Cancelled", "docid": frm.doc.name, 'doctype': cur_frm.doctype},
                            async: false,
                            callback: function(data) {
                                refresh_field("status");
                                cur_frm.reload_doc();
                            }
                        })
                }).css({'background-color':"#ef4a32",'color':"#fff","padding": "3px 6px 3px 6px"})
        }
        if(frm.doc.status == "Pending" && frm.doc.transaction_type == "Receive" && frm.doc.type != "Service Provider"){
            frm.add_custom_button(__("Mark as Claimed"), function() {
                frappe.call({
                    method: 'go1_commerce.accounts.doctype.wallet_transaction.wallet_transaction.update_transaction_status',
                    args: { "status": "Approved", "id": frm.doc.name, 'doctype': cur_frm.doctype },
                    async: false,
                    callback: function(data) {
                        refresh_field("status");
                        cur_frm.reload_doc();
                    }
                })
            }).css({'background-color':"#1d8fdb",'color':"#fff","padding": "3px 6px 3px 6px"})	
        }
    },
    type: function(frm){
        if(frm.doc.type!="Service Provider"){
            if(frm.doc.type=="Driver")
                frm.set_value('party_type',"Drivers")
            else
                frm.set_value('party_type',frm.doc.type)

        }
        else{
            frm.set_value('party_type',"")
            frm.set_value('party',"")
            frm.set_value('party_name',"")
        }
    },
    party: function(frm){
        if(frm.doc.party_type == "Drivers"){
            frappe.model.get_value(frm.doc.party_type, { 'name': frm.doc.party }, 'driver_name',
                function(d) {
                    if (d.driver_name) {
                        frm.set_value('party_name', d.driver_name)
                    }
                });
        }
        else if(frm.doc.party_type == "Business"){
            frappe.model.get_value(frm.doc.party_type, { 'name': frm.doc.party }, 'restaurant_name',
                function(d) {
                    if(d.restaurant_name) {
                        frm.set_value('party_name', d.restaurant_name)
                    }
                });
        }
    }
});
