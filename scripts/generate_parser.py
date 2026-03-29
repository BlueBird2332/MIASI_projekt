#!/usr/bin/env python3
"""Generate ANTLR parser files from grammar.

Wraps the ANTLR jar/tool so teammates don't need to remember flags.

Approach:
1. Try ``antlr4`` CLI (installed via ``pip install antlr4-tools``).
2. Fall back to ``java -jar <antlr-*.jar>`` if a jar path is given via
   the ``ANTLR_JAR`` environment variable.

The lexer must be generated before the parser so that the ``.tokens``
file is available.
"""

from __future__ import annotations

import importlib.metadata
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRAMMAR_DIR = ROOT / "src" / "pylintool" / "grammar"
OUTPUT_DIR = ROOT / "src" / "pylintool" / "generated"

LEXER_G4 = "PyWhitespaceLexer.g4"
PARSER_G4 = "PyWhitespaceParser.g4"


def _pin_antlr_version() -> None:
    """Set ANTLR4_TOOLS_ANTLR_VERSION to match the installed runtime.

    antlr4-tools tries to query Sonatype for the latest version, which can
    fail in restricted network environments.  Pinning to the runtime version
    guarantees the tool JAR and the Python runtime are always in sync.
    """
    if os.environ.get("ANTLR4_TOOLS_ANTLR_VERSION"):
        return
    try:
        version = importlib.metadata.version("antlr4-python3-runtime")
        os.environ["ANTLR4_TOOLS_ANTLR_VERSION"] = version
    except importlib.metadata.PackageNotFoundError:
        pass  # let antlr4-tools handle it


def _antlr_cmd() -> list[str]:
    """Return the base command to invoke ANTLR."""
    jar = os.environ.get("ANTLR_JAR")
    if jar and Path(jar).exists():
        return ["java", "-jar", jar]

    if shutil.which("antlr4"):
        return ["antlr4"]

    print(
        "ERROR: Cannot find ANTLR.\n"
        "  Option A: pip install antlr4-tools   (needs Java 11+)\n"
        "  Option B: set ANTLR_JAR=/path/to/antlr-4.x-complete.jar",
        file=sys.stderr,
    )
    sys.exit(1)


def _run(cmd: list[str]) -> None:
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("FAILED", file=sys.stderr)
        sys.exit(result.returncode)


def _find_tokens_dir(tmp: Path) -> Path:
    """Find the directory containing .tokens files in the temp tree."""
    for tokens in tmp.rglob("*.tokens"):
        return tokens.parent
    return tmp


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = _antlr_cmd()

    # Use a temp dir to avoid ANTLR's nested path mirroring.
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Step 1 - Lexer (produces .tokens file)
        print("[1/2] Generating lexer ...")
        _run([
            *base,
            "-Dlanguage=Python3",
            "-o", str(tmp),
            str(GRAMMAR_DIR / LEXER_G4),
        ])

        # Step 2 - Parser (needs the lexer tokens)
        print("[2/2] Generating parser ...")
        tokens_dir = _find_tokens_dir(tmp)
        _run([
            *base,
            "-Dlanguage=Python3",
            "-visitor",
            "-listener",
            "-lib", str(tokens_dir),
            "-o", str(tmp),
            str(GRAMMAR_DIR / PARSER_G4),
        ])

        # Copy all generated .py files to the flat output dir.
        count = 0
        for py_file in tmp.rglob("*.py"):
            dest = OUTPUT_DIR / py_file.name
            shutil.copy2(py_file, dest)
            count += 1

    print(f"OK - {count} file(s) written to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
