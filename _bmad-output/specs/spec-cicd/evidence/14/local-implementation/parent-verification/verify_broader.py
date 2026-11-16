"""Rerun affected shared-library groups with CI's locked Node prerequisites."""
from pathlib import Path
import json
import os
import subprocess


ROOT = Path(__file__).resolve().parents[7]
OUTPUT = Path(__file__).resolve().parent
SOURCE = ROOT / "references/Hexalith.Builds"
SCRATCH = Path(os.environ["TMPDIR"])
CANDIDATE = SCRATCH / "Builds"
SUMMARY = {"commands": []}


def run(label, command, *, cwd=CANDIDATE, data=None):
    environment = {**os.environ, "npm_config_cache": str(SCRATCH / "npm-cache")}
    with (OUTPUT / (label + ".log")).open("w") as log:
        result = subprocess.run(command, cwd=cwd, env=environment, input=data,
                                stdout=log, stderr=subprocess.STDOUT)
    SUMMARY["commands"].append({"label": label, "command": command,
                                "exitCode": result.returncode})
    (OUTPUT / "broader-results.json").write_text(json.dumps(SUMMARY, indent=2) + "\n")
    print(label, result.returncode, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


run("candidate-clone", ["git", "clone", "--quiet", "--shared", "--no-recurse-submodules",
                         str(SOURCE), str(CANDIDATE)], cwd=SCRATCH)
patch = subprocess.check_output(["git", "-C", str(SOURCE), "diff", "--binary", "HEAD"])
run("candidate-apply", ["git", "apply", "--binary"], data=patch)
run("candidate-stage", ["git", "add", "--all"])
SUMMARY["candidateTree"] = subprocess.check_output(
    ["git", "-C", str(CANDIDATE), "write-tree"], text=True).strip()
run("node-locked-install", ["npm", "ci", "--ignore-scripts"])
run("node-signatures", ["npm", "audit", "signatures"])
for group in ("test_guard_actions.py", "test_guard_tools.py", "test_ci_environment.py",
              "test_release_adapters.py", "test_release_build.py"):
    run(group.removesuffix(".py") + "-python312", [
        "uv", "run", "--no-cache", "--python", "3.12", "--with", "jsonschema==4.26.0",
        "--with", "PyYAML==6.0.3", "python", "-B", "-m", "unittest", "discover",
        "-s", "Github/lib/tests", "-p", group, "-v",
    ])
SUMMARY["result"] = "pass"
(OUTPUT / "broader-results.json").write_text(json.dumps(SUMMARY, indent=2) + "\n")
