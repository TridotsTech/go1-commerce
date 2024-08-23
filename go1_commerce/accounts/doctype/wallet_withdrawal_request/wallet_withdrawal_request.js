// Copyright (c) 2018, info@valiantsystems.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Wallet Withdrawal Request', {
	refresh: function(frm) {
		frm.events.add_approve_reject_btn(frm)
		frm.events.update_css_properties(frm)
		frm.events.filter_link_field_data(frm)
	},
    filter_link_field_data(frm){
        frm.set_query("party_type", function() {
            return{
                "filters": {
                    "name": ["in", ["Business","Drivers","Customers"]]
                }
            }
        });
    },
    update_css_properties(frm){
        if (frm.doc.status == "Open") {
            frm.set_df_property("status", "read_only", 0);
        }
        else{
            frm.set_df_property("status", "read_only", 1);
        }
    },
    add_approve_reject_btn(frm){
        if (frm.doc.status == "Pending" && frm.doc.docstatus == 1) {
            frm.add_custom_button(__("Approve"), function() {
                var approve = 1;
                frappe.confirm('Are you sure want to confirm this withdrawal request?',
                    function(){
                        if(approve == 1){
                            approve = 0
                            frappe.call({
                                method: 'go1_commerce.accounts.doctype.wallet_withdrawal_request.wallet_withdrawal_request.update_requested_status',
                                args: { "status": "Approved", "id": frm.doc.name, 'doctype': cur_frm.doctype },
                                async: false,
                                callback: function(data) {
                                    refresh_field("status");
                                    cur_frm.reload_doc();
                                }
                            })
                            frappe.show_alert('Request Approved!')
                        }
                    })
                
            }).css({'background-color':"#1d8fdb",'color':"#fff","padding": "5px"})
            frm.add_custom_button(__("Reject"), function() {
                var approve = 1;
                frappe.confirm('Are you sure want to cancel this withdrawal request?',
                    function(){
                        if(approve == 1){
                            approve = 0
                            frappe.call({
                                method: 'go1_commerce.accounts.doctype.wallet_withdrawal_request.wallet_withdrawal_request.update_requested_status',
                                args: { "status": "Rejected", "id": frm.doc.name, 'doctype': cur_frm.doctype },
                                async: false,
                                callback: function(data) {
                                    refresh_field("status");
                                    cur_frm.reload_doc();
                                }
                            })
                            frappe.show_alert('Request Approved!')
                        }
                    })
            }).css({'background-color':"#1d8fdb",'color':"#fff","padding": "5px"})
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
    }
});
