# -*- coding: utf-8 -*-
# Copyright (c) 2021, Tridots Tech and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate,add_days
from frappe.query_builder import DocType

class BirthDayClubMember(Document):
	def validate(self):
		if frappe.db.exists("BirthDay Club Member",{"email":self.email, "name":("!=", self.name)}):
			frappe.throw("Email id already reigistered with BirthDay Club")


	def after_insert(self):
		customers = frappe.db.get_all("Customers",filters={"user_id":self.email})
		if customers:
			customer_roles = frappe.db.get_all("Customer Role",
									  filters={"parent":customers[0].name,"role":"BirthDay Club Member"})
			if not customer_roles:
				frappe.log_error("No Role","Check Role")
				frappe.get_doc({'doctype': 'Customer Role',
								'parent':customers[0].name,
								'parentfield':"customer_role",
								'parenttype':"Customers",
								'role':"BirthDay Club Member" }).insert(ignore_permissions=True)
				frappe.db.commit()
			customer = frappe.get_doc("Customers",customers[0].name)
			customer.save(ignore_permissions=True)
		else:
			customer = frappe.new_doc("Customers")
			customer.email = self.email
			customer.append("customer_role",{"role":"BirthDay Club Member"})
			customer.append("customer_role",{"role":"Customer"})
			customer.save(ignore_permissions=True)


def send_email_birthday_club_members():
	from datetime import date
	todays_date = date.today()
	from go1_commerce.utils.setup import get_settings, get_settings_value
	birthday_club_settings = get_settings('BirthDay Club Setting')
	if birthday_club_settings:
		if birthday_club_settings.email_template and birthday_club_settings.sender \
								and birthday_club_settings.beneficiary_method == "Discount":
			default_currency_value = get_settings_value('Catalog Settings','default_currency')
			currency = frappe.db.get_all('Currency',fields=["*"],
									filters={"name":default_currency_value},limit_page_length=1)
			default_currency = currency[0].symbol

			
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
				validate_birthday_club_member(x, todays_date, birthday_club_settings)


def validate_birthday_club_member(x, todays_date, birthday_club_settings):
	from frappe.core.doctype.communication.email import make
	if x.is_email_sent == 0:
		from datetime import datetime
		birth_day  = getdate(datetime(todays_date.year,
						month_string_to_number(x.month.lower()), x.day, 00, 00, 00))
		allow = 0
		if birthday_club_settings.before_days > 0 and birthday_club_settings.after_days>0:
			start_date = add_days(birth_day,-1*birthday_club_settings.before_days)
			end_date = add_days(birth_day,birthday_club_settings.after_days)
			if todays_date==start_date and todays_date<=end_date:
				allow = 1
		elif birthday_club_settings.before_days > 0:
			start_date = add_days(birth_day,-1*birthday_club_settings.before_days)
			if todays_date==start_date:
				allow = 1
		elif birthday_club_settings.after_days>0:
			end_date = add_days(birth_day,birthday_club_settings.after_days)
			if todays_date<=end_date:
				allow = 1
		else:
			start_date = getdate(datetime(todays_date.year,
						month_string_to_number(x.month.lower()), 1, 00, 00, 00))
			from frappe.utils import date_diff
			date_diff = date_diff(getdate(birth_day), getdate())
			if date_diff ==  birthday_club_settings.before_days:
				allow = 1
		if allow == 1:
			email_template = frappe.get_doc("Email Template",
										birthday_club_settings.email_template)
			doc = frappe.get_doc("BirthDay Club Member",x.name)
			sender = frappe.db.get_value("Email Account",
										birthday_club_settings.sender, 'email_id')
			make( doctype = "BirthDay Club Member", name = x.name,
					subject = frappe.render_template(email_template.get("subject"), {'doc': doc}),
					content = frappe.render_template(email_template.get("body"), {'doc': doc}),
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