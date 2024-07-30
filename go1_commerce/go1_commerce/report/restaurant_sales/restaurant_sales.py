# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe.permissions import has_permission
from frappe.utils import getdate,nowdate
from datetime import datetime, timedelta
import datetime
from datetime import date, datetime
from go1_commerce.utils.setup import get_settings_value_from_domain

days=[]
total_day=frappe.db.sql('''select day(last_day(curdate()))''',as_list=1)[0]
months=['January','February','March','April','May','June','July','August','September','October','November','December']
days=[x+1 for x in range(int(total_day[0]))]

def execute(filters=None):
	columns, data = [], []
	if not filters: filters={}
	enable_tip = get_settings_value_from_domain('Business Setting', 'enable_tip')
	columns=get_columns(enable_tip)
	data=get_values(filters, enable_tip)
	return columns, data ,None,None

def get_columns(enable_tip):
	columns = [
		_("Order Id") + ":Data:120",
		_("Order Date") + ":Date:120"				
	]
	if "Admin" in frappe.get_roles(frappe.session.user) or "Super Admin" in frappe.get_roles(frappe.session.user):
		columns+=[ 
			_("Business") + ":Link/Business:120",
			_("Business Name") + ":Data:120"
		]
	columns += [
		_("Order Type") + ":Data:120",
		_("Order Status") + ":Data:120",
		_("Customer Name") + ":Data:120"]
	if "Admin" in frappe.get_roles(frappe.session.user) or "Super Admin" in frappe.get_roles(frappe.session.user):
		columns += [_("Customer Email") + ":Data:200",
		_("Customer Phone") + ":Data:120"]
	columns += [
		_("Driver") + ":Data:120",
		_("Payment Method") + ":Data:200",
		_("Payment Status") + ":Data:120",
		_("Sub Total") + ":Currency:120",
		_("Shipping Charges") + ":Currency:120",
		_("Tax Amount") + ":Currency:120"]
	columns += [
		_("Service Provider Commission") + ":Currency:170",
		_("Total Amount For Restaurant") + ":Currency:170",
		_("Payment Gateway Charges") + ":Currency:170",
	]
	if enable_tip:
		columns += [_("Tip Amount") + ":Currency:120"]
	columns += [_("Total Amount") + ":Currency:120"]
	return columns

def get_values(filters, enable_tip):
	tip_field = ''
	if enable_tip:
		tip_field = ', tip_amount'
	conditions = get_conditions(filters)
	if "Admin" in frappe.get_roles(frappe.session.user) or "Super Admin" in frappe.get_roles(frappe.session.user):
		customer_order = frappe.db.sql('''select o.name, o.order_date, o.business, (select restaurant_name from `tabBusiness` where name=o.business) as business_name,o.shipping_method_name,o.status,ifnull((concat(o.first_name,' ' ,o.last_name)),o.first_name) as full_name, o.customer_email,o.phone, d.driver_name, o.payment_method_name, o.payment_status, 
			 o.order_subtotal,o.shipping_charges,o.total_tax_amount,(case when o.status = "Cancelled" then 0 else o.commission_amt end), (case when o.status = "Cancelled" then 0 else o.total_amount_for_vendor end),payment_gateway_charges {tip_field},o.total_amount from 
			`tabOrder` o left join `tabDrivers` d on d.name = o.driver where o.naming_series !="SUB-ORD-" and o.docstatus=1 {condition} '''.format(condition=conditions, tip_field=tip_field),as_list=1)
	else:
		if "Vendor" in frappe.get_roles(frappe.session.user):
			permission=frappe.db.sql('''select group_concat(concat('"',for_value,'"')) as business from `tabUser Permission` where user=%s and allow="Business"''',(frappe.session.user),as_dict=1)
			if permission and permission[0].business:
				conditions +=' and o.status <> "Cancelled" and o.business in ({business})'.format(business=permission[0].business)
			else:
				frappe.throw(_('No {0} is mapped for your login.').format(_("Business")))
		customer_order = frappe.db.sql('''select o.name, o.order_date,o.shipping_method_name,o.status,ifnull((concat(o.first_name,' ' ,o.last_name)),o.first_name) as full_name, d.driver_name,  o.payment_method_name,o.payment_status, 
			 o.order_subtotal,o.shipping_charges,o.total_tax_amount,(case when o.status = "Cancelled" then 0 else o.commission_amt end), (case when o.status = "Cancelled" then 0 else o.total_amount_for_vendor end),payment_gateway_charges {tip_field}, o.total_amount from 
			`tabOrder` o left join `tabDrivers` d on d.name = o.driver where o.naming_series !="SUB-ORD-" and o.docstatus=1 {condition} '''.format(condition=conditions, tip_field=tip_field),as_list=1)
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
	return conditions

def get_chart_data(filters):
	status=filters.get('status') if filters.get('status') else None
	year=filters.get('year') if filters.get('year') else None
	month=filters.get('month') if filters.get('month') else None
	
	datasets=[]
	if status:
		datasets.append({
			"title":status,
			"values":get_order_list(status,year,month,months,days)
			})
	else:
		order_status=frappe.db.get_all('Order Status')
		for item in order_status:
			datasets.append({
				"title":_(item.name),
				"values":get_order_list(item.name,year,month,months,days)
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
	if status:
		condition+=' and status="'+status+'"'
	if month:
		st_date=datetime(year=int(year),day=int(day_list[0]),month=datetime.strptime(month, '%B').month)
		for item in day_list:
			parent=''
			result=frappe.get_list('Order',filters={'order_date':st_date},limit_page_length=500,ignore_permissions=False)
			if result:
				parent=",".join('"'+str(x.name)+'"' for x in result)
				data=frappe.db.sql('''select sum(total_amount) as sum1 from `tabOrder` where naming_series !="SUB-ORD-" and name in ({parent}) {condition}'''.format(condition=condition,parent=parent),as_list=1)[0]
				values.append(data[0])
			else:
				values.append(0)
			st_date=st_date+timedelta(days=1)
	else:
		for item in month_list:
			st_date=datetime(year=int(year),day=1,month=datetime.strptime(item,'%B').month)
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
				data=frappe.db.sql('''select sum(total_amount) as sum1 from `tabOrder` where naming_series !="SUB-ORD-" and name in ({parent}) {condition}'''.format(condition=condition,parent=parent),as_list=1)[0]
				values.append(data[0])
			else:
				values.append(0)	
	return values		

@frappe.whitelist(allow_guest=True)
def check_domain(domain_name):
	try:
		from frappe.core.doctype.domain_settings.domain_settings import get_active_domains
		domains_list=get_active_domains()
		domains=frappe.cache().hget('domains','domain_constants')
		if not domains:
			domains=get_domains_data()
		if domains[domain_name] in domains_list:
			return True
		return False
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "go1_commerce.go1_commerce.api.check_domain")

@frappe.whitelist()
def get_years():
	year_list = frappe.db.sql_list('''select distinct year(order_date) as years from `tabOrder` where naming_series !="SUB-ORD-"''')
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