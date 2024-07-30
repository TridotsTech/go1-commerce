var restaurant='';
frappe.listview_settings['Order'] = {
	add_fields: ["status", "payment_status", "shipping_status","order_date","total_amount", "docstatus"],
	get_indicator: function(doc) {
		if (doc.docstatus === 1) {
		    if (doc.status === "Placed") {
				return [__("Placed"), "grey", "status,=,Open"];
			}else if (doc.status  === "Processing") {
				return [__("Processing"), "orange", "status,=,Processing"];
			}  
			else if (doc.status  === "In Process") {
				return [__("In Process"), "grey", "status,=,In Process"];
			} 
			else if (doc.status  === "Shipped") {
				return [__("Shipped"), "orange", "status,=," + doc.status];
			} 
			else if (doc.status  === "Partially Shipped") {
				return [__("Partially Shipped"), "orange", "status,=," + doc.status];
			}
			else if (doc.status  === "Packed") {
				return [__("Packed"), "orange", "status,=," + doc.status];
			} 
			else if (doc.status  === "Partially Packed") {
				return [__("Partially Packed"), "orange", "status,=," + doc.status];
			}
			else if (doc.status  === "Ready") {
				return [__("Ready"), "orange", "status,=,Ready"];
			} 
			else if (doc.status  === "Delivered") {
				return [__("Delivered"), "green", "status,=," + doc.status];
			} 
			else if (doc.status  === "Partially Delivered") {
				return [__("Partially Delivered"), "green", "status,=," + doc.status];
			} 
			else if (doc.status === "Returned"){
				return [__("Returned"), "red", "status,=," + doc.status];
			}
			
			else if (doc.status  === "Cancelled") {
				return [__("Cancelled"), "red", "status,=,Cancelled"];
			} else if (doc.status  === "Completed") {
				return [__("Completed"), "green", "status,=,Completed"];
			} else if(doc.status.toLowerCase().indexOf('partially') > - 1) {
				return [__("Processing"), "orange", "status,=," + doc.status]
			}
		}else{
			if (doc.status === "Placed") {
				return [__("Open"), "grey", "status,=,Open"];
			}else if (doc.status  === "Processing") {
				return [__("Processing"), "orange", "status,=,Processing"];
			}  else if (doc.status  === "Cancelled") {
				return [__("Cancelled"), "red", "status,=,Cancelled"];
			} else if (doc.status  === "Completed") {
				return [__("Completed"), "green", "status,=,Completed"];
			} 
		}
	},
	refresh: function(me) {
		console.log("List view");
		$(".list-row-col.ellipsis.list-subject.level").attr("style","flex:1.5 !important")
		$('span.indicator.red.filterable[data-filter="docstatus,=,0"]').text("Pending");
		$('[data-fieldname="name"]').attr("placeholder","Order ID")
		$('span.indicator.orange.filterable[data-filter="payment_status,=,Pending"]').attr('style','background: #ffa00a;color: #fff;');
		$('span.indicator.darkgrey.filterable[data-filter="payment_status,=,Cancelled"]').attr('style','background: #ff5858;color: #fff;');
		$('span.indicator.darkgrey.filterable[data-filter="payment_status,=,Refunded"]').attr('style','background: #ff5858;color: #fff;');
		$('span.indicator.green.filterable[data-filter="payment_status,=,Paid"]').attr('style','background: #98d85b;color: #fff;');
		$('span.indicator.green.filterable[data-filter="payment_status,=,Partially Paid"]').attr('style','background: #98d85b;color: #fff;')
		$('span.indicator.orange.filterable[data-filter="payment_status,=,Pending"]').removeClass('indicator');
		$('span.indicator.darkgrey.filterable[data-filter="payment_status,=,Cancelled"]').removeClass('indicator');
		$('span.indicator.green.filterable[data-filter="payment_status,=,Paid"]').removeClass('indicator');
		$('span.indicator.green.filterable[data-filter="payment_status,=,Partially Paid"]').removeClass('indicator');
		$('span.indicator.darkgrey.filterable[data-filter="payment_status,=,Refunded"]').removeClass('indicator');
	},
	onload: function(listview) {
		if(frappe.session.user == 'Administrator') {
			listview.page.add_menu_item(__("Clear Records"), function() {
				listview.call_for_selected_items('go1_commerce.go1_commerce.doctype.order.order.clear_selected_orders', {"status": "Completed"});
			});
		}
	}
};
var audio = new Audio('/assets/js/bell-ring.mp3');
