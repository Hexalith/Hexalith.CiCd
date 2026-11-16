"""Read-only evidence for the fresh-main published SDK prerequisite."""
from pathlib import Path
import datetime
import json
import os
import subprocess
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT / "references/Hexalith.EventStore"), *args], text=True).strip()
request = urllib.request.Request("https://api.nuget.org/v3-flatcontainer/hexalith.eventstore.contracts/index.json", headers={"Cache-Control": "no-cache"})
with urllib.request.urlopen(request, timeout=30) as response:
    versions = json.load(response)["versions"]
stable = [v for v in versions if "-" not in v]
results = {"asOfUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "officialPackageIndex": request.full_url, "latestStable": stable[-1], "packageApiChecks": []}
for version in ("5.1.1", stable[-1]):
    command = ["dnx", "dotnet-inspect", "-y", "--", "member", "QueryResultContractAttribute",
               "--package", "Hexalith.EventStore.Contracts@" + version, "-n", "18"]
    checked = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (HERE / ("sdk-api-" + version + ".log")).write_text(checked.stdout)
    results["packageApiChecks"].append({"version": version, "command": command,
                                      "exitCode": checked.returncode, "output": checked.stdout})
path = "src/Hexalith.EventStore.Contracts/Queries/QueryResultContractAttribute.cs"
results["sourceApi"] = []
for revision in ("v5.1.1", "v5.2.0", "0be0c922883d4ea61b18e843e24472162261d934"):
    results["sourceApi"].append({"revision": git("rev-parse", revision + "^{commit}"),
                                 "containsApiSource": bool(git("ls-tree", revision, "--", path))})
profile = Path("/home/administrator/.config/gh-module-agent")
env = dict(os.environ, GH_CONFIG_DIR=str(profile))
env.pop("GITHUB_TOKEN", None)
env["GH_TOKEN"] = (profile / "token").read_text().strip()
for name, endpoint in (("releases", "repos/Hexalith/Hexalith.EventStore/releases?per_page=3"),
                       ("sourceChecks", "repos/Hexalith/Hexalith.EventStore/actions/runs?head_sha=0be0c922883d4ea61b18e843e24472162261d934&per_page=20")):
    command = ["gh", "api", endpoint]
    checked = subprocess.run(command, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if checked.returncode:
        results[name] = {"exitCode": checked.returncode, "error": checked.stderr}
    else:
        data = json.loads(checked.stdout)
        results[name] = ([{k: item.get(k) for k in ("tag_name", "draft", "prerelease", "published_at", "html_url")} for item in data]
                         if name == "releases" else [{k: item.get(k) for k in ("name", "head_sha", "status", "conclusion", "html_url")}
                                                    for item in data["workflow_runs"]])
(HERE / "sdk-prerequisite.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps({"latestStable": results["latestStable"], "packageApiChecks": [{"version": r["version"], "exitCode": r["exitCode"]} for r in results["packageApiChecks"]], "sourceApi": results["sourceApi"]}, indent=2))
