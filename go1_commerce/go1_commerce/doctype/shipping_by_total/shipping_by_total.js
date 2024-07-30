// Copyright (c) 2019, sivaranjani and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shipping By Total', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on("Shipping Charges By Total", {
	use_percentage:function(frm, cdt, cdn){
        var shipping_by_total = frappe.get_doc(cdt,cdn);
        if (shipping_by_total.use_percentage == 1) {
        	frappe.model.set_value(cdt,cdn,'charge_amount',0);
        } 
        else {
        	frappe.model.set_value(cdt,cdn,'charge_percentage',0);
        }
    },
    from_total: function(frm, cdt, cdn){
        var d= frappe.get_doc(cdt,cdn);
        if(d.from_total){
            for(var i=0;i<frm.doc.shipping_charges.length;i++){
                if(frm.doc.shipping_charges[i].name!=d.name){
                    if(parseFloat(frm.doc.shipping_charges[i].from_total)<=parseFloat(d.from_total)){
                        if(parseFloat(d.from_total)<=parseFloat(frm.doc.shipping_charges[i].to_total)){
                            frappe.throw("From Total already exists")
                        }    
                    }
                }
            }
        }    
    },
    to_total: function(frm, cdt, cdn){
         var d= frappe.get_doc(cdt,cdn);
         if(d.to_total){
            for(var i=0;i<frm.doc.shipping_charges.length;i++){
                if(frm.doc.shipping_charges[i].name!=d.name){
                    if(parseFloat(frm.doc.shipping_charges[i].from_total)<=parseFloat(d.to_total)){
                        if(parseFloat(d.to_total)<=parseFloat(frm.doc.shipping_charges[i].to_total)){
                            frappe.throw("To Total already exists") 
                        }  
                    }
                }
            }
        }
    }
}); 