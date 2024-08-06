from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, nowdate, now
from datetime import date, timedelta,datetime
from frappe.utils import now_datetime
from go1_commerce.utils.setup import get_settings


@frappe.whitelist(allow_guest = True)
def check_wallet_setting():
    return frappe.get_single("Wallet Settings")


@frappe.whitelist(allow_guest = True)
def get_core_settings():
    return frappe.get_single("Core Settings")


@frappe.whitelist(allow_guest = True)
def release_lockedin_amount():
    try:
        wallet_settings = frappe.get_single("Wallet Settings")
        wallet_trans = frappe.db.sql(''' SELECT * FROM `tabWallet Transaction` 
                                        WHERE status = "Locked" AND docstatus = 1 
                                            AND is_settlement_paid = 0 ''', as_dict = True)
        if wallet_trans:
            for x in wallet_trans:
                lockperiod = int(wallet_settings.credit_period)
                if lockperiod > 0:
                    check_today = x.transaction_date + timedelta(days = lockperiod)
                    current_datetime = datetime.now()
                    time = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
                    if check_today  == time or check_today <= time:
                        res =  update_wallet(x)
                        wallet_tra_details = frappe.get_doc("Wallet Transaction",x.name)
                        wallet_tra_details.status = "Approved"
                        wallet_tra_details.save(ignore_permissions = True)
                        frappe.db.commit()
                        return res
                else:
                    res =  update_wallet(x)
                    wallet_tra_details = frappe.get_doc("Wallet Transaction",x.name)
                    wallet_tra_details.status = "Approved"
                    wallet_tra_details.save(ignore_permissions = True)
                    frappe.db.commit()
                    return res
        wallet_trans = frappe.db.sql(''' SELECT * 
                                            FROM `tabWallet Transaction` 
                                        WHERE status = "Pending" 
                                            AND docstatus = 1 AND is_settlement_paid = 0 
                                            AND start_date IS NOT NULL 
                                        ORDER BY start_date ASC ''', as_dict = True)
        if wallet_trans:
            for x in wallet_trans:
                if x.order_id and x.order_type and frappe.db.get_value("DocField", 
                                                            {"parent": x.order_type,"fieldname": "status"}):
                    order = frappe.db.get_value(x.order_type,x.order_id,"status")
                    if x.start_date <= date.today() and order == "Active":
                        update_wallet(x)
                else:
                    if x.start_date <= date.today():
                        update_wallet(x)
        wallet_trans_end = frappe.db.sql(''' SELECT end_date,name 
                                                FROM `tabWallet Transaction` 
                                            WHERE status = "Credited" 
                                                AND docstatus = 1 AND is_settlement_paid = 0
                                                AND end_date IS NOT NULL ORDER BY end_date ASC
                                        ''', as_dict=True)
        if wallet_trans_end:
            for x in wallet_trans_end:
                if x.end_date <= date.today():
                    wt = frappe.get_doc("Wallet Transaction", x.name)
                    wt.docstatus=2
                    wt.save(ignore_permissions=True)
    except Exception: 
        frappe.log_error(title = "Error in release_lockedin_amount",mesaage = frappe.get_traceback() )


@frappe.whitelist()
def update_wallet(doc):
    try:
        current_date = now_datetime().strftime(" %Y-%m-%d %H:%M:%S")
        if doc.type != "Service Provider":
            wallet_name = frappe.db.get_value("Wallet", {"user": doc.party,
                                                        "user_type": doc.party_type })
        else:
            wallet_name = frappe.db.get_value("Wallet", {"user":doc.type })
        if wallet_name:
            return update_wallet_by_name(doc,wallet_name,current_date)
        else:
            return create_new_wallet(doc,current_date)
    except Exception:
        frappe.log_error(message = frappe.get_traceback(), title = "Error in accounts.api.update_wallet") 


def create_new_wallet(doc,current_date):
    wal = frappe.new_doc("Wallet")
    wal.last_updated = current_date
    if doc.type != "Service Provider":
        user = frappe.get_doc(doc.party_type,doc.party)
        wal.user = doc.party	
        wal.user_type = doc.type
    else:
        wal.user = doc.type	
        wal.user_type = doc.type
    validate_wallet_status(doc,wal)
    if doc.party_type == "Drivers":
        wal.mobile_no = user.mobile_no
        wal.name1 = user.full_name
    elif doc.party_type == "Service Provider":
        wal.name1 = doc.type
    elif doc.party_type == "Customers":
        if user.last_name:
            name = user.first_name+''+ user.last_name
        else:
            name = user.first_name
        wal.name1 = name
    elif doc.party_type == "Supplier":
        if user.last_name:
            name=user.first_name+''+ user.last_name
        else:
            name = user.first_name
        wal.name1 = name
    wal.insert(ignore_permissions=True)
    return {"status" : "Success",
            "message": wal}


def handling_created_status(doc, wal):
    if doc.transaction_type == "Pay":
            wal.current_wallet_amount = doc.amount
            wal.total_wallet_amount = doc.amount
            wal.locked_in_amount = 0
    else:
        if doc.is_settlement_paid == 0 and doc.type == "Service Provider":
            wal.current_wallet_amount = flt(doc.amount)
            wal.total_wallet_amount = flt(doc.amount)
            wal.locked_in_amount = 0
        else:
            wal.current_wallet_amount = -1 * flt(doc.amount)
            wal.total_wallet_amount = -1 * flt(doc.amount)
            wal.locked_in_amount = 0


def handle_pending_with_start_date(doc,wal):
    if doc.transaction_type == "Pay":
            wal.current_wallet_amount = doc.amount
            wal.total_wallet_amount = doc.amount
            wal.locked_in_amount = 0
            frappe.db.set_value('Wallet Transaction',doc.name,'status',"Credited")
    else:
        if doc.is_settlement_paid == 0 and doc.type == "Service Provider":
            wal.current_wallet_amount = flt(doc.amount)
            wal.total_wallet_amount = flt(doc.amount)
            wal.locked_in_amount = 0
            frappe.db.set_value('Wallet Transaction',doc.name,'status',"Credited")
        else:
            wal.current_wallet_amount = -1 * flt(doc.amount)
            wal.total_wallet_amount = -1 * flt(doc.amount)
            wal.locked_in_amount = 0
            frappe.db.set_value('Wallet Transaction',doc.name,'status',"Credited")


def handling_locked_status(doc, wal):
    if doc.transaction_type == "Pay":
        wal.locked_in_amount = flt(doc.amount)
        wal.total_wallet_amount = flt(doc.amount)
        wal.current_wallet_amount = 0

def handle_pending_without_startdate(doc, wal):
    if doc.transaction_type == "Pay":
        wal.locked_in_amount = flt(doc.amount)
        wal.total_wallet_amount = flt(doc.amount)
        wal.current_wallet_amount = 0
    else:
        wal.locked_in_amount = flt(doc.amount)
        wal.total_wallet_amount = flt(doc.amount)
        wal.current_wallet_amount=0

@frappe.whitelist()
def validate_wallet_status(doc,wal):
    if doc.status == "Credited":
        handling_created_status(doc, wal)
    if doc.status == "Pending" and doc.start_date <= date.today():
       handle_pending_with_start_date(doc,wal)
    if doc.status == "Locked":
       handling_locked_status(doc, wal)
    if doc.status == "Pending" and not doc.start_date:
        handle_pending_without_startdate(doc, wal)


def update_wallet_by_name(doc,wallet_name,current_date):
    wallet = frappe.get_doc("Wallet", wallet_name)
    if wallet:
        if doc.status == "Credited":
            if doc.transaction_type == "Pay":
                cur_wallet = flt(wallet.current_wallet_amount) + flt(doc.amount)
                locked_in = flt(wallet.locked_in_amount)
                total_wallet = flt(cur_wallet) + flt(locked_in)
        if doc.status == "Locked":
            if doc.transaction_type == "Pay":
                cur_wallet = flt(wallet.current_wallet_amount)
                locked_in = flt(wallet.locked_in_amount) + flt(doc.amount)
                total_wallet = flt(cur_wallet) + flt(locked_in)
        if doc.status == "Pending" and not doc.start_date:
            if doc.transaction_type == "Pay":
                cur_wallet = flt(wallet.current_wallet_amount)
                locked_in = flt(wallet.locked_in_amount) + flt(doc.amount)
                total_wallet = flt(cur_wallet) + flt(locked_in)
        if doc.status == "Pending" and doc.start_date <= date.today():
            if doc.transaction_type == "Pay":
                cur_wallet = flt(wallet.current_wallet_amount) + flt(doc.amount)
                locked_in = flt(wallet.locked_in_amount)
                total_wallet = flt(cur_wallet) + flt(locked_in)
                frappe.db.set_value('Wallet Transaction',doc.name,'status',"Credited")
        wallet_detail = frappe.get_doc('Wallet',wallet.name)
        wallet_detail.current_wallet_amount = cur_wallet
        wallet_detail.locked_in_amount = locked_in
        wallet_detail.total_wallet_amount = total_wallet
        wallet_detail.last_updated = current_date
        wallet_detail.save(ignore_permissions=True)
        return {"status" : "Successfully Realesed",
                "message": wallet_detail}


@frappe.whitelist(allow_guest = True)
def make_withdraw_request(source_name = None):
    try:
        trans_ref = ""
        ref = "Wallet"
        if source_name:
            ref = "Wallet"
            source = frappe.get_all("Wallet",
                                        fields = ["current_wallet_amount","name1","user_type","user"],
                                        filters = {"name":source_name},ignore_permissions = True)[0]
        orderlist = orders_for_update(source.user)
        if len(orderlist) > 0:
            trans_ref = ", ".join(['' + i['name'] + '' for i in orderlist])
        pe = frappe.new_doc("Wallet Withdrawal Request")
        pe.posting_date = nowdate()
        pe.party_type = source.user_type
        pe.party = source.user
        pe.party_name = source.name1
        pe.withdraw_amount = source.current_wallet_amount
        if ref == "Wallet":
            pe.withdrawal_type = "Auto Withdraw"
            pe.status = "Approved"
        if trans_ref:
            pe.order_ref = trans_ref
        pe.flags.ignore_permissions = True
        pe.submit()
        return {'status':'Success'}
    except Exception:
        frappe.log_error(message = frappe.get_traceback(), title = "Error in wallet.make_withdraw_request") 
        return {'status':'Failed'}
    
    
@frappe.whitelist(allow_guest = True)
def orders_for_update(source):
    try:
        order_list = frappe.db.sql('''  SELECT IFNULL(order_id, name) AS name, name AS trans_id 
                                            FROM `tabWallet Transaction` 
                                        WHERE is_settlement_paid = 0 AND transaction_type = "Pay" 
                                            AND party = %s ''', source, as_dict=True)
        return order_list
    except Exception:
        frappe.log_error(message = frappe.get_traceback(), title = " Error in wallet.orders_for_update")

def payment_type_check(pe, source_name):
    if pe.payment_type == 'Pay':
            pe.payment_type = 'Receive'
            check_prev_payments = frappe.db.sql(''' SELECT IFNULL(SUM(allocated_amount), 0) 
                                                    FROM `tabPayment Reference` PR 
                                                    INNER JOIN `tabPayment Entry` PE ON PE.name = PR.parent 
                                                    WHERE PE.payment_type = "Receive" 
                                                        AND PR.reference_doctype = "Order" 
                                                        AND PR.reference_name = %(ref)s
                                                ''', {'ref': source_name})
            if check_prev_payments and check_prev_payments[0]:
                if float(check_prev_payments[0][0]) > 0:
                    pe.payment_type = 'Pay'


def check_MOP_and_amount(pe,mode_of_payment, source, amount, total):
    if mode_of_payment:
            pe.mode_of_payment = mode_of_payment
    else:
        pe.mode_of_payment = ""
    pe.party_type = source.customer_type
    pe.party = source.customer
    pe.party_name = source.customer_name
    pe.contact_person = ""
    pe.contact_email = ""
    if amount:
        pe.paid_amount = (amount)
        pe.base_paid_amount = (amount)
        pe.received_amount = (amount)
        paid_amount=amount
        return paid_amount
    else:
        pe.paid_amount = abs(total)
        pe.base_paid_amount = abs(total)
        pe.received_amount = abs(total)
        paid_amount = abs(total)
        return paid_amount
@frappe.whitelist(allow_guest = True)
def make_payment(source_name = None, order = None, mode_of_payment = None, amount = None):
    try:
        frappe.log_error("source_name",source_name)
        default_currency = get_settings('Catalog Settings')
        if source_name:
            source = frappe.get_all("Order",
                                fields=["name","outstanding_amount","total_amount","customer_name","customer",
                                        "customer_type"],
                                filters={"name":source_name})[0]
        frappe.log_error("source",source)
        if order:
            source = frappe.get_all("Order",fields=["*"],filters={"name":order})[0]
        if flt(source.outstanding_amount) == 0:
            return {'status': 'failed', 'message': frappe._('No outstanding amount for this order')}
        if flt(source.outstanding_amount) != 0:
            total = source.outstanding_amount
        else:
            total = source.total_amount
        pe = frappe.new_doc("Payment Entry")
        pe.payment_type = "Receive" if flt(source.outstanding_amount) > flt(0) else "Pay"
        payment_type_check(pe, source_name)
        pe.posting_date = nowdate()
        paid_amount = check_MOP_and_amount(pe,mode_of_payment, source, amount, total)
 

        pe.allocate_payment_amount = 1
        payment_type = 'received from'
        if pe.payment_type == 'Pay':
            payment_type = 'paid to'
        pe.remarks = 'Amount {0} {1} {2} {3}'.format(default_currency.default_currency,
                                                        pe.paid_amount,
                                                        payment_type, pe.party)
        # frappe.log_error("source.order_date",source.order_date)
        pe.append("references",{'reference_doctype':"Order",
                                'reference_name': source.name,
                                "bill_no": "",
                                "due_date": source.order_date,
                                'total_amount': abs(total),
                                'outstanding_amount': 0,
                                'allocated_amount': paid_amount })
        if source_name:
            return pe
        else:
            pe.flags.ignore_permissions=True
            pe.submit()
            return pe.name
    except Exception:
        frappe.log_error(message = frappe.get_traceback(), title = "Error in accounts.api.make_payment")


@frappe.whitelist()
def customer_payment_for_order(customer):
    orders = frappe.get_all('Order',fields=['*'],filters={"customer":customer})
    if orders:
        for n in orders:
            n.order_items = frappe.get_all('Order Item',fields=["*"],filters={"parent":n.name})
            n.payments = frappe.db.sql('''  SELECT P.name, P.payment_type, P.mode_of_payment, P.posting_date,
                                                P.party_type, P.party_name, P.party, P.paid_amount,
                                                R.total_amount, R.outstanding_amount, R.allocated_amount
                                            FROM `tabPayment Entry` AS P
                                            INNER JOIN `tabPayment Reference` AS R
                                            ON R.parent = P.name
                                            WHERE R.reference_doctype = 'Order'
                                            AND R.reference_name = %s
                                            ''',n.name,as_dict=1)
    return orders



def app_pay_wallet_details(customer,page_no,page_len):
    limit_start = str(((int(page_no)-1)*int(page_len)))
    source = frappe.db.sql("""  SELECT name, user_type, user, name1 AS user_name, current_wallet_amount,
                                        locked_in_amount, total_wallet_amount
                                    FROM `tabWallet` AS W
                                    WHERE W.user = %s
                                    """,customer,as_dict=1)
    for n in source:
        n.transactions = frappe.db.sql('''  SELECT *
                                            FROM `tabWallet Transaction` AS WT
                                            WHERE WT.party = %s
                                                AND WT.transaction_type = "Pay"
                                                AND WT.disabled = 0
                                                AND WT.docstatus = 1
                                            ORDER BY WT.creation DESC
                                            LIMIT {limit_start}, {limit_page_length}
                                            '''.format(limit_start=limit_start,
                                                        limit_page_length=page_len),
                                            customer,as_dict=1)
        paid = frappe.db.sql('''  SELECT IFNULL(SUM(amount), 0) AS amount
                                FROM `tabWallet Transaction` AS WT
                                WHERE WT.party = %s
                                    AND WT.transaction_type = "Pay"
                                    AND WT.status = "Debited"
                                    AND WT.is_settlement_paid = 1
                                ''',customer,as_dict=1)
        if len(paid)>0:
            n.settled_amount=paid[0].amount
        else:
            n.settled_amount=0
    return source


def not_app_pay_wallet_details(customer,limit_start,page_len):
    source = frappe.db.sql("""  SELECT name, user_type, user, name1 AS user_name
                                    FROM `tabWallet` AS W
                                    WHERE W.user = %s+
                                    """,customer,as_dict=1)
    for n in source:
        n.to_be_received = frappe.db.sql('''SELECT IFNULL(SUM(amount), 0) AS amount
                                            FROM `tabWallet Transaction` AS WT
                                            WHERE WT.party = %s
                                                AND WT.docstatus = 1
                                                AND WT.transaction_type = "Pay"
                                                AND WT.status = "Pending"
                                            ''',customer,as_dict=1) [0].amount
        n.climed_amount= frappe.db.sql('''  SELECT IFNULL(SUM(amount), 0) AS amount
                                            FROM `tabWallet Transaction` AS WT
                                            WHERE WT.party = %s
                                            AND WT.docstatus = 1
                                            AND WT.transaction_type = "Pay"
                                            AND WT.status = "Approved"
                                            ''',customer,as_dict=1)[0].amount
        n.total_amount=frappe.db.sql('''SELECT IFNULL(SUM(amount), 0) AS amount
                                        FROM `tabWallet Transaction` AS WT
                                        WHERE WT.party = %s
                                            AND WT.docstatus = 1
                                            AND WT.transaction_type = "Pay"
                                        ''',customer,as_dict=1)[0].amount
        n.transactions = frappe.db.sql('''  SELECT *
                                            FROM `tabWallet Transaction` AS WT
                                            WHERE WT.party = %s
                                                AND WT.transaction_type = "Pay"
                                                AND WT.docstatus = 1
                                                AND WT.disabled = 0
                                            ORDER BY WT.creation DESC
                                            LIMIT {limit_start}, {limit_page_length}
                                            '''.format(limit_start=limit_start,
                                                        limit_page_length=page_len),
                                            customer,as_dict=1)
    return source
@frappe.whitelist()
def get_wallet_details(list_type,customer,page_no,page_len):
    limit_start = str(((int(page_no)-1)*int(page_len)))
    if list_type=="app_pay":
        return app_pay_wallet_details(customer,page_len,page_len)
    else:
        return not_app_pay_wallet_details(customer,limit_start,page_len)


@frappe.whitelist()
def create_withdraw_request(party_type, user, amount, note=None):
    source = None
    if party_type and user:
        source = frappe.get_all("Wallet",fields=["*"],filters={"user":user},ignore_permissions=True)[0]	
    if source:
        pe = frappe.new_doc("Wallet Withdrawal Request")
        pe.posting_date = nowdate()
        pe.party_type = party_type
        pe.party = user
        pe.withdraw_amount = amount
        pe.withdrawal_type = "Self"
        pe.status = "Approved"
        pe.order_ref=note
        pe.flags.ignore_permissions = True
        pe.submit()
        return {"status": "Success",
                "message":pe}

@frappe.whitelist()
def get_wallet_detail_counters(user):
    try:
        from go1_commerce.go1_commerce.doctype.wallet.\
            wallet import get_counter_apy_counters
        app_source = get_counter_apy_counters(user)
        wallet_name = frappe.db.get_value("Wallet", {"user": user})
        if wallet_name:
            counter_source = frappe.db.sql("""  SELECT name, user_type, user, name1 AS user_name, 
                                                    current_wallet_amount, locked_in_amount, total_wallet_amount 
                                                FROM `tabWallet` AS W
                                                WHERE W.user = %s
                                                """,user,as_dict=1)
            return {"app_source":app_source[0],
                    "counter_source":counter_source[0]}
        else:
            return {"app_source":"", 
                    "counter_source":""}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "api.getwallet_transaction")

def app_transaction_order_list(start,page_len,user):
    order_list=frappe.db.sql('''SELECT IFNULL(order_id, name) AS name,
                                        IFNULL(reference, '') AS reference,
                                        total_value,
                                        amount 
                                    FROM `tabWallet Transaction` AS WT
                                    WHERE WT.docstatus = 1 
                                        AND WT.is_settlement_paid = 0 
                                        AND WT.transaction_type = "Pay" 
                                        AND WT.party = %s 
                                    ORDER BY WT.creation DESC
                                    LIMIT {0}, {1}
                                    '''.format(start,int(page_len)),user,as_dict=1)
    return order_list
    

def app_transaction_total_count(user):
    total_count = frappe.db.sql(''' SELECT IFNULL(COUNT(*), 0) AS count 
                                        FROM `tabWallet Transaction` AS WT
                                        WHERE WT.docstatus = 1 
                                            AND WT.is_settlement_paid = 0 
                                            AND WT.party = %s 
                                        ORDER BY WT.creation DESC
                                        ''',user,as_dict=1)
    return total_count
@frappe.whitelist()
def get_app_transactions(user, page_no, page_len):
    try:
        start=(int(page_no)-1)*int(page_len)
        transaction = frappe.db.sql(''' SELECT order_id 
                                        FROM `tabWallet Transaction` AS WT
                                        WHERE WT.docstatus = 1 
                                            AND WT.type = "Business" 
                                            AND WT.reference = "Order" 
                                            AND WT.order_type = "Order" 
                                            AND WT.is_settlement_paid = 0 
                                            AND WT.transaction_type = "Pay" 
                                            AND WT.party = %s 
                                        ORDER BY WT.creation DESC
                                        ''',user,as_dict=1)
        
        if transaction:
            order_trans = ", ".join(['"' + i['order_id'] + '"' for i in transaction])
        
        
        
        
        return {'orders':app_transaction_order_list(start,page_len,user),
                'count':app_transaction_total_count(user)[0].count}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "api.getwallet_transaction")



def counter_transaction_order_list(start, page_len, user):
    order_list = frappe.db.sql('''  SELECT IFNULL(order_id, name) AS name,
                                            IFNULL(reference, '') AS reference,
                                            total_value,
                                            amount 
                                        FROM `tabWallet Transaction` AS WT
                                        WHERE WT.docstatus = 1 
                                            AND WT.is_settlement_paid = 0 
                                            AND WT.transaction_type = "Receive" 
                                            AND WT.status = "Pending" 
                                            AND WT.party = %s 
                                        ORDER BY WT.creation DESC
                                        LIMIT {0}, {1}
                                    '''.format(start,int(page_len)),user,as_dict=1)
    return order_list

def counter_transaction_total_count(user):
    total_count = frappe.db.sql(''' SELECT IFNULL(COUNT(*), 0) AS count 
                                        FROM `tabWallet Transaction` AS WT
                                        WHERE WT.docstatus = 1 
                                            AND WT.is_settlement_paid = 0 
                                            AND WT.transaction_type = "Receive" 
                                            AND WT.status = "Pending" 
                                            AND WT.party = %s 
                                        ORDER BY WT.creation DESC
                                        ''',user,as_dict=1)
    return total_count
@frappe.whitelist()
def get_counter_transactions(user, page_no, page_len):
    try:
        start=(int(page_no)-1)*int(page_len)
        transaction = frappe.db.sql(''' SELECT order_id 
                                        FROM `tabWallet Transaction` AS WT
                                        WHERE WT.docstatus = 1 
                                            AND WT.reference = "Order" 
                                            AND WT.order_type = "Order" 
                                            AND WT.is_settlement_paid = 1 
                                            AND WT.is_fund_added = 0 
                                            AND WT.transaction_type = "Receive" 
                                            AND WT.party = %s 
                                        ORDER BY WT.creation DESC
                                        ''',user,as_dict=1)
        
        if transaction:
            order_trans = ", ".join(['"' + i['order_id'] + '"' for i in transaction])
        
        
        
        
        return {'orders':counter_transaction_order_list(start, page_len, user),
                'count':counter_transaction_total_count(user)[0].count,
                "source":counter_transaction_total_count(user)[0]}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "wallet.get_commission_list")


@frappe.whitelist()
def insert_wallet_transaction(data):
    wallet_trans_entry = frappe.get_doc({
                                        "doctype":"Wallet Transaction",
                                        "reference":data['reference'],
                                        "order_type" : data['order_type'],
                                        "order_id" : data['order_id'],
                                        "transaction_date":now(),
                                        "total_value":(data['total_value'] or data['amount']),
                                        "amount":data['amount'],
                                        "notes":data['notes'],
                                        "disabled":data["disabled"],
                                        "is_settlement_paid":data['is_paid']
                                        })
    wallet_trans_entry.start_date = data['start_date']
    if data.get('end_date'):
        wallet_trans_entry.end_date = data['end_date']
    wallet_trans_entry.type = data['party_type']
    wallet_trans_entry.party_type = data['party_type']
    wallet_trans_entry.party = data['party']
    if data.get('party_name'):
        wallet_trans_entry.party_name = data['party_name']
    wallet_trans_entry.transaction_type = data['transaction_type']
    wallet_trans_entry.status = data['status']
    wallet_trans_entry.flags.ignore_permissions = True
    wallet_trans_entry.docstatus=1
    wallet_trans_entry.save()
    return wallet_trans_entry.name


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None, submit=False):
    return _make_sales_invoice(source_name, target_doc, submit)

def _make_sales_invoice(source_name, target_doc=None, submit=False, ignore_permissions=False):
    docval = frappe.get_doc("Order", source_name)
    customer = _make_party_details(docval, ignore_permissions)

    def set_missing_values(source, target):
        target.status = "Unpaid"
        target.naming_series = "INV-YYYY-"
        target.reference = source_name
        target.notes = "Invoice created against: "+source_name
        target.flags.ignore_permissions = ignore_permissions
        target.run_method("set_missing_values")
    
    doclist = get_mapped_doc("Order", source_name, {
            "Order": {
                "doctype": "Sales Invoice",
                "validation": {
                    "docstatus": ["=", 1]
                }
            },
            "Order Item": {
                "doctype": "Sales Invoice Item",
                "add_if_empty": True
            },
        }, target_doc, set_missing_values, ignore_permissions=ignore_permissions)
    if submit==True:
        doclist.docstatus = 1
        doclist.save()
    else:
        return doclist


def _make_party_details(source_name, ignore_permissions=False):
    return frappe.get_doc(source_name.customer_type, source_name.customer)


@frappe.whitelist()
def make_invoice_payment(source_name=None, source=None, target_doc=None):
    try:
        source_doctype = "Sales Invoice"
        default_currency = get_settings('Catalog Settings')
        remarks = ''
        if source_name or source:
            source = frappe.get_all(source_doctype,fields=["*"],filters={"name":source_name})[0]
        if flt(source.outstanding_amount) != 0:
            total = source.outstanding_amount
        else:
            total = source.total_amount
        pe = frappe.new_doc("Payment Entry")
        pe.payment_type = "Receive" if flt(source.outstanding_amount) > flt(0) else "Pay"
        pe.posting_date = nowdate()
        pe.mode_of_payment = source.payment_type
        pe.party_type = source.customer_type
        pe.party = source.customer
        pe.party_name = source.customer_name
        pe.contact_person = ""
        pe.contact_email = ""
        pe.paid_amount = abs(total)
        pe.base_paid_amount = abs(total)
        pe.received_amount = abs(total)
        paid_amount = abs(total)
        pe.allocate_payment_amount = 1
        payment_type = 'received from'
        if pe.payment_type == 'Pay':
            payment_type = 'paid to'
        pe.remarks = 'Amount {0} {1} {2} {3}'.format(default_currency.default_currency, pe.paid_amount, payment_type, pe.party)
        pe.append("references", {
            'reference_doctype': source_doctype,
            'reference_name': source.name,
            "bill_no": "",
            "due_date": source.order_date,
            'total_amount': abs(total),
            'outstanding_amount': 0,
            'allocated_amount': paid_amount
        })
        if source_name:
            return pe
        else:
            pe.flags.ignore_permissions=True
            pe.submit()
            return pe.name
    except Exception:
        frappe.log_error(frappe.get_traceback(), "accounts.api.make_invoice_payment")


@frappe.whitelist()
def update_docstatus(doctype, docname, statusfield , status,paid_amount = 0):
    try:
        frappe.log_error("status",status)
        doc = frappe.get_doc(doctype, docname)
        if doctype=="Sales Invoice":
            doc.status = status
            doc.paid_amount = paid_amount
        elif doctype=="Order":
            doc.payment_status = status
        else:
            doc[statusfield] = status
        doc.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "accounts.api.update_docstatus")


@frappe.whitelist()
def update_meta_data(doctype,docname,fieldname,value):
    try:
        frappe.db.set_value(doctype,docname,fieldname,value)
        doc = frappe.get_doc(doctype,docname)
        return doc
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Error in accounts.api.update_meta_data")

