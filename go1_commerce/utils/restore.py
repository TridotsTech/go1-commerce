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

class RestoreBackup:
	"""
		This class contains methods to perform On Demand Backup Restore

		To initialize, specify (db_name, user, password, db_file_name=None, db_host="localhost")
		If specifying db_file_name, also append ".sql.gz"
	"""
	def __init__(self, db_name, user, password, backup_path_tab=None, db_host="localhost"):
		self.db_host = db_host
		self.db_name = db_name
		self.user = user
		self.password = password
		self.backup_path_tab = backup_path_tab
		
	def get_backup(self, older_than=24, ignore_files=False, force=False):
		"""
			Takes a new dump if existing file is old
			and sends the link to the file as email
		"""
		if not force:
			last_tab= self.get_recent_backup(older_than)
		else:
			last_tab= False

		if not (self.backup_path_tab):
			self.set_backup_file_name()

		if not (last_tab):
			self.restore_dump()
			if not ignore_files:
				self.zip_files()

		else:
			self.backup_path_tab = last_tab

	def set_backup_file_name(self):
		todays_date = now_datetime().strftime('%Y%m%d_%H%M%S')
		site = frappe.local.site or frappe.generate_hash(length=8)
		site = site.replace('.', '_')

		for_tab = todays_date + "-" + site + "-database-table.sql.gz"
		backup_path = get_backup_path()

		if not self.backup_path_tab:
			self.backup_path_tab = os.path.join(backup_path, for_tab)

	def get_recent_backup(self, older_than):
		file_list = os.listdir(get_backup_path())
		backup_path_tab = None
		
		for this_file in file_list:
			this_file = cstr(this_file)
			this_file_path = os.path.join(get_backup_path(), this_file)
			if not is_file_old(this_file_path, older_than):
				if "_database_table" in this_file_path:
					backup_path_tab = this_file_path

		return (backup_path_tab)

	def zip_files(self):
		for folder in ("public", "private"):
			files_path = frappe.get_site_path(folder, "files")
			backup_path = self.backup_path_tab

			cmd_string = """tar -cf %s %s""" % (backup_path, files_path)
			err, out = frappe.utils.execute_in_shell(cmd_string)

			print('Restored files', os.path.abspath(backup_path))

	def restore_dump(self):
		import frappe.utils
		args = dict([item[0], frappe.utils.esc(item[1], '$ ')]
			for item in self.__dict__.copy().items())
		print("--------------------restore_dump-------------------------")
		print(args)
		cmd_string = """mysqldump -u %(user)s -p%(password)s %(db_name)s -h %(db_host)s < %(backup_path_tab)s """ % args
		print(cmd_string)
		err, out = frappe.utils.execute_in_shell(cmd_string)
		print(err)
		print(out)

	


@frappe.whitelist()
def get_backup():
	"""
		This function is executed when the user clicks on
		Toos > Download Backup
	"""
	
	odb = RestoreBackup(frappe.conf.db_name, frappe.conf.db_name,\
						  frappe.conf.db_password, db_host = frappe.db.host)
	odb.get_backup()
	frappe.msgprint(_("Download link for your backup will be stored"))

def scheduled_restore_backup(older_than=6, ignore_files=False, backup_path_tab=None, force=False):
	"""this function is called from scheduler
		deletes backups older than 7 days
		takes backup"""
	odb = restore_backup(older_than, ignore_files, backup_path_tab=backup_path_tab, force=force)
	return odb

def restore_backup(older_than=6, ignore_files=False, backup_path_tab=None, force=False):
	odb = RestoreBackup(frappe.conf.db_name, frappe.conf.db_name,\
						  frappe.conf.db_password,
						  backup_path_tab=backup_path_tab,
						  db_host = frappe.db.host)
	odb.get_backup(older_than, ignore_files, force=force)
	return odb


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


def restore_table_backup(with_files=False, backup_path_tab=None, quiet=False):
	"Backup Restore" 
	from frappe.installer import extract_sql_gzip, extract_tar_files
	if not os.path.exists(backup_path_tab):
		backup_path_tab = '../' + backup_path_tab
		if not os.path.exists(backup_path_tab):
			print('Invalid path {0}'.format(backup_path_tab[3:]))
			sys.exit(1)
	if backup_path_tab.endswith('sql.gz'):backup_path_tab = extract_sql_gzip(os.path.abspath(backup_path_tab))
	print("-----------restore------------")
	print(backup_path_tab)
	odb = scheduled_restore_backup(ignore_files=not with_files, backup_path_tab=backup_path_tab, force=True)
	return {
		"backup_path_db": odb.backup_path_tab
	}

if __name__ == "__main__":
	"""
		is_file_old db_name user password db_host
		get_backup  db_name user password db_host
	"""
	import sys
	print("----------------sys------------------")
	print(sys.argv)
	cmd = sys.argv[1]
	print(cmd)
	if cmd == "restore_dump":
		odb = RestoreBackup(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] or "localhost")
		odb.restore_dump()

	
