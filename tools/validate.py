#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["Jinja2==3.1.6", "PyYAML==6.0.3", "jsonschema==4.26.0"]
# ///
"""Emit one delivery verdict from global checks and anonymous live-main reads."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("_cicd_check_global", Path(__file__).with_name("check_global.py"))
checks = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = checks
_spec.loader.exec_module(checks)
renderer = checks.renderer


def global_checks(project: Path) -> bool:
    """The same locked global entry point is invoked exactly once per verdict."""
    try:
        output = checks.command(["uv", "run", "--locked", "--script", "--python", sys.executable,
                                 Path(__file__).with_name("check_global.py"), "--project-root", project],
                                cwd=project, timeout=1800)
        if output:
            checks.log(output.decode("utf-8", "backslashreplace").rstrip())
        return True
    except checks.FAILURES as error:
        checks.log(f"global checks: {error}")
        return False


def anonymous_environment() -> dict:
    """Git gets no inherited repository context, credentials, helpers or config."""
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(("GIT_", "GH_", "GITHUB_", "ZIZMOR_"))
                   and key not in ("SSH_ASKPASS", "SSH_AUTH_SOCK", "CURL_HOME")}
    environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                        "GIT_CONFIG_SYSTEM": os.devnull, "GIT_TERMINAL_PROMPT": "0",
                        "GIT_ASKPASS": "/bin/false", "GIT_NO_REPLACE_OBJECTS": "1",
                        "GIT_NO_LAZY_FETCH": "1", "GIT_LFS_SKIP_SMUDGE": "1"})
    return environment


def anonymous_git(repository: Path, *arguments: str, timeout=60) -> bytes:
    environment = anonymous_environment()
    environment["GIT_CEILING_DIRECTORIES"] = str(repository.parent)
    # libcurl's default netrc lookup must not see any shared/user home directory.
    with tempfile.TemporaryDirectory(prefix="hexalith-anonymous-home-") as directory:
        environment["HOME"] = directory
        environment["XDG_CONFIG_HOME"] = directory
        return checks.command(["git", "-c", "core.hooksPath=/dev/null", "-c", "submodule.recurse=false",
                               "-c", "credential.helper=", "-c", "http.extraHeader=",
                               "-c", "http.followRedirects=false", "-c", "protocol.file.allow=never",
                               "-c", "protocol.ext.allow=never", "-C", repository, *arguments],
                              timeout=timeout, env=environment)


def clone_module(repository: str, destination: Path) -> None:
    # --no-checkout avoids filters, actions and every other module-owned command.
    # Only trees are read, so blobs are never downloaded.
    # No module .gitmodules is initialized; no local checkout is consulted.
    anonymous_git(destination.parent, "clone", "--quiet", "--depth=1", "--single-branch",
                  "--branch=main", "--no-tags", "--no-checkout", "--filter=blob:none", "--",
                  f"https://github.com/Hexalith/{repository}.git", str(destination), timeout=180)


def check_submodule(project: Path, repository: str) -> None:
    path = f"references/{repository}"
    # Git's own parser handles quoted subsection names and rejects malformed files.
    config = renderer.git(project, "config", "--null", "--blob", "HEAD:.gitmodules",
                          "--get-regexp", r"^submodule\..*\.path$")
    matches = []
    for record in config.split(b"\0"):
        if not record:
            continue
        key, value = record.decode("utf-8").split("\n", 1)
        if value == path:
            matches.append(key)
    if len(matches) != 1:
        raise checks.CheckError(f"{repository}: expected exactly one direct submodule declaration for {path}")
    url_key = matches[0].removesuffix(".path") + ".url"
    url = renderer.git(project, "config", "--blob", "HEAD:.gitmodules", "--get", url_key).decode("utf-8").strip()
    if not url:
        raise checks.CheckError(f"{repository}: committed submodule declaration requires a nonempty URL")
    entries = renderer.git(project, "ls-tree", "-z", "HEAD", "--", path).split(b"\0")
    entries = [entry for entry in entries if entry]
    if len(entries) != 1:
        raise checks.CheckError(f"{repository}: no direct submodule gitlink at candidate HEAD")
    header, raw_path = entries[0].split(b"\t", 1)
    mode, kind, _ = header.decode("ascii").split()
    if mode != "160000" or kind != "commit" or raw_path.decode("utf-8") != path:
        raise checks.CheckError(f"{repository}: candidate HEAD entry must be a mode-160000 direct submodule gitlink")


def check_module(project: Path, repository: str, contract) -> None:
    source = f"rendered/{repository}/.github/hexalith-ci.json"
    config = contract.validate("ci", renderer.safe_path(project, source).read_bytes(), source, repository)
    if config["buildsTag"] != contract.tag:
        raise checks.CheckError(f"{repository}: candidate buildsTag differs from builds-version")
    check_submodule(project, repository)
    # The sole tagged reader already enforces name disjointness and enabled
    # exclusion targets. The union includes exclusions explicitly for clarity.
    actions = sorted(set(config["hooks"]) | set(config["jobs"]) | set(config["tests"]["exclude"].values()))
    with tempfile.TemporaryDirectory(prefix="hexalith-validate-module-") as directory:
        clone = Path(directory) / "module"
        clone_module(repository, clone)
        # --branch also accepts a same-named tag; only the fetched main branch
        # may certify actions, including for a module with no enabled actions.
        branch = anonymous_git(clone, "symbolic-ref", "--quiet", "HEAD").decode().strip()
        if branch != "refs/heads/main":
            raise checks.CheckError(f"{repository}: cloned HEAD must be refs/heads/main")
        head = anonymous_git(clone, "rev-parse", "--verify", "HEAD^{commit}")
        main = anonymous_git(clone, "rev-parse", "--verify", "refs/remotes/origin/main^{commit}")
        if head != main:
            raise checks.CheckError(f"{repository}: cloned HEAD differs from fetched origin/main")
        for action in actions:
            path = f".github/actions/{action}/action.yml"
            records = anonymous_git(clone, "ls-tree", "-z", "HEAD", "--", path).split(b"\0")
            records = [record for record in records if record]
            if len(records) != 1:
                raise checks.CheckError(f"{repository}: live main is missing enabled action {path}")
            header, raw_path = records[0].split(b"\t", 1)
            mode, kind, _ = header.decode("ascii").split()
            if kind != "blob" or mode not in ("100644", "100755") or raw_path.decode("utf-8") != path:
                raise checks.CheckError(f"{repository}: live-main enabled action {path} must be a committed regular file")


def validate(project: Path) -> tuple[dict, int]:
    project = project.resolve()
    global_passed = global_checks(project)
    passed = []
    try:
        registrations = renderer.registry(project)
    except checks.FAILURES as error:
        checks.log(f"registry: {error}")
        return {"global": False, "modules": []}, 1
    all_modules = True
    try:
        with checks.selected_contract(project) as contract:
            for repository, _ in registrations:
                try:
                    check_module(project, repository, contract)
                    passed.append(repository)
                    checks.log(f"module {repository}: passed")
                except checks.FAILURES as error:
                    all_modules = False
                    checks.log(f"module {repository}: {error}")
    except checks.FAILURES as error:
        global_passed = False
        all_modules = False
        checks.log(f"selected contract/prerequisite: {error}")
    verdict = {"global": global_passed, "modules": sorted(set(passed))}
    return verdict, int(not (global_passed and all_modules))


def emit_verdict(verdict: dict) -> None:
    serialized = json.dumps(verdict, separators=(",", ":"), ensure_ascii=True)
    print(serialized, flush=True)
    if os.environ.get("GITHUB_OUTPUT"):
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
            output.write("verdict=" + serialized + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        if sys.version_info < (3, 12):
            raise checks.CheckError("Python 3.12 or later is required")
        verdict, status = validate(args.project_root)
    except checks.FAILURES as error:
        checks.log(f"validation: {error}")
        verdict, status = {"global": False, "modules": []}, 1
    try:
        emit_verdict(verdict)
    except checks.FAILURES as error:
        checks.log(f"verdict output: {error}")
        status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
