from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from billing_date_utils import parse_ymd, today
from validation import normalize_whitespace


def add_placeholder(entry: ttk.Entry, placeholder_text: str) -> None:
    entry._placeholder_text = placeholder_text
    entry._has_placeholder = True

    def on_focus_in(_event=None):
        if hasattr(entry, "_has_placeholder") and entry._has_placeholder:
            entry.delete(0, tk.END)
            entry.configure(foreground="black")
            entry._has_placeholder = False

    def on_focus_out(_event=None):
        if not entry.get():
            entry.insert(0, entry._placeholder_text)
            entry.configure(foreground="gray")
            entry._has_placeholder = True

    entry.insert(0, placeholder_text)
    entry.configure(foreground="gray")
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)


def get_entry_value(entry: ttk.Entry) -> str:
    if hasattr(entry, "_has_placeholder") and entry._has_placeholder:
        return ""
    return entry.get()


def show_inline_error(parent: tk.Widget, message: str, row: int, column: int, columnspan: int = 1) -> tk.Label:
    error_label = tk.Label(
        parent,
        text="⚠️ " + message,
        background="#ffebee",
        foreground="#b00020",
        font=("Segoe UI", 11, "bold"),
        relief="solid",
        borderwidth=1,
        padx=8,
        pady=4,
    )
    error_label.grid(row=row, column=column, columnspan=columnspan, sticky="ew", padx=6, pady=2)
    parent.after(5000, lambda: error_label.grid_forget() if error_label.winfo_exists() else None)
    return error_label


def clear_inline_errors(parent: tk.Widget) -> None:
    for child in parent.winfo_children():
        if isinstance(child, tk.Label) and child.cget("background") == "#ffebee":
            child.grid_forget()


def create_date_input(
    parent: tk.Widget,
    width: int,
    default_iso: str | None = None,
    date_entry_cls: type | None = None,
):
    if date_entry_cls is not None:
        picker = date_entry_cls(parent, width=width, date_pattern="yyyy-mm-dd")
        if default_iso:
            parsed = parse_ymd(default_iso)
            if parsed:
                picker.set_date(parsed)
        else:
            picker.delete(0, tk.END)
        return picker

    fallback = ttk.Entry(parent, width=width)
    if default_iso:
        fallback.insert(0, default_iso)
    return fallback


def set_date_input_today(widget: tk.Widget, date_entry_cls: type | None = None) -> None:
    today_iso = today().isoformat()
    if date_entry_cls is not None and isinstance(widget, date_entry_cls):
        widget.set_date(today_iso)
        return
    try:
        widget.delete(0, tk.END)
        widget.insert(0, today_iso)
    except Exception:
        pass


def open_calendar_for_widget(parent_window: tk.Misc, widget: tk.Widget, date_entry_cls: type | None = None) -> None:
    try:
        if date_entry_cls is not None and isinstance(widget, date_entry_cls):
            try:
                widget.drop_down()
                return
            except Exception:
                pass

        try:
            import tkcalendar
            Calendar = tkcalendar.Calendar
        except Exception:
            messagebox.showinfo("Date Picker", "Install the 'tkcalendar' package to enable a calendar picker.")
            return

        top = tk.Toplevel(parent_window)
        top.transient(parent_window)
        top.grab_set()
        cal = Calendar(top, selectmode="day", date_pattern="yyyy-mm-dd")
        cal.pack(padx=8, pady=8)

        def _choose():
            sel = cal.get_date()
            try:
                widget.delete(0, tk.END)
                widget.insert(0, sel)
            except Exception:
                pass
            top.destroy()

        btn = ttk.Button(top, text="OK", command=_choose)
        btn.pack(pady=(0, 8))
    except Exception:
        return


def make_optional_date_clear_on_blur(widget: tk.Widget, date_entry_cls: type | None = None) -> None:
    def _on_focus_in(_event=None):
        try:
            widget._optional_prev_value = normalize_whitespace(widget.get())
        except Exception:
            widget._optional_prev_value = ""
        widget._optional_user_set = False

    def _mark_user_set(_event=None):
        widget._optional_user_set = True

    def _on_focus_out(_event=None):
        prev = normalize_whitespace(getattr(widget, "_optional_prev_value", ""))
        try:
            curr = normalize_whitespace(widget.get())
        except Exception:
            curr = ""

        if prev:
            return
        if getattr(widget, "_optional_user_set", False):
            return

        if curr == today().isoformat() or curr == prev:
            try:
                widget.delete(0, tk.END)
            except Exception:
                pass

    widget.bind("<FocusIn>", _on_focus_in, add="+")
    widget.bind("<FocusOut>", _on_focus_out, add="+")
    widget.bind("<KeyRelease>", _mark_user_set, add="+")
    if date_entry_cls is not None and isinstance(widget, date_entry_cls):
        widget.bind("<<DateEntrySelected>>", _mark_user_set, add="+")
