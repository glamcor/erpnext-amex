frappe.pages['amex_review'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'AMEX Transaction Review',
		single_column: true
	});

	// Add page buttons
	page.add_button('Bulk Approve & Post', () => {
		if (window.amex_review_instance) {
			window.amex_review_instance.bulk_approve_and_post();
		}
	}, {icon: 'fa fa-check'});

	page.add_button('Refresh', () => {
		if (window.amex_review_instance) {
			window.amex_review_instance.load_transactions();
		}
	}, {icon: 'fa fa-refresh'});

	// Initialize the page
	window.amex_review_instance = new AMEXReviewPage(page);
}

class AMEXReviewPage {
	constructor(page) {
		this.page = page;
		this.transactions = [];
		this.selected_transaction = null;
		this.selected_transactions = new Set();
		this.keyword_debounce_timer = null;
		this.sort_field = 'transaction_date';
		this.sort_order = 'desc';
		
		// Load the HTML
		$(frappe.render_template("amex_review", {})).appendTo(this.page.body);
		
		this.setup_events();
		this.setup_autocomplete_fields();
		this.load_filter_options();
		this.load_transactions();
	}

	setup_autocomplete_fields() {
		const me = this;
		
		// Single transaction vendor field
		this.vendor_field = frappe.ui.form.make_control({
			parent: $('#vendor-field'),
			df: {
				fieldtype: 'Link',
				options: 'Supplier',
				label: 'Vendor/Supplier',
				placeholder: 'Type to search...'
			},
			render_input: true
		});
		
		// Single transaction expense account field
		this.expense_account_field = frappe.ui.form.make_control({
			parent: $('#expense-account-field'),
			df: {
				fieldtype: 'Link',
				options: 'Account',
				label: 'Expense Account',
				placeholder: 'Type to search...',
				get_query: () => {
					return {
						filters: {
							'account_type': 'Expense',
							'disabled': 0
						}
					};
				}
			},
			render_input: true
		});
		
		// Single transaction cost center field
		this.cost_center_field = frappe.ui.form.make_control({
			parent: $('#cost-center-field'),
			df: {
				fieldtype: 'Link',
				options: 'Cost Center',
				label: 'Cost Center',
				placeholder: 'Type to search...',
				get_query: () => {
					return {
						filters: {
							'disabled': 0
						}
					};
				}
			},
			render_input: true
		});
		
		// Bulk vendor field
		this.bulk_vendor_field = frappe.ui.form.make_control({
			parent: $('#bulk-vendor-field'),
			df: {
				fieldtype: 'Link',
				options: 'Supplier',
				label: 'Vendor/Supplier',
				placeholder: 'Type to search...'
			},
			render_input: true
		});
		
		// Bulk expense account field
		this.bulk_expense_account_field = frappe.ui.form.make_control({
			parent: $('#bulk-expense-account-field'),
			df: {
				fieldtype: 'Link',
				options: 'Account',
				label: 'Expense Account',
				placeholder: 'Type to search...',
				get_query: () => {
					return {
						filters: {
							'account_type': 'Expense',
							'disabled': 0
						}
					};
				}
			},
			render_input: true
		});
		
		// Bulk cost center field
		this.bulk_cost_center_field = frappe.ui.form.make_control({
			parent: $('#bulk-cost-center-field'),
			df: {
				fieldtype: 'Link',
				options: 'Cost Center',
				label: 'Cost Center',
				placeholder: 'Type to search...',
				get_query: () => {
					return {
						filters: {
							'disabled': 0
						}
					};
				}
			},
			render_input: true
		});
	}

	setup_events() {
		const me = this;

		// Apply filters
		$('#apply-filters-btn').click(() => me.load_transactions());
		
		// Keyword filter with debounce
		$('#filter-keyword').on('input', function() {
			clearTimeout(me.keyword_debounce_timer);
			me.keyword_debounce_timer = setTimeout(() => {
				me.load_transactions();
			}, 500);
		});

		// Select all checkbox
		$('#select-all-transactions').change(function() {
			const checked = $(this).is(':checked');
			$('.transaction-checkbox').prop('checked', checked);
			me.update_selected_transactions();
		});

		// Transaction row click
		$(document).on('click', '.transaction-row', function(e) {
			if ($(e.target).is('input[type="checkbox"]')) return;
			
			const name = $(this).data('name');
			me.load_transaction_details(name);
			$('.transaction-row').removeClass('table-active');
			$(this).addClass('table-active');
		});

		// Transaction checkbox
		$(document).on('change', '.transaction-checkbox', function() {
			me.update_selected_transactions();
		});

		// Sortable column headers
		$(document).on('click', '.sortable-header', function() {
			const field = $(this).data('field');
			me.sort_transactions(field);
		});

		// Cost center allocation type
		$('#single-cc-btn').click(() => me.toggle_cost_center_type('single'));
		$('#split-cc-btn').click(() => me.toggle_cost_center_type('split'));

		// Add split button
		$('#add-split-btn').click(() => me.add_split_row());

		// Remove split button
		$(document).on('click', '.remove-split-btn', function() {
			$(this).closest('tr').remove();
			me.calculate_split_totals();
		});

		// Split amount/percentage change
		$(document).on('input', '.split-amount, .split-percentage', function() {
			me.calculate_split_totals();
		});

		// Classify button
		$('#classify-btn').click(() => me.classify_transaction());

		// Approve button
		$('#approve-btn').click(() => me.approve_transaction());

		// Post button
		$('#post-btn').click(() => me.post_transaction());

		// Mark duplicate button
		$('#mark-duplicate-btn').click(() => me.mark_as_duplicate());
		
		// Bulk classify button
		$('#bulk-classify-btn').click(() => me.bulk_classify_transactions());

		// Create vendor button
		$('#create-vendor-btn').click(() => $('#vendor-modal').modal('show'));

		// Save vendor button
		$('#save-vendor-btn').click(() => me.create_vendor());
	}

	load_filter_options() {
		frappe.call({
			method: 'erpnext_amex.amex_integration.page.amex_review.amex_review.get_filter_options',
			callback: (r) => {
				if (r.message) {
					// Populate batch filter
					r.message.batches.forEach(batch => {
						$('#filter-batch').append(`<option value="${batch.name}">${batch.name} (${batch.import_date})</option>`);
					});

					// Populate card member filter
					r.message.card_members.forEach(member => {
						$('#filter-card-member').append(`<option value="${member}">${member}</option>`);
					});
				}
			}
		});
	}

	load_transactions() {
		const me = this;
		const filters = {
			batch_id: $('#filter-batch').val(),
			card_member: $('#filter-card-member').val(),
			from_date: $('#filter-from-date').val(),
			to_date: $('#filter-to-date').val(),
			keyword: $('#filter-keyword').val()
		};

		$('#loading-transactions').show();
		$('#no-transactions').hide();
		$('#transaction-list').empty();

		frappe.call({
			method: 'erpnext_amex.amex_integration.page.amex_review.amex_review.get_pending_transactions',
			args: { filters: JSON.stringify(filters) },
			callback: (r) => {
				$('#loading-transactions').hide();
				
				if (r.message && r.message.length > 0) {
					me.transactions = r.message;
					me.render_transactions();
				} else {
					$('#no-transactions').show();
				}
			}
		});
	}

	sort_transactions(field) {
		// Toggle sort order if clicking same field
		if (this.sort_field === field) {
			this.sort_order = this.sort_order === 'asc' ? 'desc' : 'asc';
		} else {
			this.sort_field = field;
			this.sort_order = 'asc';
		}

		// Sort transactions
		this.transactions.sort((a, b) => {
			let aVal = a[field];
			let bVal = b[field];

			// Handle nulls
			if (aVal === null || aVal === undefined) aVal = '';
			if (bVal === null || bVal === undefined) bVal = '';

			// Compare based on type
			if (field === 'amount') {
				aVal = Number(aVal);
				bVal = Number(bVal);
			} else if (field === 'transaction_date') {
				aVal = new Date(aVal);
				bVal = new Date(bVal);
			} else {
				aVal = String(aVal).toLowerCase();
				bVal = String(bVal).toLowerCase();
			}

			if (this.sort_order === 'asc') {
				return aVal > bVal ? 1 : -1;
			} else {
				return aVal < bVal ? 1 : -1;
			}
		});

		this.render_transactions();
		this.update_sort_indicators();
	}

	update_sort_indicators() {
		// Remove all sort indicators
		$('.sortable-header .sort-indicator').remove();

		// Add indicator to current sorted column
		const icon = this.sort_order === 'asc' ? 'fa-sort-asc' : 'fa-sort-desc';
		$(`.sortable-header[data-field="${this.sort_field}"]`)
			.append(`<i class="fa ${icon} sort-indicator" style="margin-left: 5px;"></i>`);
	}

	render_transactions() {
		const tbody = $('#transaction-list');
		tbody.empty();

		// Calculate total pending amount
		let total_pending = 0;
		this.transactions.forEach(trans => {
			if (trans.status === 'Pending' || trans.status === 'Classified') {
				total_pending += Number(trans.amount) || 0;
			}
		});

		// Update total display
		$('#total-pending-amount').text(`$${total_pending.toFixed(2)}`);
		$('#total-pending-count').text(this.transactions.length);

		this.transactions.forEach(trans => {
			const statusClass = {
				'Pending': 'badge-warning',
				'Classified': 'badge-info',
				'Approved': 'badge-success',
				'Posted': 'badge-secondary'
			}[trans.status] || 'badge-secondary';

			const row = `
				<tr class="transaction-row" data-name="${trans.name}">
					<td>
						<input type="checkbox" class="transaction-checkbox" value="${trans.name}">
					</td>
					<td>${frappe.datetime.str_to_user(trans.transaction_date)}</td>
					<td>${trans.description || ''}</td>
					<td>${trans.card_member || ''}</td>
					<td>$${Number(trans.amount).toFixed(2)}</td>
					<td><span class="badge ${statusClass}">${trans.status}</span></td>
				</tr>
			`;
			tbody.append(row);
		});

		this.update_sort_indicators();
	}

	update_selected_transactions() {
		const me = this;
		this.selected_transactions.clear();
		
		$('.transaction-checkbox:checked').each(function() {
			me.selected_transactions.add($(this).val());
		});

		const count = this.selected_transactions.size;
		$('#selected-count').text(count);

		if (count > 1) {
			$('#bulk-panel').show();
			$('#classification-panel').hide();
		} else if (count === 1) {
			$('#bulk-panel').hide();
			$('#classification-panel').show();
		} else {
			$('#bulk-panel').hide();
			$('#classification-panel').hide();
		}
	}

	bulk_classify_transactions() {
		const me = this;
		const transaction_names = Array.from(this.selected_transactions);
		
		if (transaction_names.length === 0) {
			frappe.msgprint('Please select transactions to classify');
			return;
		}

		const vendor = me.bulk_vendor_field.get_value();
		const expense_account = me.bulk_expense_account_field.get_value();
		const cost_center = me.bulk_cost_center_field.get_value();
		const notes = $('#bulk-classification-notes').val();

		if (!expense_account) {
			frappe.msgprint('Please select an Expense Account');
			return;
		}

		if (!cost_center) {
			frappe.msgprint('Please select a Cost Center');
			return;
		}

		frappe.call({
			method: 'erpnext_amex.amex_integration.page.amex_review.amex_review.bulk_classify_transactions',
			args: {
				transaction_names: JSON.stringify(transaction_names),
				vendor: vendor,
				expense_account: expense_account,
				cost_center: cost_center,
				notes: notes
			},
			callback: (r) => {
				if (r.message) {
					const result = r.message;
					frappe.msgprint(`
						<strong>Bulk Classification Complete</strong><br>
						Success: ${result.success_count}<br>
						Errors: ${result.error_count}<br>
						Total: ${result.total}
					`);
					
					// Clear selections and reload
					me.selected_transactions.clear();
					$('.transaction-checkbox').prop('checked', false);
					$('#select-all-transactions').prop('checked', false);
					me.update_selected_transactions();
					me.load_transactions();
				}
			}
		});
	}

	load_transaction_details(transaction_name) {
		const me = this;
		me.selected_transaction = transaction_name;

		frappe.call({
			method: 'erpnext_amex.amex_integration.page.amex_review.amex_review.get_transaction_details',
			args: { transaction_name: transaction_name },
			callback: (r) => {
				if (r.message) {
					me.render_transaction_details(r.message.transaction);
					$('#classification-panel').show();
				}
			}
		});
	}

	render_transaction_details(trans) {
		const detailsHtml = `
			<div class="detail-row">
				<span class="detail-label">Reference:</span>
				<span class="detail-value">${trans.reference || 'N/A'}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Date:</span>
				<span class="detail-value">${frappe.datetime.str_to_user(trans.transaction_date)}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Card Member:</span>
				<span class="detail-value">${trans.card_member || 'N/A'}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Amount:</span>
				<span class="detail-value amount-large">$${Number(trans.amount).toFixed(2)}</span>
			</div>
			<div class="detail-row">
				<span class="detail-label">Category:</span>
				<span class="detail-value">${trans.amex_category || 'N/A'}</span>
			</div>
		`;
		$('#transaction-details').html(detailsHtml);

		// Set current values if classified
		if (trans.vendor) {
			this.vendor_field.set_value(trans.vendor);
		}
		if (trans.expense_account) {
			this.expense_account_field.set_value(trans.expense_account);
		}
		if (trans.cost_center) {
			this.cost_center_field.set_value(trans.cost_center);
		}
		if (trans.classification_notes) {
			$('#classification-notes').val(trans.classification_notes);
		}
	}

	toggle_cost_center_type(type) {
		if (type === 'single') {
			$('#single-cc-btn').addClass('active');
			$('#split-cc-btn').removeClass('active');
			$('#single-cost-center-div').show();
			$('#split-cost-centers-div').hide();
		} else {
			$('#single-cc-btn').removeClass('active');
			$('#split-cc-btn').addClass('active');
			$('#single-cost-center-div').hide();
			$('#split-cost-centers-div').show();
		}
	}

	classify_transaction() {
		const me = this;
		const vendor = me.vendor_field.get_value();
		const expense_account = me.expense_account_field.get_value();
		const cost_center = me.cost_center_field.get_value();
		const notes = $('#classification-notes').val();

		if (!expense_account) {
			frappe.msgprint('Please select an Expense Account');
			return;
		}

		frappe.call({
			method: 'erpnext_amex.amex_integration.page.amex_review.amex_review.classify_transaction',
			args: {
				transaction_name: me.selected_transaction,
				vendor: vendor,
				expense_account: expense_account,
				cost_center: cost_center,
				notes: notes
			},
			callback: (r) => {
				if (r.message) {
					frappe.show_alert({message: 'Transaction classified', indicator: 'green'});
					me.load_transactions();
				}
			}
		});
	}

	approve_transaction() {
		// Stub for future implementation
		frappe.msgprint('Approve functionality coming soon');
	}

	post_transaction() {
		const me = this;
		frappe.call({
			method: 'erpnext_amex.amex_integration.page.amex_review.amex_review.post_transaction',
			args: { transaction_name: me.selected_transaction },
			callback: (r) => {
				if (r.message) {
					frappe.show_alert({message: 'Posted to Journal Entry', indicator: 'green'});
					me.load_transactions();
					$('#classification-panel').hide();
				}
			}
		});
	}

	mark_as_duplicate() {
		const me = this;
		frappe.call({
			method: 'erpnext_amex.amex_integration.page.amex_review.amex_review.mark_as_duplicate',
			args: { transaction_name: me.selected_transaction },
			callback: (r) => {
				if (r.message) {
					frappe.show_alert({message: 'Marked as duplicate', indicator: 'orange'});
					me.load_transactions();
					$('#classification-panel').hide();
				}
			}
		});
	}

	bulk_approve_and_post() {
		const me = this;
		const selected = Array.from(this.selected_transactions);
		
		if (selected.length === 0) {
			frappe.msgprint('Please select transactions to post');
			return;
		}

		frappe.confirm(
			`Post ${selected.length} transaction(s) to Journal Entries?`,
			() => {
				frappe.call({
					method: 'erpnext_amex.amex_integration.page.amex_review.amex_review.bulk_approve_and_post',
					args: { transaction_names: JSON.stringify(selected) },
					callback: (r) => {
						if (r.message) {
							frappe.msgprint(`Posted ${r.message.success_count} transactions`);
							me.selected_transactions.clear();
							me.load_transactions();
						}
					}
				});
			}
		);
	}

	create_vendor() {
		const vendor_name = $('#new-vendor-name').val();
		const supplier_group = $('#new-vendor-group').val();
		const country = $('#new-vendor-country').val();

		if (!vendor_name) {
			frappe.msgprint('Please enter vendor name');
			return;
		}

		frappe.call({
			method: 'erpnext_amex.amex_integration.page.amex_review.amex_review.create_vendor_quick',
			args: {
				vendor_name: vendor_name,
				supplier_group: supplier_group,
				country: country
			},
			callback: (r) => {
				if (r.message) {
					frappe.show_alert({message: 'Vendor created', indicator: 'green'});
					$('#vendor-modal').modal('hide');
					this.vendor_field.set_value(r.message.name);
				}
			}
		});
	}
}

