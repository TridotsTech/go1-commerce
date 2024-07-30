// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Entry', {
	setup: function(frm) {
		frm.events.filter_link_field_data(frm)
	},
	refresh: function(frm) {
		frm.events.hide_unhide_fields(frm);
		frm.events.set_dynamic_labels(frm);
	},
	filter_link_field_data(frm){
		frm.set_query("reference_doctype","references", function() {
			return{
				"filters": {
					"name": ["in", ["Purchase Order","Purchase Invoice"]]
				}
			}
		});
		frm.set_query("party_type", function() {
			return{
				"filters": {
					"name": ["in", ["Customers","Supplier","Drivers","Business"]]
				}
			}
		});
		frm.set_query("contact_person", function() {
			if (frm.doc.party) {
				return {
					query: 'frappe.contacts.doctype.contact.contact.contact_query',
					filters: {
						link_doctype: frm.doc.party_type,
						link_name: frm.doc.party
					}
				};
			}
		});
		frm.set_query("reference_doctype", "references", function() {
			if (frm.doc.party_type=="Customer") {
				var doctypes = ["Order", "Invoice"];
			}

			return {
				filters: { "name": ["in", doctypes] }
			};
		});

		frm.set_query("reference_name", "references", function(doc, cdt, cdn) {
			const child = locals[cdt][cdn];
			const filters = {"docstatus": 1, "company": doc.company};
			const party_type_doctypes = ['Invoice', 'Order'];
			if (in_list(party_type_doctypes, child.reference_doctype)) {
				filters[doc.party_type.toLowerCase()] = doc.party;
			}
			return {
				filters: filters
			};
		});
	},
	contact_person: function(frm) {
		frm.set_value("contact_email", "");
	},
	hide_unhide_fields: function(frm) {
		var party_amount = frm.doc.payment_type=="Receive" ?frm.doc.paid_amount : frm.doc.received_amount;
		frm.toggle_display("received_amount", (frm.doc.payment_type == "Internal Transfer" ||
												frm.doc.paid_from_account_currency != frm.doc.paid_to_account_currency))
		frm.toggle_display(["base_total_allocated_amount"],
			(frm.doc.paid_amount && frm.doc.received_amount && frm.doc.base_total_allocated_amount &&
			((frm.doc.payment_type == "Receive" && frm.doc.paid_from_account_currency != company_currency) ||
			(frm.doc.payment_type == "Pay" && frm.doc.paid_to_account_currency != company_currency))));
		frm.toggle_display("write_off_difference_amount", (frm.doc.difference_amount && frm.doc.party &&
															(frm.doc.total_allocated_amount > party_amount)));
		frm.toggle_display("set_exchange_gain_loss",(frm.doc.paid_amount && 
			frm.doc.received_amount && frm.doc.difference_amount &&
			((frm.doc.paid_from_account_currency != company_currency ||
			frm.doc.paid_to_account_currency != company_currency) &&
			frm.doc.paid_from_account_currency != frm.doc.paid_to_account_currency)));
		frm.refresh_fields();
	},
	set_dynamic_labels: function(frm) {
		var company_currency = frm.doc.company ? frappe.get_doc(":Company", frm.doc.company).default_currency: "";
		var party_account_currency = frm.doc.payment_type == "Receive" ? frm.doc.paid_from_account_currency : 
																				frm.doc.paid_to_account_currency;
		var currency_field = (frm.doc.payment_type == "Receive") ? "paid_from_account_currency" : "paid_to_account_currency"
		frm.set_currency_labels(["base_paid_amount", "base_received_amount", "base_total_allocated_amount",
																		"difference_amount"], company_currency);
		frm.set_currency_labels(["total_allocated_amount", "unallocated_amount"], party_account_currency);
		frm.set_df_property("total_allocated_amount", "options", currency_field);
		frm.set_df_property("unallocated_amount", "options", currency_field);
		frm.set_df_property("party_balance", "options", currency_field);
		frm.set_currency_labels(["total_amount", "outstanding_amount", "allocated_amount"],party_account_currency,
																								"references");
		frm.set_currency_labels(["amount"], company_currency, "deductions");
		cur_frm.set_df_property("source_exchange_rate", "description",
								("1 " + frm.doc.paid_from_account_currency + " = [?] " + company_currency));
		cur_frm.set_df_property("target_exchange_rate", "description",
								("1 " + frm.doc.paid_to_account_currency + " = [?] " + company_currency));
		frm.refresh_fields();
	},
	show_general_ledger: function(frm) {
		if(frm.doc.docstatus == 1) {
			frm.add_custom_button(__('Ledger'), function() {
				frappe.route_options = {
					"voucher_no": frm.doc.name,
					"from_date": frm.doc.posting_date,
					"to_date": frm.doc.posting_date,
					"company": frm.doc.company,
					group_by: ""
				};
				frappe.set_route("query-report", "General Ledger");
			}, "fa fa-table");
		}
	},
	payment_type: function(frm) {
		if(frm.doc.payment_type == "Internal Transfer") {
			let fields = ["party", "party_balance", "paid_from", "paid_to",
						"references", "total_allocated_amount"]
			$.each(fields,function(i, field) {
					frm.set_value(field, null);
			});
		} 
		else {
			if(frm.doc.party) {
				frm.events.party(frm);
			}
		}
	},
	party_type: function(frm) {
		if(frm.doc.party) {
			let fields = ["party", "party_balance", "paid_from", "paid_to",
						"paid_from_account_currency", "paid_from_account_balance",
						"paid_to_account_currency", "paid_to_account_balance",
						"references", "total_allocated_amount"]
			$.each(fields,function(i, field) {
					frm.set_value(field, null);
				})
		}
	},
	party: function(frm) {
		if (frm.doc.contact_email || frm.doc.contact_person) {
			frm.set_value("contact_email", "");
			frm.set_value("contact_person", "");
		}
		if(frm.doc.payment_type && frm.doc.party_type && frm.doc.party) {
			if(!frm.doc.posting_date) {
				frappe.msgprint(__("Please select Posting Date before selecting Party"))
				frm.set_value("party", "");
				return ;
			}
			frm.set_party_account_based_on_party = true;
		}
	},
	posting_date: function(frm) {
		frm.events.paid_from_account_currency(frm);
	},
	paid_amount: function(frm,cdt,cdn) {
		frm.set_value("base_paid_amount", flt(frm.doc.paid_amount) * flt(frm.doc.source_exchange_rate));
	},
	allocate_payment_amount: function(frm) {
		if(frm.doc.payment_type == 'Internal Transfer'){
			return
		}
		if(frm.doc.references.length == 0){
			frm.events.get_outstanding_documents(frm);
		}
		if(frm.doc.payment_type == 'Internal Transfer') {
			frm.events.allocate_party_amount_against_ref_docs(frm, frm.doc.paid_amount);
		} else {
			frm.events.allocate_party_amount_against_ref_docs(frm, frm.doc.received_amount);
		}
	},
	allocate_party_amount_against_ref_docs: function(frm, paid_amount) {
		var total_positive_outstanding_including_order = 0;
		var total_negative_outstanding = 0;
		var allocated_positive_outstanding = 0
		var allocated_negative_outstanding = 0;
		var total_deductions = frappe.utils.sum($.map(frm.doc.deductions || [],function(d) { return flt(d.amount) }));
		paid_amount -= total_deductions;
		$.each(frm.doc.references || [], function(i, row) {
			if(flt(row.outstanding_amount) > 0)
				total_positive_outstanding_including_order += flt(row.outstanding_amount);
			else
				total_negative_outstanding += Math.abs(flt(row.outstanding_amount));
		})
		if ((frm.doc.payment_type=="Receive" && frm.doc.party_type=="Customer") ||
			(frm.doc.payment_type=="Pay" && frm.doc.party_type=="Supplier") ||
			(frm.doc.payment_type=="Pay" && frm.doc.party_type=="Employee") ||
			(frm.doc.payment_type=="Receive" && frm.doc.party_type=="Student")){
				if(total_positive_outstanding_including_order > paid_amount) {
					var remaining_outstanding = total_positive_outstanding_including_order - paid_amount;
					allocated_negative_outstanding = total_negative_outstanding < remaining_outstanding ?
													total_negative_outstanding : remaining_outstanding;
			}
			allocated_positive_outstanding =  paid_amount + allocated_negative_outstanding;
		} 
		else if(in_list(["Customer", "Supplier"], frm.doc.party_type)) {
			if(paid_amount > total_negative_outstanding){
				if(total_negative_outstanding == 0) {
					frappe.msgprint(__("Cannot {0} {1} {2} without any negative outstanding invoice",
						[frm.doc.payment_type,(frm.doc.party_type=="Customer" ? "to" : "from"), 
						frm.doc.party_type]));
					return false
				}
				else{
					frappe.msgprint(__("Paid Amount cannot be greater than total negative outstanding amount {0}", [total_negative_outstanding]));
					return false;
				}
			} 
			else{
				allocated_positive_outstanding = total_negative_outstanding - paid_amount;
				allocated_negative_outstanding = paid_amount + 
					(total_positive_outstanding_including_order < allocated_positive_outstanding ?
					total_positive_outstanding_including_order : allocated_positive_outstanding)
			}
		}
		$.each(frm.doc.references || [], function(i, row) {
			row.allocated_amount = 0 //If allocate payment amount checkbox is unchecked, set zero to allocate amount
			if(frm.doc.allocate_payment_amount){
				if(row.outstanding_amount > 0 && allocated_positive_outstanding > 0) {
					if(row.outstanding_amount >= allocated_positive_outstanding) {
						row.allocated_amount = allocated_positive_outstanding;
					} 
					else{
						row.allocated_amount = row.outstanding_amount;
					}
					allocated_positive_outstanding -= flt(row.allocated_amount);
				} 
				else if (row.outstanding_amount < 0 && allocated_negative_outstanding) {
					if(Math.abs(row.outstanding_amount) >= allocated_negative_outstanding){
						row.allocated_amount = -1*allocated_negative_outstanding;
					}
					else{ 
						row.allocated_amount = row.outstanding_amount;
					}
					allocated_negative_outstanding -= Math.abs(flt(row.allocated_amount));
				}
			}
		})
		frm.refresh_fields()
		frm.events.set_total_allocated_amount(frm);
	},
	set_total_allocated_amount: function(frm) {
		var total_allocated_amount = 0.0;
		var base_total_allocated_amount = 0.0;
		$.each(frm.doc.references || [], function(i, row) {
			if(row.allocated_amount) {
				total_allocated_amount += flt(row.allocated_amount);
				base_total_allocated_amount += flt(flt(row.allocated_amount) * flt(row.exchange_rate),
																			precision("base_paid_amount"));
			}
		});
		frm.set_value("total_allocated_amount", Math.abs(total_allocated_amount));
		frm.set_value("base_total_allocated_amount", Math.abs(base_total_allocated_amount));
		frm.events.set_unallocated_amount(frm);
	},
	set_unallocated_amount: function(frm) {
		var unallocated_amount = 0;
		var total_deductions = frappe.utils.sum($.map(frm.doc.deductions || [],function(d) { return flt(d.amount) }));
		if(frm.doc.party) {
			if(frm.doc.payment_type == "Receive"
				&& frm.doc.base_total_allocated_amount < frm.doc.base_received_amount + total_deductions
				&& frm.doc.total_allocated_amount < frm.doc.paid_amount + (total_deductions / frm.doc.source_exchange_rate)) {
					unallocated_amount = (frm.doc.base_received_amount + total_deductions
						- frm.doc.base_total_allocated_amount) / frm.doc.source_exchange_rate;
			} 
			else if(frm.doc.payment_type == "Pay"
				&& frm.doc.base_total_allocated_amount < frm.doc.base_paid_amount - total_deductions
				&& frm.doc.total_allocated_amount < frm.doc.received_amount + (total_deductions / frm.doc.target_exchange_rate)){
					unallocated_amount = (frm.doc.base_paid_amount - (total_deductions
						+ frm.doc.base_total_allocated_amount)) / frm.doc.target_exchange_rate;
			}
		}
		frm.set_value("unallocated_amount", unallocated_amount);
		frm.trigger("set_difference_amount");
	},
	set_difference_amount: function(frm){
		var difference_amount = 0;
		var base_unallocated_amount = flt(frm.doc.unallocated_amount) *
			(frm.doc.payment_type=="Receive" ? frm.doc.source_exchange_rate : frm.doc.target_exchange_rate);
		var base_party_amount = flt(frm.doc.base_total_allocated_amount) + base_unallocated_amount;
		if(frm.doc.payment_type == "Receive") {
			difference_amount = base_party_amount - flt(frm.doc.base_received_amount);
		} 
		else if(frm.doc.payment_type == "Pay") {
			difference_amount = flt(frm.doc.base_paid_amount) - base_party_amount;
		} 
		else{
			difference_amount = flt(frm.doc.base_paid_amount) - flt(frm.doc.base_received_amount);
		}
		var total_deductions = frappe.utils.sum($.map(frm.doc.deductions || [],function(d) { return flt(d.amount) }));
		frm.set_value("difference_amount", difference_amount - total_deductions);
		frm.events.hide_unhide_fields(frm);
	},
	unallocated_amount: function(frm) {
		frm.trigger("set_difference_amount");
	},
	validate_reference_document: function(frm, row) {
		var _validate = function(i, row) {
			if (!row.reference_doctype) {
				return;
			}
			if(frm.doc.party_type == "Customers" && in_list(["Sales Invoice","Order"], row.reference_doctype)) {
				frappe.model.set_value(row.doctype, row.name, "reference_doctype", null);
				frappe.msgprint(__("Row #{0}: Reference Document Type must be one of Sales Order, Sales Invoice or Journal Entry", [row.idx]));
				return false;
			}
			if(frm.doc.party_type == "Supplier" && in_list(["Purchase Order", "Purchase Invoice", "Journal Entry"],row.reference_doctype)){
				frappe.model.set_value(row.doctype, row.name, "against_voucher_type", null);
				frappe.msgprint(__("Row #{0}: Reference Document Type must be one of Purchase Order, Purchase Invoice or Journal Entry", [row.idx]));
				return false;
			}
		}
		if (row) {
			_validate(0, row);
		} 
		else {
			$.each(frm.doc.vouchers || [], _validate);
		}
	},
});

frappe.ui.form.on('Payment Reference', {
	reference_doctype: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		frm.events.validate_reference_document(frm, row);
	},
})

frappe.ui.form.on('Payment Deduction', {
	amount: function(frm) {
		frm.events.set_unallocated_amount(frm);
	},
	deductions_remove: function(frm) {
		frm.events.set_unallocated_amount(frm);
	}
})