#!/usr/bin/env python3
"""Enforce the evidence policy for committed changes in a PR or main push."""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
# The evidence root is a Git pathspec, as in the delivery scope classifier.
EVIDENCE_ROOT = "_bmad-" + "output"
MAX_BYTES = 256 * 1024
SHA = re.compile(r"[0-9a-f]{40}\Z")
ZERO_SHA = "0" * 40
BLOCKED_SUFFIXES = (
    b".log", b".jsonl", b".patch", b".diff", b".nupkg", b".snupkg", b".trx", b".binlog",
    b".zip", b".gz", b".tar", b".py", b".js", b".mjs", b".ps1", b".sh",
)


def git(*args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", "-c", "credential.helper=", "-c", "http.extraHeader=", "-C", str(ROOT), *args],
        input=data, capture_output=True, check=True, timeout=180,
        env=os.environ | {"GIT_TERMINAL_PROMPT": "0", "GIT_NO_REPLACE_OBJECTS": "1", "GIT_NO_LAZY_FETCH": "1"},
    ).stdout


def baseline_for(event: str) -> str:
    fields = {"pull_request": "EVIDENCE_PR_BASE", "push": "EVIDENCE_PUSH_BEFORE"}
    if event not in fields:
        raise ValueError("expected a pull_request or push event")
    baseline = os.getenv(fields[event], "")
    if SHA.fullmatch(baseline) is None or (event != "push" and baseline == ZERO_SHA):
        raise ValueError(f"missing or invalid {event} baseline SHA")
    return baseline


def resolve_baseline(baseline: str) -> str:
    if baseline == ZERO_SHA:
        return git("hash-object", "-w", "-t", "tree", "--stdin", data=b"").decode("ascii").strip()

    revision = baseline + "^{commit}"
    try:
        commit = git("rev-parse", "--verify", revision)
    except subprocess.CalledProcessError:
        git("fetch", "--no-write-fetch-head", "--no-tags", "--no-recurse-submodules",
            "--depth=1", "--filter=blob:none", "origin", baseline)
        commit = git("rev-parse", "--verify", revision)
    if commit.decode("ascii").strip() != baseline:
        raise ValueError("baseline SHA does not identify a commit")
    return baseline


def changed_entries(baseline: str, candidate: str):
    # With rename detection disabled, a move into scope appears as an addition.
    # Deletions have no destination entry to qualify.
    raw = git("diff-tree", "--no-commit-id", "--raw", "-r", "-z", "--no-renames", "--no-abbrev",
              "--diff-filter=AMT", "--ignore-submodules=none", baseline, candidate, "--", EVIDENCE_ROOT)
    entries = iter(raw.split(b"\0")[:-1])
    for header, path in zip(entries, entries, strict=True):
        _, mode, _, oid, _ = header.split()
        yield path, mode, oid


def violations(baseline: str, candidate: str):
    by_blob = {}
    for path, mode, oid in changed_entries(baseline, candidate):
        if mode == b"100755":
            yield path, "executable Git mode 100755"
        elif mode != b"100644":
            yield path, f"non-regular Git mode {mode.decode('ascii')}"
        elif path.lower().endswith(BLOCKED_SUFFIXES):
            yield path, "raw output or executable file extension"
        else:
            by_blob.setdefault(oid, []).append(path)

    if by_blob:
        # Batch missing blob wants so a sparse checkout needs one request.
        objects = b"\n".join(by_blob) + b"\n"
        size_query = "--batch-check=%(objecttype) %(objectsize)"
        sizes = git("cat-file", size_query, data=objects).splitlines()
        missing = [oid for oid, metadata in zip(by_blob, sizes, strict=True) if metadata == oid + b" missing"]
        if missing:
            # Advertising partial commits as haves can suppress the wanted blobs.
            git("-c", "fetch.negotiationAlgorithm=noop", "fetch", "--no-write-fetch-head", "--no-tags",
                "--no-recurse-submodules", "--no-auto-maintenance", "--refmap=", "--filter=blob:none",
                "--stdin", "origin", data=b"\n".join(missing) + b"\n")
            sizes = git("cat-file", size_query, data=objects).splitlines()
        for paths, metadata in zip(by_blob.values(), sizes, strict=True):
            kind, size = metadata.split()
            if kind != b"blob":
                raise ValueError(f"unreadable Git blob at {ascii(os.fsdecode(paths[0]))}")
            size = int(size)
            if size > MAX_BYTES:
                for path in paths:
                    yield path, f"{size} bytes exceeds the {MAX_BYTES} byte limit"


def main() -> int:
    operation = "read event baseline"
    try:
        baseline = baseline_for(os.getenv("GITHUB_EVENT_NAME", ""))
        operation = "verify candidate checkout"
        candidate = os.getenv("GITHUB_SHA", "")
        head = git("rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
        if SHA.fullmatch(candidate) is None or candidate != head:
            raise ValueError("HEAD does not match the exact event SHA")
        operation = f"resolve event baseline {baseline}"
        base_treeish = resolve_baseline(baseline)
        operation = f"compare event baseline {baseline} to {candidate}"
        failed = False
        for path, reason in violations(base_treeish, candidate):
            print(f"evidence check: {ascii(os.fsdecode(path))}: {reason}", file=sys.stderr)
            failed = True
    except ValueError as error:
        print(f"evidence check: could not {operation}: {error}", file=sys.stderr)
        return 1
    except (OSError, subprocess.SubprocessError):
        print(f"evidence check: could not {operation}: Git operation failed", file=sys.stderr)
        return 1

    if failed:
        return 1
    print(f"evidence check: passed for {baseline}..{candidate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
