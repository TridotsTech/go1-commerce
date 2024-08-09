# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe.permissions import has_permission
from frappe.utils import getdate,nowdate
from datetime import datetime, timedelta

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
		"Commission Amount" + ":Currency:140",
		"Total Amount For Vendor" + ":Currency:170",
		
	]

def get_values(filters):
	conditions = get_conditions(filters)
	customer_order = frappe.db.sql('''select o.name, o.order_date, o.status, o.payment_status, ifnull((concat(o.first_name,' ' ,o.last_name)),o.first_name) as full_name, 
		 o.order_subtotal,o.shipping_charges,o.total_tax_amount,o.total_amount, o.commission_amt, o.total_amount_for_vendor from 
		`tabOrder` o where o.naming_series !="SUB-ORD-" and o.docstatus=1 {condition} '''.format(condition=conditions),as_list=1)
	return customer_order

def get_conditions(filters):
	conditions=''
	if filters.get('from_date'):
		conditions+=' and o.order_date>="%s"' % filters.get('from_date')
	if filters.get('to_date'):
		conditions+=' and o.order_date<="%s"' % filters.get('to_date')
	if filters.get('restaurant'):
		conditions+=' and o.business="%s"' % filters.get('restaurant')
	if filters.get('status'):
		conditions+=' and o.status="%s"' % filters.get('status')
	if filters.get('payment_status'):
		conditions+=' and o.payment_status="%s"' % filters.get('payment_status') 
	return conditions

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
	condition=''
	if year:
		year=int(year)
	else:
		year=int(getdate().year)
	if status:
		condition+=' and status="'+status+'"'
	else:
		condition+=' and status="Completed"'		
	if month:
		st_date=datetime(year=year,day=int(day_list[0]),month=datetime.strptime(month, '%B').month)
		for item in day_list:
			parent=''
			result=frappe.get_list('Order',filters={'order_date':st_date},limit_page_length=500,ignore_permissions=False)
			if result:
				parent=",".join('"'+str(x.name)+'"' for x in result)
				data=frappe.db.sql('''select count(*) as count from `tabOrder` where naming_series !="SUB-ORD-" and name in ({parent}) {condition}'''.format(condition=condition,parent=parent),as_list=1)[0]
				values.append(data[0])
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
				data=frappe.db.sql('''select count(*) as count from `tabOrder` where naming_series !="SUB-ORD-" and name in ({parent}) {condition}'''.format(condition=condition,parent=parent),as_list=1)[0]
				values.append(data[0])
			else:
				values.append(0)	
	return values		

@frappe.whitelist()
def get_years():
	year_list = frappe.db.sql_list('''select distinct year(order_date) as years from `tabOrder` where naming_series !="SUB-ORD-"''')
	if not year_list:
		year_list = [getdate().year]
	return "\n".join(str(year) for year in year_list)
