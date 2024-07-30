//by sivaranjani
frappe.listview_settings['API Log'] = {
	add_fields: ["seen"],
	get_indicator: function(doc) {
		if(cint(doc.seen)) {
			return [__("Seen"), "green", "seen,=,1"];
		} else {
			return [__("Not Seen"), "red", "seen,=,0"];
		}
	},
	order_by: "seen asc, modified desc",
	onload: function(listview) {
		listview.page.add_menu_item(__("Clear API Logs"), function() {
			frappe.call({
				method:'go1_commerce.go1_commerce.doctype.api_log.api_log.clear_api_logs',
				callback: function() {
					listview.refresh();
				}
			});
		});
	}
};
