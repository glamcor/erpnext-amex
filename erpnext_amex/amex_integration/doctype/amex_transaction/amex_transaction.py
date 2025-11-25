# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, now


class AMEXTransaction(Document):
	def validate(self):
		"""Validate the transaction before saving"""
		self.validate_cost_center_splits()
		self.check_duplicate()
		self.detect_amex_payment()
	
	def validate_cost_center_splits(self):
		"""Ensure cost center splits total correctly"""
		if not self.cost_center_splits:
			return
		
		total_amount = sum([split.amount or 0 for split in self.cost_center_splits])
		total_percentage = sum([split.percentage or 0 for split in self.cost_center_splits])
		
		# Check if using amounts
		if any([split.amount for split in self.cost_center_splits]):
			if abs(total_amount - self.amount) > 0.01:  # Allow for rounding errors
				frappe.throw(f"Cost center split amounts ({total_amount}) must equal transaction amount ({self.amount})")
		
		# Check if using percentages
		if any([split.percentage for split in self.cost_center_splits]):
			if abs(total_percentage - 100) > 0.01:  # Allow for rounding errors
				frappe.throw(f"Cost center split percentages ({total_percentage}%) must total 100%")
	
	def check_duplicate(self):
		"""Check if this is a duplicate transaction"""
		if not self.reference:
			return
		
		# Check for existing transactions with same reference (excluding self)
		existing = frappe.db.exists("AMEX Transaction", {
			"reference": self.reference,
			"name": ["!=", self.name]
		})
		
		if existing:
			self.is_duplicate = 1
			self.duplicate_reference = existing
			self.status = "Duplicate"
	
	def detect_amex_payment(self):
		"""Detect if this is an AMEX payment transaction"""
		payment_patterns = [
			"ONLINE PAYMENT",
			"THANK YOU",
			"PAYMENT RECEIVED"
		]
		
		# Check description for payment patterns
		if any(pattern in (self.description or "").upper() for pattern in payment_patterns):
			self.is_amex_payment = 1
			self.status = "Excluded"
			return
		
		# Check for negative amounts (credits)
		if self.amount < 0:
			self.is_amex_payment = 1
			self.status = "Excluded"
	
	def classify(self, vendor=None, expense_account=None, cost_center=None, notes=None):
		"""Classify the transaction"""
		if vendor:
			self.vendor = vendor
		if expense_account:
			self.expense_account = expense_account
		if cost_center:
			self.cost_center = cost_center
		if notes:
			self.classification_notes = notes
		
		self.classified_by = frappe.session.user
		self.classification_date = now()
		self.status = "Classified"
		self.save()
	
	def approve(self):
		"""Approve the classified transaction"""
		if not self.expense_account:
			frappe.throw("Expense account is required for approval")
		
		if not self.cost_center and not self.cost_center_splits:
			frappe.throw("Cost center or cost center splits are required for approval")
		
		self.status = "Approved"
		self.save()
	
	def post_to_journal_entry(self):
		"""Post transaction to journal entry"""
		from erpnext_amex.utils.journal_entry_creator import create_journal_entry_from_transaction
		
		if self.status != "Approved":
			frappe.throw("Transaction must be approved before posting")
		
		if self.is_duplicate or self.is_amex_payment:
			frappe.throw("Cannot post duplicate or payment transactions")
		
		# Create journal entry
		je = create_journal_entry_from_transaction(self)
		
		self.journal_entry = je.name
		self.posted_date = now()
		self.status = "Posted"
		self.save()
		
		return je

