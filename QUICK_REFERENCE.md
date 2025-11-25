# AMEX Integration - Quick Reference

## 📥 Import AMEX CSV

1. **AMEX Import Batch** → New
2. Upload CSV file
3. Save → Auto-imports transactions

## 🔍 Review & Classify

1. Go to **AMEX Transaction Review** page
2. Click transaction from list
3. Fill classification panel:
   - Vendor (optional)
   - Expense Account (required)
   - Cost Center (required)
   - Notes (optional)
4. Click **Classify** → **Approve** → **Post**

## 💰 Cost Center Splits

1. Select transaction
2. Click "Split" button
3. Add rows:
   - Cost Center
   - Amount OR Percentage
4. Must total 100%

## 🏢 Create Vendor Quickly

1. In classification panel
2. Click "+ New" next to vendor dropdown
3. Enter vendor name
4. Save → Auto-selected

## 🤖 Enable ML Classification

**Settings:**
1. AMEX Integration Settings
2. ML Settings section
3. ✓ Enable ML Classification
4. Enter SageMaker endpoint name
5. Enter AWS credentials
6. Set threshold (0.90 = 90% confidence)

**Usage:**
- Transactions auto-classified on import
- Review only low-confidence items
- Accept or override predictions

## 💬 Enable Slack Notifications

**Setup:**
1. Create Slack bot
2. AMEX Integration Settings → Slack Settings
3. ✓ Enable Slack Notifications
4. Enter bot token
5. Map users to Slack IDs

**Usage:**
- Low-confidence transactions auto-notify cardholders
- Cardholders click button to classify or mark personal

## 🔍 Vendor Enrichment

**Setup:**
1. Get Google Custom Search API key
2. AMEX Integration Settings → Google API Settings
3. ✓ Enable Vendor Enrichment
4. Enter API key and search engine ID

**Usage:**
- Unknown vendors auto-searched
- Suggestions appear in classification panel
- Accept or override suggestions

## 📊 Reports

- **AMEX Import Status**: Track batch processing
- **Unclassified Transactions**: Find pending items

## 🔐 User Roles

**AMEX Transaction Manager:**
- Upload CSVs
- Classify transactions
- Create vendors

**AMEX Transaction Approver:**
- Approve transactions
- Post to journal entries

## ⚡ Keyboard Shortcuts

- Click transaction row → Opens classification panel
- Tab through fields for quick entry
- Enter after cost center → Saves classification

## 🚫 Excluded Automatically

- AMEX payments ("ONLINE PAYMENT - THANK YOU")
- Duplicate transactions (same reference)
- Negative amounts (credits/refunds)

## 📋 Bulk Operations

1. Check boxes next to transactions
2. Click "Bulk Approve & Post"
3. Confirms all selected at once

## 🛠️ Troubleshooting

**CSV Import Fails:**
- Check file is AMEX Business format
- Ensure UTF-8 encoding

**Duplicates Not Detected:**
- Enable in settings
- Check Reference field populated

**ML Not Working:**
- Verify endpoint is running
- Check AWS credentials
- Test endpoint manually

**Slack Not Sending:**
- Verify bot token
- Check bot permissions
- Ensure user has slack_user_id

## 📞 Common API Calls

```python
# Get pending transactions
GET /api/method/amex_integration.amex_integration.api.get_pending_transactions

# Classify transaction
POST /api/method/amex_integration.amex_integration.api.classify_transaction

# Post to journal entry
POST /api/method/amex_integration.amex_integration.api.post_to_journal_entry

# Get batch status
GET /api/method/amex_integration.amex_integration.api.get_batch_status
```

## ⚙️ Settings Checklist

**Required:**
- [x] AMEX Liability Account
- [x] Default Expense Account

**Recommended:**
- [x] Auto Exclude Payments
- [x] Enable Duplicate Detection
- [x] Enable Classification Memory

**Optional:**
- [ ] ML Classification (requires SageMaker)
- [ ] Slack Notifications (requires bot)
- [ ] Vendor Enrichment (requires Google API)

## 📁 File Locations

- **Review UI:** `/app/amex_review`
- **Import Batch:** List → AMEX Import Batch
- **Transactions:** List → AMEX Transaction
- **Settings:** Search → AMEX Integration Settings
- **Reports:** Reports → AMEX Integration module

## 🎯 Success Tips

1. **Start Simple:** Use manual classification first
2. **Build Memory:** Classify 50-100 transactions to train memory system
3. **Add ML:** Set up SageMaker after memory is working
4. **Batch Process:** Import weekly, not daily
5. **Review Stats:** Check reports to find patterns
6. **Train Users:** Show the review UI workflow

## 🔄 Weekly Workflow

**Monday Morning:**
1. Export AMEX CSV (previous week)
2. Upload to AMEX Import Batch
3. Review high-confidence items (auto-classified)
4. Classify remaining pending items
5. Bulk approve and post
6. Review reports for completeness

**Time:** 15-30 minutes for 50-100 transactions

---

**Need More Help?** See `IMPLEMENTATION_GUIDE.md` for detailed instructions.

