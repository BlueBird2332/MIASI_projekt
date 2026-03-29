"""File discovery — recursively finds Python files in a path."""

from __future__ import annotations

from pathlib import Path

# Directories we never descend into.
_SKIP_DIRS = frozenset({
    "__pycache__", ".venv", "venv", ".env", "env",
    "node_modules", ".git", ".hg", ".svn",
    ".mypy_cache", ".pytest_cache", ".tox",
    "dist", "build", "*.egg-info",
})


def find_python_files(target: Path) -> list[Path]:
    """Return sorted list of .py files under *target*.

    Parameters
    ----------
    target:
        A single ``.py`` file **or** a directory to scan recursively.

    Raises
    ------
    FileNotFoundError
        If *target* does not exist.
    ValueError
        If *target* is a file but not a ``.py`` file.
    """
    target = target.resolve()

    if not target.exists():
        raise FileNotFoundError(f"Path does not exist: {target}")

    if target.is_file():
        if target.suffix != ".py":
            raise ValueError(f"Not a Python file: {target}")
        return [target]

    if not target.is_dir():
        raise ValueError(f"Not a file or directory: {target}")

    results: list[Path] = []
    for path in sorted(target.rglob("*.py")):
        # Skip hidden dirs and well-known junk dirs.
        parts = path.relative_to(target).parts
        if any(p.startswith(".") or p in _SKIP_DIRS for p in parts):
            continue
        results.append(path)

    return results
