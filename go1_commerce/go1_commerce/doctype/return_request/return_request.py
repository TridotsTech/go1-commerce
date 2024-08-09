# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe.model.document import Document
import frappe, json
import datetime
from frappe.utils import flt, nowdate, getdate,now
from go1_commerce.utils.setup import get_settings


class ReturnRequest(Document):
	def validate(self):		
		update_order_status(self)
		order_info = frappe.get_doc('Order',self.order_id)
		self.customer = order_info.customer
		self.customer_email = frappe.db.get_value('Customers',self.customer,'email')
		for x in self.items:
			frappe.db.set_value('Order Item',x.order_item,'return_created',1)
			frappe.db.commit()
		current_status_level = frappe.db.get_value('Return Request Status',self.status,'status_level')
		next_status = frappe.db.sql(""" SELECT status_level
										FROM `tabReturn Request Status`
										WHERE status_level > %(level)s
										ORDER BY status_level
										""",{'level' : int(current_status_level)}, as_dict=True)
		if next_status and next_status[0].status_level:
			self.next_status_level = next_status[0].status_level
		else:
			self.next_status_level = self.next_status_level+1
		if self.product_price and self.quantity:
			self.product_amount = flt(self.product_price) * int(self.quantity)
		if self.attribute_id:
			self.attribute_description = frappe.db.get_value("Product Variant Combination",
                                                    {"attribute_id":self.attribute_id},"attribute_html")
		is_submittable = frappe.db.get_value('Return Request Status',self.status,'is_submittable')
		if is_submittable:
			self.docstatus = 1

	def after_insert(self):
		frappe.publish_realtime('update_menu', {'docname': self.name,'doctype':'Return Request'})

	def on_update(self):
		update_order_status(self)
		order_info = frappe.get_doc('Order',self.order_id)
		self.customer = order_info.customer
		self.customer_name = order_info.customer_name
		self.customer_email = order_info.customer_email
		self.customer_phone = order_info.phone
		payment_status = frappe.db.get_value("Order",self.order_id,"payment_status")
		from go1_commerce.utils.setup import get_settings
		order_settings = get_settings("Order Settings")
		catalog_settings = get_settings("Catalog Settings")
		if order_settings.return_amount_credited_to_wallet==1 and self.docstatus == 1 \
					and payment_status=="Paid" and self.is_unsuccess_delivery == 0 :
			ret_amt = 0
			for item in self.items:
				price = frappe.db.get_value("Order Item",item.order_item,"price")
				ret_amt += (item.quantity*price)
				if not catalog_settings.included_tax:
					ret_amt += frappe.db.get_value("Order Item",item.order_item,"tax")
			wallet_doc = frappe.new_doc('Wallet Transaction')
			wallet_doc.type = "Customers"
			wallet_doc.party_type = "Customers"
			wallet_doc.party = self.customer
			wallet_doc.reference = "Order"
			wallet_doc.order_type = "Order"
			wallet_doc.order_id = self.order_id
			wallet_doc.transaction_date = now()
			wallet_doc.total_value = ret_amt
			wallet_doc.transaction_type = "Pay"
			wallet_doc.is_settlement_paid = 1
			wallet_doc.amount = ret_amt
			wallet_doc.status = "Credited"
			wallet_doc.notes = "Against Return Request: "+self.name
			wallet_doc.flags.ignore_permissions = True
			wallet_doc.submit()

	def before_cancel(self):	
		if self.docstatus==2:
			self.status="Cancelled"

	def on_submit(self):
		for item in self.items:
			quantity = frappe.db.get_value("Product", item.product,"stock")
			updated_quantity = quantity + item.quantity
			frappe.log_error("updated_quantity",updated_quantity)
			frappe.db.set_value(
									"Product",
									item.product,
									"stock",
									updated_quantity
								)
			frappe.db.commit()
		
		# order_settings = get_settings("Order Settings")
		# if order_settings.enable_refund_option == 1:
		# 	doc = make_payment(self.order_id)
		# 	doc.insert(ignore_permissions = True)
			
def make_payment(source_name = None, order = None, mode_of_payment = None, amount = None):
	try:
		frappe.log_error("source_name",source_name)
		default_currency = get_settings('Catalog Settings')
		if source_name:
			source = frappe.get_all("Order",
								fields=["name","outstanding_amount","total_amount","customer_name","customer",
										"customer_type"],
								filters={"name":source_name})[0]
		frappe.log_error("source",source)
		if order:
			source = frappe.get_all("Order",fields=["*"],filters={"name":order})[0]
		
		total = source.total_amount
		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Receive" if flt(source.outstanding_amount) > flt(0) else "Pay"
		
		from go1_commerce.accounts.api import payment_type_check,check_MOP_and_amount
		payment_type_check(pe, source_name)
		pe.posting_date = nowdate()
		paid_amount = check_MOP_and_amount(pe,mode_of_payment, source, amount, total)


		pe.allocate_payment_amount = 1
		payment_type = 'received from'
		if pe.payment_type == 'Pay':
			payment_type = 'paid to'
		pe.remarks = 'Amount {0} {1} {2} {3}'.format(default_currency.default_currency,
														pe.paid_amount,
														payment_type, pe.party)
		pe.append("references",{'reference_doctype':"Order",
								'reference_name': source.name,
								"bill_no": "",
								"due_date": source.order_date,
								'total_amount': abs(total),
								'outstanding_amount': 0,
								'allocated_amount': paid_amount })
		pe.mode_of_payment = "Cash"
		pe.docstatus = 1
		if source_name:
			return pe
		else:
			pe.flags.ignore_permissions=True
			pe.submit()
			return pe.name
	except Exception:
		frappe.log_error(message = frappe.get_traceback(), title = "Error in accounts.api.make_payment")
		


def update_order_status(self):
	order_status = frappe.db.sql("""SELECT OI.name, OI.item
									FROM `tabOrder` O
									INNER JOIN `tabOrder Item` OI ON O.name = OI.parent
									WHERE OI.parenttype = "Order" 
										AND O.name = %(order_id)s 
										AND OI.item = %(item)s
									""", {'order_id': self.order_id, 'item': self.product}, as_dict=True)
	if order_status:
		frappe.db.sql(""" UPDATE `tabOrder Item`
							SET shipping_status = %(status)s
							WHERE name = %(name)s
							""", {'status': self.status, 'name': order_status[0]['name']})
		doc = frappe.get_doc('Order', self.order_id)
		doc.update_order_detail_html()



def make_customer_payment(doc):
	try:
		if doc.order_id:
			order_itemdoc = get_product_info(doc.product,doc.quantity,doc.order_id)
			if order_itemdoc:
				pay = frappe.new_doc('Customer Payments')
				pay.customer = doc.customer
				pay.payment_date = getdate(nowdate())
				pay.payment_type = "Cash"
				pay.amount = order_itemdoc['total']
				pay.payment_notes = "Paid Against Return Request: " + doc.name
				pay.save(ignore_permissions=True)
	except Exception as exc:
		frappe.log_error(message = frappe.get_traceback(),
						title = 'Error in doctype.return_request.make_customer_payment')
		raise exc



def get_product_info(product,qty,order):
	from go1_commerce.go1_commerce.v2.orders \
		import get_Products_Tax_Template
	order_itemdoc = frappe.db.sql(""" 	SELECT *
										FROM `tabOrder Item`
										WHERE parent = %s AND item = %s
										""", (order, product), as_dict=True)
	products = frappe.db.get_all('Product',fields=["*"],
								filters = {"is_active": 1,'name' : product},order_by = "stock desc")
	if products:
		for i in products:
			i.images = frappe.db.get_all('Product Image',fields = ["*"],filters = {"parent": i.name})
			Addons = frappe.db.get_all('Product Attribute Mapping',fields = ["*"],
										filters = {"parent":i.name})
			if Addons:
				for j in Addons:
					j.options = frappe.db.get_all('Product Attribute Option',fields = ["*"],
										filters = {"parent": i.name,"attribute": j.product_attribute})
				i.addons = Addons
			if i.name:
				if i.tax_category:
					tax_list = get_Products_Tax_Template(i.tax_category)
					if tax_list:
						tax_rates = tax_list[0].tax_rate
						tax_rate = 0
						for n in tax_rates:
							tax_rate += flt(n.rate)         
						product_tax = (flt(order_itemdoc[0].price * flt((tax_rate/100))))
				else:
					product_tax = 0
			productinfo={}
			productinfo['name'] = i.name
			productinfo['total_amount'] = flt(order_itemdoc[0].price) * flt(qty)
			productinfo['total_tax'] = flt(product_tax) * flt(qty)
			productinfo['total'] = flt(productinfo['total_tax']) + flt(productinfo['total_amount'])
	return productinfo


def get_query_condition(user):
	if not user: user = frappe.session.user
	from go1_commerce.go1_commerce.v2.orders \
		import get_city_based_role
	city_basedroles = get_city_based_role()
	if city_basedroles:
		employee = frappe.db.sql('''SELECT email_id, name, city 
									FROM `tabEmployee` 
									WHERE email_id = "{user}" 
										AND role IN ({role})
								'''.format(user = frappe.session.user, role = city_basedroles),
									as_dict = True)
		if employee:
			data = frappe.db.sql('''SELECT name 
									FROM `tabOrder` 
									WHERE city = "{city}"
								'''.format(city = employee[0].city), as_dict = 1)
			data_list = ",".join(['"' + x.name + '"' for x in data])
			return '(`tabReturn Request`.order_id in ({data_list}))'.format(data_list = data_list)



def get_returnorder_shipments(name):
	shipments = frappe.db.get_all("Return Shipment",filters = {"document_name":name},fields = ['*'])
	return shipments



def get_returnshipments(document_type, document_name):
	return frappe.db.get_value("Return Shipment", 
								{
									"document_type":document_type, 
									"document_name":document_name 
								}, 
								[
									'name', 'driver', 'tracking_number', 'tracking_link', 'shipped_date', 
									'delivered_date', 'status'
								],
								as_dict = True)
	


def get_return_order_items(returnId, fntype, doctype = "Order"):
	try:
		order = frappe.db.get_value("Return Request", returnId, 
								["name", "order_id", "product", "customer", "quantity"], as_dict=True)
		lists = []
		lists = frappe.db.sql('''SELECT I.item, I.item_name, R.quantity, I.price, I.amount, I.name 
								FROM `tabOrder Item` I 
								INNER JOIN `tabReturn Request` R ON R.order_id = I.parent 
								WHERE I.parent = %(orderId)s 
									AND I.item = %(product)s 
									AND R.name = %(returnId)s
							''',{
									"orderId":order.order_id, 
									"returnId":returnId, 
									"product": order.product
								}, as_dict=1)
		return lists	
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.vendor_orders.get_vendor_order_items") 



def get_attributes_combination_html(product, orderid, attribute):
	data= frappe.db.get_value("Product Variant Combination",{"attribute_id":attribute},"attribute_html")
	item_qty=frappe.db.get_value('Order Item',
								{'item':product, 'parent': orderid, 'attribute_ids':attribute},
								'quantity')
	return data, item_qty


def get_attributes_combination(product, orderid = None):
	order_item=frappe.db.get_all('Order Item',filters={'item':product, 'parent': orderid},fields=['attribute_ids'])
	orderattr = ",".join(['"' + x.attribute_ids + '"' for x in order_item if x.attribute_ids])
	cond = ""
	if orderattr:
		cond += " and attribute_id in ({orderattr})".format(orderattr = orderattr)
	combination=frappe.db.sql('''SELECT * from `tabProduct Variant Combination` where parent="{product}" {cond}'''.format(product=product, cond=cond), as_dict=True)
	frappe.log_error("combination", combination)
	for item in combination:
		if item and item.get('attributes_json'):
			variant = json.loads(item.get('attributes_json'))
			attribute_html = ""
			for obj in variant:
				if attribute_html:
					attribute_html +=", "
				option_value, attribute = frappe.db.get_value("Product Attribute Option", obj, 
														["option_value","attribute"])
				attribute_name = frappe.db.get_value("Product Attribute", attribute, "attribute_name")
				attribute_html += "<b>"+attribute_name+"</b>:"+option_value
			item["combination_txt"] = attribute_html
	item_qty = 0
	if len(combination)<=0:
		item_qty=frappe.db.get_value('Order Item',{'item':product, 'parent': orderid},'quantity')
	return combination,item_qty



def get_nextstatus(next_status_level):
	next_status=frappe.db.get_all('Return Request Status',fields=["name", "status_level"],
										filters={'status_level':next_status_level})
	return next_status



def get_eliglible_orders(doctype, txt, searchfield, start, page_len, filters):
	try:
		if not txt:
			txt = ""
		condition = ""
		wherecondition = ""
		txtcondition =""
		if filters.get('return_type') == "Return":
			condition += " INNER JOIN `tabReturn Policy` R ON R.name=P.return_policy "
			wherecondition += " AND R.eligible_for_return = 1"
		if filters.get('return_type') == "Replacement":
			condition += " INNER JOIN `tabReplacement Policy` R ON R.name=P.replacement_name "
			wherecondition += " AND R.eligible_for_replacement = 1 "
		if txt:
			txtcondition += ' AND (OI.parent like %(txt)s)'
		query = f'''SELECT O.name 
					FROM `tabOrder Item` OI 
					INNER JOIN `tabOrder` O ON O.name = OI.parent
					INNER JOIN `tabProduct` P ON P.name = OI.item 
					{condition} 
					WHERE 
						OI.return_created = 0 AND O.payment_status = 'Paid' 
						AND (O.status='Delivered' OR O.status = 'Completed')
						{wherecondition}
						{txtcondition} 
						GROUP BY OI.parent HAVING COUNT(OI.name) > 0'''
		frappe.log_error("return_query",query)
		order_list = frappe.db.sql(query,{'txt':'%'+txt+'%'})
		frappe.log_error("order_list",order_list)
		if order_list:
			return order_list
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.return_request.get_eliglible_orders") 



def get_order_items(doctype, txt, searchfield, start, page_len, filters):
	try:
		condition = ""
		wherecondition = ""
		txtcondition =""
		orderid=filters.get('order_id')
		if filters.get('return_type') == "Return":
			condition += " INNER JOIN `tabReturn Policy` R ON R.name=P.return_policy "
			wherecondition += " AND R.eligible_for_return = 1"
		if filters.get('return_type') == "Replacement":
			condition += " INNER JOIN `tabReplacement Policy` R ON R.name=P.replacement_name "
			wherecondition += " AND R.eligible_for_replacement=1 "
		if txt:
			txtcondition += " AND (O.item like %(txt)s OR O.item_name like %(txt)s OR O.name like %(txt)s)"
		query = f""" SELECT O.name,
							(CONCAT(O.item,"<br/>",O.item_name,IFNULL(O.attribute_description,''))) item_name,
							(CONCAT("<br/>SKU:",O.item_sku)) AS item_sku 
					FROM `tabOrder Item` O INNER JOIN `tabProduct` P ON P.name=O.item {condition} 
					WHERE 
						O.return_created = 0
						AND O.parent = '{orderid}' {wherecondition} {txtcondition} 
						GROUP BY O.attribute_ids,O.item """
		return frappe.db.sql(query,{'txt':'%'+txt+'%'})
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.return_request.get_order_items") 



def get_return_order_items(order_id, return_type, return_created):
	try:
		condition = ""
		wherecondition = ""
		txtcondition =""
		if return_type == "Return":
			condition += " INNER JOIN `tabReturn Policy` R ON R.name = P.return_policy "
			wherecondition += " AND R.eligible_for_return = 1"
		if return_type == "Replacement":
			condition += " INNER JOIN `tabReplacement Policy` R ON R.name = P.replacement_name "
			wherecondition += " AND R.eligible_for_replacement = 1 "
		query = f''' SELECT O.name, O.item,
							NVL(CONCAT("<br/>Name:",IFNULL(O.item_name,''),IFNULL(O.attribute_description,'')),'') item_name, 
							NVL(CONCAT("<br/>SKU:",O.item_sku),'') AS item_sku 
					FROM `tabOrder Item` O INNER JOIN `tabProduct` P ON P.name = O.item {condition} 
					WHERE 
						O.return_created = 0
						AND O.parent="{order_id}" {wherecondition} {txtcondition} 
						GROUP BY O.attribute_ids,O.item'''
		return frappe.db.sql(query,as_dict=1)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error in doctype.return_request.get_return_order_items") 



def get_order_item_info(order_item):
	try:
		query = f""" SELECT 
						O.customer,O.customer_email,O.customer_name,
						OI.item,OI.item_name,OI.attribute_description,OI.attribute_ids,OI.quantity 
					  FROM `tabOrder Item` OI 
						INNER JOIN `tabOrder` O ON OI.parent = O.name 
					  WHERE OI.name = '{order_item}' """
		resp__ = frappe.db.sql(query , as_dict = 1)
		if resp__:
			frappe.response.status = 'success'
			frappe.response.message = resp__ [0]
		else:
			frappe.response.status = 'failed'
			frappe.response.message = f'Product details not found..!'	
	except Exception:
		frappe.response.status = 'failed'
		frappe.response.message = f'Something went wrong not able to fetch <b>Product</b> details..!'
		frappe.log_error(title='Error in doctype.return_request.get_order_item_info',
							message = frappe.get_traceback())