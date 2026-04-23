"""Shared types used across all checkers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


class Severity(Enum):
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


class IssueCode(Enum):
    # ── Whitespace (W) ────────────────────────────────────────────
    W001_TAB_INDENTATION = "W001"
    W002_MIXED_INDENTATION = "W002"
    W003_TRAILING_WHITESPACE = "W003"
    W004_EXCESS_BLANK_LINES = "W004"
    W005_TAB_INLINE = "W005"
    W006_WRONG_INDENT_SIZE = "W006"
    W007_NO_NEWLINE_AT_EOF = "W007"

    # ── Type checking (T) ─────────────────────────────────────────
    T001_MYPY_ERROR = "T001"

    # ── Heuristics (H) ───────────────────────────────────────────
    H001_LINE_TOO_LONG = "H001"
    H002_FUNCTION_TOO_LONG = "H002"
    H003_MISSING_DOCSTRING = "H003"
    H004_MISSING_TYPE_ANNOTATION = "H004"
    H005_TOO_MANY_ARGUMENTS = "H005"
    H006_FILE_TOO_LONG = "H006"
    H007_TODO_COMMENT = "H007"
    H008_PRINT_STATEMENT = "H008"
    H009_BARE_EXCEPT = "H009"
    H010_MAGIC_NUMBER = "H010"


@dataclass
class Issue:
    code: IssueCode
    severity: Severity
    filepath: Path
    line: int
    col: int
    message: str


@dataclass
class FileResult:
    """Result of analysing a single file."""

    filepath: Path
    issues: list[Issue] = field(default_factory=list)
    fixed_source: str | None = None  # set only when --fix is active

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0
