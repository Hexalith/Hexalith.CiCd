#!/usr/bin/env python3
"""Read-only committed-source discovery with the actual locked trusted parser.

Run from the isolated CiCd worktree under run-with-temp. The owning repository
and module source are only read. An isolated Git index records the complete
candidate tree without staging or committing the owning worktree.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "tools"))
import scan


def main():
    destination = Path(sys.argv[1]).resolve()
    scratch = Path(os.environ["TMPDIR"])
    source = scan.rt.Git("/home/administrator/projects/hexalith/eventstore")
    revision = "d5902b78863b6920762d64c17b1276d95f2f9977"
    owning = scan.rt.Git(ROOT)
    baseline = owning.resolve("HEAD")
    changed = ("tools/scan_discovery.py", "tools/tests/test_scan.py")
    candidate = scan.rt.Git(ROOT, index=scratch / "candidate.index")
    candidate.run("read-tree", baseline)
    candidate.run("add", "--", *changed)
    tree = candidate.run("write-tree").decode().strip()
    result = {
        "cicdBaseline": baseline,
        "cicdBaselineTree": owning.resolve(baseline + "^{tree}"),
        "cicdCandidateTree": tree,
        "changedSources": {path: {"sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                                  "blob": candidate.items(tree)[path][2], "mode": candidate.items(tree)[path][0]}
                           for path in changed},
        "upstreamRevision": revision,
        "upstreamTree": source.resolve(revision + "^{tree}"),
        "python": platform.python_version(),
        "node": subprocess.check_output(["node", "--version"], text=True).strip(),
        "npm": subprocess.check_output(["npm", "--version"], text=True).strip(),
        "parser": scan.TYPESCRIPT_VERSION,
        "commands": ["Detector(committed CiCd baseline, private scratch)",
                     "Discovery(exact committed EventStore main, javascript_parser=detector.javascript).discover()"],
        "moduleCodeExecuted": False,
        "complete": False,
    }
    before = result["changedSources"]
    try:
        detector = scan.Detector(owning, baseline, scratch)
        files, errors = scan.Discovery(source, revision, javascript_parser=detector.javascript).discover()
        items = source.items(revision)
        result.update(complete=not errors, errors=errors,
                      files=[{"path": path, "mode": items[path][0], "blob": items[path][2],
                              "sha256": hashlib.sha256(row["text"].encode()).hexdigest()}
                             for path, row in sorted(files.items())])
        if any(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != row["sha256"]
               for path, row in before.items()) or owning.resolve("HEAD") != baseline:
            raise RuntimeError("owning source changed during discovery")
    except Exception as error:
        result.update(complete=False, failure=str(error))
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"complete": result["complete"], "files": len(result.get("files", [])),
                      "diagnostics": len(result.get("errors", [])), "failure": result.get("failure")}))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
