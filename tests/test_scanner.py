"""Tests for pylintool.scanner."""

from pathlib import Path

import pytest

from pylintool.scanner import find_python_files

FIXTURES = Path(__file__).parent / "fixtures"


def test_find_single_file():
    result = find_python_files(FIXTURES / "clean.py")
    assert len(result) == 1
    assert result[0].name == "clean.py"


def test_find_directory():
    result = find_python_files(FIXTURES)
    names = {p.name for p in result}
    assert "clean.py" in names
    assert "messy.py" in names


def test_nonexistent_raises():
    with pytest.raises(FileNotFoundError):
        find_python_files(Path("/nonexistent/path"))


def test_non_python_file_raises(tmp_path):
    txt = tmp_path / "readme.txt"
    txt.write_text("hello")
    with pytest.raises(ValueError, match="Not a Python file"):
        find_python_files(txt)


def test_empty_dir(tmp_path):
    result = find_python_files(tmp_path)
    assert result == []
