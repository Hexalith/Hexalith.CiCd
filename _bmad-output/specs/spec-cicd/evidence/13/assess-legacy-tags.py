"""Read-only nuget.org and GitHub package inventory for Works version tags."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
PREFIX = "repos/Hexalith/Hexalith.Works"
PACKAGES = (
    "Hexalith.Works.Contracts",
    "Hexalith.Works.Server",
    "Hexalith.Works.Projections",
    "Hexalith.Works.Reactor",
    "Hexalith.Works.Testing",
)
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(os.environ, GH_CONFIG_DIR="/home/administrator/.config/gh", GH_PROMPT_DISABLED="1")
for key in ("GH_DEBUG", "GIT_CURL_VERBOSE"):
    environment.pop(key, None)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
report = {"recorded_at": datetime.now(timezone.utc).isoformat(), "remote_mutations": False,
          "packages": [], "github_packages": [], "assessment": []}


def nuget_versions(name):
    url = "https://api.nuget.org/v3-flatcontainer/" + name.lower() + "/index.json"
    request = urllib.request.Request(url, method="GET")
    try:
        with opener.open(request, timeout=30) as response:
            body = json.loads(response.read().decode())
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
        body = None
    versions = body.get("versions", []) if isinstance(body, dict) else []
    report["packages"].append({"package": name, "url": url, "status": status, "versions": versions})
    return versions


def gh(endpoint):
    result = subprocess.run(["gh", "api", "--method", "GET", "--include", endpoint],
                            env=environment, capture_output=True, text=True, timeout=30)
    headers, _, body = result.stdout.partition("\n\n")
    status = next((line for line in headers.splitlines() if line.startswith("HTTP/")), "")
    data = json.loads(body) if body.strip() else None
    return status, data, result.returncode, result.stderr.strip()


selection = json.loads((HERE / "app-selection-verified.json").read_text())
assert selection["verified"] and "Hexalith.Works" in selection["observation"]["selected"]
status, releases, code, error = gh(PREFIX + "/releases?per_page=100")
assert code == 0 and isinstance(releases, list)
status, tags, code, error = gh(PREFIX + "/tags?per_page=100")
assert code == 0 and isinstance(tags, list)
published = {item["tag_name"] for item in releases if not item["draft"]}
package_versions = {name: nuget_versions(name) for name in PACKAGES}
status, packages, code, error = gh(PREFIX + "/packages?package_type=nuget")
report["github_packages"].append({"endpoint": PREFIX + "/packages?package_type=nuget",
                                  "status": status, "exit": code, "error": error,
                                  "data": packages if code == 0 else None})
status, containers, code, error = gh(PREFIX + "/packages?package_type=container")
report["github_packages"].append({"endpoint": PREFIX + "/packages?package_type=container",
                                  "status": status, "exit": code, "error": error,
                                  "data": containers if code == 0 else None})
for tag in tags:
    name = tag["name"]
    sha = tag["commit"]["sha"]
    version = name.removeprefix("v")
    found = [package for package, versions in package_versions.items() if version in versions]
    if name in published:
        disposition = "preserve: GitHub release"
    elif found:
        disposition = "preserve: published artifact"
    else:
        disposition = "assessed incomplete legacy tag: no package/current registry artifact"
    report["assessment"].append({"tag": name, "sha": sha, "github_release": name in published,
                                 "published_packages": found, "disposition": disposition})
path = HERE / "legacy-tag-cleanup-assessment.json"
path.write_text(json.dumps(report, indent=2) + "\n")
path.chmod(0o600)
print(json.dumps({"tags": report["assessment"],
                  "package_counts": {name: len(versions) for name, versions in package_versions.items()}},
                 indent=2))
