frappe.listview_settings['Drivers'] = {
	add_fields: ["driver_status", "working_status"],
	get_indicator:function(doc){
		if (doc.driver_status === "Online") {
			return [__("Online"), "green", "status,=,Online"];
		}
		if (doc.driver_status === "Offline") {
			return [__("Offline"), "darkgrey", "status,=,Offline"];
		}
		if (doc.working_status === "Available") {
			return [__("Available"), "green", "working_status,=,Available"];
		}
		if (doc.working_status === "Unavailable") {
			return [__("Unavailable"), "red", "working_status,=,Unavailable"];
		}
	}
}


