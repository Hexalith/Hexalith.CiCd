"""Verify immutable-release policy on complete fresh-main module candidates."""
from pathlib import Path
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
SCRATCH = Path(os.environ["TMPDIR"])
assert SCRATCH.is_dir() and SCRATCH != Path("/tmp")
proof = json.loads((OUT / "released-policy-proof.json").read_text())
POLICY = proof["resolvedGitTagCommit"]
OWNED = [".github/workflows", ".github/dependabot.yml", ".github/hexalith-ci.json",
         "references/Hexalith.Builds", ".gitmodules", "AGENTS.md", "CLAUDE.md",
         ".github/copilot-instructions.md", ".claude", "commitlint.config.mjs", ".releaserc.json"]
report = {"policy": proof, "repositories": {}, "createdCommits": [], "pushedCommits": []}


def git(path, *args, env=None, payload=None, check=True):
    result = subprocess.run(["git", "-c", "submodule.recurse=false", "-c", "fetch.recurseSubmodules=false",
                             "-C", str(path), *args], env=env, input=payload, capture_output=True)
    if check and result.returncode:
        raise RuntimeError("Git operation refused: " + args[0])
    return result.stdout if check else result


def save():
    (OUT / "candidate-policy.json").write_text(json.dumps(report, indent=2) + "\n")


archive = git(ROOT / "references/Hexalith.Builds", "archive", POLICY, "Github/guard", "Github/lib")
policy = SCRATCH / "released-policy"
policy.mkdir()
with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
    stream.extractall(policy, filter="data")
sys.dont_write_bytecode = True
sys.path.insert(0, str(policy / "Github/lib"))
import audit_lint
import expected_state
import guard_actions
from guard_tools import Tools

tools_directory = SCRATCH / "locked-tools"
tools_directory.mkdir()
report["toolLockSha256"] = hashlib.sha256((policy / "Github/guard/package-lock.json").read_bytes()).hexdigest()
report["nodeVersion"] = subprocess.check_output(["node", "--version"], text=True).strip()
save()
try:
    tools = Tools(tools_directory)
except Exception as error:
    report["lockedTools"] = str(error)
    save()
    raise
report["lockedTools"] = "npm ci --ignore-scripts and npm audit signatures passed"
save()

for name, message in [
        ("Hexalith.Platform", "fix(test): supervise complete component fixtures\n"),
        ("Hexalith.Folders", "fix(test): bind complete Server runs to real component fixtures\n")]:
    source = ROOT / "references" / name
    head = git(source, "rev-parse", "HEAD").decode().strip()
    base = git(source, "rev-parse", "origin/main").decode().strip()
    original_index_path = Path(git(source, "rev-parse", "--path-format=absolute", "--git-path", "index").decode().strip())
    original_index = original_index_path.read_bytes()
    index = SCRATCH / (name + ".index")
    environment = dict(os.environ, GIT_INDEX_FILE=str(index))
    git(source, "read-tree", head, env=environment)
    git(source, "add", "--all", env=environment)
    captured_tree = git(source, "write-tree", env=environment).decode().strip()
    patch = git(source, "diff", "--binary", head, captured_tree)
    candidate = SCRATCH / name
    git(ROOT, "clone", "--quiet", "--shared", "--no-checkout", "--no-recurse-submodules", str(source), str(candidate))
    git(candidate, "checkout", "--quiet", "--detach", base)
    row = {"sourceHead": head, "freshBase": base, "capturedSourceTree": captured_tree}
    report["repositories"][name] = row
    applied = git(candidate, "apply", "--3way", "--index", "-", payload=patch, check=False)
    row["applyExit"] = applied.returncode
    if applied.returncode:
        row["applyDiagnostics"] = applied.stderr.decode(errors="replace")
        save()
        continue
    tree = git(candidate, "write-tree").decode().strip()
    row["candidateTree"] = tree
    row["changedPaths"] = git(candidate, "diff", "--name-only", base, tree).decode().splitlines()
    before = git(candidate, "ls-tree", "-r", base, "--", *OWNED)
    after = git(candidate, "ls-tree", "-r", tree, "--", *OWNED)
    row["ownedTreePreserved"] = before == after
    (OUT / (name + "-owned-before.txt")).write_bytes(before)
    (OUT / (name + "-owned-after.txt")).write_bytes(after)
    proposed_patch = git(candidate, "diff", "--binary", base, tree)
    (OUT / (name + ".patch")).write_bytes(proposed_patch)
    row["patchSha256"] = hashlib.sha256(proposed_patch).hexdigest()
    (OUT / (name + "-message.txt")).write_text(message)
    try:
        tools.lint_message(message, name + " proposed commit")
        row["exactMessageCommitlint"] = "passed"
    except Exception as error:
        row["exactMessageCommitlint"] = str(error)
    snapshot = expected_state.tree_snapshot(expected_state.Git(candidate), tree)
    for label, operation in [("releasedAudit", lambda: audit_lint.lint(snapshot)),
                             ("releasedActionLint", lambda: guard_actions.lint(snapshot, tools))]:
        try:
            operation()
            row[label] = "passed"
        except Exception as error:
            row[label] = str(error)
    row["sourceHeadPreserved"] = head == git(source, "rev-parse", "HEAD").decode().strip()
    row["sharedIndexPreserved"] = original_index == original_index_path.read_bytes()
    save()
    print(json.dumps({"repository": name, **row}), flush=True)

report["allPolicyPassed"] = all(row.get("ownedTreePreserved") and row.get("exactMessageCommitlint") == "passed"
    and row.get("releasedAudit") == "passed" and row.get("releasedActionLint") == "passed"
    for row in report["repositories"].values())
save()
raise SystemExit(0 if report["allPolicyPassed"] else 1)
