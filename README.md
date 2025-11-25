# AMEX Integration for ERPNext

Custom ERPNext app for importing and classifying American Express CSV transaction files with ML-powered automation.

## Features

### Phase 1 (Core)
- CSV import with duplicate detection
- Manual classification UI
- Cost center split allocation
- Journal entry generation
- Classification memory system

### Phase 2 (ML)
- AWS SageMaker integration
- Automated transaction classification
- Confidence scoring

### Phase 3 (Integrations)
- Slack notifications for cardholders
- Vendor enrichment via Google Search API
- Fraud detection and reporting

### Phase 4 (Advanced)
- Advanced reporting and analytics
- Model retraining pipeline
- Bulk operations

## Installation

1. Get the app:
```bash
bench get-app https://github.com/your-org/amex_integration
```

2. Install on site:
```bash
bench --site your-site install-app amex_integration
```

3. Configure settings:
- Go to AMEX Integration Settings
- Set AMEX liability account
- Configure default expense account
- Add authorized users

## Usage

1. Upload AMEX CSV file via AMEX Import Batch
2. Review and classify transactions
3. Approve and post to Journal Entry

## Development

```bash
bench --site your-site set-config developer_mode 1
bench --site your-site clear-cache
```

## License

MIT

