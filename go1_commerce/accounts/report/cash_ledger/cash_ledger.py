# Copyright (c) 2023, Tridots Tech and contributors
# For license information, please see license.txt

# import frappe

import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	# frappe.log_error("222222222222",data)
	return columns, data

def get_columns():
	return[
			
			"Cash Collection Date" + ":Date:200",
			"Cash Approval Date" + ":Date:200",
			"Customer" + ":Link/Customers:120",
			"Customer Name" + ":Data:120",
			"Against" + ":Data",
			"Against Reference" + ":Data",
			"Order ID" + ":Data",
			"Amount" + ":Currency:80"

		]

def get_data(filters):
	condition = ""
	# if filters.get("se_id"):
	# 	condition = " AND tx.name='"+filters.get("se_id")+"'"
	# if filters.get("customer"):
	# 	condition = " AND tm.party='"+filters.get("customer")+"'"
	# if filters.get("reference_doctype"):
	# 	condition = " AND tt.reference_doctype='"+filters.get("reference_doctype")+"'"
	if filters.get('from_date'):
		condition+=' and tm.modified>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		condition+=' and tm.modified<="%s"' % filters.get('to_date')

	# return frappe.db.sql(""" 
	# 						SELECT tx.name as sales_executive_id,tx.first_name as sales_executive_name,
	# 	      				tm.creation as date,tm.party as customer,
	# 	      				cs.first_name as customer_name,tt.reference_doctype as against,tt.reference_name as against_reference,tm.paid_amount as amount
	# 	      				FROM `tabPayment Entry` tm inner join `tabPayment Reference` tt on tm.name=tt.parent  
	# 						left join `tabEmployee` tx on tm.owner=tx.username  
	# 						left join `tabCustomers` cs on cs.name=tm.party 
	# 						WHERE tm.mode_of_payment='Cash' and tt.reference_doctype<>'Wallet Transaction' AND
	# 	      				tx.name is not Null and tm.docstatus = 1 {condition} ORDER BY tm.creation DESC
	# 					""".format(condition=condition),as_dict = 1)
	ret_data = frappe.db.sql("""
							SELECT "" as cash_collection_date, 
							tm.modified as cash_approval_date,tm.party as customer,
	 	      				cs.first_name as customer_name,tt.reference_doctype as against,tt.reference_name as against_reference,
	 	      				tt.reference_name as order_id,
	 	      				tm.paid_amount as amount
	 	      				FROM `tabPayment Entry` tm inner join `tabPayment Reference` tt on tm.name=tt.parent 
	 	      				inner join `tabCustomers` cs on cs.name=tm.party
	 	      				WHERE tm.mode_of_payment='Cash' and tt.reference_doctype<>'Wallet Transaction' AND
	 	      				tm.docstatus = 1 AND tm.payment_type='Receive' {condition} ORDER BY tm.creation DESC
						""".format(condition=condition),as_dict = 1)
	
	for x in ret_data:
		if x.against=="Sales Invoice":
			x.order_id = frappe.db.get_value("Sales Invoice",x.against_reference,"reference")
		order_delivery = frappe.db.get_all("Order Delivery Slot",filters={"order":x.order_id},fields=['order_date'])
		if order_delivery:
			x.cash_collection_date = order_delivery[0].order_date
		else:
			x.cash_collection_date = frappe.db.get_value("Order",x.order_id,"order_date")
	return ret_data
