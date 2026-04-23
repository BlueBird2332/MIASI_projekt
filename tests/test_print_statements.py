"""Tests for H008 print() statement detection."""

from pathlib import Path

from pylintool.checkers.heuristics import check_heuristics

FP = Path("test.py")


class TestPrintStatements:
    def test_no_print_ok(self):
        source = "x = 1\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H008" not in codes

    def test_print_flagged(self):
        source = "print('hello')\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H008" in codes

    def test_indented_print_flagged(self):
        source = "def f():\n    print('debug')\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H008" in codes

    def test_commented_print_not_flagged(self):
        source = "# print('this is commented out')\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H008" not in codes

    def test_print_in_string_not_flagged(self):
        source = 'msg = "print(something)"\n'
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H008" not in codes

    def test_multiple_prints_all_reported(self):
        source = "print('a')\nprint('b')\nx = 1\n"
        issues = check_heuristics(FP, source)
        h008 = [i for i in issues if i.code.value == "H008"]
        assert len(h008) == 2

    def test_correct_line_number_reported(self):
        source = "x = 1\nprint('here')\nz = 3\n"
        issues = check_heuristics(FP, source)
        h008 = [i for i in issues if i.code.value == "H008"]
        assert len(h008) == 1
        assert h008[0].line == 2