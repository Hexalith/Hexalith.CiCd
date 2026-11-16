"""Read-only Memories migration metadata; never emit credential material."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PROFILE = "/home/administrator/.config/gh"
REPORT = {
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "effective_GH_CONFIG_DIR": os.environ.get("GH_CONFIG_DIR"),
    "override_presence": {name: bool(os.environ.get(name)) for name in ("GH_TOKEN", "GITHUB_TOKEN")},
    "administration_profile": PROFILE,
    "target": "Hexalith/Hexalith.Memories",
    "requests": [],
}
assert not any(REPORT["override_presence"].values()), "Unexpected credential override"
ENV = dict(os.environ, GH_CONFIG_DIR=PROFILE, GH_PROMPT_DISABLED="1")
for name in ("GH_DEBUG", "GIT_CURL_VERBOSE"):
    ENV.pop(name, None)


def compact(endpoint, value):
    if endpoint == "user":
        return {key: value.get(key) for key in ("login", "id")}
    if endpoint == "repos/Hexalith/Hexalith.Memories":
        return {key: value.get(key) for key in ("id", "full_name", "default_branch", "permissions", "security_and_analysis")}
    if endpoint.endswith("/commits/main"):
        return {"sha": value["sha"]}
    if "/releases?" in endpoint:
        return [{key: item.get(key) for key in ("id", "tag_name", "draft", "prerelease", "immutable", "published_at")}
                | {"author": item.get("author", {}).get("login")} for item in value]
    if "/releases/tags/" in endpoint:
        return {key: value.get(key) for key in ("id", "tag_name", "target_commitish", "draft", "prerelease", "immutable", "published_at")}
    if endpoint == "orgs/Hexalith/actions/secrets?per_page=100":
        return {"total_count": value["total_count"], "secrets": [
            {key: item.get(key) for key in ("name", "visibility")} for item in value["secrets"]]}
    if endpoint == "orgs/Hexalith/installations":
        return {"total_count": value["total_count"], "installations": [
            {key: item.get(key) for key in ("id", "app_id", "app_slug", "repository_selection", "permissions")}
            for item in value["installations"]]}
    if isinstance(value, dict) and "repositories" in value:
        return {"total_count": value["total_count"], "repositories": [
            {key: item.get(key) for key in ("id", "full_name")} for item in value["repositories"]]}
    if isinstance(value, dict) and "environments" in value:
        return {"total_count": value["total_count"], "environments": [
            {key: item.get(key) for key in ("id", "name", "protection_rules", "deployment_branch_policy")}
            for item in value["environments"]]}
    if isinstance(value, dict) and "workflows" in value:
        return {"total_count": value["total_count"], "workflows": [
            {key: item.get(key) for key in ("id", "name", "path", "state")}
            for item in value["workflows"]]}
    return value


def get(endpoint):
    result = subprocess.run(["gh", "api", "--method", "GET", "--include", endpoint],
                            env=ENV, capture_output=True, text=True, timeout=45)
    headers, _, body = result.stdout.partition("\n\n")
    row = {"endpoint": endpoint, "exit": result.returncode,
           "headers": [line for line in headers.splitlines() if line.lower().startswith(
               ("http/", "x-oauth-scopes:", "x-accepted-github-permissions:"))]}
    try:
        value = json.loads(body)
        row["data"] = compact(endpoint, value) if result.returncode == 0 else value
    except ValueError:
        row["parse_error"] = True
    if result.returncode:
        row["error"] = result.stderr.strip()
    return row


BASE = "repos/Hexalith/Hexalith.Memories"
ENDPOINTS = ["user", BASE, BASE + "/commits/main"] + [BASE + "/" + suffix for suffix in (
    "rulesets?includes_parents=true", "environments", "actions/variables?per_page=100",
    "actions/permissions/artifact-and-log-retention", "code-scanning/default-setup",
    "automated-security-fixes", "immutable-releases", "releases?per_page=100",
    "actions/workflows?per_page=100", "environments/hexalith-release/secrets?per_page=100",
    "environments/hexalith-release/deployment-branch-policies?per_page=100")]
ENDPOINTS += ["orgs/Hexalith/installations", "user/installations/179966090/repositories?per_page=100",
              "orgs/Hexalith/actions/variables/HEXALITH_NUGET_USER/repositories",
              "repos/Hexalith/Hexalith.Builds/releases/tags/v6.0.6"]
ENDPOINTS += [f"orgs/Hexalith/{namespace}/secrets/{name}/repositories?per_page=100"
              for namespace in ("actions", "dependabot")
              for name in ("HEXALITH_REGISTRY_PULL_USERNAME", "HEXALITH_REGISTRY_PULL_PASSWORD")]
ENDPOINTS += [f"orgs/Hexalith/actions/secrets/{name}/repositories?per_page=100"
              for name in ("NUGET_API_KEY", "HEXALITH_ZOT_USERNAME", "HEXALITH_ZOT_API_KEY", "AZURE_APPLICATIONID",
                           "AZURE_APPLICATIONSECRET", "AZURE_SUBSCRIPTION_ID", "AZURE_TENANT_ID", "SONAR_TOKEN")]
ENDPOINTS += ["orgs/Hexalith/actions/secrets?per_page=100", BASE + "/code-scanning/analyses?per_page=100"]
with ThreadPoolExecutor(max_workers=6) as pool:
    REPORT["requests"] = list(pool.map(get, ENDPOINTS))
rules = next(row for row in REPORT["requests"] if row["endpoint"].endswith("rulesets?includes_parents=true"))
if rules["exit"] == 0:
    REPORT["requests"] += [get(BASE + "/rulesets/" + str(rule["id"])) for rule in rules["data"]]
REPORT["completed_at"] = datetime.now(timezone.utc).isoformat()
(HERE / "preflight.json").write_text(json.dumps(REPORT, indent=2) + "\n")
for row in REPORT["requests"]:
    print(row["endpoint"], "exit=" + str(row["exit"]))
