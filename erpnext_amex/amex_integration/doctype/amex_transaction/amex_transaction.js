// Copyright (c) 2025, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on('AMEX Transaction', {
	setup: function(frm) {
		// Get company from AMEX Integration Settings and set filters
		frappe.call({
			method: 'frappe.client.get_single_value',
			args: {
				doctype: 'AMEX Integration Settings',
				field: 'default_company'
			},
			async: false,
			callback: function(r) {
				if (r.message) {
					frm.amex_company = r.message;
				}
			}
		});
		
		// Set query filters for Account fields
		frm.set_query('expense_account', function() {
			return {
				filters: {
					company: frm.amex_company,
					is_group: 0,
					root_type: 'Expense'
				}
			};
		});
		
		frm.set_query('amex_card_account', function() {
			return {
				filters: {
					company: frm.amex_company,
					is_group: 0
				}
			};
		});
		
		// Set query filter for Cost Center
		frm.set_query('cost_center', function() {
			return {
				filters: {
					company: frm.amex_company,
					is_group: 0
				}
			};
		});
		
		// Set query filter for Accounting Class (if it has a company field)
		frm.set_query('accounting_class', function() {
			return {
				filters: {
					company: frm.amex_company
				}
			};
		});
		
		// Set query filters for child table fields (Cost Center Splits)
		frm.set_query('cost_center', 'cost_center_splits', function() {
			return {
				filters: {
					company: frm.amex_company,
					is_group: 0
				}
			};
		});
		
		frm.set_query('accounting_class', 'cost_center_splits', function() {
			return {
				filters: {
					company: frm.amex_company
				}
			};
		});
	}
});

