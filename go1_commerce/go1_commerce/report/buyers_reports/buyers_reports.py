# Copyright (c) 2023, Tridots Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = get_columns(), get_datas(filters)
	return columns, data

def get_columns():
	col__ = []
	col__.append(_("Shopify Id")+":Data:100")
	col__.append(_("First Name")+":Data:150")
	col__.append(_("Last Name")+":Data:100")
	col__.append(_("Email")+":Email:200")
	col__.append(_("Phone")+":Phone:150")
	col__.append(_("Created")+":Date:150")
	col__.append(_("Updated")+":Date:150")
	col__.append(_("Orders Count")+":Data:150")
	col__.append(_("Last Ordered Id")+":Data:150")
	col__.append(_("Shop Location")+":Data:200")
	col__.append(_("Route")+":Data:150")
	col__.append(_("Area")+":Data:150")
	col__.append(_("Sub Area")+":Data:200")
	col__.append(_("Store Front Along")+":Attach Image:300")
	col__.append(_("Store Operator")+":Attach Image:300")
	col__.append(_("Store Close Up")+":Attach Image:300")
	col__.append(_("Store Name")+":Data:150")
	col__.append(_("Longitude")+":Geolocation:150")
	col__.append(_("Latitude")+":Geolocation:150")
	col__.append(_("Center Name")+":Data:150")
	col__.append(_("Center Type")+":Data:150")
	col__.append(_("Pincode")+":Data:150")
	col__.append(_("City")+":Data:150")
	col__.append(_("State")+":Data:150")
	col__.append(_("Country")+":Data:150")
	col__.append(_("Alternate Phone Number")+":Phone:150")
	col__.append(_("GST Number")+":Data:150")
	col__.append(_("Address")+":Data:300")
	col__.append(_("Customer Type")+":Data:150")
	col__.append(_("Establishment Year")+":Data:150")

	return col__

def get_datas(filters):
	
	query = """
			SELECT C.name shopify_id,C.first_name first_name,C.last_name last_name,C.email email,
			C.phone phone,C.creation created,C.modified updated,
			C.store_front_image store_front_along,C.store_operator_image store_operator,
			C.store_closeup_image store_closeup,C.business_latitude latitude,
			C.business_longitude longitude,
			C.city,C.state,C.country,C.zipcode,C.gst_in gst_number,
			(CASE WHEN C.route IS NOT NULL THEN C.route ELSE 0 END)route,
			C.center center_name,C.alternate_phone alternate_phone_number,
			C.business_landmark land_mark,C.business_zip pincode,
			C.address address,C.business_type customer_type,C.store_name store_name,
			CONCAT(C.business_latitude,',',C.business_longitude)shop_location,
			SA.area_name area,SA.sub_area sub_area,C.business_type center_type,
			(SELECT COUNT(ORD.customer) FROM `tabOrder` ORD WHERE ORD.customer_email = C.email)orders_count,
			(SELECT MAX(ORD.name) FROM `tabOrder` ORD WHERE ORD.customer_email = C.email)last_ordered_id
			FROM `tabCustomers` C
			INNER JOIN `tabRoute Sub Areas` RSA ON RSA.parent = C.route
			INNER JOIN `tabSub Area` SA ON SA.sub_area_code = RSA.sub_area
			GROUP BY C.email
		"""
	res = frappe.db.sql(query,as_dict=1)
	return res