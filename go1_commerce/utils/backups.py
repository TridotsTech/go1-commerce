# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

"""This module handles the On Demand Backup utility"""

from __future__ import unicode_literals, print_function

#Imports
from frappe import _
import os, frappe
from datetime import datetime
from frappe.utils import cstr, get_url, now_datetime

verbose = 0
from frappe import conf
class BackupGenerator:
	"""
		This class contains methods to perform On Demand Backup

		To initialize, specify (db_name, user, password, db_file_name=None, db_host="localhost")
		If specifying db_file_name, also append ".sql.gz"
	"""
	def __init__(self, db_name, user, password, backup_path_db=None, backup_path_tab=None, backup_path_files=None, business=None, table=None,
		backup_path_private_files=None, db_host="localhost", add_folder=None):
		self.db_host = db_host
		self.db_name = db_name
		self.user = user
		self.password = password
		self.backup_path_files = backup_path_files
		self.backup_path_db = backup_path_db
		
		self.backup_path_tab = backup_path_tab
		self.business = business
		self.table=table
		self.add_folder= add_folder
		
		self.backup_path_private_files = backup_path_private_files

	def get_backup(self, older_than=24, ignore_files=False, force=False):
		"""
			Takes a new dump if existing file is old
			and sends the link to the file as email
		"""
		if not force:
			last_db,last_tab, last_file, last_private_file = self.get_recent_backup(older_than)
		else:
			last_db,last_tab, last_file, last_private_file = False, False, False, False

		if not (self.backup_path_files and self.backup_path_db and self.backup_path_tab and self.backup_path_private_files):
			self.set_backup_file_name()

		if not (last_db and last_file and last_private_file):
			self.take_dump()
			if not ignore_files:
				self.zip_files()

		else:
			self.backup_path_files = last_file
			self.backup_path_db = last_db
			self.backup_path_private_files = last_private_file
			self.backup_path_tab = last_tab

	def set_backup_file_name(self):
		todays_date = now_datetime().strftime('%Y%m%d_%H%M%S')
		site = frappe.local.site or frappe.generate_hash(length=8)
		site = site.replace('.', '_')

		for_db = todays_date + "-" + site + "-database.sql.gz"
		for_public_files = todays_date + "-" + site + "-files.tar"
		for_private_files = todays_date + "-" + site + "-private-files.tar"
		
		for_tab = todays_date + "-" + site +"-"+self.business+"-"+self.table.replace(" ","")+"-database-table.sql.gz"
		backup_path = get_backup_path()
		if self.business:
			if not os.path.exists(os.path.join(backup_path, self.business)):
				frappe.create_folder(os.path.join(backup_path, self.business))
			backup_path = backup_path+"/"+self.business
		if self.add_folder:
			if not os.path.exists(os.path.join(backup_path, self.add_folder)):
				frappe.create_folder(os.path.join(backup_path, self.add_folder))
			backup_path = backup_path+"/"+self.add_folder
		
		if not self.backup_path_db:
			self.backup_path_db = os.path.join(backup_path, for_db)
		if not self.backup_path_files:
			self.backup_path_files = os.path.join(backup_path, for_public_files)
		if not self.backup_path_private_files:
			self.backup_path_private_files = os.path.join(backup_path, for_private_files)
		
		if not self.backup_path_tab:
			self.backup_path_tab = os.path.join(backup_path, for_tab)

	def get_recent_backup(self, older_than):
		backup_path_list = get_backup_path()
		if self.business:
			if not os.path.exists(os.path.join(backup_path, self.business)):
				frappe.create_folder(os.path.join(backup_path, self.business))
			backup_path = backup_path+"/"+self.business
		if self.add_folder:
			if not os.path.exists(os.path.join(backup_path, self.add_folder)):
				frappe.create_folder(os.path.join(backup_path, self.add_folder))
			backup_path = backup_path+"/"+self.add_folder
		file_list = os.listdir(backup_path_list)
		backup_path_files = None
		backup_path_db = None
		backup_path_private_files = None
		backup_path_tab=None
		for this_file in file_list:
			this_file = cstr(this_file)
			this_file_path = os.path.join(backup_path_list, this_file)
			if not is_file_old(this_file_path, older_than):
				if "_private_files" in this_file_path:
					backup_path_private_files = this_file_path
				elif "_files" in this_file_path:
					backup_path_files = this_file_path
				elif "_database_table" in this_file_path:
					backup_path_db = this_file_path
				elif "_database" in this_file_path:
					backup_path_db = this_file_path

		return (backup_path_db, backup_path_tab, backup_path_files, backup_path_private_files)

	def zip_files(self):
		pass
		
		for folder in ("public", "private"):
			files_path = frappe.get_site_path(folder, "files")
			backup_path = self.backup_path_files if folder=="public" else self.backup_path_private_files

	def take_dump(self):
		import frappe.utils
		self.take_table_dump()

	def take_table_dump(self):
		import frappe.utils
		args = dict([item[0], frappe.utils.esc(item[1], '$ ')]
			for item in self.__dict__.copy().items())
		print("--------------------backup-------------------------")
		print(args)
		cmd_string = """mysqldump -u %(user)s -p%(password)s --skip-triggers --compact --no-create-info %(db_name)s --tables %(table)s --where="business = '%(business)s' or restaurant='%(business)s'" -h %(db_host)s | gzip > %(backup_path_tab)s """ % args
		print(cmd_string)
		err, out = frappe.utils.execute_in_shell(cmd_string)
		print(err)
		print(out)

	def send_email(self):
		"""
			Sends the link to backup file located at erpnext/backups
		"""
		from frappe.email import get_system_managers

		recipient_list = get_system_managers()
		db_backup_url = get_url(os.path.join('backups', os.path.basename(self.backup_path_db)))
		files_backup_url = get_url(os.path.join('backups', os.path.basename(self.backup_path_files)))

		msg = """Hello,

Your backups are ready to be downloaded.

1. [Click here to download the database backup](%(db_backup_url)s)
2. [Click here to download the files backup](%(files_backup_url)s)

This link will be valid for 24 hours. A new backup will be available for
download only after 24 hours.""" % {
			"db_backup_url": db_backup_url,
			"files_backup_url": files_backup_url
		}

		datetime_str = datetime.fromtimestamp(os.stat(self.backup_path_db).st_ctime)
		subject = datetime_str.strftime("%d/%m/%Y %H:%M:%S") + """ - Backup ready to be downloaded"""

		frappe.sendmail(recipients=recipient_list, msg=msg, subject=subject)
		return recipient_list


@frappe.whitelist()
def get_backup():
	"""
		This function is executed when the user clicks on
		Toos > Download Backup
	"""
	odb = BackupGenerator(frappe.conf.db_name, frappe.conf.db_name,\
						  frappe.conf.db_password, db_host = frappe.db.host)
	odb.get_backup()
	recipient_list = odb.send_email()
	frappe.msgprint(_("Download link for your backup will be emailed on the following email address: {0}").format(', '.join(recipient_list)))

def scheduled_backup(older_than=6, ignore_files=False, backup_path_db=None, backup_path_tab=None, backup_path_files=None, backup_path_private_files=None, business=None, table=None, add_folder=None, force=False):
	"""this function is called from scheduler
		deletes backups older than 7 days
		takes backup"""
	
	odb = new_backup(older_than, ignore_files, backup_path_db=backup_path_db, backup_path_tab=backup_path_tab, backup_path_files=backup_path_files, business=business, table=table, add_folder=add_folder, force=force)
	return odb

def new_backup(older_than=6, ignore_files=False, backup_path_db=None, backup_path_tab=None, backup_path_files=None, business=None, table=None, add_folder=None, backup_path_private_files=None, force=False):
	
	odb = BackupGenerator(frappe.conf.db_name, frappe.conf.db_name,\
						  frappe.conf.db_password,
						  backup_path_db=backup_path_db, backup_path_tab=backup_path_tab, backup_path_files=backup_path_files,business=business, 							  table=table, add_folder=add_folder,
						  backup_path_private_files=backup_path_private_files,
						  db_host = frappe.db.host)
	odb.get_backup(older_than, ignore_files, force=force)
	return odb

def delete_temp_backups(business=None, add_folder=None, older_than=24):
	"""
		Cleans up the backup_link_path directory by deleting files older than 24 hours
	"""
	backup_path = get_backup_path()
	
	if business:
		if not os.path.exists(os.path.join(backup_path, business)):
			frappe.create_folder(os.path.join(backup_path, business))
		backup_path = backup_path+"/"+business
	if add_folder:
		if not os.path.exists(os.path.join(backup_path, add_folder)):
			frappe.create_folder(os.path.join(backup_path, add_folder))
		backup_path = backup_path+"/"+add_folder
	if os.path.exists(backup_path):
		file_list = os.listdir(backup_path)
		for this_file in file_list:
			this_file_path = os.path.join(backup_path, this_file)
			if is_file_old(this_file_path, older_than):
				os.remove(this_file_path)

def is_file_old(db_file_name, older_than=24):
		"""
			Checks if file exists and is older than specified hours
			Returns ->
			True: file does not exist or file is old
			False: file is new
		"""
		if os.path.isfile(db_file_name):
			from datetime import timedelta
			file_datetime = datetime.fromtimestamp\
						(os.stat(db_file_name).st_ctime)
			if datetime.today() - file_datetime >= timedelta(hours = older_than):
				if verbose: print("File is old")
				return True
			else:
				if verbose: print("File is recent")
				return False
		else:
			if verbose: print("File does not exist")
			return True

def get_backup_path():
	backup_path = frappe.utils.get_site_path(conf.get("backup_path", "private/backups"))
	return backup_path

def backup(with_files=False, backup_path_db=None, backup_path_tab=None, backup_path_files=None, business=None, table=None, add_folder=None, quiet=False):
	"Backup"
	
	odb = scheduled_backup(ignore_files=not with_files, backup_path_db=backup_path_db, backup_path_tab=backup_path_tab, backup_path_files=backup_path_files, business=business, table=table, add_folder=add_folder, force=True)
	return {
		"backup_path_db": odb.backup_path_db,
		"backup_path_tab": odb.backup_path_tab,
		"backup_path_files": odb.backup_path_files,
		"backup_path_private_files": odb.backup_path_private_files,
		"business": odb.business,
		"table": odb.table,
		"add_folder":odb.add_folder
	}

if __name__ == "__main__":
	"""
		is_file_old db_name user password db_host
		get_backup  db_name user password db_host
	"""
	import sys
	cmd = sys.argv[1]
	if cmd == "is_file_old":
		odb = BackupGenerator(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] or "localhost")
		is_file_old(odb.db_file_name)

	if cmd == "get_backup":
		odb = BackupGenerator(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] or "localhost")
		odb.get_backup()

	if cmd == "take_dump":
		odb = BackupGenerator(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] or "localhost")
		odb.take_dump()

	if cmd == "send_email":
		odb = BackupGenerator(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] or "localhost")
		odb.send_email("abc.sql.gz")
