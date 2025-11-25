# ✅ Final Frappe App Structure - CORRECT

## The Problem

When installing the app, you got this error:
```
ModuleNotFoundError: No module named 'erpnext_amex.amex_integration'
```

## Root Cause

Frappe's module system works like this:

1. **modules.txt** contains: `AMEX Integration`
2. Frappe converts "AMEX Integration" → `amex_integration` (Python-safe name)
3. Frappe looks for: `erpnext_amex/amex_integration/` directory
4. But we had DocTypes directly in `erpnext_amex/doctype/` ❌

## The Solution

Create a **module directory** inside the app to hold all module-specific content:

```
erpnext-amex/                              ← GitHub repository
├── erpnext_amex/                          ← App package
│   ├── __init__.py                        ✅ App version
│   ├── hooks.py                           ✅ App configuration
│   ├── modules.txt                        ✅ "AMEX Integration"
│   ├── patches.txt                        ✅ Database patches
│   ├── config/                            ✅ App-level config
│   ├── public/                            ✅ App-level assets
│   ├── utils/                             ✅ App-level utilities
│   ├── api.py                             ✅ App-level API
│   │
│   └── amex_integration/                  ✅ MODULE DIRECTORY
│       ├── __init__.py                    ✅ Module init
│       ├── doctype/                       ✅ All DocTypes here
│       │   ├── amex_import_batch/
│       │   ├── amex_transaction/
│       │   ├── amex_transaction_split/
│       │   ├── amex_vendor_classification_rule/
│       │   ├── amex_integration_settings/
│       │   └── fraud_report/
│       ├── page/                          ✅ All Pages here
│       │   └── amex_review/
│       └── report/                        ✅ All Reports here
│           ├── amex_import_status/
│           └── unclassified_transactions/
│
├── setup.py
├── pyproject.toml
└── requirements.txt
```

## Key Understanding

### App vs Module

- **App** (`erpnext_amex`) = The entire Frappe application
  - Contains app-wide utilities, config, hooks
  - Lives in `apps/erpnext_amex/erpnext_amex/`

- **Module** (`amex_integration`) = A functional group within the app
  - Contains DocTypes, Pages, Reports for a specific feature area
  - Lives in `apps/erpnext_amex/erpnext_amex/amex_integration/`

### Why This Structure?

Frappe's import system works like this:

```python
# When Frappe sees module "AMEX Integration" in modules.txt
module_name = "amex_integration"  # Python-safe conversion

# It tries to import:
import erpnext_amex.amex_integration.doctype.amex_transaction
#      └─ app ─┘ └── module ───┘ └─── doctype path ────┘
```

Without the `amex_integration/` directory, this import fails!

## Files Changed

1. Created `erpnext_amex/amex_integration/__init__.py`
2. Moved `erpnext_amex/doctype/` → `erpnext_amex/amex_integration/doctype/`
3. Moved `erpnext_amex/page/` → `erpnext_amex/amex_integration/page/`
4. Moved `erpnext_amex/report/` → `erpnext_amex/amex_integration/report/`

## Installation Steps

Now the app should install correctly:

### On Frappe Cloud
1. Update the app (it will pull latest from GitHub)
2. Try installing again: `bench --site your-site install-app erpnext_amex`

### Command Line
```bash
cd ~/frappe-bench
bench get-app https://github.com/glamcor/erpnext-amex.git --branch main
bench --site your-site install-app erpnext_amex
bench --site your-site migrate
bench restart
```

## Verification

After installation, you should see:
- **Workspace:** "AMEX Integration" in the sidebar
- **DocTypes:** 6 new DocTypes available
- **Page:** "AMEX Review" custom page
- **Reports:** 2 custom reports

## Why Was This Confusing?

The Frappe documentation isn't always clear about the distinction between:
- **App-level** files (in `erpnext_amex/`)
- **Module-level** files (in `erpnext_amex/amex_integration/`)

Many examples show simple apps with just one module, where the structure is flatter. But for ERPNext apps with explicit module names in `modules.txt`, you **must** have the module directory.

---

**Last Updated:** November 25, 2025  
**Status:** ✅ Structure corrected and pushed to GitHub  
**Next Step:** Update app on bench and install on site

