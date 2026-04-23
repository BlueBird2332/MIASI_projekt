"""Tests for H009 bare except detection."""

from pathlib import Path

from pylintool.checkers.heuristics import check_heuristics

FP = Path("test.py")


class TestBareExcept:
    def test_no_except_ok(self):
        source = "x = 1\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H009" not in codes

    def test_typed_except_ok(self):
        source = "try:\n    pass\nexcept ValueError:\n    pass\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H009" not in codes

    def test_except_exception_ok(self):
        source = "try:\n    pass\nexcept Exception:\n    pass\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H009" not in codes

    def test_bare_except_flagged(self):
        source = "try:\n    pass\nexcept:\n    pass\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H009" in codes

    def test_indented_bare_except_flagged(self):
        source = "def f():\n    try:\n        pass\n    except:\n        pass\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H009" in codes

    def test_commented_bare_except_not_flagged(self):
        source = "# except:\n"
        issues = check_heuristics(FP, source)
        codes = {i.code.value for i in issues}
        assert "H009" not in codes

    def test_correct_line_number_reported(self):
        source = "try:\n    pass\nexcept:\n    pass\n"
        issues = check_heuristics(FP, source)
        h009 = [i for i in issues if i.code.value == "H009"]
        assert len(h009) == 1
        assert h009[0].line == 3