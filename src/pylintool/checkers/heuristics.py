"""Code-quality heuristics checker.

Uses regex on raw source to detect:
- Lines exceeding a maximum length
- Functions that are too long (too many lines)
- Missing docstrings on functions / classes
- Missing type annotations on function parameters / return
- Functions with too many arguments
- Files that are too long

All thresholds are configurable via ``HeuristicsConfig``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pylintool.models import Issue, IssueCode, Severity


@dataclass
class HeuristicsConfig:
    max_line_length: int = 120
    max_function_lines: int = 50
    max_arguments: int = 6
    max_file_lines: int = 500
    require_docstrings: bool = True
    require_type_annotations: bool = True


_FUNC_RE = re.compile(
    r"^(?P<indent>[ ]*)(?:async\s+)?def\s+(?P<fname>[a-zA-Z_]\w*)\s*\((?P<params>[^)]*)\)",
)
_CLASS_RE = re.compile(
    r"^(?P<indent>[ ]*)class\s+(?P<cname>[a-zA-Z_]\w*)",
)
_DOCSTRING_RE = re.compile(
    r'^[ \t]*("""|\'\'\')',
)
_RETURN_ANNO_RE = re.compile(r"\)\s*->\s*\S")


def check_heuristics(
    filepath: Path,
    source: str,
    cfg: HeuristicsConfig | None = None,
) -> list[Issue]:
    """Analyse *source* and return heuristic issues."""
    cfg = cfg or HeuristicsConfig()
    issues: list[Issue] = []
    lines = source.splitlines()

    _check_line_length(issues, filepath, lines, cfg)
    _check_file_length(issues, filepath, lines, cfg)
    _check_functions_and_classes(issues, filepath, lines, cfg)
    _check_todo_comments(issues, filepath, lines)
    _check_print_statements(issues, filepath, lines)
    _check_bare_except(issues, filepath, lines)
    _check_magic_numbers(issues, filepath, lines)

    return issues


# ── Individual checks ─────────────────────────────────────────────


def _check_line_length(
    issues: list[Issue],
    fp: Path,
    lines: list[str],
    cfg: HeuristicsConfig,
) -> None:
    for i, line in enumerate(lines, start=1):
        length = len(line.expandtabs(4))
        if length > cfg.max_line_length:
            issues.append(Issue(
                code=IssueCode.H001_LINE_TOO_LONG,
                severity=Severity.WARNING,
                filepath=fp,
                line=i,
                col=cfg.max_line_length,
                message=f"Line is {length} chars (max {cfg.max_line_length})",
            ))


def _check_file_length(
    issues: list[Issue],
    fp: Path,
    lines: list[str],
    cfg: HeuristicsConfig,
) -> None:
    if len(lines) > cfg.max_file_lines:
        issues.append(Issue(
            code=IssueCode.H006_FILE_TOO_LONG,
            severity=Severity.INFO,
            filepath=fp,
            line=1,
            col=0,
            message=f"File has {len(lines)} lines (max {cfg.max_file_lines})",
        ))


def _check_functions_and_classes(
    issues: list[Issue],
    fp: Path,
    lines: list[str],
    cfg: HeuristicsConfig,
) -> None:
    i = 0
    while i < len(lines):
        func_m = _FUNC_RE.match(lines[i])
        if func_m:
            _analyse_function(issues, fp, lines, i, func_m, cfg)
            i += 1
            continue

        class_m = _CLASS_RE.match(lines[i])
        if class_m and cfg.require_docstrings:
            _check_class_docstring(issues, fp, lines, i, class_m)
            i += 1
            continue

        i += 1


def _analyse_function(
    issues: list[Issue],
    fp: Path,
    lines: list[str],
    start: int,
    match: re.Match,
    cfg: HeuristicsConfig,
) -> None:
    func_name = match.group("fname")
    indent = match.group("indent")
    params_raw = match.group("params").strip()
    lineno = start + 1

    # ── Too many arguments ────────────────────────────────────────
    if params_raw:
        params = [p.strip() for p in params_raw.split(",") if p.strip()]
        real_params = [
            p for p in params
            if p.split(":")[0].split("=")[0].strip() not in ("self", "cls")
        ]

        if len(real_params) > cfg.max_arguments:
            issues.append(Issue(
                code=IssueCode.H005_TOO_MANY_ARGUMENTS,
                severity=Severity.WARNING,
                filepath=fp,
                line=lineno,
                col=0,
                message=f"'{func_name}' has {len(real_params)} arguments (max {cfg.max_arguments})",
            ))

        # ── Missing type annotations ──────────────────────────────
        if cfg.require_type_annotations:
            for p in real_params:
                param_name = p.split("=")[0].split(":")[0].strip()
                if ":" not in p.split("=")[0]:
                    issues.append(Issue(
                        code=IssueCode.H004_MISSING_TYPE_ANNOTATION,
                        severity=Severity.INFO,
                        filepath=fp,
                        line=lineno,
                        col=0,
                        message=f"Parameter '{param_name}' in '{func_name}' has no type annotation",
                    ))

    # ── Missing return type annotation ────────────────────────────
    if cfg.require_type_annotations:
        full_def = lines[start]
        if not _RETURN_ANNO_RE.search(full_def):
            issues.append(Issue(
                code=IssueCode.H004_MISSING_TYPE_ANNOTATION,
                severity=Severity.INFO,
                filepath=fp,
                line=lineno,
                col=0,
                message=f"'{func_name}' has no return type annotation",
            ))

    # ── Function body length ──────────────────────────────────────
    body_start = start + 1
    body_end = _find_block_end(lines, body_start, indent)
    body_lines = body_end - body_start

    if body_lines > cfg.max_function_lines:
        issues.append(Issue(
            code=IssueCode.H002_FUNCTION_TOO_LONG,
            severity=Severity.WARNING,
            filepath=fp,
            line=lineno,
            col=0,
            message=f"'{func_name}' is {body_lines} lines (max {cfg.max_function_lines})",
        ))

    # ── Missing docstring ─────────────────────────────────────────
    if cfg.require_docstrings:
        j = body_start
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j >= len(lines) or not _DOCSTRING_RE.match(lines[j]):
            issues.append(Issue(
                code=IssueCode.H003_MISSING_DOCSTRING,
                severity=Severity.INFO,
                filepath=fp,
                line=lineno,
                col=0,
                message=f"'{func_name}' has no docstring",
            ))


def _check_class_docstring(
    issues: list[Issue],
    fp: Path,
    lines: list[str],
    start: int,
    match: re.Match,
) -> None:
    class_name = match.group("cname")
    j = start + 1
    while j < len(lines) and lines[j].strip() == "":
        j += 1
    if j >= len(lines) or not _DOCSTRING_RE.match(lines[j]):
        issues.append(Issue(
            code=IssueCode.H003_MISSING_DOCSTRING,
            severity=Severity.INFO,
            filepath=fp,
            line=start + 1,
            col=0,
            message=f"Class '{class_name}' has no docstring",
        ))


def _find_block_end(lines: list[str], body_start: int, parent_indent: str) -> int:
    """Return the line index past the end of a block."""
    parent_depth = len(parent_indent)
    i = body_start
    while i < len(lines):
        stripped = lines[i].lstrip()
        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue
        current_indent = len(lines[i]) - len(stripped)
        if current_indent <= parent_depth:
            break
        i += 1
    return i


_TODO_RE = re.compile(r"#.*\b(TODO|FIXME)\b", re.IGNORECASE)


def _check_todo_comments(
    issues: list[Issue],
    fp: Path,
    lines: list[str],
) -> None:
    """Report lines containing TODO or FIXME comments."""
    for i, line in enumerate(lines, start=1):
        m = _TODO_RE.search(line)
        if m:
            issues.append(Issue(
                code=IssueCode.H007_TODO_COMMENT,
                severity=Severity.INFO,
                filepath=fp,
                line=i,
                col=line.index("#"),
                message=f"Found '{m.group(1).upper()}' comment — consider resolving or tracking in an issue",
            ))

_PRINT_RE = re.compile(r"^\s*print\s*\(")


def _check_print_statements(
    issues: list[Issue],
    fp: Path,
    lines: list[str],
) -> None:
    """Report lines containing print() calls outside of comments."""
    for i, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if _PRINT_RE.match(line):
            issues.append(Issue(
                code=IssueCode.H008_PRINT_STATEMENT,
                severity=Severity.WARNING,
                filepath=fp,
                line=i,
                col=len(line) - len(stripped),
                message="Found 'print()' call — use logging instead",
            ))

_BARE_EXCEPT_RE = re.compile(r"^\s*except\s*:")


def _check_bare_except(
    issues: list[Issue],
    fp: Path,
    lines: list[str],
) -> None:
    """Report bare except: clauses that catch all exceptions silently."""
    for i, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if _BARE_EXCEPT_RE.match(line):
            issues.append(Issue(
                code=IssueCode.H009_BARE_EXCEPT,
                severity=Severity.WARNING,
                filepath=fp,
                line=i,
                col=len(line) - len(stripped),
                message="Found bare 'except:' — specify exception type, e.g. 'except Exception:'",
            ))

_MAGIC_NUMBER_RE = re.compile(r"(?<![=\w])\b(\d+\.?\d*)\b(?!\s*[=])")
_MAGIC_NUMBER_ALLOWED = {"0", "1", "2", "-1"}


def _check_magic_numbers(
    issues: list[Issue],
    fp: Path,
    lines: list[str],
) -> None:
    """Report numeric literals used directly in expressions (magic numbers)."""
    for i, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        # Pomiń linie z przypisaniem stałej (UPPER_CASE = liczba)
        if re.match(r"^\s*[A-Z_][A-Z0-9_]*\s*=", line):
            continue
        for m in _MAGIC_NUMBER_RE.finditer(line):
            value = m.group(1)
            if value in _MAGIC_NUMBER_ALLOWED:
                continue
            # Pomiń liczby wewnątrz stringów
            col = m.start()
            before = line[:col]
            if before.count('"') % 2 == 1 or before.count("'") % 2 == 1:
                continue
            issues.append(Issue(
                code=IssueCode.H010_MAGIC_NUMBER,
                severity=Severity.INFO,
                filepath=fp,
                line=i,
                col=col,
                message=f"Magic number '{value}' — assign to a named constant instead",
            ))