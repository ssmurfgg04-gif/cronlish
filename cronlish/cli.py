"""Command-line interface: ``cronlish '*/5 * * * *'`` prints a description."""
from __future__ import annotations

import argparse
import sys

from cronlish import __version__
from cronlish.describe import DescribeError, describe
from cronlish.locale import STYLES, terse


def main(argv: "list[str] | None" = None) -> int:
    """Parse arguments, print the description, and return a process exit code.

    Exit codes: ``0`` on success; ``2`` when the expression cannot be
    described (DescribeError) or when argparse rejects the command line.
    """
    parser = argparse.ArgumentParser(
        prog="cronlish",
        description="Translate a cron expression into plain human language.",
    )
    parser.add_argument(
        "expression",
        nargs="+",
        help="five-field cron expression, quoted or not, e.g. '*/5 * * * *'",
    )
    parser.add_argument("--version", action="version",
                        version=f"cronlish {__version__}")
    parser.add_argument(
        "--locale-style",
        choices=STYLES,
        default=None,
        help="optional output style; currently only 'terse' (compact log-friendly)",
    )
    args = parser.parse_args(argv)
    expr = " ".join(args.expression)
    try:
        if args.locale_style == "terse":
            print(terse(expr))
        else:
            print(describe(expr))
    except DescribeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
