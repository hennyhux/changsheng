from __future__ import annotations

from tkinter import ttk

from utils.tree_sort_utils import (
    alphanum_key,
    reapply_tree_sort,
    sort_tree_column,
)


class TreeSortMixin:
    def _select_tree_row_by_id(self, tree: ttk.Treeview, row_id: int) -> bool:
        target = str(row_id)
        for item_id in tree.get_children(""):
            values = tree.item(item_id, "values")
            if values and str(values[0]).strip() == target:
                tree.selection_set(item_id)
                tree.focus(item_id)
                tree.see(item_id)
                return True
        return False

    def _alphanum_key(self, value: str) -> tuple:
        return alphanum_key(value)

    def _sort_tree_column(self, tree: ttk.Treeview, col: str):
        if not hasattr(self, "_tree_sort_state"):
            self._tree_sort_state: dict[str, tuple[str, bool]] = {}
        if not hasattr(self, "_tree_heading_texts"):
            self._tree_heading_texts: dict[str, dict[str, str]] = {}
        sort_tree_column(tree, col, self._tree_sort_state, self._tree_heading_texts)

    def _reapply_tree_sort(self, tree: ttk.Treeview):
        if not hasattr(self, "_tree_sort_state"):
            return
        if not hasattr(self, "_tree_heading_texts"):
            self._tree_heading_texts = {}
        reapply_tree_sort(tree, self._tree_sort_state, self._tree_heading_texts)
