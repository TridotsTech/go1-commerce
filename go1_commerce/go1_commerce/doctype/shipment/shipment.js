// Copyright (c) 2019, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shipment', {
    refresh: function(frm) {
        frm.set_query('document_type', function(doc) {
            return {
                'filters': {
                    'name': ['in', ['Order', 'Vendor Orders']]
                }
            }
        })
        if (frm.doc.docstatus == 1 && (frm.doc.status == 'Shipped' || frm.doc.status == 'Items Packed')) {
            frm.set_df_property('status', 'read_only', 1)
        }
        if (frm.doc.docstatus == 1 && frm.doc.status == 'Delivered' && frm.doc.payment_status == 'Pending') {
            frm.add_custom_button(__("Mark as Paid"), function() {
                frappe.call({
                    method: 'go1_commerce.go1_commerce.doctype.shipment.shipment.make_payment',
                    args: { "name": frm.doc.name },
                    async: false,
                    callback: function(data) {
                        cur_frm.reload_doc();
                    }
                })
            });
        }
    }
});