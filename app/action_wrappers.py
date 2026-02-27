from __future__ import annotations

from datetime import date
from tkinter import messagebox

from core.config import TAG_COLORS, HISTORY_LOG_FILE
from core.app_logging import trace
from dialogs.payment_history_dialog import show_contract_payment_history
from invoicing.invoice_generator import build_invoice_groups, build_pdf_invoice_data
from invoicing.invoice_pdf import render_invoice_pdf, reportlab_available
from invoicing.ledger_export import export_customer_ledger_xlsx
from ui.ui_actions import (
    add_customer_action,
    add_truck_action,
    backup_database_action,
    create_contract_action,
    clear_invoice_customer_search_action,
    delete_customer_action,
    delete_contract_action,
    delete_truck_action,
    edit_contract_action,
    edit_selected_customer_action,
    export_customers_trucks_csv_action,
    import_customers_trucks_action,
    open_payment_form_for_contract_action,
    open_payment_form_window_action,
    record_payment_for_selected_contract_action,
    record_payment_for_selected_truck_action,
    restore_database_action,
    refresh_contracts_action,
    refresh_histories_action,
    refresh_invoices_action,
    refresh_overdue_action,
    refresh_statement_action,
    reset_contract_payments_action,
    show_contract_payment_history_action,
    show_customer_ledger_action,
    generate_customer_invoice_pdf_action,
    generate_customer_invoice_pdf_for_customer_id_action,
    generate_invoice_pdf_from_billing_selection_action,
    get_contract_outstanding_as_of_action,
    get_or_create_anchor_invoice_action,
    sync_selected_customer_to_forms_action,
    tab_has_unsaved_data_action,
    toggle_contract_action,
    refresh_customers_action,
    refresh_trucks_action,
)
from ui.ui_helpers import add_placeholder, get_entry_value, show_inline_error, clear_inline_errors
from utils.billing_date_utils import ym, parse_ym, parse_ymd, add_months
from utils.validation import normalize_whitespace


class ActionWrappersMixin:
    @trace
    def backup_database(self):
        backup_database_action(
            app=self,
            db=self.db,
            get_last_backup_dir_cb=self._get_last_backup_dir,
            set_last_backup_dir_cb=self._set_last_backup_dir,
            log_action_cb=self._log_action,
        )

    @trace
    def restore_database(self):
        restore_database_action(
            app=self,
            db=self.db,
            get_last_backup_dir_cb=self._get_last_backup_dir,
            set_last_backup_dir_cb=self._set_last_backup_dir,
            log_action_cb=self._log_action,
        )

    @trace
    def export_customers_trucks_csv(self):
        export_customers_trucks_csv_action(
            app=self,
            db=self.db,
            openpyxl_module=getattr(self, "_openpyxl_module", None),
            search_query=self.customer_search.get().strip(),
            show_invalid_cb=self._show_invalid,
            log_action_cb=self._log_action,
        )

    @trace
    def import_customers_trucks(self):
        import_customers_trucks_action(
            app=self,
            db=self.db,
            openpyxl_module=getattr(self, "_openpyxl_module", None),
            log_action_cb=self._log_action,
        )

    @trace
    def refresh_customers(self):
        refresh_customers_action(
            app=self,
            db=self.db,
            show_invalid_cb=self._show_invalid,
            row_stripe_tag_cb=self._row_stripe_tag,
            get_contract_outstanding_as_of_cb=self._get_contract_outstanding_as_of,
            outstanding_tag_from_amount_cb=self._outstanding_tag_from_amount,
        )
        self._update_view_trucks_button_state()

    @trace
    def add_customer(self):
        add_customer_action(
            app=self,
            db=self.db,
            get_entry_value_cb=get_entry_value,
            clear_inline_errors_cb=clear_inline_errors,
            show_inline_error_cb=show_inline_error,
            show_invalid_cb=self._show_invalid,
            add_placeholder_cb=add_placeholder,
            log_action_cb=self._log_action,
        )

    @trace
    def edit_selected_customer(self):
        edit_selected_customer_action(
            app=self,
            db=self.db,
            log_action_cb=self._log_action,
        )

    @trace
    def delete_customer(self):
        delete_customer_action(
            app=self,
            db=self.db,
            log_action_cb=self._log_action,
        )

    @trace
    def show_customer_ledger(self):
        tag_colors_with_palette = {**TAG_COLORS, "_palette": self._theme_palette}
        show_customer_ledger_action(
            app=self,
            db=self.db,
            tag_colors=tag_colors_with_palette,
            log_action_cb=self._log_action,
            export_customer_ledger_xlsx_cb=export_customer_ledger_xlsx,
        )

    @trace
    def record_payment_for_selected_truck(self):
        record_payment_for_selected_truck_action(
            app=self,
            db=self.db,
            open_payment_form_for_contract_cb=self._open_payment_form_for_contract,
        )

    @trace
    def refresh_trucks(self):
        refresh_trucks_action(
            app=self,
            db=self.db,
            show_invalid_cb=self._show_invalid,
            row_stripe_tag_cb=self._row_stripe_tag,
            get_contract_outstanding_as_of_cb=self._get_contract_outstanding_as_of,
            outstanding_tag_from_text_cb=self._outstanding_tag_from_text,
            truck_search_mode=getattr(self, "_truck_search_mode", "all"),
            customer_filter_id=getattr(self, "_truck_filter_customer_id", None),
        )

    @trace
    def add_truck(self):
        add_truck_action(
            app=self,
            db=self.db,
            get_entry_value_cb=get_entry_value,
            get_selected_customer_id_cb=self._get_selected_customer_id_from_combo,
            clear_inline_errors_cb=clear_inline_errors,
            show_inline_error_cb=show_inline_error,
            show_invalid_cb=self._show_invalid,
            add_placeholder_cb=add_placeholder,
            log_action_cb=self._log_action,
        )

    @trace
    def delete_truck(self):
        delete_truck_action(
            app=self,
            db=self.db,
            log_action_cb=self._log_action,
        )

    @trace
    def record_payment_for_selected_contract(self):
        record_payment_for_selected_contract_action(
            app=self,
            open_payment_form_for_contract_cb=self._open_payment_form_for_contract,
        )

    @trace
    def refresh_contracts(self, refresh_dependents: bool = True):
        refresh_contracts_action(
            app=self,
            db=self.db,
            status_badge_cb=self._status_badge,
            row_stripe_tag_cb=self._row_stripe_tag,
            get_contract_outstanding_as_of_cb=self._get_contract_outstanding_as_of,
            outstanding_tag_from_amount_cb=self._outstanding_tag_from_amount,
            customer_filter_id=getattr(self, "_truck_filter_customer_id", None),
            refresh_dependents=refresh_dependents,
        )

    @trace
    def create_contract(self):
        create_contract_action(
            app=self,
            db=self.db,
            get_selected_customer_id_cb=self._get_selected_customer_id_from_combo,
            get_selected_truck_id_cb=self._get_selected_truck_id_from_combo,
            get_entry_value_cb=get_entry_value,
            clear_inline_errors_cb=clear_inline_errors,
            show_inline_error_cb=show_inline_error,
            show_invalid_cb=self._show_invalid,
            log_action_cb=self._log_action,
        )

    @trace
    def toggle_contract(self):
        toggle_contract_action(
            app=self,
            db=self.db,
        )

    @trace
    def edit_contract(self):
        edit_contract_action(
            app=self,
            db=self.db,
            get_selected_customer_id_cb=self._get_selected_customer_id_from_combo,
            get_selected_truck_id_cb=self._get_selected_truck_id_from_combo,
            show_invalid_cb=self._show_invalid,
            log_action_cb=self._log_action,
        )

    @trace
    def delete_contract(self):
        delete_contract_action(
            app=self,
            db=self.db,
            log_action_cb=self._log_action,
        )

    @trace
    def show_contract_payment_history(self):
        show_contract_payment_history_action(
            app=self,
            db=self.db,
            get_contract_outstanding_as_of_cb=self._get_contract_outstanding_as_of,
            show_contract_payment_history_dialog_cb=show_contract_payment_history,
        )

    @trace
    def refresh_invoices(self):
        refresh_invoices_action(
            app=self,
            db=self.db,
            build_invoice_groups_cb=build_invoice_groups,
            invoice_group_label_cb=self._invoice_group_label,
            status_badge_cb=self._status_badge,
            refresh_invoice_parent_labels_cb=self._refresh_invoice_parent_labels,
            outstanding_tag_from_amount_cb=self._outstanding_tag_from_amount,
        )

    def _clear_invoice_customer_search(self):
        clear_invoice_customer_search_action(self)

    @trace
    def reset_contract_payments(self):
        reset_contract_payments_action(
            app=self,
            db=self.db,
            log_action_cb=self._log_action,
        )

    def _open_payment_form_window(self):
        open_payment_form_window_action(
            app=self,
            open_payment_form_for_contract_cb=self._open_payment_form_for_contract,
        )

    def _open_payment_form_for_contract(self, contract_id: int, plate_label: str | None = None, as_of_date: date | None = None):
        open_payment_form_for_contract_action(
            app=self,
            db=self.db,
            contract_id=contract_id,
            plate_label=plate_label,
            as_of_date=as_of_date,
            get_contract_outstanding_as_of_cb=self._get_contract_outstanding_as_of,
            get_or_create_anchor_invoice_cb=self._get_or_create_anchor_invoice,
            log_action_cb=self._log_action,
        )

    def _get_or_create_anchor_invoice(self, contract_id: int, as_of_date: date) -> int:
        return get_or_create_anchor_invoice_action(
            db=self.db,
            contract_id=contract_id,
            as_of_date=as_of_date,
        )

    def _get_contract_outstanding_as_of(self, contract_id: int, as_of_date: date) -> float:
        return get_contract_outstanding_as_of_action(
            db=self.db,
            contract_id=contract_id,
            as_of_date=as_of_date,
        )

    @trace
    def refresh_overdue(self):
        search_text = ""
        if hasattr(self, "overdue_search"):
            search_text = normalize_whitespace(self.overdue_search.get())
        refresh_overdue_action(
            app=self,
            db=self.db,
            parse_ymd_cb=parse_ymd,
            ym_cb=ym,
            row_stripe_tag_cb=self._row_stripe_tag,
            outstanding_tag_from_amount_cb=self._outstanding_tag_from_amount,
            search_query=search_text,
        )

    @trace
    def refresh_statement(self):
        refresh_statement_action(
            app=self,
            db=self.db,
            ym_cb=ym,
            parse_ym_cb=parse_ym,
            add_months_cb=add_months,
            parse_ymd_cb=parse_ymd,
        )

    def _sync_selected_customer_to_forms(self):
        sync_selected_customer_to_forms_action(
            app=self,
            set_selected_customer_cb=self._set_selected_customer,
        )

    @trace
    def refresh_histories(self):
        refresh_histories_action(
            app=self,
            ensure_history_log_exists_cb=self._ensure_history_log_exists,
            history_log_file=HISTORY_LOG_FILE,
        )

    def _generate_invoice_pdf_from_billing_selection(self):
        generate_invoice_pdf_from_billing_selection_action(
            app=self,
            db=self.db,
            generate_customer_invoice_pdf_for_customer_id_cb=self._generate_customer_invoice_pdf_for_customer_id,
        )

    @trace
    def generate_customer_invoice_pdf(self):
        generate_customer_invoice_pdf_action(
            app=self,
            generate_customer_invoice_pdf_for_customer_id_cb=self._generate_customer_invoice_pdf_for_customer_id,
        )

    def _generate_customer_invoice_pdf_for_customer_id(self, customer_id: int):
        generate_customer_invoice_pdf_for_customer_id_action(
            app=self,
            db=self.db,
            customer_id=customer_id,
            build_pdf_invoice_data_cb=build_pdf_invoice_data,
            reportlab_available_cb=reportlab_available,
            render_invoice_pdf_cb=render_invoice_pdf,
        )

    def _tab_has_unsaved_data(self, tab_str: str) -> bool:
        return tab_has_unsaved_data_action(
            app=self,
            tab_str=tab_str,
            get_entry_value_cb=get_entry_value,
        )
