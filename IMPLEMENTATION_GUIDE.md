# AMEX Integration - Implementation Guide

## Overview

This custom ERPNext app provides intelligent AMEX expense classification and import with ML-powered automation, eliminating manual coding errors and providing superior audit trails compared to legacy NetSuite workflows.

## Features Implemented

### ✓ Phase 1: Core Import & Manual Classification (COMPLETE)

- **CSV Import System**
  - Upload AMEX CSV files via batch interface
  - Automatic duplicate detection by transaction reference
  - Auto-exclude AMEX payment transactions
  - Import statistics and validation

- **Transaction Review UI** (`/app/amex_review`)
  - List view with filters (batch, card member, date range, amount)
  - Detailed classification panel
  - Bulk selection and operations
  - Real-time validation

- **Classification Features**
  - Vendor/Supplier linking
  - Expense account mapping
  - Cost center allocation (single or split)
  - Split by amount or percentage
  - Classification memory system with auto-suggestions
  - Notes and audit trail

- **Journal Entry Generation**
  - Auto-create journal entries from classified transactions
  - Support for single or multiple cost centers
  - Vendor reference tracking
  - Bulk posting capability

- **Validation & Business Rules**
  - Duplicate prevention
  - AMEX payment exclusion
  - Cost center split validation
  - Accounting period checks
  - Required field validation

- **Reporting**
  - AMEX Import Status Report
  - Unclassified Transactions Report
  - Classification statistics

- **Fraud Detection**
  - Fraud Report DocType
  - Mark transactions as fraud
  - Track AMEX dispute cases

### ✓ Phase 2: ML Integration (COMPLETE)

- **Training Data Transformation**
  - NetSuite → ERPNext data transformation script
  - Configurable mapping for departments, classes, accounts
  - Weighted training data based on recency

- **SageMaker Model**
  - Multi-output classification (vendor, account, cost center)
  - Feature extraction from description, category, amount, date
  - Confidence scoring
  - Training and inference scripts ready

- **ERPNext ML Integration**
  - Auto-classify transactions via SageMaker endpoint
  - Confidence-based auto-acceptance
  - ML prediction storage and display
  - Batch classification support

### ✓ Phase 3: Advanced Integrations (COMPLETE)

- **Slack Integration**
  - Send DMs to cardholders for unclear transactions
  - Interactive buttons for quick classification
  - Batch completion notifications
  - Low-confidence transaction alerts

- **Vendor Enrichment**
  - Google Search API integration
  - Automatic merchant lookup for unknown vendors
  - Business category suggestion
  - Confidence scoring

## Installation

### Prerequisites

1. ERPNext 14.x or later running on Frappe Cloud or self-hosted
2. Python 3.10+
3. Access to GitHub for repository hosting
4. (Optional) AWS account for SageMaker
5. (Optional) Slack workspace and bot token
6. (Optional) Google Custom Search API credentials

### Step 1: Install the App

```bash
# On your Frappe bench
cd frappe-bench
bench get-app https://github.com/your-org/erpnext_amex

# Install on your site
bench --site your-site install-app erpnext_amex

# Migrate database
bench --site your-site migrate
```

### Step 2: Configure Settings

Navigate to `AMEX Integration Settings` in ERPNext:

**Account Settings (Required):**
- Set AMEX Liability Account (e.g., "AMEX Card Payable")
- Set Default Expense Account

**Processing Settings:**
- Enable Auto Exclude Payments: ✓
- Enable Duplicate Detection: ✓
- Enable Classification Memory: ✓

**ML Settings (Optional):**
- Enable ML Classification after SageMaker setup
- Enter SageMaker Endpoint Name
- Configure AWS credentials
- Set ML Auto Accept Threshold (0.90 recommended)

**Slack Settings (Optional):**
- Enable Slack Notifications
- Enter Slack Bot Token
- Enter Slack Signing Secret

**Google API Settings (Optional):**
- Enable Vendor Enrichment
- Enter Google Search API Key
- Enter Search Engine ID

### Step 3: Set Up Roles

Create custom roles:
- **AMEX Transaction Manager**: Can upload CSVs, classify transactions, create vendors
- **AMEX Transaction Approver**: Can approve and post transactions

Assign roles to users as appropriate.

### Step 4: Configure Cost Centers

Set up your cost center hierarchy in ERPNext:

```
Marketing - Your Company
├── Content Creation - Your Company
└── Paid Ads - Your Company
    ├── TikTok - Your Company
    ├── Meta - Your Company
    └── Google - Your Company

Operations - Your Company
├── Logistics - Your Company
└── Warehouse - Your Company
```

## Usage Workflow

### Basic Workflow (Manual Classification)

1. **Upload CSV**
   - Go to `AMEX Import Batch`
   - Click "New"
   - Upload CSV file from AMEX
   - Save - system automatically parses transactions

2. **Review & Classify**
   - Go to `AMEX Transaction Review` page
   - Select a transaction from the list
   - Classification panel appears on right
   - Fill in:
     - Vendor (optional)
     - Expense Account (required)
     - Cost Center (single or split)
     - Notes (optional)
   - Click "Classify"

3. **Approve**
   - Click "Approve" after classification
   - System validates data

4. **Post to Journal Entry**
   - Click "Post to Journal Entry"
   - System creates JE with proper debits/credits
   - Transaction marked as "Posted"

### Advanced Workflow (with ML)

1. **Upload CSV**
   - Same as above

2. **Auto-Classification**
   - System automatically calls SageMaker
   - Stores predictions in transactions
   - High-confidence predictions auto-accepted

3. **Review Only Low-Confidence**
   - Filter for status "Pending"
   - Review suggestions
   - Accept or override classifications

4. **Bulk Approve & Post**
   - Select multiple transactions
   - Click "Bulk Approve & Post"
   - System processes all at once

### Cost Center Splits

For expenses spanning multiple cost centers:

1. Select transaction
2. Click "Split" allocation type
3. Add rows for each cost center
4. Enter either:
   - Amount for each center
   - Percentage for each center
5. System validates total = 100%

Example: $1,000 advertising split:
- TikTok: $600 (60%)
- Meta: $400 (40%)

## SageMaker Setup (Phase 2)

Follow detailed instructions in `sagemaker/README.md`:

1. Transform training data from NetSuite
2. Upload to S3
3. Create training job
4. Deploy model to endpoint
5. Configure endpoint name in ERPNext settings

Expected accuracy: 85-95% for vendor, account, and cost center predictions.

## API Endpoints

The app exposes RESTful APIs for integration:

```python
# Get pending transactions
GET /api/method/erpnext_amex.erpnext_amex.api.get_pending_transactions

# Classify transaction
POST /api/method/erpnext_amex.erpnext_amex.api.classify_transaction
{
    "transaction_name": "AMEX-TXN-001",
    "expense_account": "Advertising - Your Company",
    "cost_center": "Marketing - Your Company"
}

# Post to journal entry
POST /api/method/erpnext_amex.erpnext_amex.api.post_to_journal_entry
{
    "transaction_name": "AMEX-TXN-001"
}

# Get batch status
GET /api/method/erpnext_amex.erpnext_amex.api.get_batch_status?batch_id=AMEX-BATCH-001
```

## Troubleshooting

### CSV Import Fails

- Check CSV format matches AMEX Business Platinum format
- Ensure all required columns present: Date, Description, Amount, Reference, Card Member
- Check for encoding issues (UTF-8 required)

### Duplicate Detection Not Working

- Verify "Enable Duplicate Detection" is checked in settings
- Check that transactions have unique Reference values
- Look for transactions marked "Duplicate" status

### ML Predictions Not Showing

- Verify SageMaker endpoint is running
- Check AWS credentials in settings
- Review CloudWatch logs for endpoint errors
- Test endpoint manually with sample payload

### Slack Notifications Not Sending

- Verify Slack bot token is correct
- Check bot has permission to send DMs
- Ensure users have `slack_user_id` field populated
- Review Slack webhook setup

### Journal Entry Creation Fails

- Check AMEX Liability Account is configured
- Verify expense account exists and is active
- Ensure cost center exists
- Check accounting period is open
- Review validation error messages

## Performance Optimization

- **Large Batches**: Process in chunks of 100-200 transactions
- **ML Inference**: Use batch prediction for multiple transactions
- **Duplicate Detection**: Runs on database index, very fast
- **Classification Memory**: Cached for performance

## Security Considerations

- AWS credentials stored encrypted in ERPNext
- Slack tokens stored encrypted
- API endpoints require authentication
- Role-based access control enforced
- Audit trail for all classifications

## Maintenance

### Weekly Tasks
- Review unclassified transactions report
- Check for new vendors needing setup
- Verify ML accuracy metrics

### Monthly Tasks
- Export classified data for ML retraining
- Review fraud reports
- Audit cost center allocations

### Quarterly Tasks
- Retrain ML model with new data
- Review and update mapping rules
- Optimize classification memory rules

## Support & Contribution

For issues or feature requests:
1. Check existing GitHub issues
2. Review this guide and README
3. Check Frappe/ERPNext forums
4. Create detailed issue with logs

## Success Metrics

Track these KPIs:

**Phase 1:**
- CSV import success rate: Target 100%
- Time to classify transaction: Target < 30 seconds
- Duplicate detection accuracy: Target 100%

**Phase 2:**
- ML classification accuracy: Target > 85%
- Auto-accept rate: Target > 70%
- Time savings: Target 70% reduction

**Phase 3:**
- Slack response rate: Target > 80% within 24 hours
- Vendor enrichment success: Target > 60%

## Next Steps

1. Complete Phase 1 setup and test with sample CSV
2. Train classification memory with 50-100 transactions
3. Set up SageMaker for ML classification
4. Configure Slack integration
5. Enable Google Search for vendor enrichment
6. Monitor performance and adjust thresholds
7. Train users on the review UI
8. Establish monthly retraining schedule

## Files & Structure

```
erpnext_amex/
├── erpnext_amex/
│   ├── doctype/                   # All DocTypes
│   ├── page/amex_review/          # Main review UI
│   ├── report/                    # Custom reports
│   ├── utils/                     # Utility modules
│   │   ├── csv_parser.py
│   │   ├── classification_memory.py
│   │   ├── journal_entry_creator.py
│   │   ├── ml_classifier.py
│   │   ├── slack_notifier.py
│   │   └── vendor_enrichment.py
│   ├── api.py                     # REST API endpoints
│   └── hooks.py                   # App hooks
├── scripts/
│   └── transform_netsuite_to_erpnext.py
├── sagemaker/
│   ├── train.py
│   ├── inference.py
│   └── requirements.txt
└── README.md
```





