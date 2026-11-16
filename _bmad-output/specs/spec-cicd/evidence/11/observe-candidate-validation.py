"""Observe suite names/elapsed time only; never inspect process environments."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--report", default="candidate-validation-2.json", choices=("candidate-validation-2.json", "qualified-policy-candidate.json"))
parser.add_argument("--sha", default="f002539f6fbaddaa9b621a9cbf75a1263eee5dea")
args = parser.parse_args()
REPORT = HERE / args.report
PREFIX = "qualified-policy-validation-progress" if args.report == "qualified-policy-candidate.json" else "candidate-validation-2-progress"
names = {path.name for path in (ROOT / "tools/tests").glob("test_*.py")}
history = []
previous = None
deadline = time.monotonic() + 3600
while time.monotonic() < deadline:
    try:
        report = json.loads(REPORT.read_text())
    except (OSError, ValueError):
        time.sleep(2)
        continue
    candidate = report.get("candidate", report.get("head"))
    assert candidate == args.sha
    root_pid = report.get("validation_pid")
    processes = {}
    for directory in Path("/proc").iterdir():
        if not directory.name.isdigit():
            continue
        try:
            stat = (directory / "stat").read_text()
            fields = stat[stat.rfind(")") + 2:].split()
            processes[int(directory.name)] = (int(fields[1]), (directory / "cmdline").read_bytes().split(b"\0"))
        except (OSError, ValueError, IndexError):
            continue
    selected = {root_pid}
    while True:
        updated = selected | {pid for pid, (parent, _) in processes.items() if parent in selected}
        if updated == selected:
            break
        selected = updated
    suites = set()
    for pid in selected:
        if pid not in processes:
            continue
        for raw in processes[pid][1]:
            if raw and b"\n" not in raw:
                value = Path(raw.decode(errors="replace")).name
                if value in names:
                    suites.add(value)
    state = (tuple(sorted(suites)), report.get("validation_exit"), report.get("phase"))
    if state != previous and (suites or report.get("validation_exit") is not None):
        now = datetime.now(timezone.utc)
        value = {"observed_at": now.isoformat(), "candidate": candidate,
                 "elapsed_seconds": round((now - datetime.fromisoformat(report["validation_started_at"])).total_seconds(), 1),
                 "active_suites": sorted(suites), "exit": report.get("validation_exit"),
                 "verdict": report.get("verdict")}
        history.append(value)
        (HERE / (PREFIX + ".json")).write_text(json.dumps(history, indent=2) + "\n")
        print(json.dumps(value), flush=True)
        previous = state
    if report.get("validation_exit") is not None:
        raise SystemExit(0)
    time.sleep(5)
raise SystemExit("Bounded observation expired; no validation result inferred")
