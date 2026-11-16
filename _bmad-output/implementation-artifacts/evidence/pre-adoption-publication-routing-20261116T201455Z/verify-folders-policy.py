"""Recheck the current Folders policy snapshot without modifying its index.

Run with run-with-temp. This records policy only, never publication permission.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MODULE = ROOT / "references/Hexalith.Folders"
SCRATCH = Path(os.environ["TMPDIR"])
RELEASE = "fdda17c0a4538b0f7c99f813c20ca24b49006530"
ENVIRONMENT = dict(os.environ, GIT_NO_LAZY_FETCH="1",
                   GIT_NO_REPLACE_OBJECTS="1", GIT_OPTIONAL_LOCKS="0",
                   PYTHONDONTWRITEBYTECODE="1")


def git(repository, *arguments, environment=None):
    return subprocess.check_output(
        ["git", "-c", "submodule.recurse=false", "-C", str(repository),
         *arguments], env=environment or ENVIRONMENT)


assert git(ROOT / "references/Hexalith.Builds", "rev-parse",
           "refs/tags/v6.0.6^{commit}").decode().strip() == RELEASE
builds = SCRATCH / "Builds"
subprocess.run(
    ["git", "clone", "--quiet", "--shared", "--no-checkout",
     "--no-recurse-submodules", str(ROOT / "references/Hexalith.Builds"),
     str(builds)], env=ENVIRONMENT, check=True)
git(builds, "checkout", "--detach", RELEASE)
sys.path.insert(0, str(builds / "Github/lib"))
import audit_lint
import expected_state

base = git(MODULE, "rev-parse", "HEAD").decode().strip()
index_before = git(MODULE, "ls-files", "--stage", "-z")
environment = dict(ENVIRONMENT, GIT_INDEX_FILE=str(SCRATCH / "Folders.index"))
git(MODULE, "read-tree", "--empty", environment=environment)
subprocess.run(["git", "-C", str(MODULE), "update-index", "-z", "--index-info"],
               input=index_before, env=environment, check=True)
git(MODULE, "add", "--all", environment=environment)
tree = git(MODULE, "write-tree", environment=environment).decode().strip()
snapshot = expected_state.tree_snapshot(expected_state.Git(MODULE), tree)
owned = (
    ".github/workflows", ".github/hexalith-ci.json", ".github/dependabot.yml",
    "references/Hexalith.Builds", ".gitmodules", "AGENTS.md", "CLAUDE.md",
    ".github/copilot-instructions.md", ".claude",
)
result = {
    "recordedAt": datetime.now(timezone.utc).isoformat(),
    "command": ["run-with-temp", sys.executable, str(Path(__file__).resolve())],
    "verifierSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "scope": "full released audit on one immutable proposed Git tree only",
    "snapshotBase": base,
    "proposedTree": tree,
    "buildsTag": "v6.0.6",
    "buildsCommit": RELEASE,
    "auditImplementationSha256": hashlib.sha256(
        (builds / "Github/lib/audit_lint.py").read_bytes()).hexdigest(),
    "adoptionConfigPresentInSnapshot": ".github/hexalith-ci.json" in snapshot.items,
    "conservativeWholeOwnedGroupComparisonPassed": all(
        git(MODULE, "ls-tree", "-r", "-z", base, "--", path)
        == git(MODULE, "ls-tree", "-r", "-z", tree, "--", path)
        for path in owned),
    "freshRemoteBaseVerified": False,
    "fullPreparationQualificationComplete": False,
    "publicationAuthorizedByThisReport": False,
}
try:
    audit_lint.lint(snapshot)
    result["releasedAuditLint"] = {"result": "pass", "exitCode": 0}
except expected_state.ExpectedStateError as error:
    result["releasedAuditLint"] = {
        "result": "fail", "exitCode": 1, "output": str(error)}
finally:
    result["realIndexUnchangedAtCompletion"] = (
        index_before == git(MODULE, "ls-files", "--stage", "-z"))
    (HERE / "folders-current-policy.json").write_text(
        json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
raise SystemExit(result["releasedAuditLint"]["exitCode"])
