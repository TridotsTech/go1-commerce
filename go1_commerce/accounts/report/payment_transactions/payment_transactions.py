# Copyright (c) 2023, Tridotstech and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder import DocType

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return[
			"Posted Date" + ":Date",
			"Posted Time" + ":Data:120",
			"Order ID" + ":Data:120",
			"Customer Name" + ":Data:200",
			"Mode Of Payment" + ":Data:200",
			"Transaction Type" + ":Data:200",
			"Transaction ID" + ":Data:200",
			"Amount" + ":Currency:120"
		]

# def get_data(filters):
# 	condition = ""
# 	if filters.get("from_date"):
# 		condition += " AND PE.posting_date>='"+filters.get("from_date")+"'"
# 	if filters.get("to_date"):
# 		condition += " AND PE.posting_date<='"+filters.get("to_date")+"'"

# 	query = """
# 				SELECT 
# 				DATE(PE.creation) AS posted_date,
# 				DATE_FORMAT(PE.creation,'%h:%i %p') posted_time,
# 				CASE WHEN PR.reference_doctype="Sales Invoice" THEN
# 				    (SELECT reference FROM `tabSales Invoice` WHERE name=PR.reference_name)
# 				    WHEN PR.reference_doctype="Order" THEN PR.reference_name
# 				    ELSE  (
				   
# 				         SELECT  CASE WHEN order_type="Sales Invoice"
# 				         THEN (SELECT reference FROM `tabSales Invoice` WHERE name=order_id)
# 				         ELSE order_id END AS order_id
# 				            FROM `tabWallet Transaction` WHERE name=PR.reference_name
# 				            )
# 				    END
# 				AS order_id,
# 				C.business_name AS customer_name,
# 				CASE 
# 				WHEN PE.mode_of_payment="Cash"
# 				    THEN (
# 				        CASE 
# 				            WHEN PE.payment_type='Pay' THEN 'Wallet'
# 				            ELSE 
# 				            (
# 				            CASE 
# 				                WHEN PR.reference_doctype="Wallet Transaction" THEN "Wallet" 
# 				                ELSE "Cash" END
# 				            )
# 				            END
# 				        )
# 				ELSE PE.mode_of_payment END AS mode_of_payment,
# 				CASE WHEN PE.payment_type='Pay' THEN 'Debit'
# 				ELSE 'Credit' END AS transaction_type,
# 				PE.reference_no AS transaction_id,
# 				ROUND(allocated_amount,2) AS amount 
# 				FROM `tabPayment Reference` PR INNER JOIN `tabPayment Entry` PE ON PE.name = PR.parent 
# 				INNER JOIN `tabCustomers` C ON C.name = PE.party 
# 				WHERE PE.docstatus=1 {condition}
# 				ORDER BY PE.creation DESC 

# 			""".format(condition=condition)
# 	return frappe.db.sql(query,as_dict=1)

def get_data(filters):
	query = frappe.qb.from_("tabPayment Reference").as_("PR")
		.inner_join("tabPayment Entry").as_("PE")
		.on("PE.name = PR.parent")
		.inner_join("tabCustomers").as_("C")
		.on("C.name = PE.party")
		.select(
			frappe.qb.function("DATE", "PE.creation").as_("posted_date"),
			frappe.qb.function("DATE_FORMAT", "PE.creation", "%h:%i %p").as_("posted_time"),
			frappe.qb.case(
				frappe.qb.when("PR.reference_doctype = 'Sales Invoice'", 
						frappe.qb.subquery(
							frappe.qb.from_("tabSales Invoice")
							.select("reference")
							.where("name = PR.reference_name")
						)
				).when("PR.reference_doctype = 'Order'", "PR.reference_name")
				.otherwise(
					frappe.qb.subquery(
						frappe.qb.from_("tabWallet Transaction")
						.select(
							frappe.qb.case()
							.when("order_type = 'Sales Invoice'", 
								frappe.qb.subquery(
									frappe.qb.from_("tabSales Invoice")
									.select("reference")
									.where("name = order_id")
								  )
							)
							.otherwise("order_id")
						)
						.where("name = PR.reference_name")
					)
				)
			).as_("order_id"),
			"C.business_name.as_(customer_name)",
			frappe.qb.case(
				frappe.qb.when("PE.mode_of_payment = 'Cash'",
						frappe.qb.case(
							frappe.qb.when("PE.payment_type = 'Pay'", "'Wallet'")
							.otherwise(
								frappe.qb.case(
									frappe.qb.when("PR.reference_doctype = 'Wallet Transaction'", "'Wallet'")
									.otherwise("'Cash'")
								)
							)
						)
				).otherwise("PE.mode_of_payment")
			).as_("mode_of_payment"),
			frappe.qb.case(
				frappe.qb.when("PE.payment_type = 'Pay'", "'Debit'")
				.otherwise("'Credit'")
			).as_("transaction_type"),
			"PE.reference_no.as_(transaction_id)",
			frappe.qb.function("ROUND", "allocated_amount", 2).as_("amount")
		)

	if filters.get("from_date"):
		query = query.where(qb.function("DATE", "PE.posting_date") >= filters.get("from_date"))
	if filters.get("to_date"):
		query = query.where(qb.function("DATE", "PE.posting_date") <= filters.get("to_date"))
	query = query.orderby("PE.creation DESC")
	return query.run(as_dict=True)