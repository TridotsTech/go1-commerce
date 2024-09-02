# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate,nowdate,date_diff,add_to_date
from datetime import datetime, timedelta
from frappe.query_builder import DocType, Count, Sum, Function

def execute(filters=None):
	columns, data = [], []
	if not filters: filters={}
	columns=get_columns()
	data=get_values(filters)
	chart=get_chart_data(filters)
	return columns, data ,None,chart

def get_columns():
	columns = [
		{
			"label": _("Order Id"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Order",
			"width": 120
		},
		{
			"label": _("Order Date"),
			"fieldname": "order_date",
			"fieldtype": "Date",
			"width": 120
		}
	]
	columns += [
		{
			"label": _("Driver"),
			"fieldtype": "Data",
			"fieldname": "driver_name",
			"width": 120
		},
		]

	columns += [
		{
			"label": _("Order Status"),
			"fieldtype": "Data",
			"fieldname": "status",
			"width": 120
		},
		{
			"label": _("Customer Name"),
			"fieldtype": "Data",
			"fieldname": "full_name",
			"width": 120
		},
		{
			"label": _("Social Media Source"),
			"fieldtype": "Data",
			"fieldname": "provider",
			"width": 150
		},
		{
			"label": _("Payment Status"),
			"fieldtype": "Data",
			"fieldname": "payment_status",
			"width": 120
		},
		{
			"label": _("Order Type"),
			"fieldtype": "Data",
			"fieldname": "shipping_method_name",
			"width": 120
		},
		{
			"label": _("Payment Type"),
			"fieldtype": "Data",
			"fieldname": "payment_method_name",
			"width": 120
		}
	]
	columns += [
		{
			"label": _("Sub Total"),
			"fieldtype": "Currency",
			"fieldname": "order_subtotal",
			"width": 120
		},
		{
			"label": _("Discount"),
			"fieldtype": "Currency",
			"fieldname": "discount",
			"width": 120
		},
		{
			"label": _("Shipping Charges"),
			"fieldtype": "Currency",
			"fieldname": "shipping_charges",
			"width": 120
		},
		{
			"label": _("Tax Amount"),
			"fieldtype": "Currency",
			"fieldname": "total_tax_amount",
			"width": 120
		}
	]
	columns += [
		{
			"label": _("Payment Gateway Charges"),
			"fieldtype": "Currency",
			"fieldname": "payment_gateway_charges",
			"width": 120
		},
		{
			"label": _("Commission Amount"),
			"fieldtype": "Currency",
			"fieldname": "commission_amt",
			"width": 120
		},
		{
			"label": _("Amount For Vendor"),
			"fieldtype": "Currency",
			"fieldname": "total_amount_for_vendor",
			"width": 120
		},
		{
			"label": _("Total Amount"),
			"fieldtype": "Currency",
			"fieldname": "total_amount",
			"width": 120
		}
	]
	return columns

def get_values(filters):
	Order = DocType('Order')
	Drivers = DocType('Drivers')
	Customers = DocType('Customers')
	UserSocialLogin = DocType('User Social Login')
	
	conditions = []
	if filters.get('status'):
		conditions.append(Order.status == filters.get('status'))
	if filters.get('from_date') and filters.get('to_date'):
		conditions.append(Order.order_date >= filters.get('from_date'))
		conditions.append(Order.order_date <= filters.get('to_date'))
	query = (
		frappe.qb.from_(Order)
		.left_join(Drivers).on(Drivers.name == Order.driver)
		.left_join(Customers).on(Customers.name == Order.customer)
		.left_join(UserSocialLogin).on((UserSocialLogin.parent == Customers.user_id) & (UserSocialLogin.provider != 'frappe'))
		.select(
			Order.name,
			Order.order_date,
			Drivers.driver_name,
			Order.payment_status,
			Order.shipping_method_name,
			Order.payment_method_name,
			Customers.full_name,
			UserSocialLogin.provider,
			Order.order_subtotal,
			Order.cash_collected_mode,
			Order.origin_type,
			Order.discount,
			Order.shipping_charges,
			Order.total_tax_amount,
			Order.payment_gateway_charges,
			frappe.qb.from_(f'CASE WHEN o.status = "Cancelled" THEN 0 ELSE o.commission_amt END').as_('commission_amt'),
			Order.total_amount_for_vendor,
			Order.total_amount
		)
		.where(
			(Order.naming_series != "SUB-ORD-") &
			(Order.docstatus == 1) &
			*conditions
		)
	)
	if "Admin" not in frappe.get_roles(frappe.session.user) and "Super Admin" not in frappe.get_roles(frappe.session.user):
		query = query.groupby(Order.name)
	customer_order = query.run(as_dict=True)
	return customer_order

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
		days=frappe.db.sql_list("""SELECT DATE_FORMAT(a.dt,'%d')
			FROM
				(SELECT DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + 1 DAY) AS dt
				FROM `tabOrder`
				JOIN
				(SELECT @rownum := -1) r) a
			LEFT JOIN `tabOrder` o ON o.order_date=a.dt
			WHERE o.naming_series !="SUB-ORD-"
			AND a.dt<'{to_date}'
			GROUP BY a.dt""".format(from_date=from_date,to_date=to_date))
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
		days=frappe.db.sql_list("""SELECT CONCAT(DATE_FORMAT(a.dt,'{dt_format}'),' - ',DATE_FORMAT(a.dt2,'{dt_format}'))
			FROM
				(SELECT DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + 1 {interval}) AS dt,
					DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + {add_date} {interval}) AS dt2
				FROM `tabOrder`
				JOIN
				(SELECT @rownum := -1) r) a
			LEFT JOIN `tabOrder` o ON o.order_date BETWEEN a.dt AND a.dt2
			WHERE o.naming_series !="SUB-ORD-"
			AND a.dt<'{to_date}'
			GROUP BY a.dt""".format(from_date=from_date,to_date=to_date,add_date=add_date,dt_format=dt_format,interval=interval))
	elif days_diff<=366 and days_diff>180:
		add_date=1
		dt_format='%d %b'
		interval='MONTH'
		days=frappe.db.sql("""SELECT CONCAT(DATE_FORMAT(a.dt,'{dt_format}'),' - ',DATE_FORMAT(DATE_ADD(DATE_ADD(a.dt,INTERVAL -1 DAY),INTERVAL {add_date} {interval}),'{dt_format}'))
			FROM
				(SELECT DATE_ADD('{from_date}',INTERVAL @rownum := @rownum + 1 {interval}) AS dt
				FROM `tabOrder`
				JOIN
				(SELECT @rownum := -1) r) a
			LEFT JOIN `tabOrder` o ON o.order_date>=a.dt
			AND o.order_date<DATE_ADD(dt,INTERVAL {add_date} {interval})
			WHERE o.naming_series !="SUB-ORD-"
			AND a.dt<'{to_date}'
			GROUP BY a.dt""".format(from_date=from_date,to_date=to_date,add_date=add_date,dt_format=dt_format,interval=interval))
	elif days_diff<1500 and days_diff>366:
		add_date=6
		dt_format='%d-%m %y'
		interval='MONTH'
		days=frappe.db.sql_list("""SELECT CONCAT(DATE_FORMAT(a.dt,'{dt_format}'),' - ',DATE_FORMAT(a.dt2,'{dt_format}'))
			FROM
				(SELECT DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + 1 {interval}) AS dt,
					DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + {add_date} {interval}) AS dt2
				FROM `tabOrder`
				JOIN
				(SELECT @rownum := -1) r) a
			LEFT JOIN `tabOrder` o ON o.order_date>=a.dt
			AND o.order_date<a.dt2
			WHERE o.naming_series !="SUB-ORD-"
			AND a.dt<'{to_date}'
			GROUP BY a.dt""".format(from_date=from_date,to_date=to_date,add_date=add_date,dt_format=dt_format,interval=interval))
	else:
		add_date=1
		dt_format='%d %b %Y'
		interval='YEAR'
		days=frappe.db.sql_list("""SELECT CONCAT(DATE_FORMAT(a.dt,'{dt_format}'),' - ',DATE_FORMAT(DATE_ADD(DATE_ADD(a.dt,INTERVAL -1 DAY),INTERVAL {add_date} {interval}),'{dt_format}'))
			FROM
				(SELECT DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + 1 {interval}) AS dt,
					DATE_ADD('{from_date}', INTERVAL @rownum := @rownum + {add_date} {interval}) AS dt2
				FROM `tabOrder`
				JOIN
				(SELECT @rownum := -1) r) a
			LEFT JOIN `tabOrder` o ON o.order_date>=a.dt
			AND o.order_date<a.dt2
			WHERE o.naming_series !="SUB-ORD-"
			AND a.dt<'{to_date}'
			GROUP BY a.dt""".format(from_date=from_date,to_date=to_date,add_date=add_date,dt_format=dt_format,interval=interval))
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
	formated_date=from_date
	if days_diff<=31:
		result=frappe.db.sql_list("""SELECT ROUND(SUM(commission_amt), 2)
			FROM
				(SELECT DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + 1 DAY) AS dt
				FROM `tabOrder`
				JOIN
				(SELECT @rownum := -1) r) a
			LEFT JOIN `tabOrder` o ON o.order_date=a.dt
			AND o.docstatus=1 {condition}
			WHERE o.naming_series !="SUB-ORD-"
			AND a.dt<%(to_date)s
			GROUP BY a.dt""".format(condition=condition),{'from_date':from_date,'to_date':to_date})
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
		result=frappe.db.sql_list("""SELECT ROUND(SUM(commission_amt), 2)
			FROM
				(SELECT DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + 1 {interval}) AS dt,
					DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + {add_date} {interval}) AS dt2
				FROM `tabOrder`
				JOIN
				(SELECT @rownum := -1) r) a
			LEFT JOIN `tabOrder` o ON o.order_date BETWEEN a.dt AND a.dt2
			AND o.docstatus=1 {condition}
			WHERE o.naming_series !="SUB-ORD-"
			AND a.dt<%(to_date)s
			GROUP BY a.dt""".format(condition=condition,add_date=add_date,interval=interval),{'from_date':formated_date,'to_date':to_date})
	elif days_diff<=366 and days_diff>180:
		interval='MONTH'
		add_date=1
		result=frappe.db.sql_list("""SELECT ROUND(SUM(commission_amt), 2)
			FROM
				(SELECT DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + 1 {interval}) AS dt
				FROM `tabOrder`
				JOIN
				(SELECT @rownum := -1) r) a
			LEFT JOIN `tabOrder` o ON o.order_date>=a.dt
			AND o.order_date<DATE_ADD(dt,INTERVAL {add_date} {interval})
			AND o.docstatus=1 {condition}
			WHERE o.naming_series !="SUB-ORD-"
			AND a.dt<%(to_date)s
			GROUP BY a.dt""".format(condition=condition,add_date=add_date,interval=interval),{'from_date':formated_date,'to_date':to_date})
	elif days_diff<1500 and days_diff>366:
		add_date=6
		interval='MONTH'
		result=frappe.db.sql_list("""SELECT ROUND(SUM(commission_amt), 2)
			FROM
				(SELECT DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + 1 {interval}) AS dt,
					DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + {add_date} {interval}) AS dt2
				FROM `tabOrder`
				JOIN
				(SELECT @rownum := -1) r) a
			LEFT JOIN `tabOrder` o ON o.order_date>=a.dt
			AND o.order_date<a.dt2
			AND o.docstatus=1 {condition}
			WHERE o.naming_series !="SUB-ORD-"
			AND a.dt<%(to_date)s
			GROUP BY a.dt""".format(condition=condition,add_date=add_date,interval=interval),{'from_date':formated_date,'to_date':to_date})
	else:
		add_date=1
		interval='YEAR'
		result=frappe.db.sql_list("""SELECT ROUND(SUM(commission_amt), 2)
			FROM
				(SELECT DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + 1 {interval}) AS dt,
					DATE_ADD(%(from_date)s, INTERVAL @rownum := @rownum + {add_date} {interval}) AS dt2
				FROM `tabOrder`
				JOIN
				(SELECT @rownum := -1) r) a
			LEFT JOIN `tabOrder` o ON o.order_date>=a.dt
			AND o.order_date<a.dt2
			AND o.docstatus=1 {condition}
			WHERE o.naming_series !="SUB-ORD-"
			AND a.dt<%(to_date)s
			GROUP BY a.dt""".format(condition=condition,add_date=add_date,interval=interval),{'from_date':formated_date,'to_date':to_date})
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