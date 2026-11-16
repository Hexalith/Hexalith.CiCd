#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Real-Git qualification of the closed three-path owner correction."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from delivery_support import ROOT, filtered_remote, git, load

delivery = load(ROOT / "tools/deliver_g6_catalog.py", "_g6_delivery_tests")
rt = delivery.rt


class CatalogWorkspace:
    """Synthetic reviewed Projects source with real canonical Git tree bindings."""
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir()
        self.projects = self.root / "projects"
        self.projects.mkdir()
        git(self.projects, "init", "--quiet", "--initial-branch=main")
        workflow = self.projects / delivery.WORKFLOW
        workflow.parent.mkdir(parents=True)
        workflow.write_text("name: Product\n# retain every product gate\n")
        (self.projects / "foreign.txt").write_bytes(b"foreign\r\n")
        (self.projects / ".gitattributes").write_text("* filter=poison\n")
        git(self.projects, "add", ".")
        git(self.projects, "commit", "--quiet", "-m", "test: reviewed base")
        self.base = git(self.projects, "rev-parse", "HEAD")
        git(self.projects, "update-index", "--add", "--cacheinfo", "160000", self.base, "references/Foreign")
        git(self.projects, "commit", "--quiet", "-m", "test: retain gitlink")
        self.base = git(self.projects, "rev-parse", "HEAD")
        self.base_tree = git(self.projects, "rev-parse", "HEAD^{tree}")
        self.before = self.items(self.projects, self.base)
        workflow.write_text(workflow.read_text() + "# catalog acquisition before prepare-build\n")
        for path in delivery.PATHS[1:]:
            target = self.projects / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / path).read_bytes())
        git(self.projects, "add", "--", *delivery.PATHS)
        self.patch = subprocess.run(["git", "-C", str(self.projects), "diff", "--cached", "--binary", self.base],
                                    check=True, capture_output=True).stdout
        self.result_tree = git(self.projects, "write-tree")
        self.after = self.items(self.projects, self.result_tree)
        self.value = {"schema": "hexalith.projects-g6-catalog.v1", "repository": delivery.PROJECTS,
                      "pre_push_gate": "reviewed-tree-owner-authorized",
                      "base_commit": self.base, "base_tree": self.base_tree,
                      "patch_sha256": delivery.digest(self.patch), "result_tree": self.result_tree,
                      "before": {path: self.before.get(path) for path in delivery.PATHS},
                      "after": {path: self.after.get(path) for path in delivery.PATHS}}
        self.remote = self.root / "projects.git"
        git(self.root, "clone", "--bare", "--quiet", self.projects, self.remote)
        filtered_remote(self.remote)
        self.owner = self.root / "owner"
        self.owner.mkdir()
        git(self.owner, "init", "--quiet", "--initial-branch=main")
        for path in delivery.SOURCES:
            if path == delivery.MANIFEST:
                continue
            target = self.owner / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self.patch if path == delivery.PATCH else (ROOT / path).read_bytes())
        self.write_manifest()
        self.owner_remote = self.root / "owner.git"
        git(self.root, "clone", "--bare", "--quiet", self.owner, self.owner_remote)
        self.sha = git(self.owner, "rev-parse", "HEAD")
        self.report_path = self.root / "receipt.json"
        self.pushes = []
        self.fetches = []
        self.refuse = False
        self.race = None
        self.final_race = None
        self.final_registry = None
        self.final_accepted_ref = None
        self.push_outcome = None
        self.fail_reconciliation = False
        self.read_counts = {}
        self.token = "inert-narrow-token"
        workspace = self

        class Transport(rt.Transport):
            def remote(self, repository):
                if repository not in {rt.CICD, delivery.PROJECTS}:
                    raise AssertionError("transport broadened")
                return (workspace.owner_remote if repository == rt.CICD else workspace.remote).as_uri()

            def module(self, target, repository):
                workspace.fetches.append(repository)
                workspace.read_counts[repository] = workspace.read_counts.get(repository, 0) + 1
                if workspace.final_race == repository and workspace.read_counts[repository] == 2:
                    remote = workspace.owner_remote if repository == rt.CICD else workspace.remote
                    head = git(remote, "rev-parse", "main")
                    newer = git(remote, "commit-tree", git(remote, "rev-parse", head + "^{tree}"),
                                "-p", head, data=b"test: final read race\n")
                    git(remote, "update-ref", "refs/heads/main", newer)
                if workspace.final_registry and repository == rt.CICD and workspace.read_counts[repository] == 2:
                    remote = rt.Git(workspace.owner_remote, index=workspace.root / "late-registry-index")
                    head = remote.resolve("refs/heads/main")
                    blob = remote.run("hash-object", "-w", "--stdin", data=b"{}\n").decode().strip()
                    remote.run("read-tree", head)
                    remote.run("update-index", "--add", "--cacheinfo", "100644", blob,
                               "setup/" + workspace.final_registry + ".yml")
                    tree = remote.run("write-tree", "--missing-ok").decode().strip()
                    newer = remote.run("commit-tree", tree, "-p", head, data=b"test: register Projects concurrently\n").decode().strip()
                    remote.run("update-ref", "refs/heads/main", newer)
                if workspace.final_accepted_ref and repository == delivery.PROJECTS and workspace.read_counts[repository] == 2:
                    git(workspace.owner_remote, "update-ref", "refs/heads/delivered/" + workspace.final_accepted_ref, workspace.sha)
                if workspace.fail_reconciliation and workspace.pushes:
                    raise rt.DeliveryError("reconciliation unavailable")
                if workspace.token and any(workspace.token in value for value in target.env.values()):
                    raise AssertionError("token inherited by non-network Git environment")
                return super().module(target, repository)

            def push(self, target, repository, revision, token):
                if repository != delivery.PROJECTS or token != workspace.token:
                    raise AssertionError("write token/repository isolation failed")
                workspace.pushes.append(revision)
                if workspace.refuse:
                    return 1, ("denied " + workspace.token).encode()
                if workspace.race == "before":
                    workspace.advance()
                result = super().push(target, repository, revision, token)
                if workspace.race == "after":
                    workspace.advance()
                if workspace.push_outcome == "error":
                    return 1, b"accepted but connection lost"
                if workspace.push_outcome == "timeout":
                    raise rt.DeliveryError("Git push timed out; remote outcome is ambiguous")
                return result
        self.transport = Transport()

    @staticmethod
    def items(root, revision):
        result = {}
        for row in git(root, "ls-tree", "-r", revision).splitlines():
            header, path = row.split("\t")
            result[path] = header.split()
        return result

    def write_manifest(self):
        path = self.owner / delivery.MANIFEST
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.value) + "\n")
        git(self.owner, "add", ".")
        git(self.owner, "commit", "--quiet", "-m", "test: reviewed owner proposal")
        self.sha = git(self.owner, "rev-parse", "HEAD")
        if hasattr(self, "owner_remote"):
            git(self.owner, "push", "--quiet", self.owner_remote, "HEAD:main")

    def context(self):
        return {"GITHUB_REPOSITORY": "Hexalith/Hexalith.CiCd", "GITHUB_REF": "refs/heads/main",
                "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_SHA": self.sha, "G6_OWNER_SOURCE": self.sha}

    def run(self, operation="qualify", **context):
        self.read_counts.clear()
        return delivery.execute(operation, self.context() | context, self.report_path, transport=self.transport,
                                token=self.token if operation == "deliver" else "", scratch=self.root, local_root=self.owner)

    def deliver(self, qualified=None):
        qualified = qualified or self.run()
        return self.run("deliver", G6_QUALIFICATION="success", G6_PLAN=json.dumps(qualified["plan"]))

    def cli_qualify(self, **extra):
        configuration = self.root / "cli-config.json"
        configuration.write_text(json.dumps({"cicd": str(self.owner_remote), "modules": {delivery.PROJECTS: str(self.remote)},
                                              "acquisitions": str(self.root / "cli-acquisitions.jsonl")}))
        output = self.root / "outputs"
        output.unlink(missing_ok=True)
        result = subprocess.run([sys.executable, "-I", str(ROOT / "tools/tests/delivery_support.py"), "driver",
                                 str(self.owner / "tools/deliver_g6_catalog.py"), str(configuration), "qualify",
                                 "--report", str(self.report_path)], capture_output=True,
                                env=os.environ | self.context() | {"GITHUB_OUTPUT": str(output), "TMPDIR": str(self.root),
                                                                 "MODULE_TOKEN": "", "CICD_TOKEN": ""} | extra)
        return result, output.read_text() if output.exists() else ""

    def advance(self, *, tree=None, parent=None):
        head = git(self.remote, "rev-parse", "refs/heads/main")
        revision = git(self.remote, "commit-tree", tree or git(self.remote, "rev-parse", head + "^{tree}"),
                       "-p", parent or head, data=b"test: concurrent source\n")
        git(self.remote, "update-ref", "refs/heads/main", revision)
        return revision


class CatalogDeliveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(temporary.cleanup)
        self.w = CatalogWorkspace(Path(temporary.name) / "workspace")
        original = rt.environment
        def file_transport():
            result = original()
            i = int(result["GIT_CONFIG_COUNT"])
            result.update(GIT_CONFIG_COUNT=str(i + 1))
            result[f"GIT_CONFIG_KEY_{i}"] = "protocol.file.allow"
            result[f"GIT_CONFIG_VALUE_{i}"] = "always"
            return result
        self.patch = mock.patch.object(rt, "environment", side_effect=file_transport)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def assert_refused(self, result, reason=None):
        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["failed_operation"])
        if reason:
            self.assertIn(reason, result["reason"])
        self.assertEqual(self.w.pushes, [])
        self.assertEqual(git(self.w.remote, "rev-parse", "main"), self.w.base)

    def test_exact_result_preserves_foreign_objects_indices_worktrees_and_token_isolation(self):
        w = self.w
        snapshots = [(root, (root / ".git/index").read_bytes(), git(root, "status", "--porcelain"),
                      git(root, "show-ref")) for root in (w.projects, w.owner)]
        with mock.patch.dict(os.environ, {"GIT_DIR": "/nonexistent/poison", "MODULE_TOKEN": w.token,
                                         "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.hooksPath",
                                         "GIT_CONFIG_VALUE_0": "/nonexistent/poison"}):
            qualified = w.run()
            self.assertEqual(qualified["status"], "qualified")
            result = w.deliver(qualified)
        self.assertEqual(result["status"], "delivered")
        self.assertEqual(result["owner_source"], w.sha)
        self.assertEqual(result["delivered_tree"], w.result_tree)
        self.assertEqual(w.items(w.remote, result["delivered_sha"]), w.after)
        self.assertEqual(git(w.remote, "rev-parse", result["delivered_sha"] + "^"), w.base)
        for root, index, status, refs in snapshots:
            self.assertEqual((root / ".git/index").read_bytes(), index)
            self.assertEqual(git(root, "status", "--porcelain"), status)
            self.assertEqual(git(root, "show-ref"), refs)
        self.assertFalse((w.root / "executed").exists())
        self.assertNotIn(w.token.encode(), w.report_path.read_bytes())
        self.assertEqual(w.fetches.count(delivery.PROJECTS), 4)
        self.assertEqual([proof["phase"] for proof in result["full_writer_exclusion"]], ["delivery source verification", "push"])
        self.assertTrue(all(proof["registry_absent"] and proof["accepted_ref_absent"]
                            for proof in result["full_writer_exclusion"]))

    def test_already_delivered_exact_tree_and_parent_is_idempotent(self):
        delivered = self.w.deliver()
        self.w.pushes.clear()
        result = self.w.deliver()
        self.assertEqual(result["status"], "unchanged")
        self.assertEqual(result["delivered_sha"], delivered["delivered_sha"])
        self.assertEqual(result["owner_source"], self.w.sha)
        self.assertEqual(self.w.pushes, [])

    def test_partial_clone_proposal_preserves_unrelated_missing_promised_blob(self):
        w = self.w
        target = delivery.Git(w.root / "filtered.git", index=w.root / "filtered-index")
        target.init()
        self.assertEqual(w.transport.module(target, delivery.PROJECTS), w.base)
        self.assertEqual(target.run("config", "--get", "remote.origin.promisor"), b"true\n")
        unrelated_blob = w.before["foreign.txt"][2]
        missing = "?" + unrelated_blob
        before = target.run("rev-list", "--objects", "--missing=print", w.base).decode().splitlines()
        self.assertIn(missing, before)
        owner = rt.Git(w.owner)
        tree = delivery.proposal(owner, w.sha, target, w.value)
        self.assertEqual(tree, w.result_tree)
        self.assertEqual({path: list(item) for path, item in target.items(tree).items()}, w.after)
        after = target.run("rev-list", "--objects", "--missing=print", tree).decode().splitlines()
        self.assertIn(missing, after)

    def test_registered_projects_and_live_accepted_refs_fail_qualification_case_insensitively(self):
        w = self.w
        for name in (delivery.PROJECTS, delivery.PROJECTS.lower(), delivery.PROJECTS.upper()):
            for selector in ("registry", "accepted_ref"):
                with self.subTest(name=name, selector=selector):
                    if selector == "registry":
                        path = w.owner / ("setup/" + name + ".yml")
                        path.parent.mkdir(exist_ok=True)
                        path.write_text("{}\n")
                        w.write_manifest()
                    else:
                        git(w.owner_remote, "update-ref", "refs/heads/delivered/" + name, w.sha)
                    code, output = w.cli_qualify()
                    self.assertEqual(code.returncode, 1)
                    self.assertEqual(output, "")
                    result = json.loads(w.report_path.read_bytes())
                    self.assert_refused(result)
                    proof = result["full_writer_exclusion"][-1]
                    self.assertEqual(proof["phase"], "qualification")
                    self.assertFalse(proof["registry_absent" if selector == "registry" else "accepted_ref_absent"])
                    self.assertEqual(proof["matching_registry_entries"], [name] if selector == "registry" else [])
                    self.assertIn("during qualification", result["failed_operation"])
                    if selector == "registry":
                        path.unlink()
                        w.write_manifest()
                    else:
                        git(w.owner_remote, "update-ref", "-d", "refs/heads/delivered/" + name)

    def test_registry_appearance_at_final_source_read_refuses_push_and_unchanged(self):
        w = self.w
        for unchanged in (False, True):
            if unchanged:
                self.assertEqual(w.deliver()["status"], "delivered")
                w.pushes.clear()
            qualified = w.run()
            w.final_registry = delivery.PROJECTS.upper()
            result = w.deliver(qualified)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(w.pushes, [])
            self.assertIn("reread exact CiCd main before", result["failed_operation"])
            self.assertIn("CiCd main advanced", result["reason"])
            self.assertIn("setup/" + w.final_registry + ".yml", w.items(w.owner_remote, "main"))
            git(w.owner_remote, "update-ref", "refs/heads/main", w.sha)
            w.final_registry = None

    def test_accepted_ref_appearance_at_final_boundary_refuses_push_and_unchanged(self):
        w = self.w
        for unchanged in (False, True):
            if unchanged:
                self.assertEqual(w.deliver()["status"], "delivered")
                w.pushes.clear()
            qualified = w.run()
            w.final_accepted_ref = delivery.PROJECTS.lower()
            result = w.deliver(qualified)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(w.pushes, [])
            expected = "unchanged confirmation" if unchanged else "push"
            self.assertEqual(result["failed_operation"], "verify live Projects accepted-ref absence during " + expected)
            proof = result["full_writer_exclusion"][-1]
            self.assertEqual(proof["phase"], expected)
            self.assertTrue(proof["registry_absent"])
            self.assertFalse(proof["accepted_ref_absent"])
            self.assertEqual(proof["matching_accepted_refs"], ["refs/heads/delivered/" + w.final_accepted_ref])
            git(w.owner_remote, "update-ref", "-d", "refs/heads/delivered/" + w.final_accepted_ref)
            w.final_accepted_ref = None

    def test_different_live_source_refuses_without_push(self):
        self.w.advance()
        result = self.w.run()
        self.assertEqual(result["status"], "failed")
        self.assertIn("differs from reviewed", result["reason"])
        self.assertEqual(self.w.pushes, [])

    def test_exact_result_with_wrong_parent_refuses(self):
        delivered = self.w.deliver()
        self.w.pushes.clear()
        self.w.advance(tree=self.w.result_tree, parent=delivered["delivered_sha"])
        self.assertEqual(self.w.run()["status"], "failed")
        self.assertEqual(self.w.pushes, [])

    def test_changed_patch_payload_or_complete_tree_refuses(self):
        w = self.w
        for mutation in ("patch", "payload", "tree"):
            with self.subTest(mutation=mutation):
                path = w.owner / (delivery.PATCH if mutation == "patch" else delivery.PATHS[1])
                original = path.read_bytes()
                value = copy.deepcopy(w.value)
                if mutation == "tree":
                    w.value["result_tree"] = "1" * 40
                else:
                    path.write_bytes(original + b"\n")
                w.write_manifest()
                self.assert_refused(w.run())
                path.write_bytes(original)
                w.value = value
                w.write_manifest()

    def test_symlink_unexpected_mode_extra_path_and_missing_blob_refuse(self):
        w = self.w
        for bad in ("symlink", "mode", "extra", "missing"):
            with self.subTest(bad=bad):
                value = copy.deepcopy(w.value)
                if bad == "symlink":
                    w.value["after"][delivery.PATHS[1]][0] = "120000"
                elif bad == "mode":
                    w.value["before"][delivery.WORKFLOW][0] = "100755"
                elif bad == "extra":
                    w.value["after"]["product.txt"] = w.value["after"][delivery.WORKFLOW]
                else:
                    w.value["after"][delivery.WORKFLOW][2] = "f" * 40
                w.write_manifest()
                self.assert_refused(w.run())
                w.value = value
                w.write_manifest()

    def test_extra_patch_path_refuses_even_with_updated_patch_hash(self):
        w = self.w
        path = w.owner / delivery.PATCH
        patch = path.read_bytes() + b"diff --git a/extra b/extra\nnew file mode 100644\n--- /dev/null\n+++ b/extra\n@@ -0,0 +1 @@\n+unapproved\n"
        path.write_bytes(patch)
        w.value["patch_sha256"] = delivery.digest(patch)
        git(w.projects, "read-tree", w.base)
        git(w.projects, "apply", "--cached", data=patch)
        w.value["result_tree"] = git(w.projects, "write-tree")
        w.write_manifest()
        self.assert_refused(w.run(), "outside the three-path")

    def test_owner_source_and_qualification_bindings_refuse(self):
        qualified = self.w.run()
        for extra in ({"G6_QUALIFICATION": "failure"}, {"G6_PLAN": "{}"}, {"G6_OWNER_SOURCE": "f" * 40},
                      {"GITHUB_REF": "refs/heads/feature"}, {"GITHUB_EVENT_NAME": "push"}):
            with self.subTest(extra=extra):
                context = {"G6_QUALIFICATION": "success", "G6_PLAN": json.dumps(qualified["plan"])} | extra
                self.assert_refused(self.w.run("deliver", **context))

    def test_owner_advance_or_uncommitted_payload_refuses(self):
        w = self.w
        qualified = w.run()
        (w.owner / "foreign").write_text("owner advanced\n")
        w.write_manifest()
        self.assert_refused(w.deliver(qualified), "binding mismatch")
        path = w.owner / delivery.PATHS[1]
        path.write_bytes(path.read_bytes() + b"uncommitted")
        self.assert_refused(w.run(), "local owner payload differs")

    def test_push_refusal_retains_exact_operation_no_retry_and_redacts_token(self):
        self.w.refuse = True
        result = self.w.deliver()
        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["failed_operation"].startswith("git push "))
        self.assertEqual(len(self.w.pushes), 1)
        self.assertFalse(result["delivered_sha"])
        self.assertEqual(git(self.w.remote, "rev-parse", "main"), self.w.base)
        self.assertNotIn(self.w.token.encode(), self.w.report_path.read_bytes())

    def test_main_races_never_retry_rebase_or_reapply(self):
        for phase in ("before", "after"):
            with self.subTest(phase=phase):
                self.w.race = phase
                result = self.w.deliver()
                self.assertEqual(result["status"], "failed")
                self.assertEqual(len(self.w.pushes), 1)
                self.assertIn("push" if phase == "before" else "after push", result["failed_operation"])
                git(self.w.remote, "update-ref", "refs/heads/main", self.w.base)
                self.w.pushes.clear()

    def test_missing_scoped_app_token_writes_nothing(self):
        self.w.token = ""
        self.assert_refused(self.w.deliver(), "App token unavailable")

    def test_pending_owner_gate_fails_closed_in_qualification_cli(self):
        self.w.value["pre_push_gate"] = "pending-owner-decision"
        self.w.write_manifest()
        result, output = self.w.cli_qualify()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(output, "")
        receipt = json.loads(self.w.report_path.read_bytes())
        self.assert_refused(receipt, "pending owner decision")
        self.assertEqual(receipt["failed_operation"], "verify source-bound pre-push owner gate")

    def test_isolated_qualification_cli_publishes_exact_receipt_plan(self):
        result, output = self.w.cli_qualify()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout + result.stderr, b"")
        values = dict(line.split("=", 1) for line in output.splitlines())
        self.assertEqual(set(values), {"plan"})
        self.assertEqual(json.loads(values["plan"]), json.loads(self.w.report_path.read_bytes())["plan"])

    def test_behavioral_failure_generates_receipt_without_plan(self):
        result, output = self.w.cli_qualify(G6_BEHAVIORAL_RESULT="failure")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(output, "")
        receipt = json.loads(self.w.report_path.read_bytes())
        self.assertEqual(receipt["failed_operation"], "verify secret-free behavioral suites")
        self.assertIsNone(receipt["plan"])

    def test_final_owner_and_projects_rereads_refuse_before_push(self):
        for repository in (rt.CICD, delivery.PROJECTS):
            with self.subTest(repository=repository):
                qualified = self.w.run()
                self.w.final_race = repository
                result = self.w.deliver(qualified)
                self.assertEqual(result["status"], "failed")
                self.assertEqual(self.w.pushes, [])
                self.assertIn("main before push", result["failed_operation"])
                remote = self.w.owner_remote if repository == rt.CICD else self.w.remote
                git(remote, "update-ref", "refs/heads/main", self.w.sha if repository == rt.CICD else self.w.base)
                self.w.final_race = None

    def test_unchanged_requires_token_and_final_source_confirmations(self):
        delivered = self.w.deliver()
        self.w.pushes.clear()
        qualified = self.w.run()
        for repository in (rt.CICD, delivery.PROJECTS):
            with self.subTest(repository=repository):
                self.w.final_race = repository
                result = self.w.deliver(qualified)
                self.assertEqual(result["status"], "failed")
                self.assertIn("unchanged confirmation", result["failed_operation"])
                self.assertEqual(self.w.pushes, [])
                remote = self.w.owner_remote if repository == rt.CICD else self.w.remote
                git(remote, "update-ref", "refs/heads/main", self.w.sha if repository == rt.CICD else delivered["delivered_sha"])
        self.w.final_race = None
        self.w.token = ""
        result = self.w.deliver(qualified)
        self.assertEqual(result["failed_operation"], "require scoped Projects App token")
        self.assertEqual(self.w.pushes, [])

    def test_ambiguous_accepted_push_retains_candidate_and_reconciles_without_retry(self):
        for outcome, reread_fails in (("error", False), ("timeout", False), ("error", True)):
            with self.subTest(outcome=outcome, reread_fails=reread_fails):
                self.w.push_outcome = outcome
                self.w.fail_reconciliation = reread_fails
                result = self.w.deliver()
                self.assertEqual(result["status"], "failed")
                self.assertEqual(len(self.w.pushes), 1)
                self.assertEqual(result["candidate_sha"], self.w.pushes[0])
                self.assertEqual(result["candidate_tree"], self.w.result_tree)
                self.assertTrue(result["failed_operation"].startswith("git push "))
                self.assertIn("timed out" if outcome == "timeout" else "push failed", result["reason"])
                self.assertEqual(result["reconciliation"]["status"], "unavailable" if reread_fails else "observed")
                self.assertEqual(result["delivered_sha"], None if reread_fails else result["candidate_sha"])
                git(self.w.remote, "update-ref", "refs/heads/main", self.w.base)
                self.w.pushes.clear()
                self.w.fail_reconciliation = False

    def test_actual_push_stderr_is_retained_bounded_and_token_redacted(self):
        destination = self.w.root / (self.w.token + ".git")
        self.w.remote.rename(destination)
        self.w.remote = destination
        self.w.race = "before"
        result = self.w.deliver()
        self.assertEqual(result["status"], "failed")
        output = result["push_result"]["output"]
        self.assertIn("failed to push some refs", output)
        self.assertIn("[redacted]", output)
        self.assertNotIn(self.w.token, output)
        self.assertLessEqual(len(output), 2000)

    def test_production_manifest_is_closed_and_payload_matches_reviewed_blobs(self):
        value = delivery.manifest((ROOT / delivery.MANIFEST).read_bytes())
        self.assertEqual(value["pre_push_gate"], "reviewed-tree-owner-authorized")
        self.assertEqual(value["patch_sha256"], hashlib.sha256((ROOT / delivery.PATCH).read_bytes()).hexdigest())
        for path in delivery.PATHS[1:]:
            data = (ROOT / path).read_bytes()
            oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            self.assertEqual(oid, value["after"][path][2])


if __name__ == "__main__":
    unittest.main()
