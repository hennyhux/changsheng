"""
ERROR HANDLING GUIDE - Changsheng Application
==============================================

## Overview

The Changsheng application implements **centralized error handling** to prevent crashes
and provide users with friendly error messages. All UI actions are protected by
decorators that catch unhandled exceptions and display them gracefully.

## Architecture

### Error Handler Module
Location: `error_handler.py`

Provides three main tools:

1. **@safe_ui_action** - For void UI actions
2. **@safe_ui_action_returning** - For actions that return values
3. **wrap_action_with_error_handling()** - For callback wrapping

### Benefits

✓ No hard crashes - all exceptions caught and handled
✓ User-friendly error messages displayed in dialogs
✓ Full exception logging for debugging
✓ Consistent error handling across all UI actions
✓ Easy to apply and maintain

## Usage

### Using the Decorator

```python
from error_handler import safe_ui_action

@safe_ui_action("Backup Database")
def backup_database_action(app, db):
    # Your code here - any exception is caught
    db.backup_to(file_path)
```

### For Functions That Return Values

```python
from error_handler import safe_ui_action_returning

@safe_ui_action_returning("Calculate Balance", return_on_error=0.0)
def get_contract_outstanding_as_of_action(db, contract_id, as_of_date):
    # Returns 0.0 if an exception occurs
    return db.calculate_balance(contract_id, as_of_date)
```

### For Callback Functions

```python
from error_handler import wrap_action_with_error_handling

def my_callback(data):
    # Your code here
    return process(data)

# Wrap it with error handling
safe_callback = wrap_action_with_error_handling(
    my_callback,
    "Process Data",
    show_error_dialog=True
)
```

## Protected UI Actions

All of these UI actions now have centralized error handling:

**Database Operations:**
- backup_database_action
- restore_database_action
- import_customers_trucks_action
- export_customers_trucks_csv_action

**CRUD Operations:**
- add_customer_action
- add_truck_action
- delete_customer_action
- delete_truck_action
- delete_contract_action
- edit_selected_customer_action

**Contract Management:**
- create_contract_action
- edit_contract_action
- toggle_contract_action
- record_payment_for_selected_contract_action
- record_payment_for_selected_truck_action

**Payment Operations:**
- open_payment_form_for_contract_action
- open_payment_form_window_action
- reset_contract_payments_action
- get_contract_outstanding_as_of_action
- get_or_create_anchor_invoice_action

**Display Operations:**
- refresh_customers_action
- refresh_trucks_action
- refresh_contracts_action
- refresh_invoices_action
- refresh_overdue_action
- refresh_statement_action
- refresh_histories_action
- show_customer_ledger_action
- show_contract_payment_history_action

**PDF Generation:**
- generate_customer_invoice_pdf_action
- generate_customer_invoice_pdf_for_customer_id_action
- generate_invoice_pdf_from_billing_selection_action

## How It Works

When an error occurs in a protected action:

1. **Exception is caught** - The decorator catches any unhandled exception
2. **Logged** - Full exception details logged with traceback for debugging
3. **User notified** - Error dialog shown with user-friendly message
4. **Gracefully handled** - Function returns None (or specified error value)
5. **App continues** - No crash, user can continue working

Example error message to user:
```
┌─────────────────────────────────────────┐
│ Error: Add Customer                     │
├─────────────────────────────────────────┤
│ The following error occurred while      │
│ adding a customer:                      │
│                                         │
│ Customer name cannot exceed 80 chars    │
│                                         │
│ Please try again or contact support     │
│ if the problem persists.                │
└─────────────────────────────────────────┘
```

## Test Coverage

The error handling system is tested with 25 unit tests covering:

✓ Normal function execution (no interference)
✓ Exception catching and handling
✓ Return value preservation
✓ Custom return values on error
✓ Error dialog display
✓ Logging of exceptions
✓ Multiple exception types
✓ Decorator chaining
✓ Database operation errors
✓ File operation errors

**Test file:** `tests/test_error_handler.py`

## Configuration

### Disable Error Dialogs (for background operations)

```python
@safe_ui_action("Background Task", show_error_dialog=False)
def background_task():
    # Only logs errors, doesn't show dialog
    pass
```

### Full Traceback Logging

```python
@safe_ui_action("Debug Action", log_full_traceback=True)
def debug_action():
    # Logs full exception traceback for debugging
    pass
```

## Adding Error Handling to New Functions

To protect a new UI action:

1. Import the decorator:
   ```python
   from error_handler import safe_ui_action
   ```

2. Add the decorator above the function:
   ```python
   @safe_ui_action("Descriptive Action Name")
   def my_new_action():
       pass
   ```

3. That's it! Any exceptions are now handled centrally

## What Gets Logged

All errors are logged with:
- Action name
- Error message
- Full exception traceback (for debugging)
- Timestamp
- Exception type

Example log entry:
```
ERROR:changsheng_app:Error in Add Customer: Required field 'name' is empty
Traceback (most recent call last):
  File "ui_actions.py", line 1284, in add_customer_action
    ...
```

## Limitations

- **KeyboardInterrupt** - Not caught (user-initiated app exit)
- **SystemExit** - Not caught (normal app shutdown)
- **Tkinter resource deletion** - May crash if widget references are invalid

## Best Practices

1. **Provide descriptive action names** - Used in error messages
2. **Keep try-except blocks for validation** - Still use for expected errors
3. **Don't suppress warnings** - The system logs them for debugging
4. **Test error paths** - Add tests for error scenarios
5. **Monitor logs** - Review application logs for recurring errors

## Troubleshooting

**Q: I don't see error messages when something fails**
A: Check if `show_error_dialog=False` is set. Also ensure Tkinter's messagebox is available.

**Q: Errors aren't being logged**
A: Verify the logger is configured correctly:
   ```python
   logger = logging.getLogger("changsheng_app")
   ```

**Q: The same error keeps occurring**
A: Check the application log file (if configured) to see the full traceback.

## Future Enhancements

Possible improvements to the error handling system:

- [ ] Automatic error recovery/retry logic
- [ ] Detailed error analytics and reporting
- [ ] Error context breadcrumbs
- [ ] Differentiation between user errors and system errors
- [ ] Notification system for critical errors
- [ ] Error report sending to support

---

**Last Updated:** 2026-02-24
**Test Coverage:** 25 tests (all passing)
**Protected Actions:** 36 UI functions
"""
