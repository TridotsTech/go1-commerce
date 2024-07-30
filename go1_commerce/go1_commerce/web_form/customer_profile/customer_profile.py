from __future__ import unicode_literals

import frappe

def get_context(context):
	currency=frappe.db.get_all('Currency',fields=["*"], filters={"name":context.catalog_settings.default_currency},limit_page_length=1)
	context.currency=currency[0].symbol
	frappe.cache().hset('currency','symbol',context.currency)
