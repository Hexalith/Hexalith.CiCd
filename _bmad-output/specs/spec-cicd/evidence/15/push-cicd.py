"""Fast-forward the qualified CiCd registration commit to origin main."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/administrator/projects/hexalith/cicd")
BASE = "4b0a496300a7b11a2f010a97091c194ea77c7030"
HEAD = "060ab6e0812e2279e2c2ed0ebdd4c4c7bc3f1778"
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
token = subprocess.check_output(
    ["gh", "auth", "token"],
    env={**os.environ, "GH_PROMPT_DISABLED": "1"}, text=True).strip()
environment = dict(os.environ, GH_TOKEN=token, GH_PROMPT_DISABLED="1", GIT_TERMINAL_PROMPT="0")
path = HERE / "cicd-register-push.json"
assert not path.exists(), "Inspect the existing publication record before any retry"
report = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "repository": "Hexalith/Hexalith.CiCd",
    "credential": "protected cicd-agent token; no credential switch",
    "base": BASE,
    "head": HEAD,
    "push_attempted": False,
    "confirmed": False,
}


def save() -> None:
    path.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments):
    result = subprocess.run(
        arguments, cwd=ROOT, env=environment, capture_output=True, text=True, timeout=90)
    report.setdefault("operations", []).append({
        "command": arguments, "exit": result.returncode,
        "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:],
    })
    save()
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    return result.stdout.strip()


save()
assert run(["git", "rev-parse", "HEAD"]) == HEAD
assert run(["git", "rev-parse", "HEAD:references/Hexalith.McpCli"]) == "aad8894e24b28b254d1ffa69c16b7353a70452fa"
run(["git", "-c", "submodule.recurse=false", "fetch", "--no-recurse-submodules", "origin", "main"])
pre = run(["git", "rev-parse", "origin/main"])
report["prePushMain"] = pre
save()
assert pre == BASE, f"origin/main advanced to {pre}"
current = json.loads(run(["gh", "api", "repos/Hexalith/Hexalith.CiCd/git/ref/heads/main"]))
assert current["object"]["sha"] == BASE
report["push_attempted"] = True
save()
run(["git", "-c", "submodule.recurse=false", "push", "--porcelain", "origin", HEAD + ":refs/heads/main"])
current = json.loads(run(["gh", "api", "repos/Hexalith/Hexalith.CiCd/git/ref/heads/main"]))
report["readbackMain"] = current["object"]["sha"]
report["confirmed"] = current["object"]["sha"] == HEAD
report["completed_at"] = datetime.now(timezone.utc).isoformat()
save()
print(json.dumps({"repository": report["repository"], "main": current["object"]["sha"],
                  "confirmed": report["confirmed"]}, indent=2))
raise SystemExit(0 if report["confirmed"] else 1)
