"""Apply the approved ChatBot AD-21 settings using command-local maintainer access."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPOSITORY = "repos/Hexalith/Hexalith.ChatBot"
REPOSITORY_ID = 1234748496
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("phase", choices=("protection", "environment", "settings-grants"))
phase = parser.parse_args().phase
assert not any(os.environ.get(name) for name in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_CONFIG_DIR="/home/administrator/.config/gh", GH_PROMPT_DISABLED="1")
report = {"recorded_at": datetime.now(timezone.utc).isoformat(), "phase": phase,
          "profile": environment["GH_CONFIG_DIR"], "requests": []}
destination = HERE / ("fix-github-" + phase + ".json")


def api(method, endpoint, payload=None):
    command = ["gh", "api", "--method", method, endpoint]
    if payload is not None:
        command += ["--input", "-"]
    result = subprocess.run(command, input=None if payload is None else json.dumps(payload),
                            env=environment, capture_output=True, text=True, timeout=40)
    data = json.loads(result.stdout) if result.stdout.strip() else None
    report["requests"].append({"method": method, "endpoint": endpoint,
                               "payload": payload, "exit": result.returncode,
                               "data": data, "error": result.stderr.strip()})
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(method, endpoint, "exit", result.returncode, flush=True)
    assert result.returncode == 0, "Administration failed; inspect the sanitized report"
    return data


def selected_repository_ids(endpoint):
    """Read every selection page before assessing additive organization grants."""
    identifiers = set()
    page = 1
    while True:
        selected = api("GET", endpoint + f"?per_page=100&page={page}")
        repositories = selected["repositories"]
        identifiers.update(item["id"] for item in repositories)
        if len(repositories) < 100:
            assert len(identifiers) == selected["total_count"]
            return identifiers
        page += 1


account = api("GET", "user")
assert account["login"] == "jpiquot" and account["id"] == 6775094
metadata = api("GET", REPOSITORY)
assert metadata["id"] == REPOSITORY_ID and metadata["default_branch"] == "main"
selection = json.loads((HERE / "app-selection-verification.json").read_text())
assert selection["installation_id"] == 179966090
assert "Hexalith.ChatBot" in selection["selected_repositories"]
assert selection["saved"] is True

if phase == "protection":
    rulesets = api("GET", REPOSITORY + "/rulesets?includes_parents=true")
    for name, target, include, types in (
            ("Protect main", "branch", "refs/heads/main", ("deletion", "non_fast_forward")),
            ("v tags", "tag", "refs/tags/v*", ("update", "deletion"))):
        desired = {"name": name, "target": target, "enforcement": "active", "bypass_actors": [],
                   "conditions": {"ref_name": {"include": [include], "exclude": []}},
                   "rules": [{"type": item} for item in types]}
        matches = [item for item in rulesets if item["name"] == name]
        assert len(matches) <= 1, "Ambiguous existing rulesets"
        current = api("GET", REPOSITORY + "/rulesets/" + str(matches[0]["id"])) if matches else None
        if current is None:
            current = api("POST", REPOSITORY + "/rulesets", desired)
        assert all(current[key] == value for key, value in desired.items()), "Existing protection differs"
        verified = api("GET", REPOSITORY + "/rulesets/" + str(current["id"]))
        assert all(verified[key] == value for key, value in desired.items())
elif phase == "environment":
    existing = api("GET", REPOSITORY + "/environments")
    if not any(item["name"] == "hexalith-release" for item in existing["environments"]):
        api("PUT", REPOSITORY + "/environments/hexalith-release",
            {"wait_timer": 0, "reviewers": [], "prevent_self_review": False,
             "deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True}})
    endpoint = REPOSITORY + "/environments/hexalith-release/deployment-branch-policies"
    policies = api("GET", endpoint)
    if not policies["branch_policies"]:
        api("POST", endpoint, {"name": "main", "type": "branch"})
    policies = api("GET", endpoint)
    assert policies["total_count"] == 1
    assert policies["branch_policies"][0]["name"] == "main"
    assert policies["branch_policies"][0]["type"] == "branch"
    release_environment = api("GET", REPOSITORY + "/environments/hexalith-release")
    assert release_environment["deployment_branch_policy"] == {
        "protected_branches": False, "custom_branch_policies": True}
else:
    assert api("GET", REPOSITORY + "/code-scanning/default-setup")["state"] == "not-configured"
    assert api("GET", REPOSITORY + "/automated-security-fixes")["enabled"] is False
    variables = api("GET", REPOSITORY + "/actions/variables")["variables"]
    switches = [item for item in variables if item["name"] == "HEXALITH_RELEASE_PUBLISH_ENABLED"]
    if not switches:
        api("POST", REPOSITORY + "/actions/variables",
            {"name": "HEXALITH_RELEASE_PUBLISH_ENABLED", "value": "false"})
    else:
        assert len(switches) == 1 and switches[0]["value"] in ("true", "false")
    assert api("GET", REPOSITORY + "/actions/permissions/artifact-and-log-retention")["days"] == 90
    assert metadata["security_and_analysis"]["secret_scanning_push_protection"]["status"] == "enabled"
    for namespace in ("actions", "dependabot"):
        for name in ("HEXALITH_REGISTRY_PULL_USERNAME", "HEXALITH_REGISTRY_PULL_PASSWORD"):
            endpoint = f"orgs/Hexalith/{namespace}/secrets/{name}/repositories"
            before = selected_repository_ids(endpoint)
            api("PUT", endpoint + "/" + str(REPOSITORY_ID))
            assert before | {REPOSITORY_ID} <= selected_repository_ids(endpoint)
    endpoint = "orgs/Hexalith/actions/variables/HEXALITH_NUGET_USER/repositories"
    before = selected_repository_ids(endpoint)
    api("PUT", endpoint + "/" + str(REPOSITORY_ID))
    assert before | {REPOSITORY_ID} <= selected_repository_ids(endpoint)

report["result"] = "pass"
report["completed_at"] = datetime.now(timezone.utc).isoformat()
destination.write_text(json.dumps(report, indent=2) + "\n")
