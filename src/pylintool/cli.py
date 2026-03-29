"""Command-line interface for pylintool."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from pylintool.models import FileResult, Severity
from pylintool.scanner import find_python_files


@click.command()
@click.argument("target", type=click.Path(exists=True, path_type=Path))
@click.option("--fix", is_flag=True, help="Auto-fix whitespace issues in-place.")
@click.option("--check", is_flag=True, help="Exit 1 if any issues found (CI mode).")
@click.option("--typecheck", is_flag=True, help="Run mypy type checking on each file.")
@click.option("--heuristics", is_flag=True, help="Enable code-quality heuristics.")
@click.option("--all", "all_checks", is_flag=True, help="Enable all optional checks.")
@click.option("--max-line-length", type=int, default=120, show_default=True,
              help="Maximum line length for heuristic check.")
@click.option("--max-function-lines", type=int, default=50, show_default=True,
              help="Maximum function body length.")
@click.option("--max-arguments", type=int, default=6, show_default=True,
              help="Maximum number of function arguments.")
@click.option("--max-file-lines", type=int, default=500, show_default=True,
              help="Maximum file length.")
@click.option("--quiet", "-q", is_flag=True, help="Only print summary.")
def main(
    target: Path,
    fix: bool,
    check: bool,
    typecheck: bool,
    heuristics: bool,
    all_checks: bool,
    max_line_length: int,
    max_function_lines: int,
    max_arguments: int,
    max_file_lines: int,
    quiet: bool,
) -> None:
    """Lint and fix Python files.

    TARGET is a .py file or a directory to scan recursively.

    \b
    By default only whitespace checks run and --fix is available.
    Add --typecheck, --heuristics, or --all for deeper analysis.
    """
    if all_checks:
        typecheck = True
        heuristics = True

    try:
        files = find_python_files(target)
    except (FileNotFoundError, ValueError) as exc:
        raise click.ClickException(str(exc))

    if not files:
        click.echo("No Python files found.")
        return

    # Lazy imports so we only load what's needed.
    from pylintool.checkers.whitespace import check_whitespace, fix_source

    heuristics_cfg = None
    if heuristics:
        from pylintool.checkers.heuristics import HeuristicsConfig
        heuristics_cfg = HeuristicsConfig(
            max_line_length=max_line_length,
            max_function_lines=max_function_lines,
            max_arguments=max_arguments,
            max_file_lines=max_file_lines,
        )

    results: list[FileResult] = []

    for filepath in files:
        source = filepath.read_text(encoding="utf-8")
        result = FileResult(filepath=filepath)

        # ── Whitespace (always on) ────────────────────────────────
        result.issues.extend(check_whitespace(filepath, source))

        if fix:
            result.fixed_source = fix_source(source)

        # ── Type checking (opt-in) ────────────────────────────────
        if typecheck:
            from pylintool.checkers.typecheck import check_types
            result.issues.extend(check_types(filepath))

        # ── Heuristics (opt-in) ───────────────────────────────────
        if heuristics and heuristics_cfg is not None:
            from pylintool.checkers.heuristics import check_heuristics
            result.issues.extend(check_heuristics(filepath, source, heuristics_cfg))

        results.append(result)

    # ── Write fixes ───────────────────────────────────────────────
    if fix:
        for r in results:
            if r.fixed_source is not None:
                r.filepath.write_text(r.fixed_source, encoding="utf-8")

    # ── Output ────────────────────────────────────────────────────
    total = 0
    files_with_issues = 0
    severity_colours = {
        Severity.ERROR: "red",
        Severity.WARNING: "yellow",
        Severity.INFO: "cyan",
    }

    for r in results:
        if not r.has_issues:
            continue
        files_with_issues += 1
        total += len(r.issues)

        if quiet:
            continue

        for issue in r.issues:
            colour = severity_colours.get(issue.severity, "white")
            click.echo(
                click.style(f"  {issue.code.value}", fg=colour, bold=True)
                + f" {r.filepath}:{issue.line}:{issue.col} "
                + issue.message
            )

    # ── Summary ───────────────────────────────────────────────────
    click.echo()
    if total == 0:
        click.secho("All clean!", fg="green", bold=True)
    else:
        verb = "fixed" if fix else "found"
        colour = "yellow" if fix else "red"
        click.secho(
            f"{total} issue(s) {verb} across {files_with_issues} file(s) "
            f"({len(files)} scanned).",
            fg=colour,
            bold=True,
        )

    if check and total > 0 and not fix:
        sys.exit(1)


if __name__ == "__main__":
    main()
