"""Enable AI.Tools immutable releases and inventory package-free legacy no-ops.

Run after authenticated App adoption. Uses only the command-local maintainer
profile. Never reads secret values or revokes another repository's access.
Omits unused NuGet publishing-policy and Zot publisher deletion.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
MODULE = "Hexalith.AI.Tools"
REPOSITORY_ID = 1221438803
ADOPTION_SHA = "3a4a78d91b36849c4700e8bc9aae74a1b91f2fba"
INITIAL_SHA = "180ca5692637a018c3f5547daf657e2a90bd5288"
PULL = {"HEXALITH_REGISTRY_PULL_USERNAME", "HEXALITH_REGISTRY_PULL_PASSWORD"}
LEGACY = ("NUGET_API_KEY", "HEXALITH_ZOT_USERNAME", "HEXALITH_ZOT_PASSWORD",
          "HEXALITH_ZOT_PUSH_USERNAME", "HEXALITH_ZOT_PUSH_PASSWORD",
          "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID", "SONAR_TOKEN")
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_CONFIG_DIR="/home/administrator/.config/gh", GH_PROMPT_DISABLED="1")
for key in ("GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(key, None)
path = HERE / "post-adoption-github-cleanup.json"
assert not path.exists(), "Inspect saved cleanup status before any repeated write"
report = {"started_at": datetime.now(timezone.utc).isoformat(),
          "administration_profile": environment["GH_CONFIG_DIR"],
          "module": MODULE, "repository_id": REPOSITORY_ID,
          "current_main": ADOPTION_SHA, "initial_adoption_sha": INITIAL_SHA,
          "requests": [], "result": "pending"}


def save():
    path.write_text(json.dumps(report, indent=2) + "\n")


def api(method, endpoint, *, allowed=(0,)):
    value = subprocess.run(["gh", "api", "--method", method, "--include", endpoint],
                           env=environment, capture_output=True, text=True, timeout=60)
    headers, _, body = value.stdout.partition("\n\n")
    status = next((line for line in headers.splitlines() if line.startswith("HTTP/")), "")
    document = json.loads(body) if body.strip() else None
    report["requests"].append({"at": datetime.now(timezone.utc).isoformat(), "method": method,
                               "endpoint": endpoint, "status": status, "exit": value.returncode,
                               "data": document, "error": value.stderr.strip()})
    save()
    print(method, endpoint, status, flush=True)
    assert value.returncode in allowed, value.stderr
    return document, status


user, _ = api("GET", "user")
assert (user["login"], user["id"]) == ("jpiquot", 6775094)
prefix = "repos/Hexalith/" + MODULE
assert api("GET", prefix)[0]["id"] == REPOSITORY_ID
assert api("GET", prefix + "/git/ref/heads/main")[0]["object"]["sha"] == ADOPTION_SHA
_, status = api("PUT", prefix + "/immutable-releases")
assert "204" in status
assert api("GET", prefix + "/immutable-releases")[0]["enabled"] is True
report["immutable_releases"] = True
save()

legacy_hits = {}
for service in ("actions", "dependabot"):
    inventory, _ = api("GET", f"orgs/Hexalith/{service}/secrets?per_page=100")
    assert inventory["total_count"] == len(inventory["secrets"]) < 100
    for secret in inventory["secrets"]:
        name = secret["name"]
        assert secret["visibility"] == "selected", "Broad access must be assessed before declaring absence"
        repositories, _ = api("GET", f"orgs/Hexalith/{service}/secrets/{name}/repositories?per_page=100")
        ids = {item["id"] for item in repositories["repositories"]}
        present = REPOSITORY_ID in ids
        if name in PULL:
            assert present, name + " pull grant missing after provisioning"
        elif name in LEGACY or name.startswith("HEXALITH_ZOT") or name.startswith("AZURE_"):
            assert not present, "Legacy grant now present; remove exact AI.Tools membership only after assessment"
            legacy_hits.setdefault(service, {})[name] = "absent"
        elif present and name not in PULL:
            raise AssertionError("Unexpected selected grant " + name)
report["legacy_org_secret_membership"] = legacy_hits or "no legacy family membership"
variable, _ = api("GET", "orgs/Hexalith/actions/variables/HEXALITH_NUGET_USER")
assert variable["visibility"] == "selected" and variable["value"] == "jpiquot"
variable_repos, _ = api("GET", "orgs/Hexalith/actions/variables/HEXALITH_NUGET_USER/repositories?per_page=100")
assert REPOSITORY_ID in {item["id"] for item in variable_repos["repositories"]}
for service in ("actions", "dependabot"):
    inventory, _ = api("GET", prefix + f"/{service}/secrets?per_page=100")
    assert inventory["total_count"] == 0 and inventory["secrets"] == []
production, status = api("GET", prefix + "/environments/production/secrets?per_page=100", allowed=(0, 1))
assert "404" in status or (production or {}).get("total_count", 0) == 0
current, _ = api("GET", prefix + "/environments/hexalith-release/secrets?per_page=100")
assert current["total_count"] == 0 and current["secrets"] == []
assert api("GET", prefix + "/keys?per_page=100")[0] == []
report.update(
    nuget_publishing_policy="omitted package-free; no policy created or deleted",
    zot_publisher="omitted package-free; no module identity created or revoked",
    current_release_secrets_empty=True,
    result="pass",
    completed_at=datetime.now(timezone.utc).isoformat())
save()
print(json.dumps({"result": "pass", "immutable_releases": True}, indent=2))
