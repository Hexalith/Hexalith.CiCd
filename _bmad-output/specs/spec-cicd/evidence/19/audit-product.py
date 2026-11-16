#!/usr/bin/env python3
"""Audit final source ownership and exercise dormant nightly script routing in a private job."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

evidence = Path(__file__).resolve().parent
repo = evidence.parents[4] / "references/Hexalith.ChatBot"
baseline = "6a4ca07b18e9b58500dc79dfede1f308da36c828"

def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=repo)

def digest(data):
    return hashlib.sha256(data).hexdigest()

owned = []
for name in [".claude/settings.json", ".github/copilot-instructions.md", ".github/workflows/ci.yml",
             ".github/workflows/release.yml", ".gitmodules", "AGENTS.md", "CLAUDE.md"]:
    before, current = git("show", baseline + ":" + name), (repo / name).read_bytes()
    baseline_mode = git("ls-tree", baseline, "--", name).decode().split()[0]
    current_mode = "100755" if os.access(repo / name, os.X_OK) else "100644"
    owned.append({"path": name, "bytes_equal": before == current, "baseline_mode": baseline_mode,
                  "current_mode": current_mode, "sha256": digest(current)})
assert all(item["bytes_equal"] and item["baseline_mode"] == item["current_mode"] for item in owned)

def gitlinks(revision):
    return [line for line in git("ls-tree", "-r", revision).decode().splitlines() if line.startswith("160000 ")]

links = gitlinks("HEAD")
assert links == gitlinks(baseline) and len(links) == 16
initialized = [line.split("\t", 1)[1] for line in links if (repo / line.split("\t", 1)[1] / ".git").exists()]
assert not initialized
scenario = "tests/Hexalith.ChatBot.IntegrationTests/Recovery/LiveRecoverySweep.cs"
assert git("show", "HEAD:" + scenario) == (repo / scenario).read_bytes()
assert json.loads(git("show", baseline + ":global.json"))["sdk"] == json.loads((repo / "global.json").read_text())["sdk"]
ownership = {"baseline": baseline, "head": git("rev-parse", "HEAD").decode().strip(), "owned": owned,
    "all_owned_unchanged": True, "gitlinks_unchanged": True, "gitlinks_count": len(links),
    "initialized_nested_submodules": initialized, "sdk_pin_unchanged": True,
    "recovery_scenario_body_unchanged_from_preparation": True,
    "product_diff_sha256": digest(git("diff", "--binary", "HEAD")),
    "product_untracked_sha256": {name: digest((repo / name).read_bytes()) for name in git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0") if name},
    "changed_tracked_sha256": {name: digest((repo / name).read_bytes()) if (repo / name).is_file() else None for name in git("diff", "--name-only", "HEAD").decode().splitlines()}}
(evidence / "product-fix-ownership.json").write_text(json.dumps(ownership, indent=2) + "\n")

scratch = Path(os.environ["TMPDIR"]) / "routing"
scratch.mkdir()
stubs = scratch / "bin"
stubs.mkdir()
(stubs / "date").write_text('#!/bin/sh\nprintf "%s\\n" "$ROUTING_WEEKDAY"\n')
(stubs / "dotnet").write_text('''#!/usr/bin/env python3
import json, os, sys
with open(os.environ['ROUTING_INVOCATIONS'], 'a') as output:
    output.write(json.dumps({'arguments': sys.argv[1:], 'retention': os.environ.get('HEXALITH_CHATBOT_RECOVERY_RETENTION_FAILURE_DIR')}) + '\\n')
raise SystemExit(int(os.environ['ROUTING_DOTNET_EXIT']))
''')
for executable in stubs.iterdir():
    executable.chmod(0o700)
environment = dict(os.environ, PATH=str(stubs) + os.pathsep + os.environ["PATH"],
    RUNNER_TEMP=str(scratch), ROUTING_INVOCATIONS=str(scratch / "invocations.jsonl"))
scripts = {name: repo / ".github/actions/nightly" / name for name in ["run-release.sh", "run-recovery.sh"]}
for script in scripts.values():
    subprocess.run(["bash", "-n", script], check=True)
cases = []
for name, script, weekday, requested_exit, expected_calls, expected_exit in [
    ("release failure stays failed", "run-release.sh", "7", 37, 1, 37),
    ("due recovery still invokes whole project", "run-recovery.sh", "7", 0, 1, 0),
    ("non-Sunday leaves weekly sweep due for Sunday", "run-recovery.sh", "1", 0, 0, 0),
    ("recovery failure stays failed", "run-recovery.sh", "7", 23, 1, 23),
]:
    invocation = scratch / "invocations.jsonl"
    invocation.unlink(missing_ok=True)
    completed = subprocess.run(["bash", scripts[script]], cwd=repo,
        env=dict(environment, ROUTING_WEEKDAY=weekday, ROUTING_DOTNET_EXIT=str(requested_exit)),
        capture_output=True, text=True, timeout=15)
    calls = [json.loads(line) for line in invocation.read_text().splitlines()] if invocation.exists() else []
    assert completed.returncode == expected_exit and len(calls) == expected_calls, (name, completed, calls)
    for call in calls:
        assert call["arguments"][:2] == ["test", "--project"]
        assert not any("filter" in value.lower() or value == "-method" for value in call["arguments"])
        assert "--no-build" in call["arguments"] and "--no-restore" in call["arguments"]
    cases.append({"case": name, "exit": completed.returncode, "calls": calls})
action = (repo / ".github/actions/nightly/action.yml").read_text()
condition = "!cancelled() && steps.runtime.outcome == 'success'"
assert "if: ${{ " + condition + " }}" in action and "continue-on-error" not in action
recovery = scripts["run-recovery.sh"].read_text()
assert git("show", "HEAD:.github/actions/nightly/run-recovery.sh").decode() == recovery
routing = {"product_diff_sha256": ownership["product_diff_sha256"], "script_cases": cases,
    "recovery_step_condition": condition, "release_failure_cannot_suppress_due_recovery": True,
    "release_failure_remains_job_failure": True, "recovery_script_unchanged_from_preparation": True,
    "recovery_timeouts_minutes": [250, 280, 300], "recovery_preparation_cleanup_capacity_minutes": 330,
    "release_allowance_minutes": 30, "required_shared_total_minutes": 360,
    "github_hosted_execution_verified": False}
(evidence / "product-nightly-routing.json").write_text(json.dumps(routing, indent=2) + "\n")
print("Owned files, SDK, sixteen gitlinks and recovery body unchanged; nightly script routing checks passed.")
