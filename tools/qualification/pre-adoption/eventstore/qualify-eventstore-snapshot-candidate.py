#!/usr/bin/env python3
"""Bounded EventStore snapshot prerequisite verifier approved on 2026-11-17.

Run under run-with-temp on exact committed preparation inputs. Never pushes,
edits a source checkout, initializes nested submodules, runs Azure, or adds a
mode to check.py. The exception expires as soon as accepted adoption exists.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MODULE = "Hexalith.EventStore"
CI_PROFILE = "/home/administrator/.config/gh-cicd-agent"
MODULE_TOKEN_FILE = Path("/home/administrator/.config/gh-module-agent/token")
PREPARATION_PATHS = frozenset({'docs/guides/configuration-reference.md', 'src/Hexalith.EventStore.Client/Handlers/DomainProcessorBase.cs', 'tests/Hexalith.EventStore.FoldedSnapshotFixture/FoldedOrderCommand.cs', 'tests/Hexalith.EventStore.Server.Tests/Configuration/FoldedSnapshotActorConfigurationTests.cs', 'tests/Hexalith.EventStore.FoldedSnapshotFixture/Hexalith.EventStore.FoldedSnapshotFixture.csproj', 'src/Hexalith.EventStore.Client/Aggregates/EventStoreAggregate.cs', 'docs/guides/upgrade-path.md', 'tests/Hexalith.EventStore.FoldedSnapshotFixture/FoldedOrderAggregate.cs', 'src/Hexalith.EventStore.Server/Configuration/FoldedSnapshotActorConfigurationExtensions.cs', 'src/Hexalith.EventStore.Server/Configuration/ServiceCollectionExtensions.cs', 'tests/Hexalith.EventStore.FoldedSnapshotFixture/FoldedOrderChanged.cs', 'tests/Hexalith.EventStore.FoldedSnapshotFixture/FoldedOrderState.cs', 'src/Hexalith.EventStore.Client/Handlers/FoldedSnapshotProcessor.cs', 'tests/Hexalith.EventStore.FoldedSnapshotFixture/FoldedOrderLimits.cs', 'tests/Hexalith.EventStore.DomainService.Tests/FoldedAggregateCaptureTests.cs', 'tests/Hexalith.EventStore.DomainService.Tests/Hexalith.EventStore.DomainService.Tests.csproj', 'tests/Hexalith.EventStore.FoldedSnapshotFixture/FoldedOrderRejected.cs'})

SHA = re.compile(r"[0-9a-f]{40}")


EXPECTED_CI_ACCOUNT = {"login": "jpiquot"}
MAIN_FETCH_REFSPEC = "+refs/heads/main:refs/remotes/origin/main"
AZURE_LIVE_PROJECT = "tests/Hexalith.EventStore.PayloadProtection.AzureKeyVault.LiveTests/Hexalith.EventStore.PayloadProtection.AzureKeyVault.LiveTests.csproj"
AZURE_MANUAL_JOB = {
    "trigger": "manual",
    "runner": {"group": "payload-protection-azure-private-ephemeral", "labels": ["self-hosted", "linux", "x64"]},
    "environment": "payload-protection-azure-conformance",
    "secrets": ["PAYLOAD_AZURE_AUTHORITY_JSON", "PAYLOAD_AZURE_CUSTODY_JSON"],
    "preparation": "build-only",
    "timeoutMinutes": 45,
}


def preparation_stage_configuration(plan, builds_tag, command, module):
    """Project this EventStore preparation onto the released stages 1–3 contract.

    This is not the adoption configuration. Preserve every planned setting for
    the selected v6.1.0 validator; it rejects unsupported policy without dropping
    enabled features, timeout values or test requirements.
    """
    configuration = deepcopy(plan)
    tests = configuration["tests"]
    jobs = configuration["jobs"]
    if (set(jobs) != {"payload-azure"} or jobs.get("payload-azure") != AZURE_MANUAL_JOB
            or [project for project, route in tests["exclude"].items() if route == "payload-azure"] != [AZURE_LIVE_PROJECT]
            or "after-unit-tests" not in configuration["hooks"]):
        raise ValueError("Preparation requires the exact Azure live project, manual job and offline hook route")
    tests["exclude"][AZURE_LIVE_PROJECT] = "after-unit-tests"
    del jobs["payload-azure"]
    has_additional_sdk = "additionalSdkVersion" in configuration
    required_sdk = configuration.get("additionalSdkVersion")
    sdk_check = None
    if has_additional_sdk:
        if not isinstance(required_sdk, str) or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", required_sdk) is None:
            raise ValueError("Preparation requires an exact additional SDK version")
        observed = command(["dotnet", "--list-sdks"], module).stdout
        installed = sorted({match.group(1) for line in observed.splitlines()
                            if (match := re.fullmatch(r"([^\s]+)\s+\[[^\r\n]+\]\s*", line))})
        if required_sdk not in installed:
            raise ValueError("Required additional .NET SDK is not installed: " + required_sdk)
        sdk_check = {"required": required_sdk, "installed_versions": installed, "command": ["dotnet", "--list-sdks"]}
    configuration.update(schema="hexalith.ci.v1", buildsTag=builds_tag)
    return configuration, {"scope": "EventStore-only pre-adoption local stages 1–3; not an adoption configuration",
                           "all_planned_settings_preserved_except_declared_azure_offline_route": True,
                           "ciTimeoutMinutes": configuration["ciTimeoutMinutes"],
                           "additional_sdk_check": sdk_check,
                           "azure_offline_projection": {"project": AZURE_LIVE_PROJECT, "from": "payload-azure", "to": "after-unit-tests"},
                           "azure_service_cases": "Unexecuted and authority-owned; only the existing offline authority-schema class runs in the unit hook"}


def git_read(command, repository, *arguments, **authentication):
    # Never strip path whitespace from NUL-delimited history output.
    return command(["git", "-c", "submodule.recurse=false", *arguments], repository,
                   **authentication).stdout.rstrip("\n")


def require_preparation_paths(paths):
    protected = sorted(set(paths) - PREPARATION_PATHS)
    if protected:
        raise ValueError("Preparation changed protected paths: " + ", ".join(protected))


def verify_preparation_history(git, repository, base, head):
    edges = []
    for row in git(repository, "rev-list", "--reverse", "--parents", base + ".." + head).splitlines():
        commit, *parents = row.split()
        if not parents:
            raise ValueError("Preparation history contains a parentless introduced commit")
        for parent in parents:
            changed = [name for name in git(repository, "diff", "--name-only", "-z", parent, commit).split("\0") if name]
            require_preparation_paths(changed)
            edges.append({"parent": parent, "commit": commit, "changed_paths": changed})
    return edges


def refresh_module_main(git, repository):
    git(repository, "fetch", "--no-recurse-submodules", "origin", MAIN_FETCH_REFSPEC, module_auth=True)
    return git(repository, "rev-parse", "origin/main")


def require_unadopted(command):
    account = json.loads(command(["gh", "api", "user"], profile=CI_PROFILE).stdout)
    if {key: account.get(key) for key in EXPECTED_CI_ACCOUNT} != EXPECTED_CI_ACCOUNT:
        raise ValueError("Intended CiCd-agent account is unverified")
    repository = json.loads(command(["gh", "api", "repos/Hexalith/Hexalith.CiCd"], profile=CI_PROFILE).stdout)
    if repository.get("full_name") != "Hexalith/Hexalith.CiCd" or repository.get("default_branch") != "main":
        raise ValueError("Known CiCd repository access is unverified")
    known = json.loads(command(["gh", "api", "repos/Hexalith/Hexalith.CiCd/git/ref/heads/main"], profile=CI_PROFILE).stdout)
    if known.get("ref") != "refs/heads/main" or known.get("object", {}).get("type") != "commit" or not SHA.fullmatch(known.get("object", {}).get("sha", "")):
        raise ValueError("Known CiCd main access is unverified")
    result = command(["gh", "api", "repos/Hexalith/Hexalith.CiCd/git/ref/heads/delivered/" + MODULE], profile=CI_PROFILE, check=False)
    if result.returncode == 0:
        raise ValueError("Accepted adoption exists; this exception has expired. Run the normal module check.py")
    try:
        missing = json.loads(result.stdout)
    except ValueError:
        missing = {}
    if (missing.get("message") != "Not Found" or missing.get("status") != "404"
            or missing.get("documentation_url") != "https://docs.github.com/rest/git/refs#get-a-reference"
            or result.stderr.strip() != "gh: Not Found (HTTP 404)"):
        raise ValueError("Adoption absence is unverified; authentication and other failures never establish absence")


def run_preparation_unit_projects(ci_pipeline, prepared, results):
    """Complete the released unit projects, then preserve every failure."""
    classified = ci_pipeline.classified_projects(prepared, repository="Hexalith/" + MODULE)
    runner = ci_pipeline.test_runner(prepared.root)
    failures = []
    for project in classified.unit:
        try:
            ci_pipeline.execute_unit_projects(prepared.root, (project,), runner=runner)
        except ci_pipeline.PipelineError as error:
            result = {"project": project, "result": "failed", "exit": error.returncode, "error": str(error)}
            failures.append(result)
        else:
            result = {"project": project, "result": "passed"}
        results.append(result)
    if failures:
        raise ci_pipeline.PipelineError(
            "Unit project failures after completing all classified projects: "
            + "; ".join(value["project"] + ": " + value["error"] for value in failures),
            returncode=failures[0]["exit"])
    return classified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base")
    parser.add_argument("head")
    parser.add_argument("builds_tag")
    parser.add_argument("builds_sha")
    parser.add_argument("--module", type=Path, default=ROOT / "references" / MODULE)
    parser.add_argument("--report", type=Path, required=True, help="Durable result path outside TMPDIR.")
    args = parser.parse_args()
    report = {"approval": "Story23 approved upstream prerequisite; preserves story20 preparation obligations", "base": args.base, "head": args.head,
              "builds_tag": args.builds_tag, "builds_sha": args.builds_sha, "result": "failed",
              "started_at": datetime.now(timezone.utc).isoformat(), "push_performed": False,
              "nested_submodule_initialization": False, "azure_executed": False, "operations": []}
    report["qualificationSource"] = {
        "derivedFrom": "_bmad-output/specs/spec-cicd/evidence/20/pre-adoption-verify.py",
        "sourceRevision": "166350673f5eb57555ed4a1aaf501f8828cfa32d",
        "sourceSha256": "5786daecdec77e924d5b79586b0367f976fcc9ce9cf68f454d1132a5414db763",
        "scope": "17 exact new product paths with source ownership, released package-mode and offline product checks",
    }
    args.report = args.report.resolve()

    def save():
        args.report.write_text(json.dumps(report, indent=2) + "\n")

    def command(arguments, cwd=ROOT, *, profile=None, module_auth=False, check=True):
        environment = os.environ.copy()
        token = ""
        if profile:
            environment["GH_CONFIG_DIR"] = profile
        if module_auth:
            # The module agent has a token file, not a gh configuration profile.
            # Keep it process-local and omit environment values from all reports.
            token = MODULE_TOKEN_FILE.read_text().strip()
            if not token:
                raise ValueError("The established module-agent token is unavailable")
            for key in ("GITHUB_TOKEN", "GH_DEBUG", "GIT_CURL_VERBOSE", "GIT_TRACE", "GIT_TRACE_CURL", "GIT_TRACE_PACKET"):
                environment.pop(key, None)
            environment["GH_TOKEN"] = token
        result = subprocess.run(list(map(str, arguments)), cwd=cwd, env=environment,
                                text=True, capture_output=True, timeout=180)
        if token:
            result.stdout = result.stdout.replace(token, "<redacted-module-token>")
            result.stderr = result.stderr.replace(token, "<redacted-module-token>")
        report["operations"].append({"command": list(map(str, arguments)), "cwd": str(cwd),
                                     "profile": profile, "module_agent_process_token": module_auth, "exit": result.returncode,
                                     "stdout": result.stdout, "stderr": result.stderr})
        save()
        if check and result.returncode:
            raise RuntimeError(f"{arguments[0]} exited {result.returncode}: {result.stderr.strip()}")
        return result

    def git(repository, *arguments, profile=None, module_auth=False):
        return git_read(command, repository, *arguments, profile=profile, module_auth=module_auth)

    def require(value, message):
        if not value:
            raise ValueError(message)

    def not_adopted():
        require_unadopted(command)

    def fresh():
        not_adopted()
        require(refresh_module_main(git, args.module) == args.base, "EventStore main advanced; rebase product changes from fresh main")
        require(git(args.module, "rev-parse", "HEAD") == args.head, "EventStore HEAD changed")
        require(not git(args.module, "status", "--porcelain", "--ignore-submodules=all"), "Commit every preparation input before verifying")

    def export(repository, revision, destination):
        destination.mkdir(parents=True)
        archive = destination.parent / (destination.name + ".tar")
        with archive.open("wb") as output:
            subprocess.run(["git", "-c", "submodule.recurse=false", "archive", revision], cwd=repository, stdout=output, check=True)
        with tarfile.open(archive) as payload:
            payload.extractall(destination, filter="data")
        archive.unlink()

    try:
        require(all(SHA.fullmatch(value) for value in (args.base, args.head, args.builds_sha)), "Exact lowercase commit identities are required")
        require(re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", args.builds_tag), "An exact stable Builds release tag is required")
        require(not any(key in os.environ for key in ("GH_TOKEN", "GITHUB_TOKEN")), "Remove inherited token overrides; use the designated profiles")
        scratch = Path(os.environ["TMPDIR"]).resolve()
        require(not args.report.is_relative_to(scratch), "Save the report outside disposable TMPDIR")
        args.module = args.module.resolve()
        # Local dirtiness fails before any remote operation.
        require(git(args.module, "rev-parse", "HEAD") == args.head, "EventStore HEAD differs from candidate")
        require(not git(args.module, "status", "--porcelain", "--ignore-submodules=all"), "Commit every preparation input before verifying")
        require(git(args.module, "rev-parse", "--is-shallow-repository") == "false", "Full module history is required")
        require(git(args.module, "config", "--get", "remote.origin.url").removesuffix(".git") in
                ("https://github.com/Hexalith/Hexalith.EventStore", "git@github.com:Hexalith/Hexalith.EventStore"), "Wrong module origin")
        git(args.module, "merge-base", "--is-ancestor", args.base, args.head)
        fresh()
        builds = ROOT / "references/Hexalith.Builds"
        release = json.loads(command(["gh", "api", "repos/Hexalith/Hexalith.Builds/releases/tags/" + args.builds_tag], profile=CI_PROFILE).stdout)
        require(release.get("tag_name") == args.builds_tag and release.get("draft") is False and release.get("immutable") is True
                and release.get("prerelease") is False and release.get("author", {}).get("login") == "github-actions[bot]",
                "Builds release must be published, immutable, stable and authored by github-actions[bot]")
        git(builds, "fetch", "--no-recurse-submodules", "origin", "tag", args.builds_tag, profile=CI_PROFILE)
        require(git(builds, "rev-parse", args.builds_tag + "^{commit}") == args.builds_sha, "Builds tag/source identity mismatch")
        git(builds, "fetch", "--no-recurse-submodules", "origin", MAIN_FETCH_REFSPEC, profile=CI_PROFILE)
        git(builds, "merge-base", "--is-ancestor", args.builds_sha, "origin/main")
        workspace = scratch / "eventstore-preparation"
        workspace.mkdir()
        trusted = workspace / "shared-builds"
        export(builds, args.builds_sha, trusted)
        sys.path.insert(0, str(trusted / "Github/lib"))
        import audit_lint
        import ci_pipeline
        import expected_state
        import guard_actions
        import guard_commitlint
        from guard_tools import Tools
        source = expected_state.Git(args.module)
        before, candidate = (expected_state.tree_snapshot(source, sha) for sha in (args.base, args.head))
        require(".github/hexalith-ci.json" not in before.items and ".github/hexalith-ci.json" not in candidate.items,
                "An adopted CI configuration is present; use normal check.py")
        changed = sorted(path for path in before.items.keys() | candidate.items.keys() if before.items.get(path) != candidate.items.get(path))
        require(bool(changed), "The preparation candidate has no product changes")
        require_preparation_paths(changed)
        report["preparation_history_edges"] = verify_preparation_history(git, args.module, args.base, args.head)
        unchanged = []
        for path in sorted((before.items.keys() | candidate.items.keys()) - set(changed)):
            old, new = before.items.get(path), candidate.items.get(path)
            require(old == new and old is not None, "Unchanged tree identity differs: " + path)
            record = {"path": path, "mode": old.mode, "oid": old.oid}
            if old.mode != "160000":
                require(before.read(path) == candidate.read(path), "Unchanged bytes differ: " + path)
                record["sha256"] = hashlib.sha256(before.read(path)).hexdigest()
            unchanged.append(record)
        # Every instruction/settings file and .gitmodules is compared in full,
        # which is stronger than comparing only its owned block/entries/section.
        report.update(changed_paths=changed, complete_unchanged_byte_mode_gitlink_records=unchanged)
        audit_lint.lint(candidate)
        tool_directory = workspace / "policy-tools"
        tool_directory.mkdir()
        tools = Tools(tool_directory)
        guard_actions.lint(candidate, tools)
        guard_commitlint.lint(source, tools, event_name="push", event={}, frozen_head=args.head, commit_range=(args.base, args.head))
        lock = json.loads(before.read("package-lock.json"))
        for package in ("@commitlint/cli", "@commitlint/config-conventional"):
            require(lock["packages"]["node_modules/" + package]["version"] == "21.2.4",
                    "The owning legacy commitlint version differs from the shared integrity-locked CLI")
        owning_policy = tool_directory / "eventstore.commitlint.config.mjs"
        owning_policy.write_bytes(before.read("commitlint.config.mjs"))
        for sha in git(args.module, "rev-list", "--reverse", args.base + ".." + args.head).splitlines():
            checked = subprocess.run(["node", str(tool_directory / "node_modules/@commitlint/cli/cli.js"),
                                      "--config", str(owning_policy), "--color=false"], cwd=tool_directory,
                                     env=tools.environment, input=guard_commitlint.message(source, sha),
                                     text=True, capture_output=True, timeout=120)
            require(checked.returncode == 0, "Owning commitlint policy failed: " + checked.stdout + checked.stderr)
        report["policy_and_commit_validation"] = "passed"
        save()
        module = workspace / MODULE
        command(["git", "-c", "submodule.recurse=false", "clone", "--no-hardlinks", "--no-checkout", "--no-recurse-submodules", args.module, module])
        git(module, "checkout", "--detach", args.head)
        # A local clone records its filesystem source as origin. Product source
        # identity checks must see the already verified original repository URL.
        git(module, "remote", "set-url", "origin", git(args.module, "config", "--get", "remote.origin.url"))
        # Export only already available direct repositories, never initialize
        # the module's nested gitlinks. Missing source is a blocking prerequisite.
        plan = json.loads((HERE / "fixtures" / "planned-configuration.json").read_text())
        configuration, projection = preparation_stage_configuration(plan, args.builds_tag, command, module)
        ci_pipeline.validate_config(configuration, repository="Hexalith/" + MODULE)
        stage_configuration = workspace / "eventstore-preparation-stages-1-3.json"
        stage_configuration.write_text(json.dumps(configuration, indent=2) + "\n")
        report["preparation_stage_projection"] = {**projection, "configuration_path": str(stage_configuration),
                                                 "configuration": configuration, "trusted_builds_tag": args.builds_tag,
                                                 "trusted_builds_sha": args.builds_sha}
        save()
        for name in ("Hexalith.Builds", "Hexalith.Tenants", "Hexalith.Platform", "Hexalith.FrontComposer"):
            path = "references/" + name
            require(path in candidate.items and candidate.items[path].mode == "160000", "Required direct product dependency is absent: " + name)
            repository = ROOT / "references" / name
            require(git(repository, "rev-parse", "--show-toplevel") == str(repository), "Required direct repository is uninitialized: " + name)
            origin = git(repository, "config", "--get", "remote.origin.url")
            require(origin.removesuffix(".git") in ("https://github.com/Hexalith/" + name, "git@github.com:Hexalith/" + name),
                    "Required direct repository origin differs: " + name)
            actual_gitlink = candidate.items[path].oid
            revision = args.builds_sha if name == "Hexalith.Builds" else actual_gitlink
            if name == "Hexalith.Builds":
                report["builds_product_preview"] = {
                    "source_candidate_gitlink": actual_gitlink, "selected_release_tag": args.builds_tag,
                    "selected_release_sha": args.builds_sha, "disposable_export_revision": revision,
                    "source_gitlink_unchanged": True,
                    "scope": "Disposable product build preview uses the selected trusted release; no module-owned source gitlink is edited",
                }
                save()
            git(repository, "cat-file", "-e", revision + "^{commit}")
            destination = module / path
            if destination.is_dir():
                destination.rmdir()
            # Product source-identity checks require a Git worktree. Clone only
            # this already available direct repository, never its nested links.
            command(["git", "-c", "submodule.recurse=false", "clone", "--no-hardlinks", "--no-checkout", "--no-recurse-submodules",
                     repository, destination])
            git(destination, "checkout", "--detach", revision)
            git(destination, "remote", "set-url", "origin", origin)
            require(not git(destination, "status", "--porcelain=v1", "--untracked-files=all"),
                    "Disposable direct repository is dirty: " + name)
        require(not git(module, "status", "--porcelain=v1", "--untracked-files=all", "--",
                        "src", "Directory.Build.props", "Directory.Build.targets", "Directory.Packages.props", "global.json"),
                "Disposable provider source is dirty")
        # Immutable published fixtures must not inherit a same-version local
        # package from a developer's global cache. Child fixture tools inherit
        # these disposable NuGet locations too.
        os.environ.update(NUGET_PACKAGES=str(workspace / "nuget-packages"),
                          NUGET_HTTP_CACHE_PATH=str(workspace / "nuget-http-cache"),
                          NUGET_PLUGINS_CACHE_PATH=str(workspace / "nuget-plugins-cache"))
        report["private_nuget_caches"] = True
        save()
        prepared = ci_pipeline.PreparedConfig(module, module, configuration, configuration["solution"], "global.json", ())
        ci_pipeline.restore_and_build(prepared)
        report["unit_project_results"] = []
        try:
            classified = run_preparation_unit_projects(ci_pipeline, prepared, report["unit_project_results"])
        finally:
            save()
        report["unit_projects"] = list(classified.unit)
        product_environment = os.environ.copy()
        product_environment.update(EXT_PROTECTION_INTEROP_CONFIGURATION="Release", EXT_PROTECTION_INTEROP_PROJECT_REFERENCES="false")
        subprocess.run([sys.executable, "-B", "scripts/ci-product-checks.py", "offline"], cwd=module, env=product_environment, check=True)
        report["ordinary_build_unit_package_consumer_checks"] = "passed"
        report["unexecuted_authority_owned_lanes"] = ["Azure live qualification", "Dapr live/broker/Kubernetes fixtures require their declared worker prerequisites"]
        fresh()
        report.update(result="passed", completed_at=datetime.now(timezone.utc).isoformat(),
                      push_condition="Repeat fresh base/head/adoption checks immediately before the separately authorized module-agent push")
        save()
        return 0
    except Exception as error:
        report["failure"] = str(error)
        save()
        print("EventStore preparation verification failed: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
