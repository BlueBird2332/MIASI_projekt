"""Tests for pylintool.checkers.typecheck."""

from pathlib import Path
from unittest.mock import patch

from pylintool.checkers.typecheck import check_types, _parse_mypy_line


FP = Path("test.py")


class TestParseMypyLine:
    def test_valid_error(self):
        line = "test.py:10:5: error: Incompatible types in assignment"
        issue = _parse_mypy_line(line, FP)
        assert issue is not None
        assert issue.line == 10
        assert issue.col == 5
        assert "Incompatible types" in issue.message

    def test_valid_note(self):
        line = "test.py:3:1: note: See docs for help"
        issue = _parse_mypy_line(line, FP)
        assert issue is not None

    def test_garbage_returns_none(self):
        assert _parse_mypy_line("not a valid line", FP) is None

    def test_incomplete_returns_none(self):
        assert _parse_mypy_line("test.py:10:", FP) is None


class TestCheckTypes:
    @patch("pylintool.checkers.typecheck.shutil.which", return_value=None)
    def test_mypy_not_installed(self, _mock):
        issues = check_types(FP)
        assert len(issues) == 1
        assert "not installed" in issues[0].message
