"""Read-only, credential-safe AD-21 discovery for story 17; no provisioning."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PREFIX = "repos/Hexalith/Hexalith.Folders"
PROFILE = "/home/administrator/.config/gh"
assert not os.environ.get("GH_TOKEN") and not os.environ.get("GITHUB_TOKEN")
environment = dict(os.environ, GH_CONFIG_DIR=PROFILE, GH_PROMPT_DISABLED="1")
for key in ("GH_DEBUG", "GIT_TRACE", "GIT_CURL_VERBOSE"):
    environment.pop(key, None)


def read(endpoint):
    result = subprocess.run(
        ["gh", "api", "--include", endpoint], env=environment,
        capture_output=True, text=True, timeout=60,
    )
    headers, _, payload = result.stdout.partition("\n\n")
    try:
        data = json.loads(payload) if payload.strip() else None
    except ValueError:
        data = {"unparsed_response": True}
    return {
        "endpoint": endpoint, "exit": result.returncode,
        "status": next((line for line in headers.splitlines() if line.startswith("HTTP/")), ""),
        "permission_metadata": [line for line in headers.splitlines()
                                if line.lower().startswith(("x-oauth-scopes:", "x-accepted-oauth-scopes:",
                                                            "x-accepted-github-permissions:"))],
        "data": data, "error": result.stderr.strip(),
    }


endpoints = [
    "user", PREFIX, PREFIX + "/branches/main", PREFIX + "/rulesets?includes_parents=true",
    PREFIX + "/environments", PREFIX + "/environments/hexalith-release",
    PREFIX + "/environments/hexalith-release/secrets",
    PREFIX + "/environments/hexalith-release/deployment-branch-policies",
    PREFIX + "/actions/permissions", PREFIX + "/actions/permissions/artifact-and-log-retention",
    PREFIX + "/actions/variables/HEXALITH_RELEASE_PUBLISH_ENABLED",
    PREFIX + "/code-scanning/default-setup", PREFIX + "/automated-security-fixes",
    PREFIX + "/code-scanning/analyses?tool_name=CodeQL&per_page=100",
    PREFIX + "/releases?per_page=100", PREFIX + "/git/matching-refs/tags/v",
    "orgs/Hexalith/installations", "user/installations/179966090/repositories",
]
for namespace in ("actions", "dependabot"):
    for name in ("HEXALITH_REGISTRY_PULL_USERNAME", "HEXALITH_REGISTRY_PULL_PASSWORD"):
        endpoints.append(f"orgs/Hexalith/{namespace}/secrets/{name}/repositories")
endpoints.append("orgs/Hexalith/actions/variables/HEXALITH_NUGET_USER/repositories")
with ThreadPoolExecutor(max_workers=4) as executor:
    responses = list(executor.map(read, endpoints))
rulesets = next(item["data"] for item in responses if item["endpoint"].endswith("rulesets?includes_parents=true"))
if isinstance(rulesets, list):
    responses.extend(read(PREFIX + "/rulesets/" + str(item["id"])) for item in rulesets)
report = {
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "scope": "Read-only story 17 planning; absence is not inferred from authorization failures.",
    "target_repository": "Hexalith/Hexalith.Folders", "administration_profile": PROFILE,
    "default_profile": os.environ.get("GH_CONFIG_DIR"),
    "token_overrides_present": {name: bool(os.environ.get(name)) for name in ("GH_TOKEN", "GITHUB_TOKEN")},
    "responses": responses,
    "external_prerequisites": {
        "nuget_policy": "unverified: no connected document session",
        "module_specific_zot_push_identity": "unverified: secret names do not prove identity scope",
    },
}
(HERE / "planning-preflight.json").write_text(json.dumps(report, indent=2) + "\n")
for response in responses:
    print(response["status"], response["endpoint"])
