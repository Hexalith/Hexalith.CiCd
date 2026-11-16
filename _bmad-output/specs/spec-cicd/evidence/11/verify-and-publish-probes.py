"""Verify exact local pilot probe heads, then push/create unmerged PRs.

Run under run-with-temp with one acceptable released Builds tag argument.
Only the protected module credential is used for remote module operations.
All full product output must be redirected to pre-adoption-probe-verification.log.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MODULES = ("Hexalith.Commons", "Hexalith.PolymorphicSerializations")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("builds_tag")
args = parser.parse_args()
assert re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", args.builds_tag)
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
prepared = json.loads((HERE / "local-probe-preparation.json").read_text())
assert prepared["remote_push_performed"] is False and set(prepared["modules"]) == set(MODULES)
report_path = HERE / "pre-delivery-probes.json"
assert not report_path.exists(), "Inspect saved partial push/PR outcomes; do not repeat blindly"
scratch = Path(os.environ["TMPDIR"]).resolve() / "pre-delivery-probes"
scratch.mkdir()
environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                   GH_PROMPT_DISABLED="1")
for name in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(name, None)
report = {"started_at": datetime.now(timezone.utc).isoformat(), "builds_tag": args.builds_tag,
          "purpose": "pre-delivery restricted-token product-only Update branch qualification; never merge",
          "credential_source": "/home/administrator/.config/gh-module-agent/token",
          "modules": {}, "operations": [], "nested_submodule_initialization": False}


def save():
    report_path.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, repository, *, credential=False, data=None):
    result = subprocess.run(arguments, cwd=repository, env=environment if credential else None,
                            input=data, text=True, capture_output=True, timeout=180)
    report["operations"].append({"command": arguments, "cwd": str(repository), "exit": result.returncode,
                                  "stdout": result.stdout, "stderr": result.stderr})
    save()
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


worktrees = []
try:
    user = json.loads(run(["gh", "api", "user", "--jq", "{login,id}"], ROOT, credential=True))
    report["authenticated_actor"] = {"login": user["login"], "id": user["id"]}
    for name in MODULES:
        value = prepared["modules"][name]
        source = ROOT / "references" / name
        job = scratch / name
        assert value["branch"] == "cicd-pilot-update-" + ("commons" if name == MODULES[0] else "poly") + "-20261116"
        assert run(["git", "rev-parse", "refs/heads/" + value["branch"]], source) == value["head"]
        run(["git", "worktree", "add", "--detach", str(job), value["head"]], source)
        worktrees.append((source, job))
        report["modules"][name] = {key: value[key] for key in ("branch", "base", "head", "changed_paths", "allowed_changed_paths")}
        report["modules"][name].update(remote_branch_created=False, pull_request_created=False)
    save()
    verifier = [sys.executable, str(HERE / "pre-adoption-verify.py"), args.builds_tag,
                *[prepared["modules"][name][key] for name in MODULES for key in ("base", "head")],
                "--purpose", "probe", "--commons-repository", str(scratch / MODULES[0]),
                "--poly-repository", str(scratch / MODULES[1])]
    result = subprocess.run(verifier, cwd=ROOT, check=False)
    report["complete_approved_verifier_exit"] = result.returncode
    save()
    assert result.returncode == 0, "Full approved verification failed; no probe push attempted"
    proof_path = HERE / "pre-adoption-probe-verification.json"
    proof = json.loads(proof_path.read_text())
    assert proof["result"] == "pass" and proof["purpose"] == "probe" and proof["builds_tag"] == args.builds_tag
    report["verification_report_sha256"] = hashlib.sha256(proof_path.read_bytes()).hexdigest()
    for name in MODULES:
        value = report["modules"][name]
        job = scratch / name
        assert proof["modules"][name]["base"] == value["base"] and proof["modules"][name]["head"] == value["head"]
        # Repeat immediately for each individual push, including Commons after
        # Poly has completed its full verification. No stale test result grants
        # permission to push a successor or a new current-main base.
        run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], job, credential=True)
        assert run(["git", "rev-parse", "origin/main"], job) == value["base"], "Main advanced; rerun affected checks"
        assert run(["git", "rev-parse", "HEAD"], job) == value["head"]
        assert run(["git", "status", "--porcelain", "--ignore-submodules=all"], job) == ""
        assert run(["git", "ls-remote", "--heads", "origin", "refs/heads/" + value["branch"]], job, credential=True) == ""
        value["immediate_prepush_freshness_at"] = datetime.now(timezone.utc).isoformat()
        save()
        run(["git", "push", "--porcelain", "origin", "HEAD:refs/heads/" + value["branch"]], job, credential=True)
        value["remote_branch_created"] = True
        save()
        endpoint = "repos/Hexalith/" + name
        remote = json.loads(run(["gh", "api", endpoint + "/git/ref/heads/" + value["branch"]], job, credential=True))
        assert remote["object"]["sha"] == value["head"]
        main = json.loads(run(["gh", "api", endpoint + "/git/ref/heads/main"], job, credential=True))
        assert main["object"]["sha"] == value["base"], "Main advanced before PR creation"
        body = ("Disposable pilot qualification for the actual App delivery's workflow-changing main update. "
                "Do not merge.\n\nBase: `" + value["base"] + "`\nHead: `" + value["head"] + "`\n\n"
                "Product-only changes passed the complete human-approved pre-adoption checks, including unchanged owned bytes, modes and gitlinks. "
                "Legacy tooling is retained. This probe will be closed and its branch deleted after the actual Update branch outcome is recorded.")
        request = {"title": "test(cicd): qualify pilot Update branch behavior", "head": value["branch"],
                   "base": "main", "body": body, "maintainer_can_modify": False}
        pull = json.loads(run(["gh", "api", "--method", "POST", endpoint + "/pulls", "--input", "-"],
                              job, credential=True, data=json.dumps(request)))
        assert pull["head"]["sha"] == value["head"] and pull["base"]["sha"] == value["base"]
        assert pull["state"] == "open" and pull["merged_at"] is None
        value.update(pull_request_created=True, pull_request_number=pull["number"], pull_request_url=pull["html_url"])
        save()
    report["result"] = "both pre-delivery probe branches and unmerged PRs created"
finally:
    cleanup = []
    for source, worktree in reversed(worktrees):
        result = subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=source,
                                capture_output=True, text=True, timeout=120)
        cleanup.append({"repository": str(source), "path": str(worktree), "exit": result.returncode,
                        "stderr": result.stderr})
    report["temporary_worktree_cleanup"] = cleanup
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    save()
    assert all(value["exit"] == 0 for value in cleanup), "Temporary worktree cleanup failed"
    for source, worktree in worktrees:
        assert "worktree " + str(worktree) + "\n" not in run(["git", "worktree", "list", "--porcelain"], source) + "\n"
    report["all_temporary_worktree_metadata_removed"] = True
    save()
