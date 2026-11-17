"""Run the normal post-adoption checker on authenticated AI.Tools main.

Clone and Builds initialization stay under TMPDIR. Nested Builds in the
persistent checkout are not initialized.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ADOPTED = "3a4a78d91b36849c4700e8bc9aae74a1b91f2fba"
BUILDS = "0ccd12af6576a3aac601340dec7dba53e86768c3"
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
tmpdir = Path(os.environ["TMPDIR"]).resolve()
clone = tmpdir / "ai-tools"
log = HERE / "standalone-checker.txt"
report = {"started_at": datetime.now(timezone.utc).isoformat(),
          "job_head": ADOPTED, "builds_sha": BUILDS, "result": "pending"}
module_env = dict(os.environ, GH_CONFIG_DIR="/home/administrator/.config/gh-module-agent",
                  GH_PROMPT_DISABLED="1")
for key in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    module_env.pop(key, None)


def run(arguments, *, cwd, env=None, check=True):
    value = subprocess.run(arguments, cwd=cwd, env=env, capture_output=True, timeout=300)
    if check and value.returncode != 0:
        raise AssertionError(value.stderr.decode() or value.stdout.decode())
    return value


run(["gh", "repo", "clone", "Hexalith/Hexalith.AI.Tools", str(clone), "--", "-n"],
    cwd=tmpdir, env=module_env)
run(["git", "checkout", "--detach", ADOPTED], cwd=clone, env=module_env)
run(["git", "submodule", "update", "--init", "references/Hexalith.Builds"], cwd=clone, env=module_env)
builds_head = run(["git", "rev-parse", "HEAD"], cwd=clone / "references/Hexalith.Builds").stdout.decode().strip()
assert builds_head == BUILDS
references_root = clone / "references/Hexalith.Builds/references"
nested = []
if references_root.exists():
    for path in sorted(references_root.iterdir()):
        contents = sorted(child.name for child in path.iterdir()) if path.is_dir() else [path.name]
        nested.append({"path": str(path.relative_to(clone)), "contents": contents})
        assert path.is_dir() and contents == [], path
checker = run(["python3", "references/Hexalith.Builds/check.py"], cwd=clone, check=False)
log.write_text(checker.stdout.decode() + checker.stderr.decode())
report.update(exit=checker.returncode, builds_head=builds_head,
              nested_builds_dirs=nested,
              log=log.name, completed_at=datetime.now(timezone.utc).isoformat(),
              result="pass" if checker.returncode == 0 else "fail")
(HERE / "standalone-checker.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"result": report["result"], "exit": checker.returncode}, indent=2))
raise SystemExit(checker.returncode)
