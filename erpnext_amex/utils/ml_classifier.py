# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
import json
import boto3
from botocore.exceptions import ClientError


def classify_transaction(transaction_data):
	"""
	Classify a transaction using SageMaker endpoint
	
	Args:
		transaction_data: Dictionary with transaction details
	
	Returns:
		dict: Classification prediction with confidence
	"""
	settings = frappe.get_single('AMEX Integration Settings')
	
	if not settings.enable_ml_classification:
		return None
	
	if not settings.sagemaker_endpoint_name:
		frappe.log_error("SageMaker endpoint not configured", "ML Classifier Error")
		return None
	
	try:
		# Initialize SageMaker runtime client
		runtime = get_sagemaker_runtime_client(settings)
		
		# Prepare payload
		payload = {
			'vendor_description': transaction_data.get('description', ''),
			'amount': transaction_data.get('amount', 0),
			'amex_category': transaction_data.get('amex_category', ''),
			'date': transaction_data.get('transaction_date', ''),
			'card_member': transaction_data.get('card_member', '')
		}
		
		# Invoke endpoint
		response = runtime.invoke_endpoint(
			EndpointName=settings.sagemaker_endpoint_name,
			ContentType='application/json',
			Body=json.dumps(payload)
		)
		
		# Parse response
		result = json.loads(response['Body'].read().decode())
		
		# Extract first result (for single transaction)
		if isinstance(result, list) and len(result) > 0:
			return result[0]
		
		return result
	
	except Exception as e:
		frappe.log_error(f"SageMaker Classification Error: {str(e)}", "ML Classifier Error")
		return None


def batch_classify_transactions(transactions):
	"""
	Classify multiple transactions in batch
	
	Args:
		transactions: List of transaction dictionaries
	
	Returns:
		list: List of classification predictions
	"""
	settings = frappe.get_single('AMEX Integration Settings')
	
	if not settings.enable_ml_classification:
		return []
	
	try:
		runtime = get_sagemaker_runtime_client(settings)
		
		# Prepare payload for batch
		payload = []
		for trans in transactions:
			payload.append({
				'vendor_description': trans.get('description', ''),
				'amount': trans.get('amount', 0),
				'amex_category': trans.get('amex_category', ''),
				'date': trans.get('transaction_date', ''),
				'card_member': trans.get('card_member', '')
			})
		
		# Invoke endpoint
		response = runtime.invoke_endpoint(
			EndpointName=settings.sagemaker_endpoint_name,
			ContentType='application/json',
			Body=json.dumps(payload)
		)
		
		# Parse response
		results = json.loads(response['Body'].read().decode())
		
		return results
	
	except Exception as e:
		frappe.log_error(f"Batch SageMaker Classification Error: {str(e)}", "ML Classifier Error")
		return []


def get_sagemaker_runtime_client(settings):
	"""
	Get boto3 SageMaker runtime client with credentials from settings
	
	Args:
		settings: AMEX Integration Settings document
	
	Returns:
		boto3 client
	"""
	# Get credentials
	aws_access_key = settings.get_password('aws_access_key_id')
	aws_secret_key = settings.get_password('aws_secret_access_key')
	aws_region = settings.aws_region or 'us-east-1'
	
	if not aws_access_key or not aws_secret_key:
		raise ValueError("AWS credentials not configured in AMEX Integration Settings")
	
	# Create client
	runtime = boto3.client(
		'sagemaker-runtime',
		aws_access_key_id=aws_access_key,
		aws_secret_access_key=aws_secret_key,
		region_name=aws_region
	)
	
	return runtime


def apply_ml_classification(transaction_doc, auto_accept=False):
	"""
	Apply ML classification to a transaction document
	
	Args:
		transaction_doc: AMEX Transaction document
		auto_accept: Whether to auto-accept high-confidence predictions
	
	Returns:
		bool: True if classification was applied
	"""
	settings = frappe.get_single('AMEX Integration Settings')
	
	if not settings.enable_ml_classification:
		return False
	
	# Get classification
	transaction_data = {
		'description': transaction_doc.description,
		'amount': transaction_doc.amount,
		'amex_category': transaction_doc.amex_category,
		'transaction_date': transaction_doc.transaction_date,
		'card_member': transaction_doc.card_member
	}
	
	prediction = classify_transaction(transaction_data)
	
	if not prediction:
		return False
	
	# Store ML predictions
	transaction_doc.ml_predicted_vendor = prediction.get('vendor')
	transaction_doc.ml_predicted_account = prediction.get('expense_account')
	transaction_doc.ml_predicted_cost_center = prediction.get('cost_center')
	transaction_doc.ml_confidence_score = prediction.get('confidence', 0)
	transaction_doc.ml_split_recommended = prediction.get('split_recommended', 0)
	
	# Auto-accept if confidence is high enough
	if auto_accept and prediction.get('confidence', 0) >= settings.ml_auto_accept_threshold:
		# Find actual vendor/account/cost center if they exist
		vendor = frappe.db.get_value('Supplier', {'supplier_name': prediction.get('vendor')}, 'name')
		account = frappe.db.get_value('Account', prediction.get('expense_account'), 'name')
		cost_center = frappe.db.get_value('Cost Center', prediction.get('cost_center'), 'name')
		
		if account:  # Account is required
			transaction_doc.vendor = vendor
			transaction_doc.expense_account = account
			transaction_doc.cost_center = cost_center
			transaction_doc.status = 'Classified'
			transaction_doc.classification_notes = f"Auto-classified by ML (confidence: {prediction.get('confidence', 0):.2%})"
	
	return True


def parse_prediction_response(response):
	"""
	Parse and validate prediction response
	
	Args:
		response: Response from SageMaker endpoint
	
	Returns:
		dict: Parsed and validated prediction
	"""
	if not response:
		return None
	
	# Ensure all expected fields are present
	prediction = {
		'vendor': response.get('vendor'),
		'expense_account': response.get('expense_account'),
		'cost_center': response.get('cost_center'),
		'confidence': float(response.get('confidence', 0)),
		'split_recommended': bool(response.get('split_recommended', False))
	}
	
	return prediction


