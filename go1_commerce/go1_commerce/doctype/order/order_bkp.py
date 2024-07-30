# -*- coding: utf-8 -*-
# Copyright (c) 2018 info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json, math, os
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.core.doctype.domain_settings.domain_settings import get_active_domains
from frappe.utils import flt, comma_or, nowdate, getdate, now, get_datetime, to_timedelta, touch_file
from datetime import datetime, timedelta
from go1_commerce.utils.setup import get_settings_from_domain, get_settings_value_from_domain, get_doc_versions
from go1_commerce.go1_commerce.api import update_status, get_today_date
from go1_commerce.go1_commerce.doctype.customers.customers import update_customer_preference_from_order
from go1_commerce.go1_commerce.api import node_cancel_order, node_unassigned_driver_order
from frappe.desk.form.linked_with import get_linked_docs, get_linked_doctypes

whitelisted_globals = {
	"int": int,
	"float": float,
	"long": int,
	"round": round,
	"date": datetime.date,
	"getdate": getdate,
	"str":str,
	"math": math
}

class Order(Document):
	def onload(self):
		pass

	def on_update(self):		
		if self.order_item:
			from go1_commerce.go1_commerce.doctype.discounts.discounts import check_product_discounts
			total_weight = 0
			for item in self.order_item:
				total_weight += flt(item.weight) if item.weight else 0
			check_product_discounts(self.order_item, self.customer, self.shipping_method, self.payment_method, order=self.name,total_weight=total_weight)
		
		if self.outstanding_amount==0:
			frappe.db.set_value("Order", self.name, "payment_status", "Paid")
		self.update_order_detail_html()
		if check_domain("restaurant") and self.docstatus == 0:
			if self.business and self.order_time != "ASAP":
				business_info = frappe.get_doc("Business",self.business)
				today_date = get_today_date(business_info.time_zone, True)
				from go1_commerce.go1_commerce.api import check_business_closed
				restaurant_resp = check_business_closed(self.business,business_info.time_zone,getdate(today_date), today_date.strftime('%I:%M %p'), False, True,self.shipping_method_name)
				if restaurant_resp:
					if restaurant_resp.get("closed") == 1:
						frappe.db.set_value('Order', self.name, 'restaurant_closed', 1)
						frappe.db.set_value('Order', self.name, 'restaurant_next_available', restaurant_resp.get("next_available_at").replace("Opens at",""))
						frappe.db.set_value('Order', self.name, 'preorder_email', 1)
			
	def validate(self):
		self.set_customer_info()		
		self.maintain_history()	
		catalog_settings = get_settings_from_domain('Catalog Settings')
		if not self.currency and catalog_settings.default_currency:
			self.currency = catalog_settings.default_currency
		self.update_order()
		
	def update_order(self):		
		catalog_settings = get_settings_from_domain('Catalog Settings')
		order_settings = get_settings_from_domain('Order Settings')
		tax = subtotal = 0
		if self.order_item:		
			for item in self.order_item:
				if (item.order_item_type and item.item) and not item.item_name:
					selected_field = frappe.db.get_all('Party Name List',fields=['party_name_field'],filters={'parent':'Party Settings','party_type':item.order_item_type})
					if selected_field:
						res = frappe.db.get_value(item.order_item_type,item.item,selected_field[0].party_name_field)
						if self.docstatus==0:
							item.item_name = res
						else:
							frappe.db.set_value(item.doctype,item.name,'item_name',res)
					else:
						item.item_name = ""
				if item.order_item_type == 'Product':
					business = frappe.db.get_value('Product',item.item,'restaurant')
					item_sku = frappe.db.get_value('Product',item.item,'sku')
					item_weight = frappe.db.get_value('Product',item.item,'weight')
					if item_weight and int(item_weight) > 0:
						weight = item_weight
					else:
						weight = 0
					
					if self.docstatus==0:
						item.business = business
						item.item_sku = item_sku
					
					else:
						frappe.db.set_value(item.doctype,item.name,'business',business)
						frappe.db.set_value(item.doctype,item.name,'item_sku',item_sku)
						
					attr_image =''
					if item.attribute_ids:
						attr_ids = item.attribute_ids.split('\n')
						id_list = []
						for i in attr_ids:
							if i: id_list.append(i)
						ids = ",".join(['"' + x + '"' for x in id_list])
						options = frappe.db.sql('''select * from `tabProduct Attribute Option` where parent = %(parent)s and name in ({0})'''.format(ids),{'parent':item.item},as_dict = 1)				
						title = ''
						for op in options:
							if op.image_list:
								images = json.loads(op.image_list)
								if len(images) > 0:
									images = sorted(images, key=lambda x: x.get('is_primary'), reverse=True)
									attr_image = images[0].get('thumbnail')
							if op.product_title and op.product_title not in ['', '-']:
								title = op.product_title
						if title != '' and item.item_name != title:
							item.item_name = title
					result = frappe.db.sql('''select cart_thumbnail,list_image from `tabProduct Image` where parent=%(product)s order by is_primary desc limit 1''',{'product':item.item},as_dict=1)
					if attr_image:
						if self.docstatus==0:
							item.item_image = attr_image
						else:
							frappe.db.set_value(item.doctype,item.name,'item_image',attr_image)
					elif result and result[0].cart_thumbnail:
						if self.docstatus==0:
							item.item_image = result[0].cart_thumbnail
						else:
							frappe.db.set_value(item.doctype,item.name,'item_image',result[0].cart_thumbnail)
				else:
					if frappe.db.get_value("DocField", {"parent": item.order_item_type,"fieldname": "business"}): #by siva
						item.business = frappe.db.get_value(item.order_item_type,item.item,'business')
				
				if not item.is_free_item:
					total = 0
					amount = 0
					if order_settings.allow_admin_to_edit_order == 1 and order_settings.price_calculated_based_on_weight == 1:
						
						actual_weight = item.weight
						unitprice = flt(item.base_price)*flt(actual_weight)
						item.price = unitprice
						if item.weight == 1:
							amount = flt(item.price) * int(item.quantity)
						else:
							amount = unitprice
						item.amount = amount
						
					if self.docstatus==1:
						frappe.db.set_value(item.doctype,item.name,'amount',item.amount)
					total += flt(item.amount) if item.amount else 0
					if item.shipping_charges:
						total = flt(total) + flt(item.shipping_charges)
					if not catalog_settings.included_tax:
						total += flt(item.tax) if item.tax else 0
					if item.d_amount:
						total = flt(total) - flt(item.d_amount)
					if self.docstatus==0:
						item.t_amount = total
					else:
						frappe.db.set_value(item.doctype,item.name,'t_amount',total)
					tax = tax + (item.tax if item.tax else 0)
					subtotal = subtotal + flt(item.amount)
		
		if self.docstatus==0:
			self.total_tax_amount = tax
		else:
			self.total_tax_amount = tax
			frappe.db.set_value(self.doctype,self.name,'total_tax_amount',tax)
		if self.shipping_method:
			shipping_method_name = frappe.db.get_value('Shipping Method', self.shipping_method, 'shipping_method_name')
			self.shipping_method_name = shipping_method_name 
			frappe.db.set_value(self.doctype,self.name,'shipping_method_name',shipping_method_name)
		if self.payment_method:
			if frappe.db.exists("Payment Method",self.payment_method):
				payment_method_info = frappe.get_doc('Payment Method',self.payment_method)
				if payment_method_info:
					self.payment_method_name = payment_method_info.payment_method
					if payment_method_info.display_name:
						self.payment_method_name = payment_method_info.display_name
					if payment_method_info.display_text:
						payment_method_info.display_text = json.loads(payment_method_info.display_text)
						for shipping_type in payment_method_info.display_text:
							if shipping_type.get("shipping_method_name") == self.shipping_method_name:
								self.payment_method_name = shipping_type.get("display_text")
			if not self.payment_method_name and frappe.db.exists("Business Payment Gateway Settings",self.payment_method):
				payment_method_info = frappe.get_doc('Business Payment Gateway Settings',self.payment_method)
				if payment_method_info:
					self.payment_method_name = payment_method_info.gateway_type
					if payment_method_info.display_text:
						payment_method_info.display_text = json.loads(payment_method_info.display_text)
						for shipping_type in payment_method_info.display_text:
							if shipping_type.get("shipping_method_name") == self.shipping_method_name:
								self.payment_method_name = shipping_type.get("display_text")
			frappe.db.set_value(self.doctype,self.name,'payment_method_name',self.payment_method_name)
		
		if self.tax_breakup and self.tax_breakup.find(' - shipping') != -1:
			delivery_tax = self.tax_breakup.split('\n')
			break_up = ''
			for t in delivery_tax:
				if t and t.find(' - shipping') == -1:
					break_up = break_up + t + '\n'
			self.tax_breakup = break_up
			if self.tax_json:
				tax_json = json.loads(self.tax_json)
				new_json = []
				for t in tax_json:
					if not t.get('is_shipping'):
						new_json.append(t)
				self.tax_json = json.dumps(new_json)
		shipping_charge_tax = self.shipping_charge_tax()
	
		self.order_subtotal = subtotal
		if self.docstatus == 1:
			frappe.db.set_value(self.doctype,self.name,'order_subtotal',subtotal)
		
		tax_template = None
		tax_val=0
		if self.tax_breakup:
			tax_parts = self.tax_breakup.split('\n')
			for t in tax_parts:
				splits = t.split(' - ')
				if len(splits) > 3 and splits[3] and splits[3] == 'Excl. Tax':
					tax_val = tax_val + float(splits[2])	
				if len(splits) > 3 and splits[3] and splits[3] == 'Incl. Tax':
					tax_val = tax_val + float(splits[2])		
		if not self.discount:
			self.discount = 0
		new_disount = self.calculate_discount(order_settings)
		if self.discount and self.discount > 0:
			temp_discount = str(self.discount).split('.')
			self.discount = math.ceil(self.discount * 100) / 100
			
			self.total_tax_amount = tax_val
			frappe.db.set_value(self.doctype,self.name,'total_tax_amount',tax_val)
		else:
			tax_val = math.ceil(self.total_tax_amount * 100) / 100
		frappe.db.set_value(self.doctype,self.name,'total_tax_amount',math.ceil(self.total_tax_amount * 100) / 100)
		if not catalog_settings.included_tax:
			total_amount = self.order_subtotal - self.discount + self.shipping_charges + tax_val + float(self.pickup_charge)
		else:
			total_amount = self.order_subtotal - self.discount + self.shipping_charges + float(self.pickup_charge)
		self.total_amount = total_amount
		if self.gift_card_amount:
			self.total_amount = self.total_amount - flt(self.gift_card_amount)
		self.order_subtotal_after_discount = float(self.order_subtotal) - float(self.discount)
		if self.docstatus == 1:
			frappe.db.set_value(self.doctype,self.name,'order_subtotal_after_discount',self.order_subtotal_after_discount)
		if self.tip_amount and float(self.tip_amount) > 0:
			self.total_amount = self.total_amount + float(self.tip_amount)
		if not self.payment_gateway_charges:
			self.payment_charges()
		
		if self.checkout_attributes:
			for attr in self.checkout_attributes:
				self.total_amount += flt(attr.price_adjustment)
		self.calculate_commission()
		if not self.barcode:
			self.check_barcode()
		if not self.qrcode:
			self.check_qrcode()		
		
		if self.business and not self.business_email:
			self.business_email = frappe.db.get_value('Business',self.business,'contact_email')
		self.total_amount = math.ceil(self.total_amount * 100) / 100
		if self.docstatus == 1:
			frappe.db.set_value(self.doctype,self.name,'total_amount',self.total_amount)
		if self.payment_status == "Paid":
			update_giftcard_payments(self.name,self.transaction_id)
			if self.giftcard_coupon_code:
				update_giftcard_status(self)
		if self.docstatus == 0:
			if self.outstanding_amount == 0:
				frappe.db.sql("""UPDATE `tabOrder` SET docstatus = 1 where name = %(orderid)s""",{"orderid":self.name})
				frappe.db.commit()
		self.check_outstanding_balance(self.total_amount,new_disount)
		
		self.update_order_detail_html()
		

	def calculate_discount(self, order_settings):
		
		new_disount = self.discount
		allowed_discount = 1
		customer_orders = frappe.db.get_all("Order",filters={"docstatus":1,"customer":self.customer,"is_recurring_order":1,"name":("!=",self.name)})
		if not customer_orders:
			allowed_discount = 0
		if self.order_item and len(self.order_item) > 0 and order_settings.allow_admin_to_edit_order == 1 and self.is_custom_discount == 0 and allowed_discount == 1:
			from go1_commerce.go1_commerce.doctype.discounts.discounts import get_order_subtotal_discount
			from go1_commerce.go1_commerce.api import validate_coupon
			total_weight = 0
			for item in self.order_item:
				total_weight += flt(item.weight) if item.weight else 0
			check_subtotal_discount = 1
			if self.discount_coupon:
				discount_response = get_coupon_discount(self.name,self.order_subtotal,self.discount_coupon)
				if discount_response:
					if discount_response.get("status")!="failed":
						check_subtotal_discount = 0
						if discount_response.get("new_order_item"):
							child = discount_response.get("new_order_item")
							self.append("order_item", {"amount":child.amount, "is_free_item":child.is_free_item,"is_gift_card":child.is_gift_card,"is_rewarded":child.is_rewarded,
									"order_item_type":child.order_item_type, "is_scanned":child.is_scanned, "item_name":child.item_name, "item_image":child.item_image, "ordered_weight":child.ordered_weight,
									"price": child.price, "quantity":child.quantity, "return_created":child.return_created, "shipping_status":child.shipping_status, "shipping_charges":child.shipping_charges,
									"t_amount":child.t_amount, "tax":child.tax, "weight":child.weight, "discount_coupon":child.discount_coupon})
					else:
						self.discount_coupon = None
						frappe.db.set_value('Order', self.name, 'discount_coupon', None)
						self.discount =  0
						new_disount = 0
						frappe.db.set_value(self.doctype,self.name,'discount',0)
			if check_subtotal_discount:
				discount_response = get_order_subtotal_discount(self.order_subtotal, self.customer, self.order_item, total_weight, self.is_recurring_order,self.shipping_method, self.payment_method, self.shipping_charges)
				if self.name and len(discount_response.get('products_list'))>0:
					check = next((x for x in self.order_item if (x.is_free_item == 1 and x.discount == discount_response.get('discount_rule'))), None)
					if not check:
						for child in discount_response.get("products_list"):
							product = frappe.get_doc("Product", child.get('product'))
							new_order_item={}
							new_order_item['amount'] = (product.price*child.get('quantity'))
							new_order_item['is_free_item'] = 1
							new_order_item['is_gift_card'] = 0
							new_order_item['is_rewarded'] = 0
							new_order_item['order_item_type'] = "Product"
							new_order_item['is_scanned'] = 0
							new_order_item['item_name'] = product.item
							new_order_item['item'] = child.get('product')
							new_order_item['item_image'] = product.image
							new_order_item['ordered_weight'] = product.weight
							new_order_item['price'] = product.price
							new_order_item['quantity'] = child.get('quantity')
							new_order_item['return_created'] = 0
							new_order_item['shipping_status'] = "Pending"
							new_order_item['shipping_charges'] = 0
							new_order_item['t_amount'] = (product.price*child.get('quantity'))
							new_order_item['tax'] = 0
							new_order_item['weight'] = product.weight
							self.append("order_item", {"item":new_order_item['item'], "amount":new_order_item['amount'], "is_free_item":new_order_item['is_free_item'],"is_gift_card":new_order_item['is_gift_card'],"is_rewarded":new_order_item['is_rewarded'],
									"order_item_type":new_order_item['order_item_type'], "is_scanned":new_order_item['is_scanned'], "item_name":new_order_item['item_name'], "item_image":new_order_item['item_image'], "ordered_weight":new_order_item['ordered_weight'],
									"price": new_order_item['price'], "quantity":new_order_item['quantity'], "return_created":new_order_item['return_created'], "shipping_status":new_order_item['shipping_status'], "shipping_charges":new_order_item['shipping_charges'],
									"t_amount":new_order_item['t_amount'], "tax":new_order_item['tax'], "weight":new_order_item['weight']})
			if discount_response and discount_response.get('discount_amount'):
				self.discount = math.ceil(float(discount_response.get('discount_amount')) * 100) / 100
				new_disount = discount_response.get('discount_amount')
				if self.docstatus == 1:
					frappe.db.set_value(self.doctype, self.name, 'discount', self.discount)
			discount_history = frappe.db.get_all("Discount Usage History",filters={'order_id':self.name})
			for x in discount_history:
				frappe.db.sql('''DELETE FROM `tabDiscount Usage History` WHERE name=%(usage_name)s''',{'usage_name':x.name})
			if discount_response and discount_response.get('discount_amount'):
				from go1_commerce.go1_commerce.api import insert_discount_usage_history
				insert_discount_usage_history(self.name, self.customer, discount_response.get('discount_rule'))
			for x in self.order_item:
				if x.discount and x.is_free_item == 0:
					discount_usage_history = frappe.db.get_all("Discount Usage History",filters={"order_id":self.name},fields=['*'])
					if not discount_usage_history:
						from go1_commerce.go1_commerce.api import insert_discount_usage_history
						insert_discount_usage_history(self.name, self.customer, x.discount)

		return new_disount

	def set_customer_info(self):
		if not self.customer_type:
			self.customer_type = "Customers"
		if self.customer_type == "Customers" and not self.customer_name:
			if frappe.request and frappe.request.cookies.get('guest_customer_name'):
				self.customer_name = frappe.request.cookies.get('guest_customer_name')
			else:
				self.customer_name = frappe.db.get_value("Customers",self.customer,"full_name")
		if self.customer_type == "Business":
			self.customer_name = frappe.db.get_value(self.customer_type,self.customer,"restaurant_name")
		if self.customer and not self.customer_email and self.customer_type == "Customers":
			self.customer_email = frappe.db.get_value('Customers',self.customer,'email')
		if not self.phone:
			if frappe.request and frappe.request.cookies.get('guest_customer_phone'):
				self.customer_phone = frappe.request.cookies.get('guest_customer_phone')
		if self.customer and not self.phone and not self.shipping_phone and self.customer_type == "Customers":
			self.customer_phone = frappe.db.get_value('Customers', self.customer, 'phone')
			self.phone = frappe.db.get_value('Customers', self.customer, 'phone')


	def maintain_history(self):
		prev_state = self.pre_status
		cur_state = self.status
		if prev_state != cur_state:
			row = self.append('status_history', {})
			row.before_change = prev_state
			row.new_status = self.status
			row.updated_on = now()
			row.parent = self.name
			row.notes = "Order Placed"
			row.parentfield = "status_history"
			row.parenttype = "Order"
			self.pre_status=cur_state

	def update_status_history(self):
		prev_state = self.pre_status
		cur_state = self.status
		workflow = frappe.db.get_all('Workflow', filters={'is_active': 1, 'document_type': 'Order'})
		if workflow:
			cur_state = self.workflow_state
		if prev_state != cur_state and self.pre_status:
			items = frappe.new_doc("Status History")
			items.before_change= prev_state
			items.new_status= cur_state
			items.updated_on= now()
			items.parenttype="Order"
			items.parentfield="status_history"
			items.notes = "Order status changed to "+str(cur_state)
			items.parent=self.name
			items.save(ignore_permissions=True)
			frappe.db.commit()
		else:
			if self.pre_status:
				items = frappe.new_doc("Status History")
				items.before_change= prev_state
				items.new_status= cur_state
				items.updated_on= now()
				items.parenttype="Order"
				items.parentfield="status_history"
				items.notes = "Order updated"
				items.parent=self.name
				items.save(ignore_permissions=True)
				frappe.db.commit()
			else:
				items = frappe.new_doc("Status History")
				items.before_change= prev_state
				items.new_status= cur_state
				items.updated_on= now()
				items.parenttype="Order"
				items.parentfield="status_history"
				items.notes = "Order Placed"
				items.parent=self.name
				items.save(ignore_permissions=True)
				frappe.db.commit()
		frappe.db.set_value('Order', self.name, 'pre_status', cur_state)

	def payment_charges(self):
		if self.payment_method:
			if frappe.db.get_value('Payment Method', self.payment_method):
				payment = frappe.get_doc('Payment Method', self.payment_method)
				gateway_charges = 0
				if payment.use_additional_fee_percentage:
					gateway_charges = (flt(self.order_subtotal) - flt(self.discount) + flt(self.total_tax_amount) + flt(self.shipping_charges)) * flt(payment.additional_fee_percentage) / 100
				if payment.additional_charge:
					gateway_charges = flt(gateway_charges) + flt(payment.additional_charge)
				self.payment_gateway_charges = gateway_charges

	def check_outstanding_balance(self, total_amount,discount_new):
		paid_amount = 0
		outstanding_amount = round(flt(total_amount), 2)
		payment_reference = frappe.db.get_all('Payment Reference', filters={'reference_doctype': 'Order', 'reference_name': self.name, 'docstatus': 1}, fields=['allocated_amount'])
		if payment_reference:
			paid_amount = sum(round(flt(x.allocated_amount), 2) for x in payment_reference if x.allocated_amount > 0)
		discount_amt = 0
		
		if self.paid_using_wallet and self.paid_using_wallet > 0:
			paid_amount += round(flt(self.paid_using_wallet), 2)
			discount_amt += flt(self.paid_using_wallet)
		if "loyalty" in frappe.get_installed_apps() and self.get('loyalty_amount') and self.loyalty_amount > 0:
			paid_amount += round(flt(self.loyalty_amount), 2)
			discount_amt += flt(self.loyalty_amount)
		if paid_amount > 0 and self.total_amount >= paid_amount:
			outstanding_amount = flt(self.total_amount) - round(flt(paid_amount), 2)
		self.order_subtotal_after_discount = float(self.order_subtotal) - float(discount_new) - float(discount_amt)
		if flt(outstanding_amount) == flt(self.total_amount) and flt(outstanding_amount) > 0:
			if (self.payment_status == "Authorized") or (self.payment_status == 'Paid' and self.transaction_id):
				pass
			else:
				self.payment_status = 'Pending'
		elif flt(outstanding_amount) == flt(0):
			self.payment_status = 'Paid'
			if frappe.db.get_value(self.doctype, self.name, 'docstatus') == 0:
				frappe.db.set_value(self.doctype,self.name,'docstatus', 1)
				frappe.db.commit()

		else:
			self.payment_status = 'Partially Paid'
		self.outstanding_amount = outstanding_amount
		self.paid_amount = paid_amount
		if self.docstatus == 1:
			frappe.db.set_value(self.doctype,self.name,'outstanding_amount', outstanding_amount)
			frappe.db.set_value(self.doctype,self.name,'paid_amount', paid_amount)
			frappe.db.set_value(self.doctype,self.name,'payment_status', self.payment_status)
			frappe.db.commit()
		

	def shipping_charge_tax(self):
		tax_template = None
		tax = charge=0
		text = ''
		calculative_amount = self.shipping_charges
		catalog_settings = get_settings_from_domain('Catalog Settings')
		
		if catalog_settings.shipping_is_taxable and catalog_settings.shipping_tax_class:
			tax_template = catalog_settings.shipping_tax_class
			text = 'Shipping'
		tax_splitup = []
		if tax_template:
			tax_type = ''
			if catalog_settings.shipping_is_taxable:
				if catalog_settings.shipping_price_includes_tax:
					tax_type = "Incl. Tax"
				else:
					tax_type = "Excl. Tax"
			tax_info = frappe.get_doc('Product Tax Template', tax_template)
			for item in tax_info.tax_rates:
			
				
				if catalog_settings.shipping_price_includes_tax:
					if charge>0 :
						calculative_amount +=charge
					tax_val = float(calculative_amount) * item.rate / (100 + item.rate)
				else:
					tax_val = float(calculative_amount) * float(item.rate) / 100
				cur_tax = next((x for x in tax_splitup if x['type'] == item.tax),None)
				if cur_tax:
					for it in tax_splitup:
						if it['type'] == item.tax:
							it['amount'] = it['amount'] + tax_val
				else:
					tax_splitup.append({'type': item.tax,'rate': item.rate,'amount': tax_val, 'account': item.get('account_head'), 'tax_type': tax_type, 'is_shipping': 1})
				if catalog_settings.shipping_price_includes_tax==0:
					tax = float(tax) + float(tax_val)
				else:
					tax = float(tax)
			self.total_tax_amount = self.total_tax_amount + tax
			shipping = frappe._('{0}').format(text)
			if not self.tax_breakup: 
				self.tax_breakup = ''
			else:
				breakup = self.tax_breakup.split('\n')
				new_breakup = ''
				for br in breakup:
					part = br.split(' - ')
					if len(part) > 4 and part[4] == 'shipping':
						pass
					else:
						new_breakup += br + '\n'
				self.tax_breakup = new_breakup
			tax_json = json.loads(self.tax_json) if self.tax_json else []
			for x in tax_splitup:
				tax_json.append(x)
				self.tax_breakup += '{0} - {1}% - {2} - {3} - shipping\n'.format((x['type'] + '(' + shipping + ')'), str(x['rate']), str(x['amount']), tax_type)
			self.tax_json = json.dumps(tax_json)
			return tax
	

	def calculate_restaurant_charges(self, business):
		
		business_info = frappe.get_doc('Business',business)
		commission_type = gateway_fee_by = commission_percent = commission_amount = None
		driver_fee_type = driver_fee_by =  None
		driver_charges = self.driver_charges
		if not driver_charges:
			driver_charges = 0
		vendor_discount = self.vendor_discount
		if not vendor_discount:
			vendor_discount = 0
		actual_shipping_charges = self.actual_shipping_charges
		if not actual_shipping_charges:
			actual_shipping_charges = 0
		party_payment_structure = frappe.db.sql('''select name, party_type from `tabParty Payment Structure` where reference_doctype = "Order" order by field (party_type, 'Service Provider', 'Driver', 'Business')''', as_dict=1)
		
		if self.shipping_method_name == "Delivery":
			if business_info.is_percentage_delivery:
				commission_type = 'Percentage'
				commission_percent = business_info.commision_percentage_delivery
			else:
				commission_type = 'Amount'
				commission_amount = business_info.commission_amount_delivery
		else:
			if business_info.is_percentage:
				commission_type = 'Percentage'
				commission_percent = business_info.commision_percentage
			else:
				commission_type = 'Amount'
				commission_amount = business_info.commission_amount
		gateway_fee_by = business_info.payment_gateway_charges_paid_by if self.shipping_method_name == "Pickup" else business_info.payment_gateway_charges_paid_by_delivery
		driver_fee_by = business_info.driver_fee
		
		doc = self.__dict__
		doc['commission_type'] = commission_type
		doc['commission_percentage'] = commission_percent
		doc['commission_amount'] = commission_amount
		doc['gateway_fee_by'] = gateway_fee_by
		doc['driver_fee_by'] = driver_fee_by
		doc['driver_fee_by'] = driver_fee_by
		doc['driver_charges'] = driver_charges
		doc['vendor_discount'] = vendor_discount
		doc['actual_shipping_charges'] = actual_shipping_charges

		
		if party_payment_structure:
			for item in party_payment_structure:
				formulas = frappe.db.get_all('Party Payment Condition', fields=['*'], filters={'parent': item.name}, order_by='idx')
				amount = 0
				for formula in formulas:
					if formula.condition:
						if not frappe.safe_eval(formula.condition, None, doc):
							continue
					if formula.is_formula_based:
						amount = frappe.safe_eval(formula.formula, whitelisted_globals, doc)
					else:
						amount = formula.amount
					amount = round(amount, 2)
					break

				if item.party_type == 'Service Provider':
					self.commission_amt = amount
					doc['commission_amt'] = amount
					if self.docstatus == 1:
						frappe.db.set_value('Order', self.name, 'commission_amt', amount)
				elif item.party_type == 'Business':
					self.total_amount_for_vendor = amount
					doc['total_amount_for_vendor'] = amount
					if self.docstatus == 1:
						if flt(amount) > 0:
							frappe.db.set_value('Order', self.name, 'total_amount_for_vendor', math.ceil(float(amount) * 100) / 100)
				elif item.party_type == 'Driver' and (self.shipping_method_name == 'Delivery' or self.driver):
					self.total_driver_charges = amount
					doc['total_driver_charges'] = amount
					if self.docstatus == 1:
						frappe.db.set_value('Order', self.name, 'total_driver_charges', amount)

	def calculate_multivendor_charges(self, business=None):
		'''
		to calculate customer commision for reseller
		'''
		party_payment_structure = frappe.db.sql('''select name, party_type from `tabParty Payment Structure` where reference_doctype = "Order" order by field (party_type, 'Customers')''', as_dict=1)
		
		doc = self.__dict__
		if party_payment_structure:
			for item in party_payment_structure:
				if item.party_type=="Customers":
					formulas = frappe.db.get_all('Party Payment Condition', fields=['*'], filters={'parent': item.name}, order_by='idx')
					amount = 0
					for formula in formulas:
						if formula.condition:
							if not frappe.safe_eval(formula.condition, None, doc):
								continue
						if formula.is_formula_based:
							amount = frappe.safe_eval(formula.formula, whitelisted_globals, doc)
						else:
							amount = formula.amount
						amount = round(amount, 2)
						break
					self.customer_commission = amount
					doc['customer_commission'] = amount
					if self.docstatus == 1:
						frappe.db.set_value('Order', self.name, 'customer_commission', amount)
				
	def get_order_timeslot(self):
		if self.business:
			business = frappe.get_doc('Business',self.business)
			if self.order_time != 'ASAP':
				time_diff = business.order_online_time_difference_delivery
				if self.shipping_method_name == 'Pickup':
					time_diff = business.order_online_time_difference_pickup
				if time_diff and int(time_diff) > 0:
					dtfmt = '%Y-%m-%d %H:%M:%S'
					time = frappe.utils.to_timedelta(self.order_time)
					order_date = frappe.utils.get_datetime(str(self.order_date) + ' ' + str(time))
					order_date_range = order_date + timedelta(minutes=int(time_diff))
					order_date_range = order_date_range.strftime('%I:%M %p')
					return order_date_range

	def get_delivery_timeslot(self, name):
		if self.name:
			delivery_slot = []
			check_delivery_slot = frappe.db.get_all('Order Delivery Slot', filters={'order': name}, fields=['order_date', 'from_time', 'to_time', 'product_category'])
			if check_delivery_slot:
				for deli_slot in check_delivery_slot:
					category = ''
					if deli_slot.product_category:
						category = frappe.get_value('Product Category', deli_slot.product_category, 'category_name')
					from_time = datetime.strptime(str(deli_slot.from_time), '%H:%M:%S').time()
					to_time = datetime.strptime(str(deli_slot.to_time), '%H:%M:%S').time()
					delivery_slot.append({
						'delivery_date': deli_slot.order_date.strftime('%b %d, %Y'),
						'from_time': from_time.strftime('%I:%M %p'),
						'to_time': to_time.strftime('%I:%M %p'),
						'category': category
						})
			return delivery_slot

	def check_barcode(self):
		enable_barcode = get_settings_value_from_domain('Order Settings', 'generate_barcode_for_order')
		if enable_barcode:
			import barcode
			from barcode.writer import ImageWriter
			EAN = barcode.get_barcode_class('code128')
			ean = EAN(self.name, writer=ImageWriter())
			fullname = ean.save(self.name)
			filename = randomStringDigits(18)
			path = 'public/files/{filename}.png'.format(filename=filename)
			touch_file(os.path.join(frappe.get_site_path(), path))
			f = open(os.path.join(frappe.get_site_path(), path), 'wb')
			ean.write(f)
			self.barcode = "/files/" + filename + ".png"

	def check_qrcode(self):
		try:
			enable_qr_code=get_settings_value_from_domain('Order Settings', 'generate_qrcode_for_order')
			if enable_qr_code:
				import qrcode
				from qrcode.image.pure import PymagingImage
				qr = qrcode.QRCode(
					version=1,
					error_correction=qrcode.constants.ERROR_CORRECT_L,
					box_size=10,
					border=4,
				)
				qr.add_data(self.name)
				qr.make(fit=True)

				img = qr.make_image(fill_color="black", back_color="white")
				filename = randomStringDigits(18)
				path = 'public/files/{filename}.png'.format(filename=filename)
				touch_file(os.path.join(frappe.get_site_path(),path))
				img.save(os.path.join(frappe.get_site_path(),path))
				self.qrcode = "/files/" + filename + ".png"
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ecommerce_bussiness_store.ecommerce_bussiness_store.order.check_qrcode")	

	def make_vendor_orders(self):
		business_list = frappe.db.sql('''select distinct business from `tabOrder Item` where parent=%(name)s''',{'name':self.name},as_dict=1)
		target_doc = None
		if business_list:
			for item in business_list:
				doc = frappe.new_doc('Vendor Orders')
				order_items = list(filter(lambda x: x.business == item.business, self.order_item))
				doc = get_mapped_doc("Order", self.name,	{
					"Order": {
						"doctype": "Vendor Orders"
					},
					"Order Item": {
						"doctype": "Order Item",
						"condition": lambda doc: (doc.business==item.business)
					}
				}, target_doc, ignore_permissions=True)
				doc.naming_series = 'VO-'
				doc.business = item.business
				if self.docstatus == 1:
					doc.docstatus = 1
				doc.save(ignore_permissions=True)

	def before_cancel(self):
		frappe.db.set_value("Order", self.name, "status", "Cancelled")
		self.status = "Cancelled"
	
	def on_cancel(self):
		self.update_order_detail_html()
		self.update_items_stock()
		
	
	def update_items_stock(self):
		from go1_commerce.go1_commerce.api import get_attributes_json
		try:
			if self.name:
				items=frappe.db.sql('''select o.*,p.inventory_method,p.stock from `tabOrder Item` o inner join `tabProduct` p on o.item = p.name where o.parent = %(parent)s order by o.idx''',{'parent':self.name},as_dict = 1)
				if items:
					for item in items:
						if item.inventory_method=="Track Inventory":
							stock = int(item.stock) + int(item.quantity)
							frappe.db.set_value('Product', item.item, 'stock', stock)
						elif item.inventory_method=="Track Inventory By Product Attributes":
							attribute_id = get_attributes_json(item.attribute_ids)
							check_data = frappe.db.get_all('Product Variant Combination', filters={'parent': item.item, 'attributes_json': attribute_id}, fields=['stock', 'price', 'weight', 'name', 'sku', 'role_based_pricing'])
							if check_data:
								stock = int(check_data[0].stock) + int(item.quantity)
								frappe.db.set_value('Product Variant Combination', check_data[0].name, 'stock', stock)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ecommerce_bussiness_store.ecommerce_bussiness_store.order.on_cancel")
	
	def on_submit(self):
		order_settings = get_settings_from_domain('Order Settings')
		invoice_state = "Placed"
		
		invoice_creation_states = frappe.db.get_all("Auto Invoice Creation Status",fields=['status'],filters={"parent":order_settings.name})
		if self.status in invoice_creation_states and order_settings.enable_invoice==1 and order_settings.automate_invoice_creation==1:
			tran_name = frappe.db.get_value("Sales Invoice",{"reference":self.name})
			if not tran_name:
				make_invoice(self.name)
		if self.status == 'Completed':
			w_settings=frappe.get_single('Wallet Settings')
			if w_settings.enable_wallet==1 or w_settings.enable_customer_wallet==1:
				update_wallet_entry(self)	
		self.adjust_product_inventory()
		
		if self.customer and self.customer_type=="Customers":
			if self.status != "Cancelled":
				self.order_reward()	
		
		
		if self.status not in ['Completed', 'Cancelled']:
			self.check_vendor_notification()
			

		frappe.enqueue('go1_commerce.go1_commerce.doctype.order.order.clear_guest_user_details', order_id=self.name)
		if self.status == 'Cancelled':
			self.cancel_order_detail()
		discount_usage_history = frappe.db.get_all("Discount Usage History",filters={"order_id":self.name},fields=['*'])
		frappe.log_error(discount_usage_history,"on submit")
		
		self.update_shipmentbag()
		frappe.publish_realtime('update_menu', {'docname': self.name,'doctype':'Order'})
		
	def update_order_detail_html(self):
		template = generate_order_detail_template(self.name)
		frappe.db.set_value('Order', self.name, 'order_info', template)

	def update_shipmentbag(self):
		shopping_settings = get_settings_from_domain('Shopping Cart Settings')
		if self.is_shipment_bag_item==1 and shopping_settings.enable_shipment_bag==1 and self.customer_type=="Customers":
			if frappe.db.exists("Shipment Bag",{"customer": self.customer, "is_paid":0}):
				data_name = frappe.db.get_value("Shipment Bag",{"customer": self.customer, "is_paid":0})
				shipment= frappe.get_doc("Shipment Bag", data_name)
				shipment.append('items', {"order_id":self.name, "shipping_charge": self.shipment_charge})
				shipment.save(ignore_permissions=True)
			else:
				shipment= frappe.new_doc("Shipment Bag")
				shipment.customer= self.customer
				if self.business:
					shipment.business= self.business
				shipment.customer_name= self.customer_name
				shipment.append('items', {"order_id":self.name, "shipping_charge": self.shipment_charge})
				shipment.insert(ignore_permissions=True)

	def order_reward(self):
		order_settings = get_settings_from_domain('Order Settings')
		reward=frappe.db.get_all('Reward Points Usage History',fields=['*'],filters={'customer_id':self.customer,'message':'Reward Point for Order '+self.name})
		if not reward:
			if order_settings.enabled:	
				if order_settings.point_for_purchases:
					result= frappe.get_doc({
						"doctype": "Reward Points Usage History",
						"customer_id":self.customer,
						"points":order_settings.point_for_purchases,
						"amount":0,
						"message": "Reward Point for Order "+self.name,
						"usage_order_id":self.name
						}).insert(ignore_permissions=True)

	def calculate_commission(self):
		domains_list = get_active_domains()
		commission = 0
		if "Restaurant" in domains_list:
			if self.business:
				self.calculate_restaurant_charges(self.business)
		else:
			self.calculate_multivendor_charges()
			for item in self.order_item:
				product_rate = frappe.db.get_value('Product',item.item,'commission_rate')
				if product_rate:
					commission = commission + (product_rate * item.t_amount / 100)
			self.commission_amt = commission
			if self.total_amount:
				self.total_amount_for_vendor = self.total_amount - commission
		
	def get_item_image(self, item_code):		
		result = frappe.db.sql('''select cart_thumbnail,list_image from `tabProduct Image` where parent=%(product)s order by is_primary desc limit 1''',{'product':item_code},as_dict=1)
		if result and result[0].cart_thumbnail:
			return result[0].cart_thumbnail
		elif result and result[0].list_image:
			return result[0].list_image
		else:
			default_image = get_settings_value_from_domain('Media Settings', 'default_image')
			if default_image:
				return default_image
			folder_path=''
			try:
				path = frappe.get_module_path("cms_website")
				if path:
					folder_path='cmswebsite'
			except Exception:
				try:
					path = frappe.get_module_path("restaurant_cms_website")
					if path:
						folder_path='restaurantcmswebsite'
				except Exception:
					path=None
			if folder_path:
				template='/assets/{path}/images/no-img-120.jpg'.format(path=folder_path)
				return template
		
	def adjust_product_inventory(self):		
		if self.order_item:
			for item in self.order_item:
				if item.order_item_type=='Product' and frappe.db.exists("Product", item.item):
					product_info=frappe.get_doc('Product',item.item)
					if product_info.inventory_method=='Track Inventory':
						if int(product_info.stock)>=int(item.quantity):
							product_info.stock=product_info.stock-item.quantity
							frappe.db.set_value('Product',product_info.name,'stock',product_info.stock)
						else:
							frappe.throw("Product stock quantity should be greater than item quantity.")
					elif product_info.inventory_method=='Track Inventory By Product Attributes':
						from go1_commerce.go1_commerce.api import get_attributes_json
						attribute_id = get_attributes_json(item.attribute_ids)
						check = next((x for x in product_info.variant_combination if x.attributes_json==attribute_id),None)
						if check:
							if check.stock > 0:
								if int(check.stock)>=int(item.quantity):
									check.stock = check.stock - float(item.quantity)
									frappe.db.set_value('Product Variant Combination', check.name, 'stock', check.stock)
								else:
									frappe.throw("Product stock quantity should be greater than item quantity.")
	
	def on_update_after_submit(self):
		self.update_status_history()
		self.update_order()
		order_settings = get_settings_from_domain('Order Settings', business=self.business)
		allow = False
		if self.get('__islocal') or self.get('__unsaved'):
			allow = True
		invoice_creation_states = frappe.db.get_all("Auto Invoice Creation Status",fields=['status'],filters={"parent":order_settings.name})
		if self.status in invoice_creation_states and order_settings.enable_invoice==1 and order_settings.automate_invoice_creation==1:
			tran_name = frappe.db.get_value("Sales Invoice",{"reference":self.name})
			if not tran_name:
				make_invoice(self.name)
		if self.status == 'Cancelled':
			self.cancel_order_detail()
			self.update_items_stock()
			
		self.update_order_detail_html()
		if self.payment_status == 'Paid':
			self.check_vendor_orders_payment()
		if self.status == 'Delivered' and self.payment_status == 'Paid':
			self.status = 'Completed'
			frappe.db.set_value('Order', self.name, 'status', self.status)
		if self.status == 'Completed' and self.payment_status == 'Paid':
			self.check_cashback()
		self.reload()

		if self.status == 'Completed':
			
			if self.customer:
				update_customer_preference_from_order(self.name)
			w_settings=frappe.get_single('Wallet Settings')
			if w_settings.enable_wallet==1 or w_settings.enable_customer_wallet==1:
				if not frappe.db.get_all('Wallet Transaction',filters={'order_id':self.name, 'docstatus': ('!=', 2)}):
					update_wallet_entry(self)

		if self.payment_status=="Paid":
			all_trans = frappe.db.get_all('Wallet Transaction',filters={'order_id':self.name, "status":"Pending", "transaction_type" :"Receive"})
			for item in all_trans:
				frappe.db.set_value('Wallet Transaction', item.name, 'status', 'Credited')


		payment_method_name = ""
		payment_method = frappe.db.get_all("Payment Method",filters={"name":self.payment_method},fields=['*'])
		if payment_method and self.outstanding_amount > 0 and self.payment_status != 'Paid':
			payment_method = payment_method[0]
			payment_method_name = payment_method.payment_method
			if payment_method_name == "Stripe":
				gateway_settings = None
				if frappe.db.get_value('Business Payment Gateway Settings', self.payment_method):
					gateway_dt = 'Business Payment Gateway Settings'
					gateway_settings = frappe.get_doc(gateway_dt, self.payment_method)
				else:
					gateway_dt = 'Stripe Gateway Settings'
					gateway_settings = frappe.get_single("Stripe Gateway Settings")
				if gateway_settings.future_payments == 1:
					payment_capture_states = frappe.db.get_all("Future Payment Capturing Status",fields=['status'])
					for payment_order_status in payment_capture_states:
						if self.status == payment_order_status.status and self.outstanding_amount > 0:
							future_payment = frappe.db.get_all("Stripe Future Payment",filters={"customer":self.customer,"order":self.name},fields=['*'])
							if future_payment:
								from stripe_payment.stripe_payment.api import make_future_payment
								make_future_payment(self.name,future_payment[0].card_source_id,future_payment[0].stripe_customer_id)


	def update_coupon_discount(self):
		total_weight = 0
		for item in self.order_item:
			total_weight += flt(item.weight) if item.weight else 0
		from go1_commerce.go1_commerce.doctype.discounts.discounts import get_coupon_code
		response = get_coupon_code(self.discount_coupon, self.order_subtotal, self.customer, cart_items, None, shipping_method=self.shipping_method, payment_method=self.payment_method, business=None, website_type=None, total_weight =total_weight,shipping_charges=self.shipping_charges)
		frappe.log_error(response, 'go1_commerce.go1_commerce.doctype.order.update_coupon_discount')

	def cancel_order_detail(self):
		if self.name and self.paid_using_wallet and int(self.paid_using_wallet) > 0:
			tran_name = frappe.db.get_value("Wallet Transaction",{"order_id":self.name,"order_type":"Order"})
			if tran_name:
				wall = frappe.get_doc("Wallet Transaction", tran_name)
				wall.docstatus = 2
				wall.save(ignore_permissions=True)

		if self.outstanding_amount == self.total_amount:
			frappe.db.set_value("Order", self.name, "outstanding_amount", 0)
			frappe.db.set_value("Order", self.name, "payment_status", "Cancelled")
		vendor_orders = frappe.db.get_all('Vendor Orders', filters={'order_reference': self.name})
		if vendor_orders:
			for item in vendor_orders:
				doc = frappe.get_doc('Vendor Orders', item.name)
				doc.status = "Cancelled"
				doc.save(ignore_permissions=True)

	def check_order_delivery(self):
		orderDelivery=frappe.db.get_all('Order Delivery',filters={'order_id':self.name})		
		if not orderDelivery:
			from go1_commerce.go1_commerce.api import notify_drivers
			notify_drivers(self.name)

	def check_workflow_state(self):
		workflow = frappe.db.get_all('Workflow', filters={'is_active': 1, 'document_type': 'Order'})
		if workflow:
			workflow = frappe.get_doc('Workflow', workflow[0].name)
			check_status = list(filter(lambda x: x.state == self.workflow_state, workflow.transitions))
			checked_condition = []
			domain = None
			if self.web_url:
				if 'https://www.' in self.web_url:
					domain = self.web_url.split('https://www.')[1]
				elif 'https://' in self.web_url:
					domain = self.web_url.split('https://')[1]
				else:
					domain = self.web_url
			for item in check_status:
				if item.condition:
					if not frappe.safe_eval(item.condition, None, {'doc': self}):
						continue
				if item.next_state in checked_condition:
					continue
				checked_condition.append(item.next_state)
				if item.next_state == 'Driver Accepted':
					enable_notification = get_settings_value_from_domain('Order Settings', 'enable_driver_notification', domain=domain)
					allow_notification = False
					diff = 0
					order_date = None
					time_zone = frappe.db.get_value('Business', self.business, 'time_zone')
					max_time = frappe.db.sql('''select max(estimated_time) from `tabRestaurant Preparation Time` where parent = %(parent)s''', {'parent': self.business})
					max_preparation_time = 0
					if max_time and max_time[0]:
						max_preparation_time = max_time[0][0]
					if not max_preparation_time:
						max_preparation_time = frappe.db.get_value('Business', self.business, 'avg_preparation_time')
					notify_time = int(max_preparation_time) if max_preparation_time else 0
					if self.shipping_method_name == 'Delivery' and self.expected_travel_time:
						notify_time = notify_time + int(self.expected_travel_time)
					now_date = get_today_date(time_zone, True)
					if self.order_time == 'ASAP':
						allow_notification = True
					else:
						if notify_time and int(notify_time) > 0:
							order_time = frappe.utils.to_timedelta(self.order_time)
							order_date = get_datetime(str(self.order_date) + ' ' + str(order_time))
							if order_date > now_date:
								diff = frappe.utils.time_diff_in_seconds(order_date, now_date)
								if diff <= (int(notify_time) * 60):
									allow_notification = True
						else:
							allow_notification = True
					if allow_notification:
						if enable_notification:
							self.check_order_delivery()
						cancel_order = get_settings_value_from_domain('Business Setting','cancel_order', domain=domain)
						if cancel_order:
							cancel_after = get_settings_value_from_domain('Business Setting','cancel_after', domain=domain)
							import datetime
							current_time = datetime.datetime.now()
							cancel_at = current_time + timedelta(seconds=int(cancel_after))
							node_cancel_order(self.name, cancel_at, 'go1_commerce.go1_commerce.api.cancel_order', cancel_after, business=self.business)
						elif self.workflow_state != 'Driver Not Assigned':
							enable_driver_reallocation = get_settings_value_from_domain('Business Setting','enable_driver_reallocation', domain=domain)
							if not enable_driver_reallocation:
								cancel_after = get_settings_value_from_domain('Business Setting','driver_unassigned_after', domain=domain)
								import datetime
								current_time = datetime.datetime.now()
								cancel_at = current_time + timedelta(seconds=int(cancel_after))
								node_unassigned_driver_order(self.name, cancel_at, 'go1_commerce.go1_commerce.api.driver_unassigned_order', cancel_after, business=self.business)

				elif item.next_state in ['Restaurant Accepted', 'Business Accepted']:
					self.check_order_time(domain)
					self.check_vendor_notification()
			if self.workflow_state in ['Restaurant Accepted', 'Business Accepted']:
				self.check_order_time(domain)
				if not self.order_accepted_time:
					self.order_accepted_time = get_today_date(replace=True)
					frappe.db.set_value('Order', self.name, 'order_accepted_time', self.order_accepted_time)
				if self.business and not self.preparation_time or self.preparation_time == '':
					prep_time_list = frappe.db.get_all('Restaurant Preparation Time', filters={'parent': self.business}, fields=['estimated_time', 'is_default'])
					if prep_time_list and len(prep_time_list) > 0:
						check_default = next((x for x in prep_time_list if x.is_default == 1), None)
						if check_default:
							frappe.db.set_value('Order', self.name, 'preparation_time', check_default.estimated_time)
						else:
							check_min = min([x.estimated_time for x in prep_time_list if x.estimated_time])
							if check_min:
								frappe.db.set_value('Order', self.name, 'preparation_time', check_min)
			if self.workflow_state == 'Order Delivered' and not self.delivered_time:
				self.delivered_time = get_today_date(replace=True)
				frappe.db.set_value('Order', self.name, 'delivered_time', self.delivered_time)
			if self.workflow_state == 'Driver Arrived' and not self.driver_arrived_time:
				time_zone = frappe.db.get_value('Business', self.business, 'time_zone')
				current_date = get_today_date(time_zone, replace=True)
				frappe.db.set_value('Order', self.name, 'driver_arrived_time', current_date)
			if self.workflow_state == 'Out For Delivery':
				if not self.driver_picked_time:
					time_zone = frappe.db.get_value('Business', self.business, 'time_zone')
					current_date = get_today_date(time_zone, replace=True)
					self.driver_picked_time = current_date
					frappe.db.set_value('Order', self.name, 'driver_picked_time', self.driver_picked_time)
				if self.driver_arrived_time:
					time_diff_driver = frappe.utils.time_diff_in_seconds(self.driver_picked_time, self.driver_arrived_time)
					import datetime
					self.driver_waiting_time = datetime.timedelta(seconds=time_diff_driver) 
					frappe.db.set_value('Order', self.name, 'driver_waiting_time', self.driver_waiting_time)
			if self.workflow_state == 'Driver Not Assigned' and frappe.db.get_value('Order', self.name, 'is_drivers_reallocated') == 0:
				check_reallocation = get_settings_value_from_domain('Business Setting','order_reallocation_drivers', domain=domain)
				if check_reallocation:
					notifications = frappe.db.get_all('Driver Assigned', filters={"order_id":self.name},fields=['respond_within','notified_at'],order_by="respond_within desc",limit_page_length=1)
					if notifications:
						reallocation_time = get_settings_value_from_domain('Business Setting','each_allocation_time_difference', domain=domain)
						driver_time = get_settings_value_from_domain('Business Setting','driver_time', domain=domain)
						if reallocation_time == 0:
							reallocation_time = 1
						import datetime
						time_inseconds = int(reallocation_time*60)
						schedule_at =  notifications[0].notified_at 
						reallocate_drivers_max_count = get_settings_value_from_domain('Business Setting','reallocate_drivers_max_count', domain=domain)
						for x in range(reallocate_drivers_max_count):
							node_cancel_order(self.name, schedule_at, 'go1_commerce.go1_commerce.api.retrigger_notify_drivers', time_inseconds, business=self.business)
							time_inseconds = time_inseconds + int(reallocation_time*60) + 2
						frappe.db.set_value('Order', self.name, 'is_drivers_reallocated', 1)
						frappe.db.commit()

	def check_order_time(self, domain=None):
		allow_cancel_order = True
		if self.order_time != 'ASAP':
			time_zone = frappe.db.get_value('Business', self.business, 'time_zone')
			max_time = frappe.db.sql('''select max(estimated_time) from `tabRestaurant Preparation Time` where parent = %(parent)s''', {'parent': self.business})
			max_preparation_time = 0
			if max_time and max_time[0]:
				max_preparation_time = max_time[0][0]
			if not max_preparation_time:
				max_preparation_time = frappe.db.get_value('Business', self.business, 'avg_preparation_time')
			notify_time = int(max_preparation_time) if max_preparation_time else 0
			if self.shipping_method_name == 'Delivery' and self.expected_travel_time:
				notify_time = notify_time + int(self.expected_travel_time)
			now_date = get_today_date(time_zone, True)
			if notify_time and int(notify_time) > 0:
				order_time = frappe.utils.to_timedelta(self.order_time)
				order_date = get_datetime(str(self.order_date) + ' ' + str(order_time))
				if order_date > now_date:
					diff = frappe.utils.time_diff_in_seconds(order_date, now_date)
					if diff <= (int(notify_time) * 60):
						pass
					else:
						if int(diff) > 0:
							diff = diff - ((int(notify_time) + 10) * 60)
							new_date = now_date + timedelta(seconds=int(diff))
							if self.restaurant_status == 'Accepted' and self.workflow_state in ['Restaurant Accepted', 'Business Accepted']:
								node_cancel_order(self.name, new_date, 'go1_commerce.go1_commerce.doctype.order.order.send_business_notification', diff, business=self.business)
							if self.shipping_method_name == 'Delivery' and self.driver_status != 'Accepted' and self.workflow_state != 'Driver Not Assigned':
								node_cancel_order(self.name, new_date, 'go1_commerce.go1_commerce.doctype.order.order.reschedule_notification', diff, business=self.business)

		if self.restaurant_status == 'Pending':
			self.check_vendor_notification()
			if allow_cancel_order:
				cancel_order_business = get_settings_value_from_domain('Business Setting', 'business_cancel_order', domain=domain)
				if cancel_order_business:
					cancel_after = get_settings_value_from_domain('Business Setting', 'business_accept_time', domain=domain)
					current_time = datetime.now()
					cancel_at = current_time + timedelta(seconds=int(cancel_after))						
					node_cancel_order(self.name, cancel_at, 'go1_commerce.go1_commerce.doctype.order.order.cancel_order', cancel_after, business=self.business)

	def calculate_travel_time(self):
		try:
			if self.shipping_method_name == 'Delivery':
				source = '{0} {1} {2} {3} {4}'.format(self.address, self.city, (self.state or ''), self.country, self.zipcode)
				latitude, longitude = frappe.db.get_value('Business', self.business, ['latitude', 'longitude'])
				destination = '{0},{1}'.format(latitude, longitude)
				from go1_commerce.go1_commerce.api import check_distance_from_maps
				result = check_distance_from_maps(source, destination)
				if result:
					time_taken = result[0]['duration']['value']
					if time_taken:
						expected_time = int(time_taken) / 60
						self.expected_travel_time = expected_time
						frappe.db.set_value('Order', self.name, 'expected_travel_time', expected_time)
						frappe.db.commit()
						return expected_time
			return 0
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.doctype.order.order(calculate_travel_time)')

	def check_vendor_orders_payment(self):
		vendor_orders = frappe.db.get_all('Vendor Orders', filters={'order_reference': self.name, 'payment_status': ('!=', self.payment_status)})
		if vendor_orders:
			for item in vendor_orders:
				doc = frappe.get_doc('Vendor Orders', item.name)
				doc.payment_status = self.payment_status
				doc.save(ignore_permissions=True)

	def check_vendor_notification(self, check_existing=True):
		if "notification" in frappe.get_installed_apps():
			from notification.notification.api import insert_notification_queue
			vendors = frappe.db.get_all('App Alert Device', filters={'document': 'Shop User'},fields=['user','name'])
			if vendors:
				for vendor in vendors:
					if check_existing and not frappe.db.get_all('Notification Queue', filters={'document': 'Order', 'reference_name': self.name, 'shop_user': vendor.name }):
						insert_notification_queue('Order', self.name, vendor.user)
					elif not check_existing:
						insert_notification_queue('Order', self.name, vendor.user)

	def check_cashback(self):
		from go1_commerce.go1_commerce.doctype.discounts.discounts import update_customer_wallet
		update_customer_wallet(self)

	def update_order_delivery(self):
		if self.shipping_method_name == 'Delivery' and self.status == 'Cancelled':
			order_delivery = frappe.db.get_all('Order Delivery', filters={'order_id': self.name})
			if order_delivery:
				frappe.db.set_value('Order Delivery', order_delivery[0].name, 'delivery_status', 'Cancelled')
			if self.driver:
				check_orders_list = frappe.db.sql('''select name from `tabOrder` where driver = %(driver)s and status not in ("Completed", "Cancelled") and name <> %(name)s''', {'driver': self.driver, 'name': self.name}, as_dict=1)
				if not check_orders_list:
					frappe.db.set_value('Drivers', self.driver, 'working_status', 'Available')


	@frappe.whitelist(allow_guest=True)
	def get_restaurant_order_to_time(self,order_date,order_time,time_diff):
		order_date_time = get_datetime(str(order_date) + ' ' + str(order_time))
		to_order_date_time = order_date_time + timedelta(minutes=int(time_diff))
		return to_order_date_time.strftime('%I:%M %p')
@frappe.whitelist()
def generate_order_detail_template(order_id):
	catalog_settings = get_settings_from_domain('Catalog Settings')
	currency = frappe.db.get_all('Currency',fields=["*"], filters={"name":catalog_settings.default_currency},limit_page_length=1)
	if order_id:		
		order_info = frappe.db.get_all('Order', fields=['*'], filters={'name':order_id})
		if order_info:
			items = frappe.db.get_all('Order Item',filters={'parent':order_info[0].name},fields=['*'],order_by='idx')
			if items:
				for item in items:
					attr_image =''
					if item.attribute_ids:
						attr_ids = item.attribute_ids.split('\n')
						id_list = []
						for i in attr_ids:
							if i: id_list.append(i)
						ids = ",".join(['"' + x + '"' for x in id_list])
						options = frappe.db.sql('''select * from `tabProduct Attribute Option` where parent = %(parent)s and name in ({0})'''.format(ids),{'parent':item.item},as_dict = 1)				
						for op in options:
							if op.image_list:
								images = json.loads(op.image_list)
								if len(images) > 0:
									images = sorted(images, key=lambda x: x.get('is_primary'), reverse=True)
									attr_image = images[0].get('thumbnail')
					result = frappe.db.sql('''select cart_thumbnail,list_image from `tabProduct Image` where parent=%(product)s order by is_primary desc limit 1''',{'product':item.item},as_dict=1)
					if attr_image:
						item.item_image = attr_image
					elif result and result[0].cart_thumbnail:
						item.item_image = result[0].cart_thumbnail					
					sku =  frappe.db.sql('''SELECT sku from `tabProduct` WHERE name=%(name)s''',{'name':item.item},as_dict=1)
					item.item_sku = ""
					if sku and sku[0].sku:
						item.item_sku = sku[0].sku
						
			order_info[0].order_item = items
			checkout_attributes = frappe.db.get_all('Order Checkout Attributes',filters={'parent':order_info[0].name},fields=['*'])
			order_info[0].checkout_attributes = checkout_attributes
			order_details = order_info[0]
			restaurant = show_address = 0
			show_address = 1
			
			multi_vendor = 0
			
			theme_settings = '#247eba'
			themes = frappe.db.get_all('Web Theme', filters={'is_active': 1},fields=['primary_button_background_color'])
			if themes:
				theme_settings = themes[0].primary_button_background_color
			delivery_slot = []
			check_delivery_slot = frappe.db.get_all('Order Delivery Slot', filters={'order': order_info[0].name}, fields=['order_date', 'from_time', 'to_time','product_category'])
			if check_delivery_slot:
				for deli_slot in check_delivery_slot:
					category = ''
					if deli_slot.product_category:
						category = frappe.get_value('Product Category', deli_slot.product_category, 'category_name')
					from_time = datetime.strptime(str(deli_slot.from_time), '%H:%M:%S').time()
					to_time = datetime.strptime(str(deli_slot.to_time), '%H:%M:%S').time()
					delivery_slot.append({
						'delivery_date': deli_slot.order_date.strftime('%b %d, %Y'),
						'from_time': from_time.strftime('%I:%M %p'),
						'to_time': to_time.strftime('%I:%M %p'),
						'category': category
						})
			order_settings = get_settings_from_domain('Order Settings')
			shipments = frappe.db.get_all("Shipment",filters={"document_name":order_info[0].name},fields=['*'])
			status_history = frappe.db.get_all("Status History",filters={"parent":order_info[0].name},fields=['*'],order_by='creation desc')
			tax_splitup = None
			if order_details.tax_json:
				tax_splitup = json.loads(order_details.tax_json)
			check_process_status = 0
			allow_shipment = 0
			check_order_status = frappe.db.get_all("Order Status",filters={"shipping_status":"In Process"})
			if check_order_status:
				check_process_status = 1
			if order_details.shipping_method:
				shipping_method = frappe.db.get_all("Shipping Method",fields=['is_deliverable'],filters={"name":order_details.shipping_method})
				if shipping_method:
					if shipping_method[0].is_deliverable == 1:
						allow_shipment = 1
			customer_fullname,customer_notes = frappe.db.get_value('Customers', order_details.customer,["full_name","customer_notes"])
			if not "loyalty" in frappe.get_installed_apps(): 
				order_details.loyalty_amount = 0
			farm_share_notes = None
			if "johnhenrys_custom_app" in frappe.get_installed_apps() and order_details.is_recurring_order == 1: 
				farm_share_notes = frappe.db.get_value('Customers', order_details.customer,"farm_share_notes")
			is_driver = 0
			
			context = {
				'order_details': order_details,
				"currency": currency[0].symbol,
				"catalog_settings": catalog_settings,
				'restaurant': restaurant,
				'show_address': show_address,
				'themes':theme_settings,
				'multi_vendor': multi_vendor,
				'delivery_slot': delivery_slot,
				'order_settings':order_settings,
				'shipments':shipments,
				"check_process_status":check_process_status,
				"status_history":status_history,
				"allow_shipment":allow_shipment,
				"customer_notes":customer_notes,
				"customer_fullname":customer_fullname,
				'tax_splitup': tax_splitup,
				'is_driver': is_driver,
				"farm_share_notes":farm_share_notes,
				'loyalty': 1 if "loyalty" in frappe.get_installed_apps() else 0
			}

			if order_settings.admin_order_template == "Order Template with Progress":
				return frappe.render_template('templates/order_template.html', context)
			else:
				return frappe.render_template('templates/order_detail_template.html', context)

@frappe.whitelist(allow_guest=True)
def calculate_order_shipping_charges(self):
	try:
		tax_percent = tax_rate = isMobileCart = 0
		mobilecartitems = []


		cart = business = shipping_method = None
		condition = ''
		catalog_settings = get_settings_from_domain('Catalog Settings', business=self.business)
		shipping_rate_method = frappe.db.sql('''select shipping_rate_method as name from `tabShipping Rate Method` where is_active = 1 {0}'''.format(condition), as_dict=1)
		shipping_charges = 0
		order = frappe.get_doc('Order', self.name)
		if self.shipping_method:
			shipping_method = self.shipping_method
		if self.order_subtotal:
			subtotal = self.order_subtotal
		state = country = zipcode =None
		if self.shipping_state:
			state = self.shipping_state
		if self.shipping_country:
			country = self.shipping_country
		if self.shipping_zipcode:
			zipcode = self.shipping_zipcode
		if shipping_rate_method:
			if shipping_rate_method[0].name == 'Shipping By Weight':
				shipping_charges = calculate_single_vendor_weight_based_shipping_charges1(shipping_method, state, country, zipcode, subtotal, order)
			if shipping_rate_method[0].name == 'Shipping By Total':
				shipping_charges = calculate_single_vendor_total_based_shipping_charges1(
						shipping_method, state, country, zipcode, subtotal, order)
			if shipping_rate_method[0].name == 'Fixed Rate Shipping':
				shipping_charges = calculate_single_vendor_fixed_rate_shipping_charges1(shipping_method, state, country, zipcode, subtotal, order)
		tax = tax_percent = 0
		if order and order.total_tax_amount:
			tax = 0
			tax_percent = 0
		if shipping_charges > 0:
			if catalog_settings.shipping_is_taxable == 1 and catalog_settings.shipping_tax_class != '':
				if catalog_settings.shipping_tax_class:
					tax_template = frappe.get_doc('Product Tax Template', catalog_settings.shipping_tax_class)
					for item in tax_template.tax_rates:
						tax_percent = tax_percent + float(item.rate)
						if catalog_settings.shipping_price_includes_tax == 1:
							tax = tax + shipping_charges * item.rate / (100 + item.rate)
						else:
							tax = tax + float(shipping_charges) * float(item.rate) / 100

		return {
			'shipping_charges': shipping_charges,
			'tax_rate': (math.ceil(tax * 100) / 100),
			'item_tax': (order.total_tax_amount if order else 0),
			'tax_percent': tax_percent,
			}
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.doctype.order.order.calculate_order_shipping_charges')


@frappe.whitelist(allow_guest=True)
def update_wallet_entry(self):		
	try:
		business_info = None
		if self.business:
			business_info = frappe.get_doc('Business', self.business)
		party_type_list = ['Service Provider', 'Business', 'Drivers', 'Customers']
		w_settings=frappe.get_single('Wallet Settings')
		if w_settings.party_splitup:
			party_type_list = []
			for part in w_settings.party_splitup:
				party_type_list.append(part.party)
		for item in party_type_list:
			amount = 0
			party = party_name = ""
			payment_notes = "Against order: {0}".format(self.name)
			status = "Pending"
			is_settlement_paid = 0
			if int(w_settings.enable_approval)==0:
				status = "Credited"
				is_settlement_paid = 1
			transaction_type = "Pay"
			payment_method_name = ""
			party_type = item
			if frappe.db.get_value('Payment Method', self.payment_method):
				payment_method_name = frappe.db.get_value('Payment Method', self.payment_method, 'payment_method')
			if payment_method_name == '':
				if frappe.db.get_value("Business Payment Gateway Settings",self.payment_method):
					payment_method_name = frappe.db.get_value("Business Payment Gateway Settings",self.payment_method, 'gateway_type')
			if self.payment_method_name != "Cash" and int(w_settings.credit_period) > 0:
				status = "Locked"
			if item == 'Business' and self.business:
				party = self.business
				party_name = frappe.db.get_value('Business', self.business, 'restaurant_name')
				amount = self.total_amount_for_vendor
				if self.payment_status == 'Paid' and self.payment_method_name == 'Cash':
					status = 'Credited'
				if self.payment_method_name == 'Cash':
					transaction_type = 'Receive'
			elif item == 'Drivers':
				party_type = 'Drivers'
				if not self.driver:
					if party_type == 'Drivers': continue
				if party_type == 'Business':
					party = self.business
					party_name = frappe.db.get_value('Business', self.business, 'restaurant_name')
					payment_notes = '{0}\nDriver Charges: {1}'.format(payment_notes, round(self.total_driver_charges, 2))
				else:
					party = self.driver
					party_name = frappe.db.get_value('Drivers',self.driver,'driver_name')
				amount = self.total_driver_charges
			elif item == 'Service Provider':
				amount = float(self.commission_amt)
				transaction_type = 'Receive'
				if self.payment_method_name != 'Cash':
					status = 'Credited'
				else:
					transaction_type = 'Receive'
			elif item == 'Customers' and flt(self.customer_commission)>0 and int(w_settings.enable_customer_wallet)==1:
				party_type = 'Customers'
				party = self.customer
				party_name = self.customer_name
				amount = self.customer_commission
				payment_notes = "Commission against order ID: {0}".format(self.name)
			if self.payment_status == 'Paid' and self.transaction_id and (payment_method_name == "Stripe" or self.payment_method =="Stripe Payment") and amount > 0:
				from stripe_payment.stripe_payment.api import transfer_amount_to_users
				if item != "Service Provider":
					frappe.enqueue('stripe_payment.stripe_payment.api.transfer_amount_to_users', doc=self,party_type=party_type, party_name=party, amount=amount)
					status = "Credited"
			if flt(amount)>0:
				wallet_doc = frappe.new_doc('Wallet Transaction')
				wallet_doc.type = party_type if party_type != "Drivers" else "Driver"
				wallet_doc.reference = self.doctype
				wallet_doc.order_type = self.doctype
				wallet_doc.order_id = self.name
				wallet_doc.transaction_date = now()
				wallet_doc.total_value = self.total_amount
				wallet_doc.transaction_type = transaction_type
				wallet_doc.is_settlement_paid = is_settlement_paid
				wallet_doc.amount = amount
				wallet_doc.status = status
				wallet_doc.notes = payment_notes
				if item != "Service Provider":
					wallet_doc.party_type = party_type
					wallet_doc.party = party
					wallet_doc.party_name = party_name
				wallet_doc.flags.ignore_permissions = True
				wallet_doc.submit()

	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.order.order.update_wallet_entry") 
				
	
@frappe.whitelist()
def get_drivers(doctype, txt, searchfield, start, page_len, filters):
	try:
		user=frappe.db.sql('''select name from `tabDrivers`''')
		return user
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.order.get_drivers") 
	
@frappe.whitelist()
def get_customers(doctype,txt,searchfield,start,page_len,filters):
	try:
		user=frappe.db.sql('''select name, full_name from `tabCustomers` where naming_series <> "GC-"''')
		return user
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.order.get_customers") 

@frappe.whitelist()
def get_order_status(doctype,txt,searchfield,start,page_len,filters):
	try:
		condition=''
		if txt:
			condition+=' and name like "%{txt}%"'.format(txt=txt)
		active_domains=''
		from frappe.core.doctype.domain_settings.domain_settings import get_active_domains
		domains_list=get_active_domains()
		for item in domains_list:
			if item:
				active_domains+='"'+item+'",'	
		query='SELECT name from `tabOrder Status` where (case when domain_based=1 then domain in ({active_domains}) else 1=1 end) {condition} order by display_order'.format(active_domains=active_domains[:-1],condition=condition)
		results=frappe.db.sql('''{query}'''.format(query=query))
		return results
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.order.order.get_order_status") 

@frappe.whitelist()
def check_payment(self):
	try:
		if self.payment_status=="Paid":
			payment=frappe.db.get_all('Payment Entry',filters={'order_id':self.name})
			paymant_type="Cash" if self.payment_type=="Cash" else "Online Payment"
			if not payment:
				frappe.get_doc({
					"doctype":"Payment Entry",
					"restaurant":self.restaurant,
					"order_id":self.name,
					"customer":self.customer,
					"customer_name":self.customer_name,
					"amount_to_pay":self.total_amount,
					"use_wallet_balance":0,
					"paid_amount":self.total_amount,
					"mode_of_payment":paymant_type
					}).submit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.order.check_payment") 
	
@frappe.whitelist(allow_guest=True)
def send_cancel_notification(self):
	try:
		app_notification_settings=frappe.get_single('App Notification Settings')
		customer=frappe.get_doc("Customers",self.customer)
		player=[]
		if customer:
			if customer.player_id:
				player.append(customer.player_id)
				os_app_id = app_notification_settings.app_id
				os_apikey = app_notification_settings.secret_key
				client = OneSignalAppClient(app_id=os_app_id, app_api_key=os_apikey)
				notification = Notification(app_notification_settings.app_id, Notification.DEVICES_MODE)
				notification.include_player_ids = player # Must be a list!
				notification.data={'add_data':"Order notification"}
				notification.contents={"en":"Your Order "+self.name+" has been cancelled by Restaurant."}
				try:
					result = client.create_notification(notification)
				except HTTPError as e:
					result = e.response.json()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.order.send_cancel_notification") 
	
@frappe.whitelist(allow_guest=True)
def send_notification(self,doctype="Order",message="You have an order!"):
	try:
		frappe.publish_realtime(event='msgprint',message='hello',user='administrator')
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.order.send_notification") 

@frappe.whitelist(allow_guest=True)
def check_orderDelivery(self):
	try:
		orderDelivery=frappe.db.get_all('Order Delivery',filters={'order_id':self.name})
		import random 
		import string
		random = ''.join([random.choice(string.ascii_letters
				+ string.digits) for n in range(10)])
		if not orderDelivery:
			self.delivery_created=1
			frappe.get_doc({
				"doctype":"Order Delivery",
				"order_id":self.name,
				"posted_date":getdate(nowdate()),
				"name":random
				}).insert()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.order.check_orderDelivery") 
	
@frappe.whitelist(allow_guest=True)
def update_orderDelivery(self):
	try:
		orderDelivery=frappe.db.get_all('Delivery',filters={'order_id':self.name})
		if orderDelivery:
			doc=frappe.get_doc('Order Delivery',orderDelivery[0].name)
			if self.driver_status=="Driver Accepted":
				doc.delivery_status="Driver Assigned"
				if doc.driver_assigned:
					for item in doc.driver_assigned:
						if item.driver==self.driver:
							item.status="Accepted"
							frappe.db.set_value('Drivers',item.driver,'working_status','On Duty')
			elif self.driver_status=="Delivered":
				doc.delivery_status="Delivered"
			if self.status=="Cancelled":
				doc.delivery_status="Cancelled"
			doc.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.doctype.order.update_orderDelivery") 



@frappe.whitelist()
def make_invoice(source_name, target_doc=None):
	from go1_commerce.accounts.api import make_sales_invoice
	make_sales_invoice(source_name, target_doc=None, submit=True)
	
def randomStringDigits(stringLength=6):
	import random
	import string
	lettersAndDigits = string.ascii_uppercase + string.digits
	return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))

@frappe.whitelist()
def get_order_settings(order_id,doctype):
	if not frappe.db.get_value(doctype, order_id):
		return
	order = frappe.get_doc(doctype,order_id)
	check_process_status = 0
	allow_shipment = 0
	check_order_status = frappe.db.get_all("Order Status",filters={"shipping_status":"In Process"})
	if check_order_status:
		check_process_status = 1
	if order.shipping_method:
		shipping_method = frappe.db.get_all("Shipping Method",fields=['is_deliverable'],filters={"name":order.shipping_method})
		if shipping_method:
			if shipping_method[0].is_deliverable == 1:
				allow_shipment = 1
	loyalty = 0
	if "loyalty" in frappe.get_installed_apps():
		loyalty = 1
	return {"loyalty":loyalty,"proccess_status":check_process_status,"order_settings":get_settings_from_domain('Order Settings'),"allow_shipment":allow_shipment}

@frappe.whitelist()
def check_order_settings():
	is_restaurant_driver = 0
	return {"order_settings":get_settings_from_domain('Order Settings'),"is_restaurant":False,"is_restaurant_driver":is_restaurant_driver}

@frappe.whitelist()
def make_refund(refund_amount, order):
	payment = get_customer_payments(order)
	if len(payment)>0:
		refund = frappe.get_doc("Payment Entry",payment[0].name)
		refund.cancel()
		if refund.docstatus==2:
			frappe.db.set_value("Order", order, "payment_status", "Refunded")
			return "success"
	return "failed"

@frappe.whitelist()
def mark_as_ready(order):
	order_info = frappe.get_doc("Order",order)
	order_info.status = "Ready"
	order_info.save(ignore_permissions=True)

@frappe.whitelist()
def get_customer_payments(order):
	payments=frappe.db.sql('''select p.name,p.posting_date,p.paid_amount,r.outstanding_amount from `tabPayment Entry` p, `tabPayment Reference` r where r.parent=p.name and r.reference_doctype="Order" and r.reference_name=%s''',order,as_dict=1)
	return payments

@frappe.whitelist()
def send_notification_for_order(self):
	from mobile_notification.mobile_notification.doctype.app_notification_center.app_notification_center import send_default_notification_new
	if self.status=="Completed" and self.customer_type=="Customers":
		cust_subject = 'Order is claimed by vendor!'
		cust_id = frappe.db.get_all('Customers',fields=['name','player_id'],filters={"name":self.customer,"player_id":("!=",""),"player_id":("!=",None),"player_id":("!=","null")})
		cust_history = frappe.db.get_all('Notification History',fields=['name'],filters={"reference":self.doctype,"reference_name":self.name,"app_type":'User',"value":self.status})
		if len(cust_id)>0 and len(cust_history)<=0:
			send_default_notification_new(self.doctype,self.name,[cust_id[0].player_id],cust_subject,'User',self.status)

@frappe.whitelist(allow_guest=True)
def cancel_order(order):
	if not frappe.db.get_value('Order', order):
		return
	OrderDetail = frappe.get_doc('Order', order)
	if OrderDetail.restaurant_status != 'Accepted' and OrderDetail.status != 'Cancelled':
		OrderDetail.status = 'Cancelled'
		OrderDetail.restaurant_status = 'Not Responded'
		OrderDetail.save(ignore_permissions=True)
		frappe.db.set_value('Order', order, 'workflow_state', 'Order Cancelled')
		frappe.publish_realtime('order_tracking',{'name':OrderDetail.name, 'workflow_state':'Order Cancelled','business':OrderDetail.business})
		if "mobile_notification" in frappe.get_installed_apps():
			from go1_commerce.go1_commerce.api import send_notification_for_order
			send_notification_for_order('Order Cancelled', OrderDetail)
	return {'status': 'Success'}

@frappe.whitelist()
def auto_complete_orders():
	try:
		return True
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'auto_complete_orders')

@frappe.whitelist(allow_guest=True)
def reschedule_notification(order):
	try:
		if not frappe.db.get_value('Order', order):
			return
		order_doc = frappe.get_doc('Order', order)
		if order_doc.get('workflow_state') and order_doc.workflow_state != 'Driver Accepted':
			from frappe.model.workflow import get_workflow_name
			workflow_name = get_workflow_name('Order')
			domain = None
			if order_doc.web_url:
				if 'https://www.' in order_doc.web_url:
					domain = order_doc.web_url.split('https://www.')[1]
				elif 'https://' in order_doc.web_url:
					domain = order_doc.web_url.split('https://')[1]
				else:
					domain = order_doc.web_url
			if workflow_name:
				workflow = frappe.get_doc('Workflow', workflow_name)
				check_state = list(filter(lambda x: x.state == order_doc.workflow_state, workflow.transitions))
				if check_state:
					check_driver_status = next((st for st in check_state if st.next_state == 'Driver Accepted'), None)
					if check_driver_status:
						enable_notification = get_settings_value_from_domain('Order Settings', 'enable_driver_notification')
						if enable_notification:
							order_doc.check_order_delivery()
						cancel_order = get_settings_value_from_domain('Business Setting','cancel_order', domain=domain)
						if cancel_order and int(cancel_order) == 1:
							cancel_after = get_settings_value_from_domain('Business Setting','cancel_after', domain=domain)
							current_time = datetime.now()
							cancel_at = current_time + timedelta(seconds=int(cancel_after))
							node_cancel_order(order_doc.name, cancel_at, 'go1_commerce.go1_commerce.api.cancel_order', cancel_after, business=order_doc.business)							
						else:
							pass
							cancel_after = get_settings_value_from_domain('Business Setting','driver_unassigned_after', domain=domain)
							if order_doc.workflow_state != 'Driver Not Assigned' and cancel_after and int(cancel_after) > 0:
								current_time = datetime.now()
								cancel_at = current_time + timedelta(seconds=int(cancel_after))
								node_unassigned_driver_order(order_doc.name, cancel_at, 'go1_commerce.go1_commerce.api.driver_unassigned_order', cancel_after, business=order_doc.business)
		return {'status': 'Success'}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.doctype.order.order.reschedule_notification')
		return {'status': 'Error'}

@frappe.whitelist(allow_guest=True)
def get_linked_invoice(order):
	return frappe.db.get_value("Sales Invoice",{"reference":order})

@frappe.whitelist(allow_guest=True)
def send_business_notification(order):
	try:
		if not frappe.db.get_value('Order', order):
			return
		order_doc = frappe.get_doc('Order', order)
		if order_doc.get('workflow_state') and order_doc.workflow_state in ['Restaurant Accepted', 'Business Accepted']:
			users_list = frappe.db.sql_list('''select d.device_id from `tabApp Alert Device` d 
						left join `tabShop User` s on s.name = d.user and d.document = "Shop User" 
						where s.restaurant = %(business)s and s.role = "Vendor" and d.enabled = 1 
						and d.device_id is not null and d.device_id <> "" group by d.device_id''', {'business': order_doc.business})
			if users_list and len(users_list)> 0 and "notification" in frappe.get_installed_apps():
				message = 'Order #{0} to be completed by {1}'.format(order_doc.name, order_doc.order_time)
				check_notification = []
				if not check_notification:
					from notification.notification.doctype.app_alert_settings.app_alert_settings import send_app_notification
					check_msg = "Order #"+order_doc.name+" to be completed by"
					check_notifications = frappe.db.get_all("Notification History",filters={'subject': ('like', '%' + check_msg + '%'),'reference_name':order_doc.name})
					if not check_notifications:
						res = send_app_notification('Order', order_doc.name, users_list, message, 'Admin App', '', add_data='Preorder Notification')
						prev_time = order_doc.expected_travel_time
						order_doc.calculate_travel_time()
						order_doc.expected_travel_time = frappe.db.get_value("Order",order_doc.name,"expected_travel_time")
						order_time = to_timedelta(order_doc.order_time)
						order_date = datetime.strptime(str(getdate(order_doc.order_date)) + ' ' + str(order_time), '%Y-%m-%d %H:%M:%S')
						collect_time = 0
						if order_doc.expected_travel_time and int(order_doc.expected_travel_time) > 0:
							collect_time = int(order_doc.expected_travel_time)
						collect_datetime = order_date - timedelta(minutes=int(collect_time))
						pickup_time = collect_datetime.strftime('%I:%M %p')
						frappe.publish_realtime('preorder_notification', {'name': order_doc.name, 'business': order_doc.business, 'pickup_time': pickup_time, 'shipping_method_name': order_doc.shipping_method_name})
						if prev_time != order_doc.expected_travel_time:
							frappe.publish_realtime('order_tracking', {'name': order_doc.name, 'workflow_state': order_doc.get('workflow_state'),'business': order_doc.business})
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.doctype.order.order.send_business_notification')

@frappe.whitelist(allow_guest=True)
def calculate_multi_vendor_weight_based_shipping_charges1(shipping_method, state, country, zipcode, subtotal,
	order):
	total_shipping_charges = 0
	weight = 0
	vendors = frappe.db.sql('''select P.restaurant from `tabOrder Item` CI inner join `tabProduct` P on P.name=CI.item
						inner join `tabBusiness` B on P.restaurant=B.name where CI.parent=%(orderid)s group by P.restaurant''', {'orderid': order.name}, as_dict=True)
	for x in vendors:
		vendor_products = frappe.db.sql('''select P.name from `tabOrder Item` CI
					inner join `tabProduct` P on P.name=CI.item inner join `tabBusiness` B on P.restaurant=B.name
					where CI.parent=%(cartid)s and P.restaurant=%(business)s''', {'cartid': order.name, 'business': x.restaurant}, as_dict=True)
		for item in vendor_products:
			shipping_charges = 0
			(product_weight, enable_shipping, free_shipping,
			 additional_shipping_cost, tracking_method) = frappe.db.get_value('Product', item.get('name') or item.get('item'), ['weight', 'enable_shipping', 'free_shipping', 'additional_shipping_cost', 'inventory_method'])
			order_total = 0
			if enable_shipping == 1 and free_shipping == 0:
				citem = None
				citems = frappe.db.sql('''select * from `tabOrder Item` CI where parent=%(cartid)s and item=%(product)s''', {'cartid': cart.name, 'product': item.name}, as_dict=True)
				if citems:
					citem = citems[0]
				if citem.get('attribute_ids') and tracking_method == 'Track Inventory By Product Attributes':
					attribute_id = get_attributes_json(citem.get('attribute_ids'))
					combination_weight = frappe.db.sql('''select weight from `tabProduct Variant Combination` where parent=%(name)s and attributes_json=%(attribute_id)s''', {'name': citem.get('item'), 'attribute_id': attribute_id}, as_dict=1)
					if combination_weight:
						weight = combination_weight[0].weight * citem.get('quantity')
						if additional_shipping_cost > 0:
							shipping_charges += additional_shipping_cost * citem.get('quantity')
						order_total = order_total + float(citem.get('t_amount'))
				else:
					weight = citem.get('weight') * citem.get('quantity')
					if additional_shipping_cost > 0:
						shipping_charges += additional_shipping_cost * citem.get('quantity')
					order_total = order_total + float(citem.get('t_amount'))
					if citem.get('attribute_ids'):
						attr_id = citem.get('attribute_ids').splitlines()
						for item in attr_id:
							query = '''SELECT * FROM `tabProduct Attribute Option` WHERE name="{name}"'''.format(name=item)
							attribute_weight = frappe.db.sql(query, as_dict=1)
							if attribute_weight and attribute_weight[0].weight_adjustment:
								weight += flt(attribute_weight[0].weight_adjustment) * citem.get('quantity')
				shipping_charges_list = frappe.db.sql('''select * from `tabShipping By Weight Charges` where shipping_method=%(shipping_method)s and %(weight)s>=order_weight_from and %(weight)s<=order_weight_to''', {'weight': weight, 'shipping_method': shipping_method}, as_dict=True)
				charges = calculate_shipping_charges_from_list1(shipping_charges, shipping_charges_list, state, country, zipcode, order_total, 1, x.restaurant)
				frappe.db.set_value('Order Item', citems[0].name, 'shipping_charges', charges)
				total_shipping_charges += charges
	return total_shipping_charges

@frappe.whitelist(allow_guest=True)
def calculate_multi_vendor_total_based_shipping_charges1(shipping_method, state, country, zipcode, subtotal, order):
	total_shipping_charges = 0
	vendors = frappe.db.sql('''select P.restaurant from `tabOrder Item` CI
					inner join `tabProduct` P on P.name=CI.item
					inner join `tabBusiness` B on P.restaurant=B.name
					where CI.parent=%(cartid)s group by P.restaurant''',
						  {'cartid': order.name}, as_dict=True)
	for x in vendors:
		vendor_products = frappe.db.sql('''select CI.* from `tabOrder Item` CI
					inner join `tabProduct` P on P.name=CI.item
					inner join `tabBusiness` B on P.restaurant=B.name
					where CI.parent=%(cartid)s and P.restaurant=%(business)s''',
							  {'cartid': order.name,
							  'business': x.restaurant}, as_dict=True)
		for item in vendor_products:
			shipping_charges = 0 
			order_total = 0
			(product_weight, enable_shipping, free_shipping,
			 additional_shipping_cost, tracking_method) = \
				frappe.db.get_value('Product', item.get('item'),
									['weight', 'enable_shipping',
									'free_shipping',
									'additional_shipping_cost',
									'inventory_method'])
			if enable_shipping == 1 and free_shipping == 0:
				order_total = order_total + float(item.get('t_amount'))
				if additional_shipping_cost > 0:
					shipping_charges += additional_shipping_cost \
					* item.get('quantity')
				shipping_charges_list = \
					frappe.db.sql('''select * from `tabShipping By Total Charges` where shipping_method=%(shipping_method)s and %(order_total)s>=order_total_from and %(order_total)s<=order_total_to'''
								  , {'order_total': order_total,
								  'shipping_method': shipping_method},
								  as_dict=True)
				charges = calculate_shipping_charges_from_list1(
					shipping_charges,
					shipping_charges_list,
					state, country, zipcode,
					order_total,
					1,
					x.restaurant,
					)
				frappe.db.set_value('Order Item', item.name,
							'shipping_charges', charges)
				total_shipping_charges += charges
	return total_shipping_charges

@frappe.whitelist(allow_guest=True)
def calculate_multi_vendor_fixed_rate_shipping_charges1(
	shipping_method,
	state, country, zipcode,
	subtotal,
	order):
	try:
		total_shipping_charges = 0
		vendors = \
				frappe.db.sql('''select P.restaurant from `tabOrder Item` CI
						inner join `tabProduct` P on P.name=CI.item
						inner join `tabBusiness` B on P.restaurant=B.name
						where CI.parent=%(cartid)s group by P.restaurant''',
							  {'cartid': order.name}, as_dict=True)
		for x in vendors:
			order_total = 0
			vendor_products = \
					frappe.db.sql('''select P.name from `tabOrder Item` CI
						inner join `tabProduct` P on P.name=CI.item
						inner join `tabBusiness` B on P.restaurant=B.name
						where CI.parent=%(cartid)s and P.restaurant=%(business)s''',
								  {'cartid': order.name,
								  'business': x.restaurant}, as_dict=True)
			for item in vendor_products:
				shipping_charges = 0 
				(product_weight, enable_shipping, free_shipping,
				 additional_shipping_cost, tracking_method) = \
					frappe.db.get_value('Product', item.get('name')
										or item.get('item'), ['weight',
										'enable_shipping', 'free_shipping',
										'additional_shipping_cost',
										'inventory_method'])
				if enable_shipping == 1 and free_shipping == 0:
					citem = None
					citems = frappe.db.sql('''select * from `tabOrder Item` CI where parent=%(cartid)s and item=%(product)s'''
								, {'cartid': order.name,
								'product': item.name}, as_dict=True)
					if citems:
						citem = citems[0]
					if citem:
						if additional_shipping_cost > 0:
							if additional_shipping_cost > 0:
								shipping_charges += additional_shipping_cost \
								* citem.get('quantity')
						order_total = order_total + float(citem.get('t_amount'
								))
					shipping_charges_list = \
						frappe.db.sql('''select * from `tabShipping By Fixed Rate Charges` where shipping_method=%(shipping_method)s'''
									  ,
									  {'shipping_method': shipping_method},
									  as_dict=True)
					charges = calculate_shipping_charges_from_list1(
						shipping_charges,
						shipping_charges_list,
						state, country, zipcode,
						order_total,
						1,
						x.restaurant,
						)
					frappe.db.set_value('Order Item', citems[0].name,
								'shipping_charges', charges)
					total_shipping_charges += charges
		return total_shipping_charges
	except Exception:
		frappe.log_error(frappe.get_traceback(), 'go1_commerce.go1_commerce.api.calculate_multi_vendor_fixed_rate_shipping_charges')

@frappe.whitelist(allow_guest=True)
def calculate_single_vendor_weight_based_shipping_charges1(shipping_method, state, country, zipcode, subtotal,
	order):
	shipping_charges = 0
	weight = 0
	order_total = 0
	if order and order.order_item:
		for citem in order.order_item:
			(product_weight, enable_shipping, free_shipping,
			 additional_shipping_cost, tracking_method) = frappe.db.get_value('Product', citem.item,
					['weight', 'enable_shipping', 'free_shipping', 'additional_shipping_cost', 'inventory_method'])
			if enable_shipping == 1 and free_shipping == 0:
				if citem.attribute_ids and tracking_method == 'Track Inventory By Product Attributes':
					attribute_id = get_attributes_json(citem.attribute_ids)						
					combination_weight = frappe.db.sql('''select weight from `tabProduct Variant Combination` where parent=%(name)s and attributes_json=%(attribute_id)s''', {'name': citem.item, 'attribute_id': attribute_id}, as_dict=1)
					if combination_weight:
						weight += combination_weight[0].weight * citem.quantity
						if additional_shipping_cost > 0:
							shipping_charges += additional_shipping_cost * citem.quantity
						order_total += citem.t_amount
				else:
					weight += citem.weight * citem.quantity
					if additional_shipping_cost > 0:
						shipping_charges += additional_shipping_cost \
						* citem.quantity
					order_total += citem.t_amount
					if citem.attribute_ids:
						attr_id = citem.attribute_ids.splitlines()
						for item in attr_id:
							query = \
								'''SELECT * FROM `tabProduct Attribute Option` WHERE name="{name}"'''.format(name=item)
							attribute_weight = frappe.db.sql(query,
									as_dict=1)
							if attribute_weight and attribute_weight[0].weight_adjustment:
								weight += flt(attribute_weight[0].weight_adjustment) * citem.quantity
	shipping_charges_list = frappe.db.sql('''select * from `tabShipping By Weight Charges` where shipping_method=%(shipping_method)s and %(weight)s>=order_weight_from and %(weight)s<=order_weight_to'''
					  , {'weight': weight,'shipping_method': shipping_method}, as_dict=True)
	return calculate_shipping_charges_from_list1(shipping_charges,
			shipping_charges_list, state, country, zipcode, order_total)

@frappe.whitelist(allow_guest=True)
def calculate_single_vendor_fixed_rate_shipping_charges1(shipping_method,state, country, zipcode,subtotal,order):
	shipping_charges = 0
	order_total = 0
	if order and order.order_item:
		for citem in order.order_item:
			(product_weight, enable_shipping, free_shipping,
			 additional_shipping_cost, tracking_method) = \
				frappe.db.get_value('Product', citem.item,
					['weight', 'enable_shipping', 'free_shipping',
					'additional_shipping_cost', 'inventory_method'])
			if enable_shipping == 1 and free_shipping == 0:
				if additional_shipping_cost > 0:
					shipping_charges += additional_shipping_cost * citem.quantity
				order_total += citem.t_amount
	shipping_charges_list = \
		frappe.db.sql('''select * from `tabShipping By Fixed Rate Charges` where shipping_method=%(shipping_method)s'''
					  , {'shipping_method': shipping_method},
					  as_dict=True)
	return calculate_shipping_charges_from_list1(shipping_charges,
			shipping_charges_list, state, country, zipcode, order_total)

@frappe.whitelist(allow_guest=True)
def calculate_single_vendor_total_based_shipping_charges1(shipping_method, state, country, zipcode, subtotal, order):
	shipping_charges = 0
	order_total = 0
	if order and order.order_item:
		for citem in order.order_item:
			(product_weight, enable_shipping, free_shipping,
			 additional_shipping_cost, tracking_method) = frappe.db.get_value('Product', citem.item,
					['weight', 'enable_shipping', 'free_shipping', 'additional_shipping_cost', 'inventory_method'])
			if enable_shipping == 1 and free_shipping == 0:
				order_total += citem.t_amount
				if additional_shipping_cost > 0:
					shipping_charges += additional_shipping_cost * citem.quantity

	shipping_charges_list = frappe.db.sql('''select * from `tabShipping By Total Charges` where shipping_method=%(shipping_method)s and %(order_total)s>=order_total_from and %(order_total)s<=order_total_to'''
					  , {'order_total': order_total, 'shipping_method': shipping_method}, as_dict=True)
	return calculate_shipping_charges_from_list1(shipping_charges,
			shipping_charges_list, state, country, zipcode, order_total)

@frappe.whitelist(allow_guest=True)
def calculate_shipping_charges_from_list1(shipping_charges, shipping_charges_list, state, country, zipcode, subtotal, is_multivendor=None, vendor_id=None):
	if is_multivendor and vendor_id:
		matchedByVendor = []
		vendors = frappe.db.sql('select zip_code from `tabBusiness` where name=%(vendor_id)s' , {'vendor_id': vendor_id}, as_dict=True)
		if vendors:
			vendor_info = vendors[0]
			for x in shipping_charges_list:
				shipping_zone = frappe.get_doc('Shipping Zones', x.shipping_zone)
				if shipping_zone:
					shipping_city = frappe.db.sql('''select * from `tabShipping City` where name=%(city)s''', {'city': shipping_zone.from_city}, as_dict=True)
					if shipping_city:
						if shipping_city[0].zipcode_range:
							if shipping_zip_matches_order(vendor_info.zip_code, shipping_city[0].zipcode_range):
								matchedByVendor.append(x)
		if len(matchedByVendor) == 0:
			for item in shipping_charges_list:
				shipping_zone = frappe.get_doc('Shipping Zones', item.shipping_zone)
				if not shipping_zone.from_city:
					matchedByVendor.append(item)
					shipping_charges_list = matchedByVendor
	matchedShippingCharges = []

	matchedByZip = []
	for item in shipping_charges_list:
		shipping_zone = frappe.get_doc('Shipping Zones', item.shipping_zone)
		if shipping_zone:
			shipping_city = frappe.db.sql('''select * from `tabShipping City` where name=%(city)s''', {'city': shipping_zone.to_city},as_dict=True)
			if shipping_city:
				if shipping_city[0].zipcode_range:
					if shipping_zip_matches_order(zipcode, shipping_city[0].zipcode_range):
						matchedShippingCharges.append(item)
	if len(matchedShippingCharges) == 0:
		for x in shipping_charges_list:
			shipping_zone = frappe.get_doc('Shipping Zones', x.shipping_zone)
			if shipping_zone.state == state:
				matchedShippingCharges.append(x)
		if len(matchedShippingCharges) == 0:
			for x in shipping_charges_list:
				shipping_zone = frappe.get_doc('Shipping Zones', x.shipping_zone)
				if shipping_zone.country == country:
					matchedShippingCharges.append(x)


	matchedByState = []
	for x in matchedByZip:
		shipping_zone = frappe.get_doc('Shipping Zones', x.shipping_zone)
		if shipping_zone.state == state:
			matchedByState.append(x)
	if len(matchedByState) == 0:
		for x in matchedByZip:
			shipping_zone = frappe.get_doc('Shipping Zones', x.shipping_zone)
			if not shipping_zone.state:
				matchedByState.append(x)


	matchedByCountry = []
	for x in matchedByState:
		shipping_zone = frappe.get_doc('Shipping Zones', x.shipping_zone)
		if shipping_zone.country == country:
			matchedByCountry.append(x)
	if len(matchedByCountry) == 0:
		for x in matchedByState:
			shipping_zone = frappe.get_doc('Shipping Zones', x.shipping_zone)
			if not shipping_zone.country:
				matchedByCountry.append(x)


	if matchedShippingCharges:
		shipingmatchedByZip = matchedShippingCharges[0]
		if shipingmatchedByZip.use_percentage == 1:
			shipping_charges += float(subtotal) * shipingmatchedByZip.charge_percentage / 100
		else:
			shipping_charges += float(shipingmatchedByZip.charge_amount)
	return shipping_charges

@frappe.whitelist(allow_guest=True)
def shipping_zip_matches_order(zip, ziprange):
	zipcoderanges = []
	returnValue = False
	if ziprange.find(',') > -1:
		zipcoderanges = ziprange.split(',')
		for x in zipcoderanges:
			if x.find('-') > -1:
				zipcoderanges_after = x.split('-')
				for zipcode in range(int(zipcoderanges_after[0]), int(zipcoderanges_after[1]) + 1):
					if str(zipcode).lower() == str(zip).lower():
						returnValue = True
			else:
				if str(x).lower() == str(zip).lower():
					returnValue = True
	elif ziprange.find('-') > -1:
		zipcoderanges_after = ziprange.split('-')
		for zipcode in range(int(zipcoderanges_after[0]), int(zipcoderanges_after[1]) + 1):
			if str(zipcode).lower() == str(zip).lower():
				returnValue = True
	else:
		if str(ziprange).lower() == str(zip).lower():
			returnValue = True
	return returnValue

@frappe.whitelist(allow_guest=True)
def get_installed_app():
	installed_apps = frappe.db.sql(''' select * from `tabModule Def` where app_name='shipping_providers' ''', as_dict=True)
	return installed_apps
@frappe.whitelist(allow_guest=True)
def check_installed_app(app_name):
	if app_name in frappe.get_installed_apps():
		return True
	return False
@frappe.whitelist()
def clear_guest_user_details(order_id):
	if not frappe.db.get_value('Order', order_id):
		return
	order_info = frappe.get_doc('Order', order_id)
	if order_info and order_info.customer and order_info.customer_type=="Customers":
		customer_info = frappe.get_doc('Customers', order_info.customer)
		if customer_info.naming_series == 'GC-':
			frappe.db.set_value('Customers', customer_info.name, 'first_name', 'Guest')
			frappe.db.set_value('Customers', customer_info.name, 'email', None)
			frappe.db.set_value('Customers', customer_info.name, 'phone', None)
			if customer_info.table_6:
				for item in customer_info.table_6:
					item.delete()
			if not order_info.customer_name:
				frappe.db.set_value('Order', order_id, 'customer_name', customer_info.first_name)
		else:
			if not order_info.customer_name:
				frappe.db.set_value('Order', order_id, 'customer_name', customer_info.full_name)


@frappe.whitelist()
def update_order_shipment_payment(order):
	shipments = frappe.db.get_all("Shipment",filters={"document_name":order},fields=['*'])
	if shipments:
		frappe.db.sql(''' UPDATE `tabShipment` set payment_status = 'Paid' WHERE name = %(shipment_id)s ''',{'shipment_id':shipments[0].name})

def get_query_condition(user):
	return True
	
@frappe.whitelist()
def update_order_totals(order,shipping_charges,discount_amount,Wallet_amount,loyalty_amount=None,loyalty_points=None):
	order_info = frappe.get_doc("Order",order)
	frappe.db.set_value('Order', order, 'shipping_charges', shipping_charges)
	frappe.db.set_value('Order', order, 'discount', discount_amount)
	if flt(order_info.discount)!= flt(discount_amount):
		frappe.db.set_value('Order', order, 'is_custom_discount', 1)
	frappe.db.set_value('Order', order, 'paid_using_wallet', Wallet_amount)
	
	if loyalty_amount:
		frappe.db.set_value('Order', order, 'loyalty_amount', loyalty_amount)
		frappe.db.set_value('Order', order, 'loyalty_points', loyalty_points)


	frappe.db.commit()
	order_info = frappe.get_doc("Order",order)
	order_info.save(ignore_permissions=True)
	if flt(loyalty_amount)>0:
		check_points = frappe.db.get_all("Loyalty Point Entry",filters={"reference":order,"customer":order_info.customer},fields=['*'])
		if check_points:
			for x in check_points:
				if x.loyalty_points < 0:
					frappe.db.sql('''DELETE FROM `tabLoyalty Point Entry` WHERE name =%(loyalty_entry_name)s''',{"loyalty_entry_name":x.name})
					frappe.db.commit()
		from loyalty.loyalty.doctype.loyalty_settings.loyalty_settings import order_redeem_point
		
		order_redeem_point(order)



@frappe.whitelist()	
def create_custom_wallet_entry(order,amount):
	wallet_trans_entry = frappe.get_doc({
	"doctype":"Wallet Transaction",
	"reference":"Order",
	"order_type":"Order",
	"order_id":order.name,
	"transaction_date":now(),
	"total_value":amount,
	"amount":amount,
	"is_settlement_paid":0,
	"is_fund_added":1
	})
	wallet_trans_entry.order_id =  order.name
	wallet_trans_entry.type = "Customers"
	wallet_trans_entry.party_type = "Customers"
	wallet_trans_entry.party = order.customer
	wallet_trans_entry.transaction_type = "Pay"
	wallet_trans_entry.status = "Debited"
	wallet_trans_entry.flags.ignore_permissions = True
	wallet_trans_entry.submit()

@frappe.whitelist()
def update_order_checkout_attributes(order,attributes):
	for x in json.loads(attributes):
		if x.get('name') and x.get('name') != '':
			frappe.db.set_value('Order Checkout Attributes', x.get("name"), 'attribute_description', x.get("attribute_description"))
		else:
			frappe.get_doc({
				'doctype': 'Order Checkout Attributes',
				'parent': order,
				'parenttype': 'Order',
				'parentfield': "checkout_attributes",
				'price_adjustment': (x.get('price_adjustment') or 0),
				'attribute_id': x.get('checkout_attribute_id'),
				'attribute_description': x.get('attribute_description')
				}).insert(ignore_permissions=True)
	frappe.db.commit()
	order_info = frappe.get_doc("Order",order)
	order_info.save(ignore_permissions=True)
@frappe.whitelist()	
def update_giftcard_payments(order_id,transaction_id):
	giftcard_orders = frappe.get_all("Gift Card Order",filters={"order_reference":order_id})
	for x in giftcard_orders:
		giftcard_order = frappe.get_doc("Gift Card Order",x.name)
		giftcard_order.transaction_id = transaction_id
		giftcard_order.payment_status = "Paid"
		giftcard_order.save(ignore_permissions=True)
@frappe.whitelist()	
def update_giftcard_status(order):
	giftcard_orders = frappe.get_all("Gift Card Order",filters={"giftcart_coupon_code":order.giftcard_coupon_code,"is_giftcard_used":0})
	for x in giftcard_orders:
		giftcard_order = frappe.get_doc("Gift Card Order",x.name)
		giftcard_order.is_giftcard_used = 1
		giftcard_order.save(ignore_permissions=True)
		usage_history = frappe.new_doc("Gift Card Usage History")
		usage_history.used_code = order.giftcard_coupon_code
		usage_history.customer_name = order.customer_name
		usage_history.customer_email = order.customer_email
		usage_history.customer_phone = order.phone
		usage_history.order_id = order.name
		usage_history.customer = order.customer
		usage_history.save(ignore_permissions=True)
		frappe.db.commit()

@frappe.whitelist()	
def get_customer_loyaltypoints(customer_id,order_total):
	catalog_settings = get_settings_from_domain('Catalog Settings')
	currency = frappe.get_doc("Currency",catalog_settings.default_currency)
	catalog_settings.default_currency = currency.symbol
	checkout_points= {
				"total_available_points": round(0,2), 
				"total_available_amount": round(0,2),
				"remaining_points":round(0,2),
				"total":round(0,2), 
				"deduction":round(0,2), 
				"use_flat_rates":0,
				"flat_rates":0,
				"deduction_point":round(0,2), 
				"payable":round(0,2)
			}	
	if "loyalty" in frappe.get_installed_apps():
		from loyalty.loyalty.api import checkout_redeem_points
		checkout_points = checkout_redeem_points(customer=customer_id,party_type="Customers", amount=order_total)
	return {"checkout_points":checkout_points,"settings":catalog_settings}

@frappe.whitelist()
def clear_selected_orders(names):
	docs = json.loads(names)
	if len(docs) == 0:
		frappe.throw(frappe._('Please select any record'))
	for i, item in enumerate(docs):	
		check_linked_docs('Order', item)
		show_progress(docs, frappe._('Deleting {}'.format('Order')), i, item)

def check_linked_docs(dt, dn):
	linkinfo = get_linked_doctypes(dt)
	linked_docs = get_linked_docs(dt, dn, linkinfo)
	if not linked_docs:
		doc = frappe.get_doc(dt, dn)
		doc.flags.ignore_permissions = True
		if doc.docstatus == 1:
			doc.cancel()
		doc.delete()
	for _dt, link_docs in linked_docs.items():
		for rec in link_docs:
			if _dt == 'Discounts' and dt == 'Order':
				frappe.db.sql('''delete from `tabDiscount Usage History` where parent = %(rec)s and order_id = %(name)s''', {'rec': rec.name, 'name': dn})
			else:
				check_linked_docs(_dt, rec.name)

def show_progress(docnames, message, i, description):
	n = len(docnames)
	if n >= 10:
		frappe.publish_progress(
			float(i) * 100 / n,
			title = message,
			description = description
		)
def get_coupon_discount(order_id,order_subtotal,coupon_code):
	status = 'success'
	coupon = frappe.db.get_all('Discounts', filters={'requires_coupon_code': 1, 'coupon_code': coupon_code}, fields=['*'])
	msg = ''
	coupon_data = None
	if coupon:
		coupon_data = frappe.get_doc('Discounts', coupon[0].name)
		if coupon_data:
			if  coupon_data.discount_requirements:
				for req in coupon_data.discount_requirements:
					if req.discount_requirement == 'Spend x amount':
						if float(order_subtotal) < float(req.amount_to_be_spent):
							status = 'failed'
							msg = 'Your cart must contain minimum value 0f $' + str(req.amount_to_be_spent)
							break
					elif req.discount_requirement == 'Specific price range':
						if req.min_amount and float(order_subtotal) < float(req.min_amount):
							status = 'failed'
							msg = 'Your cart must contain minimum value of $' + str(req.min_amount)
							break
						if req.max_amount and float(order_subtotal) > float(req.max_amount):
							status = 'failed'
							msg = 'Your cart value must not exceed of $' + str(req.max_amount)
							break
		else:
			status = 'failed'
	else:
		status = 'failed'
	if status == 'failed':
		return {'message': msg, 'status': status}
	if status == 'success':
		if coupon_data.price_or_product_discount == "Price":
			discount_amount = coupon_data.discount_amount
			if coupon_data.percent_or_amount == "Discount Percentage":
				discount_amount = (flt(order_subtotal)*flt(coupon_data.discount_percentage))/100
			if coupon_data.max_discount_amount>0:
				if discount_amount>coupon_data.max_discount_amount:
					discount_amount = coupon_data.max_discount_amount
			free_order_items = frappe.db.sql("""SELECT name FROM `tabOrder Item` WHERE parent=%(order_id)s AND is_free_item = 1 AND discount_coupon<>'' """,{"order_id":order_id},as_dict=1)
			for x in free_order_items:
				frappe.db.sql(""" DELETE FROM `tabOrder Item` WHERE name=%(order_item_id)s""",{"order_item_id":x.name})
				frappe.db.commit()
			return {"discount_amount":discount_amount,"discount_rule":coupon_data.name,"status":status}
		else:
			new_order_item = ""
			free_order_items = frappe.db.sql("""SELECT name FROM `tabOrder Item` WHERE parent=%(order_id)s AND is_free_item = 1 AND discount_coupon<>'' """,{"order_id":order_id},as_dict=1)
			for x in free_order_items:
				frappe.db.sql(""" DELETE FROM `tabOrder Item` WHERE name=%(order_item_id)s""",{"order_item_id":x.name})
				frappe.db.commit()
			if coupon_data.free_product:
				product = frappe.get_doc("Product",coupon_data.free_product)
				new_order_item = frappe.new_doc("Order Item")
				new_order_item.amount = (product.price*coupon_data.free_qty)
				new_order_item.is_free_item = 1
				new_order_item.is_gift_card = 0
				new_order_item.parent = order_id
				new_order_item.parentfield = "order_item"
				new_order_item.parenttype =  "Order"
				new_order_item.is_rewarded = 0
				new_order_item.order_item_type = "Product"
				new_order_item.is_scanned = 0
				new_order_item.item_name = product.item
				new_order_item.item = coupon_data.free_product
				new_order_item.item_image = product.image
				new_order_item.ordered_weight = product.weight
				new_order_item.price = product.price
				new_order_item.quantity = coupon_data.free_qty
				new_order_item.return_created = 0
				new_order_item.shipping_status = "Pending"
				new_order_item.shipping_charges = 0
				new_order_item.t_amount = (product.price*coupon_data.free_qty)
				new_order_item.tax = 0
				new_order_item.weight = product.weight
				new_order_item.discount_coupon = coupon_code
				new_order_item.insert()
			return {'message': msg, 'status': status, "new_order_item": new_order_item}


@frappe.whitelist()
def get_shipment_bag_id(order_id):
	items=frappe.db.sql('''select parent from `tabShipment Bag Item` where order_id=%(order_id)s order by idx''',{'order_id':order_id},as_dict=1)
	if items:
		return {"status":"success","shipment_id":items[0].parent}
	else:
		return {"status":"failed","shipment_id":items[0].parent}

@frappe.whitelist()
def auto_driver_reallocation():
	return True
	