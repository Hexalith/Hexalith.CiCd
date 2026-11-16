"""Verify a committed, local-only Memories preparation candidate in private TMPDIR.

Run with run-with-temp. All Git reads/clones use local repositories. This does
not fetch, push, call GitHub, provision settings, register or adopt the module.
Package restore and npm tool verification may use their normal public feeds.
"""

import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time


SOURCE = Path("/home/administrator/projects/hexalith/memories-story-22")
EVIDENCE = Path(__file__).resolve().parent
ROOT = Path(os.environ["TMPDIR"]) / "memories"
BASELINE = "c64e292a46858058f6764095c8e01c2faa0ff3e0"
PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--suites", nargs="*", default=["coverage_gate", "release_dispatch",
    "release_preflight", "builds_publication_qualification", "publish_containers",
    "access_telemetry_functional_retention"])
PARSER.add_argument("--no-core", action="store_true")
PARSER.add_argument("--project", help="Qualify only this affected complete test project")
ARGS = PARSER.parse_args()


def git(*arguments, root=SOURCE):
    return subprocess.check_output(["git", *arguments], cwd=root, text=True).strip()


CANDIDATE = git("rev-parse", "HEAD")
OUTPUT = EVIDENCE / ("verification-" + CANDIDATE[:12])
OUTPUT.mkdir(exist_ok=True)


def run(label, arguments, *, root=ROOT, timeout=1800):
    started = time.monotonic()
    process = None
    with (OUTPUT / (label + ".log")).open("w") as log:
        log.write("Candidate: " + CANDIDATE + "\nCommand: " + json.dumps(arguments) + "\n")
        log.flush()
        try:
            process = subprocess.Popen(arguments, cwd=root, stdout=log,
                stderr=subprocess.STDOUT, start_new_session=True,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                    DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1",
                    MSBUILDDISABLENODEREUSE="1"))
            exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            exit_code = 124
            log.write("\nVerification command exceeded its local diagnostic budget.\n")
        finally:
            # Any child still in this command's group must finish before cleanup.
            if process is not None:
                finish_group(process.pid)
                process.wait()
    record = {"command": arguments, "exitCode": exit_code,
              "seconds": round(time.monotonic() - started, 2)}
    output = (OUTPUT / (label + ".log")).read_text()
    counts = {name: int(value) for name, value in re.findall(
        r"^  (total|failed|succeeded|skipped): (\d+)$", output, re.MULTILINE)}
    if counts:
        record["testCounts"] = counts
    print(label, json.dumps(record), flush=True)
    return label, record


def finish_group(group):
    def remaining():
        active = []
        for proc in Path("/proc").iterdir():
            if not proc.name.isdigit():
                continue
            try:
                fields = (proc / "stat").read_text().rsplit(")", 1)[1].split()
            except (FileNotFoundError, ProcessLookupError):
                continue
            if int(fields[2]) == group and fields[0] not in ("Z", "X"):
                active.append(int(proc.name))
        return active
    for action in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(group, action)
        except ProcessLookupError:
            return
        deadline = time.monotonic() + 10
        while remaining() and time.monotonic() < deadline:
            time.sleep(0.1)
        if not remaining():
            return
    raise RuntimeError("Verification process group did not stop: " + str(group))


def interrupt(_number, _frame):
    raise KeyboardInterrupt("Verification interrupted; finishing active child process group")


signal.signal(signal.SIGTERM, interrupt)


subprocess.run(["git", "clone", "--local", "--no-hardlinks", "--no-checkout",
                str(SOURCE), str(ROOT)], check=True, capture_output=True)
subprocess.run(["git", "checkout", "--detach", CANDIDATE], cwd=ROOT,
               check=True, capture_output=True)
dependencies = {}
for name in ("Hexalith.AI.Tools", "Hexalith.Builds", "Hexalith.Commons",
             "Hexalith.EventStore", "Hexalith.Tenants", "Hexalith.FrontComposer",
             "Hexalith.McpCli", "Hexalith.Platform"):
    relative = "references/" + name
    sha = git("rev-parse", CANDIDATE + ":" + relative)
    subprocess.run(["git", "clone", "--local", "--no-hardlinks", "--no-checkout",
                    str(SOURCE / relative), str(ROOT / relative)],
                   check=True, capture_output=True)
    subprocess.run(["git", "checkout", "--detach", sha], cwd=ROOT / relative,
                   check=True, capture_output=True)
    dependencies[relative] = sha

protected = [".github/workflows", ".github/hexalith-ci.json",
             ".github/dependabot.yml", "references/Hexalith.Builds",
             ".gitmodules", "AGENTS.md", "CLAUDE.md",
             ".github/copilot-instructions.md", ".claude/settings.json",
             ".claude/settings.local.json", "global.json"]
proof = {}
for path in protected:
    before = git("ls-tree", "-r", BASELINE, "--", path)
    after = git("ls-tree", "-r", CANDIDATE, "--", path)
    proof[path] = {"unchanged": before == after, "baselineTree": before,
                   "candidateTree": after}
    if before != after:
        raise RuntimeError("Owned/foreign instruction bytes, modes or gitlinks changed: " + path)

records = {}
(OUTPUT / "inputs.json").write_text(json.dumps({"candidate": CANDIDATE,
    "baseline": BASELINE, "dependencies": dependencies, "protectedContent": proof}, indent=2) + "\n")
if not ARGS.no_core:
  label, record = run("ci-product-build", ["dotnet", "build", ARGS.project or "Hexalith.Memories.slnx",
    "--configuration", "Release", "-m:1", "-warnaserror",
    "--disable-build-servers", "-p:UseHexalithProjectReferences=false",
    "-p:NuGetAudit=false"])
  records[label] = record
  if record["exitCode"]:
    # Preserve audit/restore failures and try a smaller complete project. No audit bypass.
    label, record = run("cli-tests-build", ["dotnet", "build",
        "tests/Hexalith.Memories.Cli.Tests/Hexalith.Memories.Cli.Tests.csproj",
        "--configuration", "Release", "-m:1", "-warnaserror",
        "-p:UseHexalithProjectReferences=false", "-p:NuGetAudit=true"])
    records[label] = record
    if not record["exitCode"]:
        label, record = run("cli-tests", ["dotnet", "test", "--project",
            "tests/Hexalith.Memories.Cli.Tests/Hexalith.Memories.Cli.Tests.csproj",
            "--configuration", "Release", "--no-build", "--no-restore",
            "--stop-on-fail", "off"])
        records[label] = record
  else:
    projects = [ROOT / ARGS.project] if ARGS.project else sorted((ROOT / "tests").glob("*.Tests/*.csproj"))
    for project in projects:
        # Each entire project is attempted; no trait filter or truncation.
        label, record = run(project.stem, ["dotnet", "test", "--project",
            str(project.relative_to(ROOT)), "--configuration", "Release",
            "--no-build", "--no-restore", "--stop-on-fail", "off"], timeout=2700)
        records[label] = record

  label, record = run("release-audit", ["dotnet", "restore", ARGS.project or "Hexalith.Memories.slnx",
    "--force", "-p:Configuration=Release", "-warnaserror",
    "-p:UseHexalithProjectReferences=false", "-p:NuGetAudit=true"])
  records[label] = record

suites = [ROOT / "tests/tooling" / name for name in ARGS.suites]
if any(not path.is_dir() or not any(path.glob("*test*.py")) for path in suites):
    raise RuntimeError("Selected product suite is missing")
def suite(path):
    return run("python-" + path.name, [sys.executable, "-m", "unittest", "discover",
        "-s", str(path.relative_to(ROOT)), "-p", "*test*.py"], timeout=2700)

for path in suites:
    label, record = suite(path)
    records[label] = record

status = git("status", "--short", root=ROOT)
summary = {"candidate": CANDIDATE, "baseline": BASELINE,
           "scope": "local preparation only; no hosted acceptance or push approval",
           "dependencies": dependencies, "protectedContent": proof,
           "commands": records, "finalDisposableStatus": status,
           "unexecuted": ["stage-4 fast integration: prepared Dapr/composition environment unavailable",
               "nightly slow/performance integration and complete benchmark project: prepared environment unavailable",
               "browser runtime/typecheck/artifacts: shared npm Playwright preparation unavailable",
               "real rollout and recovery: shared prepared OCI/tool inputs unavailable",
               "Debug/source graph and complete source-selected catalog project: separately released support unavailable",
               "hosted validation, adoption, cleanup, green CI and scheduled nightly: local-only stage"],
           "completeAcceptance": False,
           "attemptedCommandsSucceeded": all(record["exitCode"] == 0 for record in records.values())}
(OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print("SUMMARY", OUTPUT / "summary.json", flush=True)
sys.exit(0 if summary["attemptedCommandsSucceeded"] else 1)
