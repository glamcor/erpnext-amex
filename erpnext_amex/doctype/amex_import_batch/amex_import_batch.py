# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext_amex.utils.csv_parser import parse_amex_csv, create_import_batch


class AMEXImportBatch(Document):
	def validate(self):
		"""Validate the batch before saving"""
		if not self.batch_reference:
			self.batch_reference = self.name
	
	def on_submit(self):
		"""Process the CSV file when batch is submitted"""
		pass
	
	def after_insert(self):
		"""Process CSV file after batch is created"""
		if self.csv_file:
			self.process_csv()
	
	def process_csv(self):
		"""Parse and process the uploaded CSV file"""
		try:
			# Get the file path
			file_doc = frappe.get_doc("File", {"file_url": self.csv_file})
			file_path = file_doc.get_full_path()
			
			# Parse CSV and create transactions
			result = parse_amex_csv(file_path, self.name)
			
			# Update batch summary
			self.total_transactions = result.get("total", 0)
			self.duplicate_count = result.get("duplicates", 0)
			self.excluded_count = result.get("excluded", 0)
			self.pending_count = result.get("pending", 0)
			self.status = "In Review"
			self.save()
			
			frappe.msgprint(f"Imported {self.total_transactions} transactions. {self.duplicate_count} duplicates, {self.excluded_count} payments excluded.")
			
		except Exception as e:
			frappe.log_error(f"Error processing CSV: {str(e)}", "AMEX Import Error")
			self.status = "Error"
			self.save()
			frappe.throw(f"Error processing CSV file: {str(e)}")

