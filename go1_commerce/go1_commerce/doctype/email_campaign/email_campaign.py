# -*- coding: utf-8 -*-
# Copyright (c) 2018, info@valiantsystems.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, today,nowdate
from frappe.core.doctype.communication.email import make
from frappe.query_builder import DocType

class EmailCampaign(Document):
	def validate(self):
		# by gopi on 13/6/24
		# self.set_date()
		self.validate_sender()
		self.validate_email_campaign_already_exists()
		# self.update_status()
		# end


	def set_date(self):
		send_after_days = []
		campaign = frappe.get_doc("Campaign", self.campaign)
		for entry in campaign.get("campaign_schedules"):
			send_after_days.append(entry.send_after_days)
		try:
			self.end_date = add_days(getdate(self.start_date), max(send_after_days))
		except ValueError:
			frappe.throw(_("Please set up the Campaign Schedule in the Campaign {0}").format(self.campaign))

	def validate_sender(self):
		if not self.sender:
			sender = frappe.db.get_value('Email Campaign Settings', None, 'default_sender')
			if sender:
				self.sender = sender

	def validate_email_campaign_already_exists(self):
		if not self.status == 'Completed':
			email_campaign_exists = frappe.db.exists("Email Campaign", {
				"campaign": self.campaign,
				"email_campaign_for": self.email_campaign_for,
				"recipient": self.recipient,
				"status": ("in", ["In Progress", "Scheduled"]),
				"name": ("!=", self.name)
			})
			if email_campaign_exists:
				frappe.throw(_("The Campaign '{0}' already exists for the {1} '{2}'").format(self.campaign, self.email_campaign_for, self.recipient))

	def update_status(self):
		start_date = getdate(self.start_date)
		end_date = getdate(self.end_date)
		today_date = getdate(today())
		if start_date > today_date:
			self.status = "Scheduled"
		elif end_date >= today_date:
			self.status = "In Progress"
		elif end_date < today_date:
			self.status = "Completed"

#called through hooks to send campaign mails to leads

# by gopi on 13/6/24
@frappe.whitelist()
def send_email_to_campaigns():
	try:
		email_campaigns = frappe.get_all("Email Campaign", filters = { 'status': ('not in', ['Unsubscribed', 'Completed', 'Scheduled']) })
		for camp in email_campaigns:
			email_campaign = frappe.get_doc("Email Campaign", camp.name)
			if email_campaign.campaign:
				campaign = frappe.db.get_value("Campaign Email Schedule", {"parent":email_campaign.campaign},"email_template")
				campaign_email = frappe.get_doc({
					'doctype': 'Campaign Email Schedule', 
					'parent': email_campaign.campaign
					})
				email_campaign.email_template=campaign
			send_mail(email_campaign)
	except Exception:
		frappe.log_error(title="Error in send_email_to_campaigns", message = frappe.get_traceback())

def send_mail(email_campaign):
	email_template = frappe.get_doc("Email Template", email_campaign.get("email_template"))
	sender = frappe.db.get_value("User", email_campaign.get("sender"), 'email')
	doc = None
	if email_campaign.email_campaign_for == 'Email Group':	
		EmailGroupMember = DocType('Email Group Member')
		query = (
			frappe.qb.from_(EmailGroupMember)
			.select(EmailGroupMember.email)
			.where((EmailGroupMember.email_group == email_campaign.recipient) &
				(EmailGroupMember.unsubscribed == 0))
		)
		recipient = query.run(pluck=True)
	elif email_campaign.email_campaign_for == 'Shopping Cart':
		customer = frappe.db.get_value('Shopping Cart', email_campaign.recipient, 'customer')
		recipient = [frappe.db.get_value('Customers', customer, 'email')]
	else:
		recipient = [frappe.db.get_value(email_campaign.email_campaign_for, email_campaign.get("recipient"), 'email')]
	# frappe.log_error("--recipient",recipient)

	# send mail and link communication to document
	for r in recipient:
		if r:
			doc = frappe.get_doc(email_campaign.email_campaign_for, email_campaign.get("recipient"))
			if email_campaign.email_campaign_for == 'Email Group':
				doc = frappe.get_doc('Email Group Member', {'email': r})
			if email_campaign.email_campaign_for == 'Shopping Cart' and (len(doc.items) == 0 or not doc.items):
				doc = None
			# frappe.log_error("--doc",doc)
			if doc:
				make(
					doctype = "Email Campaign",
					name = email_campaign.name,
					subject = frappe.render_template(email_template.get("subject"),{'doc': doc}),
					content = frappe.render_template(email_template.get("body"),{'doc': doc}),
					sender = sender,
					recipients = r,
					communication_medium = "Email",
					send_email = True
				)



#called from hooks on doc_event Email Unsubscribe
def unsubscribe_recipient(doc, method):
	if doc.reference_doctype == 'Email Campaign':
		email_campaign = frappe.get_doc(doc.reference_doctype, doc.reference_name)
		if email_campaign.email_campaign_for != 'Email Group':
			frappe.db.set_value("Email Campaign", doc.reference_name, "status", "Unsubscribed")
		else:
			frappe.db.set_value('Email Group Member', doc.email, 'unsubscribed', 1)

#called through hooks to update email campaign status daily
# by gopi on 13/6/24
@frappe.whitelist()
def set_email_campaign_status():
	email_campaigns = frappe.get_all("Email Campaign", filters = { 'status': ('not in', ['Unsubscribed', 'Completed'])})
	for entry in email_campaigns:
		email_campaign = frappe.get_doc("Email Campaign", entry.name)
		if email_campaign.status == "In Progress":
			if email_campaign.end_date and email_campaign.end_date < getdate(nowdate()):
				email_campaign.status = "Completed"
		elif email_campaign.status == "Scheduled":
			if email_campaign.start_date <= getdate(nowdate()):
				email_campaign.status = "In Progress"
		email_campaign.save(ignore_permissions=True)

