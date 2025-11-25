# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
import requests
import json
from bs4 import BeautifulSoup


def search_vendor_info(vendor_description):
	"""
	Search for vendor information using Google Search API
	
	Args:
		vendor_description: Vendor/merchant description from transaction
	
	Returns:
		dict: Vendor information or None
	"""
	settings = frappe.get_single('AMEX Integration Settings')
	
	if not settings.enable_vendor_enrichment:
		return None
	
	if not settings.google_search_api_key or not settings.google_search_engine_id:
		frappe.log_error("Google Search API not configured", "Vendor Enrichment Error")
		return None
	
	try:
		api_key = settings.get_password('google_search_api_key')
		search_engine_id = settings.google_search_engine_id
		
		# Clean up vendor description for search
		search_query = clean_vendor_description(vendor_description)
		
		# Call Google Custom Search API
		url = 'https://www.googleapis.com/customsearch/v1'
		params = {
			'key': api_key,
			'cx': search_engine_id,
			'q': search_query,
			'num': 3  # Get top 3 results
		}
		
		response = requests.get(url, params=params)
		response.raise_for_status()
		results = response.json()
		
		# Parse results
		vendor_info = parse_search_results(results, vendor_description)
		
		return vendor_info
	
	except Exception as e:
		frappe.log_error(f"Vendor enrichment error: {str(e)}", "Vendor Enrichment Error")
		return None


def clean_vendor_description(description):
	"""
	Clean vendor description for better search results
	
	Args:
		description: Raw vendor description
	
	Returns:
		str: Cleaned search query
	"""
	import re
	
	# Remove common patterns
	cleaned = description
	
	# Remove transaction codes
	cleaned = re.sub(r'[A-Z0-9]{8,}', '', cleaned)
	
	# Remove location codes
	cleaned = re.sub(r'\s+[A-Z]{2}$', '', cleaned)
	
	# Remove special characters
	cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', cleaned)
	
	# Normalize whitespace
	cleaned = re.sub(r'\s+', ' ', cleaned).strip()
	
	# Take first few words (usually the merchant name)
	words = cleaned.split()[:3]
	cleaned = ' '.join(words)
	
	return cleaned


def parse_search_results(results, original_description):
	"""
	Parse Google Search results to extract vendor information
	
	Args:
		results: Google Search API results
		original_description: Original vendor description
	
	Returns:
		dict: Extracted vendor information
	"""
	items = results.get('items', [])
	
	if not items:
		return None
	
	# Get first result (most relevant)
	first_result = items[0]
	
	vendor_info = {
		'suggested_name': first_result.get('title', ''),
		'website': first_result.get('link', ''),
		'description': first_result.get('snippet', ''),
		'original_search': original_description,
		'confidence': 0.7  # Base confidence
	}
	
	# Try to extract business category from snippet
	snippet = first_result.get('snippet', '').lower()
	
	categories = {
		'advertising': 'Advertising and Marketing',
		'marketing': 'Advertising and Marketing',
		'software': 'Software and Technology',
		'restaurant': 'Meals and Entertainment',
		'hotel': 'Travel and Accommodation',
		'fuel': 'Fuel and Automotive',
		'office': 'Office Supplies',
		'shipping': 'Shipping and Freight'
	}
	
	for keyword, category in categories.items():
		if keyword in snippet:
			vendor_info['suggested_category'] = category
			break
	
	# Increase confidence if multiple results match
	if len(items) > 1:
		second_title = items[1].get('title', '')
		if are_similar(first_result.get('title', ''), second_title):
			vendor_info['confidence'] = 0.85
	
	return vendor_info


def are_similar(str1, str2):
	"""Check if two strings are similar"""
	# Simple similarity check
	str1_words = set(str1.lower().split())
	str2_words = set(str2.lower().split())
	
	common_words = str1_words & str2_words
	
	if len(common_words) >= 2:
		return True
	
	return False


def suggest_vendor_identity(transaction_doc):
	"""
	Get vendor identity suggestion for a transaction
	
	Args:
		transaction_doc: AMEX Transaction document
	
	Returns:
		dict: Suggested vendor information
	"""
	vendor_info = search_vendor_info(transaction_doc.description)
	
	if vendor_info:
		# Log the suggestion
		transaction_doc.add_comment(
			'Comment',
			f"Vendor suggestion from search: {vendor_info.get('suggested_name')} - {vendor_info.get('website')}"
		)
	
	return vendor_info


def enrich_unknown_vendor(transaction_name):
	"""
	API method to enrich an unknown vendor
	
	Args:
		transaction_name: Transaction ID
	
	Returns:
		dict: Vendor enrichment results
	"""
	transaction = frappe.get_doc('AMEX Transaction', transaction_name)
	
	if transaction.vendor:
		return {
			'status': 'already_has_vendor',
			'vendor': transaction.vendor
		}
	
	vendor_info = suggest_vendor_identity(transaction)
	
	if vendor_info:
		return {
			'status': 'suggestion_found',
			'vendor_info': vendor_info
		}
	else:
		return {
			'status': 'no_suggestion',
			'message': 'Could not find vendor information'
		}


@frappe.whitelist()
def search_and_suggest(description):
	"""
	Whitelist API method to search for vendor
	
	Args:
		description: Vendor description to search
	
	Returns:
		dict: Search results
	"""
	result = search_vendor_info(description)
	return result or {'status': 'not_found'}


def batch_enrich_transactions(transaction_list):
	"""
	Enrich multiple transactions in batch
	
	Args:
		transaction_list: List of transaction names
	
	Returns:
		dict: Summary of enrichment results
	"""
	results = {
		'enriched': [],
		'not_found': [],
		'errors': []
	}
	
	for trans_name in transaction_list:
		try:
			result = enrich_unknown_vendor(trans_name)
			
			if result['status'] == 'suggestion_found':
				results['enriched'].append({
					'transaction': trans_name,
					'suggestion': result['vendor_info']
				})
			else:
				results['not_found'].append(trans_name)
		
		except Exception as e:
			results['errors'].append({
				'transaction': trans_name,
				'error': str(e)
			})
	
	return results


