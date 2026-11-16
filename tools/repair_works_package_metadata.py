#!/usr/bin/env python3
"""Prepare and apply the finite Works legacy metadata-authentication repair."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile

BASE = "6ad5854aa14a9950e1fbfc32d7e27953a1c4b82b"
BUILD_PATHS = {".github/workflows/domain-ci.yml": 3,
               "Github/prepare-domain-release/action.yml": 1}
WORKS_PATHS = {".github/workflows/ci.yml": 2, ".github/workflows/codeql.yml": 1,
               ".github/workflows/commitlint.yml": 1,
               ".github/workflows/dependency-review.yml": 1,
               ".github/workflows/release.yml": 3}
OWNER = Path(__file__).resolve().parents[1]


def git(root, *arguments, data=None, environment=None, check=True):
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1", GIT_OPTIONAL_LOCKS="0")
    env.update(environment or {})
    result = subprocess.run(["git", "-c", "submodule.recurse=false", "-C", str(root), *arguments],
                            input=data, capture_output=True, env=env, check=False)
    if check and result.returncode:
        raise ValueError("Git operation failed: " + " ".join(arguments[:2]))
    return result


def text(root, *arguments):
    return git(root, *arguments).stdout.decode().strip()


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def owner_identity():
    path = "tools/repair_works_package_metadata.py"
    if text(OWNER, "remote", "get-url", "origin") != "https://github.com/Hexalith/Hexalith.CiCd.git":
        raise ValueError("Materialize this repair from the official CiCd owner checkout")
    raw = Path(__file__).read_bytes()
    if git(OWNER, "show", "HEAD:" + path).stdout != raw:
        raise ValueError("Commit the exact owner materializer before preparing or applying a proposal")
    return {"owner_source": text(OWNER, "log", "-1", "--format=%H", "--", path),
            "materializer_sha256": sha256(raw)}


def authenticate_builds(root, revision):
    if not re.fullmatch(r"[0-9a-f]{40}", revision) or text(root, "rev-parse", revision + "^") != BASE:
        raise ValueError("Select the exact single compatibility commit on the frozen Builds source")
    changed = text(root, "diff", "--name-only", BASE, revision).splitlines()
    if set(changed) != set(BUILD_PATHS):
        raise ValueError("Compatibility commit changes paths outside the two approved Builds files")
    for path, count in BUILD_PATHS.items():
        if text(root, "ls-tree", BASE, "--", path).split()[:2] != ["100644", "blob"] \
                or text(root, "ls-tree", revision, "--", path).split()[:2] != ["100644", "blob"]:
            raise ValueError("Compatibility commit must preserve regular file modes")
        before = git(root, "show", BASE + ":" + path).stdout
        indent = b"          " if path.startswith(".github/") else b"        "
        needle = indent + b"PACKAGE_PREPARE_SCRIPT: ${{ inputs.package-prepare-script }}\n"
        if before.count(needle) != count:
            raise ValueError("Frozen package preparation shape differs")
        expected = before.replace(needle, needle + indent + b"GH_TOKEN: ${{ github.token }}\n")
        if git(root, "show", revision + ":" + path).stdout != expected:
            raise ValueError("Compatibility commit must contain only four scoped token additions")


def transform(path, raw, revision):
    if raw.count(BASE.encode()) != WORKS_PATHS[path]:
        raise ValueError("Works execution references differ from the reviewed frozen pin: " + path)
    result = raw.replace(BASE.encode(), revision.encode())
    if path == ".github/workflows/ci.yml":
        needle = (b"      - name: Prepare verified published Builds artifacts\n"
                  b"        run: bash scripts/prepare-platform-builds.sh\n")
        if result.count(needle) != 1:
            raise ValueError("Direct parity package preparation differs from the reviewed step")
        result = result.replace(needle, needle.replace(b"        run:",
            b"        env:\n          GH_TOKEN: ${{ github.token }}\n        run:"))
    return result


def proposal(module, builds, revision):
    authenticate_builds(builds, revision)
    origin = text(module, "remote", "get-url", "origin")
    if origin not in ("https://github.com/Hexalith/Hexalith.Works.git", "git@github.com:Hexalith/Hexalith.Works.git"):
        raise ValueError("Repair targets only the official Works repository")
    base = text(module, "rev-parse", "HEAD")
    if git(module, "cat-file", "-e", base + ":.github/hexalith-ci.json", check=False).returncode == 0:
        raise ValueError("Adopted Works must use its normal delivered perimeter")
    changes, before, after = {}, {}, {}
    for path in WORKS_PATHS:
        entry = text(module, "ls-tree", base, "--", path).split()
        if len(entry) != 4 or entry[0:2] != ["100644", "blob"]:
            raise ValueError("Repair requires the exact regular workflow file: " + path)
        raw = git(module, "show", base + ":" + path).stdout
        changed = transform(path, raw, revision)
        before[path] = [*entry[:3], sha256(raw)]
        after[path] = ["100644", "blob", blob(changed), sha256(changed)]
        changes[path] = changed
    with tempfile.TemporaryDirectory(prefix="works-auth-proposal-") as temporary:
        store = Path(temporary) / "objects.git"
        git(module, "clone", "--quiet", "--bare", "--shared", "--", str(module), str(store))
        env = {"GIT_INDEX_FILE": str(Path(temporary) / "index")}
        git(store, "read-tree", base, environment=env)
        for path, raw in changes.items():
            identity = git(store, "hash-object", "-w", "--stdin", data=raw).stdout.decode().strip()
            git(store, "update-index", "--add", "--cacheinfo", "100644," + identity + "," + path, environment=env)
        result_tree = git(store, "write-tree", environment=env).stdout.decode().strip()
        patch = git(store, "diff", "--cached", "--binary", "--full-index", "--no-ext-diff", "--no-textconv", base,
                    environment=env).stdout
    manifest = {"schema": "hexalith.works-package-metadata-auth.v1", "repository": "Hexalith.Works",
                **owner_identity(),
                "base_commit": base, "base_tree": text(module, "rev-parse", base + "^{tree}"),
                "builds_base": BASE, "builds_execution": revision, "before": before, "after": after,
                "result_tree": result_tree, "patch_sha256": sha256(patch)}
    return manifest, patch, changes


def apply(module, builds, revision, directory):
    recorded = json.loads((directory / "works-package-metadata-auth.json").read_bytes())
    manifest, patch, changes = proposal(module, builds, revision)
    if recorded != manifest or (directory / "works-package-metadata-auth.patch").read_bytes() != patch:
        raise ValueError("Owner proposal, exact source or patch identity changed; regenerate and revalidate")
    for path, entry in manifest["before"].items():
        target = module / path
        if any(parent.is_symlink() for parent in (target, *target.parents)):
            raise ValueError("Workflow target may not traverse symbolic links")
        if not stat.S_ISREG(target.stat().st_mode) or target.stat().st_mode & 0o111:
            raise ValueError("Preserve changed workflow file modes: " + path)
        if sha256(target.read_bytes()) != entry[3] or git(module, "diff", "--quiet", "--cached", "--", path,
                                                          check=False).returncode:
            raise ValueError("Preserve existing workflow edits; target differs: " + path)
    # All five targets were validated before writing. No staging, commits, refs or remote operations.
    for path, raw in changes.items():
        (module / path).write_bytes(raw)
    receipt = {"schema": "hexalith.works-package-metadata-auth.applied.v1",
               "owner_source": manifest["owner_source"], "base_commit": manifest["base_commit"],
               "result_tree": manifest["result_tree"], "patch_sha256": manifest["patch_sha256"],
               "after": {path: sha256((module / path).read_bytes()) for path in changes}}
    (directory / "works-package-metadata-auth-applied.json").write_text(json.dumps(receipt, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "apply"])
    parser.add_argument("--module", required=True, type=Path)
    parser.add_argument("--builds", required=True, type=Path)
    parser.add_argument("--builds-execution", required=True)
    parser.add_argument("--proposal", required=True, type=Path)
    args = parser.parse_args()
    module, builds, directory = args.module.resolve(), args.builds.resolve(), args.proposal.resolve()
    if args.mode == "apply":
        apply(module, builds, args.builds_execution, directory)
    else:
        manifest, patch, _ = proposal(module, builds, args.builds_execution)
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "works-package-metadata-auth.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (directory / "works-package-metadata-auth.patch").write_bytes(patch)
    print(json.dumps({"status": "prepared" if args.mode == "prepare" else "applied", "proposal": str(directory)}))


if __name__ == "__main__":
    main()
