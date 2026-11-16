"""Recheck preserved Story 22 inputs using only existing local Git objects.

Run with run-with-temp. This does not execute product suites or authenticate
remote state. Its output supplements, never replaces, the earlier exact-input
test summaries and authoritative workspace publication receipt.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--cicd-root", type=Path, required=True)
args = parser.parse_args()
root = args.cicd_root.resolve()
evidence = root / "_bmad-output/specs/spec-cicd/evidence/22"
product = root.parent / "memories-story-22"
published_objects = root / "references/Hexalith.Memories"
builds = root / "references/Hexalith.Builds"
environment = dict(os.environ, GIT_NO_LAZY_FETCH="1", GIT_NO_REPLACE_OBJECTS="1",
                   GIT_OPTIONAL_LOCKS="0")


def git(repository, *arguments):
    return subprocess.check_output(["git", "-c", "core.hooksPath=/dev/null",
        "-c", "core.fsmonitor=false", "-c", "submodule.recurse=false",
        "-C", str(repository), *arguments], env=environment)


def tree(repository, revision, path):
    return git(repository, "ls-tree", "-r", "-z", revision, "--", path)


candidate = json.loads((evidence / "local-candidate.json").read_text())
baseline, final = candidate["baseline"], candidate["finalRevision"]
assert git(product, "rev-parse", "HEAD").decode().strip() == final
assert not git(product, "status", "--porcelain=v1", "--ignore-submodules=all")
bundle = evidence / candidate["bundle"]
assert bundle.stat().st_size == candidate["bundleBytes"]
assert hashlib.sha256(bundle.read_bytes()).hexdigest() == candidate["bundleSha256"]
bundle_check = subprocess.run(["git", "-C", str(product), "bundle", "verify", str(bundle)],
    env=environment, capture_output=True, text=True, check=True)

receipt_bytes = (evidence / "workspace-publication.json").read_bytes()
receipt = json.loads(receipt_bytes)
publication = next(row for row in receipt["records"]["module-push-results.json"]
                   if row["repository"] == "Hexalith.Memories")
published_base, published = publication["base"], publication["commit"]
assert publication["pushExitCode"] == 0 and not publication["qualificationComplete"]
paths = git(product, "diff", "--name-only", "-z", baseline, final).split(b"\0")
paths = [path.decode() for path in paths if path]
published_paths = git(published_objects, "diff", "--name-only", "-z",
                      published_base, published).split(b"\0")
assert {path.encode() for path in paths} == {path for path in published_paths if path}
differences = [path for path in paths
               if tree(product, final, path) != tree(published_objects, published, path)]
assert not differences, differences

protected = json.loads((evidence / "owned-and-output-preservation.json").read_text())
preservation = {}
for path in protected["checks"]:
    local_unchanged = tree(product, baseline, path) == tree(product, final, path)
    published_unchanged = (tree(published_objects, published_base, path)
                           == tree(published_objects, published, path))
    assert local_unchanged and published_unchanged, path
    preservation[path] = {"localPreparationUnchanged": local_unchanged,
                          "publishedPreparationUnchanged": published_unchanged}

overlay = "deploy/kubernetes/overlays/production/access-telemetry-disabled-patch.yaml"
blocker = json.loads((evidence / "telemetry-prerequisite-blocker.json").read_text())
overlay_hash = hashlib.sha256(git(published_objects, "show", published + ":" + overlay)).hexdigest()
assert overlay_hash == blocker["candidateWorktreeSha256"]
assert overlay_hash != blocker["expectedApprovalHash"]
tag = (root / "builds-version").read_text().strip()
release_revision = git(builds, "rev-parse", "refs/tags/" + tag + "^{commit}").decode().strip()
assert tag == "v6.0.6" and release_revision == "fdda17c0a4538b0f7c99f813c20ca24b49006530"
release_inputs = {path: hashlib.sha256(git(builds, "show", release_revision + ":" + path)).hexdigest()
                  for path in ("Github/lib/ci_environment.py", "Github/lib/ci_pipeline.py")}
assert not (root / "setup/Hexalith.Memories.yml").exists()

result = {
    "recordedAt": datetime.now(timezone.utc).isoformat(),
    "scope": "local object integrity and preservation only; no new runtime or hosted qualification",
    "cicdCommittedSource": git(root, "rev-parse", "HEAD").decode().strip(),
    "localCandidate": final,
    "localProductWorktreeClean": True,
    "bundle": {"bytes": bundle.stat().st_size, "sha256": candidate["bundleSha256"],
               "gitBundleVerifyPassed": bundle_check.returncode == 0},
    "publication": {"receiptSha256": hashlib.sha256(receipt_bytes).hexdigest(),
                    "base": published_base, "candidate": published,
                    "source": "existing authenticated publication receipt; no new remote read",
                    "changedPathCount": len(paths), "sameChangedPaths": True,
                    "allChangedPathBytesModesAndGitlinksMatchLocalCandidate": True,
                    "qualificationComplete": False},
    "ownedAndOutputPreservation": preservation,
    "selectedBuildsRelease": {"tag": tag, "localTagCommit": release_revision,
                              "sourceSha256": release_inputs,
                              "releaseAuthenticationRepeated": False},
    "telemetryPrerequisite": {"status": "still blocked", "inputSha256": overlay_hash,
                              "expectedApprovalSha256": blocker["expectedApprovalHash"]},
    "registeredOrAdopted": False,
    "remoteOperationsPerformed": False,
    "productTestsRepeated": False,
    "completeAcceptance": False,
}
output = evidence / "resumed-local-verification.json"
output.write_text(json.dumps(result, indent=2) + "\n")
print(f"PASS: bundle integrity; {len(paths)} published preparation paths match the local candidate;")
print(f"{len(preservation)} owned/output groups preserved at both bases; selected release unchanged.")
print("BLOCKED: existing telemetry approval mismatch; adoption/runtime qualification remains incomplete.")
