# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
from erpnext_amex.utils.classification_memory import get_classification_suggestion, learn_from_transaction
from erpnext_amex.utils.journal_entry_creator import create_journal_entry_from_transaction, create_bulk_journal_entries


@frappe.whitelist()
def get_pending_transactions(filters=None):
	"""Get list of pending transactions for review"""
	if filters is None:
		filters = {}
	elif isinstance(filters, str):
		filters = json.loads(filters)
	
	# Build filter conditions
	conditions = ["status IN ('Pending', 'Classified')"]
	
	if filters.get('batch_id'):
		conditions.append(f"batch_id = '{filters['batch_id']}'")
	
	if filters.get('card_member'):
		conditions.append(f"card_member LIKE '%{filters['card_member']}%'")
	
	if filters.get('from_date'):
		conditions.append(f"transaction_date >= '{filters['from_date']}'")
	
	if filters.get('to_date'):
		conditions.append(f"transaction_date <= '{filters['to_date']}'")
	
	if filters.get('min_amount'):
		conditions.append(f"amount >= {filters['min_amount']}")
	
	if filters.get('max_amount'):
		conditions.append(f"amount <= {filters['max_amount']}")
	
	where_clause = " AND ".join(conditions) if conditions else "1=1"
	
	transactions = frappe.db.sql(f"""
		SELECT 
			name, transaction_date, description, card_member, 
			amount, status, vendor, expense_account, cost_center,
			reference, amex_category, is_duplicate, is_amex_payment,
			ml_confidence_score, ml_predicted_vendor
		FROM `tabAMEX Transaction`
		WHERE {where_clause}
		ORDER BY transaction_date DESC, name DESC
		LIMIT 500
	""", as_dict=True)
	
	# Get suggestions for each transaction
	for trans in transactions:
		suggestion = get_classification_suggestion(trans.description, trans.amount)
		if suggestion:
			trans['suggestion'] = suggestion
	
	return transactions


@frappe.whitelist()
def get_transaction_details(transaction_name):
	"""Get full details of a transaction"""
	transaction = frappe.get_doc('AMEX Transaction', transaction_name)
	
	# Get suggestion
	suggestion = get_classification_suggestion(transaction.description, transaction.amount)
	
	return {
		'transaction': transaction.as_dict(),
		'suggestion': suggestion
	}


@frappe.whitelist()
def classify_transaction(transaction_name, vendor=None, expense_account=None, cost_center=None, notes=None, cost_center_splits=None):
	"""
	Classify a transaction
	
	Args:
		transaction_name: Name of the transaction
		vendor: Supplier name (optional)
		expense_account: Account name
		cost_center: Cost Center name (for single allocation)
		notes: Classification notes
		cost_center_splits: List of splits for multi-center allocation
	"""
	transaction = frappe.get_doc('AMEX Transaction', transaction_name)
	
	# Update classification
	if vendor:
		transaction.vendor = vendor
	if expense_account:
		transaction.expense_account = expense_account
	if cost_center:
		transaction.cost_center = cost_center
	if notes:
		transaction.classification_notes = notes
	
	# Handle splits
	if cost_center_splits:
		transaction.cost_center_splits = []
		for split in cost_center_splits:
			transaction.append('cost_center_splits', split)
	
	transaction.classified_by = frappe.session.user
	transaction.classification_date = frappe.utils.now()
	transaction.status = 'Classified'
	transaction.save(ignore_permissions=True)
	frappe.db.commit()
	
	# Learn from this classification
	learn_from_transaction(transaction)
	
	return {'status': 'success', 'transaction': transaction.as_dict()}


@frappe.whitelist()
def approve_transaction(transaction_name):
	"""Approve a classified transaction"""
	transaction = frappe.get_doc('AMEX Transaction', transaction_name)
	transaction.approve()
	frappe.db.commit()
	
	return {'status': 'success', 'transaction': transaction.as_dict()}


@frappe.whitelist()
def post_transaction(transaction_name):
	"""Post transaction to journal entry"""
	transaction = frappe.get_doc('AMEX Transaction', transaction_name)
	je = transaction.post_to_journal_entry()
	frappe.db.commit()
	
	return {
		'status': 'success',
		'journal_entry': je.name,
		'transaction': transaction.as_dict()
	}


@frappe.whitelist()
def bulk_approve_and_post(transaction_names):
	"""Approve and post multiple transactions"""
	import json
	
	if isinstance(transaction_names, str):
		transaction_names = json.loads(transaction_names)
	
	results = {
		'approved': [],
		'posted': [],
		'errors': []
	}
	
	for trans_name in transaction_names:
		try:
			transaction = frappe.get_doc('AMEX Transaction', trans_name)
			
			# Approve if not already
			if transaction.status == 'Classified':
				transaction.approve()
				results['approved'].append(trans_name)
			
			# Post if approved
			if transaction.status == 'Approved':
				je = transaction.post_to_journal_entry()
				results['posted'].append({'transaction': trans_name, 'journal_entry': je.name})
		
		except Exception as e:
			results['errors'].append({'transaction': trans_name, 'error': str(e)})
	
	frappe.db.commit()
	return results


@frappe.whitelist()
def create_vendor_quick(vendor_name, supplier_group=None, country=None):
	"""Quick create a vendor/supplier"""
	supplier = frappe.get_doc({
		'doctype': 'Supplier',
		'supplier_name': vendor_name,
		'supplier_group': supplier_group or 'All Supplier Groups',
		'country': country or frappe.defaults.get_user_default('country') or 'United States'
	})
	supplier.insert(ignore_permissions=True)
	frappe.db.commit()
	
	return {'status': 'success', 'supplier': supplier.name}


@frappe.whitelist()
def get_filter_options():
	"""Get options for filters"""
	batches = frappe.get_all('AMEX Import Batch', fields=['name', 'import_date'], order_by='import_date desc', limit=50)
	
	card_members = frappe.db.sql("""
		SELECT DISTINCT card_member 
		FROM `tabAMEX Transaction`
		ORDER BY card_member
	""", as_dict=True)
	
	return {
		'batches': batches,
		'card_members': [cm['card_member'] for cm in card_members]
	}


@frappe.whitelist()
def mark_as_duplicate(transaction_name, original_reference=None):
	"""Mark transaction as duplicate"""
	transaction = frappe.get_doc('AMEX Transaction', transaction_name)
	transaction.is_duplicate = 1
	transaction.duplicate_reference = original_reference
	transaction.status = 'Duplicate'
	transaction.save(ignore_permissions=True)
	frappe.db.commit()
	
	return {'status': 'success'}


@frappe.whitelist()
def get_account_list(account_type=None):
	"""Get list of accounts for dropdown"""
	filters = {}
	if account_type:
		filters['account_type'] = account_type
	
	accounts = frappe.get_all('Account', 
		filters=filters,
		fields=['name', 'account_name', 'account_type'],
		order_by='name'
	)
	
	return accounts


@frappe.whitelist()
def get_cost_center_list():
	"""Get list of cost centers for dropdown"""
	cost_centers = frappe.get_all('Cost Center',
		fields=['name', 'cost_center_name', 'parent_cost_center'],
		order_by='name'
	)
	
	return cost_centers


@frappe.whitelist()
def get_supplier_list():
	"""Get list of suppliers for dropdown"""
	suppliers = frappe.get_all('Supplier',
		fields=['name', 'supplier_name'],
		order_by='supplier_name',
		limit=1000
	)
	
	return suppliers


