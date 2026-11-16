"""Prepare a nonpublishing merge snapshot without touching the user's index or files."""
from pathlib import Path
import json
import os
import subprocess

packet = Path(__file__).resolve().parent
root = packet.parents[2]
scratch = Path(os.environ["TMPDIR"])
candidate = scratch / "CiCd"

def git(directory, *args, env=None, check=True):
    return subprocess.run(["git", "-c", "submodule.recurse=false", "-C", str(directory), *args],
                          env=env, check=check, capture_output=True, text=True)

head = git(root, "rev-parse", "HEAD").stdout.strip()
remote = git(root, "rev-parse", "refs/remotes/origin/main").stdout.strip()
base = git(root, "merge-base", head, remote).stdout.strip()
source_env = dict(os.environ, GIT_INDEX_FILE=str(scratch / "source.index"))
git(root, "read-tree", head, env=source_env)
git(root, "add", "--all", env=source_env)
local_tree = git(root, "write-tree", env=source_env).stdout.strip()
git(root, "clone", "--shared", "--no-checkout", "--no-recurse-submodules", str(root), str(candidate))
git(candidate, "checkout", "--detach", remote)
merge_env = dict(os.environ, GIT_INDEX_FILE=str(candidate / ".git/candidate.index"))
git(candidate, "read-tree", "-m", base, local_tree, remote, env=merge_env)
git(candidate, "checkout-index", "--all", "--force", env=merge_env, check=False)
merged = git(candidate, "merge-index", "git-merge-one-file", "-a", env=merge_env, check=False)
conflicts = git(candidate, "diff", "--name-only", "--diff-filter=U", env=merge_env).stdout.splitlines()
resolutions = []
def blob(ref, path):
    return subprocess.check_output(["git", "-C", str(candidate), "show", ref + ":" + path])

ledger = "_bmad-output/implementation-artifacts/deferred-work.md"
if ledger in conflicts:
    common, local, published = (blob(ref, ledger) for ref in (base, local_tree, remote))
    if local.startswith(common) and published.startswith(common):
        (candidate / ledger).write_bytes(published + local[len(common):])
        git(candidate, "add", "--", ledger, env=merge_env)
        resolutions.append({"path": ledger, "resolution": "Preserved published ledger and appended the exact local suffix."})

spec = "_bmad-output/implementation-artifacts/spec-projects-g6-hosted-gate-repair.md"
if spec in conflicts and git(candidate, "cat-file", "-e", base + ":" + spec, check=False).returncode != 0:
    preserved = "_bmad-output/implementation-artifacts/fix-publication-20261116/preserved-root-inputs/spec-projects-g6-hosted-gate-repair.md.txt"
    (candidate / preserved).parent.mkdir(parents=True, exist_ok=True)
    (candidate / preserved).write_bytes(blob(local_tree, spec))
    (candidate / spec).write_bytes(blob(remote, spec))
    git(candidate, "add", "--", spec, preserved, env=merge_env)
    resolutions.append({"path": spec, "resolution": "Kept published spec at its canonical path and preserved the exact local draft separately.", "preserved": preserved})

conflicts = git(candidate, "diff", "--name-only", "--diff-filter=U", env=merge_env).stdout.splitlines()
report = {"root_head": head, "remote_main": remote, "merge_base": base,
          "local_snapshot_tree": local_tree, "merge_exit": merged.returncode,
          "conflicts": conflicts, "resolutions": resolutions, "merge_output": merged.stdout + merged.stderr,
          "original_worktree_and_index_changed": False, "commit_created": False, "push_performed": False}
if not conflicts:
    report["candidate_tree"] = git(candidate, "write-tree", env=merge_env).stdout.strip()
    patch = subprocess.check_output(["git", "-C", str(candidate), "diff", "--cached", "--binary", remote], env=merge_env)
    (packet / "cicd-merged-candidate.patch").write_bytes(patch)
    builds = candidate / "references/Hexalith.Builds"
    git(candidate, "clone", "--shared", "--no-recurse-submodules", str(root / "references/Hexalith.Builds"), str(builds))
    report["qualification"] = []
    for name, command in [
        ("render-check", ["uv", "run", "--locked", "--script", "tools/render.py", "--check"]),
        ("renderer-tests", ["uv", "run", "--locked", "--script", "tools/tests/test_render.py"]),
        ("validator-tests", ["uv", "run", "--locked", "--script", "tools/tests/test_validate.py"]),
    ]:
        with (packet / ("merged-cicd-" + name + ".log")).open("w") as output:
            result = subprocess.run(command, cwd=candidate, stdout=output, stderr=subprocess.STDOUT, timeout=240)
        report["qualification"].append({"name": name, "exit_code": result.returncode})
else:
    for index, path in enumerate(conflicts):
        output = candidate / path
        if output.is_file():
            (packet / ("cicd-conflict-" + str(index) + ".txt")).write_bytes(output.read_bytes())
(packet / "cicd-merge-preparation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"remote_main": remote, "conflicts": conflicts, "commit_created": False, "push_performed": False}))
