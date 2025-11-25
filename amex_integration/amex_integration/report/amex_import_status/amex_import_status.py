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
			"label": _("Batch ID"),
			"fieldtype": "Link",
			"options": "AMEX Import Batch",
			"width": 180
		},
		{
			"fieldname": "import_date",
			"label": _("Import Date"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "uploaded_by",
			"label": _("Uploaded By"),
			"fieldtype": "Link",
			"options": "User",
			"width": 150
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "total_transactions",
			"label": _("Total"),
			"fieldtype": "Int",
			"width": 80
		},
		{
			"fieldname": "pending_count",
			"label": _("Pending"),
			"fieldtype": "Int",
			"width": 80
		},
		{
			"fieldname": "processed_count",
			"label": _("Processed"),
			"fieldtype": "Int",
			"width": 80
		},
		{
			"fieldname": "duplicate_count",
			"label": _("Duplicates"),
			"fieldtype": "Int",
			"width": 80
		},
		{
			"fieldname": "excluded_count",
			"label": _("Excluded"),
			"fieldtype": "Int",
			"width": 80
		},
		{
			"fieldname": "completion_pct",
			"label": _("Completion %"),
			"fieldtype": "Percent",
			"width": 100
		}
	]


def get_data(filters):
	conditions = []
	
	if filters.get("from_date"):
		conditions.append(f"import_date >= '{filters.get('from_date')}'")
	
	if filters.get("to_date"):
		conditions.append(f"import_date <= '{filters.get('to_date')}'")
	
	if filters.get("status"):
		conditions.append(f"status = '{filters.get('status')}'")
	
	where_clause = " AND ".join(conditions) if conditions else "1=1"
	
	data = frappe.db.sql(f"""
		SELECT 
			name,
			import_date,
			uploaded_by,
			status,
			total_transactions,
			pending_count,
			processed_count,
			duplicate_count,
			excluded_count,
			CASE 
				WHEN total_transactions > 0 
				THEN (processed_count * 100.0 / total_transactions)
				ELSE 0 
			END as completion_pct
		FROM `tabAMEX Import Batch`
		WHERE {where_clause}
		ORDER BY import_date DESC, name DESC
		LIMIT 500
	""", as_dict=True)
	
	return data

