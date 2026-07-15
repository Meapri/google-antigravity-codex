#!/usr/bin/env python3
"""Print a secret-safe compatibility report for the official agy CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from google_antigravity_codex import cli  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print the full JSON report")
    parser.add_argument(
        "--require-tested",
        action="store_true",
        help="fail when the installed agy version differs from the exact tested version",
    )
    args = parser.parse_args()
    report = cli.status()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report["text"])
        for warning in report.get("warnings", []):
            print(f"warning: {warning}")
    if not report.get("success"):
        return 1
    if args.require_tested and not report.get("cli", {}).get("tested"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
