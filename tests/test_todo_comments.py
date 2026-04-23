"""Tests for H007 TODO/FIXME comment detection."""

from pathlib import Path

from pylintool.checkers.heuristics import check_heuristics

FP = Path("test.py")


class TestTodoComments:
    def test_no_todo_ok(self):
        source = "x = 1  # just a regular comment\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H007" not in codes

    def test_todo_flagged(self):
        source = "x = 1  # TODO: fix this\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H007" in codes

    def test_fixme_flagged(self):
        source = "x = 1  # FIXME: broken\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H007" in codes

    def test_case_insensitive(self):
        source = "x = 1  # todo: lowercase\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H007" in codes

    def test_todo_in_string_not_flagged(self):
        source = 'msg = "TODO: this is in a string"\n'
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H007" not in codes

    def test_multiple_todos_all_reported(self):
        source = "x = 1  # TODO: first\ny = 2  # FIXME: second\nz = 3\n"
        issues = check_heuristics(FP, source)
        h007 = [i for i in issues if i.code.value == "H007"]
        assert len(h007) == 2

    def test_correct_line_number_reported(self):
        source = "x = 1\ny = 2  # TODO: here\nz = 3\n"
        issues = check_heuristics(FP, source)
        h007 = [i for i in issues if i.code.value == "H007"]
        assert len(h007) == 1
        assert h007[0].line == 2