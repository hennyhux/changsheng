from __future__ import annotations

from tkinter import ttk


def make_searchable_combo(combo: ttk.Combobox):
    combo.configure(state="normal")
    combo._search_all_values = list(combo["values"])

    def _on_key(event):
        if event.keysym in ("Return", "KP_Enter", "Escape", "Tab", "Up", "Down", "Left", "Right"):
            return
        typed = combo.get().strip().lower()
        all_vals = getattr(combo, "_search_all_values", list(combo["values"]))
        filtered = [value for value in all_vals if typed in value.lower()] if typed else all_vals
        combo["values"] = filtered

    def _on_focus_out(_event):
        value = combo.get().strip()
        all_vals = getattr(combo, "_search_all_values", list(combo["values"]))
        combo["values"] = all_vals
        if value and value not in all_vals:
            combo.set("")

    combo.bind("<KeyRelease>", _on_key)
    combo.bind("<FocusOut>", _on_focus_out)
