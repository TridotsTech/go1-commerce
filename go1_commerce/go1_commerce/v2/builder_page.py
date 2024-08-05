import frappe

@frappe.whitelist()
def update_global_script(doc,method):
	global_script = frappe.get_value("Builder Settings","Builder Settings","custom_server_script")
	if global_script:
		if doc.page_data_script:
			if "data.user = frappe.session.user" not in doc.page_data_script:
				doc.db_set('page_data_script',doc.page_data_script +"\n# Global Script"+ global_script)
		else:
			doc.db_set('page_data_script',"\n# Global Script\n"+global_script)
	frappe.db.commit()

