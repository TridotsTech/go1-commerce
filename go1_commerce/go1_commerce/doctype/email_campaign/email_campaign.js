// Copyright (c) 2019, Tridots Tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Email Campaign', {
	refresh: function(frm) {
		frm.trigger('email_campaign_for')
	},
	email_campaign_for: function(frm){
		if(frm.doc.email_campaign_for){
			if(frm.doc.email_campaign_for != frm.doc.campaign_for)
				frm.set_value('campaign_for', frm.doc.email_campaign_for)
		}
	}
});
