#!/usr/bin/env python3
"""Print candidate reviewed coverage gaps from one duplicate-scan report.

Read-only and stdlib only. It reads a ``hexalith.duplicate-scan.v1`` report.json
and prints a complete ``hexalith.scan-coverage-gaps.v1`` document for the named
modules on stdout, for human review. It never writes
tools/scan-coverage-gaps.json or any other file: a reviewer copies the entries
that a recorded human decision covers.

Each located error with statement digests becomes one entry; identical errors
add to its ``occurrences``. Errors that module acceptance can never accept,
such as whole-file or coverage-limit diagnostics, errors outside Python sources
and diagnostics too long to record, are listed on stderr, as are run-level
errors, findings involving the module and an incomplete row. Exit 0 when every error of the named modules is
a candidate, 1 when any is not, and 2 for a usage error or an unreadable report.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


def acceptance_module():
    # Load the sibling by path, so this also runs under python3 -I, without
    # writing its bytecode cache.
    sys.dont_write_bytecode = True
    path = Path(__file__).resolve().with_name("nightly_acceptance.py")
    spec = importlib.util.spec_from_file_location("_scan_gap_acceptance", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


acceptance = acceptance_module()


class Refused(Exception):
    """The report or the selection cannot produce candidates."""


def candidates(report, modules, decision):
    """(document, notes): the candidate record for ``modules`` and what can never be accepted."""
    if not isinstance(report, dict) or report.get("schema") != acceptance.SCAN_SCHEMA:
        raise Refused("report is not " + acceptance.SCAN_SCHEMA)
    rows, errors, findings = report.get("modules"), report.get("errors"), report.get("findings")
    if (not isinstance(rows, list) or not isinstance(errors, list) or not isinstance(findings, list)
            or not all(isinstance(row, dict) and isinstance(row.get("module"), str) for row in rows)):
        raise Refused("report modules, findings or errors are malformed")
    gaps, notes = {}, []
    if errors:
        notes.append("run-level errors fail acceptance: " + acceptance.clean(errors[0], 150))
    for name in modules:
        matching = [row for row in rows if row["module"] == name]
        if len(matching) != 1:
            raise Refused(f"report has {len(matching)} rows for {acceptance.clean(name, 100)}")
        row = matching[0]
        involved = acceptance.involving(findings, name)
        if involved:
            notes.append(f"{name}: {len(involved)} cross-module duplicate findings fail acceptance")
        row_errors, sources = row.get("errors"), row.get("errorSources")
        if row.get("result") == "pass" and row_errors == []:
            continue
        if row.get("result") != "fail" or not isinstance(row_errors, list) or not row_errors:
            notes.append(f"{name}: row result {acceptance.clean(row.get('result'), 20)} does not match its errors")
            continue
        if not isinstance(sources, list) or len(sources) != len(row_errors):
            notes.append(f"{name}: row has no per-error source details")
            continue
        for error, source in zip(row_errors, sources):
            located, refusal = acceptance.located_error(error, source)
            if refusal:
                notes.append(f"{name}: error {refusal}: " + acceptance.clean(error, 1000))
                continue
            path, _, diagnostic, digest, callers = located
            diagnostic = acceptance.normalized_diagnostic(diagnostic)
            if (not acceptance.gap_path(path) or len(diagnostic) > acceptance.MAX_DIAGNOSTIC
                    or not acceptance.printable(diagnostic)):
                notes.append(f"{name}: error path or diagnostic cannot be recorded: " + acceptance.clean(error, 1000))
                continue
            key = (name, path, diagnostic, digest, callers)
            gaps[key] = gaps.get(key, 0) + 1
    document = {"schema": acceptance.GAPS_SCHEMA, "gaps": [
        {"module": module, "path": path, "diagnostic": diagnostic, "line_sha256": digest,
         "caller_sha256": list(callers), "occurrences": count, "decision": dict(decision)}
        for (module, path, diagnostic, digest, callers), count in sorted(gaps.items())]}
    # The printed document must pass the reader's own strict validation.
    acceptance.coverage_gaps(document)
    return document, notes


def main(argv=None, *, stdout=None, stderr=None):
    stdout, stderr = stdout or sys.stdout, stderr or sys.stderr
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("report", type=Path, help="duplicate-scan report.json to read")
    parser.add_argument("--module", action="append", required=True, help="module whose errors to list (repeatable)")
    parser.add_argument("--story", required=True, help="story key whose spec change log records the decision")
    parser.add_argument("--date", required=True, help="date of that change-log entry, YYYY-MM-DD")
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return error.code if isinstance(error.code, int) else 2
    decision = {"story": args.story, "date": args.date}
    if not acceptance.decision_reference(decision):
        print("scan gap candidates: --story must be a story key such as 15 or 28-7 and --date an ISO date",
              file=stderr)
        return 2
    try:
        data = args.report.read_bytes()
        report = acceptance.parse_json(data, acceptance.MAX_MEMBER["report.json"])
        document, notes = candidates(report, list(dict.fromkeys(args.module)), decision)
    except (OSError, ValueError, Refused) as error:
        print("scan gap candidates: " + acceptance.clean(error), file=stderr)
        return 2
    for note in notes:
        print("not a candidate: " + note, file=stderr)
    print(json.dumps(document, indent=2, ensure_ascii=True), file=stdout)
    return 1 if notes else 0


if __name__ == "__main__":
    raise SystemExit(main())
