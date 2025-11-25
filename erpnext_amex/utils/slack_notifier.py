# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
import json
import requests
from frappe.utils import get_url


def send_classification_request(transaction_doc, user_slack_id=None):
	"""
	Send Slack notification requesting classification from cardholder
	
	Args:
		transaction_doc: AMEX Transaction document
		user_slack_id: Slack user ID (optional, will lookup if not provided)
	
	Returns:
		bool: True if notification sent successfully
	"""
	settings = frappe.get_single('AMEX Integration Settings')
	
	if not settings.enable_slack_notifications:
		return False
	
	if not settings.slack_bot_token:
		frappe.log_error("Slack bot token not configured", "Slack Notification Error")
		return False
	
	# Get Slack user ID if not provided
	if not user_slack_id:
		user_slack_id = get_slack_user_id(transaction_doc.card_member)
	
	if not user_slack_id:
		frappe.log_error(f"No Slack user ID found for {transaction_doc.card_member}", "Slack Notification Error")
		return False
	
	# Format message
	message = format_transaction_message(transaction_doc)
	
	try:
		# Send Slack message
		bot_token = settings.get_password('slack_bot_token')
		
		response = requests.post(
			'https://slack.com/api/chat.postMessage',
			headers={
				'Authorization': f'Bearer {bot_token}',
				'Content-Type': 'application/json'
			},
			json={
				'channel': user_slack_id,
				'blocks': message['blocks'],
				'text': message['text']
			}
		)
		
		response.raise_for_status()
		result = response.json()
		
		if result.get('ok'):
			# Store Slack message timestamp for reference
			transaction_doc.add_comment(
				'Comment',
				f"Slack notification sent. Message TS: {result.get('ts')}"
			)
			return True
		else:
			frappe.log_error(f"Slack API error: {result.get('error')}", "Slack Notification Error")
			return False
	
	except Exception as e:
		frappe.log_error(f"Error sending Slack notification: {str(e)}", "Slack Notification Error")
		return False


def format_transaction_message(transaction_doc):
	"""
	Format transaction details as Slack message blocks
	
	Args:
		transaction_doc: AMEX Transaction document
	
	Returns:
		dict: Slack message with blocks
	"""
	transaction_url = get_url(f"/app/amex-transaction/{transaction_doc.name}")
	
	# Format amount
	amount_formatted = frappe.format(transaction_doc.amount, {'fieldtype': 'Currency'})
	
	# Create message blocks
	blocks = [
		{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": "🔔 AMEX Transaction Needs Classification"
			}
		},
		{
			"type": "section",
			"fields": [
				{
					"type": "mrkdwn",
					"text": f"*Date:*\n{transaction_doc.transaction_date}"
				},
				{
					"type": "mrkdwn",
					"text": f"*Amount:*\n{amount_formatted}"
				},
				{
					"type": "mrkdwn",
					"text": f"*Description:*\n{transaction_doc.description}"
				},
				{
					"type": "mrkdwn",
					"text": f"*Reference:*\n{transaction_doc.reference}"
				}
			]
		}
	]
	
	# Add category if available
	if transaction_doc.amex_category:
		blocks.append({
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": f"*AMEX Category:* {transaction_doc.amex_category}"
			}
		})
	
	# Add action buttons
	blocks.extend([
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "What is this expense for?"
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Classify in ERPNext"
					},
					"url": transaction_url,
					"style": "primary"
				},
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Mark as Personal"
					},
					"value": f"personal_{transaction_doc.name}",
					"action_id": "mark_personal"
				}
			]
		}
	])
	
	# Plain text fallback
	text = f"AMEX Transaction: {transaction_doc.description} - {amount_formatted} on {transaction_doc.transaction_date}"
	
	return {
		'blocks': blocks,
		'text': text
	}


def get_slack_user_id(card_member_name):
	"""
	Get Slack user ID for a card member
	
	Args:
		card_member_name: Name of card member
	
	Returns:
		str: Slack user ID or None
	"""
	# Try to find ERPNext user by name
	user = frappe.db.get_value('User', {'full_name': card_member_name}, 'name')
	
	if not user:
		# Try searching by first/last name parts
		name_parts = card_member_name.split()
		if len(name_parts) >= 2:
			first_name = name_parts[0]
			last_name = name_parts[-1]
			user = frappe.db.get_value('User', {
				'first_name': first_name,
				'last_name': last_name
			}, 'name')
	
	if user:
		# Check if user has Slack ID in custom field
		slack_id = frappe.db.get_value('User', user, 'slack_user_id')
		if slack_id:
			return slack_id
	
	# If no mapping found, try looking up by email
	# This would require Slack API call to get user by email
	# For now, return None and log error
	return None


def handle_slack_response(payload):
	"""
	Handle interactive Slack responses
	
	Args:
		payload: Slack interaction payload
	
	Returns:
		dict: Response to send back to Slack
	"""
	try:
		# Parse action
		action = payload.get('actions', [{}])[0]
		action_id = action.get('action_id')
		value = action.get('value')
		
		if action_id == 'mark_personal':
			# Extract transaction name from value
			transaction_name = value.replace('personal_', '')
			
			# Mark transaction as personal/excluded
			transaction = frappe.get_doc('AMEX Transaction', transaction_name)
			transaction.status = 'Excluded'
			transaction.classification_notes = 'Marked as personal expense by cardholder via Slack'
			transaction.save(ignore_permissions=True)
			frappe.db.commit()
			
			return {
				'text': '✓ Transaction marked as personal expense'
			}
	
	except Exception as e:
		frappe.log_error(f"Error handling Slack response: {str(e)}", "Slack Handler Error")
		return {
			'text': '✗ Error processing your response'
		}


def notify_low_confidence_transactions(batch_id=None):
	"""
	Send Slack notifications for all low-confidence transactions
	
	Args:
		batch_id: Optional batch ID to filter transactions
	
	Returns:
		int: Number of notifications sent
	"""
	filters = {
		'status': 'Pending',
		'ml_confidence_score': ['<', 0.5]
	}
	
	if batch_id:
		filters['batch_id'] = batch_id
	
	transactions = frappe.get_all(
		'AMEX Transaction',
		filters=filters,
		fields=['name', 'card_member']
	)
	
	notifications_sent = 0
	
	for trans in transactions:
		transaction_doc = frappe.get_doc('AMEX Transaction', trans.name)
		if send_classification_request(transaction_doc):
			notifications_sent += 1
	
	return notifications_sent


def send_batch_complete_notification(batch_id):
	"""
	Send notification when batch import is complete
	
	Args:
		batch_id: AMEX Import Batch ID
	
	Returns:
		bool: True if sent successfully
	"""
	settings = frappe.get_single('AMEX Integration Settings')
	
	if not settings.enable_slack_notifications:
		return False
	
	batch = frappe.get_doc('AMEX Import Batch', batch_id)
	
	# Send to a general channel or specific users
	# For now, just log - implement channel notification as needed
	frappe.logger().info(f"Batch {batch_id} import complete: {batch.total_transactions} transactions")
	
	return True


