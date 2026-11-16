"""Read-only pilot preflight; never loads or emits credential material."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
report = {"recorded_at": datetime.now(timezone.utc).isoformat(),
          "effective_GH_CONFIG_DIR": os.environ.get("GH_CONFIG_DIR"),
          "override_presence": {name: name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN")},
          "administration_profile": "/home/administrator/.config/gh", "requests": []}
assert not any(report["override_presence"].values()), "Unexpected inherited credential override"
environment = dict(os.environ, GH_CONFIG_DIR=report["administration_profile"], GH_PROMPT_DISABLED="1")
for name in ("GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(name, None)


def compact(endpoint, value):
    if "/releases?" in endpoint:
        return [{name: release.get(name) for name in (
            "id", "tag_name", "target_commitish", "draft", "prerelease", "immutable", "published_at")}
            | {"author": release.get("author", {}).get("login"),
               "marked": "hexalith-release:" in (release.get("body") or "")} for release in value]
    if endpoint == "orgs/Hexalith/installations":
        return {"total_count": value["total_count"], "installations": [
            {name: item.get(name) for name in ("id", "app_id", "app_slug", "repository_selection", "permissions")}
            for item in value["installations"]]}
    if isinstance(value, dict) and "repositories" in value:
        return {"total_count": value["total_count"], "repositories": [
            {name: item.get(name) for name in ("id", "full_name")} for item in value["repositories"]]}
    if isinstance(value, dict) and "environments" in value:
        return {"total_count": value["total_count"], "environments": [
            {name: item.get(name) for name in ("id", "name", "protection_rules", "deployment_branch_policy")}
            for item in value["environments"]]}
    return value


def get(endpoint, *, select=None):
    result = subprocess.run(["gh", "api", "--method", "GET", "--include", endpoint],
                            env=environment, text=True, capture_output=True, timeout=60)
    headers, _, body = result.stdout.partition("\n\n")
    row = {"endpoint": endpoint, "exit": result.returncode,
           "headers": [line for line in headers.splitlines() if line.startswith(
               ("HTTP/", "X-Oauth-Scopes:", "X-Accepted-Github-Permissions:"))]}
    try:
        value = json.loads(body)
        row["data"] = (select(value) if select else compact(endpoint, value)) if result.returncode == 0 else value
    except ValueError:
        row["parse_error"] = True
    if result.returncode:
        row["error"] = result.stderr.strip()
    report["requests"].append(row)
    (HERE / "recheck-preflight.json").write_text(json.dumps(report, indent=2) + "\n")
    print(endpoint, row["headers"][:1], "exit=" + str(result.returncode), flush=True)
    return row.get("data")


get("user", select=lambda value: {name: value[name] for name in ("login", "id")})
for repository in ("Hexalith.Commons", "Hexalith.PolymorphicSerializations"):
    prefix = "repos/Hexalith/" + repository
    get(prefix, select=lambda value: {name: value.get(name) for name in (
        "id", "full_name", "default_branch", "permissions", "security_and_analysis")})
    get(prefix + "/commits/main", select=lambda value: {"sha": value["sha"]})
    rules = get(prefix + "/rulesets?includes_parents=true")
    if isinstance(rules, list):
        for rule in rules:
            get(prefix + "/rulesets/" + str(rule["id"]))
    for endpoint in ("environments", "actions/variables", "actions/permissions/artifact-and-log-retention",
                     "code-scanning/default-setup", "automated-security-fixes", "immutable-releases",
                     "keys", "releases?per_page=100", "git/matching-refs/tags/v"):
        get(prefix + "/" + endpoint)
get("orgs/Hexalith/installations")
get("user/installations/179966090/repositories?per_page=100")
for namespace in ("actions", "dependabot"):
    for name in ("HEXALITH_REGISTRY_PULL_USERNAME", "HEXALITH_REGISTRY_PULL_PASSWORD"):
        get(f"orgs/Hexalith/{namespace}/secrets/{name}/repositories")
get("orgs/Hexalith/actions/variables/HEXALITH_NUGET_USER/repositories")
report["completed_at"] = datetime.now(timezone.utc).isoformat()
(HERE / "recheck-preflight.json").write_text(json.dumps(report, indent=2) + "\n")
