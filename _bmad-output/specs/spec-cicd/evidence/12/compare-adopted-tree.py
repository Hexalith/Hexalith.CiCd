"""Compare adopted AI.Tools main to the accepted CiCd perimeter.

Clone objects stay under TMPDIR. Evidence is written beside this file.
Does not initialize nested Builds in the persistent checkout.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MODULE = "Hexalith.AI.Tools"
ADOPTED = "3a4a78d91b36849c4700e8bc9aae74a1b91f2fba"
PARENT = "180ca5692637a018c3f5547daf657e2a90bd5288"
PREP = "cfd1ebea92587cdea41b9aa2cff47358bf2f32f6"
DELIVERED = "2a5fd369b26d7648fac26be81c4129d4ba33ef0a"
assert os.environ.get("GH_CONFIG_DIR") == "/home/administrator/.config/gh-cicd-agent"
assert not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN"))
tmpdir = Path(os.environ["TMPDIR"]).resolve()
clone = tmpdir / "ai-tools"
report = {"started_at": datetime.now(timezone.utc).isoformat(),
          "adopted": ADOPTED, "parent": PARENT, "preparation": PREP,
          "delivered_sha": DELIVERED, "result": "pending"}


def run(arguments, *, cwd, env=None):
    value = subprocess.run(arguments, cwd=cwd, env=env, capture_output=True, timeout=180)
    assert value.returncode == 0, value.stderr.decode()
    return value.stdout


module_env = dict(os.environ, GH_CONFIG_DIR="/home/administrator/.config/gh-module-agent",
                  GH_PROMPT_DISABLED="1")
for key in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE"):
    module_env.pop(key, None)
run(["gh", "repo", "clone", "Hexalith/Hexalith.AI.Tools", str(clone),
     "--", "--no-checkout"], cwd=tmpdir, env=module_env)
run(["git", "fetch", "--no-recurse-submodules", "origin", ADOPTED, PARENT, PREP],
    cwd=clone, env=module_env)
assert run(["git", "rev-parse", ADOPTED], cwd=clone).decode().strip() == ADOPTED
assert run(["git", "rev-parse", f"{ADOPTED}^"], cwd=clone).decode().strip() == PARENT
assert run(["git", "rev-parse", f"{PARENT}^"], cwd=clone).decode().strip() == PREP
names = run(["git", "ls-tree", "-r", "--name-only", ADOPTED], cwd=clone).decode().splitlines()
assert "package.json" not in names and "package-lock.json" not in names
assert "commitlint.config.mjs" not in names
gitlink = run(["git", "ls-tree", ADOPTED, "references/Hexalith.Builds"], cwd=clone).decode().strip()
assert gitlink.startswith("160000 commit 0ccd12af6576a3aac601340dec7dba53e86768c3")
nested = clone / "references/Hexalith.Builds"
assert not nested.exists() or not any(nested.iterdir())
sys.path.insert(0, str(ROOT / "references/Hexalith.Builds/Github/lib"))
import expected_state
git = expected_state.Git(clone)
comparison = expected_state.compare_repository(
    git, repository="Hexalith/" + MODULE, ref=ADOPTED, delivered_sha=DELIVERED)
comparison.require_clean()
assert comparison.delivered_sha == DELIVERED
report.update(
    result="pass",
    tree=run(["git", "rev-parse", ADOPTED + "^{tree}"], cwd=clone).decode().strip(),
    perimeter_match=True,
    delivered_sha_used=comparison.delivered_sha,
    nested_builds_empty=True,
    completed_at=datetime.now(timezone.utc).isoformat())
(HERE / "adopted-tree-comparison.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"result": "pass", "tree": report["tree"]}, indent=2))
