// Copyright (c) 2020, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm) {
		if(frm.doc.status!="Paid" && frm.doc.docstatus==1){
            frm.remove_custom_button('Make Payment');
            frm.add_custom_button("Make Payment", function() {
                frappe.model.open_mapped_doc({
                    method: "go1_commerce.accounts.api.make_invoice_payment",
                    frm: cur_frm
                })
            });
        }  
        if (frm.doc.tax_breakup) {
            frm.trigger('show_tax_spliup')
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
                    let row_data = $(`  <tr>
                                            <td> ${tax_type} </td>
                                            <td> ${frappe.format(tax_percent)} </td>
                                            <td> ${parseFloat(tax_value).toFixed(2)} </td>
                                            <td> ${product_tax_type} </td>
                                        </tr>`);
                    table_html.find('tbody').append(row_data);
                }
            })
        }
    },
});