"""Whitespace checker — ANTLR-based analysis and auto-fix.

Uses the PyWhitespaceParser parse tree to detect:
- Tab indentation / mixed indentation            (W001, W002)
- Trailing whitespace                            (W003)
- Excess consecutive blank lines (>2)            (W004)
- Inline tab characters used for alignment       (W005)
- Non-standard indent width                      (W006)
- Missing final newline                          (W007)
- Unexpected / redundant indentation             (W008)

Also provides a ``fix_source`` function that rewrites the source.
"""

from __future__ import annotations

from pathlib import Path

from antlr4 import CommonTokenStream, InputStream, ParseTreeWalker, Token

from pylintool.generated.PyWhitespaceLexer import PyWhitespaceLexer
from pylintool.generated.PyWhitespaceParser import PyWhitespaceParser
from pylintool.generated.PyWhitespaceParserListener import PyWhitespaceParserListener
from pylintool.models import Issue, IssueCode, Severity


# ── Parse-tree listener ───────────────────────────────────────────


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


# ── Token-stream analyses ─────────────────────────────────────────


def _check_inline_tabs(filepath: Path, tokens: CommonTokenStream) -> list[Issue]:
    """Detect tab characters used for inline alignment within a line (W005).

    Leading and trailing whitespace is already handled by W001/W002/W003;
    this function only flags tabs that appear *between* other tokens.
    """
    issues: list[Issue] = []
    all_toks = tokens.tokens

    for i, tok in enumerate(all_toks):
        if tok.type != PyWhitespaceLexer.WS or "\t" not in tok.text:
            continue
        if tok.column == 0:
            # Column-zero WS is leading indentation — already covered by W001/W002.
            continue

        # Determine whether this is trailing whitespace (only WS before NEWLINE/EOF).
        is_trailing = False
        for j in range(i + 1, len(all_toks)):
            next_tok = all_toks[j]
            if next_tok.line != tok.line:
                is_trailing = True
                break
            if next_tok.type in (PyWhitespaceLexer.NEWLINE, Token.EOF):
                is_trailing = True
                break
            if next_tok.type != PyWhitespaceLexer.WS:
                # A non-WS token follows on the same line → inline tab.
                break

        if not is_trailing:
            issues.append(Issue(
                code=IssueCode.W005_TAB_INLINE,
                severity=Severity.WARNING,
                filepath=filepath,
                line=tok.line,
                col=tok.column,
                message="Tab character used for alignment (use spaces)",
            ))

    return issues


def _check_indent_structure(filepath: Path, tokens: CommonTokenStream) -> list[Issue]:
    """Detect unexpected / redundant indentation (W008).

    Walks the token stream line by line and maintains an indentation stack.
    A line whose indentation exceeds the current stack top without a preceding
    block-opening statement (one whose last visible token is ``:``) is flagged.

    Continuation contexts (explicit ``\\`` or open brackets) are skipped.
    """
    _COLON = PyWhitespaceParser.COLON
    _LPAREN = PyWhitespaceParser.LPAREN
    _RPAREN = PyWhitespaceParser.RPAREN
    _LBRACK = PyWhitespaceParser.LBRACK
    _RBRACK = PyWhitespaceParser.RBRACK
    _LBRACE = PyWhitespaceParser.LBRACE
    _RBRACE = PyWhitespaceParser.RBRACE
    _WS = PyWhitespaceLexer.WS
    _NL = PyWhitespaceLexer.NEWLINE
    _CMT = PyWhitespaceLexer.COMMENT
    _LC = PyWhitespaceLexer.LINE_CONTINUATION

    # Group all tokens by 1-based line number.
    by_line: dict[int, list] = {}
    for tok in tokens.tokens:
        if tok.type == Token.EOF:
            continue
        by_line.setdefault(tok.line, []).append(tok)

    indent_stack: list[int] = [0]
    expecting_indent = False  # True after a line that ends with ':'
    in_continuation = False   # True when inside explicit or implicit continuation
    paren_depth = 0           # Net count of unclosed (, [, {
    issues: list[Issue] = []

    for lineno in sorted(by_line):
        toks = by_line[lineno]

        # Lines containing only whitespace / newlines are treated as blank.
        if not any(t.type not in (_WS, _NL) for t in toks):
            # Preserve current expecting_indent / paren_depth across blank lines.
            continue

        # Leading indentation (tabs expanded to 4 spaces).
        indent = len(toks[0].text.expandtabs(4)) if toks[0].type == _WS else 0

        # Only check indentation changes outside of continuation contexts.
        if not in_continuation and paren_depth == 0:
            top = indent_stack[-1]
            if indent > top:
                if not expecting_indent:
                    issues.append(Issue(
                        code=IssueCode.W008_OVER_INDENTED,
                        severity=Severity.WARNING,
                        filepath=filepath,
                        line=lineno,
                        col=0,
                        message=(
                            f"Unexpected indentation ({indent} spaces): "
                            "not preceded by a block-opening statement"
                        ),
                    ))
                indent_stack.append(indent)
            elif indent < top:
                # Dedent: pop stack levels until we match (or pass) the new level.
                while len(indent_stack) > 1 and indent_stack[-1] > indent:
                    indent_stack.pop()

        # ── Update state for the NEXT line ────────────────────────
        expecting_indent = False
        in_continuation = False

        # Block opener: last visible (non-WS, non-NL, non-comment) token is ':'.
        visible = [t for t in toks if t.type not in (_WS, _NL, _CMT)]
        if visible:
            expecting_indent = (visible[-1].type == _COLON)

        # Track explicit line-continuation and bracket depth.
        for tok in toks:
            if tok.type == _LC:
                in_continuation = True
            elif tok.type in (_LPAREN, _LBRACK, _LBRACE):
                paren_depth += 1
            elif tok.type in (_RPAREN, _RBRACK, _RBRACE):
                paren_depth = max(0, paren_depth - 1)

        # Implicit continuation while inside open brackets.
        if paren_depth > 0:
            in_continuation = True

    return issues


# ── Public API ────────────────────────────────────────────────────


def check_whitespace(filepath: Path, source: str) -> list[Issue]:
    """Parse *source* with ANTLR and return all whitespace/indentation issues."""
    input_stream = InputStream(source)
    lexer = PyWhitespaceLexer(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = PyWhitespaceParser(tokens)

    tree = parser.file_input()

    listener = _WhitespaceListener(filepath)
    ParseTreeWalker().walk(listener, tree)

    issues: list[Issue] = list(listener.issues)

    # Fill the token stream so the post-parse scans see every token.
    tokens.fill()
    all_tokens = tokens.tokens

    # ── W003: trailing whitespace (token-stream fallback) ─────────
    # The grammar may consume trailing spaces into line_content;
    # scan the raw token stream to catch what the listener missed.
    for i, tok in enumerate(all_tokens):
        if tok.type == PyWhitespaceLexer.WS:
            next_type = all_tokens[i + 1].type if i + 1 < len(all_tokens) else -1
            if next_type in (PyWhitespaceLexer.NEWLINE, PyWhitespaceParser.EOF):
                issues.append(Issue(
                    code=IssueCode.W003_TRAILING_WHITESPACE,
                    severity=Severity.WARNING,
                    filepath=filepath,
                    line=tok.line,
                    col=tok.column,
                    message="Trailing whitespace",
                ))

    # ── W005: inline tab characters ───────────────────────────────
    issues.extend(_check_inline_tabs(filepath, tokens))

    # ── W008: unexpected / redundant indentation ──────────────────
    issues.extend(_check_indent_structure(filepath, tokens))

    # ── W007: missing final newline ───────────────────────────────
    if source and not source.endswith("\n"):
        issues.append(Issue(
            code=IssueCode.W007_NO_NEWLINE_AT_EOF,
            severity=Severity.WARNING,
            filepath=filepath,
            line=source.count("\n") + 1,
            col=0,
            message="No newline at end of file",
        ))

    return issues


def fix_source(source: str) -> str:
    """Return a cleaned-up copy of *source*.

    Fixes applied
    -------------
    1. Tabs → 4 spaces everywhere (fixes W001, W002, W005)
    2. Trailing whitespace stripped (fixes W003)
    3. Consecutive blank lines capped at 2 (fixes W004)
    4. Exactly one newline at end of file (fixes W007)

    Not fixed automatically
    -----------------------
    W006 (wrong indent multiple) and W008 (over-indentation) require
    understanding block context and are left for the developer to resolve.
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
