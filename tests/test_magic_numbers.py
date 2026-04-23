"""Tests for H010 magic number detection."""

from pathlib import Path

from pylintool.checkers.heuristics import check_heuristics

FP = Path("test.py")


class TestMagicNumbers:
    def test_no_magic_number_ok(self):
        source = "x = 1\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H010" not in codes

    def test_allowed_numbers_ok(self):
        source = "if x == 0:\n    pass\nif y == 1:\n    pass\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H010" not in codes

    def test_magic_number_in_condition_flagged(self):
        source = "if x > 42:\n    pass\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H010" in codes

    def test_magic_number_in_expression_flagged(self):
        source = "result = x * 100\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H010" in codes

    def test_named_constant_not_flagged(self):
        source = "MAX_RETRIES = 42\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H010" not in codes

    def test_number_in_string_not_flagged(self):
        source = 'msg = "wartość to 42"\n'
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H010" not in codes

    def test_commented_number_not_flagged(self):
        source = "# limit wynosi 42\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H010" not in codes

    def test_correct_line_number_reported(self):
        source = "x = 1\ny = x * 99\nz = 3\n"
        issues = check_heuristics(FP, source)
        h010 = [i for i in issues if i.code.value == "H010"]
        assert len(h010) == 1
        assert h010[0].line == 2