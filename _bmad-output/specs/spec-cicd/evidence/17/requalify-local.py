#!/usr/bin/env python3
"""Requalify the exact Folders candidate locally without activating delivery.

Run with run-with-temp and an unused --output directory outside TMPDIR. Only
local Git objects are read. Existing evidence and module worktrees stay intact.
An exit of one preserves failed preparation gates; it is not an adoption pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


EVIDENCE = Path(__file__).resolve().parent
CICD = EVIDENCE.parents[4]
OWNED = (
    ".github/workflows", ".github/dependabot.yml", ".github/hexalith-ci.json",
    "references/Hexalith.Builds", ".gitmodules", "AGENTS.md", "CLAUDE.md",
    ".github/copilot-instructions.md", ".claude", "commitlint.config.mjs",
    ".releaserc.json",
)


def git(root: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-c", "submodule.recurse=false", "-C", str(root), *arguments],
        text=True,
    ).strip()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clone(source: Path, target: Path, revision: str) -> None:
    subprocess.run(
        ["git", "-c", "submodule.recurse=false", "clone", "--shared",
         "--no-checkout", str(source), str(target)],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "submodule.recurse=false", "-C", str(target),
         "checkout", "--detach", revision],
        check=True, capture_output=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    scratch = Path(os.environ["TMPDIR"]).resolve()
    output = args.output.resolve()
    if output.is_relative_to(scratch):
        raise ValueError("Save requested evidence outside the disposable TMPDIR")
    output.mkdir(parents=True, exist_ok=False)
    saved = json.loads((EVIDENCE / "final-candidate.json").read_text())
    source = CICD / "references/Hexalith.Folders"
    head = git(CICD, "rev-parse", "HEAD")
    revision = git(source, "rev-parse", "HEAD")
    if revision != saved["candidate"]:
        raise ValueError("Folders differs from the exact qualified candidate")
    before = git(source, "status", "--porcelain=v1", "--untracked-files=all")
    if before:
        raise ValueError("Folders must be clean; preserve its changes before qualification")
    module = scratch / "Folders"
    project = scratch / "CiCd"
    clone(source, module, revision)
    clone(CICD, project, head)
    builds_revision = git(CICD / "references/Hexalith.Builds", "rev-parse",
                          "refs/tags/v6.0.6^{commit}")
    if builds_revision != saved["builds"]:
        raise ValueError("The released Builds tag no longer matches saved evidence")
    builds = project / "references/Hexalith.Builds"
    clone(CICD / "references/Hexalith.Builds", builds, builds_revision)
    report = {
        "status": "running",
        "scope": "local objects only; no remote Git, provisioning, adoption or credentials",
        "revisions": {"cicd": head, "folders": revision,
                      "folders_tree": git(module, "rev-parse", "HEAD^{tree}"),
                      "folders_parents": git(module, "show", "-s", "--format=%P", "HEAD"),
                      "builds": builds_revision, "builds_tag": "v6.0.6"},
        "commands": [],
        "policy_source_blobs": {
            path: git(project, "rev-parse", head + ":" + path)
            for path in ("tools/render.py", "tools/check_global.py", "tools/scan_discovery.py",
                         "templates/.github/workflows/ci.yml.j2")},
        "changed_policy_inputs_since_prior_resume": git(
            project, "diff", "--name-only", "b836159cea272e5211333296936106cf82833a27", head,
            "--", "tools/render.py", "tools/check_global.py", "tools/scan_discovery.py",
            "templates/.github/workflows/ci.yml.j2").splitlines(),
    }

    def save() -> None:
        (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")

    def job(label: str, arguments: list[str], cwd: Path) -> None:
        with (output / (label + ".txt")).open("w") as log:
            result = subprocess.run(arguments, cwd=cwd, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=180)
        report["commands"].append({"label": label, "arguments": arguments,
                                   "exit_code": result.returncode,
                                   "output": label + ".txt"})
        save()
        if result.returncode:
            raise RuntimeError(label + " failed; see saved output")

    try:
        report["candidate_tree_matches_saved"] = report["revisions"]["folders_tree"] == saved["tree"]
        report["owned_tree_preserved"] = (
            git(module, "ls-tree", "-r", saved["base"], "--", *OWNED)
            == git(module, "ls-tree", "-r", revision, "--", *OWNED)
        )
        if not report["candidate_tree_matches_saved"] or not report["owned_tree_preserved"]:
            raise RuntimeError("Candidate or owned-tree identity failed")
        report["nested_submodules_uninitialized"] = not any(
            path.name == ".git" for path in (source / "references").rglob(".git")
        )
        if not report["nested_submodules_uninitialized"]:
            raise RuntimeError("A nested checkout is initialized; do not use it as proof")

        sys.path.insert(0, str(project / "tools"))
        import check_global
        from delivery_runtime import Git
        from scan_discovery import Discovery

        with check_global.selected_contract(project) as contract:
            check_global.check_render(project, contract)
            check_global.check_committed_render(project)
            check_global.check_committed_inputs(project)
        report["production_local_validator_boundaries"] = "passed"
        job("production-render-check", ["uv", "run", "--locked", "--script",
                                        "tools/render.py", "--check"], project)
        shutil.copyfile(EVIDENCE / "Hexalith.Folders.setup-candidate.yml",
                        project / "setup/Hexalith.Folders.yml")
        job("candidate-render", ["uv", "run", "--locked", "--script", "tools/render.py"], project)
        job("candidate-render-check", ["uv", "run", "--locked", "--script",
                                       "tools/render.py", "--check"], project)
        with check_global.selected_contract(project) as contract:
            check_global.check_documents(project, check_global.renderer.registry(project), contract)
        archived = json.loads((EVIDENCE / "registration-candidate.json").read_text())["files"]
        rendered = {
            path: {"sha256": digest((project / path).read_bytes()),
                   "matches_archived_candidate": digest((project / path).read_bytes()) == value}
            for path, value in archived.items() if path.startswith("rendered/")
        }
        report["candidate_render"] = rendered
        report["candidate_documents_and_callers"] = "passed"
        if not all(item["matches_archived_candidate"] for item in rendered.values()):
            raise RuntimeError("Current render differs from the archived proposal")

        files, errors = Discovery(Git(module), revision).discover()
        old = json.loads((EVIDENCE / "action-discovery.json").read_text())
        report["action_discovery"] = {
            "selected_files": sorted(files), "error_count": len(errors),
            "matches_saved_diagnostics": errors == old["errors"],
            "diagnostics_sha256": digest(json.dumps(errors, separators=(",", ":")).encode()),
            "existing_diagnostics": "../action-discovery.json" if errors == old["errors"] else None,
        }
        if errors != old["errors"]:
            (output / "action-discovery.json").write_text(json.dumps(errors, indent=2) + "\n")

        # These inputs have not changed: bind their existing outcomes instead
        # of repeating audits, classification, runner tests or product suites.
        report["unchanged_qualification"] = {
            "released_builds": builds_revision == saved["builds"],
            "strict_runner": digest((module / "tests/tools/run-complete-project-tests.ps1").read_bytes()) == saved["strict_runner_sha256"],
            "prior_results": ["../final-candidate.json", "../resume/verification.json",
                              "../complete-project-runner-qualification.json"],
            "rerun": False,
        }
        if not all(report["unchanged_qualification"][name] for name in ("released_builds", "strict_runner")):
            raise RuntimeError("Previously qualified inputs changed; obtain fresh affected outcomes")
        blockers = json.loads((EVIDENCE / "resume/product-blocker-analysis.json").read_text())
        report["product_blocker_source_identity"] = {
            path: git(module, "rev-parse", revision + ":" + path) == binding["current_blob"]
            for path, binding in blockers["current_source_binding"].items()}
        if not all(report["product_blocker_source_identity"].values()):
            raise RuntimeError("Product blocker source changed; prior failure proof needs a new run")
        report["product_suites"] = {
            "rerun": False, "reason": "Exact candidate and failed prerequisite sources unchanged; preserve prior outcomes without duplicating runs.",
            "prior_results": ["../final-candidate.json", "../attempt-3/product-verification.json",
                              "../focused-product-prerequisites.json"],
        }
        report["blockers"] = [
            "Released audit lint remains failed on eight unchanged historical auditSources declarations; see final-candidate.json.",
            f"Current CiCd discovery reports {len(errors)} diagnostics; no exemption was added.",
            "Unchanged retained Server/AppHost/FR58 and operator-provider prerequisites remain incomplete; see resume/product-blocker-analysis.json.",
            "Predecessor acceptance, AD-21 administration, protected adoption and the genuine scheduled release remain outstanding.",
        ]
        report["not_executed"] = {
            "full_validator": "It clones live module repositories, outside the local-only boundary.",
            "normal_module_checker": "Folders is unadopted; its nested Builds remains intentionally absent.",
            "live_acceptance": "Predecessor checkpoints, AD-21, adoption, retirement and scheduled release remain gated.",
        }
        report["status"] = "blocked; local candidate preserved"
        return 1
    except Exception as error:
        report["status"] = "failed local qualification"
        report["error"] = str(error)
        return 2
    finally:
        report["folders_worktree_preserved"] = git(source, "status", "--porcelain=v1", "--untracked-files=all") == before
        report["folders_head_preserved"] = git(source, "rev-parse", "HEAD") == revision
        report["scratch_root"] = str(scratch)
        save()
        print(json.dumps({"status": report["status"], "report": str(output / "verification.json")}))


if __name__ == "__main__":
    raise SystemExit(main())
