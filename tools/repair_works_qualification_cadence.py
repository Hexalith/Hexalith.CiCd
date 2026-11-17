#!/usr/bin/env python3
"""Prepare and locally apply the finite, exact-source Works qualification cadence."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import stat
import tempfile

_spec = importlib.util.spec_from_file_location("works_metadata_owner_helpers", Path(__file__).with_name("repair_works_package_metadata.py"))
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)
blob, git, sha256, text = _helpers.blob, _helpers.git, _helpers.sha256, _helpers.text

OWNER = Path(__file__).resolve().parents[1]
BASE = "f88f99573114fb112a61163dbbd6c88f03df413c"
CI = ".github/workflows/ci.yml"
QUALIFICATION = ".github/workflows/qualification.yml"
RELEASE = ".github/workflows/release.yml"
PATHS = (CI, QUALIFICATION, RELEASE)
STEM = "works-qualification-cadence"


def owner_identity():
    """Bind a local proposal to the official owner's exact materializer, including unpublished edits."""
    if text(OWNER, "remote", "get-url", "origin") != "https://github.com/Hexalith/Hexalith.CiCd.git":
        raise ValueError("Materialize this repair from the official CiCd owner checkout")
    return {"owner_source": text(OWNER, "rev-parse", "HEAD"),
            "materializer_sha256": sha256(Path(__file__).read_bytes()),
            "helper_sha256": sha256((OWNER / "tools/repair_works_package_metadata.py").read_bytes())}


def transform(ci, release):
    """Move only the complete parity job; preserve all execution pins and unrelated job bytes."""
    start, end = b"  platform-parity:\n", b"  ci:\n"
    if ci.count(start) != 1 or ci.count(end) != 1:
        raise ValueError("Frozen Works parity/ordinary job boundaries differ")
    first, last = ci.index(start), ci.index(end)
    if last <= first:
        raise ValueError("Frozen Works parity job order differs")
    parity = ci[first:last]
    old = b"      - name: Require current main with successful exact-source push CI\n"
    if release.count(old) != 1 or release.count(b"    needs: verify-source\n") != 1:
        raise ValueError("Frozen Works pre-production release proof differs")
    qualification = (b"name: Qualification\n\non:\n  schedule:\n    - cron: '23 2 * * *'\n"
                     b"  workflow_dispatch:\n\nconcurrency:\n"
                     b"  group: qualification-${{ github.sha }}\n  cancel-in-progress: false\n\n"
                     b"permissions:\n  contents: read\n\njobs:\n" + parity)
    return {CI: ci[:first] + ci[last:], QUALIFICATION: qualification,
            RELEASE: release.replace(old, b"      - name: Require current main with exact-source CI and complete qualification\n")}


def proposal(module):
    if text(module, "remote", "get-url", "origin") not in (
            "https://github.com/Hexalith/Hexalith.Works.git", "git@github.com:Hexalith/Hexalith.Works.git"):
        raise ValueError("Cadence repair targets only the official Works repository")
    base = text(module, "rev-parse", "HEAD")
    if git(module, "merge-base", "--is-ancestor", BASE, base, check=False).returncode:
        raise ValueError("Cadence proposal requires a descendant of the approved Works baseline " + BASE)
    if git(module, "cat-file", "-e", base + ":.github/hexalith-ci.json", check=False).returncode == 0:
        raise ValueError("Adopted Works must use its normal delivered perimeter")
    before, sources = {}, {}
    for path in (CI, RELEASE):
        entry = text(module, "ls-tree", base, "--", path).split()
        if len(entry) != 4 or entry[:2] != ["100644", "blob"]:
            raise ValueError("Cadence repair requires the exact regular workflow file: " + path)
        raw = git(module, "show", base + ":" + path).stdout
        if raw != git(module, "show", BASE + ":" + path).stdout:
            raise ValueError("Owned workflow differs from the approved Works baseline: " + path)
        before[path] = [*entry[:3], sha256(raw)]
        sources[path] = raw
    if text(module, "ls-tree", base, "--", QUALIFICATION):
        raise ValueError("Preserve an existing qualification workflow")
    before[QUALIFICATION] = None
    changes = transform(sources[CI], sources[RELEASE])
    after = {path: ["100644", "blob", blob(raw), sha256(raw)] for path, raw in changes.items()}
    with tempfile.TemporaryDirectory(prefix="works-cadence-proposal-") as temporary:
        store = Path(temporary) / "objects.git"
        git(module, "clone", "--quiet", "--bare", "--shared", "--", str(module), str(store))
        env = {"GIT_INDEX_FILE": str(Path(temporary) / "index")}
        git(store, "read-tree", base, environment=env)
        for path, raw in changes.items():
            identity = git(store, "hash-object", "-w", "--stdin", data=raw).stdout.decode().strip()
            git(store, "update-index", "--add", "--cacheinfo", "100644," + identity + "," + path, environment=env)
        result_tree = text_with_environment(store, env, "write-tree")
        patch = git(store, "diff", "--cached", "--binary", "--full-index", "--unified=0", "--no-ext-diff",
                    "--no-textconv", base, environment=env).stdout
    return ({"schema": "hexalith.works-qualification-cadence.v1", "repository": "Hexalith.Works",
             **owner_identity(), "approved_baseline": BASE, "base_commit": base, "base_tree": text(module, "rev-parse", base + "^{tree}"),
             "before": before, "after": after, "result_tree": result_tree, "patch_sha256": sha256(patch)}, patch, changes)


def text_with_environment(root, environment, *arguments):
    return git(root, *arguments, environment=environment).stdout.decode().strip()


def apply(module, directory):
    recorded = json.loads((directory / (STEM + ".json")).read_bytes())
    manifest, patch, changes = proposal(module)
    if recorded != manifest or (directory / (STEM + ".patch")).read_bytes() != patch:
        raise ValueError("Owner proposal, exact source or patch identity changed; regenerate and revalidate")
    for path, entry in manifest["before"].items():
        target = module / path
        if any(parent.is_symlink() for parent in (target, *target.parents)):
            raise ValueError("Workflow target may not traverse symbolic links")
        if git(module, "diff", "--quiet", "--cached", "--", path, check=False).returncode:
            raise ValueError("Preserve staged workflow edits: " + path)
        if entry is None:
            if target.exists():
                raise ValueError("Preserve an existing qualification workflow")
            continue
        metadata = target.stat()
        if metadata.st_nlink != 1:
            raise ValueError("Preserve hard-linked workflow aliases: " + path)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o111:
            raise ValueError("Preserve changed workflow file modes: " + path)
        if sha256(target.read_bytes()) != entry[3]:
            raise ValueError("Preserve existing workflow edits: " + path)
    # Validate every target before any write. No staging, commits, refs or remote operations.
    for path, raw in changes.items():
        (module / path).write_bytes(raw)
    receipt = {"schema": "hexalith.works-qualification-cadence.applied.v1", **owner_identity(),
               "base_commit": manifest["base_commit"], "result_tree": manifest["result_tree"],
               "patch_sha256": manifest["patch_sha256"],
               "after": {path: sha256((module / path).read_bytes()) for path in changes}}
    (directory / (STEM + "-applied.json")).write_text(json.dumps(receipt, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "apply"))
    parser.add_argument("--module", required=True, type=Path)
    parser.add_argument("--proposal", required=True, type=Path)
    args = parser.parse_args()
    module, directory = args.module.resolve(), args.proposal.resolve()
    if args.mode == "apply":
        apply(module, directory)
    else:
        manifest, patch, _ = proposal(module)
        directory.mkdir(parents=True, exist_ok=False)
        (directory / (STEM + ".json")).write_text(json.dumps(manifest, indent=2) + "\n")
        (directory / (STEM + ".patch")).write_bytes(patch)
    print(json.dumps({"status": "prepared" if args.mode == "prepare" else "applied", "proposal": str(directory)}))


if __name__ == "__main__":
    main()
