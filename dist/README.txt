"""
CHANGSHENG - Truck Lot Tracker
Ready-to-Run Application Guide

Version: 2.0 (Executable)
Release Date: February 24, 2026
Status: Production Ready

═════════════════════════════════════════════════════════════════

OVERVIEW

Changsheng is a professional truck parking lot management system that helps you:

✓ Manage customers and their contact information
✓ Track truck inventory with license plates and details
✓ Create and manage service contracts
✓ Generate monthly invoices
✓ Record payments and track receivables
✓ Monitor overdue accounts
✓ Export data to Excel and CSV
✓ Generate PDF invoices

No programming experience needed. Everything is built-in and ready to use!

═════════════════════════════════════════════════════════════════

GETTING STARTED

1. INSTALLATION (First Time Only):

   - Copy the entire dist folder to your desired location
   - Or extract from installer if provided
   - Keep changsheng.exe and _internal folder together

2. RUNNING THE APPLICATION:

   - Windows 10/11: Double-click changsheng.exe
   - Or create a shortcut and place on Desktop
   - First run: Wait 5 seconds for database initialization
   - Subsequent runs: Instant startup

3. DATABASE:

   - Automatically created on first run
   - Location: C:\Users\[Your Username]\changsheng.db
   - Backed up automatically by the app
   - Your data persists between sessions

═════════════════════════════════════════════════════════════════

BASIC WORKFLOW

1. ADD CUSTOMERS
   → Customers tab → Add Customer button
   → Enter name, phone, company, notes
   → Click Save

2. ADD TRUCKS
   → Trucks tab → Add Truck button
   → Select customer, enter plate number, state
   → Optional: make, model, notes
   → Click Save

3. CREATE CONTRACTS
   → Contracts tab → Create Contract button
   → Select customer and truck/scope
   → Enter monthly rate and dates
   → Click Save

4. GENERATE INVOICES
   → Billing tab → Select month
   → Click "Generate Invoices for Month"
   → Invoices automatically created

5. RECORD PAYMENTS
   → Invoices tab → Select invoice → Record Payment
   → Or Billing tab → Record Payment for selected contract
   → Enter amount, date, payment method
   → Click Save

═════════════════════════════════════════════════════════════════

KEY FEATURES

📊 DASHBOARD
  • Quick overview of key metrics
  • Recent activity summary
  • At-a-glance business health

👥 CUSTOMERS
  • Store unlimited customers
  • Track phone, company, notes
  • View associated trucks and contracts
  • Edit or delete anytime

🚚 TRUCKS
  • Manage truck inventory
  • License plate (unique identifier)
  • State, make, model tracking
  • Link to customers

📝 CONTRACTS
  • Per-truck or customer-level billing
  • Monthly rate configuration
  • Active/inactive status
  • Start and end dates

💵 BILLING
  • Monthly invoice generation
  • Automatic calculation of amounts due
  • Payment method tracking
  • Outstanding balance tracking

🧾 INVOICES & PAYMENTS
  • Professional invoice display
  • Payment recording with dates and methods
  • Export to PDF
  • Payment history for each contract

⏰ OVERDUE REPORTS
  • Monitor unpaid invoices
  • See aging of receivables
  • Identify late customers
  • Filter by date range

📊 MONTHLY STATEMENT
  • Summary of billing period
  • Total billed vs. paid
  • Outstanding balances
  • Period analysis

═════════════════════════════════════════════════════════════════

LANGUAGE SUPPORT

The application supports bilingual interface:

English:  All UI in English (default)
中文:    All UI in Chinese (Simplified)

Switch language:
→ Top-right corner language selector
→ Choose "English" or "中文"
→ Interface updates immediately

═════════════════════════════════════════════════════════════════

DATA MANAGEMENT

BACKUP (Automatic)
  • Daily incremental backup
  • Backup folder in Documents
  • One-click restore functionality

EXPORT
  • Export customers and trucks to CSV
  • Export invoices and payments to Excel
  • Preserve formatting in generated files

IMPORT
  • Import customer and truck data from CSV
  • Bulk add customers at once
  • Validation before import

═════════════════════════════════════════════════════════════════

TROUBLESHOOTING

❌ APPLICATION WON'T START:
   ✓ Check system requirements (Windows 10/11, 64-bit)
   ✓ Ensure _internal folder is in same directory as .exe
   ✓ Try running as Administrator
   ✓ Check firewall/antivirus (may block on first run)

❌ DATABASE ERRORS:
   ✓ Ensure sufficient disk space (at least 1 GB free)
   ✓ Check write permissions on C:\Users folder
   ✓ Try running as Administrator
   ✓ Restart application if error persists

❌ SLOW PERFORMANCE:
   ✓ Close other applications
   ✓ Clear browser cache
   ✓ Restart computer
   ✓ Check available RAM (minimum 4 GB recommended)

❌ DATA NOT SAVING:
   ✓ Check notification for validation errors
   ✓ Verify all required fields are filled
   ✓ Ensure numeric fields contain only numbers
   ✓ Click Save button (not just Enter)

❌ PDF GENERATION FAILS:
   ✓ Ensure repor tlab is installed (built-in)
   ✓ Check disk space for PDF file
   ✓ Try saving to different location
   ✓ Restart application

═════════════════════════════════════════════════════════════════

SYSTEM REQUIREMENTS

Minimum:
  • Windows 10 or Windows 11
  • 64-bit processor
  • 2 GB RAM
  • 1 GB disk space (for app + data)

Recommended:
  • Windows 11
  • 8+ GB RAM
  • SSD (for faster response)
  • Internet connection (for export/share)

═════════════════════════════════════════════════════════════════

TIPS & TRICKS

💡 KEYBOARD SHORTCUTS:
   • Tab key: Move between fields
   • Enter: Submit form (same as clicking Save)
   • Ctrl+Z: Undo (if supported for current operation)
   • F5: Refresh current view

💡 QUICK ACTIONS:
   • Click column headers to sort tables
   • Use search to find customers/trucks quickly
   • Double-click row to view details
   • Right-click for additional options (if available)

💡 DATA ENTRY:
   • Use consistent formatting for consistency
   • Dates: Always use YYYY-MM-DD format
   • Plates: Format (e.g., "TX-ABC-1234")
   • Rates: Dollar amounts without $ symbol

💡 REPORTS:
   • Export month-end statements for accounting
   • Use "Overdue" tab for collections
   • Customer Ledger shows complete history
   • Monthly Statement for revenue tracking

═════════════════════════════════════════════════════════════════

CONTACTING SUPPORT

For issues or feature requests:

1. Check the Troubleshooting section above
2. Review the Help documentation (if available)
3. Check application log files:
   → Look in application folder for logs
   → Contains error details for debugging

4. Contact your system administrator or support team

═════════════════════════════════════════════════════════════════

PRIVACY & DATA SECURITY

Your Data:
  ✓ Stored locally on your computer
  ✓ Not transmitted to any server
  ✓ Only accessible by local users
  ✓ Backed up security by the application

Security:
  ✓ Database uses industry-standard SQLite
  ✓ Input validation prevents SQL injection
  ✓ No network vulnerabilities (local app)
  ✓ Regular backups protect against data loss

═════════════════════════════════════════════════════════════════

VERSION HISTORY

2.0 (Current - Feb 2026):
  ✓ Centralized error handling (no more crashes!)
  ✓ 385+ comprehensive unit tests
  ✓ Bilingual support (English/Chinese)
  ✓ Professional PDF generation
  ✓ Excel export with formatting
  ✓ Complete contract management
  ✓ Monthly statements and overdue reports
  ✓ Payment tracking with multiple methods
  ✓ Standalone executable (no Python needed)

═════════════════════════════════════════════════════════════════

GETTING HELP

Built-in Features:
  • Hover over fields for descriptions
  • Dialog boxes explain actions before confirmation
  • Status messages show what just happened
  • Error messages are clear and actionable

Online Help:
  • Application includes inline documentation
  • Data export includes field definitions
  • Customer ledger provides complete history

═════════════════════════════════════════════════════════════════

FREQUENTLY ASKED QUESTIONS

Q: Can I use this on multiple computers?
A: Yes, copy changsheng.exe and _internal folder to each computer.
   Each installation maintains its own database.

Q: Can I share data between computers?
A: Yes, use Backup/Restore or export to CSV for data transfer.

Q: How often should I backup?
A: Application auto-backs up daily. Manual backup before major changes.

Q: Can I delete old records?
A: Yes, use Delete buttons in respective tabs. Deleted records are permanent.

Q: Does this work with Excel?
A: Yes, export to Excel format for analysis and reporting.

Q: What if I lose my data?
A: Restore from backup using Backup/Restore feature. Backups are automatic.

Q: Can I customize reports?
A: Export data to Excel for custom report creation.

═════════════════════════════════════════════════════════════════

COPYRIGHT & LICENSE

Changsheng - Truck Lot Tracker
Copyright © 2026
All rights reserved.

Distribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:
  1. Redistributions must retain the above copyright notice
  2. This list of conditions follows all included documentation

═════════════════════════════════════════════════════════════════

THANK YOU for using Changsheng!

We're committed to providing a reliable, professional tool for 
truck lot management. Your feedback helps us improve continuously.

Questions or Suggestions? Contact your administrator or support team.

═════════════════════════════════════════════════════════════════

Application Status: ✅ Production Ready
Last Updated: February 24, 2026
No Known Issues
"""
