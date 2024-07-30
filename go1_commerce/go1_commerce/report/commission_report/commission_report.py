# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate,nowdate,date_diff,add_to_date
from datetime import datetime, timedelta

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = commission_report(filters)
	chart=get_chart_data(filters)
	return columns, data ,None,chart


def get_columns():
	return[
		"Shop Name" + ":Data:120",
		"Owner" + ":Data:120",
		"Total Amount" + ":Currency:140",
		"Commission Amount" + ":Currency:140"
	]

def commission_report(filters):
	conditions = get_conditions(filters)
	if "Admin" in frappe.get_roles(frappe.session.user) or "Super Admin" in frappe.get_roles(frappe.session.user):
		customer_order = frappe.db.sql('''select (select restaurant_name from `tabBusiness` where name=o.business) as business_name,(select contact_person from `tabBusiness` where name=o.business) as contact_person,o.total_amount, o.commission_amt from 
			`tabVendor Orders` o left join `tabDrivers` d on d.name = o.driver left join `tabCustomers` c on c.name = o.customer left join `tabUser Social Login` s on s.parent = c.user_id and s.provider != 'frappe' where o.naming_series !="SUB-ORD-" and o.docstatus=1 {condition} '''.format(condition=conditions),as_list=1)
	else:
		if "Vendor" in frappe.get_roles(frappe.session.user):
			permission=frappe.db.sql('''select group_concat(concat('"',for_value,'"')) as business from `tabUser Permission` where user=%s and allow="Business"''',(frappe.session.user),as_dict=1)
			if permission and permission[0].business:
				conditions +=' and o.business in ({business})'.format(business=permission[0].business)
			else:
				frappe.throw(_('No {0} is mapped for your login.').format(_("Business")))
		customer_order = frappe.db.sql('''select (select restaurant_name from `tabBusiness` where name=o.business) as business_name,(select contact_person from `tabBusiness` where name=o.business) as contact_person,o.total_amount, o.commission_amt from 
			`tabVendor Orders` o left join `tabDrivers` d on d.name = o.driver left join `tabCustomers` c on c.name = o.customer left join `tabUser Social Login` s on s.parent = c.user_id and s.provider != 'frappe' where o.naming_series !="SUB-ORD-" and o.docstatus=1 {condition} group by o.name'''.format(condition=conditions),as_list=1)
	return customer_order


def get_conditions(filters):
	conditions=''
	from_date=filters.get('from_date') if filters.get('from_date') else None
	to_date=filters.get('to_date') if filters.get('to_date') else None
	if filters.get('status'):
		conditions+=' and o.status="%s"' % filters.get('status')
	if from_date and to_date:
		conditions+='and o.order_date >= "%s"' % from_date
		conditions+='and o.order_date <= "%s"' % to_date
	if filters.get('restaurant'):
		conditions += ' and o.business = "%s"' % filters.get('restaurant')
	return conditions

def get_chart_data(filters):
	status=filters.get('status') if filters.get('status') else None
	from_date=filters.get('from_date') if filters.get('from_date') else None
	to_date=filters.get('to_date') if filters.get('to_date') else None

	datasets=get_datasets(status,from_date,to_date)
	
	days_diff=(date_diff(to_date,from_date))
	label=get_label(status,from_date,to_date,days_diff)
	
	chart = {
		"data": {
			'labels': label,
			'datasets': datasets
		}
	}
	chart["type"] = "line"
	return chart

def get_datasets(status,from_date,to_date):
	datasets=[]
	if status:
		datasets.append({
			"title":status,
			"values":get_order_list(status,from_date,to_date)
			})
	else:
		order_status=frappe.db.get_all('Order Status')
		for item in order_status:			
			datasets.append({
				"title":_(item.name),
				"values":get_order_list(item.name,from_date,to_date)
				})
	return datasets

def get_label(status,from_date,to_date,days_diff):
	label=[]
	if days_diff<=31:
		dt_format='%d'
		days=frappe.db.sql_list(f"""SELECT
				*
			FROM (SELECT DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + 1 DAY) as dt FROM `tabVendor Orders` JOIN (SELECT @rownum := -1) r) a
			LEFT JOIN `tabVendor Orders` o on o.order_date=a.dt where o.naming_series !="SUB-ORD-" and a.dt<'{to_date}' group by a.dt""")
	elif days_diff<180:
		dt_format='%d %b'
		add_date=1
		interval='DAY'
		if days_diff>31 and days_diff<=60:
			add_date=2
		elif days_diff>60 and days_diff<=120:
			add_date=4
		elif days_diff>120 and days_diff<180:
			interval='DAY'
			add_date=7
			dt_format='%d %b'
		days=frappe.db.sql_list("""SELECT
				*
			FROM (SELECT DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + 1 {interval}) as dt, DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + {add_date} {interval}) as dt2 FROM `tabVendor Orders` JOIN (SELECT @rownum := -1) r) a
			LEFT JOIN `tabVendor Orders` o on o.order_date between a.dt and a.dt2 where o.naming_series !="SUB-ORD-" and a.dt<'{to_date}' group by a.dt""".format(from_date=from_date,to_date=to_date,add_date=add_date,dt_format=dt_format,interval=interval))
	elif days_diff<=366 and days_diff>180:
		add_date=1
		dt_format='%d %b'
		interval='MONTH'
		days=frappe.db.sql("""SELECT
			CONCAT(DATE_FORMAT(a.dt,'{dt_format}'),' - ',DATE_FORMAT(DATE_ADD(DATE_ADD(a.dt,INTERVAL -1 DAY),INTERVAL {add_date} {interval}),'{dt_format}'))
		FROM (SELECT DATE_ADD('{from_date}',INTERVAL @rownum := @rownum + 1 {interval}) as dt FROM `tabVendor Orders` JOIN (SELECT @rownum := -1) r) a
		LEFT JOIN `tabVendor Orders` o on o.order_date>=a.dt and o.order_date<DATE_ADD(dt,INTERVAL {add_date} {interval}) where o.naming_series !="SUB-ORD-" and a.dt<'{to_date}' group by a.dt""".format(from_date=from_date,to_date=to_date,add_date=add_date,dt_format=dt_format,interval=interval))
	elif days_diff<1500 and days_diff>366:
		add_date=6
		dt_format='%d-%m %y'
		interval='MONTH'
		days=frappe.db.sql_list("""SELECT
				*
			FROM (SELECT DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + 1 {interval}) as dt, DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + {add_date} {interval}) as dt2 FROM `tabOrder` JOIN (SELECT @rownum := -1) r) a
			LEFT JOIN `tabOrder` o on o.order_date>=a.dt and o.order_date<a.dt2 where o.naming_series !="SUB-ORD-" and a.dt<'{to_date}' group by a.dt""".format(from_date=from_date,to_date=to_date,add_date=add_date,dt_format=dt_format,interval=interval))
	else:
		add_date=1
		dt_format='%d %b %Y'
		interval='YEAR'
		days=frappe.db.sql_list("""SELECT
				*
			FROM (SELECT DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + 1 {interval}) as dt, DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + {add_date} {interval}) as dt2 FROM `tabVendor Orders` JOIN (SELECT @rownum := -1) r) a
			LEFT JOIN `tabVendor Orders` o on o.order_date>=a.dt and o.order_date<a.dt2 where o.naming_series !="SUB-ORD-" and a.dt<'{to_date}' group by a.dt""".format(from_date=from_date,to_date=to_date,add_date=add_date,dt_format=dt_format,interval=interval))
	label=days
	return label

def get_order_list(status,from_date,to_date):
	values=[]
	condition=''
	days_diff=(date_diff(to_date,from_date))
	if status:
		condition+=' and status="'+status+'"'
	else:
		condition+=' and status="Completed"'
	if "Vendor" in frappe.get_roles(frappe.session.user) and frappe.session.user!='Administrator':
		permission=frappe.db.sql('''select group_concat(concat('"',for_value,'"')) as business from `tabUser Permission` where user=%s and allow="Business"''',(frappe.session.user),as_dict=1)
		if permission and permission[0].business:
			condition+=' and `tabOrder`.business in ({business})'.format(business=permission[0].business)
		
	formated_date=from_date
	if days_diff<=31:
		result=frappe.db.sql_list("""SELECT
				ROUND(commission_amt, 2) 
			FROM (SELECT DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + 1 DAY) as dt FROM `tabVendor Orders` JOIN (SELECT @rownum := -1) r) a
			LEFT JOIN `tabVendor Orders` o on o.order_date=a.dt and o.docstatus=1 {condition} where o.naming_series !="SUB-ORD-" and a.dt<%(to_date)s group by a.dt""".format(condition=condition),{'from_date':from_date,'to_date':to_date})
	elif days_diff<180:		
		add_date=1
		interval='DAY'
		if days_diff>31 and days_diff<=60:
			formated_date=add_to_date(from_date,days=-1)
			add_date=2
		elif days_diff>60 and days_diff<=120:
			formated_date=add_to_date(from_date,days=-3)
			add_date=4
		elif days_diff>120 and days_diff<180:
			interval='DAY'
			add_date=7
			formated_date=add_to_date(from_date,days=-6)
		result=frappe.db.sql_list("""SELECT
				ROUND(commission_amt, 2) 
			FROM (SELECT DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + 1 {interval}) as dt, DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + {add_date} {interval}) as dt2 FROM `tabVendor Orders` JOIN (SELECT @rownum := -1) r) a
			LEFT JOIN `tabVendor Orders` o on o.order_date between a.dt and a.dt2 and o.docstatus=1 {condition} where o.naming_series !="SUB-ORD-" and a.dt<%(to_date)s group by a.dt""".format(condition=condition,add_date=add_date,interval=interval),{'from_date':formated_date,'to_date':to_date})
	elif days_diff<=366 and days_diff>180:
		interval='MONTH'
		add_date=1
		result=frappe.db.sql_list("""SELECT
				ROUND(commission_amt, 2) 
			FROM (SELECT DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + 1 {interval}) as dt FROM `tabVendor Orders` JOIN (SELECT @rownum := -1) r) a
			LEFT JOIN `tabVendor Orders` o on o.order_date>=a.dt and o.order_date<DATE_ADD(dt,INTERVAL {add_date} {interval}) and o.docstatus=1 {condition} where o.naming_series !="SUB-ORD-" and a.dt<%(to_date)s group by a.dt""".format(condition=condition,add_date=add_date,interval=interval),{'from_date':formated_date,'to_date':to_date})
	elif days_diff<1500 and days_diff>366:
		add_date=6
		interval='MONTH'
		result=frappe.db.sql_list("""SELECT
				ROUND(commission_amt, 2) 
			FROM (SELECT DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + 1 {interval}) as dt, DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + {add_date} {interval}) as dt2 FROM `tabVendor Orders` JOIN (SELECT @rownum := -1) r) a
			LEFT JOIN `tabVendor Orders` o on o.order_date>=a.dt and o.order_date<a.dt2 and o.docstatus=1 {condition} where o.naming_series !="SUB-ORD-" and a.dt<%(to_date)s group by a.dt""".format(condition=condition,add_date=add_date,interval=interval),{'from_date':formated_date,'to_date':to_date})
	else:
		add_date=1
		interval='YEAR'
		result=frappe.db.sql_list("""SELECT
				ROUND(commission_amt, 2) 
			FROM (SELECT DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + 1 {interval}) as dt, DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + {add_date} {interval}) as dt2 FROM `tabVendor Orders` JOIN (SELECT @rownum := -1) r) a
			LEFT JOIN `tabVendor Orders` o on o.order_date>=a.dt and o.order_date<a.dt2 and o.docstatus=1 {condition} where o.naming_series !="SUB-ORD-" and a.dt<%(to_date)s group by a.dt""".format(condition=condition,add_date=add_date,interval=interval),{'from_date':formated_date,'to_date':to_date})
	values=result
	return values		


@frappe.whitelist()
def get_years():
	year_list = frappe.db.sql_list('''select distinct year(order_date) as years from `tabOrder`''')
	if not year_list:
		year_list = [getdate().year]
	return "\n".join(str(year) for year in year_list)

@frappe.whitelist()
def get_curmonth():
	c_date=getdate(nowdate())
	today_with_time = datetime(
			year=c_date.year, 
			month=c_date.month,
			day=c_date.day,
	)
	month=today_with_time.strftime("%B")
	return month
