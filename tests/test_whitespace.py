"""Tests for pylintool.checkers.whitespace."""

import pytest

from pylintool.checkers.whitespace import fix_source


class TestFixSource:
    def test_tabs_to_spaces(self):
        result = fix_source("\tindented\n")
        assert result == "    indented\n"

    def test_nested_tabs(self):
        result = fix_source("\t\tdouble\n")
        assert result == "        double\n"

    def test_trailing_whitespace_removed(self):
        result = fix_source("hello   \n")
        assert result == "hello\n"

    def test_excess_blank_lines_capped(self):
        source = "a\n\n\n\n\nb\n"
        result = fix_source(source)
        assert result == "a\n\n\nb\n"

    def test_trailing_blanks_removed(self):
        result = fix_source("code\n\n\n\n")
        assert result == "code\n"

    def test_ensures_final_newline(self):
        result = fix_source("no newline at end")
        assert result == "no newline at end\n"

    def test_empty_input(self):
        assert fix_source("") == ""

    def test_only_whitespace(self):
        result = fix_source("   \n\t\n  \n")
        assert result == ""

    def test_mixed_indentation_fixed(self):
        result = fix_source("\t x = 1\n")
        assert "\t" not in result
        assert "x = 1\n" in result

    def test_preserves_content(self):
        source = '    x = "hello world"\n    return x\n'
        assert fix_source(source) == source

    def test_multiline_realistic(self):
        source = (
            "def foo():\n"
            "\tprint('hello')   \n"
            "\n"
            "\n"
            "\n"
            "\n"
            "\tprint('world')\n"
        )
        expected = (
            "def foo():\n"
            "    print('hello')\n"
            "\n"
            "\n"
            "    print('world')\n"
        )
        assert fix_source(source) == expected


class TestCheckWhitespace:
    """These tests require ANTLR-generated files.

    They are skipped if the parser hasn't been generated yet.
    """

    @pytest.fixture(autouse=True)
    def _skip_if_no_parser(self):
        try:
            from pylintool.checkers.whitespace import check_whitespace  # noqa: F401
            from pylintool.generated.PyWhitespaceLexer import PyWhitespaceLexer  # noqa: F401
        except ImportError:
            pytest.skip("ANTLR parser not generated yet — run: make generate")

    def test_clean_file_no_issues(self):
        from pylintool.checkers.whitespace import check_whitespace
        from pathlib import Path

        source = "def foo():\n    pass\n"
        issues = check_whitespace(Path("test.py"), source)
        assert len(issues) == 0

    def test_tab_detected(self):
        from pylintool.checkers.whitespace import check_whitespace
        from pathlib import Path

        source = "\tx = 1\n"
        issues = check_whitespace(Path("test.py"), source)
        codes = {i.code.value for i in issues}
        assert "W001" in codes

    def test_trailing_ws_detected(self):
        from pylintool.checkers.whitespace import check_whitespace
        from pathlib import Path

        source = "x = 1   \n"
        issues = check_whitespace(Path("test.py"), source)
        codes = {i.code.value for i in issues}
        assert "W003" in codes

    def test_excess_blanks_detected(self):
        from pylintool.checkers.whitespace import check_whitespace
        from pathlib import Path

        source = "a\n\n\n\nb\n"
        issues = check_whitespace(Path("test.py"), source)
        codes = {i.code.value for i in issues}
        assert "W004" in codes

    def test_no_final_newline_detected(self):
        from pylintool.checkers.whitespace import check_whitespace
        from pathlib import Path

        source = "x = 1"
        issues = check_whitespace(Path("test.py"), source)
        codes = {i.code.value for i in issues}
        assert "W007" in codes

    def test_inline_tab_detected(self):
        from pylintool.checkers.whitespace import check_whitespace
        from pathlib import Path

        source = "x\t= 1\n"
        issues = check_whitespace(Path("test.py"), source)
        codes = {i.code.value for i in issues}
        assert "W005" in codes

    def test_leading_tab_not_flagged_as_inline(self):
        """Tab used for indentation should be W001, not W005."""
        from pylintool.checkers.whitespace import check_whitespace
        from pathlib import Path

        source = "\tx = 1\n"
        issues = check_whitespace(Path("test.py"), source)
        codes = {i.code.value for i in issues}
        assert "W001" in codes
        assert "W005" not in codes

    def test_over_indented_without_block_opener(self):
        from pylintool.checkers.whitespace import check_whitespace
        from pathlib import Path

        source = "x = 1\n    y = 2\n"
        issues = check_whitespace(Path("test.py"), source)
        codes = {i.code.value for i in issues}
        assert "W008" in codes

    def test_correct_indentation_after_block_opener(self):
        from pylintool.checkers.whitespace import check_whitespace
        from pathlib import Path

        source = "def foo():\n    return 1\n"
        issues = check_whitespace(Path("test.py"), source)
        codes = {i.code.value for i in issues}
        assert "W008" not in codes

    def test_top_level_indentation_flagged(self):
        from pylintool.checkers.whitespace import check_whitespace
        from pathlib import Path

        source = "    x = 1\n"
        issues = check_whitespace(Path("test.py"), source)
        codes = {i.code.value for i in issues}
        assert "W008" in codes

    def test_continuation_not_flagged_as_over_indented(self):
        from pylintool.checkers.whitespace import check_whitespace
        from pathlib import Path

        source = "x = (\n    1 + 2\n)\n"
        issues = check_whitespace(Path("test.py"), source)
        codes = {i.code.value for i in issues}
        assert "W008" not in codes

    def test_nested_block_not_flagged(self):
        from pylintool.checkers.whitespace import check_whitespace
        from pathlib import Path

        source = "if True:\n    if True:\n        x = 1\n"
        issues = check_whitespace(Path("test.py"), source)
        codes = {i.code.value for i in issues}
        assert "W008" not in codes
