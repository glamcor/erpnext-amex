# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import re
import frappe
from frappe.utils import now


def get_classification_suggestion(description, amount=None):
	"""
	Get classification suggestion based on vendor description
	
	Args:
		description: Transaction description
		amount: Transaction amount (optional, for better matching)
	
	Returns:
		dict: Suggested classification or None
	"""
	if not description:
		return None
	
	# Normalize the description
	normalized = normalize_vendor_name(description)
	
	# Look for exact match first
	rule = frappe.db.get_value(
		'AMEX Vendor Classification Rule',
		{'vendor_pattern': normalized, 'enabled': 1},
		['matched_supplier', 'default_expense_account', 'default_cost_center', 'confidence_score'],
		as_dict=True
	)
	
	if rule:
		return rule
	
	# Look for partial matches
	rules = frappe.get_all(
		'AMEX Vendor Classification Rule',
		filters={'enabled': 1},
		fields=['vendor_pattern', 'matched_supplier', 'default_expense_account', 'default_cost_center', 'confidence_score']
	)
	
	for rule in rules:
		# Check if rule pattern is contained in description
		if rule.vendor_pattern.lower() in normalized.lower():
			return rule
	
	return None


def save_classification_rule(description, vendor=None, expense_account=None, cost_center=None):
	"""
	Save or update classification rule based on user's classification
	
	Args:
		description: Transaction description
		vendor: Supplier name
		expense_account: Account name
		cost_center: Cost Center name
	
	Returns:
		doc: AMEX Vendor Classification Rule document
	"""
	if not description:
		return None
	
	normalized = normalize_vendor_name(description)
	
	# Check if rule already exists
	existing = frappe.db.exists('AMEX Vendor Classification Rule', normalized)
	
	if existing:
		# Update existing rule
		rule = frappe.get_doc('AMEX Vendor Classification Rule', normalized)
		
		# Update fields if provided
		if vendor:
			rule.matched_supplier = vendor
		if expense_account:
			rule.default_expense_account = expense_account
		if cost_center:
			rule.default_cost_center = cost_center
		
		# Update usage statistics
		rule.use_count = (rule.use_count or 0) + 1
		rule.last_used = now()
		
		# Increase confidence with each use
		rule.confidence_score = min(1.0, (rule.confidence_score or 0.5) + 0.1)
		
		rule.save(ignore_permissions=True)
	else:
		# Create new rule
		rule = frappe.get_doc({
			'doctype': 'AMEX Vendor Classification Rule',
			'vendor_pattern': normalized,
			'matched_supplier': vendor,
			'default_expense_account': expense_account,
			'default_cost_center': cost_center,
			'confidence_score': 0.7,
			'use_count': 1,
			'last_used': now(),
			'enabled': 1
		})
		rule.insert(ignore_permissions=True)
	
	frappe.db.commit()
	return rule


def normalize_vendor_name(description):
	"""
	Normalize vendor name for better matching
	
	Args:
		description: Raw transaction description
	
	Returns:
		str: Normalized vendor name
	"""
	if not description:
		return ''
	
	# Convert to lowercase
	normalized = description.lower().strip()
	
	# Remove common transaction codes and patterns
	# Remove reference numbers (sequences of digits/letters after spaces)
	normalized = re.sub(r'\s+[0-9a-z]{8,}.*$', '', normalized)
	
	# Remove location codes (e.g., "CA", "NY")
	normalized = re.sub(r'\s+[a-z]{2}$', '', normalized)
	
	# Remove special characters except spaces and hyphens
	normalized = re.sub(r'[^a-z0-9\s\-]', '', normalized)
	
	# Remove extra whitespace
	normalized = re.sub(r'\s+', ' ', normalized).strip()
	
	# Take first significant part (usually vendor name)
	# Split by multiple spaces or common separators
	parts = re.split(r'\s{2,}|\s+-\s+', normalized)
	if parts:
		normalized = parts[0]
	
	# Limit length
	if len(normalized) > 100:
		normalized = normalized[:100]
	
	return normalized


def get_top_vendors(limit=10):
	"""
	Get most frequently used vendors
	
	Args:
		limit: Number of vendors to return
	
	Returns:
		list: List of vendor rules sorted by use count
	"""
	rules = frappe.get_all(
		'AMEX Vendor Classification Rule',
		filters={'enabled': 1},
		fields=['vendor_pattern', 'matched_supplier', 'use_count', 'confidence_score'],
		order_by='use_count desc',
		limit=limit
	)
	
	return rules


def update_rule_confidence(rule_name, accepted):
	"""
	Update confidence score based on user acceptance
	
	Args:
		rule_name: Name of the classification rule
		accepted: Boolean - whether user accepted the suggestion
	"""
	if not frappe.db.exists('AMEX Vendor Classification Rule', rule_name):
		return
	
	rule = frappe.get_doc('AMEX Vendor Classification Rule', rule_name)
	
	if accepted:
		# Increase confidence
		rule.confidence_score = min(1.0, (rule.confidence_score or 0.5) + 0.05)
		rule.use_count = (rule.use_count or 0) + 1
	else:
		# Decrease confidence
		rule.confidence_score = max(0.0, (rule.confidence_score or 0.5) - 0.1)
	
	rule.last_used = now()
	rule.save(ignore_permissions=True)
	frappe.db.commit()


def learn_from_transaction(transaction_doc):
	"""
	Learn from a classified transaction and update or create rules
	
	Args:
		transaction_doc: AMEX Transaction document
	"""
	if not transaction_doc.expense_account:
		return
	
	# Save classification as a rule
	save_classification_rule(
		transaction_doc.description,
		vendor=transaction_doc.vendor,
		expense_account=transaction_doc.expense_account,
		cost_center=transaction_doc.cost_center
	)

