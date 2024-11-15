# Copyright (c) 2013, sivaranjani and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.query_builder import DocType, Count

def execute(filters=None):
    columns, data = [], []
    columns = get_columns()
    data = products_report()
    return columns, data

def get_columns():
    return[
        "Vendor Name" + ":Link/Business:120",
        "Product" + ":Data:120",	
        "Quantity" + ":Int:120"
    ]

def products_report():
    Product = DocType('Product')
    OrderItem = DocType('Order Item')
    query = (
        frappe.qb.from_(Product)
        .left_join(OrderItem)
        .on(
            (OrderItem.item == Product.name) &
            (OrderItem.parenttype == "Order")
        )
        .select(
            Product.restaurant,
            Product.item,
            Count(OrderItem.name).as_("qty")
        )
        .groupby(Product.name)
    )
    results = query.run(as_dict=True)
    return results