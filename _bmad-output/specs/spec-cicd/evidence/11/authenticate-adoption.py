"""Authenticate actual pilot delivery artifacts, refs, parents and complete trees.

Read-only verification under run-with-temp; no module checkout/index application,
App-key access, nested initialization or owned-file authoring occurs here.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--qualified-policy", action="store_true")
args = parser.parse_args()
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
binding = json.loads((HERE / ("qualified-policy-push.json" if args.qualified_policy else "cicd-candidate-push.json")).read_text())
candidate = json.loads((HERE / ("qualified-policy-candidate.json" if args.qualified_policy else "adoption-candidate.json")).read_text())
preparation = json.loads((HERE / "local-product-preparation.json").read_text())
initial_adoption = json.loads((HERE / "authenticated-adoption.json").read_text()) if args.qualified_policy else None
if initial_adoption:
    assert initial_adoption["result"] == "pass"
HEAD = candidate["head"]
assert HEAD == binding["head"] == ("3427f041c5f686c460c1fa027cf6f835791209c1" if args.qualified_policy else "f002539f6fbaddaa9b621a9cbf75a1263eee5dea")
MODULES = ("Hexalith.Commons", "Hexalith.PolymorphicSerializations")
path = HERE / ("authenticated-policy-redelivery.json" if args.qualified_policy else "authenticated-adoption.json")
assert not path.exists(), "Preserve previous/partial authentication; inspect before resuming"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "candidate": HEAD,
          "kind": "qualified-policy redelivery" if args.qualified_policy else "initial pilot adoption",
          "run_id": binding["delivery_run"]["id"], "operations": [], "modules": {}, "result": "pending"}
module_environment = dict(os.environ, GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
                          GH_PROMPT_DISABLED="1")
for name in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    module_environment.pop(name, None)


def save():
    path.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, *, cwd=ROOT, module=False):
    value = subprocess.run(arguments, cwd=cwd, env=module_environment if module else None,
                           capture_output=True, timeout=180)
    report["operations"].append({"command": arguments, "repository": str(cwd), "exit": value.returncode,
                                  "stdout": value.stdout.decode(), "stderr": value.stderr.decode()})
    save()
    assert value.returncode == 0, value.stderr.decode()
    return value.stdout


def get(endpoint, *, module=False):
    return json.loads(run(["gh", "api", endpoint], module=module))


# Load only the released trusted shared perimeter library and committed CiCd
# production artifact parser. These adapters perform ordinary anonymous reads.
for filename in ("tools/nightly_runtime.py", "tools/nightly_delivery_wait.py"):
    trusted = subprocess.run(["git", "show", HEAD + ":" + filename], cwd=ROOT,
                             capture_output=True, check=True, timeout=30).stdout
    assert trusted == (ROOT / filename).read_bytes()
    report.setdefault("trusted_production_parser_source_sha256", {})[filename] = hashlib.sha256(trusted).hexdigest()
sys.path.insert(0, str(ROOT / "tools"))
import nightly_runtime as rt
import nightly_delivery_wait as wait
builds_source = ROOT / "references/Hexalith.Builds"
assert subprocess.run(["git", "rev-parse", "HEAD"], cwd=builds_source,
                      capture_output=True, text=True, check=True).stdout.strip() == candidate["direct_gitlinks"]["Hexalith.Builds"]
assert subprocess.run(["git", "status", "--porcelain", "--ignore-submodules=all"], cwd=builds_source,
                      capture_output=True, text=True, check=True).stdout == ""
sys.path.insert(0, str(ROOT / "references/Hexalith.Builds/Github/lib"))
import expected_state
import perimeter

staging = subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                         capture_output=True, check=True, timeout=30).stdout
report["original_staging_sha256"] = hashlib.sha256(staging).hexdigest()
endpoint = "repos/Hexalith/Hexalith.CiCd/actions/runs/" + str(report["run_id"])
selected = get(endpoint)
assert selected["head_sha"] == HEAD and selected["path"] == ".github/workflows/deliver.yml"
assert selected["event"] == "push" and selected["head_branch"] == "main"
assert selected["status"] == "completed" and selected["conclusion"] == "success"
assert selected["run_attempt"] == binding["delivery_run"]["run_attempt"]
inventory = get(endpoint + "/artifacts?per_page=100")
assert inventory["total_count"] < 100
artifacts = [item for item in inventory["artifacts"] if item["name"] == "hexalith-delivery"]
assert len(artifacts) == 1
artifact = artifacts[0]
origin = artifact["workflow_run"]
assert (origin["id"], origin["head_sha"], origin["head_branch"]) == (selected["id"], HEAD, "main")
credential = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True,
                            check=True, timeout=30).stdout.strip()
api = rt.API(rt.Budget(token_epoch=time.time()))
document = api.artifact_member("Hexalith.CiCd", artifact, "delivery.json", credential)
state = {"delivery": {"runId": selected["id"], "attempt": selected["run_attempt"], "head": HEAD, "event": "push"},
         "repositories": list(MODULES), "errors": []}
rows = wait.report_document(document, state)
assert not state["errors"] and document["tools_source_sha"] == HEAD
assert len(rows) == 2
refreshed = get(endpoint)
assert all(refreshed[key] == selected[key] for key in ("id", "head_sha", "run_attempt", "status", "conclusion", "event", "path"))
(HERE / ("qualified-policy-delivery-report.json" if args.qualified_policy else "delivery-report.json")).write_text(json.dumps(document, indent=2) + "\n")
report["artifact"] = {key: artifact[key] for key in ("id", "name", "size_in_bytes", "digest", "workflow_run", "expired", "expires_at")}
report["run"] = {key: selected[key] for key in ("id", "head_sha", "head_branch", "event", "path", "status", "conclusion", "run_attempt", "html_url")}
save()
expected = perimeter.Git(ROOT).snapshot(HEAD)
builds = perimeter.Git(ROOT / "references/Hexalith.Builds")
assert builds.run("rev-parse", "v6.0.6^{commit}").decode().strip() == candidate["direct_gitlinks"]["Hexalith.Builds"]
for name in MODULES:
    row = next(item for item in document["modules"] if item["repository"] == name)
    assert row["accepted_sha"] == HEAD and row["advancement"] == "advanced"
    assert row["application"] == "pushed" and row["processed"] is True and row["reasons"] == []
    adopted = row["pushed_sha"]
    assert re.fullmatch(r"[0-9a-f]{40}", adopted)
    prefix = "repos/Hexalith/" + name
    accepted = get("repos/Hexalith/Hexalith.CiCd/git/ref/heads/delivered/" + name)
    assert accepted["object"]["sha"] == HEAD
    commit = get(prefix + "/git/commits/" + adopted, module=True)
    before = initial_adoption["modules"][name]["adoption_sha"] if args.qualified_policy else preparation["modules"][name]["head"]
    assert [item["sha"] for item in commit["parents"]] == [before], "Inspect actual forward-only race before claiming initial adoption"
    source = ROOT / "references" / name
    nested = source / "references/Hexalith.Builds"
    assert not nested.exists() or not any(nested.iterdir())
    run(["git", "fetch", "--no-recurse-submodules", "origin", "main"], cwd=source, module=True)
    assert run(["git", "rev-parse", "origin/main"], cwd=source).decode().strip() == adopted
    assert run(["git", "rev-parse", "HEAD"], cwd=source).decode().strip() == preparation["modules"][name]["head"]
    assert run(["git", "status", "--porcelain", "--ignore-submodules=all"], cwd=source) == b""
    git = expected_state.Git(source)
    comparison = expected_state.compare_repository(git, repository="Hexalith/" + name,
                                                   ref=adopted, delivered_sha=HEAD)
    comparison.require_clean()
    assert comparison.delivered_sha == HEAD
    old, actual = git.snapshot(before), git.snapshot(adopted)
    assert actual.ref == commit["tree"]["sha"]
    config = json.loads(expected.read("rendered/" + name + ".perimeter.json"))
    plan = perimeter._Plan(config, old, expected, "rendered/" + name, builds, None)
    unchanged, repaired = [], []
    for filename in sorted(set(old.items) | set(actual.items) | set(plan.changes)):
        if filename not in plan.changes:
            assert old.items.get(filename) == actual.items.get(filename), "Foreign byte/mode/gitlink changed: " + filename
            unchanged.append(filename)
            continue
        wanted = plan.changes[filename]
        observed = actual.items.get(filename)
        if wanted is None:
            assert observed is None, filename
        elif wanted.mode == "160000":
            assert observed == perimeter.Item(wanted.mode, wanted.oid), filename
        else:
            assert observed is not None and observed.mode == wanted.mode, filename
            assert actual.read(filename) == wanted.data, "Actual full/merged owned bytes differ: " + filename
        repaired.append(filename)
    assert actual.read("global.json") == old.read("global.json")
    csharp = [filename for filename in unchanged if filename.endswith(".cs")]
    assert len(csharp) > 0 and all(filename in unchanged for filename in old.items if filename.endswith(".cs"))
    assert not nested.exists() or not any(nested.iterdir())
    report["modules"][name] = {"adoption_sha": adopted, "application_sha": adopted, "sole_parent": before, "accepted_sha": HEAD,
        "tree": actual.ref, "message": commit["message"], "perimeter_match": True,
        "foreign_tree_preserved": True, "unchanged_paths": len(unchanged),
        "unchanged_path_list_sha256": hashlib.sha256("\n".join(unchanged).encode()).hexdigest(),
        "owned_repair_paths": repaired, "csharp_files_unchanged": len(csharp), "sdk_pin_unchanged": True,
        "original_nested_builds_empty": True}
    save()
assert subprocess.run(["git", "diff", "--cached", "--binary", "--no-ext-diff"], cwd=ROOT,
                      capture_output=True, check=True, timeout=30).stdout == staging
report.update(result="pass", completed_at=datetime.now(timezone.utc).isoformat(), original_staging_preserved=True)
save()
print(json.dumps({"result": report["result"], "candidate": HEAD, "modules": report["modules"]}, indent=2))
