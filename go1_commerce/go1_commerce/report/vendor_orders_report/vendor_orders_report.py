# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns=get_columns()
	data=vendororder_report(filters)
	return columns, data

def get_columns():
	if "Shipping Provider" in frappe.get_roles(frappe.session.user) and frappe.session.user != 'Administrator':
		return[
			"Order ID" + ":Link/Order:150",
			"Customer ID" + ":Link/Customers:150",
			"Business Name" + ":Data:120",
			"Order Date" + ":Date:120",
			"Order Status" + ":Data:120",
			"Payment Method" + ":Data:120",
			"Payment Status" + ":Data:120",
			"Shipping Date" + ":Date:120",
			"Delivered Date" + ":Date:120",
			"Order Amount" + ":Currency:120",
			"IGST" + ":Currency:120",
			"SGST" + ":Currency:120",
			"CGST" + ":Currency:120",
			"Order Total" + ":Currency:120",
		]
	elif "Vendor" in frappe.get_roles(frappe.session.user) and frappe.session.user != 'Administrator':
		return[
			"Order ID" + ":Link/Order:150",
			"Customer ID" + ":Link/Customers:150",
			"Invoice Date" + ":Date:120",
			"Invoice Number" + ":Link/Vendor Orders:150",
			"Order Date" + ":Date:120",
			"Order Status" + ":Data:120",
			"Payment Method" + ":Data:120",
			"Payment Status" + ":Data:120",
			"Driver Name" + ":Data:120",
			"Shipping Provider" + ":Data:120",
			"Shipping Charges" + ":Currency:120",
			"Shipping Date" + ":Date:120",
			"Delivered Date" + ":Date:120",
			"Order Amount" + ":Currency:120",
			"Delivery Charges" + ":Currency:120",
			"Commision Amount" + ":Currency:120",
			"IGST" + ":Currency:120",
			"SGST" + ":Currency:120",
			"CGST" + ":Currency:120",
			"Order Total" + ":Currency:120",
		]
	else:
		return[
			"Order ID" + ":Link/Order:150",
			"Customer ID" + ":Link/Customers:150",
			"Invoice Date" + ":Date:120",
			"Invoice Number" + ":Link/Vendor Orders:150",
			"Order Date" + ":Date:120",
			"Order Status" + ":Data:120",
			"Payment Method" + ":Data:120",
			"Payment Status" + ":Data:120",
			"Business Name" + ":Data:120",
			"GST" + ":Data:120",
			"Vendor Commision" + ":Currency:120",
			"Driver Name" + ":Data:120",
			"Shipping Provider" + ":Data:120",
			"Shipping Charges" + ":Currency:120",
			"Delivered Date" + ":Date:120",
			"Order Amount" + ":Currency:120",
			"Delivery Charges" + ":Currency:120",
			"Commision Amount" + ":Currency:120",
			"IGST" + ":Currency:120",
			"SGST" + ":Currency:120",
			"CGST" + ":Currency:120",
			"Order Total" + ":Currency:120",
		]
	
def vendororder_report(filters):
	condition=''
	if filters.get('from_date'):
		condition+=' and VO.order_date>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		condition+=' and VO.order_date<="%s"' % filters.get('to_date')
	if filters.get('status'):
		condition+=' and VO.status="%s"' % filters.get('status')
	if filters.get('payment_status'):
		condition+=' and VO.payment_status="%s"' % filters.get('payment_status') 
	
	if "Vendor" in frappe.get_roles(frappe.session.user) and frappe.session.user != 'Administrator':
		shop_user=frappe.db.get_all('Shop User',filters={'name':frappe.session.user},fields=['name','restaurant'])
		if shop_user and shop_user[0].restaurant:
			condition+=' and VO.business="%s"' % shop_user[0].restaurant
		vendor_order = frappe.db.sql('''select VO.order_reference,VO.customer,VO.order_date,VO.name,VO.order_date,VO.status,VO.payment_method_name,VO.payment_status,ifnull(D.driver_name,''),ifnull(VO.shipping_provider,''),VO.shipping_charges,cast(S.shipped_date as date),cast(S.delivered_date as date),VO.order_subtotal,VO.shipping_charges,VO.commission_amt,case when B.state=VO.shipping_state then VO.total_tax_amount else 0 end as igst,case when B.state<>VO.shipping_state then VO.total_tax_amount/2 else 0 end as sgst,case when B.state!=VO.shipping_state then VO.total_tax_amount/2 else 0 end as cgst,VO.total_amount from `tabVendor Orders` VO left join `tabBusiness` B on B.name=VO.business left join `tabShipment` S on S.document_name=VO.name left join `tabDrivers` D on D.name=S.driver where VO.docstatus=1 {condition} order by VO.creation desc'''.format(condition=condition), as_list=1)
	elif "Shipping Provider" in frappe.get_roles(frappe.session.user) and frappe.session.user != 'Administrator':
		shipping_provider=frappe.db.get_all('Shipping Provider',filters={'email':frappe.session.user},fields=['name','email'])
		if shipping_provider and shipping_provider[0].name:
			condition+=' and VO.shipping_provider="%s"' % shipping_provider[0].name
		vendor_order = frappe.db.sql('''select VO.order_reference,VO.customer,VO.order_date,VO.status,VO.payment_method_name,VO.payment_status,ifnull(D.driver_name,''),cast(S.shipped_date as date),cast(S.delivered_date as date),VO.order_subtotal,case when B.state=VO.shipping_state then VO.total_tax_amount else 0 end as igst,case when B.state<>VO.shipping_state then VO.total_tax_amount/2 else 0 end as sgst,case when B.state!=VO.shipping_state then VO.total_tax_amount/2 else 0 end as cgst,VO.total_amount from `tabVendor Orders` VO left join `tabBusiness` B on B.name=VO.business left join `tabShipment` S on S.document_name=VO.name left join `tabDrivers` D on D.name=S.driver where VO.docstatus=1 {condition} order by VO.creation desc'''.format(condition=condition), as_list=1)
	else:
		vendor_order = frappe.db.sql('''select VO.order_reference,VO.customer,VO.order_date,VO.name,VO.order_date,VO.status,VO.payment_method_name,VO.payment_status,B.restaurant_name,ifnull(B.gstin,''),VO.total_amount_for_vendor,ifnull(D.driver_name,''),ifnull(VO.shipping_provider,''),VO.shipping_charges,cast(S.delivered_date as date),VO.order_subtotal,VO.shipping_charges,VO.commission_amt,case when B.state=VO.shipping_state then VO.total_tax_amount else 0 end as igst,case when B.state<>VO.shipping_state then VO.total_tax_amount/2 else 0 end as sgst,case when B.state!=VO.shipping_state then VO.total_tax_amount/2 else 0 end as cgst,VO.total_amount from `tabVendor Orders` VO left join `tabBusiness` B on B.name=VO.business left join `tabShipment` S on S.document_name=VO.name left join `tabDrivers` D on D.name=S.driver where VO.docstatus=1 {condition} order by VO.creation desc'''.format(condition=condition), as_list=1)
	return vendor_order