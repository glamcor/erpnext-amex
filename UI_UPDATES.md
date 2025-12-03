# UI Updates - AMEX Review Page

## Changes Made (Not Pushed to Git)

### 1. Dark Theme Support ✅
Created `amex_review.css` with theme-aware styling:
- Uses ERPNext's CSS variables (`--card-bg`, `--text-color`, `--border-color`, etc.)
- Automatically adapts to dark/light theme
- All colors, backgrounds, and borders respect the active theme

### 2. Cost Center Hierarchy Display ✅
**Python Backend (`amex_review.py`):**
- Updated `get_cost_center_list()` to return hierarchical data
- Uses ERPNext's nested set model (`lft`, `rgt` fields)
- Calculates indent level for each cost center
- Adds visual hierarchy with `display_name` like:
  ```
  Marketing
    ├─ Content Creation
    ├─ Paid Ads
      ├─ TikTok
      ├─ Meta
      ├─ Google
  ```

**JavaScript (`amex_review.js`):**
- Updated dropdown population to use `display_name`
- Applies to both single cost center and split cost center dropdowns

### 3. CSS Theme Variables Used
```css
var(--card-bg)           /* Card backgrounds */
var(--text-color)        /* Primary text */
var(--text-muted)        /* Labels, secondary text */
var(--border-color)      /* All borders */
var(--control-bg)        /* Form inputs */
var(--primary)           /* Primary buttons, links */
var(--bg-light)          /* Light backgrounds */
var(--highlight-color)   /* Hover states */
```

## Questions Answered

### 1. Expense Account Dropdown Empty?
**Issue:** The dropdown calls `get_account_list` which queries for accounts with `account_type='Expense'`.

**Possible causes:**
- No Expense accounts exist in Chart of Accounts
- Accounts are disabled
- API call is failing

**To debug:**
1. Go to: Accounting → Chart of Accounts
2. Check if you have accounts with Type = "Expense"
3. Check browser console for API errors

### 2. Category Field - From AMEX
**Source:** AMEX CSV file (Column: "Category")

**Examples:**
- "Business Services-Advertising Services"
- "Transportation-Taxis & Coach"  
- "Merchandise & Supplies-Office Supplies"

**Purpose:**
- Reference/audit trail
- Helps with pattern matching for classification
- Can be used for reporting
- No direct financial impact - just metadata

### 3. Multi-Select Behavior
**Current:** Right panel only applies to the clicked transaction

**Bulk Approve & Post:** Only posts already-classified transactions

**Enhancement Idea:** Add bulk classification feature where same vendor/account/cost center can be applied to multiple selected transactions at once.

### 4. Cost Center Hierarchy
**Fixed!** Now shows indented hierarchy instead of flat list.

**How it works:**
- ERPNext stores cost centers in a nested set tree
- `lft` and `rgt` fields define the hierarchy
- We calculate indent levels and add visual markers
- Dropdown shows the full tree structure

## Files Modified

1. **Created:** `erpnext_amex/amex_integration/page/amex_review/amex_review.css`
   - Full theme-aware stylesheet

2. **Modified:** `erpnext_amex/amex_integration/page/amex_review/amex_review.py`
   - `get_cost_center_list()` - Added hierarchy logic

3. **Modified:** `erpnext_amex/amex_integration/page/amex_review/amex_review.js`
   - Updated cost center dropdown population to use `display_name`
   - Applied to both single and split views

## Next Steps (User Requested)

### To Apply These Changes:
```bash
cd ~/frappe-bench
bench update --app erpnext_amex
bench --site your-site clear-cache
bench restart
```

### Additional Features to Consider:
1. **Bulk Classification** - Apply same settings to multiple transactions
2. **Better Expense Account Filtering** - Group by type or add search
3. **Smart Suggestions** - Show recent classifications for similar vendors
4. **Keyboard Shortcuts** - Quick navigation and actions

### Debugging Empty Expense Account Dropdown:
```sql
-- Run this in ERPNext console to check Expense accounts
SELECT name, account_name, disabled 
FROM `tabAccount` 
WHERE account_type = 'Expense' 
AND disabled = 0
LIMIT 10;
```

## Theme Preview
The UI will now automatically match your ERPNext theme:
- **Light Theme:** Clean white backgrounds, dark text
- **Dark Theme:** Dark backgrounds, light text, reduced contrast
- **All themes:** Proper hover states, focus states, and visual hierarchy

---

**Status:** Code updated locally, NOT pushed to Git (as requested)
**Date:** November 25, 2025




