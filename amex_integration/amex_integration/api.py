# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json


@frappe.whitelist()
def upload_csv(file_content=None, file_name=None):
	"""
	Upload and process AMEX CSV file
	
	Args:
		file_content: Base64 encoded file content or file URL
		file_name: Name of the file
	
	Returns:
		dict: Result of import
	"""
	try:
		from amex_integration.amex_integration.utils.csv_parser import create_import_batch
		
		# Create batch record
		batch = create_import_batch(file_content, frappe.session.user)
		
		return {
			'status': 'success',
			'batch_id': batch.name,
			'message': 'CSV uploaded successfully'
		}
	
	except Exception as e:
		frappe.log_error(f"CSV Upload Error: {str(e)}", "API Error")
		return {
			'status': 'error',
			'message': str(e)
		}


@frappe.whitelist()
def get_pending_transactions(batch_id=None, card_member=None, limit=100):
	"""
	Get list of pending transactions
	
	Args:
		batch_id: Filter by batch (optional)
		card_member: Filter by card member (optional)
		limit: Maximum number of records
	
	Returns:
		list: Pending transactions
	"""
	filters = {'status': ['in', ['Pending', 'Classified']]}
	
	if batch_id:
		filters['batch_id'] = batch_id
	if card_member:
		filters['card_member'] = card_member
	
	transactions = frappe.get_all(
		'AMEX Transaction',
		filters=filters,
		fields=['name', 'transaction_date', 'description', 'card_member', 'amount', 'status'],
		limit=limit,
		order_by='transaction_date desc'
	)
	
	return transactions


@frappe.whitelist()
def classify_transaction(transaction_name, vendor=None, expense_account=None, cost_center=None, notes=None):
	"""
	Classify a transaction via API
	
	Args:
		transaction_name: Transaction ID
		vendor: Supplier name
		expense_account: Account name
		cost_center: Cost Center name
		notes: Classification notes
	
	Returns:
		dict: Result
	"""
	try:
		transaction = frappe.get_doc('AMEX Transaction', transaction_name)
		transaction.classify(vendor, expense_account, cost_center, notes)
		
		return {
			'status': 'success',
			'transaction': transaction.name,
			'message': 'Transaction classified successfully'
		}
	
	except Exception as e:
		frappe.log_error(f"Classification Error: {str(e)}", "API Error")
		return {
			'status': 'error',
			'message': str(e)
		}


@frappe.whitelist()
def get_batch_status(batch_id):
	"""
	Get status of an import batch
	
	Args:
		batch_id: Batch ID
	
	Returns:
		dict: Batch status and statistics
	"""
	batch = frappe.get_doc('AMEX Import Batch', batch_id)
	
	return {
		'batch_id': batch.name,
		'status': batch.status,
		'total_transactions': batch.total_transactions,
		'processed_count': batch.processed_count,
		'pending_count': batch.pending_count,
		'duplicate_count': batch.duplicate_count,
		'excluded_count': batch.excluded_count
	}


@frappe.whitelist()
def validate_transaction(transaction_name):
	"""
	Validate a transaction before posting
	
	Args:
		transaction_name: Transaction ID
	
	Returns:
		dict: Validation result
	"""
	from amex_integration.amex_integration.utils.journal_entry_creator import validate_journal_entry_data
	
	transaction = frappe.get_doc('AMEX Transaction', transaction_name)
	is_valid, error_msg = validate_journal_entry_data(transaction)
	
	return {
		'valid': is_valid,
		'error': error_msg if not is_valid else None
	}


@frappe.whitelist()
def post_to_journal_entry(transaction_name):
	"""
	Post transaction to journal entry via API
	
	Args:
		transaction_name: Transaction ID
	
	Returns:
		dict: Result with journal entry name
	"""
	try:
		transaction = frappe.get_doc('AMEX Transaction', transaction_name)
		je = transaction.post_to_journal_entry()
		
		return {
			'status': 'success',
			'journal_entry': je.name,
			'transaction': transaction.name
		}
	
	except Exception as e:
		frappe.log_error(f"Post to JE Error: {str(e)}", "API Error")
		return {
			'status': 'error',
			'message': str(e)
		}


@frappe.whitelist()
def get_classification_stats():
	"""
	Get classification statistics
	
	Returns:
		dict: Statistics about transactions
	"""
	total = frappe.db.count('AMEX Transaction')
	
	stats = {
		'total': total,
		'pending': frappe.db.count('AMEX Transaction', {'status': 'Pending'}),
		'classified': frappe.db.count('AMEX Transaction', {'status': 'Classified'}),
		'approved': frappe.db.count('AMEX Transaction', {'status': 'Approved'}),
		'posted': frappe.db.count('AMEX Transaction', {'status': 'Posted'}),
		'duplicates': frappe.db.count('AMEX Transaction', {'is_duplicate': 1}),
		'excluded': frappe.db.count('AMEX Transaction', {'is_amex_payment': 1})
	}
	
	# Calculate percentages
	if total > 0:
		stats['pending_pct'] = round(stats['pending'] / total * 100, 2)
		stats['posted_pct'] = round(stats['posted'] / total * 100, 2)
	
	return stats


@frappe.whitelist()
def get_vendor_suggestions(description):
	"""
	Get vendor suggestions based on description
	
	Args:
		description: Transaction description
	
	Returns:
		dict: Suggested classification
	"""
	from amex_integration.amex_integration.utils.classification_memory import get_classification_suggestion
	
	suggestion = get_classification_suggestion(description)
	
	if suggestion:
		return {
			'has_suggestion': True,
			'vendor': suggestion.get('matched_supplier'),
			'expense_account': suggestion.get('default_expense_account'),
			'cost_center': suggestion.get('default_cost_center'),
			'confidence': suggestion.get('confidence_score')
		}
	else:
		return {
			'has_suggestion': False
		}


@frappe.whitelist()
def bulk_classify_and_post(transactions_json):
	"""
	Bulk classify and post multiple transactions
	
	Args:
		transactions_json: JSON string of list of transactions with classifications
	
	Returns:
		dict: Summary of results
	"""
	try:
		transactions = json.loads(transactions_json) if isinstance(transactions_json, str) else transactions_json
		
		results = {
			'success': [],
			'errors': []
		}
		
		for trans_data in transactions:
			try:
				trans_name = trans_data['transaction_name']
				trans = frappe.get_doc('AMEX Transaction', trans_name)
				
				# Classify
				trans.classify(
					vendor=trans_data.get('vendor'),
					expense_account=trans_data.get('expense_account'),
					cost_center=trans_data.get('cost_center'),
					notes=trans_data.get('notes')
				)
				
				# Approve
				trans.approve()
				
				# Post
				je = trans.post_to_journal_entry()
				
				results['success'].append({
					'transaction': trans_name,
					'journal_entry': je.name
				})
			
			except Exception as e:
				results['errors'].append({
					'transaction': trans_data.get('transaction_name'),
					'error': str(e)
				})
		
		return results
	
	except Exception as e:
		frappe.log_error(f"Bulk Process Error: {str(e)}", "API Error")
		return {
			'status': 'error',
			'message': str(e)
		}

