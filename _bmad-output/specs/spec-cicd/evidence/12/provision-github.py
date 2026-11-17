"""Authorized, bounded AD-21 GitHub administration for AI.Tools story 12.

Package-free: create the main-only hexalith-release environment and normal
organization grants. Omit unused module Zot publishing credentials and
package-scoped NuGet policy. Uses only the command-local maintainer profile.
Does not read secret values, modify module files, push product refs, adopt
modules or remove legacy access.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
MODULE = "Hexalith.AI.Tools"
REPOSITORY_ID = 1221438803
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("phase", choices=("cleanup", "rulesets", "environments", "settings-grants"))
arguments = parser.parse_args()
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_CONFIG_DIR="/home/administrator/.config/gh", GH_PROMPT_DISABLED="1")
for name in ("GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(name, None)
path = HERE / ("provision-" + arguments.phase + ".json")
report = {"started_at": datetime.now(timezone.utc).isoformat(),
          "phase": arguments.phase, "module": MODULE, "repository_id": REPOSITORY_ID,
          "administration_profile": environment["GH_CONFIG_DIR"],
          "default_profile": os.environ.get("GH_CONFIG_DIR"),
          "package_free": True, "requests": []}
deadline = time.monotonic() + 1200


def save():
    path.write_text(json.dumps(report, indent=2) + "\n")


def api(method, endpoint, body=None, *, allowed=(0,)):
    assert time.monotonic() < deadline, "Provisioning deadline exceeded"
    command = ["gh", "api", "--method", method, "--include", endpoint]
    if body is not None:
        command += ["--input", "-"]
    result = subprocess.run(command, input=json.dumps(body) if body is not None else None,
                            env=environment, capture_output=True, text=True, timeout=60)
    headers, _, data = result.stdout.partition("\n\n")
    value = json.loads(data) if data.strip() else None
    status = next((line for line in headers.splitlines() if line.startswith("HTTP/")), "")
    report["requests"].append({"recorded_at": datetime.now(timezone.utc).isoformat(),
        "method": method, "endpoint": endpoint, "input": body, "exit": result.returncode,
        "status": status, "data": value, "error": result.stderr.strip()})
    save()
    print(method, endpoint, status, flush=True)
    assert result.returncode in allowed, result.stderr
    return value, status


user, _ = api("GET", "user")
assert user["login"] == "jpiquot" and user["id"] == 6775094
prefix = "repos/Hexalith/" + MODULE
metadata, _ = api("GET", prefix)
assert metadata["full_name"] == "Hexalith/" + MODULE and metadata["id"] == REPOSITORY_ID
assert metadata["default_branch"] == "main"
if arguments.phase == "cleanup":
    analyses, status = api("GET", prefix + "/code-scanning/analyses?tool_name=CodeQL&per_page=100", allowed=(0, 1))
    assert analyses == [] or ("404" in status and (analyses or {}).get("message") == "no analysis found"), (
        "Unexpected CodeQL inventory requires assessment")
    releases, _ = api("GET", prefix + "/releases?per_page=100")
    assert isinstance(releases, list) and len(releases) < 100
    assert not any(item["draft"] for item in releases), "Unexpected draft requires assessment"
    tags, _ = api("GET", prefix + "/git/matching-refs/tags/v")
    assert isinstance(tags, list) and len(tags) < 100
    release_tags = {item["tag_name"] for item in releases if not item["draft"]}
    assert all(item["ref"].removeprefix("refs/tags/") in release_tags for item in tags), (
        "Unpublished version tag requires assessment")
    report["stale_state_assessment"] = {
        "codeql": "no analysis found; no deletion target",
        "unmarked_drafts": [], "orphan_version_tags": [], "cleanup_writes": 0}
elif arguments.phase == "rulesets":
    desired = [
        {"name": "Protect main", "target": "branch", "enforcement": "active", "bypass_actors": [],
         "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
         "rules": [{"type": "deletion"}, {"type": "non_fast_forward"}]},
        {"name": "v tags", "target": "tag", "enforcement": "active", "bypass_actors": [],
         "conditions": {"ref_name": {"include": ["refs/tags/v*"], "exclude": []}},
         "rules": [{"type": "update"}, {"type": "deletion"}]},
    ]
    inventory, _ = api("GET", prefix + "/rulesets?includes_parents=true")
    assert isinstance(inventory, list)
    assert all(item["source"] == "Hexalith/" + MODULE for item in inventory), (
        "Existing protection needs assessment before changing it")
    names = {item["name"] for item in inventory}
    for definition in desired:
        matches = [item for item in inventory if item["name"] == definition["name"]]
        assert len(matches) <= 1
        if not matches:
            api("POST", prefix + "/rulesets", definition)
    actual, _ = api("GET", prefix + "/rulesets?includes_parents=true")
    assert {item["name"] for item in actual} == {item["name"] for item in desired}
    assert len(actual) == 2
    for item in actual:
        detail, _ = api("GET", prefix + "/rulesets/" + str(item["id"]))
        wanted = next(entry for entry in desired if entry["name"] == item["name"])
        assert all(detail.get(key) == value for key, value in wanted.items())
    report["exact_rulesets_verified"] = True
    report["ruleset_writes"] = 0 if names == {item["name"] for item in desired} else "created missing"
elif arguments.phase == "environments":
    environments, _ = api("GET", prefix + "/environments")
    foreign = [item["name"] for item in environments["environments"] if item["name"] != "hexalith-release"]
    if not any(item["name"] == "hexalith-release" for item in environments["environments"]):
        body = {"wait_timer": 0, "reviewers": [], "prevent_self_review": False,
                "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True}}
        api("PUT", prefix + "/environments/hexalith-release", body)
    detail, _ = api("GET", prefix + "/environments/hexalith-release")
    assert detail["deployment_branch_policy"] == {
        "protected_branches": False, "custom_branch_policies": True}
    policies, status = api("GET", prefix + "/environments/hexalith-release/deployment-branch-policies")
    existing = policies.get("branch_policies", []) if isinstance(policies, dict) else []
    if not existing:
        api("POST", prefix + "/environments/hexalith-release/deployment-branch-policies",
            {"name": "main", "type": "branch"})
    policies, _ = api("GET", prefix + "/environments/hexalith-release/deployment-branch-policies")
    assert policies["total_count"] == 1
    assert policies["branch_policies"][0]["name"] == "main"
    assert policies["branch_policies"][0]["type"] == "branch"
    secrets, _ = api("GET", prefix + "/environments/hexalith-release/secrets")
    assert secrets.get("total_count", 0) == 0 and secrets.get("secrets", []) == [], (
        "Package-free AI.Tools must not receive unused Zot publishing secrets")
    report.update(main_only_release_environment_verified=True,
                  foreign_environments=foreign,
                  zot_publishing_credentials="omitted")
else:
    setup, _ = api("GET", prefix + "/code-scanning/default-setup")
    assert setup["state"] == "not-configured"
    updates, _ = api("GET", prefix + "/automated-security-fixes", allowed=(0, 1))
    assert updates is not None and updates.get("enabled") is False
    variables, _ = api("GET", prefix + "/actions/variables")
    switches = [item for item in variables["variables"] if item["name"] == "HEXALITH_RELEASE_PUBLISH_ENABLED"]
    if not switches:
        api("POST", prefix + "/actions/variables",
            {"name": "HEXALITH_RELEASE_PUBLISH_ENABLED", "value": "true"})
    else:
        assert len(switches) == 1 and switches[0]["value"] == "true", (
            "Assess the existing publication switch before changing intent")
    switch, _ = api("GET", prefix + "/actions/variables/HEXALITH_RELEASE_PUBLISH_ENABLED")
    assert switch["value"] == "true"
    retention, _ = api("GET", prefix + "/actions/permissions/artifact-and-log-retention")
    assert retention["days"] == 90
    assert metadata["security_and_analysis"]["secret_scanning_push_protection"]["status"] == "enabled"
    for kind, names in (
            ("actions/secrets", ("HEXALITH_REGISTRY_PULL_USERNAME", "HEXALITH_REGISTRY_PULL_PASSWORD")),
            ("dependabot/secrets", ("HEXALITH_REGISTRY_PULL_USERNAME", "HEXALITH_REGISTRY_PULL_PASSWORD")),
            ("actions/variables", ("HEXALITH_NUGET_USER",)),
    ):
        for name in names:
            endpoint = f"orgs/Hexalith/{kind}/{name}"
            visibility, _ = api("GET", endpoint)
            assert visibility["visibility"] == "selected"
            before, _ = api("GET", endpoint + "/repositories")
            before_ids = {item["id"] for item in before["repositories"]}
            if REPOSITORY_ID not in before_ids:
                api("PUT", endpoint + "/repositories/" + str(REPOSITORY_ID))
            after, _ = api("GET", endpoint + "/repositories")
            after_ids = {item["id"] for item in after["repositories"]}
            assert after_ids == before_ids | {REPOSITORY_ID}
    report.update(shared_grants_verified=True, nuget_publishing_policy="omitted",
                  legacy_access_removed=False)
report["completed_at"] = datetime.now(timezone.utc).isoformat()
report["result"] = "pass"
save()
print(json.dumps({"phase": arguments.phase, "result": "pass"}, indent=2), flush=True)
