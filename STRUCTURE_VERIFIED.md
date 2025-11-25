# ✅ App Structure - Verified Correct

This document confirms the app structure matches the official Frappe app conventions (ERPNext, HRMS, etc.)

## Final Structure

```
erpnext-amex/                          ← GitHub repository root
├── erpnext_amex/                      ← Module directory (app_name)
│   ├── __init__.py                    ✅ Contains __version__
│   ├── hooks.py                       ✅ App configuration
│   ├── modules.txt                    ✅ Module list
│   ├── patches.txt                    ✅ Database patches
│   ├── api.py                         ✅ API endpoints
│   ├── config/                        ✅ Desktop/docs config
│   │   ├── desktop.py
│   │   └── docs.py
│   ├── public/                        ✅ Static assets
│   │   ├── js/erpnext_amex.js
│   │   └── css/erpnext_amex.css
│   ├── doctype/                       ✅ 6 DocTypes
│   │   ├── amex_import_batch/
│   │   ├── amex_transaction/
│   │   ├── amex_transaction_split/
│   │   ├── amex_vendor_classification_rule/
│   │   ├── amex_integration_settings/
│   │   └── fraud_report/
│   ├── page/                          ✅ Custom pages
│   │   └── amex_review/
│   ├── report/                        ✅ Custom reports
│   │   ├── amex_import_status/
│   │   └── unclassified_transactions/
│   └── utils/                         ✅ Utility modules
│       ├── csv_parser.py
│       ├── classification_memory.py
│       ├── journal_entry_creator.py
│       ├── ml_classifier.py
│       ├── slack_notifier.py
│       └── vendor_enrichment.py
│
├── pyproject.toml                     ✅ Python project config
├── setup.py                           ✅ Package setup
├── requirements.txt                   ✅ Dependencies
├── license.txt                        ✅ License
├── README.md                          ✅ Documentation
├── sagemaker/                         ✅ ML training scripts
└── scripts/                           ✅ Data transformation scripts
```

## Key Points

### ✅ Correct Placement (Inside `erpnext_amex/`)
- `hooks.py` - App configuration and metadata
- `modules.txt` - List of app modules
- `patches.txt` - Database migration patches
- `__init__.py` - Contains `__version__`
- `config/` - Desktop and docs configuration
- `public/` - Static JS/CSS assets

### ✅ Root Level Files
- `pyproject.toml` - Python project metadata
- `setup.py` - Package installation
- `requirements.txt` - Python dependencies
- `license.txt` - MIT license
- `README.md` - Project documentation

## Comparison with Official Apps

| File | ERPNext | HRMS | erpnext_amex |
|------|---------|------|--------------|
| `hooks.py` | `erpnext/hooks.py` | `hrms/hooks.py` | `erpnext_amex/hooks.py` ✅ |
| `modules.txt` | `erpnext/modules.txt` | `hrms/modules.txt` | `erpnext_amex/modules.txt` ✅ |
| `patches.txt` | `erpnext/patches.txt` | `hrms/patches.txt` | `erpnext_amex/patches.txt` ✅ |
| `__init__.py` | `erpnext/__init__.py` | `hrms/__init__.py` | `erpnext_amex/__init__.py` ✅ |

## Installation

The app should now install correctly on Frappe Cloud:

```bash
# Via Frappe Cloud UI
# Organization: glamcor
# Repository: erpnext-amex
# Branch: main

# Or via command line
bench get-app https://github.com/glamcor/erpnext-amex.git
bench --site your-site install-app erpnext_amex
```

## Why This Structure?

Frappe expects the app module directory to contain all app-specific files:
1. **hooks.py** - Defines app metadata and integration points
2. **modules.txt** - Lists modules for the workspace
3. **patches.txt** - Database migration tracking
4. **config/** - Desktop icons and documentation
5. **public/** - Static assets served by the web server

The root of the repository contains only Python packaging files (`setup.py`, `pyproject.toml`) and documentation.

---

**Last Updated:** November 25, 2025
**Structure Verified Against:** ERPNext develop, HRMS develop
