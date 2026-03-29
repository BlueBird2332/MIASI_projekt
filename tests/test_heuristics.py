"""Tests for pylintool.checkers.heuristics."""

from pathlib import Path

from pylintool.checkers.heuristics import HeuristicsConfig, check_heuristics


FP = Path("test.py")


class TestLineTooLong:
    def test_short_line_ok(self):
        issues = check_heuristics(FP, "x = 1\n")
        codes = {i.code.value for i in issues}
        assert "H001" not in codes

    def test_long_line_flagged(self):
        source = "x = " + "a" * 200 + "\n"
        issues = check_heuristics(FP, source, HeuristicsConfig(max_line_length=120))
        codes = {i.code.value for i in issues}
        assert "H001" in codes

    def test_custom_threshold(self):
        source = "x = " + "a" * 80 + "\n"
        issues = check_heuristics(FP, source, HeuristicsConfig(max_line_length=79))
        codes = {i.code.value for i in issues}
        assert "H001" in codes


class TestFunctionTooLong:
    def test_short_function_ok(self):
        source = "def f():\n    pass\n"
        issues = check_heuristics(FP, source, HeuristicsConfig(max_function_lines=50))
        codes = {i.code.value for i in issues}
        assert "H002" not in codes

    def test_long_function_flagged(self):
        body = "\n".join(f"    x{i} = {i}" for i in range(60))
        source = f"def f():\n{body}\n"
        issues = check_heuristics(FP, source, HeuristicsConfig(max_function_lines=50))
        codes = {i.code.value for i in issues}
        assert "H002" in codes


class TestMissingDocstring:
    def test_docstring_present_ok(self):
        source = 'def f():\n    """Does stuff."""\n    pass\n'
        issues = check_heuristics(FP, source)
        h003 = [i for i in issues if i.code.value == "H003" and "f" in i.message]
        assert len(h003) == 0

    def test_missing_docstring_flagged(self):
        source = "def f():\n    pass\n"
        issues = check_heuristics(FP, source)
        h003 = [i for i in issues if i.code.value == "H003" and "'f'" in i.message]
        assert len(h003) == 1

    def test_class_missing_docstring_flagged(self):
        source = "class Foo:\n    x = 1\n"
        issues = check_heuristics(FP, source)
        h003 = [i for i in issues if i.code.value == "H003" and "Foo" in i.message]
        assert len(h003) == 1


class TestMissingTypeAnnotation:
    def test_annotated_ok(self):
        source = "def f(x: int) -> str:\n    pass\n"
        issues = check_heuristics(FP, source)
        h004 = [i for i in issues if i.code.value == "H004"]
        assert len(h004) == 0

    def test_missing_param_annotation(self):
        source = "def f(x) -> str:\n    pass\n"
        issues = check_heuristics(FP, source)
        h004 = [i for i in issues if i.code.value == "H004" and "x" in i.message]
        assert len(h004) == 1

    def test_missing_return_annotation(self):
        source = "def f(x: int):\n    pass\n"
        issues = check_heuristics(FP, source)
        h004 = [i for i in issues if i.code.value == "H004" and "return" in i.message]
        assert len(h004) == 1

    def test_self_not_counted(self):
        source = "def f(self, x: int) -> None:\n    pass\n"
        issues = check_heuristics(FP, source)
        h004 = [i for i in issues if i.code.value == "H004"]
        assert len(h004) == 0


class TestTooManyArguments:
    def test_few_args_ok(self):
        source = "def f(a: int, b: int) -> None:\n    pass\n"
        issues = check_heuristics(FP, source, HeuristicsConfig(max_arguments=6))
        codes = {i.code.value for i in issues}
        assert "H005" not in codes

    def test_many_args_flagged(self):
        source = "def f(a, b, c, d, e, f, g, h) -> None:\n    pass\n"
        issues = check_heuristics(FP, source, HeuristicsConfig(max_arguments=6))
        codes = {i.code.value for i in issues}
        assert "H005" in codes


class TestFileTooLong:
    def test_short_file_ok(self):
        source = "x = 1\n" * 100
        issues = check_heuristics(FP, source, HeuristicsConfig(max_file_lines=500))
        codes = {i.code.value for i in issues}
        assert "H006" not in codes

    def test_long_file_flagged(self):
        source = "x = 1\n" * 600
        issues = check_heuristics(FP, source, HeuristicsConfig(max_file_lines=500))
        codes = {i.code.value for i in issues}
        assert "H006" in codes
