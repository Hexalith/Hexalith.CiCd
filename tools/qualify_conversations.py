#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["Jinja2==3.1.6", "PyYAML==6.0.3", "jsonschema==4.26.0"]
# ///
"""Qualify exact pre-adoption Conversations inputs without writing its owned tree.

Run under run-with-temp. This explicit local exception never pushes, creates an
accepted delivered ref, overlays module CI JSON or uses a source-built producer.
It requires committed candidate content and a real acceptable released tool.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager, nullcontext
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen
from xml.etree import ElementTree
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import delivery_runtime as delivery
import render as renderer

REPOSITORY = "Hexalith/Hexalith.Conversations"
PRODUCT_PATHS = ("src/", "tests/", "scripts/", "tools/", ".github/actions/", ".githooks/commit-msg", ".config/dotnet-tools.json",
                 "Directory.Build.props", ".gitattributes", "Hexalith.Conversations.slnx", "references/Hexalith.Platform")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def git(root: Path, *args: str) -> bytes:
    # Only the local clone operation permits a local transport. Network identity
    # checks below use the existing fixed anonymous delivery transport.
    result = subprocess.run(["git", "-c", "core.hooksPath=" + os.devnull, "-c", "submodule.recurse=false",
        "-c", "protocol.file.allow=always", "-C", str(root), *args],
        env=delivery.environment(), capture_output=True, check=False)
    if result.returncode:
        raise delivery.DeliveryError("qualification local Git inspection failed: " + args[0])
    return result.stdout


def clone_local(source: Path, destination: Path, revision: str, origin: str) -> None:
    git(destination.parent, "clone", "--no-checkout", "--no-hardlinks", "--no-local", str(source), str(destination))
    git(destination, "checkout", "--detach", revision)
    git(destination, "remote", "set-url", "origin", origin)


def owned_inventory(snapshot, document: dict, perimeter) -> list[dict]:
    """Derive a conservative byte/mode/gitlink mask from canonical ownership.

    Entire partial-owner files remain unchanged in this preparation phase. This
    includes npm selectors: npm file deletion is a post-adoption cleanup.
    """
    paths = set()
    for entry in document["entries"]:
        if entry["kind"] == "whole-dir":
            paths.update(path for path in snapshot.items if path == entry["path"] or path.startswith(entry["path"] + "/"))
        elif entry["kind"] == "absent-glob":
            paths.update(path for path in snapshot.items if perimeter.wildmatch(entry["pattern"], path))
        else:
            paths.add(entry["path"])
    result = []
    for path in sorted(paths):
        item = snapshot.items.get(path)
        row = {"path": path, "mode": item.mode if item else None, "oid": item.oid if item else None}
        if item is not None and item.mode != "160000":
            row["sha256"] = digest(snapshot.read(path))
        result.append(row)
    return result


def product_difference(before, after) -> list[dict]:
    result = []
    for path in sorted(before.items.keys() | after.items.keys()):
        old, new = before.items.get(path), after.items.get(path)
        if old == new:
            continue
        if not any(path == prefix or prefix.endswith("/") and path.startswith(prefix) for prefix in PRODUCT_PATHS):
            raise delivery.DeliveryError("preparation changed a path outside the approved central product inventory: " + path)
        result.append({"path": path, "before": {"mode": old.mode, "oid": old.oid} if old else None,
                       "after": {"mode": new.mode, "oid": new.oid} if new else None})
    if not result:
        raise delivery.DeliveryError("qualification requires a concrete committed product preparation change")
    return result


def live_baseline(transport) -> str:
    value = transport.api.get("/repos/" + REPOSITORY + "/git/ref/heads/main")
    if value.get("ref") != "refs/heads/main":
        raise delivery.DeliveryError("fresh Conversations main identity is unavailable")
    kind, revision = delivery.object_identity(value)
    if kind != "commit":
        raise delivery.DeliveryError("Conversations main is not a commit")
    return revision


def producer_provenance(version: str, revision: str) -> dict:
    """Read actual public NuGet provenance; never substitute a source build."""
    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is None:
        raise delivery.DeliveryError("producer pin must be an exact released stable version")
    url = "https://api.nuget.org/v3-flatcontainer/hexalith.builds.module.cli/" + version + "/hexalith.builds.module.cli." + version + ".nupkg"
    with urlopen(Request(url, headers={"User-Agent": "Hexalith-CiCd-qualification"}), timeout=60) as response:
        payload = response.read(128 * 1024 * 1024 + 1)
    if len(payload) > 128 * 1024 * 1024:
        raise delivery.DeliveryError("released producer package exceeds qualification bound")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [name for name in archive.namelist() if name.endswith(".nuspec")]
        if len(names) != 1:
            raise delivery.DeliveryError("released producer has no unique nuspec")
        metadata = ElementTree.fromstring(archive.read(names[0])).find("{*}metadata")
        repository = metadata.find("{*}repository") if metadata is not None else None
        if (metadata is None or metadata.findtext("{*}id") != "Hexalith.Builds.Module.Cli"
                or metadata.findtext("{*}version") != version or repository is None or repository.get("commit") != revision):
            raise delivery.DeliveryError("released producer package provenance differs from the selected Builds release")
    return {"version": version, "sourceCommit": revision, "sha256": digest(payload), "bytes": len(payload)}


@contextmanager
def private_environment(root: Path):
    changes = {"NUGET_PACKAGES": str(root / "packages"), "DOTNET_CLI_HOME": str(root / "dotnet-home"),
               "PLAYWRIGHT_BROWSERS_PATH": str(root / "browsers")}
    previous = {key: os.environ.get(key) for key in changes}
    os.environ.update(changes)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def action(root: Path, name: str, tools) -> None:
    """Execute the already policy-checked module composite without extra setup."""
    document = tools.parse_yaml((root / ".github/actions" / name / "action.yml").read_text())
    for step in document["runs"]["steps"]:
        if set(step) - {"name", "run", "shell"} or step.get("shell") != "bash" or not isinstance(step.get("run"), str):
            raise delivery.DeliveryError("local qualification requires an explicit bash product-hook step")
        subprocess.run(["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]], cwd=root, check=True)


def qualify(project: Path, *, candidate: str, product_head: str, baseline: str, output: Path) -> dict:
    candidate, product_head, baseline = map(delivery.sha, (candidate, product_head, baseline))
    scratch = Path(os.environ["TMPDIR"]).resolve(strict=True)
    output = output.resolve()
    if (output.is_relative_to(scratch) or output.exists() or output.is_relative_to(project / "references")
            or output.is_relative_to(project / "rendered") or output.is_relative_to(project / "setup")
            or output.is_relative_to(project / "templates")):
        raise delivery.DeliveryError("qualification receipt requires a fresh non-product path outside disposable scratch")
    module_source = project / "references/Hexalith.Conversations"
    transport = delivery.Transport()
    report = {"schema": "hexalith.conversations-qualification.v1", "kind": "candidate-qualification", "result": "failed",
              "candidate": candidate, "productHead": product_head, "baselineHead": baseline}
    try:
        if git(project, "rev-parse", "HEAD").decode().strip() != candidate:
            raise delivery.DeliveryError("qualification requires the exact committed CiCd candidate HEAD")
        if git(module_source, "rev-parse", "HEAD").decode().strip() != product_head or git(module_source, "status", "--porcelain", "--ignore-submodules=all"):
            raise delivery.DeliveryError("qualification requires the exact clean committed product HEAD")
        git(module_source, "merge-base", "--is-ancestor", baseline, product_head)
        if git(project, "show", candidate + ":tools/qualify_conversations.py") != Path(__file__).read_bytes():
            raise delivery.DeliveryError("qualification orchestration must itself be committed in the candidate")
        if git(project, "ls-tree", candidate, "--", "references/Hexalith.Conversations").decode().strip() != "160000 commit " + baseline + "\treferences/Hexalith.Conversations":
            raise delivery.DeliveryError("qualification candidate must retain the published baseline module gitlink")
        if live_baseline(transport) != baseline:
            raise delivery.DeliveryError("fresh Conversations main differs from qualification baseline")
        with tempfile.TemporaryDirectory(prefix="conversations-qualification-", dir=scratch) as temporary:
            work = Path(temporary)
            candidate_root, module = work / "candidate", work / "module"
            clone_local(project, candidate_root, candidate, "https://github.com/Hexalith/Hexalith.CiCd.git")
            clone_local(module_source, module, product_head, "https://github.com/" + REPOSITORY + ".git")
            git(module, "update-ref", "refs/remotes/origin/main", baseline)
            tag = git(project, "show", candidate + ":builds-version").decode().strip()
            acquired, _ = transport.builds(tag, work / "acceptable-release")
            release = acquired.resolve("refs/tags/" + tag + "^{commit}")
            if git(project, "ls-tree", candidate, "--", "references/Hexalith.Builds").decode().strip() != "160000 commit " + release + "\treferences/Hexalith.Builds":
                raise delivery.DeliveryError("candidate Builds gitlink differs from its acceptable released catalog")
            builds = candidate_root / "references/Hexalith.Builds"
            builds.mkdir(parents=True, exist_ok=True)
            git(builds, "init", "--template=")
            git(builds, "remote", "add", "origin", "https://github.com/Hexalith/Hexalith.Builds.git")
            # The acquired immutable release author/ancestry/API evidence above
            # fixes the tag identity before this full actual checkout is used.
            git(builds, "fetch", "--no-tags", "--no-recurse-submodules", "origin", "+refs/tags/" + tag + ":refs/tags/" + tag)
            git(builds, "checkout", "--detach", "refs/tags/" + tag)
            if git(builds, "rev-parse", "HEAD").decode().strip() != release:
                raise delivery.DeliveryError("released checkout changed after authenticated acquisition")
            if renderer.render(candidate_root, check=True):
                raise delivery.DeliveryError("committed candidate render is not reproducible from its released contract")
            subprocess.run([sys.executable, "-I", str(candidate_root / "tools/check_global.py"), "--project-root", str(candidate_root)], check=True)
            sys.path.insert(0, str(builds / "Github/lib"))
            import audit_lint, ci_config, ci_dapr_scope, ci_environment, ci_pipeline, expected_state, guard_actions, guard_commitlint, guard_tools, module_preparation, perimeter
            config_path = "rendered/Hexalith.Conversations/.github/hexalith-ci.json"
            config_bytes = git(project, "show", candidate + ":" + config_path)
            config = ci_config.validate_config(renderer.json_document(config_bytes, config_path), repository=REPOSITORY)
            if (config["solution"] != "Hexalith.Conversations.slnx" or config.get("moduleManifest") != "module/hexalith.module-manifest.v2.json"
                    or not config["dapr"] or not config["browsers"] or "after-unit-tests" not in config["hooks"]
                    or "testsupport-windows" not in config["jobs"] or "csharp" not in config["codeql"]
                    or config["submodules"] != ["references/Hexalith.Platform"]
                    or "tests/Hexalith.Conversations.Admin.Web.Tests/Hexalith.Conversations.Admin.Web.Tests.csproj" not in config["tests"]["integration"]):
                raise delivery.DeliveryError("candidate configuration omits the approved Conversations product coverage")
            perimeter_doc = renderer.json_document(git(project, "show", candidate + ":rendered/Hexalith.Conversations.perimeter.json"), "candidate perimeter")
            source_git = expected_state.Git(module)
            before, product = (expected_state.tree_snapshot(source_git, revision) for revision in (baseline, product_head))
            owned_before = owned_inventory(before, perimeter_doc, perimeter)
            owned_after = owned_inventory(product, perimeter_doc, perimeter)
            if owned_before != owned_after:
                raise delivery.DeliveryError("product preparation changed canonical owned bytes, modes or gitlinks")
            differences = product_difference(before, product)
            original_builds = module_preparation._pin(module, "references/Hexalith.Builds")
            if original_builds != before.items["references/Hexalith.Builds"].oid:
                raise delivery.DeliveryError("original owned Builds pin changed")
            platform = module / "references/Hexalith.Platform"
            platform.mkdir(parents=True, exist_ok=True)
            platform_commit = module_preparation._pin(module, "references/Hexalith.Platform")
            git(platform, "init", "--template=")
            git(platform, "remote", "add", "origin", "https://github.com/Hexalith/Hexalith.Platform.git")
            git(platform, "fetch", "--no-recurse-submodules", "--no-tags", "origin", platform_commit, "refs/tags/*:refs/tags/*")
            git(platform, "checkout", "--detach", platform_commit)
            tags = sorted(tag for tag in git(platform, "tag", "--points-at", platform_commit).decode().splitlines() if re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag))
            if not tags:
                raise delivery.DeliveryError("qualified Platform identity has no actual release tag")
            pin = module_preparation._tool(module)
            provenance = producer_provenance(pin, release)
            if pin != tag[1:]:
                raise delivery.DeliveryError("qualified tool and active Builds release versions differ")
            authority = {"schema": "hexalith.managed-build.v1", "kind": "candidate-qualification", "repository": REPOSITORY,
                "moduleRoot": str(module), "moduleHead": product_head, "originalBuildsGitlink": original_builds,
                "buildsTag": tag, "buildsCommit": release, "buildsRoot": str(builds), "deliveredSha": None,
                "configurationDigest": digest(config_bytes), "perimeterDigest": None, "platformCommit": platform_commit,
                "platformCatalogCommit": module_preparation._pin(platform, "references/Hexalith.Builds"), "platformReleaseTag": tags[0], "producerPin": pin,
                "qualification": {"baselineHead": baseline, "ownedBaselineDigest": digest(canonical(owned_before)),
                    "ownedProductDigest": digest(canonical(owned_after)), "productDiffDigest": digest(canonical(differences)),
                    "ciCdRoot": str(candidate_root), "ciCdCandidate": candidate,
                    "candidateTree": git(project, "rev-parse", candidate + "^{tree}").decode().strip(), "renderedConfigPath": config_path,
                    "renderedConfigBlob": git(project, "rev-parse", candidate + ":" + config_path).decode().strip(), "producerSourceCommit": release}}
            prepared = ci_pipeline.PreparedConfig(module, module, config, config["solution"], "global.json", tuple(["references/Hexalith.Builds", *config["submodules"]]))
            with tempfile.TemporaryDirectory(prefix="policy-tools-", dir=work) as tool_directory:
                tools = guard_tools.Tools(Path(tool_directory))
                audit_lint.lint(product)
                guard_actions.lint(product, tools)
                guard_commitlint.lint(source_git, tools, event_name="push", event={}, frozen_head=product_head, commit_range=(baseline, product_head))
                legacy_lock = renderer.json_document(before.read("package-lock.json"), "baseline commit policy lock")
                trusted_lock = renderer.json_document((tools.directory / "package-lock.json").read_bytes(), "trusted commit policy lock")
                for package in ("@commitlint/cli", "@commitlint/config-conventional"):
                    key = "node_modules/" + package
                    if legacy_lock["packages"][key]["version"] != trusted_lock["packages"][key]["version"]:
                        raise delivery.DeliveryError("baseline owning commit policy requires a different pinned validator")
                legacy_config = tools.directory / "module.commitlint.config.mjs"
                legacy_config.write_bytes(before.read("commitlint.config.mjs"))
                for revision in git(module, "rev-list", "--reverse", baseline + ".." + product_head).decode().splitlines():
                    result = tools._process(["node", str(tools.directory / "node_modules/@commitlint/cli/cli.js"),
                        "--config", str(legacy_config), "--color=false"], "owning module commitlint", guard_commitlint.message(source_git, revision))
                    if result.returncode:
                        raise delivery.DeliveryError("owning module commit policy refused a preparation commit")
                with private_environment(work):
                    environment = module_preparation.prepare_qualified_environment(prepared, authority, work)
                    with module_preparation.applied_qualification(prepared, authority, environment):
                        ci_pipeline.restore_and_build(prepared)
                        classified = ci_pipeline.run_unit_tests(prepared, repository=REPOSITORY)
                        browsers = config["browsers"] or any("E2E" in Path(path).stem for path in classified.integration)
                        with ci_dapr_scope.isolated_dapr(module, work) if config["dapr"] else nullcontext(None) as dapr_setup:
                            ci_environment.setup_environment(module, solution=config["solution"], dapr=False, browsers=browsers, registry=config["registry"])
                            for name in ("after-unit-tests",):
                                if name in config["hooks"]:
                                    action(module, name, tools)
                            ci_pipeline.run_integration_tests(prepared, repository=REPOSITORY)
                            if "after-integration-tests" in config["hooks"]:
                                action(module, "after-integration-tests", tools)
                            report["dapr"] = dapr_setup

            if live_baseline(transport) != baseline or git(module_source, "rev-parse", "HEAD").decode().strip() != product_head:
                raise delivery.DeliveryError("baseline or tested product head changed; qualification cannot be reused")
            if owned_inventory(expected_state.tree_snapshot(source_git, "HEAD"), perimeter_doc, perimeter) != owned_before:
                raise delivery.DeliveryError("qualification changed owned state")
            report.update(result="passed", authority=authority, producer=provenance, ownedInventory=owned_before,
                          productDiff=differences, outputs=environment.files, nativeWindows="pending separate released-input execution")
    except Exception as error:
        report["reason"] = delivery.clean(error)
        raise
    finally:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(canonical(report) + b"\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--product-head", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        qualify(args.project_root.resolve(), candidate=args.candidate, product_head=args.product_head, baseline=args.baseline, output=args.output)
        return 0
    except Exception as error:
        print(delivery.clean(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
