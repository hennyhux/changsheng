#!/usr/bin/env python3
"""Unit tests for config.py constants and patterns."""

import sys
from pathlib import Path
import re

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from core.config import (
    PHONE_PATTERN,
    PLATE_PATTERN,
    STATE_PATTERN,
    SEARCH_PLATE_PATTERN,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    TREE_ROW_HEIGHT,
    DB_PATH,
)


class TestConfigPatterns(unittest.TestCase):
    """Test regex patterns in config."""

    def test_phone_pattern_exists(self):
        """Test PHONE_PATTERN is defined."""
        assert PHONE_PATTERN is not None
        assert isinstance(PHONE_PATTERN, type(re.compile("")))

    def test_plate_pattern_exists(self):
        """Test PLATE_PATTERN is defined."""
        assert PLATE_PATTERN is not None
        assert isinstance(PLATE_PATTERN, type(re.compile("")))

    def test_state_pattern_exists(self):
        """Test STATE_PATTERN is defined."""
        assert STATE_PATTERN is not None
        assert isinstance(STATE_PATTERN, type(re.compile("")))

    def test_search_plate_pattern_exists(self):
        """Test SEARCH_PLATE_PATTERN is defined."""
        assert SEARCH_PLATE_PATTERN is not None
        assert isinstance(SEARCH_PLATE_PATTERN, type(re.compile("")))

    def test_phone_pattern_valid(self):
        """Test phone pattern matches valid phones."""
        valid_phones = [
            "555-123-4567",
            "(555) 123-4567",
            "5551234567",
            "555.123.4567",
        ]
        for phone in valid_phones:
            assert PHONE_PATTERN.fullmatch(phone), f"Pattern should match {phone}"

    def test_phone_pattern_invalid(self):
        """Test phone pattern rejects invalid phones."""
        invalid_phones = [
            "123",  # too short
            "12345678901234567890a",  # contains letter
            "",  # empty
        ]
        for phone in invalid_phones:
            assert not PHONE_PATTERN.fullmatch(phone), f"Pattern should not match {phone}"

    def test_plate_pattern_valid(self):
        """Test plate pattern matches valid plates."""
        valid_plates = [
            "ABC-1234",
            "AB",
            "ABCDEFGHIJKLMNO",  # 15 chars
            "ABC 123",
        ]
        for plate in valid_plates:
            assert PLATE_PATTERN.fullmatch(plate), f"Pattern should match {plate}"

    def test_plate_pattern_invalid(self):
        """Test plate pattern rejects invalid plates."""
        invalid_plates = [
            "A",  # too short
            "ABCDEFGHIJKLMNOP",  # too long (16 chars)
            "abc-1234",  # lowercase
            "ABC@123",  # invalid char
        ]
        for plate in invalid_plates:
            assert not PLATE_PATTERN.fullmatch(plate), f"Pattern should not match {plate}"

    def test_state_pattern_valid(self):
        """Test state pattern matches valid states."""
        valid_states = ["CA", "TX", "NY", "WA"]
        for state in valid_states:
            assert STATE_PATTERN.fullmatch(state), f"Pattern should match {state}"

    def test_state_pattern_invalid(self):
        """Test state pattern rejects invalid states."""
        invalid_states = [
            "C",  # too short
            "CAL",  # too long
            "ca",  # lowercase
            "C1",  # contains number
            "C-",  # contains symbol
        ]
        for state in invalid_states:
            assert not STATE_PATTERN.fullmatch(state), f"Pattern should not match {state}"

    def test_search_plate_pattern_valid(self):
        """Test search plate pattern."""
        valid = ["ABC", "ABC-123", "123", "ABC-123-XYZ"]
        for plate in valid:
            assert SEARCH_PLATE_PATTERN.fullmatch(plate), f"Pattern should match {plate}"

    def test_search_plate_pattern_allows_empty(self):
        """Test search plate pattern allows empty for searching."""
        assert SEARCH_PLATE_PATTERN.fullmatch(""), "Pattern should match empty for search"

    def test_search_plate_pattern_rejects_invalid_chars(self):
        """Test search plate pattern rejects invalid characters."""
        invalid = ["ABC@123", "ABC#456", "ABC$XYZ"]
        for plate in invalid:
            assert not SEARCH_PLATE_PATTERN.fullmatch(plate), f"Pattern should not match {plate}"


class TestConfigConstants(unittest.TestCase):
    """Test configuration constants."""

    def test_window_width_positive(self):
        """Test window width is positive."""
        assert WINDOW_WIDTH > 0

    def test_window_height_positive(self):
        """Test window height is positive."""
        assert WINDOW_HEIGHT > 0

    def test_tree_row_height_positive(self):
        """Test tree row height is positive."""
        assert TREE_ROW_HEIGHT > 0

    def test_window_dimensions_reasonable(self):
        """Test window dimensions are reasonable."""
        # Typical modern monitors are 1920x1080 or larger
        assert 800 <= WINDOW_WIDTH <= 3840, "Window width should be reasonable"
        assert 600 <= WINDOW_HEIGHT <= 2160, "Window height should be reasonable"

    def test_tree_row_height_reasonable(self):
        """Test tree row height is reasonable."""
        assert 20 <= TREE_ROW_HEIGHT <= 100, "Row height should be reasonable"

    def test_db_path_is_string(self):
        """Test database path is a string."""
        assert isinstance(DB_PATH, str)

    def test_db_path_non_empty(self):
        """Test database path is not empty."""
        assert len(DB_PATH) > 0


if __name__ == "__main__":
    unittest.main()
