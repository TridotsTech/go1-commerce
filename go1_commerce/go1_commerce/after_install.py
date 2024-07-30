# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals, print_function

import frappe
import frappe, os, re
import json

def after_install():   
    install_shipping_method()
    install_shipping_rate_method()
    install_shipping_status()
    install_order_status()
    install_roles()
    install_party_type()
    install_payment_method()
    install_payment_mode()
    install_reference()
    install_return_request_reason()
    install_return_request_status()
    install_accounts()
    install_pages()
    install_catalogs()
    install_media_settings()


def install_roles():
    file_name = "roles.json"
    read_module_path(file_name) 
                    
def install_order_status():
    file_name = "order_status.json"
    read_module_path(file_name)     

def install_party_type():
    file_name = "party_type.json"
    read_module_path(file_name)             

def install_payment_method():
    file_name = "payment_method.json"
    read_module_path(file_name)

def install_payment_mode():
    file_name = "mode_of_payment.json"
    read_module_path(file_name)

def install_reference():
    file_name = "reference.json"
    read_module_path(file_name) 

def install_return_request_reason():
    file_name = "return_request_reason.json"
    read_module_path(file_name)

def install_return_request_status():
    file_name = "return_request_status.json"
    read_module_path(file_name)

def install_accounts():
    file_name = "accounts.json"
    read_module_path(file_name)

def install_pages():
    file_name = "pages.json"
    read_module_path(file_name)

def install_shipping_method():
    file_name = "shipping_methods.json"
    read_module_path(file_name)

def install_shipping_rate_method():
    file_name = "shipping_rate_methods.json"
    read_module_path(file_name)

def install_shipping_status():
    file_name = "shipping_status.json"
    read_module_path(file_name)

def install_catalogs():
    file_name = "default_catalog.json"
    read_module_path(file_name)

def install_media_settings():
    file_name = "media_setting.json"
    read_module_path(file_name)



def read_module_path(file_name):
    path = frappe.get_module_path("go1_commerce")
    file_path = os.path.join(path,"default_data",file_name)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            out = json.load(f)
        for i in out:
            try:
                frappe.get_doc(i).insert()
            except frappe.NameError:
                pass
            except Exception as e:
                pass   
                

