#!/usr/bin/env python3
"""
Transform NetSuite historical transaction data to ERPNext format for ML training

This script:
1. Reads historical NetSuite JSON transaction data from S3
2. Maps NetSuite structure (Departments, Classes, Accounts) to ERPNext structure
3. Creates clean training dataset for SageMaker
4. Outputs JSON files ready for model training
"""

import json
import os
import boto3
import pandas as pd
from datetime import datetime
import re


class NetSuiteToERPNextTransformer:
	"""Transform NetSuite transaction data to ERPNext format"""
	
	def __init__(self, s3_bucket, s3_prefix, output_dir='training_data'):
		self.s3_bucket = s3_bucket
		self.s3_prefix = s3_prefix
		self.output_dir = output_dir
		self.s3_client = boto3.client('s3')
		
		# Mapping tables (to be customized based on your specific mappings)
		self.department_to_cost_center = {}
		self.class_to_dimension = {}
		self.account_mapping = {}
		
		os.makedirs(output_dir, exist_ok=True)
	
	def load_mapping_config(self, config_file):
		"""Load mapping configuration from JSON file"""
		with open(config_file, 'r') as f:
			config = json.load(f)
		
		self.department_to_cost_center = config.get('department_to_cost_center', {})
		self.class_to_dimension = config.get('class_to_dimension', {})
		self.account_mapping = config.get('account_mapping', {})
	
	def fetch_netsuite_data(self):
		"""Fetch NetSuite JSON files from S3"""
		print(f"Fetching data from s3://{self.s3_bucket}/{self.s3_prefix}")
		
		transactions = []
		
		# List objects in S3
		paginator = self.s3_client.get_paginator('list_objects_v2')
		pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=self.s3_prefix)
		
		for page in pages:
			if 'Contents' not in page:
				continue
			
			for obj in page['Contents']:
				if obj['Key'].endswith('.json'):
					print(f"Processing {obj['Key']}")
					
					# Download and parse JSON
					response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=obj['Key'])
					data = json.loads(response['Body'].read())
					
					# Handle different JSON structures
					if isinstance(data, list):
						transactions.extend(data)
					elif isinstance(data, dict) and 'transactions' in data:
						transactions.extend(data['transactions'])
					else:
						transactions.append(data)
		
		print(f"Fetched {len(transactions)} transactions from NetSuite")
		return transactions
	
	def normalize_vendor_name(self, vendor):
		"""Normalize vendor name for consistency"""
		if not vendor:
			return ''
		
		# Convert to lowercase
		normalized = vendor.lower().strip()
		
		# Remove common suffixes
		suffixes = [' inc', ' llc', ' corp', ' corporation', ' ltd', ' limited']
		for suffix in suffixes:
			if normalized.endswith(suffix):
				normalized = normalized[:-len(suffix)].strip()
		
		# Remove special characters except spaces
		normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
		
		# Normalize whitespace
		normalized = re.sub(r'\s+', ' ', normalized).strip()
		
		return normalized
	
	def map_department_to_cost_center(self, department):
		"""Map NetSuite department to ERPNext cost center"""
		if not department:
			return None
		
		# Try exact match first
		if department in self.department_to_cost_center:
			return self.department_to_cost_center[department]
		
		# Try fuzzy matching
		dept_lower = department.lower()
		for ns_dept, erp_cc in self.department_to_cost_center.items():
			if ns_dept.lower() in dept_lower or dept_lower in ns_dept.lower():
				return erp_cc
		
		# Default fallback
		return 'Main - Your Company'  # Replace with your default cost center
	
	def map_account(self, ns_account):
		"""Map NetSuite account to ERPNext account"""
		if not ns_account:
			return None
		
		if ns_account in self.account_mapping:
			return self.account_mapping[ns_account]
		
		# Try to infer from account name
		account_lower = ns_account.lower()
		if 'advertising' in account_lower or 'marketing' in account_lower:
			return 'Advertising and Marketing - Your Company'
		elif 'travel' in account_lower:
			return 'Travel Expenses - Your Company'
		elif 'office' in account_lower:
			return 'Office Expenses - Your Company'
		
		# Default
		return 'Miscellaneous Expenses - Your Company'
	
	def transform_transaction(self, ns_transaction):
		"""Transform a single NetSuite transaction to ERPNext training format"""
		try:
			# Extract relevant fields from NetSuite transaction
			# Adjust field names based on your actual NetSuite JSON structure
			vendor_name = ns_transaction.get('vendor', '') or ns_transaction.get('payee', '')
			memo = ns_transaction.get('memo', '') or ns_transaction.get('description', '')
			amount = float(ns_transaction.get('amount', 0) or 0)
			date = ns_transaction.get('date', '')
			department = ns_transaction.get('department', '')
			ns_class = ns_transaction.get('class', '')
			account = ns_transaction.get('account', '')
			
			# Transform to ERPNext format
			erp_transaction = {
				'vendor_description': self.normalize_vendor_name(vendor_name),
				'original_vendor': vendor_name,
				'memo': memo,
				'amount': amount,
				'date': date,
				'netsuite_department': department,
				'netsuite_class': ns_class,
				'netsuite_account': account,
				'classification': {
					'vendor': vendor_name,
					'expense_account': self.map_account(account),
					'cost_center': self.map_department_to_cost_center(department)
				},
				'source': 'netsuite',
				'confidence': 0.7  # Lower confidence for historical data
			}
			
			# Calculate weight based on date (more recent = higher weight)
			if date:
				try:
					trans_date = datetime.strptime(date, '%Y-%m-%d')
					months_old = (datetime.now() - trans_date).days / 30
					
					if months_old < 3:
						erp_transaction['weight'] = 3.0
					elif months_old < 6:
						erp_transaction['weight'] = 1.0
					else:
						erp_transaction['weight'] = 0.5
				except:
					erp_transaction['weight'] = 0.5
			else:
				erp_transaction['weight'] = 0.5
			
			return erp_transaction
		
		except Exception as e:
			print(f"Error transforming transaction: {str(e)}")
			return None
	
	def transform_all(self):
		"""Transform all NetSuite transactions"""
		ns_transactions = self.fetch_netsuite_data()
		
		print("Transforming transactions...")
		erp_transactions = []
		
		for ns_trans in ns_transactions:
			erp_trans = self.transform_transaction(ns_trans)
			if erp_trans:
				erp_transactions.append(erp_trans)
		
		print(f"Successfully transformed {len(erp_transactions)} transactions")
		return erp_transactions
	
	def save_training_data(self, transactions):
		"""Save transformed data in format for SageMaker"""
		# Save as JSON
		output_file = os.path.join(self.output_dir, 'training_data.json')
		with open(output_file, 'w') as f:
			json.dump(transactions, f, indent=2)
		print(f"Saved training data to {output_file}")
		
		# Also save as CSV for easy inspection
		df = pd.DataFrame(transactions)
		csv_file = os.path.join(self.output_dir, 'training_data.csv')
		df.to_csv(csv_file, index=False)
		print(f"Saved CSV to {csv_file}")
		
		# Save statistics
		stats = {
			'total_transactions': len(transactions),
			'unique_vendors': len(set([t['vendor_description'] for t in transactions if t.get('vendor_description')])),
			'date_range': {
				'earliest': min([t['date'] for t in transactions if t.get('date')], default=None),
				'latest': max([t['date'] for t in transactions if t.get('date')], default=None)
			},
			'avg_amount': sum([t['amount'] for t in transactions]) / len(transactions) if transactions else 0
		}
		
		stats_file = os.path.join(self.output_dir, 'statistics.json')
		with open(stats_file, 'w') as f:
			json.dump(stats, f, indent=2)
		print(f"Saved statistics to {stats_file}")
		
		return output_file


def main():
	"""Main execution function"""
	import argparse
	
	parser = argparse.ArgumentParser(description='Transform NetSuite data to ERPNext format')
	parser.add_argument('--s3-bucket', required=True, help='S3 bucket name')
	parser.add_argument('--s3-prefix', required=True, help='S3 prefix/path to NetSuite JSON files')
	parser.add_argument('--mapping-config', help='Path to mapping configuration JSON file')
	parser.add_argument('--output-dir', default='training_data', help='Output directory for training data')
	
	args = parser.parse_args()
	
	# Initialize transformer
	transformer = NetSuiteToERPNextTransformer(
		s3_bucket=args.s3_bucket,
		s3_prefix=args.s3_prefix,
		output_dir=args.output_dir
	)
	
	# Load mapping configuration if provided
	if args.mapping_config:
		print(f"Loading mapping configuration from {args.mapping_config}")
		transformer.load_mapping_config(args.mapping_config)
	
	# Transform data
	transactions = transformer.transform_all()
	
	# Save training data
	output_file = transformer.save_training_data(transactions)
	
	print(f"\n✓ Transformation complete! Training data saved to {output_file}")
	print(f"  Total transactions: {len(transactions)}")
	print(f"\nNext steps:")
	print(f"  1. Review the mapping configuration and adjust if needed")
	print(f"  2. Upload training data to S3 for SageMaker")
	print(f"  3. Run the SageMaker training script")


if __name__ == '__main__':
	main()


