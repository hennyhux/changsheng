from __future__ import annotations

import re
from tkinter import ttk

from utils.validation import normalize_whitespace


def heading_text_without_sort_marker(text: str) -> str:
    return text.removesuffix(" ▲").removesuffix(" ▼")


def alphanum_key(value: str) -> tuple:
    normalized = normalize_whitespace(value or "")
    if not normalized:
        return (2,)

    numeric = normalized.replace("$", "").replace(",", "")
    if re.fullmatch(r"-?\d+(\.\d+)?", numeric):
        return (0, float(numeric))

    parts = re.split(r"(\d+)", normalized.lower())
    key_parts = []
    for part in parts:
        if part == "":
            continue
        if part.isdigit():
            key_parts.append((0, int(part)))
        else:
            key_parts.append((1, part))
    return (1, tuple(key_parts))


def sort_tree_column(
    tree: ttk.Treeview,
    col: str,
    tree_sort_state: dict[str, tuple[str, bool]],
    tree_heading_texts: dict[str, dict[str, str]],
):
    tree_key = str(tree)
    if tree_key not in tree_heading_texts:
        tree_heading_texts[tree_key] = {
            current_col: heading_text_without_sort_marker(str(tree.heading(current_col, "text")))
            for current_col in tree["columns"]
        }

    prev_col, prev_rev = tree_sort_state.get(tree_key, ("", False))
    reverse = (not prev_rev) if prev_col == col else False
    tree_sort_state[tree_key] = (col, reverse)

    items = list(tree.get_children(""))
    items.sort(key=lambda item_id: alphanum_key(tree.set(item_id, col)), reverse=reverse)
    for idx, item_id in enumerate(items):
        tree.move(item_id, "", idx)

    labels = tree_heading_texts[tree_key]
    for current_col in tree["columns"]:
        label = labels.get(current_col, current_col)
        if current_col == col:
            label += " ▼" if reverse else " ▲"
        tree.heading(current_col, text=label)


def reapply_tree_sort(
    tree: ttk.Treeview,
    tree_sort_state: dict[str, tuple[str, bool]],
    tree_heading_texts: dict[str, dict[str, str]],
):
    tree_key = str(tree)
    saved_col, saved_rev = tree_sort_state.get(tree_key, ("", False))
    if not saved_col or saved_col not in tree["columns"]:
        return

    items = list(tree.get_children(""))
    items.sort(key=lambda item_id: alphanum_key(tree.set(item_id, saved_col)), reverse=saved_rev)
    for idx, item_id in enumerate(items):
        tree.move(item_id, "", idx)

    labels = tree_heading_texts.get(tree_key, {})
    for current_col in tree["columns"]:
        label = labels.get(current_col, current_col)
        if current_col == saved_col:
            label += " ▼" if saved_rev else " ▲"
        tree.heading(current_col, text=label)
