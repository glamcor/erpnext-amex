# AMEX Integration - Installation Checklist

## Pre-Installation

- [ ] ERPNext 14.x or later is running
- [ ] Access to Frappe bench (SSH or local)
- [ ] GitHub repository accessible: https://github.com/glamcor/erpnext-amex.git
- [ ] Sample AMEX CSV file ready for testing

## Installation Steps

### 1. Get the App
```bash
cd ~/frappe-bench
bench get-app https://github.com/glamcor/erpnext-amex.git
```
- [ ] App cloned successfully
- [ ] No errors in console

### 2. Install on Site
```bash
bench --site your-site-name install-app amex_integration
```
- [ ] Installation completed without errors
- [ ] "Installing amex_integration" message appeared
- [ ] No DocType errors

### 3. Migrate Database
```bash
bench --site your-site-name migrate
```
- [ ] All DocTypes created
- [ ] No migration errors
- [ ] Database tables created

### 4. Clear Cache & Restart
```bash
bench --site your-site-name clear-cache
bench restart
```
- [ ] Cache cleared
- [ ] Bench restarted successfully

## Post-Installation Verification

### 5. Check Module Installed
- [ ] Log into ERPNext
- [ ] Search "AMEX Integration" in awesome bar
- [ ] Module appears in results
- [ ] Click opens module page

### 6. Verify DocTypes Created
- [ ] AMEX Import Batch exists
- [ ] AMEX Transaction exists
- [ ] AMEX Integration Settings exists
- [ ] Fraud Report exists
- [ ] AMEX Vendor Classification Rule exists
- [ ] AMEX Transaction Split (child table) exists

### 7. Verify Pages & Reports
- [ ] AMEX Transaction Review page accessible at `/app/amex_review`
- [ ] AMEX Import Status report exists
- [ ] Unclassified Transactions report exists

### 8. Check Permissions
- [ ] AMEX Transaction Manager role exists
- [ ] AMEX Transaction Approver role exists
- [ ] Permissions are set on DocTypes

## Configuration

### 9. Configure Settings
Go to **AMEX Integration Settings**:

**Required:**
- [ ] Set AMEX Liability Account
- [ ] Set Default Expense Account (optional but recommended)

**Processing:**
- [ ] Auto Exclude Payments: Enabled
- [ ] Enable Duplicate Detection: Enabled
- [ ] Enable Classification Memory: Enabled

**Optional (Phase 2):**
- [ ] ML Classification settings (if using SageMaker)
- [ ] Slack settings (if using notifications)
- [ ] Google API settings (if using enrichment)

### 10. Set Up Chart of Accounts

Create/verify accounts:
- [ ] AMEX Liability account exists (Current Liabilities)
- [ ] Expense accounts exist (or use existing)
  - [ ] Advertising expenses
  - [ ] Travel expenses
  - [ ] Office expenses
  - [ ] Professional fees
  - [ ] etc.

### 11. Set Up Cost Centers

Create cost center hierarchy:
- [ ] Marketing cost centers
- [ ] Operations cost centers
- [ ] Any other departments

### 12. Assign User Roles

For each user:
- [ ] Assign AMEX Transaction Manager or Approver role
- [ ] Test user can access module

## Functional Testing

### 13. Test CSV Import

- [ ] Create new AMEX Import Batch
- [ ] Upload sample CSV file
- [ ] Save
- [ ] Transactions created automatically
- [ ] Batch statistics updated (total, pending, duplicates, excluded)
- [ ] No errors in console

### 14. Test Review UI

- [ ] Navigate to `/app/amex_review`
- [ ] Page loads without errors
- [ ] Transaction list appears
- [ ] Filters work (batch, card member, dates)
- [ ] Click transaction opens classification panel
- [ ] All fields visible

### 15. Test Classification

- [ ] Select a transaction
- [ ] Choose expense account
- [ ] Choose cost center
- [ ] Click "Classify"
- [ ] Status changes to "Classified"
- [ ] Transaction refreshes

### 16. Test Vendor Creation

- [ ] Click "+ New" next to vendor dropdown
- [ ] Modal opens
- [ ] Enter vendor name
- [ ] Click "Create Vendor"
- [ ] Vendor created successfully
- [ ] Vendor appears in dropdown

### 17. Test Cost Center Splits

- [ ] Select transaction
- [ ] Click "Split" button
- [ ] Add multiple cost center rows
- [ ] Enter amounts or percentages
- [ ] Verify totals validate correctly
- [ ] Save classification

### 18. Test Approval & Posting

- [ ] Approve a classified transaction
- [ ] Status changes to "Approved"
- [ ] Click "Post to Journal Entry"
- [ ] Journal Entry created
- [ ] JE has correct:
  - [ ] Credit to AMEX Liability
  - [ ] Debit to Expense Account
  - [ ] Cost center assigned
  - [ ] Vendor linked (if applicable)
- [ ] Transaction status = "Posted"

### 19. Test Duplicate Detection

- [ ] Upload same CSV twice
- [ ] Second import marks duplicates
- [ ] Duplicate count shown in batch
- [ ] Duplicate transactions have status "Duplicate"

### 20. Test Payment Exclusion

- [ ] Verify AMEX payments excluded (negative amounts)
- [ ] "ONLINE PAYMENT - THANK YOU" transactions marked excluded
- [ ] Excluded count shown in batch

### 21. Test Classification Memory

- [ ] Classify same vendor multiple times
- [ ] Upload new CSV with same vendor
- [ ] Suggestion appears for that vendor
- [ ] Confidence score increases with use

### 22. Test Reports

- [ ] Open AMEX Import Status report
- [ ] Data shows correctly
- [ ] Open Unclassified Transactions report
- [ ] Pending transactions listed

### 23. Test Bulk Operations

- [ ] Select multiple transactions
- [ ] Click "Bulk Approve & Post"
- [ ] All selected transactions processed
- [ ] Journal Entries created

## Optional: Phase 2 & 3 Setup

### 24. SageMaker Setup (Optional)

If enabling ML classification:
- [ ] Follow `sagemaker/README.md`
- [ ] Transform training data
- [ ] Train model
- [ ] Deploy endpoint
- [ ] Configure in ERPNext settings
- [ ] Test ML predictions

### 25. Slack Integration (Optional)

If enabling Slack notifications:
- [ ] Create Slack bot
- [ ] Get bot token
- [ ] Configure in settings
- [ ] Add slack_user_id to User DocType
- [ ] Populate user Slack IDs
- [ ] Test notification

### 26. Google Search API (Optional)

If enabling vendor enrichment:
- [ ] Get Google Custom Search API key
- [ ] Create search engine
- [ ] Configure in settings
- [ ] Test vendor search

## 🎉 Installation Complete!

Once all checkboxes are checked, your AMEX Integration is fully operational!

## Common Installation Issues

### Error: "App already exists"
```bash
# Remove and reinstall
bench remove-app amex_integration
bench get-app https://github.com/glamcor/erpnext-amex.git
bench --site your-site-name install-app amex_integration
```

### Error: "DocType already exists"
```bash
# This usually means partial installation
# Clear the site and reinstall, or:
bench --site your-site-name migrate --skip-failing
```

### Error: "Permission denied"
```bash
# Check file permissions
cd ~/frappe-bench/apps/amex_integration
sudo chown -R frappe:frappe .
```

### CSS/JS Not Loading
```bash
# Build assets
bench build --app amex_integration

# Or build everything
bench build
```

## Support

After installation:
1. Review `QUICK_REFERENCE.md` for daily usage
2. Review `IMPLEMENTATION_GUIDE.md` for detailed documentation
3. Test with sample data before production use
4. Train users on the review UI workflow

---

**Ready to process AMEX expenses efficiently!** 🚀

