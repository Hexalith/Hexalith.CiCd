#!/usr/bin/env python3
"""Approved Works preparation proof for the exact unadopted product candidate.

Clone and overlay under TMPDIR. Initialize only the root gitlinks this proof
needs. Do not write hexalith-ci.json, edit owned files, skip tests, or run
R1–R11. Save the record outside TMPDIR.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = Path("/home/administrator/projects/hexalith/works-story-13")
EVIDENCE = HERE / "prepare-proof.json"
OWNED_PREFIXES = (
    ".github/workflows/",
    ".github/dependabot.yml",
    ".github/hexalith-ci.json",
    ".github/copilot-instructions.md",
    "commitlint.config.mjs",
    "global.json",
    "AGENTS.md",
    "CLAUDE.md",
    ".gitmodules",
)
ALLOWED_PRODUCT = {
    ".github/actions/after-unit-tests/action.yml",
    ".github/actions/platform-parity/action.yml",
    "scripts/tests/test_release_builds_compatibility.py",
    "scripts/tests/test_release_hook_permissions.py",
    "tests/Hexalith.Works.ArchitectureTests/FitnessTests/CiCdConfigurationTests.cs",
    "tests/Hexalith.Works.ArchitectureTests/FitnessTests/PlanningEvidenceDocumentationTests.cs",
    "package.json",
    "package-lock.json",
    ".releaserc.json",
    "docs/boundary-decision-record.md",
    "docs/eventstore-api-surface-constraints.md",
    "tools/source-debug-dependencies.json",
}
STAGE_GITLINKS = (
    "references/Hexalith.Builds",
    "references/Hexalith.Platform",
    "references/Hexalith.Parties",
    "references/Hexalith.EventStore",
    "references/Hexalith.Commons",
    "references/Hexalith.PolymorphicSerializations",
)
SOURCE_IDENTITY_GITLINKS = (
    "references/Hexalith.EventStore",
    "references/Hexalith.PolymorphicSerializations",
)
DOCUMENT = {
    "schema": "hexalith.ci.v1",
    "buildsTag": "v6.2.0",
    "solution": "Hexalith.Works.slnx",
    "dapr": True,
    "browsers": False,
    "registry": False,
    "dotnetTools": False,
    "codeql": ["csharp", "python"],
    "ciTimeoutMinutes": 60,
    "additionalSdkVersion": "10.0.404",
    "hooks": ["after-unit-tests"],
    "jobs": {},
    "submodules": ["references/Hexalith.Platform", "references/Hexalith.Parties"],
    "npmWorkspaces": [],
    "tests": {
        "integration": [],
        "exclude": {},
        "minimumExpectedTests": {},
        "failSkips": True,
    },
}


def git(repository: Path, *arguments: str, capture: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=capture,
        text=True,
    )
    return result.stdout if capture else ""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def overlay_candidate(destination: Path) -> None:
    names = git(SOURCE, "diff", "--name-only", "--no-ext-diff", "HEAD").splitlines()
    names += git(SOURCE, "ls-files", "--others", "--exclude-standard").splitlines()
    for relative in names:
        source = SOURCE / relative
        target = destination / relative
        if source.is_file() and not source.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        elif not source.exists():
            target.unlink(missing_ok=True)


def candidate_tree(destination: Path) -> str:
    index = Path(os.environ["TMPDIR"]) / "candidate.index"
    environment = dict(os.environ, GIT_INDEX_FILE=str(index))
    subprocess.run(["git", "-C", str(destination), "read-tree", "HEAD"], env=environment, check=True)
    subprocess.run(["git", "-C", str(destination), "add", "-A"], env=environment, check=True)
    return subprocess.check_output(
        ["git", "-C", str(destination), "write-tree"], env=environment, text=True
    ).strip()


def owned_preservation(destination: Path, tree: str, main_sha: str, record: dict) -> None:
    raw = git(destination, "diff", "--raw", main_sha, tree)
    changed = []
    for line in raw.splitlines():
        path = line.split("\t", 1)[1]
        changed.append(path)
        if path not in ALLOWED_PRODUCT and not path.startswith(".github/actions/"):
            raise RuntimeError("owned or unexpected path changed: " + path)
        if any(path == prefix or path.startswith(prefix) for prefix in OWNED_PREFIXES):
            raise RuntimeError("owned path changed: " + path)
    builds = git(destination, "ls-tree", tree, "references/Hexalith.Builds").strip().split()
    main_builds = git(destination, "ls-tree", main_sha, "references/Hexalith.Builds").strip().split()
    if builds[:3] != main_builds[:3] or builds[0] != "160000":
        raise RuntimeError("Builds gitlink drifted")
    record["owned_paths_unchanged"] = True
    record["product_paths"] = changed
    record["builds_gitlink"] = builds[2]


def main() -> int:
    record = {
        "result": "failed",
        "harness_sha256": sha256(Path(__file__)),
        "source": str(SOURCE),
        "r1_r11": "not-run",
    }
    try:
        if "TMPDIR" not in os.environ:
            raise RuntimeError("run under run-with-temp so TMPDIR is private")
        os.environ.setdefault("GIT_TERMINAL_PROMPT", "0")
        record["source_head"] = git(SOURCE, "rev-parse", "HEAD").strip()
        record["origin_main"] = git(SOURCE, "rev-parse", "origin/main").strip()
        if record["source_head"] != record["origin_main"]:
            raise RuntimeError("product branch must start from freshly fetched origin/main")
        destination = Path(os.environ["TMPDIR"]) / "Hexalith.Works"
        subprocess.run(
            [
                "git",
                "clone",
                "--quiet",
                "--shared",
                "--no-recurse-submodules",
                str(SOURCE),
                str(destination),
            ],
            check=True,
        )
        overlay_candidate(destination)
        tree = candidate_tree(destination)
        record["candidate_tree"] = tree
        owned_preservation(destination, tree, record["origin_main"], record)

        def init_gitlinks(paths: tuple[str, ...]) -> dict[str, str]:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(destination),
                    "--literal-pathspecs",
                    "-c",
                    "protocol.file.allow=never",
                    "-c",
                    "submodule.recurse=false",
                    "submodule",
                    "update",
                    "--init",
                    "--checkout",
                    "--",
                    *paths,
                ],
                check=True,
            )
            return {path: git(destination / path, "rev-parse", "HEAD").strip() for path in paths}

        record["initialized_gitlinks"] = init_gitlinks(STAGE_GITLINKS)
        nested = sorted(str(path.relative_to(destination)) for path in destination.glob("references/*/references/*/.git"))
        if nested:
            raise RuntimeError("nested submodule initialized: " + ", ".join(nested))

        scratch = Path(os.environ["TMPDIR"]) / "dotnet"
        os.environ.update(
            NUGET_PACKAGES=str(scratch / "packages"),
            NUGET_HTTP_CACHE_PATH=str(scratch / "http"),
            NUGET_PLUGINS_CACHE_PATH=str(scratch / "plugins"),
            DOTNET_CLI_HOME=str(scratch / "cli"),
            DOTNET_CLI_UI_LANGUAGE="en-US",
            DOTNET_NOLOGO="1",
            DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1",
            MSBUILDDISABLENODEREUSE="1",
            MinVerVersionOverride="0.0.0",
        )

        builds_lib = destination / "references/Hexalith.Builds/Github/lib"
        sys.path.insert(0, str(builds_lib))
        import audit_lint
        import ci_pipeline
        import expected_state
        import guard_actions
        from guard_tools import Tools, SOURCE as GUARD_SOURCE

        snapshot = expected_state.tree_snapshot(expected_state.Git(destination), tree)
        audit_lint.lint(snapshot)
        record["released_audit_lint"] = "pass"
        tools_dir = Path(os.environ["TMPDIR"]) / "guard-tools"
        tools_dir.mkdir()
        tools = Tools(tools_dir)
        guard_actions.lint(snapshot, tools)
        record["released_action_lint"] = "pass"
        record["builds_lib_revision"] = git(destination / "references/Hexalith.Builds", "rev-parse", "HEAD").strip()
        record["guard_lock_sha256"] = sha256(GUARD_SOURCE / "package-lock.json")
        message = (HERE / "works-commit-message.txt").read_text(encoding="utf-8")
        tools.lint_message(message, "builds-policy")
        copied = tools_dir / "module-commitlint.config.mjs"
        shutil.copyfile(destination / "commitlint.config.mjs", copied)
        result = tools._process(
            [
                "node",
                str(tools_dir / "node_modules/@commitlint/cli/cli.js"),
                "--config",
                str(copied),
                "--color=false",
            ],
            "owning repository commitlint",
            message,
        )
        if result.returncode:
            raise RuntimeError("Works commitlint failed:\n" + result.stdout + result.stderr)
        record["commitlint"] = "pass"
        record["commit_message"] = message.strip()

        ci_pipeline.validate_config(DOCUMENT, repository="Hexalith/Hexalith.Works")
        prepared = ci_pipeline.PreparedConfig(
            destination,
            destination,
            DOCUMENT,
            DOCUMENT["solution"],
            "global.json",
            ("references/Hexalith.Builds", *DOCUMENT["submodules"]),
        )
        print("Package-mode restore/build", flush=True)
        ci_pipeline.restore_and_build(prepared)
        record["package_mode_build"] = "pass"
        print("Stage 3 unit/property/architecture", flush=True)
        classified = ci_pipeline.run_unit_tests(prepared, repository="Hexalith/Hexalith.Works")
        record["unit_projects"] = list(classified.unit)
        record["integration_projects"] = list(classified.integration)
        if classified.unit != (
            "tests/Hexalith.Works.ArchitectureTests/Hexalith.Works.ArchitectureTests.csproj",
            "tests/Hexalith.Works.PropertyTests/Hexalith.Works.PropertyTests.csproj",
            "tests/Hexalith.Works.UnitTests/Hexalith.Works.UnitTests.csproj",
        ):
            raise RuntimeError("unexpected stage-3 projects: " + str(classified.unit))
        if classified.integration != (
            "tests/Hexalith.Works.IntegrationTests/Hexalith.Works.IntegrationTests.csproj",
        ):
            raise RuntimeError("unexpected stage-4 projects: " + str(classified.integration))
        if classified.excluded:
            raise RuntimeError("proof must not exclude test projects")
        record["stage3"] = "pass"
        print("Stage 4 integration (no Explicit request)", flush=True)
        ci_pipeline.run_integration_tests(prepared, repository="Hexalith/Hexalith.Works")
        record["stage4"] = "pass"

        record["initialized_gitlinks"].update(init_gitlinks(SOURCE_IDENTITY_GITLINKS))
        packages = Path(os.environ["TMPDIR"]) / "works-packages"
        packages.mkdir()
        subprocess.run(
            [sys.executable, "scripts/pack-release-packages.py", str(packages), "0.0.0"],
            cwd=destination,
            check=True,
        )
        subprocess.run(
            [sys.executable, "scripts/validate-nuget-packages.py", str(packages)],
            cwd=destination,
            check=True,
        )
        subprocess.run(
            [sys.executable, "scripts/validate-consumer-package-references.py", str(packages)],
            cwd=destination,
            check=True,
        )
        record["consumer_validation"] = "pass"

        artifacts = Path(os.environ["TMPDIR"]) / "works-source-pairs"
        subprocess.run(
            [
                sys.executable,
                "scripts/verify-source-debug.py",
                "--check-only",
                "--artifacts-path",
                str(artifacts),
            ],
            cwd=destination,
            check=True,
        )
        record["source_identity"] = json.loads((artifacts / "result.json").read_text())["status"]
        if record["source_identity"] != "passed":
            raise RuntimeError("source identity failed")
        record["result"] = "pass"
        return 0
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        EVIDENCE.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, indent=2), flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
