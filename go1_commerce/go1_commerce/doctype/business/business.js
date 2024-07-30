// Copyright (c) 2018, info@valiantsystems.com and contributors
// For license information, please see license.txt

frappe.require("assets/go1_commerce/css/uppy.min.css");
frappe.require("assets/go1_commerce/js/uppy.min.js");
frappe.require("assets/go1_commerce/js/jquery-sortable.js");

frappe.ui.form.on('Business', {
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
   
    refresh: function(frm) {
        if(frm.doc.country){
            frm.set_query("state", function() {
               return {
                   "filters": {
                       "country": frm.doc.country,
                   }
               };
           });
       }

        if(frm.doc.state){
            frm.set_query("city", function() {
                return {
                    "filters": {
                        "state": frm.doc.state,
                    }
                };
            });
        }
     
       frm.set_query("country", function() {
           return {
               "filters": {
                   "enabled": 1
               }
           }
       });
       
    },
    after_save: function(frm) {
        cur_frm.reload_doc();
    },
});


