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

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters):
	birthday_club_settings = get_settings_from_domain('BirthDay Club Setting')
	if birthday_club_settings.beneficiary_method == "Discount":
	    return frappe.db.sql("""SELECT M.email,M.day,M.month,substring_index(M.creation, ' ',1),
	    						(SELECT order_id FROM `tabDiscount Usage History` DU WHERE 
	    						parent = %(discount_id)s AND DU.customer = C.name ORDER BY DU.creation DESC limit 1) as `Order ID`
	    						FROM `tabBirthDay Club Member` M INNER JOIN `tabCustomers` C
	    						ON M.email = C.email 
	    						ORDER BY M.creation DESC """,{"discount_id":birthday_club_settings.discount_id})

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
