"""Fast-forward qualified McpCli product preparation to GitHub main."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
MODULE = Path("/home/administrator/projects/hexalith/mcpcli-story-15-product")
BASE = "97511d77aeb8fd7759bc5f14a32d2550ec5c0cb5"
HEAD = "aad8894e24b28b254d1ffa69c16b7353a70452fa"
PROTECTED = [
    ".github/workflows", ".github/dependabot.yml", ".github/hexalith-ci.json",
    ".releaserc.json", ".gitmodules", "references/Hexalith.Builds",
    "AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md",
    ".claude/settings.json", "commitlint.config.mjs",
]
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
environment = dict(
    os.environ,
    GH_CONFIG_DIR="/home/administrator/.config/gh-module-agent",
    GH_TOKEN=Path("/home/administrator/.config/gh-module-agent/token").read_text().strip(),
    GH_PROMPT_DISABLED="1",
    GIT_TERMINAL_PROMPT="0",
)
path = HERE / "mcpcli-product-push.json"
assert not path.exists(), "Inspect the existing publication record before any retry"
report = {
    "started_at": datetime.now(timezone.utc).isoformat(),
    "repository": "Hexalith/Hexalith.McpCli",
    "credential": "protected module-agent token; no credential switch",
    "base": BASE,
    "head": HEAD,
    "push_attempted": False,
    "confirmed": False,
}


def save() -> None:
    path.write_text(json.dumps(report, indent=2) + "\n")


def run(arguments, *, timeout=90):
    result = subprocess.run(
        arguments, cwd=MODULE, env=environment, capture_output=True, text=True, timeout=timeout)
    report.setdefault("operations", []).append({
        "command": arguments, "exit": result.returncode,
        "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:],
    })
    save()
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    return result.stdout.strip()


save()
assert run(["git", "status", "--porcelain", "--ignore-submodules=all"]) == ""
assert run(["git", "rev-parse", "HEAD"]) == HEAD
owned = run(["git", "diff", "--name-status", BASE, HEAD, "--", *PROTECTED])
assert owned == "", owned
run(["git", "-c", "submodule.recurse=false", "fetch", "--no-recurse-submodules", "github", "main"])
pre = run(["git", "rev-parse", "github/main"])
report["prePushMain"] = pre
save()
assert pre == BASE, f"github main advanced to {pre}; reintegrate before pushing"
current = json.loads(run(["gh", "api", "repos/Hexalith/Hexalith.McpCli/git/ref/heads/main"]))
assert current["object"]["sha"] == BASE
report["push_attempted"] = True
save()
run(["git", "-c", "submodule.recurse=false", "push", "--porcelain", "github", HEAD + ":refs/heads/main"])
current = json.loads(run(["gh", "api", "repos/Hexalith/Hexalith.McpCli/git/ref/heads/main"]))
report["readbackMain"] = current["object"]["sha"]
report["confirmed"] = current["object"]["sha"] == HEAD
report["completed_at"] = datetime.now(timezone.utc).isoformat()
save()
print(json.dumps({"repository": report["repository"], "main": current["object"]["sha"],
                  "confirmed": report["confirmed"]}, indent=2))
raise SystemExit(0 if report["confirmed"] else 1)
