# Deployment Instructions

## ✅ App Structure Fixed

The app structure has been corrected to match Frappe's requirements. The `hooks.py` file is now at the root level.

## 🚀 Installation on ERPNext

### Step 1: Get the App

SSH into your Frappe Cloud server or access your bench directory:

```bash
cd ~/frappe-bench

# Get the app from GitHub
bench get-app https://github.com/glamcor/erpnext-amex.git
```

This will clone the app into `apps/erpnext_amex/`

### Step 2: Install on Your Site

```bash
# Install the app on your site
bench --site your-site-name install-app erpnext_amex

# This will:
# - Create all 6 DocTypes
# - Set up permissions
# - Create the AMEX Integration module
# - Install reports and pages
```

### Step 3: Run Migration

```bash
# Migrate to create database tables
bench --site your-site-name migrate
```

### Step 4: Clear Cache and Restart

```bash
# Clear cache to load new assets
bench --site your-site-name clear-cache

# Restart bench
bench restart
```

### Step 5: Verify Installation

1. Log into your ERPNext instance
2. Search for "AMEX Integration" in the awesome bar
3. You should see:
   - AMEX Import Batch
   - AMEX Transaction
   - AMEX Transaction Review (page)
   - AMEX Integration Settings
   - Reports

### Step 6: Initial Configuration

1. Go to **AMEX Integration Settings**
2. Set **AMEX Liability Account** (create if needed):
   - Account Type: Liability
   - Example: "AMEX Card Payable - Your Company"
3. Set **Default Expense Account** (optional)
4. Enable settings:
   - ✓ Auto Exclude Payments
   - ✓ Enable Duplicate Detection
   - ✓ Enable Classification Memory
5. Save

### Step 7: Set Up Roles

1. Go to **Role Permission Manager**
2. Create custom roles if not exists:
   - **AMEX Transaction Manager**
   - **AMEX Transaction Approver**
3. Assign permissions (already set in DocTypes)
4. Assign roles to users

### Step 8: Test with Sample Data

1. Go to **AMEX Import Batch** → New
2. Upload the sample CSV file
3. Save
4. Go to **AMEX Transaction Review** page
5. Verify transactions loaded
6. Test classification workflow

## 🔄 Updating the App

When you make changes and push to GitHub:

```bash
# On your server
cd ~/frappe-bench/apps/erpnext_amex

# Pull latest changes
git pull origin main

# Run migration (if DocTypes changed)
bench --site your-site-name migrate

# Clear cache
bench --site your-site-name clear-cache

# Restart
bench restart
```

## 🧪 Verification Checklist

After installation, verify:

- [ ] Can access AMEX Integration Settings
- [ ] Can create AMEX Import Batch
- [ ] Can upload CSV file
- [ ] Transactions are created automatically
- [ ] Can access AMEX Transaction Review page
- [ ] Can classify a transaction
- [ ] Can create vendor via quick-create
- [ ] Can approve a transaction
- [ ] Can post to Journal Entry
- [ ] Journal Entry is created correctly
- [ ] Duplicate detection works
- [ ] AMEX payments are excluded
- [ ] Reports are accessible

## 🆘 Troubleshooting

### "Not a valid Frappe App" Error

**Fixed!** The structure has been corrected. `hooks.py` is now at the root level.

### Module Not Found Errors

```bash
# Ensure app is installed
bench --site your-site-name list-apps

# Should show: erpnext_amex

# If not listed, reinstall:
bench --site your-site-name install-app erpnext_amex
```

### DocTypes Not Showing

```bash
# Run migration
bench --site your-site-name migrate

# Check for errors in logs
bench --site your-site-name console
```

### Permission Errors

1. Check user has appropriate role
2. Go to Role Permission Manager
3. Verify roles have access to DocTypes
4. Clear cache and refresh browser

### CSS/JS Not Loading

```bash
# Build assets
bench build --app erpnext_amex

# Clear cache
bench --site your-site-name clear-cache

# Hard refresh browser (Cmd+Shift+R)
```

## 📦 What Gets Installed

**DocTypes:**
1. AMEX Import Batch
2. AMEX Transaction
3. AMEX Transaction Split (Child Table)
4. AMEX Vendor Classification Rule
5. AMEX Integration Settings (Single)
6. Fraud Report

**Pages:**
- AMEX Transaction Review

**Reports:**
- AMEX Import Status
- Unclassified Transactions

**Roles:**
- AMEX Transaction Manager
- AMEX Transaction Approver

**Module:**
- AMEX Integration (appears in module list)

## 🎯 Post-Installation Setup

### 1. Create AMEX Liability Account (if not exists)

1. Go to Chart of Accounts
2. Create new account:
   - Account Name: "AMEX Card Payable"
   - Account Type: Liability
   - Parent: Current Liabilities

### 2. Create Expense Accounts (if needed)

Suggested accounts:
- Advertising - Online
- Travel Expenses
- Office Supplies
- Professional Fees
- Shipping and Freight
- Meals and Entertainment

### 3. Set Up Cost Center Hierarchy

Create your cost center structure:
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

### 4. Assign User Roles

1. Go to User List
2. For each user who will use the system:
   - Add role: AMEX Transaction Manager (or Approver)
   - Save

### 5. Optional: Add Slack User IDs

If using Slack integration:
1. Add custom field to User DocType: `slack_user_id`
2. Populate for each user
3. Configure Slack bot token in settings

## ✅ You're Ready!

Once installation is complete:
1. Upload your first CSV
2. Classify a few transactions to train the memory system
3. Review the workflow
4. Set up ML when ready

---

**Questions?** Refer to `IMPLEMENTATION_GUIDE.md` for detailed usage instructions.




