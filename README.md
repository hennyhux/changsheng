# Changsheng Truck Lot Tracker

## Overview
Changsheng is a comprehensive truck lot management and billing system designed for small businesses. It provides robust features for tracking customers, contracts, trucks, invoices, payments, and overdue balances, all within a user-friendly desktop interface.

## Features
- Customer management: Add, edit, and search customers
- Truck tracking: Assign trucks to customers, manage plates and details
- Contract management: Create, edit, and track contracts with monthly rates
- Invoice generation: Automated PDF invoices with logo support
- Payment history: Record and view payments per contract
- Overdue tracking: Identify and manage overdue balances
- Data export: Export ledgers and histories for accounting
- Multi-language support: English and Chinese UI
- Robust error handling and validation

## Folder Structure
```
billing_date_utils.py
changsheng.py
config.py
contract_edit_dialog.py
customer_picker.py
database_service.py
error_handler.py
history_blackbox.txt
import_preview_dialog.py
invoice_generator.py
invoice_pdf.py
language_map.py
ledger_export.py
payment_history_dialog.py
payment_popup.py
ui_actions.py
ui_helpers.py
validation.py
app/
db_backups/
invoice/
tabs/
test_data/
tests/
```

## Setup & Installation
1. **Python Version**: Requires Python 3.10+
2. **Dependencies**:
   - Install required packages:
     ```bash
     pip install -r requirements.txt
     ```
   - Key dependencies: `tkinter`, `reportlab`, `openpyxl`, `sqlite3`
3. **Database**:
   - Uses SQLite for local storage. Database files are auto-created in `db_backups/`.
4. **Logo**:
   - Place your logo as `app/logo.png` for invoice branding.

## Running the Application
- Launch the main app:
  ```bash
  python changsheng.py
  ```
- For packaged executable:
  - Build with PyInstaller:
    ```bash
    pyinstaller changsheng.spec
    ```
  - Run the generated `.exe` in `build/changsheng/`

## Usage Guide
- **Billing Tab**: Manage invoices, payments, and contracts. Expand customers to view contract details. Tree stripping and highlighting improve visibility.
- **Monthly Statement**: View summary of balances and payments.
- **Overdue Tab**: Track overdue contracts and record payments.
- **Export**: Use ledger export for accounting.
- **Error Handling**: Errors are logged and shown in dialogs for easy troubleshooting.

## Testing
- Run all tests:
  ```bash
  python -m unittest discover tests
  ```
- Test files cover edge cases, performance, and validation.

## Troubleshooting
- **Logo not showing in invoice**: Ensure `app/logo.png` is included in build and accessible.
- **Database issues**: Check `db_backups/` for integrity and backups.
- **Missing dependencies**: Install all packages from `requirements.txt`.
- **UI quirks**: Tree stripping and expand/collapse highlighting are enabled for better visibility.

## Contributing
- Fork the repo, create a branch, and submit pull requests.
- Follow PEP8 and project conventions.

## License
MIT License

## Contact
For support or feature requests, contact the maintainer or open an issue.
