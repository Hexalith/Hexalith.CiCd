#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Re-run saved discovery against exact Git objects; never run Folders code."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

EVIDENCE = Path(__file__).resolve().parent
CICD = EVIDENCE.parents[4]
OUTPUT = EVIDENCE / "powershell-discovery"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--folders", type=Path, required=True, help="Local Folders Git object source")
args = parser.parse_args()
scratch = Path(os.environ["TMPDIR"])
OUTPUT.mkdir(exist_ok=True)


def git(root, *arguments):
    return subprocess.check_output(["git", "-C", str(root), *arguments], text=True).strip()


def save(name, data):
    (OUTPUT / name).write_text(json.dumps(data, indent=2) + "\n")


# Execute the saved minimal reproduction unchanged in a disposable CiCd copy.
copy = scratch / "cicd"
subprocess.run(["git", "clone", "--quiet", "--shared", "--no-recurse-submodules", str(CICD), str(copy)], check=True)
for name in ("scan_discovery.py", "scan_powershell.ps1"):
    shutil.copyfile(CICD / "tools" / name, copy / "tools" / name)
minimal_script = copy / EVIDENCE.relative_to(CICD) / "reproduce-action-discovery.py"
subprocess.run([sys.executable, str(minimal_script)], check=True, stdout=subprocess.DEVNULL)
minimal = json.loads(minimal_script.with_name("action-discovery-minimal.json").read_text())
minimal["classification"] = "Ordinary PowerShell parameters and assignment; no child execution or discovery diagnostics."
save("minimal.json", minimal)
assert not minimal["errors"], minimal
assert minimal["selected"] == [".github/actions/example/action.yml", "tests/tools/verify.ps1"], minimal

sys.path.insert(0, str(CICD / "tools"))
from delivery_runtime import Git
from scan_discovery import Discovery

saved = json.loads((EVIDENCE / "action-discovery.json").read_text())
revision = saved["candidate"]
assert git(args.folders, "rev-parse", revision + "^{commit}") == revision

# Verify that the saved 940 diagnostics really describe this exact source.
baseline = "2adf156b24e0a8053de42d7d4bf9b7c15a8b82e4"
baseline_path = scratch / "baseline_discovery.py"
baseline_path.write_text(subprocess.check_output(
    ["git", "-C", str(CICD), "show", baseline + ":tools/scan_discovery.py"], text=True))
spec = importlib.util.spec_from_file_location("baseline_discovery", baseline_path)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
before_files, before_errors = old.Discovery(Git(args.folders), revision).discover()
assert sorted(before_files) == saved["paths"] and before_errors == saved["errors"]

files, errors = Discovery(Git(args.folders), revision).discover()
save("folders.json", {"candidate": revision, "paths": sorted(files), "errors": errors})
summary = {
    "status": "discovery fix verified; story 17 remains in progress",
    "cicd_base": baseline,
    "source_sha256": {name: hashlib.sha256((CICD / name).read_bytes()).hexdigest()
                      for name in ("tools/scan_discovery.py", "tools/scan_powershell.ps1")},
    "folders": revision,
    "folders_tree": git(args.folders, "rev-parse", revision + "^{tree}"),
    "powershell_version": subprocess.check_output(
        ["pwsh", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", "$PSVersionTable.PSVersion.ToString()"],
        text=True).strip(),
    "saved_baseline_reproduced": True,
    "minimal": {"before_errors": len(json.loads((EVIDENCE / "action-discovery-minimal.json").read_text())["errors"]),
                "after_errors": len(minimal["errors"]), "result": "minimal.json"},
    "folders_discovery": {"before_files": len(before_files), "after_files": len(files),
                          "before_errors": len(before_errors), "after_errors": len(errors),
                          "added_files": sorted(set(files) - set(before_files)),
                          "removed_files": sorted(set(before_files) - set(files)),
                          "remaining_by_category": dict(sorted(Counter(
                              error.split(": local-script discovery: ", 1)[-1].split(": ", 1)[0]
                              for error in errors).items())),
                          "remaining_by_file": dict(sorted(Counter(
                              error.split(":", 1)[0] for error in errors).items())),
                          "result": "folders.json"},
    "separate_prerequisites": "Eight historical audit declarations, real product/workload/provider prerequisites, "
                              "AD-21 adoption, delivered green CI and scheduled-night acceptance remain unproven.",
}
save("verification.json", summary)
print(json.dumps(summary, indent=2))
