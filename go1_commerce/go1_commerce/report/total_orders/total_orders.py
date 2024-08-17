# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe.permissions import has_permission
from frappe.utils import getdate,nowdate
from datetime import datetime, timedelta
from frappe.query_builder import DocType, Field, Order

def execute(filters=None):
	columns, data = [], []
	if not filters: filters={}
	columns=get_columns()
	data=get_values(filters)
	chart=get_chart_data(filters)
	return columns, data ,None,chart

def get_columns():
	return[
		"Order Number" + ":Link/Order:120",
		"Order Date" + ":Date:120",
		"Order Status" + ":Data:120",
		"Payment Status" + ":Data:120",
		"Customer Name" + ":Data:120",
		"Sub Total" + ":Currency:120",
		"Shipping Charge" + ":Currency:120",
		"Tax Amount" + ":Currency:120",
		"Total Amount" + ":Currency:120",
		
		
	]

def get_values(filters):
	Order = DocType('Order')
	query = (
		frappe.qb.from_(Order)
		.select(
			Order.name,
			Order.order_date,
			Order.status,
			Order.payment_status,
			frappe.qb.functions.Concat(Order.first_name, ' ', Order.last_name).ifnull(Order.first_name).as_("full_name"),
			Order.order_subtotal,
			Order.shipping_charges,
			Order.total_tax_amount,
			Order.total_amount
		)
		.where(Order.naming_series != "SUB-ORD-")
		.where(Order.docstatus == 1)
	)
	if filters.get('from_date'):
		query = query.where(Order.order_date >= filters.get('from_date'))
	if filters.get('to_date'):
		query = query.where(Order.order_date <= filters.get('to_date'))
	if filters.get('restaurant'):
		query = query.where(Order.business == filters.get('restaurant'))
	if filters.get('status'):
		query = query.where(Order.status == filters.get('status'))
	if filters.get('payment_status'):
		query = query.where(Order.payment_status == filters.get('payment_status'))
	customer_order = query.run(as_list=True)
	return customer_order

def get_chart_data(filters):
	status=filters.get('status') if filters.get('status') else None
	months=['January','February','March','April','May','June','July','August','September','October','November','December']
	route=filters.get('route') if filters.get('route') else None
	year=filters.get('year') if filters.get('year') else None
	month=filters.get('month') if filters.get('month') else None
	days=[]
	total_day=frappe.db.sql('''select day(last_day(curdate()))''',as_list=1)[0]
	days=[x+1 for x in range(int(total_day[0]))]
	datasets=[]
	if status:
		datasets.append({
			"title":status,
			"values":get_order_list(status,year,month,months,days)
			})
	else:
		datasets.append({
			"title":'Completed',
			"values":get_order_list('Completed',year,month,months,days)
			})
		datasets.append({
			"title":'Placed',
			"values":get_order_list('Placed',year,month,months,days)
			})
		datasets.append({
			"title":'Processing',
			"values":get_order_list('Processing',year,month,months,days)
			})
		datasets.append({
			"title":'Cancelled',
			"values":get_order_list('Cancelled',year,month,months,days)
			})	
	chart = {
		"data": {
			'labels': days if month else months,
			'datasets': datasets
		}
	}
	chart["type"] = "line"
	return chart

def get_order_list(status,year,month,month_list,day_list):
	values=[]
	Order = DocType('Order')
	conditions = []
	if year:
		year=int(year)
	else:
		year=int(getdate().year)
	status = filters.get('status')
	parent = filters.get('parent')
	if status:
		conditions.append(Order.status == status)
	else:
		conditions.append(Order.status == "Completed")		
	if month:
		st_date=datetime(year=year,day=int(day_list[0]),month=datetime.strptime(month, '%B').month)
		for item in day_list:
			parent=''
			result=frappe.get_list('Order',filters={'order_date':st_date},limit_page_length=500,ignore_permissions=False)
			if result:
				parent=",".join('"'+str(x.name)+'"' for x in result)
				if parent:
					conditions.append(Order.name.isin(parent))
				query = (
					frappe.qb.from_(Order)
					.select(frappe.qb.functions.Count("*").as_("count"))
					.where(Order.naming_series != "SUB-ORD-")
				)
				for condition in conditions:
					query = query.where(condition)
				data = query.run(as_list=True)
				values.append(data[0][0]) if data else 0
				
			else:
				values.append(0)
			st_date=st_date+timedelta(days=1)
	else:
		for item in month_list:
			st_date=datetime(year=year,day=1,month=datetime.strptime(item,'%B').month)
			next_month = st_date.replace(day=28) + timedelta(days=4)			
			ed_date=next_month - timedelta(days=next_month.day)
			filters=[]
			st_filter=["order_date",">=",st_date.date()]
			ed_filter=["order_date","<=",ed_date.date()]
			naming_filter=["naming_series","!=","SUB-ORD-"]
			filters.append(st_filter)
			filters.append(ed_filter)
			filters.append(naming_filter)
			result=frappe.get_list('Order',filters=filters,limit_page_length=5000,ignore_permissions=False)
			if result:
				parent=",".join('"'+str(x.name)+'"' for x in result)
				if parent:
					conditions.append(Order.name.isin(parent))
				query = (
					frappe.qb.from_(Order)
					.select(frappe.qb.functions.Count("*").as_("count"))
					.where(Order.naming_series != "SUB-ORD-")
				)
				for condition in conditions:
					query = query.where(condition)
				data = query.run(as_list=True)
				values.append(data[0][0]) if data else 0
				
			else:
				values.append(0)	
	return values		

@frappe.whitelist()
def get_years():
	Order = DocType('Order')
	query = (
		frappe.qb.from_(Order)
		.select(frappe.qb.functions.Year(Order.order_date).as_("years"))
		.distinct()
		.where(Order.naming_series != "SUB-ORD-")
	)
	year_list = query.run(as_list=True)
	if not year_list:
		year_list = [getdate().year]
	return "\n".join(str(year) for year in year_list)
