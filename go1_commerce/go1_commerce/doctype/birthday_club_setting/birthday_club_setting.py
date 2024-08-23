# -*- coding: utf-8 -*-
# Copyright (c) 2021, Tridots Tech and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, nowdate, add_days
from frappe.model.document import Document
from go1_commerce.utils.setup import get_settings
from frappe.query_builder import DocType


class BirthDayClubSetting(Document):
	def on_update(self):
		if self.beneficiary_method == "Discount":
			if self.requires_coupon_code == 1:
				if not self.coupon_code or self.coupon_code == "":
					frappe.throw("Please enter the coupon code")
			if not self.discount_id:
				discount = create_birthday_club_discount(self)
				self.discount_id = discount.name
			else:
				update_birthday_club_discount(self)
		if self.beneficiary_method == "Wallet":
			if self.discount_id:
				self.remove_birthday_club_discount()
				self.discount_id = None


def update_birthday_club_discount(self):
	
	DiscountRequirements = DocType('Discount Requirements')
	delt = (frappe.qb.from_(DiscountRequirements)
		.delete()
		.where(DiscountRequirements.parent == self.discount_id)
		.run())
	frappe.db.commit()
	frappe.get_doc({
				'doctype': 'Discount Requirements',
				'parent':self.discount_id,
				'discount_requirement':"Limit to role",
				'parentfield':"discount_requirements",
				'parenttype':"Discounts",
				'items_list':"[{\"item\":\"BirthDay Club Member\",\"item_name\":\"BirthDay Club Member\",\
																							\"idx\":1}]",
			}).insert(ignore_permissions=True)
	frappe.db.commit()
	if self.discount_type == "Discount Amount":
		frappe.get_doc({
						'doctype': 'Discount Requirements',
						'parent':self.discount_id,
						'discount_requirement':"Spend x amount",
						'parentfield':"discount_requirements",
						'parenttype':"Discounts",
						'amount_to_be_spent':self.discount_amount,
					}).insert(ignore_permissions=True)
	
		frappe.db.commit()
	frappe.db.commit()
	discount = frappe.get_doc("Discounts",self.discount_id)
	discount.percent_or_amount = self.discount_type
	discount.discount_percentage = self.discount_percentage
	discount.discount_amount = self.discount_amount
	discount.requires_coupon_code = self.requires_coupon_code
	discount.coupon_code = self.coupon_code
	discount.save()
	return discount

def create_birthday_club_discount(self):
	from_date = getdate(nowdate())
	to_date = add_days(from_date, -1)
	discount_requirements = []
	discount_requirements.append({"discount_requirement":"Limit to role",
								  "items_list": "[{\"item\":\"BirthDay Club Member\",\"item_name\":\
															\"BirthDay Club Member\",\"idx\":1}]"})
	if self.discount_type == "Discount Amount":
		discount_requirements.append({"discount_requirement":"Spend x amount",
									  "amount_to_be_spent": self.discount_amount})
	discount = frappe.get_doc({"doctype":"Discounts",
							"name1": "BirthDay Club - "+self.name+"-"+str(from_date),
							"discount_type" : "Assigned to Sub Total",
							"start_date":to_date,
							"limitations":"N times per user",
							"limitation_count":1,
							"percent_or_amount":self.discount_type,
							"discount_percentage":self.discount_percentage,
							"discount_amount":self.discount_amount,
							"requires_coupon_code":self.requires_coupon_code,
							"discount_requirements":discount_requirements,
							"coupon_code":self.coupon_code,
							"is_birthday_club_discount":1,
							})
	discount.save()
	frappe.db.commit()
	discount.save()
	return discount


def remove_birthday_club_discount(self):
	from_date = getdate(nowdate())
	to_date = add_days(from_date, -1)
	discount = frappe.get_doc("Discounts",self.discount_id)
	discount.end_date = to_date
	discount.save()


def update_birthday_club_wallet():
	from datetime import date
	todays_date = date.today()
	birthday_club_settings = get_settings('BirthDay Club Setting')
	if birthday_club_settings:
		if birthday_club_settings.beneficiary_method == "Wallet":
			BirthDayClubMember = DocType('BirthDay Club Member')
			Customers = DocType('Customers')
			HasRole = DocType('Has Role')
			query = (
				frappe.qb.from_(BirthDayClubMember)
				.inner_join(Customers).on(Customers.email == BirthDayClubMember.email)
				.inner_join(HasRole).on(HasRole.parent == BirthDayClubMember.email)
				.select(
					BirthDayClubMember.name,
					BirthDayClubMember.email,
					BirthDayClubMember.day,
					BirthDayClubMember.month,
					BirthDayClubMember.is_email_sent,
					Customers.name.as_('customer_id')
				)
				.where(HasRole.role == 'BirthDay Club Member')
			)
			members = query.run(as_dict=True)
			for x in members:
				from datetime import datetime
				birth_day  = getdate(datetime(todays_date.year, 
							month_string_to_number(x.month.lower()), x.day, 00, 00, 00))
				allow = 0
				if birthday_club_settings.before_days > 0:
					start_date = add_days(birth_day,-1*birthday_club_settings.before_days)
					if todays_date==start_date:
						allow = 1
				else:
					start_date = getdate(datetime(todays_date.year, 
								month_string_to_number(x.month.lower()), 1, 00, 00, 00))
					from frappe.utils import date_diff
					date_diff = date_diff(getdate(birth_day), getdate())
					if date_diff ==  birthday_club_settings.before_days:
						allow = 1
				if allow == 1:
					wallet_transaction = frappe.new_doc("Wallet Transaction")
					wallet_transaction.type = "Customers"
					wallet_transaction.party_type = "Customers"
					wallet_transaction.status = "Credited"
					wallet_transaction.is_settlement_paid = 1
					wallet_transaction.party = x.customer_id
					wallet_transaction.amount = birthday_club_settings.wallet_amount
					wallet_transaction.notes = "Amount Credited Against Birth Club - "+\
															birthday_club_settings.name
					wallet_transaction.docstatus = 1
					wallet_transaction.save()
					from frappe.core.doctype.communication.email import make
					email_template = frappe.get_doc("Email Template",birthday_club_settings.email_template)
					doc = frappe.get_doc("BirthDay Club Member",x.name)
					sender = frappe.db.get_value("Email Account", birthday_club_settings.sender, 
																						'email_id')
					make(doctype = "BirthDay Club Member", name = x.name,
						subject = frappe.render_template(email_template.get("subject"),{'doc': doc}),
						content = frappe.render_template(email_template.get("body"),{'doc': doc}),
						sender = sender, recipients = x.email,
						communication_medium = "Email", send_email = True )
	 

def month_string_to_number(string):
	m = {
		'jan': 1,
		'feb': 2,
		'mar': 3,
		'apr': 4,
		'may': 5,
		'jun': 6,
		'jul': 7,
		'aug': 8,
		'sep': 9,
		'oct': 10,
		'nov': 11,
		'dec': 12
		}
	s = string.strip()[:3].lower()
	try:
		out = m[s]
		return out
	except:
		raise ValueError('Not a month')

def get_month_lastday(date):
	import calendar
	last_day = date.replace(day = calendar.monthrange(date.year, date.month)[1])
	return last_day