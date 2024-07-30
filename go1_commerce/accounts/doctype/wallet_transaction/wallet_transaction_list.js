frappe.listview_settings['Wallet Transaction'] = {
	add_fields: ["status", "transaction_type","type"],
	get_indicator: function(doc) {
		if (doc.docstatus === 1) {
			if (doc.status === "Pending") {
				return [__("Pending"), "orange", "status,=,Pending"];
			} 
			else if (doc.status  === "Locked") {
				return [__("Locked"), "black", "status,=,Locked"];
			}
			else if (doc.status  === "Approved") {
				return [__("Approved"), "blue", "status,=,Approved"];
			} 
			else if (doc.status  === "Cancelled") {
				return [__("Cancelled"), "red", "status,=,Cancelled"];
			} 
			else if (doc.status  === "Credited" &&  doc.transaction_type === "Pay") {
				return [__("Credited"), "green", "status,=,Credited"];
			} 
			else if (doc.status  === "Credited" &&  doc.transaction_type === "Receive") {
				if(doc.type == "Service Provider"){
					return [__("Credited"), "green", "status,=,Credited"];
				}
				else{
					return [__("Debited"), "red", "status,=,Credited"];
				}
			}
			else if (doc.status  === "Debited" &&  doc.transaction_type === "Pay") {
				return [__("Debited"), "red", "status,=,Debited"];
			}  
		}
		else if(doc.docstatus === 2) {
			return [__("Cancelled"), "red", "docstatus,=,2"];
		}
	}
};

