# Copyright (c) 2023, Tridots Tech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder import DocType, Field, Subquery, Function

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
	customers = DocType("Customers")
	route_sub_areas = DocType("Route Sub Areas")
	sub_area = DocType("Sub Area")
	orders = DocType("Order")
	orders_count_subquery = (
		frappe.qb.from_(orders, alias='ORD')
		.select(orders.customer.count())
		.where(orders.customer_email == Field("C.email"))
	)
	last_ordered_id_subquery = (
		frappe.qb.from_(orders, alias='ORD')
		.select(orders.name.max())
		.where(orders.customer_email == Field("C.email"))
	)
	query = (
		frappe.qb.from_(customers, alias='C')
		.inner_join(route_sub_areas, alias='RSA', on=route_sub_areas.parent == customers.route)
		.inner_join(sub_area, alias='SA', on=sub_area.sub_area_code == route_sub_areas.sub_area)
		.select(
			customers.name.as_("shopify_id"),
			customers.first_name.as_("first_name"),
			customers.last_name.as_("last_name"),
			customers.email.as_("email"),
			customers.phone.as_("phone"),
			customers.creation.as_("created"),
			customers.modified.as_("updated"),
			customers.store_front_image.as_("store_front_along"),
			customers.store_operator_image.as_("store_operator"),
			customers.store_closeup_image.as_("store_closeup"),
			customers.business_latitude.as_("latitude"),
			customers.business_longitude.as_("longitude"),
			customers.city,
			customers.state,
			customers.country,
			customers.zipcode,
			customers.gst_in.as_("gst_number"),
			Function("IFNULL", customers.route, 0).as_("route"),
			customers.center.as_("center_name"),
			customers.alternate_phone.as_("alternate_phone_number"),
			customers.business_landmark.as_("land_mark"),
			customers.business_zip.as_("pincode"),
			customers.address,
			customers.business_type.as_("customer_type"),
			customers.store_name,
			Function("CONCAT", customers.business_latitude, ',', customers.business_longitude).as_("shop_location"),
			sub_area.area_name.as_("area"),
			sub_area.sub_area.as_("sub_area"),
			customers.business_type.as_("center_type"),
			orders_count_subquery.as_("orders_count"),
			last_ordered_id_subquery.as_("last_ordered_id")
		)
		.groupby(customers.email)
	)
	result = query.run(as_dict=True)