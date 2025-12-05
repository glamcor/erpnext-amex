# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate, flt


def create_journal_entry_from_transaction(transaction_doc):
	"""
	Create a Journal Entry from an AMEX Transaction
	
	Args:
		transaction_doc: AMEX Transaction document
	
	Returns:
		doc: Journal Entry document
	"""
	# Get settings
	settings = frappe.get_single('AMEX Integration Settings')
	
	# Use transaction's card account (from batch), fall back to settings if not set
	amex_liability_account = transaction_doc.amex_card_account or settings.amex_liability_account
	
	if not amex_liability_account:
		frappe.throw("AMEX Card Account not set on transaction and no default configured in AMEX Integration Settings")
	
	if not transaction_doc.expense_account:
		frappe.throw("Expense Account is required")
	
	# Validate vendor requirement
	if settings.require_vendor_for_posting and not transaction_doc.vendor:
		frappe.throw("Vendor is required for posting")
	
	# Create Journal Entry
	je = frappe.get_doc({
		'doctype': 'Journal Entry',
		'posting_date': transaction_doc.transaction_date or nowdate(),
		'company': frappe.defaults.get_user_default('Company'),
		'user_remark': get_journal_entry_remark(transaction_doc),
		'amex_transaction_reference': transaction_doc.name
	})
	
	# Add custom field link if it exists
	if hasattr(je, 'amex_transaction_reference'):
		je.amex_transaction_reference = transaction_doc.name
	
	# Add debit entries (Expense) and determine credit entry details
	if transaction_doc.cost_center_splits and len(transaction_doc.cost_center_splits) > 0:
		# Multiple cost centers (split allocation)
		# Each split has its own cost center and accounting class
		
		# For the credit side, use the first split's cost center and accounting class
		first_split = transaction_doc.cost_center_splits[0]
		credit_cost_center = first_split.cost_center
		credit_accounting_class = getattr(first_split, 'accounting_class', None)
		
		# Build credit entry (AMEX Liability)
		credit_entry = {
			'account': amex_liability_account,
			'cost_center': credit_cost_center,
			'credit_in_account_currency': abs(transaction_doc.amount)
		}
		if credit_accounting_class:
			credit_entry['accounting_class'] = credit_accounting_class
		je.append('accounts', credit_entry)
		
		# Add debit entries - one per split, each with its own accounting class
		for split in transaction_doc.cost_center_splits:
			amount = split.amount or 0
			
			# Calculate amount from percentage if amount not provided
			if not amount and split.percentage:
				amount = flt(transaction_doc.amount * split.percentage / 100, 2)
			
			split_accounting_class = getattr(split, 'accounting_class', None)
			
			debit_entry = {
				'account': transaction_doc.expense_account,
				'cost_center': split.cost_center,
				'debit_in_account_currency': amount,
				'party_type': 'Supplier' if transaction_doc.vendor else None,
				'party': transaction_doc.vendor if transaction_doc.vendor else None,
				'user_remark': split.notes or ''
			}
			# Add accounting class from the split (each line gets its own class)
			if split_accounting_class:
				debit_entry['accounting_class'] = split_accounting_class
			je.append('accounts', debit_entry)
	else:
		# Single cost center - use transaction-level accounting class
		credit_cost_center = transaction_doc.cost_center
		accounting_class = getattr(transaction_doc, 'accounting_class', None)
		
		# Build credit entry (AMEX Liability)
		credit_entry = {
			'account': amex_liability_account,
			'cost_center': credit_cost_center,
			'credit_in_account_currency': abs(transaction_doc.amount)
		}
		if accounting_class:
			credit_entry['accounting_class'] = accounting_class
		je.append('accounts', credit_entry)
		
		# Single debit entry
		debit_entry = {
			'account': transaction_doc.expense_account,
			'cost_center': transaction_doc.cost_center,
			'debit_in_account_currency': abs(transaction_doc.amount),
			'party_type': 'Supplier' if transaction_doc.vendor else None,
			'party': transaction_doc.vendor if transaction_doc.vendor else None
		}
		if accounting_class:
			debit_entry['accounting_class'] = accounting_class
		je.append('accounts', debit_entry)
	
	# Save and submit
	je.insert(ignore_permissions=True)
	je.submit()
	frappe.db.commit()
	
	return je


def create_bulk_journal_entries(transaction_list):
	"""
	Create journal entries for multiple transactions
	
	Args:
		transaction_list: List of AMEX Transaction names or documents
	
	Returns:
		dict: Summary of results
	"""
	success_count = 0
	error_count = 0
	errors = []
	
	for transaction in transaction_list:
		try:
			if isinstance(transaction, str):
				transaction_doc = frappe.get_doc('AMEX Transaction', transaction)
			else:
				transaction_doc = transaction
			
			# Check if already posted
			if transaction_doc.journal_entry:
				continue
			
			# Check if approved
			if transaction_doc.status != 'Approved':
				errors.append(f"{transaction_doc.name}: Not approved")
				error_count += 1
				continue
			
			# Create journal entry
			je = create_journal_entry_from_transaction(transaction_doc)
			
			# Update transaction
			transaction_doc.journal_entry = je.name
			transaction_doc.status = 'Posted'
			transaction_doc.save(ignore_permissions=True)
			
			success_count += 1
			
		except Exception as e:
			error_count += 1
			error_msg = f"{transaction_doc.name if 'transaction_doc' in locals() else transaction}: {str(e)}"
			errors.append(error_msg)
			frappe.log_error(error_msg, "Bulk Journal Entry Creation Error")
	
	frappe.db.commit()
	
	return {
		'success': success_count,
		'errors': error_count,
		'error_messages': errors
	}


def get_journal_entry_remark(transaction_doc):
	"""
	Generate remark for journal entry
	
	Args:
		transaction_doc: AMEX Transaction document
	
	Returns:
		str: Remark text
	"""
	remark_parts = []
	
	remark_parts.append(f"AMEX Transaction: {transaction_doc.reference}")
	remark_parts.append(f"Card Member: {transaction_doc.card_member}")
	remark_parts.append(f"Description: {transaction_doc.description}")
	
	if transaction_doc.vendor:
		vendor_name = frappe.db.get_value('Supplier', transaction_doc.vendor, 'supplier_name')
		remark_parts.append(f"Vendor: {vendor_name}")
	
	if transaction_doc.classification_notes:
		remark_parts.append(f"Notes: {transaction_doc.classification_notes}")
	
	return " | ".join(remark_parts)


def validate_journal_entry_data(transaction_doc):
	"""
	Validate that transaction has all required data for journal entry
	
	Args:
		transaction_doc: AMEX Transaction document
	
	Returns:
		tuple: (bool, str) - (is_valid, error_message)
	"""
	settings = frappe.get_single('AMEX Integration Settings')
	
	# Check for AMEX card account (transaction-level takes priority)
	amex_liability_account = transaction_doc.amex_card_account or settings.amex_liability_account
	if not amex_liability_account:
		return False, "AMEX Card Account not set on transaction and no default configured"
	
	if not transaction_doc.expense_account:
		return False, "Expense Account is required"
	
	if settings.require_vendor_for_posting and not transaction_doc.vendor:
		return False, "Vendor is required"
	
	# Validate cost center
	if not transaction_doc.cost_center and not transaction_doc.cost_center_splits:
		return False, "Cost Center is required"
	
	# Validate splits if present
	if transaction_doc.cost_center_splits:
		total = sum([s.amount or 0 for s in transaction_doc.cost_center_splits])
		if abs(total - transaction_doc.amount) > 0.01:
			return False, f"Cost center split amounts ({total}) must equal transaction amount ({transaction_doc.amount})"
	
	# Check for duplicates
	if transaction_doc.is_duplicate:
		return False, "Cannot post duplicate transaction"
	
	# Check for AMEX payments
	if transaction_doc.is_amex_payment:
		return False, "Cannot post AMEX payment transaction"
	
	return True, ""


def reverse_journal_entry(transaction_doc):
	"""
	Reverse a journal entry for a transaction
	
	Args:
		transaction_doc: AMEX Transaction document
	
	Returns:
		doc: Reversed Journal Entry document
	"""
	if not transaction_doc.journal_entry:
		frappe.throw("No journal entry found to reverse")
	
	original_je = frappe.get_doc('Journal Entry', transaction_doc.journal_entry)
	
	if original_je.docstatus != 1:
		frappe.throw("Original journal entry is not submitted")
	
	# Cancel original
	original_je.cancel()
	
	# Update transaction status
	transaction_doc.journal_entry = None
	transaction_doc.status = 'Approved'
	transaction_doc.save(ignore_permissions=True)
	
	frappe.db.commit()
	
	return original_je


