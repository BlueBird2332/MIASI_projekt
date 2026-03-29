"""Type checker — delegates to mypy and collects results.

This checker shells out to ``mypy`` and parses its machine-readable
output into our standard ``Issue`` format.  If mypy is not installed
it reports a single INFO-level issue and moves on.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from pylintool.models import Issue, IssueCode, Severity


def check_types(filepath: Path) -> list[Issue]:
    """Run mypy on *filepath* and return issues.

    If mypy is not installed the function returns an informational
    issue instead of raising.
    """
    mypy_bin = shutil.which("mypy")
    if mypy_bin is None:
        return [Issue(
            code=IssueCode.T001_MYPY_ERROR,
            severity=Severity.INFO,
            filepath=filepath,
            line=0,
            col=0,
            message="mypy is not installed — skipping type check "
                    "(install with: uv add mypy)",
        )]

    try:
        result = subprocess.run(
            [
                mypy_bin,
                "--no-color-output",
                "--no-error-summary",
                "--show-column-numbers",
                "--no-pretty",
                str(filepath),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return [Issue(
            code=IssueCode.T001_MYPY_ERROR,
            severity=Severity.WARNING,
            filepath=filepath,
            line=0,
            col=0,
            message="mypy timed out after 60 s",
        )]

    issues: list[Issue] = []
    for raw_line in result.stdout.splitlines():
        issue = _parse_mypy_line(raw_line, filepath)
        if issue is not None:
            issues.append(issue)

    return issues


def _parse_mypy_line(line: str, fallback_path: Path) -> Issue | None:
    """Parse a single mypy output line.

    Expected format::

        path.py:10:5: error: Incompatible types …
    """
    parts = line.split(":", maxsplit=4)
    if len(parts) < 5:
        return None

    _path, line_s, col_s, level_raw, msg = parts
    try:
        lineno = int(line_s)
        colno = int(col_s)
    except ValueError:
        return None

    level = level_raw.strip().lower()
    severity = Severity.ERROR if level == "error" else Severity.WARNING

    return Issue(
        code=IssueCode.T001_MYPY_ERROR,
        severity=severity,
        filepath=fallback_path,
        line=lineno,
        col=colno,
        message=f"[mypy] {msg.strip()}",
    )
