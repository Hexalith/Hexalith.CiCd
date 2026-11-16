"""Enable pilot immutable releases and authenticate bounded credential no-ops.

Run only after real adoption authentication. Uses the command-local maintainer
profile; never reads secret values or revokes an administrator/other module.
NuGet Trusted Publishing deletion is separately bound to reviewed UI controls.
"""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--resume-readback", action="store_true")
args = parser.parse_args()
adoption = json.loads((HERE / "authenticated-adoption.json").read_text())
assert adoption["result"] == "pass"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_CONFIG_DIR="/home/administrator/.config/gh", GH_PROMPT_DISABLED="1")
for key in ("GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(key, None)
destination = HERE / "post-adoption-github-cleanup.json"
if args.resume_readback:
    prior = json.loads(destination.read_text())
    assert all(prior["modules"][name]["immutable_releases"] is True for name in adoption["modules"])
    historical = HERE / "post-adoption-github-cleanup-initial.json"
    assert not historical.exists()
    historical.write_bytes(destination.read_bytes())
else:
    assert not destination.exists(), "Inspect saved cleanup status before any repeated write"
IDS = {"Hexalith.Commons": 952960148, "Hexalith.PolymorphicSerializations": 957156862}
PULL = {"HEXALITH_REGISTRY_PULL_USERNAME", "HEXALITH_REGISTRY_PULL_PASSWORD"}
report = {"started_at": datetime.now(timezone.utc).isoformat(), "candidate": adoption["candidate"],
          "administration_profile": environment["GH_CONFIG_DIR"], "requests": [], "modules": {}, "result": "pending"}
if args.resume_readback:
    report["prior_write_evidence"] = "post-adoption-github-cleanup-initial.json"
    report["resume_reason"] = "Correct readback expectation: preserve existing NuGet login jpiquot; package owner Hexalith is a different field. No variable was changed."
    report["additional_puts_on_resume"] = False


def save():
    destination.write_text(json.dumps(report, indent=2) + "\n")


def api(method, endpoint):
    value = subprocess.run(["gh", "api", "--method", method, "--include", endpoint],
                           env=environment, capture_output=True, text=True, timeout=60)
    headers, _, body = value.stdout.partition("\n\n")
    status = next(line for line in headers.splitlines() if line.startswith("HTTP/"))
    document = json.loads(body) if body.strip() else None
    report["requests"].append({"at": datetime.now(timezone.utc).isoformat(), "method": method,
                                 "endpoint": endpoint, "status": status, "exit": value.returncode,
                                 "data": document, "error": value.stderr})
    save()
    assert value.returncode == 0, value.stderr
    return document, status


def get(endpoint):
    return api("GET", endpoint)[0]


user = get("user")
assert (user["login"], user["id"]) == ("jpiquot", 6775094)
for name, identity in IDS.items():
    prefix = "repos/Hexalith/" + name
    assert get(prefix)["id"] == identity
    assert get(prefix + "/git/ref/heads/main")["object"]["sha"] == adoption["modules"][name]["adoption_sha"]
    if not args.resume_readback:
        _, status = api("PUT", prefix + "/immutable-releases")
        assert "204" in status
    assert get(prefix + "/immutable-releases")["enabled"] is True
    report["modules"][name] = {"immutable_releases": True, "adoption_sha": adoption["modules"][name]["adoption_sha"]}
    save()

selections = {}
for service in ("actions", "dependabot"):
    inventory = get("orgs/Hexalith/" + service + "/secrets?per_page=100")
    assert inventory["total_count"] == len(inventory["secrets"]) < 100
    selected = {}
    for secret in inventory["secrets"]:
        name = secret["name"]
        assert secret["visibility"] == "selected", "Broad access must be assessed before declaring absence"
        repositories = get("orgs/Hexalith/" + service + "/secrets/" + name + "/repositories?per_page=100")
        assert repositories["total_count"] == len(repositories["repositories"]) < 100
        identities = sorted(item["id"] for item in repositories["repositories"])
        pilot_ids = set(identities) & set(IDS.values())
        if name in PULL:
            assert pilot_ids == set(IDS.values())
        else:
            assert not pilot_ids, "Verified legacy grant now present; remove exact pilot membership only after assessment"
        selected[name] = identities
    assert PULL <= set(selected)
    selections[service] = selected
variable = get("orgs/Hexalith/actions/variables/HEXALITH_NUGET_USER")
assert variable["visibility"] == "selected" and variable["value"] == "jpiquot"
variable_repos = get("orgs/Hexalith/actions/variables/HEXALITH_NUGET_USER/repositories?per_page=100")
assert variable_repos["total_count"] == len(variable_repos["repositories"]) < 100
assert set(IDS.values()) <= {item["id"] for item in variable_repos["repositories"]}
report["org_secret_selections"] = selections
for name in IDS:
    prefix = "repos/Hexalith/" + name
    for service in ("actions", "dependabot"):
        inventory = get(prefix + "/" + service + "/secrets?per_page=100")
        assert inventory["total_count"] == 0 and inventory["secrets"] == []
    production = get(prefix + "/environments/production/secrets?per_page=100")
    assert production["total_count"] == 0 and production["secrets"] == []
    current = get(prefix + "/environments/hexalith-release/secrets?per_page=100")
    assert current["total_count"] == 2
    assert {item["name"] for item in current["secrets"]} == {"HEXALITH_REGISTRY_USERNAME", "HEXALITH_REGISTRY_PASSWORD"}
    assert get(prefix + "/keys?per_page=100") == []
    source = ROOT / "references" / name
    sha = adoption["modules"][name]["adoption_sha"]
    config = json.loads(subprocess.run(["git", "show", sha + ":.github/hexalith-ci.json"], cwd=source,
                                      capture_output=True, text=True, check=True).stdout)
    assert config["registry"] is False
    files = subprocess.run(["git", "ls-tree", "-r", "--name-only", sha], cwd=source,
                            capture_output=True, text=True, check=True).stdout.splitlines()
    container = [filename for filename in files if re.search(r"(^|/)(dockerfile(?:\..*)?|.*\.dockerfile|(?:docker-)?compose(?:\.[^/]*)?\.ya?ml)$", filename, re.I)
                 or filename.endswith(".dcproj")]
    assert not container
    prior = json.loads((HERE / "zot-pilot-automation-scope.json").read_text())["modules"][name]
    assert prior["registry_workflow_change_commits"] == prior["container_file_history_commits"] == []
    report["modules"][name].update(legacy_secret_and_deploy_key_cleanup="no-op: no pilot grant exists",
        legacy_zot_cleanup="no-op: package-only pilot has no legacy container publisher path or credential grant",
        registry_enabled=False, container_input_files=[], current_release_secret_pair_preserved=True)
    save()

# Parse in memory and retain ONLY access-control metadata. Never save ConfigMap
# contents, htpasswd material, session data or API key/hash values.
value = subprocess.run(["kubectl", "--context", "jpiquot@local", "-n", "registry-distribution", "get",
                        "configmap", "distribution-registry-config", "-o", "json"],
                       capture_output=True, text=True, check=True, timeout=60)
configmap = json.loads(value.stdout)
configuration = [json.loads(text) for text in configmap["data"].values() if text.lstrip().startswith("{")]
controls = [document["http"]["accessControl"] for document in configuration
            if "accessControl" in document.get("http", {})]
assert len(controls) == 1
prior = json.loads((HERE / "cleanup-registry-acl.json").read_text())
assert controls[0] == prior["accessControl"], "Preserve/assess concurrent registry policy changes"
report["registry_acl"] = {"resourceVersion": configmap["metadata"]["resourceVersion"], "accessControl": controls[0],
    "all_preexisting_administrator_and_other_module_access_preserved": True, "writes_performed": False,
    "global_api_key_mapping": "unverified; no global key absence or administrator automation guarantee asserted"}
report["legacy_nuget_key_disposition"] = "prior explicit disposition retained: sole visible key954800 expired; no secret/principal mapping inferred or key changed"
report.update(result="pass", completed_at=datetime.now(timezone.utc).isoformat())
save()
print(json.dumps({"result": report["result"], "modules": report["modules"]}, indent=2))
