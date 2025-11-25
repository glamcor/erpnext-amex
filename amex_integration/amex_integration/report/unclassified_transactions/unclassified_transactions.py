# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "name",
			"label": _("Transaction ID"),
			"fieldtype": "Link",
			"options": "AMEX Transaction",
			"width": 180
		},
		{
			"fieldname": "transaction_date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "description",
			"label": _("Description"),
			"fieldtype": "Data",
			"width": 250
		},
		{
			"fieldname": "card_member",
			"label": _("Card Member"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "amount",
			"label": _("Amount"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "amex_category",
			"label": _("AMEX Category"),
			"fieldtype": "Data",
			"width": 180
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "batch_id",
			"label": _("Batch"),
			"fieldtype": "Link",
			"options": "AMEX Import Batch",
			"width": 150
		}
	]


def get_data(filters):
	conditions = ["status IN ('Pending', 'Classified')"]
	
	if filters.get("from_date"):
		conditions.append(f"transaction_date >= '{filters.get('from_date')}'")
	
	if filters.get("to_date"):
		conditions.append(f"transaction_date <= '{filters.get('to_date')}'")
	
	if filters.get("card_member"):
		conditions.append(f"card_member = '{filters.get('card_member')}'")
	
	if filters.get("batch_id"):
		conditions.append(f"batch_id = '{filters.get('batch_id')}'")
	
	where_clause = " AND ".join(conditions) if conditions else "1=1"
	
	data = frappe.db.sql(f"""
		SELECT 
			name,
			transaction_date,
			description,
			card_member,
			amount,
			amex_category,
			status,
			batch_id
		FROM `tabAMEX Transaction`
		WHERE {where_clause}
		ORDER BY transaction_date DESC, name DESC
		LIMIT 1000
	""", as_dict=True)
	
	return data

