"""Whitespace checker — ANTLR-based analysis and auto-fix.

Uses the PyWhitespaceParser parse tree to detect:
- Tab indentation / mixed indentation
- Trailing whitespace
- Excess consecutive blank lines (>2)
- Non-standard indent width
- Missing final newline

Also provides a ``fix_source`` function that rewrites the source.
"""

from __future__ import annotations

from pathlib import Path

from antlr4 import CommonTokenStream, InputStream, ParseTreeWalker

from pylintool.generated.PyWhitespaceLexer import PyWhitespaceLexer
from pylintool.generated.PyWhitespaceParser import PyWhitespaceParser
from pylintool.generated.PyWhitespaceParserListener import PyWhitespaceParserListener
from pylintool.models import FileResult, Issue, IssueCode, Severity


# ── Listener ──────────────────────────────────────────────────────


class _WhitespaceListener(PyWhitespaceParserListener):
    """Collects whitespace issues while walking the parse tree."""

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.issues: list[Issue] = []
        self._line = 1
        self._consecutive_blanks = 0

    # blank line ───────────────────────────────────────────────────

    def enterBlankLine(self, ctx: PyWhitespaceParser.BlankLineContext) -> None:
        self._consecutive_blanks += 1
        if self._consecutive_blanks > 2:
            self.issues.append(Issue(
                code=IssueCode.W004_EXCESS_BLANK_LINES,
                severity=Severity.WARNING,
                filepath=self.filepath,
                line=self._line,
                col=0,
                message="More than 2 consecutive blank lines",
            ))
        self._line += 1

    # content line ─────────────────────────────────────────────────

    def enterContentLine(self, ctx: PyWhitespaceParser.ContentLineContext) -> None:
        self._consecutive_blanks = 0
        self._check_leading(ctx)
        self._check_trailing(ctx)
        self._line += 1

    def enterLastLine(self, ctx: PyWhitespaceParser.LastLineContext) -> None:
        self._consecutive_blanks = 0
        self._check_leading(ctx)
        self._check_trailing(ctx)
        # No increment — this is the final line.

    # helpers ──────────────────────────────────────────────────────

    def _check_leading(self, ctx) -> None:
        ws_ctx = ctx.leading_ws()
        if ws_ctx is None:
            return

        text: str = ws_ctx.getText()
        has_tab = "\t" in text
        has_space = " " in text

        if has_tab and has_space:
            self.issues.append(Issue(
                code=IssueCode.W002_MIXED_INDENTATION,
                severity=Severity.ERROR,
                filepath=self.filepath,
                line=self._line,
                col=0,
                message="Mixed tabs and spaces in indentation",
            ))
        elif has_tab:
            self.issues.append(Issue(
                code=IssueCode.W001_TAB_INDENTATION,
                severity=Severity.ERROR,
                filepath=self.filepath,
                line=self._line,
                col=0,
                message="Tab used for indentation (use 4 spaces)",
            ))

        normalised = text.expandtabs(4)
        if len(normalised) % 4 != 0:
            self.issues.append(Issue(
                code=IssueCode.W006_WRONG_INDENT_SIZE,
                severity=Severity.WARNING,
                filepath=self.filepath,
                line=self._line,
                col=0,
                message=f"Indentation is {len(normalised)} spaces (not a multiple of 4)",
            ))

    def _check_trailing(self, ctx) -> None:
        ws_ctx = ctx.trailing_ws()
        if ws_ctx is None:
            return
        self.issues.append(Issue(
            code=IssueCode.W003_TRAILING_WHITESPACE,
            severity=Severity.WARNING,
            filepath=self.filepath,
            line=self._line,
            col=ws_ctx.start.column,
            message="Trailing whitespace",
        ))


# ── Public API ────────────────────────────────────────────────────


def check_whitespace(filepath: Path, source: str) -> list[Issue]:
    """Parse *source* with ANTLR and return whitespace issues."""
    input_stream = InputStream(source)
    lexer = PyWhitespaceLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = PyWhitespaceParser(tokens)

    tree = parser.file_input()

    listener = _WhitespaceListener(filepath)
    ParseTreeWalker().walk(listener, tree)

    # Token-stream trailing whitespace check.
    # The grammar may greedily consume trailing spaces into line_content,
    # so we scan the raw token stream for WS immediately before NEWLINE/EOF.
    tokens.fill()
    all_tokens = tokens.tokens
    for i, tok in enumerate(all_tokens):
        if tok.type == PyWhitespaceLexer.WS:
            next_type = all_tokens[i + 1].type if i + 1 < len(all_tokens) else -1
            if next_type in (PyWhitespaceLexer.NEWLINE, PyWhitespaceParser.EOF):
                listener.issues.append(Issue(
                    code=IssueCode.W003_TRAILING_WHITESPACE,
                    severity=Severity.WARNING,
                    filepath=filepath,
                    line=tok.line,
                    col=tok.column,
                    message="Trailing whitespace",
                ))

    # Check final newline (cannot be detected from the parse tree alone).
    if source and not source.endswith("\n"):
        listener.issues.append(Issue(
            code=IssueCode.W007_NO_NEWLINE_AT_EOF,
            severity=Severity.WARNING,
            filepath=filepath,
            line=source.count("\n") + 1,
            col=0,
            message="No newline at end of file",
        ))

    return listener.issues


def fix_source(source: str) -> str:
    """Return a cleaned-up copy of *source*.

    Fixes applied
    -------------
    1. Tabs → 4 spaces
    2. Trailing whitespace removed
    3. Consecutive blank lines capped at 2
    4. Exactly one newline at EOF
    """
    lines = source.split("\n")
    fixed: list[str] = []
    consecutive_blank = 0

    for raw in lines:
        line = raw.expandtabs(4).rstrip()

        if line == "":
            consecutive_blank += 1
            if consecutive_blank <= 2:
                fixed.append(line)
        else:
            consecutive_blank = 0
            fixed.append(line)

    # Trim trailing blank lines, then ensure exactly one final newline.
    while fixed and fixed[-1] == "":
        fixed.pop()

    text = "\n".join(fixed)
    return text + "\n" if text else ""
