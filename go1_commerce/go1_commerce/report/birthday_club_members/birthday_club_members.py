from __future__ import unicode_literals
import frappe, os, re, json
from frappe.website.website_generator import WebsiteGenerator
from frappe.utils import touch_file, encode
from frappe import _
from frappe.utils import flt, getdate, nowdate, get_url, add_days, now
from datetime import datetime
from pytz import timezone
from frappe.utils import strip, get_files_path
import pytz
from urllib.parse import unquote
from six import string_types
from frappe.model.document import Document
from go1_commerce.utils.setup import get_settings_from_domain
from frappe.query_builder import DocType, Field, Subquery, Function

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters):
	birthday_club_settings = get_settings_from_domain('BirthDay Club Setting')
	if birthday_club_settings.beneficiary_method == "Discount":
		birthday_club_member = DocType("BirthDay Club Member")
		customers = DocType("Customers")
		discount_usage_history = DocType("Discount Usage History")
		subquery = (
			frappe.qb.from_(discount_usage_history, alias='DU')
			.select(discount_usage_history.order_id)
			.where(discount_usage_history.parent == birthday_club_settings.discount_id)
			.where(discount_usage_history.customer == Field("C.name"))
			.orderby(discount_usage_history.creation.desc())
			.limit(1)
		)
		
		query = (
			frappe.qb.from_(birthday_club_member, alias='M')
			.inner_join(customers, alias='C', on=birthday_club_member.email == customers.email)
			.select(
				birthday_club_member.email,
				birthday_club_member.day,
				birthday_club_member.month,
				Function("SUBSTRING_INDEX", birthday_club_member.creation, ' ', 1).as_("creation_date"),
				subquery.as_("Order ID")
			)
			.orderby(birthday_club_member.creation.desc())
		)
		result = query.run(as_dict=True)
		return result

def get_columns():
	birthday_club_settings = get_settings_from_domain('BirthDay Club Setting')
	if birthday_club_settings.beneficiary_method == "Discount":
		return[
				"Email" + ":Data:200",
				"Birth Day" + ":Data:200",
				"Birth Month" + ":Data:200",
				"Registered On" + ":Date",
				"Redeem For Order"+ ":Link/Order:180",
			]
	if birthday_club_settings.beneficiary_method == "Wallet":
		return[
				"Email" + ":Data:200",
				"Birth Day" + ":Data:200",
				"Birth Month" + ":Data:200",
				"Registered On" + ":Date",
				"Wallet Amount Credited On"+ ":Date",
			]
	if birthday_club_settings.beneficiary_method == "Wallet":
		return[
				"Email" + ":Data:200",
				"Birth Day" + ":Data:200",
				"Birth Month" + ":Data:200",
				"Registered On" + ":Date",
				"Points Credited On"+ ":Date",
			]
