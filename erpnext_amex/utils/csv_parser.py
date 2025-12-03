# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import csv
import frappe
from frappe.utils import nowdate, flt


def parse_amex_csv(file_path, batch_id):
	"""
	Parse AMEX CSV file and create transaction records
	
	Args:
		file_path: Path to the CSV file
		batch_id: AMEX Import Batch ID
	
	Returns:
		dict: Summary of import results
	"""
	transactions = []
	duplicate_count = 0
	excluded_count = 0
	
	# Get the batch to retrieve the AMEX card account
	batch = frappe.get_doc('AMEX Import Batch', batch_id)
	amex_card_account = batch.amex_card_account
	
	try:
		with open(file_path, 'r', encoding='utf-8') as csvfile:
			# Read CSV with proper handling of multi-line fields
			reader = csv.DictReader(csvfile)
			
			for row in reader:
				# Skip empty rows
				if not row.get('Date') or not row.get('Amount'):
					continue
				
				# Parse transaction data
				transaction_data = {
					'batch_id': batch_id,
					'amex_card_account': amex_card_account,
					'transaction_date': parse_date(row.get('Date')),
					'description': row.get('Description', '').strip(),
					'card_member': row.get('Card Member', '').strip(),
					'account_number': row.get('Account #', '').strip(),
					'amount': flt(row.get('Amount', 0)),
					'extended_details': row.get('Extended Details', '').strip(),
					'statement_description': row.get('Appears On Your Statement As', '').strip(),
					'address': row.get('Address', '').strip(),
					'city_state': row.get('City/State', '').strip(),
					'zip_code': row.get('Zip Code', '').strip(),
					'country': row.get('Country', '').strip(),
					'reference': row.get('Reference', '').strip().replace("'", ""),
					'amex_category': row.get('Category', '').strip(),
					'status': 'Pending'
				}
				
				# Check for duplicates
				if detect_duplicate(transaction_data['reference']):
					transaction_data['is_duplicate'] = 1
					transaction_data['status'] = 'Duplicate'
					duplicate_count += 1
				
				# Check if AMEX payment
				if identify_amex_payment(transaction_data):
					transaction_data['is_amex_payment'] = 1
					transaction_data['status'] = 'Excluded'
					excluded_count += 1
				
				transactions.append(transaction_data)
		
		# Create transaction records in database
		for trans_data in transactions:
			try:
				trans_doc = frappe.get_doc({
					'doctype': 'AMEX Transaction',
					**trans_data
				})
				trans_doc.insert(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(f"Error creating transaction: {str(e)}", "AMEX Transaction Import Error")
		
		# Commit the transactions
		frappe.db.commit()
		
		pending_count = len([t for t in transactions if t['status'] == 'Pending'])
		
		return {
			'total': len(transactions),
			'duplicates': duplicate_count,
			'excluded': excluded_count,
			'pending': pending_count
		}
	
	except Exception as e:
		frappe.log_error(f"Error parsing CSV: {str(e)}", "CSV Parser Error")
		raise


def parse_date(date_str):
	"""Parse date from AMEX CSV format (MM/DD/YYYY)"""
	if not date_str:
		return nowdate()
	
	try:
		# Handle MM/DD/YYYY format
		from datetime import datetime
		date_obj = datetime.strptime(date_str.strip(), '%m/%d/%Y')
		return date_obj.strftime('%Y-%m-%d')
	except:
		return nowdate()


def detect_duplicate(reference):
	"""
	Check if a transaction with this reference already exists
	
	Args:
		reference: Transaction reference ID
	
	Returns:
		bool: True if duplicate found
	"""
	if not reference:
		return False
	
	existing = frappe.db.exists('AMEX Transaction', {'reference': reference})
	return bool(existing)


def identify_amex_payment(transaction_data):
	"""
	Identify if transaction is an AMEX payment (should be excluded)
	
	Args:
		transaction_data: Dictionary of transaction data
	
	Returns:
		bool: True if this is an AMEX payment
	"""
	# Payment keywords to look for
	payment_patterns = [
		'ONLINE PAYMENT',
		'THANK YOU',
		'PAYMENT RECEIVED',
		'AUTOPAY',
		'AUTOMATIC PAYMENT'
	]
	
	description = (transaction_data.get('description') or '').upper()
	
	# Check description for payment patterns
	if any(pattern in description for pattern in payment_patterns):
		return True
	
	# Check for negative amounts (credits/payments)
	amount = transaction_data.get('amount', 0)
	if amount < 0:
		return True
	
	return False


def validate_transaction_data(transaction_data):
	"""
	Validate transaction data before creating record
	
	Args:
		transaction_data: Dictionary of transaction data
	
	Returns:
		bool: True if valid
	"""
	required_fields = ['transaction_date', 'description', 'card_member', 'amount', 'reference']
	
	for field in required_fields:
		if not transaction_data.get(field):
			frappe.throw(f"Missing required field: {field}")
	
	return True


def create_import_batch(csv_file, user):
	"""
	Create an AMEX Import Batch record
	
	Args:
		csv_file: File path or attachment
		user: User creating the batch
	
	Returns:
		doc: AMEX Import Batch document
	"""
	batch = frappe.get_doc({
		'doctype': 'AMEX Import Batch',
		'import_date': nowdate(),
		'uploaded_by': user,
		'csv_file': csv_file,
		'status': 'Draft'
	})
	batch.insert(ignore_permissions=True)
	frappe.db.commit()
	
	return batch

