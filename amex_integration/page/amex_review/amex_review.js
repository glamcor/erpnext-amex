frappe.pages['amex_review'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'AMEX Transaction Review',
		single_column: true
	});

	// Initialize the page
	new AMEXReviewPage(page);
}

class AMEXReviewPage {
	constructor(page) {
		this.page = page;
		this.transactions = [];
		this.selected_transaction = null;
		this.selected_transactions = new Set();
		
		// Load the HTML
		$(frappe.render_template("amex_review", {})).appendTo(this.page.body);
		
		this.setup_events();
		this.load_filter_options();
		this.load_dropdowns();
		this.load_transactions();
	}

	setup_events() {
		const me = this;

		// Refresh button
		$('#refresh-btn').click(() => me.load_transactions());

		// Apply filters
		$('#apply-filters-btn').click(() => me.load_transactions());

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

		// Bulk approve button
		$('#bulk-approve-btn').click(() => me.bulk_approve_and_post());

		// Create vendor button
		$('#create-vendor-btn').click(() => $('#vendor-modal').modal('show'));

		// Save vendor button
		$('#save-vendor-btn').click(() => me.create_vendor());
	}

	load_filter_options() {
		frappe.call({
			method: 'amex_integration.amex_integration.page.amex_review.amex_review.get_filter_options',
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

	load_dropdowns() {
		// Load suppliers
		frappe.call({
			method: 'amex_integration.amex_integration.page.amex_review.amex_review.get_supplier_list',
			callback: (r) => {
				if (r.message) {
					r.message.forEach(supplier => {
						$('#vendor-select').append(`<option value="${supplier.name}">${supplier.supplier_name}</option>`);
					});
				}
			}
		});

		// Load accounts
		frappe.call({
			method: 'amex_integration.amex_integration.page.amex_review.amex_review.get_account_list',
			args: { account_type: 'Expense' },
			callback: (r) => {
				if (r.message) {
					r.message.forEach(account => {
						$('#expense-account-select').append(`<option value="${account.name}">${account.account_name}</option>`);
					});
				}
			}
		});

		// Load cost centers
		frappe.call({
			method: 'amex_integration.amex_integration.page.amex_review.amex_review.get_cost_center_list',
			callback: (r) => {
				if (r.message) {
					r.message.forEach(cc => {
						const option = `<option value="${cc.name}">${cc.cost_center_name}</option>`;
						$('#cost-center-select').append(option);
						$('.split-cost-center-select').append(option);
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
			to_date: $('#filter-to-date').val()
		};

		$('#loading-transactions').show();
		$('#transaction-list').empty();
		$('#no-transactions').hide();

		frappe.call({
			method: 'amex_integration.amex_integration.page.amex_review.amex_review.get_pending_transactions',
			args: { filters: filters },
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

	render_transactions() {
		const tbody = $('#transaction-list');
		tbody.empty();

		this.transactions.forEach(trans => {
			const status_badge = this.get_status_badge(trans.status);
			const suggestion_indicator = trans.suggestion ? '<i class="fa fa-lightbulb-o text-warning" title="Suggestion available"></i>' : '';
			
			const row = `
				<tr class="transaction-row" data-name="${trans.name}">
					<td>
						<input type="checkbox" class="transaction-checkbox" value="${trans.name}">
					</td>
					<td>${frappe.datetime.str_to_user(trans.transaction_date)}</td>
					<td>${trans.description} ${suggestion_indicator}</td>
					<td>${trans.card_member}</td>
					<td>${frappe.format(trans.amount, {fieldtype: 'Currency'})}</td>
					<td>${status_badge}</td>
				</tr>
			`;
			tbody.append(row);
		});
	}

	get_status_badge(status) {
		const badges = {
			'Pending': 'badge-warning',
			'Classified': 'badge-info',
			'Approved': 'badge-primary',
			'Posted': 'badge-success',
			'Duplicate': 'badge-secondary',
			'Excluded': 'badge-dark'
		};
		const badge_class = badges[status] || 'badge-secondary';
		return `<span class="badge ${badge_class}">${status}</span>`;
	}

	load_transaction_details(transaction_name) {
		const me = this;

		frappe.call({
			method: 'amex_integration.amex_integration.page.amex_review.amex_review.get_transaction_details',
			args: { transaction_name: transaction_name },
			callback: (r) => {
				if (r.message) {
					me.selected_transaction = r.message.transaction;
					me.render_transaction_details(r.message.transaction, r.message.suggestion);
					$('#classification-panel').show();
				}
			}
		});
	}

	render_transaction_details(trans, suggestion) {
		const details_html = `
			<h6>${trans.description}</h6>
			<p class="text-muted small">
				<strong>Reference:</strong> ${trans.reference}<br>
				<strong>Date:</strong> ${frappe.datetime.str_to_user(trans.transaction_date)}<br>
				<strong>Card Member:</strong> ${trans.card_member}<br>
				<strong>Amount:</strong> ${frappe.format(trans.amount, {fieldtype: 'Currency'})}<br>
				<strong>Category:</strong> ${trans.amex_category || 'N/A'}
			</p>
			${suggestion ? this.render_suggestion(suggestion) : ''}
		`;
		$('#transaction-details').html(details_html);

		// Populate form with existing data or suggestions
		if (trans.vendor || (suggestion && suggestion.matched_supplier)) {
			$('#vendor-select').val(trans.vendor || suggestion.matched_supplier);
		}
		
		if (trans.expense_account || (suggestion && suggestion.default_expense_account)) {
			$('#expense-account-select').val(trans.expense_account || suggestion.default_expense_account);
		}
		
		if (trans.cost_center || (suggestion && suggestion.default_cost_center)) {
			$('#cost-center-select').val(trans.cost_center || suggestion.default_cost_center);
		}
		
		$('#classification-notes').val(trans.classification_notes || '');

		// Show appropriate buttons based on status
		this.update_action_buttons(trans.status);

		// Load splits if present
		if (trans.cost_center_splits && trans.cost_center_splits.length > 0) {
			this.toggle_cost_center_type('split');
			this.load_splits(trans.cost_center_splits);
		}
	}

	render_suggestion(suggestion) {
		return `
			<div class="alert alert-info small">
				<i class="fa fa-lightbulb-o"></i> <strong>Suggestion:</strong><br>
				${suggestion.matched_supplier ? `Vendor: ${suggestion.matched_supplier}<br>` : ''}
				${suggestion.default_expense_account ? `Account: ${suggestion.default_expense_account}<br>` : ''}
				${suggestion.default_cost_center ? `Cost Center: ${suggestion.default_cost_center}<br>` : ''}
				<small>Confidence: ${(suggestion.confidence_score * 100).toFixed(0)}%</small>
			</div>
		`;
	}

	update_action_buttons(status) {
		$('#classify-btn').toggle(status === 'Pending');
		$('#approve-btn').toggle(status === 'Classified');
		$('#post-btn').toggle(status === 'Approved');
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
			
			// Add initial split row if empty
			if ($('#split-table-body tr').length === 0) {
				this.add_split_row();
				this.add_split_row();
			}
		}
	}

	add_split_row() {
		const amount = this.selected_transaction ? this.selected_transaction.amount : 0;
		const row = `
			<tr>
				<td>
					<select class="form-control form-control-sm split-cost-center-select">
						<option value="">Select...</option>
					</select>
				</td>
				<td>
					<input type="number" class="form-control form-control-sm split-amount" step="0.01" placeholder="Amount">
				</td>
				<td>
					<input type="number" class="form-control form-control-sm split-percentage" step="0.01" placeholder="%">
				</td>
				<td>
					<button class="btn btn-sm btn-danger remove-split-btn" type="button">
						<i class="fa fa-times"></i>
					</button>
				</td>
			</tr>
		`;
		
		$('#split-table-body').append(row);

		// Populate cost centers for new row
		const last_select = $('#split-table-body tr:last .split-cost-center-select');
		frappe.call({
			method: 'amex_integration.amex_integration.page.amex_review.amex_review.get_cost_center_list',
			callback: (r) => {
				if (r.message) {
					r.message.forEach(cc => {
						last_select.append(`<option value="${cc.name}">${cc.cost_center_name}</option>`);
					});
				}
			}
		});
	}

	load_splits(splits) {
		$('#split-table-body').empty();
		splits.forEach(split => {
			this.add_split_row();
			const last_row = $('#split-table-body tr:last');
			last_row.find('.split-cost-center-select').val(split.cost_center);
			last_row.find('.split-amount').val(split.amount);
			last_row.find('.split-percentage').val(split.percentage);
		});
	}

	calculate_split_totals() {
		// Calculate totals and remaining
		let total_amount = 0;
		let total_percentage = 0;

		$('#split-table-body tr').each(function() {
			const amount = parseFloat($(this).find('.split-amount').val()) || 0;
			const percentage = parseFloat($(this).find('.split-percentage').val()) || 0;
			total_amount += amount;
			total_percentage += percentage;
		});

		// Could add visual feedback for totals here
		console.log('Total amount:', total_amount, 'Total percentage:', total_percentage);
	}

	classify_transaction() {
		const me = this;

		if (!me.selected_transaction) {
			frappe.msgprint('No transaction selected');
			return;
		}

		const expense_account = $('#expense-account-select').val();
		if (!expense_account) {
			frappe.msgprint('Please select an expense account');
			return;
		}

		// Gather data
		const data = {
			transaction_name: me.selected_transaction.name,
			vendor: $('#vendor-select').val() || null,
			expense_account: expense_account,
			notes: $('#classification-notes').val() || null
		};

		// Handle cost center allocation
		if ($('#single-cc-btn').hasClass('active')) {
			data.cost_center = $('#cost-center-select').val();
			if (!data.cost_center) {
				frappe.msgprint('Please select a cost center');
				return;
			}
		} else {
			// Gather splits
			const splits = [];
			$('#split-table-body tr').each(function() {
				const split = {
					cost_center: $(this).find('.split-cost-center-select').val(),
					amount: parseFloat($(this).find('.split-amount').val()) || null,
					percentage: parseFloat($(this).find('.split-percentage').val()) || null
				};
				if (split.cost_center) {
					splits.push(split);
				}
			});

			if (splits.length === 0) {
				frappe.msgprint('Please add at least one cost center split');
				return;
			}

			data.cost_center_splits = splits;
		}

		// Save classification
		frappe.call({
			method: 'amex_integration.amex_integration.page.amex_review.amex_review.classify_transaction',
			args: data,
			callback: (r) => {
				if (r.message && r.message.status === 'success') {
					frappe.show_alert({message: 'Transaction classified successfully', indicator: 'green'});
					me.load_transactions();
					me.load_transaction_details(me.selected_transaction.name);
				}
			}
		});
	}

	approve_transaction() {
		const me = this;

		frappe.call({
			method: 'amex_integration.amex_integration.page.amex_review.amex_review.approve_transaction',
			args: { transaction_name: me.selected_transaction.name },
			callback: (r) => {
				if (r.message && r.message.status === 'success') {
					frappe.show_alert({message: 'Transaction approved', indicator: 'green'});
					me.load_transactions();
					me.load_transaction_details(me.selected_transaction.name);
				}
			}
		});
	}

	post_transaction() {
		const me = this;

		frappe.call({
			method: 'amex_integration.amex_integration.page.amex_review.amex_review.post_transaction',
			args: { transaction_name: me.selected_transaction.name },
			callback: (r) => {
				if (r.message && r.message.status === 'success') {
					frappe.show_alert({message: `Posted to Journal Entry ${r.message.journal_entry}`, indicator: 'green'});
					me.load_transactions();
					me.load_transaction_details(me.selected_transaction.name);
				}
			}
		});
	}

	mark_as_duplicate() {
		const me = this;

		frappe.call({
			method: 'amex_integration.amex_integration.page.amex_review.amex_review.mark_as_duplicate',
			args: { transaction_name: me.selected_transaction.name },
			callback: (r) => {
				if (r.message && r.message.status === 'success') {
					frappe.show_alert({message: 'Marked as duplicate', indicator: 'orange'});
					me.load_transactions();
					$('#classification-panel').hide();
				}
			}
		});
	}

	bulk_approve_and_post() {
		const me = this;
		const selected = Array.from(me.selected_transactions);

		if (selected.length === 0) {
			frappe.msgprint('Please select transactions to approve and post');
			return;
		}

		frappe.confirm(
			`Approve and post ${selected.length} transaction(s)?`,
			() => {
				frappe.call({
					method: 'amex_integration.amex_integration.page.amex_review.amex_review.bulk_approve_and_post',
					args: { transaction_names: selected },
					callback: (r) => {
						if (r.message) {
							const msg = `Posted: ${r.message.posted.length}, Errors: ${r.message.errors.length}`;
							frappe.msgprint(msg);
							me.load_transactions();
							me.selected_transactions.clear();
							$('#select-all-transactions').prop('checked', false);
						}
					}
				});
			}
		);
	}

	create_vendor() {
		const me = this;
		const vendor_name = $('#new-vendor-name').val();

		if (!vendor_name) {
			frappe.msgprint('Please enter vendor name');
			return;
		}

		frappe.call({
			method: 'amex_integration.amex_integration.page.amex_review.amex_review.create_vendor_quick',
			args: {
				vendor_name: vendor_name,
				supplier_group: $('#new-vendor-group').val(),
				country: $('#new-vendor-country').val()
			},
			callback: (r) => {
				if (r.message && r.message.status === 'success') {
					frappe.show_alert({message: 'Vendor created successfully', indicator: 'green'});
					$('#vendor-modal').modal('hide');
					
					// Add to dropdown and select
					$('#vendor-select').append(`<option value="${r.message.supplier}">${vendor_name}</option>`);
					$('#vendor-select').val(r.message.supplier);
					
					// Clear form
					$('#new-vendor-name').val('');
				}
			}
		});
	}

	update_selected_transactions() {
		this.selected_transactions.clear();
		$('.transaction-checkbox:checked').each((i, el) => {
			this.selected_transactions.add($(el).val());
		});
	}
}


