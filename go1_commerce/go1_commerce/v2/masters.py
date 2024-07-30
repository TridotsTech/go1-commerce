from __future__ import unicode_literals, print_function
import frappe, json, os
from frappe import _
from frappe.utils import get_datetime, getdate
from datetime import datetime
from go1_commerce.utils.utils import other_exception,get_today_date

def failed_msg_resp(message,code = None):
	frappe.response.http_status_code = code if code else 404
	return {"status":"Failed",
         	"error_message":message,"data":[]}

def failed_msg_400_resp(message):
	frappe.response.http_status_code = 400
	return {"status":"Failed",
			"error_message":message}

@frappe.whitelist()
def get_countries():
	try:
		query = """ SELECT name,time_zones FROM `tabCountry` WHERE docstatus=0 """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data=data)
		else:
			return failed_msg_resp("The Contry list not found")
	except Exception:
		other_exception("country get_country_list")


@frappe.whitelist()
def get_states(country=None):
	try:
		condition = ""
		if country:
			condition = " AND country ='"+country+"'"
		query = """ SELECT name,country FROM `tabState` WHERE docstatus=0
	                {condition}	""".format(condition=condition)
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data=data)
		else:
			return failed_msg_resp("The state list not found")
	except Exception:
		other_exception("state get_state_list")

@frappe.whitelist()
def get_cities(state=None):
	try:
		condition = ""
		if state:
			condition = " AND state ='"+state+"'"
		query = """ SELECT name,state FROM `tabCity` WHERE docstatus=0
	                {condition} """.format(condition=condition)
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The city list not found")
	except Exception:
		other_exception("city get_city_list")

@frappe.whitelist(allow_guest=True)
def get_centres(city=None):
	try:
		condition = ""
		if city:
			condition = " AND city ='"+city+"'"
		query = """ SELECT name,approval_status,center_code,contact_name,mobile_no,
	                owned_by,city,state,country,pin FROM `tabWarehouse` 
		            WHERE docstatus=0 AND disabled=0 AND allow_product_listing=1 
		            AND approval_status='Approved'
		            AND fulfillment_center=1 {condition} 
					""".format(condition=condition)
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The centres list not found")
	except Exception:
		other_exception("zone get_centres")

@frappe.whitelist()
def get_zones(city=None):
	try:
		condition = ""
		if city:
			condition = " AND city ='"+city+"'"
		query = """ SELECT name,zone_name,city,state FROM `tabZone` 
					WHERE docstatus=0 {condition} 
					""".format(condition=condition)
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The zones list not found")
	except Exception:
		other_exception("zone get_zone_list")
		
@frappe.whitelist()
def get_areas(zone_name=None):
	try:
		condition = ""
		if zone_name:
			condition = " AND zone_name ='"+zone_name+"'"
		query = """ SELECT name,area,zone_name,city,state FROM `tabArea` 
	                WHERE docstatus=0 {condition} 
					""".format(condition=condition)
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The areas list not found")
	except Exception:
		other_exception("area get_area_list")

@frappe.whitelist()
def get_subareas(area=None):
	try:
		condition = ""
		if area:
			condition = " AND area ='"+area+"'"
		query = """ SELECT name,sub_area,area,area_name,city,zone 
	                FROM `tabSub Area` WHERE docstatus=0 {condition} 
		            """.format(condition=condition)
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The subareas list not found")
	except Exception:
		other_exception("subarea get_subarea_list")

@frappe.whitelist()
def get_routes(centre=None):
	try:
		condition = ""
		if centre:
			condition = " AND centre ='"+centre+"'"
		query = """ SELECT name,centre,route_name FROM `tabRoute` WHERE docstatus=0 
	                {condition} """.format(condition=condition)
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The route list not found")
	except Exception:
		other_exception("route get_route_list")


		
@frappe.whitelist()
def get_seller_types():
	try:
		query = """ SELECT name FROM `tabSeller Type` 
		            WHERE docstatus=0 """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The seller_types list not found")
	except Exception:
		other_exception("get_seller_type")

@frappe.whitelist()
def get_cancel_reasons():
	try:
		query = """ SELECT name FROM `tabOrder Cancel Reason`"""
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The cancel_reasons list not found")
	except Exception:
		other_exception("get_cancel_reasons")

@frappe.whitelist()
def get_lead_dropped_reasons():
	try:
		query = """ SELECT name FROM `tabReason For Lead`"""
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The lead_dropped_reasons list not found")
	except Exception:
		other_exception("get_lead_dropped_reasons")

@frappe.whitelist()
def get_buyer_business_type():
	try:
		query = """ SELECT name FROM `tabBuyer Business Type` 
		            WHERE docstatus=0 """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The buyer_business_type list not found")
	except Exception:
		other_exception("get_buyer_business_type")

@frappe.whitelist()
def get_purpose_of_visits():
	try:
		query = """ SELECT name FROM `tabVisit of Purpose` 
		            WHERE docstatus=0 """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The purpose_of_visits list not found")
	except Exception:
		other_exception("get_purpose_of_visit")

@frappe.whitelist()
def get_customer_purpose_of_visits():
	try:
		query = """ SELECT name,vis_of_purps FROM `tabVisit of Purpose` 
		            WHERE type="Customer" ORDER BY name  """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="vis_of_purps",value="name",data = data)
		else:
			return failed_msg_resp("The customer_purpose_of_visits list not found")
	except Exception:
		other_exception("get_customer_purpose_of_visits")

@frappe.whitelist()
def get_lead_purpose_of_visits():
	try:
		query = """ SELECT name,vis_of_purps FROM `tabVisit of Purpose` 
		            WHERE type="Lead" ORDER BY name """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="vis_of_purps",value="name",data = data)
		else:
			return failed_msg_resp("The lead_purpose_of_visits list not found")
	except Exception:
		other_exception("get_lead_purpose_of_visits")

@frappe.whitelist()
def get_visit_status():
	try:
		query = """ SELECT name FROM `tabVisit Status` 
		            WHERE 1=1 """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The visit_status list not found")
	except Exception:
		other_exception("get_visit_status")

@frappe.whitelist()
def get_unsuccessful_delivered_reasons():
	try:
		query = """ SELECT name FROM `tabReturn Request Reasons` 
		            WHERE docstatus=0 and enable_unsful_dc_order =1"""
		return format_output(label="name",value="name",data=frappe.db.sql(query,as_dict=1))
	except Exception:
		other_exception("get_return_request_reasons")
		
@frappe.whitelist()
def get_lead_source():
	try:
		query = """ SELECT name FROM `tabLead Source` 
		            WHERE 1=1 """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The lead_source list not found")
	except Exception:
		other_exception("get_visit_status")

@frappe.whitelist()
def get_payment_methods():
	try:
		query = """ SELECT name FROM `tabPayment Method` 
		            WHERE docstatus=0 """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The payment_methods list not found")
	except Exception:
		other_exception("get_mode_of_payments")

@frappe.whitelist()
def get_payment_modes():
	try:
		query = """ SELECT name FROM `tabMode Of Payments`"""
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The payment_modes list not found")
	except Exception:
		other_exception("get_payment_modes")
@frappe.whitelist()
def get_return_request_reasons():
	try:
		query = """ SELECT name FROM `tabReturn Request Reasons` 
		            WHERE docstatus=0 """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The return_request_reasons list not found")
	except Exception:
		other_exception("get_return_request_reasons")

@frappe.whitelist()
def get_replacement_request_reasons():
	try:
		query = """ SELECT name FROM `tabReplacement Request Reasons` 
		            WHERE docstatus=0 """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The replacement_request_reasons list not found")
	except Exception:
		other_exception("get_replacement_request_reasons")

@frappe.whitelist()
def get_order_status():
	try:
		query = """ SELECT name FROM `tabOrder Status` 
		            WHERE docstatus=0 """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The order_status list not found")
	except Exception:
		other_exception("get_get_order_status")

@frappe.whitelist()
def get_return_request_status():
	try:
		query = """ SELECT name FROM `tabReturn Request Status` 
		            WHERE docstatus=0 """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The return_request_status list not found")
	except Exception:
		other_exception("get_Return_Request_Status")

@frappe.whitelist()
def get_replacement_request_status():
	try:
		query = """ SELECT name FROM `tabReplacement Status` 
		            WHERE docstatus=0 """
		data = frappe.db.sql(query,as_dict=1)
		if data:
			return format_output(label="name",value="name",data = data)
		else:
			return failed_msg_resp("The replacement_request_status list not found")
	except Exception:
		other_exception("get_replacement_request_status")

@frappe.whitelist()
def get_weekly_offs():
	path = frappe.get_module_path("go1_commerce")
	masters_file_path = os.path.join(path, "masters.json")
	
	if os.path.exists(masters_file_path):
		with open(masters_file_path) as jsonFile:
			jsonObject = json.load(jsonFile)
			jsonFile.close()
			data = jsonObject['weekly_off']
			if data:
				return format_output1(data)
			else:
				return failed_msg_resp("The weekly_off list not found")


@frappe.whitelist()
def get_customer_status():
	path = frappe.get_module_path("go1_commerce")
	masters_file_path = os.path.join(path, "masters.json")
	if os.path.exists(masters_file_path):
		with open(masters_file_path) as jsonFile:
			jsonObject = json.load(jsonFile)
			jsonFile.close()
			data = jsonObject['customser_status']
			if data:
				return format_output1(data)
			else:
				return failed_msg_resp("The customser_status list not found")



@frappe.whitelist()
def get_types_of_document():
	path = frappe.get_module_path("go1_commerce")
	masters_file_path = os.path.join(path, "masters.json")
	if os.path.exists(masters_file_path):
		with open(masters_file_path) as jsonFile:
			jsonObject = json.load(jsonFile)
			jsonFile.close()
			data = jsonObject['type_of_document']
			if data:
				return format_output1(data)
			else:
				return failed_msg_resp("The type_of_document list not found")

@frappe.whitelist()
def get_kyc_status():
	path = frappe.get_module_path("go1_commerce")
	masters_file_path = os.path.join(path, "masters.json")
	if os.path.exists(masters_file_path):
		with open(masters_file_path) as jsonFile:
			jsonObject = json.load(jsonFile)
			jsonFile.close()
			data = jsonObject['kyc_status']
			if data:
				return format_output1(data)
			else:
				return failed_msg_resp("The kys_status list not found")

@frappe.whitelist()
def get_address_proof_document_types():
	path = frappe.get_module_path("go1_commerce")
	masters_file_path = os.path.join(path, "masters.json")
	if os.path.exists(masters_file_path):
		with open(masters_file_path) as jsonFile:
			jsonObject = json.load(jsonFile)
			jsonFile.close()
			data = jsonObject['kys_address_proof']
			if data:
				return format_output1(data)
			else:
				return failed_msg_resp("The kys_address_proof list not found")

@frappe.whitelist()
def get_personal_proof_document_types():
	path = frappe.get_module_path("go1_commerce")
	masters_file_path = os.path.join(path, "masters.json")
	if os.path.exists(masters_file_path):
		with open(masters_file_path) as jsonFile:
			jsonObject = json.load(jsonFile)
			jsonFile.close()
			data = jsonObject['kys_person_proof']
			if data:
				return format_output1(data)
			else:
				return failed_msg_resp("The personal_proof_document_types list not found")
		
@frappe.whitelist()
def get_business_document_types():
	path = frappe.get_module_path("go1_commerce")
	masters_file_path = os.path.join(path, "masters.json")
	if os.path.exists(masters_file_path):
		with open(masters_file_path) as jsonFile:
			jsonObject = json.load(jsonFile)
			jsonFile.close()
			data = jsonObject['kys_business_document']
			if data:
				return format_output1(data)
			else:
				return failed_msg_resp("The business_document_types list not found")

@frappe.whitelist()
def get_lead_status():
	path = frappe.get_module_path("go1_commerce")
	masters_file_path = os.path.join(path, "masters.json")
	if os.path.exists(masters_file_path):
		with open(masters_file_path) as jsonFile:
			jsonObject = json.load(jsonFile)
			jsonFile.close()
			data = jsonObject['lead_status']
			if data:
				return format_output1(data)
			else:
				return failed_msg_resp("The lead_status list not found")

@frappe.whitelist()
def get_store_classes():
	path = frappe.get_module_path("go1_commerce")
	masters_file_path = os.path.join(path, "masters.json")
	
	if os.path.exists(masters_file_path):
		with open(masters_file_path) as jsonFile:
			jsonObject = json.load(jsonFile)
			jsonFile.close()
			data = jsonObject['store_class']
			if data:
				return format_output1(data) 
			else:
				return failed_msg_resp("The store_class list not found")

def format_output(label,value,data):
	return_data = []
	for x in data:
		return_data.append({"label":x[label],"value":x[value]})
	return {"status":"Success","success_message":"","data":return_data}

def format_output_data(label,value,data):
	return_data = []
	for x in data:
		return_data.append({"label":x[label],"value":x[value]})
	return return_data
def format_output1(data):
	frappe.local.response.http_status_code = 200
	return {"status":"Success","success_message":"","data":data}


@frappe.whitelist()
def upload_file(**kwargs):
	try:
		if not kwargs.get('file_name'):
			failed_msg_400_resp("The file_name is missing.")
		if not kwargs.get('content'):
			failed_msg_400_resp("The content is missing.")
		from go1_commerce.utils.utils \
			import get_uploaded_file_content,validation_exception,permission_exception
		res = frappe.get_doc({
				"doctype": "File",
				"file_name": kwargs.get('file_name'),
				"is_private": 0,
				"content": get_uploaded_file_content(kwargs.get('content'))
				}).insert(ignore_permissions=True)
		res.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.local.response["status"] = "Success"	
		frappe.local.response["file_url"] = res.file_url	
	except frappe.exceptions.ValidationError:
		validation_exception()
	except frappe.exceptions.PermissionError:
		permission_exception()
	except Exception:
		other_exception("masters upload_file")



@frappe.whitelist()
def get_checkout_settings():
	category_condition = ship_condition = ""
	default_delivery_slots = []
	delivery_list = frappe.db.sql(
				    '''SELECT SH.parent FROM `tabDelivery Slot Shipping Method` SH
					INNER JOIN `tabDelivery Setting` DS ON DS.name = SH.parent
					WHERE enable=1 {0}'''.format(ship_condition), as_dict=1)
	for x in delivery_list:
		if not frappe.db.get_all("Delivery Slot Category",
	     	   filters={"parent":x.parent}):
			(dates_lists, blocked_day_list) = get_delivery_slots_list(x.parent)
			x.dates_lists = dates_lists
			x.blocked_day_list = blocked_day_list
			for available_day in x.dates_lists:
				if getdate(str(available_day.get("date")).split(" ")[0]) in\
					 blocked_day_list:
					available_day["allowed"] = 0
				else:
					available_day["allowed"] = 1
			default_delivery_slots.append(x)

	delivery_slots_settings = []
	if default_delivery_slots:
		for x in default_delivery_slots[0].dates_lists:
			slots_list = []
			for s in x.get("slots"):
				slots_list.append({"from_time":s.get("from_time"),
								 "to_time":s.get("to_time"),
								 "slot_label":s.get("time_format"),
								 })
			delivery_slots_settings.append({
				"date":getdate(x.get("date")),"format_date":x.get("format_date"),
				"slots":slots_list
				})
	if delivery_slots_settings:
		frappe.local.response.http_status_code = 200
		data = {"delivery_slots":delivery_slots_settings,
				"market_place_fees":frappe.db.get_all("Market Place Fee",
												fields=["fee_name","fee_amount","fee_type","fee_percentage"])}
		return format_output1(data)
	else:
		return failed_msg_resp("The checkout_settings not found")
	
def get_slot_lists(slots = None, date = None, min_time = None, restrict = None, max_booking_slot = None):
	if not slots:
		failed_msg_400_resp("The slots is missing.")
	if not date:
		failed_msg_400_resp("The date is missing.")
	if not min_time:
		failed_msg_400_resp("The min_time is missing.")
	if not max_booking_slot:
		failed_msg_400_resp("The max_booking_slot is missing.")
	slot_list = []
	dtfmt = '%Y-%m-%d %H:%M:%S'
	for item in slots:
		current_date = get_datetime()
		from_date = datetime.strptime(str(getdate(date)) + ' ' + str(item.from_time), dtfmt)
		to_date = datetime.strptime(str(getdate(date)) + ' ' + str(item.to_time), dtfmt)
		if from_date > current_date:
			diff = frappe.utils.time_diff_in_seconds(from_date, current_date)
			current_date
			if diff >= (int(min_time) * 60):
				allow = False
				if restrict:
					check_bookings = frappe.db.get_all('Order Delivery Slot',
									 filters={'order_date': date, 'from_time': from_date.strftime("%H:%M:%S")}, 
									 fields=["order_date","from_time"],limit_page_length=1000)
					if len(check_bookings) < int(max_booking_slot):
						allow = True
				else:
					allow = True
				if allow:
					doc = item.__dict__
					doc['time_format'] = '{0} - {1}'.format(from_date.strftime('%I:%M %p'), 
					     									to_date.strftime('%I:%M %p'))
					slot_list.append(doc)
	if slot_list:
		return slot_list
	else:
		return failed_msg_resp("The slot_list not found")

def get_delivery_slots_list(name):
	if not name:
		failed_msg_400_resp("The name is missing.")
	delivery = frappe.get_doc('Delivery Setting', name)
	if delivery:
		today_date = currentdate = get_today_date(replace=True)
		dates_list = []
		blocked_day_list = []
		if delivery.enable_start_date and delivery.no_of_dates_start_from>0:
			today_date = frappe.utils.add_days(today_date, int(delivery.no_of_dates_start_from))
			slots_list = get_slot_lists(delivery.delivery_slots, today_date, 
			       						delivery.min_time, delivery.restrict_slot, 
										delivery.max_booking_slot)
			if slots_list:
				dates_list.append({'date': today_date, 'slots': slots_list, 
		       					  'format_date': today_date.strftime('%b %d, %Y')})
		if delivery.slot_for_current_date and today_date == currentdate:
			slots_list = get_slot_lists(delivery.delivery_slots, today_date, 
			       						delivery.min_time, delivery.restrict_slot, 
										delivery.max_booking_slot)
			if slots_list:
				dates_list.append({'date': today_date, 
		       					   'slots': slots_list, 
								   'format_date': today_date.strftime('%b %d, %Y')})
		data = get_deivery_slots(dates_list,delivery)
		dates_list = data[0]
		blocked_day_list = data[1]
		return (dates_list, blocked_day_list)


def get_deivery_slots(dates_list,delivery,today_date,blocked_day_list):
	if delivery.enable_future_dates:
		allowed_dates = delivery.no_of_future_dates
		if delivery.slot_for_current_date:
			allowed_dates = int(allowed_dates) + 1
		new_date = today_date
		block_day = new_date.strftime('%A')
		while len(dates_list) < int(allowed_dates):
			new_date = frappe.utils.add_days(new_date, days=1)
			block_day = new_date.strftime('%A')
			new_slot_list = []
			blocked = 0
			dtfmt = '%Y-%m-%d %H:%M:%S'
			for item in delivery.delivery_slots:
				allow = False
				slot_date = datetime.strptime(str(getdate(new_date)) + ' ' + str(item.from_time), dtfmt)
				to_date = datetime.strptime(str(getdate(new_date)) + ' ' + str(item.to_time), dtfmt)
				if delivery.restrict_slot:
					check_bookings = frappe.db.get_all('Order Delivery Slot',
										filters={'order_date': new_date, 
												'from_time': slot_date.strftime("%H:%M:%S")}, 
										limit_page_length=1000)
					if len(check_bookings) < int(delivery.max_booking_slot):
						allow = True
				else:
					allow = True
				if allow:
					doc = item.__dict__
					doc['time_format'] = '{0} - {1}'.format(slot_date.strftime('%I:%M %p'), 
														to_date.strftime('%I:%M %p'))
					new_slot_list.append(doc)
			blocked_day = frappe.db.get_all("Delivery Day Block",
							filters={'parenttype':'Delivery Setting','parentfield':'enable_day','parent':delivery.name},
							fields=['day'])
			day_list = list(set([x.day for x in blocked_day if x.day == block_day]))
			if day_list and len(day_list) > 0:
				date1 = getdate(new_date)
				blocked_day_list.append(date1)
				blocked = 1
			dates_list.append({'date': new_date, 'slots': new_slot_list,
								'format_date': new_date.strftime('%b %d, %Y')})
	return [dates_list, blocked_day_list]