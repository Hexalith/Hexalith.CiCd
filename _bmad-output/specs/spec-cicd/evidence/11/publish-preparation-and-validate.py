"""Publish verified pilot preparation, then fully validate the exact CiCd candidate.

Run under run-with-temp. No delivery-triggering CiCd push occurs here. Only the
protected module credential writes module mains; existing CiCd-agent credentials
read the release and qualify the isolated committed candidate.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--validation-only", action="store_true")
parser.add_argument("--attempt", type=int, default=1)
args = parser.parse_args()
assert (args.attempt == 1 and not args.validation_only) or (args.attempt >= 2 and args.validation_only)
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MODULES = ("Hexalith.Commons", "Hexalith.PolymorphicSerializations")
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
candidate = json.loads((HERE / "adoption-candidate.json").read_text())
preparation = json.loads((HERE / "local-product-preparation.json").read_text())
proof_path = HERE / "pre-adoption-verification.json"
proof = json.loads(proof_path.read_text())
assert proof["result"] == "pass" and proof["builds_tag"] == "v6.0.6"
report_path = HERE / ("candidate-validation-" + str(args.attempt) + ".json" if args.validation_only
                      else "preparation-publication-and-candidate-validation.json")
assert not report_path.exists(), "Inspect actual partial remote outcomes; never repeat uncertain pushes"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "candidate": candidate["head"],
          "candidate_base": candidate["base"], "builds_tag": "v6.0.6", "phase": "preflight",
          "approved_proof_sha256": hashlib.sha256(proof_path.read_bytes()).hexdigest(),
          "modules": {}, "operations": [], "cicd_push_performed": False,
          "validation_only": args.validation_only, "attempt": args.attempt}
if args.validation_only:
    published = json.loads((HERE / "preparation-publication-and-candidate-validation.json").read_text())
    assert all(published["modules"][name]["push_confirmed"] is True for name in MODULES)
module_environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                          GH_PROMPT_DISABLED="1")
for name in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    module_environment.pop(name, None)
scratch = Path(os.environ["TMPDIR"]) / "committed-live-candidate"
scratch.mkdir()
job = scratch / "cicd"
builds = ROOT / "references/Hexalith.Builds"
worktrees = []


def save():
    report_path.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, repository, *, module=False):
    result = subprocess.run(arguments, cwd=repository, env=module_environment if module else None,
                            capture_output=True, text=True, timeout=180)
    report["operations"].append({"command": arguments, "cwd": str(repository), "exit": result.returncode,
                                  "stdout": result.stdout, "stderr": result.stderr})
    save()
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def get(endpoint, *, module=False):
    return json.loads(run(["gh", "api", endpoint], ROOT, module=module))


staging = subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                         capture_output=True, check=True).stdout
assert hashlib.sha256(staging).hexdigest() == candidate["original_staging_sha256"]
run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], ROOT)
assert run(["git", "rev-parse", "origin/main"], ROOT) == candidate["base"]
assert run(["git", "rev-parse", "refs/heads/" + candidate["branch"]], ROOT) == candidate["head"]
for path, expected in candidate["source_file_sha256"].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
release = get("repos/Hexalith/Hexalith.Builds/releases/tags/v6.0.6")
assert release["draft"] is False and release["prerelease"] is False and release["immutable"] is True
assert release["author"]["login"] == "github-actions[bot]" and release["published_at"]
run(["git", "fetch", "--no-recurse-submodules", "origin", "tag", "v6.0.6"], builds)
builds_sha = run(["git", "rev-parse", "v6.0.6^{commit}"], builds)
assert builds_sha == candidate["direct_gitlinks"]["Hexalith.Builds"] == "fdda17c0a4538b0f7c99f813c20ca24b49006530"
assert run(["git", "rev-parse", "HEAD"], builds) == builds_sha
assert run(["git", "status", "--porcelain", "--ignore-submodules=all"], builds) == ""
run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], builds)
run(["git", "merge-base", "--is-ancestor", builds_sha, "origin/main"], builds)
report["released_source_freshness"] = "pass"
try:
    run(["git", "worktree", "add", "--detach", str(job), candidate["head"]], ROOT)
    worktrees.append((ROOT, job))
    direct = job / "references/Hexalith.Builds"
    assert direct.is_dir() and not any(direct.iterdir())
    direct.rmdir()
    run(["git", "worktree", "add", "--detach", str(direct), builds_sha], builds)
    worktrees.append((builds, direct))
    for name in MODULES:
        source = ROOT / "references" / name
        value = preparation["modules"][name]
        assert all(proof["modules"][name][key] == value[key] for key in ("base", "head"))
        assert candidate["direct_gitlinks"][name] == value["head"]
        run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], source, module=True)
        expected_main = value["head"] if args.validation_only else value["base"]
        assert run(["git", "rev-parse", "origin/main"], source) == expected_main, "Main advanced; reassess affected inputs"
        assert run(["git", "rev-parse", "HEAD"], source) == value["head"]
        assert run(["git", "status", "--porcelain", "--ignore-submodules=all"], source) == ""
        report["modules"][name] = {"base": value["base"], "tested_head": value["head"],
            "freshness_at": datetime.now(timezone.utc).isoformat(), "push_attempted": not args.validation_only,
            "preparation_already_published": args.validation_only}
        report["phase"] = ("verify published preparation " if args.validation_only else "publish preparation ") + name
        save()
        if not args.validation_only:
            run(["git", "push", "--porcelain", "origin", "HEAD:refs/heads/main"], source, module=True)
        current = get("repos/Hexalith/" + name + "/git/ref/heads/main", module=True)
        assert current["object"]["sha"] == value["head"]
        commit = get("repos/Hexalith/" + name + "/git/commits/" + value["head"], module=True)
        assert [parent["sha"] for parent in commit["parents"]] == [value["base"]]
        report["modules"][name].update(push_confirmed=True, remote_main=current["object"]["sha"], tree=commit["tree"]["sha"])
        save()
        print("Verified " + ("existing preparation main: " if args.validation_only else "preparation main push: ") + name + " " + value["head"], flush=True)
    report["phase"] = "full locked committed/live-main candidate verdict"
    report["validation_started_at"] = datetime.now(timezone.utc).isoformat()
    save()
    credential = subprocess.run(["gh", "auth", "token"], cwd=ROOT, capture_output=True, text=True, check=True, timeout=30).stdout.strip()
    assert credential
    validation_environment = dict(os.environ, GH_TOKEN=credential, GH_PROMPT_DISABLED="1",
                                  UV_CACHE_DIR=str(scratch / "uv-cache"))
    for name in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
        validation_environment.pop(name, None)
    output_path = HERE / ("adoption-candidate-full-validation-" + str(args.attempt) + ".log" if args.validation_only
                          else "adoption-candidate-full-validation.log")
    with output_path.open("w") as output:
        process = subprocess.Popen(["uv", "run", "--locked", "--script", "tools/validate.py"], cwd=job,
                                   env=validation_environment, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        report["validation_pid"] = process.pid
        save()
        try:
            status = process.wait(timeout=2400)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            report["validation_outer_timeout"] = True
            raise
        finally:
            # Includes children left by a failed inner timeout. Never leave a
            # validation process group running when its disposable job exits.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    report["validation_exit"] = status
    report["validation_completed_at"] = datetime.now(timezone.utc).isoformat()
    report["validation_log_sha256"] = hashlib.sha256(output_path.read_bytes()).hexdigest()
    lines = output_path.read_text().splitlines()
    verdicts = []
    for line in lines:
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict) and set(value) == {"global", "modules"}:
            verdicts.append(value)
    assert len(verdicts) == 1
    report["verdict"] = verdicts[0]
    save()
    assert status == 0 and verdicts[0] == {"global": True, "modules": list(MODULES)}, "Full candidate validation failed"
    for name in MODULES:
        assert get("repos/Hexalith/" + name + "/git/ref/heads/main", module=True)["object"]["sha"] == preparation["modules"][name]["head"]
    assert run(["git", "rev-parse", "HEAD"], job) == candidate["head"]
    assert run(["git", "status", "--porcelain", "--ignore-submodules=all"], job) == ""
    report.update(phase="complete", result="both preparation mains published and exact committed/live candidate passed")
    save()
finally:
    cleanup = []
    for source, worktree in reversed(worktrees):
        result = subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=source,
                                capture_output=True, text=True, timeout=120)
        cleanup.append({"repository": str(source), "path": str(worktree), "exit": result.returncode, "stderr": result.stderr})
    report["temporary_worktree_cleanup"] = cleanup
    after = subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                           capture_output=True, check=True).stdout
    report["original_staging_preserved"] = after == staging
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    save()
    assert all(row["exit"] == 0 for row in cleanup) and after == staging
    for source, worktree in worktrees:
        assert "worktree " + str(worktree) + "\n" not in run(["git", "worktree", "list", "--porcelain"], source) + "\n"
    report["all_temporary_worktree_metadata_removed"] = True
    save()
print(json.dumps({key: report[key] for key in ("candidate", "result", "verdict", "original_staging_preserved")}, indent=2))
