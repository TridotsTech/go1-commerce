# Copyright (c) 2013, Tridots Tech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.query_builder import DocType, Field, functions
from frappe.query_builder.functions import Concat, Cast, GroupConcat, Sum

def execute(filters=None):
    columns, data = [], []
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        _("Id") + ":Link/Customers:120",
        _("Customer Name") + ":Data: 200",
        _("Customer Email") + ":Data:200",
        _("Customer Phone") + ":Data:120"]
    if "loyalty" in frappe.get_installed_apps():
        columns += [
        _("Loyalty Points") + ":Data:140"
        ]
    columns += [
        _("Creation Date") + ":Data:200",
        _("Social Media Source") + ":Data:150",
        ]
    
    return columns

def get_data(filters):
    Customer = DocType('Customers')
    UserSocialLogin = DocType('User Social Login')
    LoyaltyPointEntry = DocType('Loyalty Point Entry')
    query = frappe.qb.from_(Customer).select(
        Customer.name,
        Customer.full_name,
        Customer.email,
        Customer.phone,
        Cast(Customer.creation, 'DATE').as_('creation_date'),
        GroupConcat(UserSocialLogin.provider).as_('social_logins')
    )
    if "loyalty" in frappe.get_installed_apps():
        query = query.left_join(LoyaltyPointEntry).on(
            (LoyaltyPointEntry.customer == Customer.name) &
            (LoyaltyPointEntry.party_type == 'Customers')
        ).select(
            IfNull(Sum(LoyaltyPointEntry.loyalty_points), 0).as_('total_points')
        )
    query = query.left_join(UserSocialLogin).on(
        (UserSocialLogin.parent == Customer.user_id) &
        (UserSocialLogin.provider != 'frappe')
    )
    if filters.get('from_date'):
        query = query.where(Cast(Customer.creation, 'DATE') >= filters.get('from_date'))
    if filters.get('to_date'):
        query = query.where(Cast(Customer.creation, 'DATE') <= filters.get('to_date'))
    query = query.where(Customer.name != '').where(Customer.naming_series != 'GC-')
    query = query.groupby(Customer.name)
    query = query.orderby(Customer.creation.desc())
    return query.run(as_list=True)