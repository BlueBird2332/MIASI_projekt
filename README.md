# pylintool

ANTLR-based Python linter and formatter. Built as a university project.

## Features

| Feature | Flag | Auto-fix |
|---|---|---|
| Whitespace: tabs → spaces, trailing WS, excess blank lines | *(always on)* | `--fix` |
| Type checking (delegates to mypy) | `--typecheck` | — |
| Line too long | `--heuristics` | — |
| Function too long | `--heuristics` | — |
| Missing docstrings | `--heuristics` | — |
| Missing type annotations | `--heuristics` | — |
| Too many function arguments | `--heuristics` | — |
| File too long | `--heuristics` | — |

## Prerequisites

- **Python 3.11+**
- **Java 11+** (needed only once, to generate the ANTLR parser)
- **[uv](https://docs.astral.sh/uv/)** (recommended package manager)

Install uv if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh    # macOS / Linux / WSL
```

## Quick start

```bash
git clone <your-repo-url>
cd pylintool

# one command — installs Python, deps, and generates the ANTLR parser
make setup
```

That's it. `make setup` runs `uv sync --all-extras` then `make generate`.

## Usage

```bash
# Lint a single file (whitespace only)
pylintool path/to/file.py

# Lint a whole directory
pylintool src/

# Auto-fix whitespace issues in-place
pylintool src/ --fix

# Enable type checking
pylintool src/ --typecheck

# Enable code-quality heuristics
pylintool src/ --heuristics

# Everything at once
pylintool src/ --all

# CI mode: exit 1 if any issue found
pylintool src/ --check

# Custom thresholds
pylintool src/ --heuristics --max-line-length 80 --max-function-lines 30
```

## Development

```bash
# Run tests
make test

# Tests with coverage
make test-cov

# Regenerate parser after editing .g4 files
make generate

# Lint pylintool's own source
make lint
```

## Project structure

```
pylintool/
├── src/pylintool/
│   ├── grammar/              # ANTLR .g4 grammar files (source of truth)
│   │   ├── PyWhitespaceLexer.g4
│   │   └── PyWhitespaceParser.g4
│   ├── generated/            # ANTLR output (git-ignored, regenerated)
│   ├── checkers/
│   │   ├── whitespace.py     # ANTLR listener — whitespace analysis + fix
│   │   ├── typecheck.py      # Delegates to mypy
│   │   └── heuristics.py     # Code-quality metrics via regex
│   ├── cli.py                # Click CLI entry point
│   ├── models.py             # Shared Issue / FileResult types
│   └── scanner.py            # File/dir discovery
├── tests/
├── scripts/
│   └── generate_parser.py    # Cross-platform ANTLR wrapper
├── Makefile
├── pyproject.toml
├── .python-version
├── .gitattributes
└── .gitignore
```

## How ANTLR is used

The ANTLR grammar (`PyWhitespaceLexer.g4` + `PyWhitespaceParser.g4`) tokenises
Python source while **keeping whitespace as visible tokens** instead of skipping
it. The parser groups tokens into lines with explicit `leading_ws` and
`trailing_ws` rules. A `ParseTreeWalker` with a custom listener then walks the
tree and reports issues.

The heuristics checker uses regex on raw source (function/class structure) because
full Python parsing via ANTLR's official Python3 grammar is complex and
unnecessary for line-level metrics.

## Architecture decisions

- **uv** for reproducible environments — no Docker needed since the team is on
  WSL + macOS + Linux.
- **ANTLR version pinning**: both the tool (`antlr4-tools`) and the runtime
  (`antlr4-python3-runtime`) must match. The default is **4.11.1** but you can
  use any version as long as tool and runtime agree — update
  `pyproject.toml` accordingly.
- Generated files are **git-ignored** and regenerated via `make generate`.
- Type checking delegates to **mypy** rather than reimplementing it.
