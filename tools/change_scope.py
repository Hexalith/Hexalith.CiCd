#!/usr/bin/env python3
"""Classify committed CiCd inputs without credentials or module checkouts."""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("_scope_repository_inputs", Path(__file__).with_name("repository_inputs.py"))
inputs = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = inputs
_spec.loader.exec_module(inputs)

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "https://github.com/Hexalith/Hexalith.CiCd.git"
SHA = re.compile(r"[0-9a-f]{40}\Z")
NAME = re.compile(r"[A-Za-z0-9._-]{1,100}\Z")
SCOPES = ("none", "module", "full")
FAILURES = (OSError, ValueError, UnicodeError, subprocess.SubprocessError)


def normalize_scope(scope) -> str:
    return scope if isinstance(scope, str) and scope in SCOPES else "full"


def skip_checks(scope, event_name: str) -> int:
    """Only this exact Python decision may skip a workflow's readers/writer."""
    return int(normalize_scope(scope) == "none" and event_name in ("pull_request", "push"))


def git(project: Path, *arguments: str) -> bytes:
    """Disable inherited Git context, credential sources, redirects and hooks."""
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(("GIT_", "GH_", "GITHUB_", "ZIZMOR_"))
                   and key not in ("SSH_ASKPASS", "SSH_AUTH_SOCK", "CURL_HOME")}
    environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                        "GIT_CONFIG_SYSTEM": os.devnull, "GIT_TERMINAL_PROMPT": "0",
                        "GIT_ASKPASS": "/bin/false", "GIT_NO_REPLACE_OBJECTS": "1",
                        "GIT_NO_LAZY_FETCH": "1", "GIT_LFS_SKIP_SMUDGE": "1"})
    with tempfile.TemporaryDirectory(prefix="hexalith-scope-home-") as directory:
        environment.update(HOME=directory, XDG_CONFIG_HOME=directory)
        result = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "submodule.recurse=false",
                                 "-c", "credential.helper=", "-c", "http.extraHeader=",
                                 "-c", "http.followRedirects=false", "-c", "protocol.file.allow=never",
                                 "-c", "protocol.ext.allow=never", "-C", str(project), *arguments],
                                env=environment, capture_output=True, check=True, timeout=180)
    return result.stdout


def tree(project: Path, revision: str) -> dict:
    if SHA.fullmatch(revision) is None:
        raise ValueError("expected an exact commit identity")
    actual = git(project, "rev-parse", "--verify", revision + "^{commit}").decode("ascii").strip()
    if actual != revision:
        raise ValueError("commit identity differs")
    result = {}
    for record in git(project, "ls-tree", "-r", "-z", revision).split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        mode, kind, oid = header.decode("ascii").split()
        path = raw_path.decode("utf-8")
        relative = PurePosixPath(path)
        if (path in result or relative.is_absolute() or ".." in relative.parts
                or relative.as_posix() != path or SHA.fullmatch(oid) is None
                or (mode, kind) not in (("100644", "blob"), ("100755", "blob"),
                                        ("120000", "blob"), ("160000", "commit"))):
            raise ValueError("unknown tree entry")
        result[path] = (mode, kind, oid)
    return result


def registrations(entries: dict) -> set[str]:
    result = set()
    for path, entry in entries.items():
        relative = PurePosixPath(path)
        if relative.parent == PurePosixPath("setup") and relative.suffix == ".yml":
            name = relative.stem
            if (NAME.fullmatch(name) is None or name in (".", "..")
                    or name.casefold() == "hexalith.builds" or entry[0] not in ("100644", "100755")
                    or name.casefold() in {item.casefold() for item in result}):
                raise ValueError("ambiguous setup registry")
            result.add(name)
    return result


def compare(candidate: dict, baseline: dict) -> str:
    """Object IDs compare committed bytes; NUL-delimited paths need no rename heuristics."""
    changed = [path for path in candidate.keys() | baseline.keys() if candidate.get(path) != baseline.get(path)]
    if ".gitmodules" in changed:
        return "full"
    modules = registrations(candidate) | registrations(baseline)
    scope = "none"
    for path in changed:
        old, new = baseline.get(path), candidate.get(path)
        if (old and new and old[0] == new[0] == "160000"
                and PurePosixPath(path).parent == PurePosixPath("references")):
            continue
        # New/deleted gitlinks, symlinks and changed modes are shared inputs.
        if (any(entry and entry[0] not in ("100644", "100755") for entry in (old, new))
                or old and new and old[0] != new[0]):
            return "full"
        relative = PurePosixPath(path)
        if (path in inputs.PROSE_FILES or path.startswith(inputs.PROSE_DIRECTORIES)
                or path.startswith(inputs.EVIDENCE_ROOT + "/")
                or relative.parent == PurePosixPath("docs") and relative.suffix == ".md"):
            continue
        matches = [name for name in modules if path == f"setup/{name}.yml"
                   or path == f"rendered/{name}.perimeter.json"
                   or path.startswith((f"rendered/{name}/", f"rendered/{name}-execution/"))]
        if len(matches) != 1:
            return "full"
        scope = "module"
    return scope


def accepted_commits(project: Path) -> list[str]:
    identities = set()
    for line in git(project, "ls-remote", "--refs", REMOTE, "refs/heads/delivered/*").splitlines():
        oid, ref = line.decode("ascii").split("\t")
        prefix = "refs/heads/delivered/"
        if (SHA.fullmatch(oid) is None or not ref.startswith(prefix)
                or NAME.fullmatch(ref[len(prefix):]) is None):
            raise ValueError("malformed accepted ref")
        identities.add(oid)
    if not identities:
        raise ValueError("no accepted commit")
    return sorted(identities)


def classify(project: Path, event_name: str, pr_base: str = "") -> str:
    if event_name not in ("pull_request", "push", "schedule"):
        print("change scope: class=full fallback=event requires full", file=sys.stderr)
        return "full"
    reason = "candidate root unverified"
    baseline = ""
    try:
        project = project.resolve()
        toplevel = git(project, "rev-parse", "--show-toplevel").decode("utf-8").removesuffix("\n")
        if Path(toplevel).resolve() != project:
            raise ValueError("candidate must be the Git toplevel")
        reason = "candidate commit unreadable"
        revision = git(project, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
        if SHA.fullmatch(revision) is None:
            raise ValueError("candidate commit identity malformed")
        print(f"change scope: candidate={revision}", file=sys.stderr)
        reason = "candidate tree unreadable"
        candidate = tree(project, revision)
        results = []
        # Scratch objects never alter the candidate's shallow boundary or refs.
        with tempfile.TemporaryDirectory(prefix="hexalith-scope-baselines-") as directory:
            scratch = Path(directory)
            reason = "baseline workspace unavailable"
            git(scratch, "init", "--bare", "--quiet")
            # Discover as well as fetch in the private repository, where local
            # URL rewrites and checkout-specific HTTP configuration cannot act.
            reason = "accepted refs unreadable"
            baselines = [pr_base] if event_name == "pull_request" else accepted_commits(scratch)
            for baseline in baselines:
                reason = "baseline identity malformed"
                if SHA.fullmatch(baseline) is None:
                    raise ValueError("missing exact baseline")
                reason = "baseline fetch failed"
                git(scratch, "fetch", "--quiet", "--no-tags", "--depth=1", "--filter=blob:none",
                    REMOTE, baseline)
                reason = "baseline comparison unreadable"
                result = compare(candidate, tree(scratch, baseline))
                results.append(result)
                print(f"change scope: baseline={baseline} class={result}", file=sys.stderr)
        # Inspect every baseline before choosing: one unreadable baseline is full.
        return min(results, key=SCOPES.index)
    except FAILURES:
        identity = f" baseline={baseline}" if SHA.fullmatch(baseline) else ""
        # Reasons are fixed, bounded text; Git stderr, paths and exception
        # strings can contain credentials or hostile control characters.
        print(f"change scope:{identity} class=full fallback={reason}", file=sys.stderr)
        return "full"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    event_name = os.environ.get("CHANGE_SCOPE_EVENT", "")
    scope = normalize_scope(classify(args.project_root, event_name, os.environ.get("CHANGE_SCOPE_PR_BASE", "")))
    print(scope, flush=True)
    if os.environ.get("GITHUB_OUTPUT"):
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
            output.write(f"scope={scope}\nskip_checks={skip_checks(scope, event_name)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
