"""Authenticate actual McpCli App delivery, perimeter match and sole parent.

Clone objects stay under TMPDIR. Evidence is written beside this file.
Does not initialize nested Builds or apply owned files in the persistent tree.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/administrator/projects/hexalith/cicd")
HEAD = "060ab6e0812e2279e2c2ed0ebdd4c4c7bc3f1778"
PREP = "aad8894e24b28b254d1ffa69c16b7353a70452fa"
RUN_ID = 44171668132
MODULE = "Hexalith.McpCli"
REGISTERED = (
    "Hexalith.AI.Tools",
    "Hexalith.Commons",
    "Hexalith.Conversations",
    "Hexalith.McpCli",
    "Hexalith.PolymorphicSerializations",
)
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
assert Path(os.environ["TMPDIR"]).resolve().is_dir()
path = HERE / "authenticated-adoption.json"
assert not path.exists(), "Inspect the existing adoption record before any retry"
report = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "candidate": HEAD,
    "product_preparation_sha": PREP,
    "run_id": RUN_ID,
    "result": "pending",
}
module_environment = dict(
    os.environ,
    GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
    GH_PROMPT_DISABLED="1",
    GIT_TERMINAL_PROMPT="0",
)
for name in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    module_environment.pop(name, None)


def save() -> None:
    path.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, *, cwd=ROOT, env=None, timeout=180):
    value = subprocess.run(
        arguments, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    report.setdefault("operations", []).append({
        "command": arguments, "repository": str(cwd), "exit": value.returncode,
        "stdout": value.stdout[-4000:], "stderr": value.stderr[-4000:],
    })
    save()
    assert value.returncode == 0, value.stdout + value.stderr
    return value.stdout.strip()


save()
for filename in ("tools/nightly_runtime.py", "tools/nightly_delivery_wait.py"):
    trusted = subprocess.check_output(["git", "show", HEAD + ":" + filename], cwd=ROOT)
    assert trusted == (ROOT / filename).read_bytes()
    report.setdefault("trusted_production_parser_source_sha256", {})[filename] = (
        hashlib.sha256(trusted).hexdigest())
sys.path.insert(0, str(ROOT / "tools"))
import nightly_runtime as rt
import nightly_delivery_wait as wait
sys.path.insert(0, str(ROOT / "references/Hexalith.Builds/Github/lib"))
import expected_state
import perimeter

selected = json.loads(run(["gh", "api", f"repos/Hexalith/Hexalith.CiCd/actions/runs/{RUN_ID}"]))
assert selected["head_sha"] == HEAD
assert selected["path"] == ".github/workflows/deliver.yml"
assert selected["event"] == "push" and selected["head_branch"] == "main"
assert selected["status"] == "completed" and selected["conclusion"] == "success"
inventory = json.loads(run([
    "gh", "api", f"repos/Hexalith/Hexalith.CiCd/actions/runs/{RUN_ID}/artifacts?per_page=100"]))
assert inventory["total_count"] < 100
artifacts = [item for item in inventory["artifacts"] if item["name"] == "hexalith-delivery"]
assert len(artifacts) == 1
artifact = artifacts[0]
assert (artifact["workflow_run"]["id"], artifact["workflow_run"]["head_sha"],
        artifact["workflow_run"]["head_branch"]) == (selected["id"], HEAD, "main")
credential = subprocess.check_output(
    ["gh", "auth", "token"], env={**os.environ, "GH_PROMPT_DISABLED": "1"}, text=True).strip()
api = rt.API(rt.Budget(token_epoch=time.time()))
document = api.artifact_member("Hexalith.CiCd", artifact, "delivery.json", credential)
state = {
    "delivery": {
        "runId": selected["id"],
        "attempt": selected["run_attempt"],
        "head": HEAD,
        "event": "push",
    },
    "repositories": list(REGISTERED),
    "errors": [],
}
wait.report_document(document, state)
assert not state["errors"]
assert document["tools_source_sha"] == HEAD
assert document["failed"] is False and document["global"] is True
(HERE / "delivery-report.json").write_text(json.dumps(document, indent=2) + "\n")
report["artifact"] = {key: artifact[key] for key in (
    "id", "name", "size_in_bytes", "digest", "workflow_run", "expired", "expires_at")}
report["run"] = {key: selected[key] for key in (
    "id", "head_sha", "head_branch", "event", "path", "status", "conclusion",
    "run_attempt", "html_url")}
save()

row = next(item for item in document["modules"] if item["repository"] == MODULE)
assert row["accepted_sha"] == HEAD and row["advancement"] == "advanced"
assert row["application"] == "pushed" and row["processed"] is True and row["reasons"] == []
adopted = row["pushed_sha"]
assert re.fullmatch(r"[0-9a-f]{40}", adopted)
accepted = json.loads(run([
    "gh", "api", "repos/Hexalith/Hexalith.CiCd/git/ref/heads/delivered/" + MODULE]))
assert accepted["object"]["sha"] == HEAD
commit = json.loads(run(
    ["gh", "api", f"repos/Hexalith/{MODULE}/git/commits/{adopted}"],
    env=module_environment))
assert [item["sha"] for item in commit["parents"]] == [PREP], (
    "Inspect actual forward-only race before claiming initial adoption")
assert commit["author"]["name"] == "github-actions[bot]"
assert "from Hexalith.CiCd" in commit["message"] and HEAD[:12] in commit["message"]

clone = Path(os.environ["TMPDIR"]) / "mcpcli-adopted"
run(["gh", "repo", "clone", "Hexalith/" + MODULE, str(clone), "--", "--no-checkout"],
    cwd=Path(os.environ["TMPDIR"]), env=module_environment, timeout=180)
run(["git", "fetch", "--no-recurse-submodules", "origin", adopted, PREP],
    cwd=clone, env=module_environment)
assert run(["git", "rev-parse", adopted], cwd=clone) == adopted
assert run(["git", "rev-parse", adopted + "^"], cwd=clone) == PREP
nested = clone / "references/Hexalith.Builds"
assert not nested.exists() or not any(nested.iterdir())
gitlink = run(["git", "ls-tree", adopted, "references/Hexalith.Builds"], cwd=clone)
assert gitlink.startswith("160000 commit 0ccd12af6576a3aac601340dec7dba53e86768c3")
names = run(["git", "ls-tree", "-r", "--name-only", adopted], cwd=clone).splitlines()
assert "package.json" not in names and "package-lock.json" not in names
git = expected_state.Git(clone)
comparison = expected_state.compare_repository(
    git, repository="Hexalith/" + MODULE, ref=adopted, delivered_sha=HEAD)
comparison.require_clean()
assert comparison.delivered_sha == HEAD

old, actual = git.snapshot(PREP), git.snapshot(adopted)
assert actual.ref == commit["tree"]["sha"]
expected = perimeter.Git(ROOT).snapshot(HEAD)
builds = perimeter.Git(ROOT / "references/Hexalith.Builds")
assert builds.run("rev-parse", "v6.2.0^{commit}").decode().strip() == (
    "0ccd12af6576a3aac601340dec7dba53e86768c3")
config = json.loads(expected.read("rendered/" + MODULE + ".perimeter.json"))
plan = perimeter._Plan(config, old, expected, "rendered/" + MODULE, builds, None)
unchanged, repaired = [], []
for filename in sorted(set(old.items) | set(actual.items) | set(plan.changes)):
    if filename not in plan.changes:
        assert old.items.get(filename) == actual.items.get(filename), (
            "Foreign byte/mode/gitlink changed: " + filename)
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
        assert actual.read(filename) == wanted.data, "Actual owned bytes differ: " + filename
    repaired.append(filename)
assert actual.read("global.json") == old.read("global.json")
csharp = [filename for filename in unchanged if filename.endswith(".cs")]
assert csharp and all(
    filename in unchanged for filename in old.items if filename.endswith(".cs"))
assert not nested.exists() or not any(nested.iterdir())
workflows = [name for name in names if name.startswith(".github/workflows/")]
assert set(workflows) == {".github/workflows/ci.yml", ".github/workflows/release.yml"}
report["modules"] = {
    MODULE: {
        "adoption_sha": adopted,
        "application_sha": adopted,
        "sole_parent": PREP,
        "accepted_sha": HEAD,
        "tree": actual.ref,
        "message": commit["message"],
        "perimeter_match": True,
        "foreign_tree_preserved": True,
        "unchanged_paths": len(unchanged),
        "owned_repair_paths": repaired,
        "csharp_files_unchanged": len(csharp),
        "sdk_pin_unchanged": True,
        "original_nested_builds_empty": True,
        "legacy_workflows_absent": True,
    }
}
report.update(result="pass", completed_at=datetime.now(timezone.utc).isoformat())
save()
print(json.dumps({"result": "pass", "candidate": HEAD, "adopted": adopted,
                  "tree": actual.ref}, indent=2))
