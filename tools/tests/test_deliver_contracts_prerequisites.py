#!/usr/bin/env python3
"""Offline behavioral qualification using real Git objects and private indexes."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


delivery = load(ROOT / "tools/deliver_contracts_prerequisites.py", "_contracts_behavioral_tests")
rt = delivery.rt


def allow_fixture_files(environment):
    result = environment.copy()
    index = int(result["GIT_CONFIG_COUNT"])
    result.update(GIT_CONFIG_COUNT=str(index + 1))
    result[f"GIT_CONFIG_KEY_{index}"] = "protocol.file.allow"
    result[f"GIT_CONFIG_VALUE_{index}"] = "always"
    return result


def git(root, *args, data=None, raw=False):
    result = subprocess.run(["git", "-C", str(root), *map(str, args)], input=data, capture_output=True,
                            env=allow_fixture_files(rt.environment()), check=True)
    return result.stdout if raw else result.stdout.decode().strip()


def items(root, revision):
    result = {}
    for row in git(root, "ls-tree", "-r", "-z", "--full-tree", revision, raw=True).split(b"\0"):
        if row:
            header, path = row.split(b"\t", 1)
            result[path.decode()] = header.decode().split()
    return result


def file_transport(runtime, remotes, repository, token, observer=None):
    """Replace only the network transport at the public invocation boundary."""
    class API:
        def pages(self, path, passed_token=None, *, field=None):
            if path != "/installation/repositories" or field != "repositories" or passed_token != token:
                raise AssertionError("unexpected authenticated API access")
            if observer:
                observer.api_reads.append(path)
                return observer.inventory
            return [{"full_name": "Hexalith/" + repository}]

        def get(self, path, passed_token=None, **options):
            if path != "/repos/Hexalith/" + repository or passed_token != token:
                raise AssertionError("unexpected repository API access")
            if observer:
                observer.api_reads.append(path)
                return observer.metadata
            return {"full_name": "Hexalith/" + repository, "default_branch": "main"}

    class Transport(runtime.Transport):
        def __init__(self):
            super().__init__(api=API())

        def remote(self, selected):
            if selected not in remotes:
                raise AssertionError("transport repository broadened")
            if observer:
                observer.before_remote(selected)
            return Path(remotes[selected]).as_uri()

        def configure(self, target, selected):
            super().configure(target, selected)
            target.env = allow_fixture_files(target.env)

        def module(self, target, selected):
            if token and any(token in value for value in target.env.values()):
                raise AssertionError("write token inherited by secret-free Git command")
            if observer:
                observer.before_read(selected)
            return super().module(target, selected)

        def push(self, target, selected, revision, passed_token):
            if selected != repository or passed_token != token:
                raise AssertionError("write repository/token broadened")
            if observer:
                observer.pushes.append(revision)
                if observer.push_mode == "refuse":
                    return 1, ("denied " + token + "\n" + "x" * 4000).encode()
                if observer.push_mode == "race-before":
                    observer.advance()
            result = super().push(target, selected, revision, passed_token)
            if observer:
                if observer.push_mode == "accepted-error":
                    return 1, b"server accepted write; connection lost"
                if observer.push_mode == "accepted-timeout":
                    raise runtime.DeliveryError("Git push timed out; remote outcome is ambiguous; no retry")
                if observer.push_mode == "accepted-interrupt":
                    raise KeyboardInterrupt("accepted push interrupted before final receipt")
            return result
    return Transport()


class Workspace:
    def __init__(self, root, profile="projects-pins"):
        self.root = Path(root)
        self.root.mkdir()
        self.profile = profile
        self.config = delivery.configuration(profile)
        self.repository = self.config["repository"]
        self.product = self.root / "product"
        self.product.mkdir()
        git(self.product, "init", "--quiet", "--initial-branch=main")
        for path in self.config["paths"]:
            target = self.product / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(("original " + path + "\r\n").encode())
        (self.product / "foreign.txt").write_bytes(b"unchanged\r\nforeign\r\n")
        (self.product / ".gitattributes").write_text("* filter=poison\n")
        (self.product / ".gitmodules").write_text('[submodule "Foreign"]\n path = references/Foreign\n url = https://invalid.example/unavailable\n')
        (self.product / "foreign-link").symlink_to("foreign.txt")
        (self.product / "executable").write_bytes(b"#!/bin/sh\nexit 99\n")
        (self.product / "executable").chmod(0o755)
        git(self.product, "add", ".")
        git(self.product, "commit", "--quiet", "-m", "test: initial source")
        initial = git(self.product, "rev-parse", "HEAD")
        git(self.product, "update-index", "--add", "--cacheinfo", "160000", initial, "references/Foreign")
        git(self.product, "commit", "--quiet", "-m", "test: preserve foreign gitlink")
        self.base = git(self.product, "rev-parse", "HEAD")
        self.base_tree = git(self.product, "rev-parse", "HEAD^{tree}")
        self.before = items(self.product, self.base)
        for path in self.config["paths"]:
            target = self.product / path
            target.write_bytes(target.read_bytes() + b"reviewed prerequisite\r\n")
        git(self.product, "add", "--", *self.config["paths"])
        self.patch = git(self.product, "diff", "--cached", "--binary", "--full-index", self.base, raw=True)
        self.result_tree = git(self.product, "write-tree")
        self.after = items(self.product, self.result_tree)
        self.value = {"schema": delivery.SCHEMA, "repository": self.repository,
                      "pre_push_gate": "reviewed-tree-owner-authorized", "base_commit": self.base,
                      "base_tree": self.base_tree, "result_tree": self.result_tree,
                      "patch_sha256": delivery.digest(self.patch), "validation_sha256": "0" * 64,
                      "before": {path: self.before[path] for path in self.config["paths"]},
                      "after": {path: self.after[path] for path in self.config["paths"]}}
        self.remote = self.root / "product.git"
        git(self.root, "clone", "--bare", "--quiet", self.product, self.remote)
        for key in ("uploadpack.allowFilter", "uploadpack.allowAnySHA1InWant"):
            git(self.remote, "config", key, "true")
        self.owner = self.root / "owner"
        self.owner.mkdir()
        git(self.owner, "init", "--quiet", "--initial-branch=main")
        for path in self.config["sources"]:
            if path in {self.config["manifest"], self.config["patch"], self.config["validation"], *self.config["logs"].values()}:
                continue
            target = self.owner / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / path).read_bytes())
        (self.owner / "setup").mkdir()
        (self.owner / "setup/Hexalith.Foreign.yml").write_text("{}\n")
        self.public_bodies = {delivery.public_url(fixed): ("repository-signed fixture " + fixed[0]).encode()
                              for fixed in delivery.PUBLICATIONS}
        self.publication_receipts = [{"status": "published-verified", "package_id": fixed[0], "version": fixed[1],
                                     "producer_source": fixed[2], "archive_sha256": fixed[3],
                                     "public_archive_sha256": delivery.digest(self.public_bodies[delivery.public_url(fixed)]),
                                     "payload_entries_verified": True} for fixed in delivery.PUBLICATIONS]
        self.write_proof()
        self.commit_owner()
        self.owner_remote = self.root / "owner.git"
        git(self.root, "clone", "--bare", "--quiet", self.owner, self.owner_remote)
        for key in ("uploadpack.allowFilter", "uploadpack.allowAnySHA1InWant"):
            git(self.owner_remote, "config", key, "true")
        self.report = self.root / "receipt.json"
        self.token = "inert-contracts-test-token"
        self.inventory = [{"full_name": "Hexalith/" + self.repository}]
        self.metadata = {"full_name": "Hexalith/" + self.repository, "default_branch": "main"}
        self.read_counts = {}
        self.fetches = []
        self.api_reads = []
        self.public_reads = []
        self.pushes = []
        self.push_mode = None
        self.read_race = None
        self.accepted_race = False
        self.fail_post_push_read = False
        self.transport = file_transport(rt, {rt.CICD: self.owner_remote, self.repository: self.remote},
                                        self.repository, self.token, self)

    def write_proof(self):
        logs = {}
        for name, path in self.config["logs"].items():
            data = (json.dumps({"publications": self.publication_receipts}) + "\n").encode() if (
                name == "package-qualification" and self.profile == "projects-pins") else (name + " fixture\n").encode()
            local = self.owner / path
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(data)
            logs[name] = data
        proof = {"schema": delivery.VALIDATION_SCHEMA, "status": "passed",
                 **{key: self.value[key] for key in ("base_commit", "base_tree", "result_tree", "patch_sha256")},
                 "checks": {name: {"status": "passed", "log_sha256": delivery.digest(logs[name])}
                            for name in delivery.CHECKS}}
        self.proof = proof
        self.save_proof()

    def save_proof(self):
        path = self.owner / self.config["validation"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.proof) + "\n")
        self.value["validation_sha256"] = delivery.digest(path.read_bytes())

    def commit_owner(self):
        path = self.owner / self.config["manifest"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.value) + "\n")
        (self.owner / self.config["patch"]).write_bytes(self.patch)
        git(self.owner, "add", ".")
        git(self.owner, "commit", "--quiet", "-m", "test: exact owner proposal")
        self.source = git(self.owner, "rev-parse", "HEAD")
        if hasattr(self, "owner_remote"):
            git(self.owner, "push", "--quiet", self.owner_remote, "HEAD:refs/heads/main")

    def context(self):
        return {"GITHUB_REPOSITORY": "Hexalith/Hexalith.CiCd", "GITHUB_REF": "refs/heads/main",
                "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_SHA": self.source, "GITHUB_WORKFLOW_SHA": self.source,
                "GITHUB_WORKFLOW_REF": "Hexalith/Hexalith.CiCd/" + delivery.WORKFLOW + "@refs/heads/main",
                "PREREQUISITE_OWNER_SOURCE": self.source, "PREREQUISITE_PROFILE": self.profile,
                "PREREQUISITE_BEHAVIORAL_RESULT": "success"}

    def run(self, operation="qualify", token=None, **overrides):
        self.read_counts.clear()
        return delivery.execute(operation, self.context() | overrides, self.report, profile=self.profile,
                                transport=self.transport, token=self.token if token is None and operation == "deliver" else token or "",
                                scratch=self.root, local_root=self.owner, public_fetch=self.public_fetch)

    def public_fetch(self, url):
        if url not in {delivery.public_url(fixed) for fixed in delivery.PUBLICATIONS}:
            raise AssertionError("public package request broadened")
        self.public_reads.append(url)
        return self.public_bodies.get(url)

    def commit_package_log(self, value):
        local = self.owner / self.config["logs"]["package-qualification"]
        local.write_text(json.dumps(value) + "\n")
        self.proof["checks"]["package-qualification"]["log_sha256"] = delivery.digest(local.read_bytes())
        self.save_proof()
        self.commit_owner()

    def deliver(self, qualified=None, **overrides):
        qualified = qualified if qualified is not None else self.run()
        return self.run("deliver", **({"PREREQUISITE_QUALIFICATION": "success",
                                       "PREREQUISITE_PLAN": json.dumps(qualified["plan"])} | overrides))

    def before_remote(self, selected):
        pass

    def before_read(self, selected):
        self.fetches.append(selected)
        count = self.read_counts[selected] = self.read_counts.get(selected, 0) + 1
        if self.read_race == (selected, count):
            self.advance(self.owner_remote if selected == rt.CICD else self.remote)
        if self.accepted_race and selected == self.repository and count == 2:
            git(self.owner_remote, "update-ref", "refs/heads/delivered/" + self.repository.swapcase(), self.source)
        if self.fail_post_push_read and self.pushes:
            raise rt.DeliveryError("post-push reconciliation unavailable")

    def advance(self, remote=None, tree=None, parent=None):
        remote = remote or self.remote
        head = git(remote, "rev-parse", "refs/heads/main")
        revision = git(remote, "commit-tree", tree or git(remote, "rev-parse", head + "^{tree}"),
                       "-p", parent or head, data=b"test: independent concurrent source\n")
        git(remote, "update-ref", "refs/heads/main", revision)
        return revision

    def cli(self, operation="qualify", **overrides):
        configuration = self.root / "transport.json"
        configuration.write_text(json.dumps({"source": str(self.owner / "tools/deliver_contracts_prerequisites.py"),
            "remotes": {rt.CICD: str(self.owner_remote), self.repository: str(self.remote)},
            "repository": self.repository, "token": self.token,
            "public_payloads": {url: data.decode() for url, data in self.public_bodies.items()}}))
        output = self.root / "outputs"
        output.unlink(missing_ok=True)
        result = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "transport-driver", str(configuration),
                                 operation, "--profile", self.profile, "--report", str(self.report)],
                                env=os.environ | self.context() | {"TMPDIR": str(self.root), "GITHUB_OUTPUT": str(output),
                                    "MODULE_TOKEN": self.token if operation == "deliver" else "", "CICD_TOKEN": "",
                                    "PYTHONPATH": "/invalid/poison", "GIT_DIR": "/invalid/poison"} | overrides,
                                capture_output=True)
        return result, output.read_text() if output.exists() else ""


class PrerequisiteDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.temporary.cleanup)
        self.serial = 0
        self.w = self.workspace()

    def workspace(self, profile="projects-pins"):
        self.serial += 1
        return Workspace(Path(self.temporary.name) / str(self.serial), profile)

    def refused(self, result, reason=None, workspace=None):
        workspace = workspace or self.w
        self.assertEqual(result["status"], "failed", result)
        self.assertTrue(result["failed_operation"])
        self.assertFalse(result["push_attempted"])
        self.assertIsNone(result["delivered_sha"])
        self.assertEqual(workspace.pushes, [])
        self.assertEqual(git(workspace.remote, "rev-parse", "main"), workspace.base)
        if reason:
            self.assertIn(reason, result["reason"])

    def snapshot(self, workspace):
        return [(root, (root / ".git/index").read_bytes(), git(root, "status", "--porcelain"), git(root, "show-ref"))
                for root in (workspace.product, workspace.owner)]

    def test_happy_each_profile_preserves_all_foreign_tree_entries_and_working_state(self):
        for profile in delivery.PROFILES:
            with self.subTest(profile=profile):
                w = self.workspace(profile)
                snapshots = self.snapshot(w)
                q = w.run()
                self.assertEqual(q["status"], "qualified", q)
                self.assertEqual(w.api_reads, [], "qualification must use no authenticated API")
                result = w.deliver(q)
                self.assertEqual(result["status"], "delivered", result)
                self.assertEqual(w.pushes, [result["candidate_sha"]])
                self.assertEqual(git(w.remote, "rev-parse", "main^{tree}"), w.result_tree)
                self.assertEqual(git(w.remote, "rev-list", "--parents", "-n", "1", "main").split(),
                                 [result["delivered_sha"], w.base])
                self.assertEqual(git(w.remote, "show", "-s", "--format=%B", "main") + "\n", w.config["message"].decode())
                actual = items(w.remote, "main")
                self.assertEqual(actual, w.after)
                for path in set(w.before) - set(w.config["paths"]):
                    self.assertEqual(actual[path], w.before[path])
                self.assertEqual(self.snapshot(w), snapshots)
                self.assertEqual(json.loads(w.report.read_text()), result)
                self.assertEqual([p["phase"] for p in result["full_writer_exclusion"]], ["delivery source verification", "push"])
                self.assertNotIn(w.token, w.report.read_text())

    def test_isolated_cli_qualifies_and_delivers_with_success_outputs_and_sanitized_environment(self):
        w = self.w
        result, output = w.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout + result.stderr, b"")
        self.assertTrue(output.startswith("plan="))
        qualified = json.loads(output.removeprefix("plan="))
        result, output = w.cli("deliver", PREREQUISITE_QUALIFICATION="success", PREREQUISITE_PLAN=json.dumps(qualified))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "")
        self.assertEqual(json.loads(w.report.read_text())["status"], "delivered")

    def test_cli_failed_behavior_writes_receipt_and_emits_no_plan(self):
        for status in ("failure", "skipped", "cancelled", ""):
            with self.subTest(status=status):
                result, output = self.w.cli(PREREQUISITE_BEHAVIORAL_RESULT=status)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(output, "")
                self.refused(json.loads(self.w.report.read_text()), "behavioral")

    def test_exact_dispatch_source_repo_ref_workflow_and_profile_are_required(self):
        cases = {"GITHUB_REPOSITORY": "Hexalith/Hexalith.Projects", "GITHUB_REF": "refs/heads/product",
                 "GITHUB_EVENT_NAME": "push", "GITHUB_WORKFLOW_REF": "Hexalith/Hexalith.CiCd/.github/workflows/deliver.yml@refs/heads/main",
                 "GITHUB_SHA": "a" * 40, "GITHUB_WORKFLOW_SHA": "a" * 40,
                 "PREREQUISITE_OWNER_SOURCE": "a" * 40, "PREREQUISITE_PROFILE": "projects-publisher"}
        for key, value in cases.items():
            with self.subTest(key=key):
                self.refused(self.w.run(**{key: value}))
        self.assertEqual(self.w.fetches, [])

    def test_failed_skipped_or_missing_behavior_and_qualification_are_refused(self):
        for field in ("PREREQUISITE_BEHAVIORAL_RESULT", "PREREQUISITE_QUALIFICATION"):
            for status in ("failure", "skipped", "cancelled", "", None):
                with self.subTest(field=field, status=status):
                    self.refused(self.w.deliver({"plan": {}}, **{field: status}))

    def test_each_exact_plan_field_and_unknown_fields_are_bound(self):
        w = self.w
        q = w.run()
        for field in (*q["plan"], "unknown"):
            with self.subTest(field=field):
                changed = copy.deepcopy(q)
                changed["plan"][field] = "different-reviewed-value"
                self.refused(w.deliver(changed), "binding mismatch")

    def test_plan_cannot_be_omitted_malformed_or_cross_profile(self):
        for raw in ("", "null", "[]", '{"duplicate":1,"duplicate":2}', '{"NaN":NaN}'):
            with self.subTest(raw=raw):
                self.refused(self.w.deliver({"plan": {}}, PREREQUISITE_PLAN=raw))

    def test_each_local_trusted_source_must_match_committed_source(self):
        w = self.w
        for path in w.config["sources"]:
            with self.subTest(path=path):
                local = w.owner / path
                original = local.read_bytes()
                local.write_bytes(original + b"tampered\n")
                self.refused(w.run(), "local owner payload differs")
                local.write_bytes(original)

    def test_symlink_trusted_source_is_refused(self):
        local = self.w.owner / self.w.config["patch"]
        data = local.read_bytes()
        sibling = local.with_name("foreign-copy.patch")
        sibling.write_bytes(data)
        local.unlink()
        local.symlink_to(sibling.name)
        self.refused(self.w.run(), "nonregular")

    def test_oversized_local_source_is_refused_before_unbounded_read(self):
        local = self.w.owner / self.w.config["patch"]
        with local.open("wb") as stream:
            stream.truncate(rt.MAX_JSON + 1)
        self.refused(self.w.run(), "source size limit")

    def test_manifest_cross_repository_unknown_fields_paths_modes_and_pending_owner_gate_refuse(self):
        cases = [("repository", "Hexalith.EventStore"), ("unknown", True), ("pre_push_gate", "pending-owner-decision"),
                 ("before", {"foreign.txt": ["100644", "blob", "a" * 40]}),
                 ("after", {path: ["100755", "blob", "a" * 40] for path in self.w.config["paths"]}),
                 ("after", {path: None for path in self.w.config["paths"]})]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                w = self.workspace()
                w.value[field] = value
                w.commit_owner()
                self.refused(w.run(), workspace=w)

    def test_patch_cannot_change_extra_path_even_when_full_result_hash_is_updated(self):
        w = self.w
        (w.product / "foreign.txt").write_bytes(b"forbidden foreign change\n")
        git(w.product, "add", "foreign.txt")
        w.patch = git(w.product, "diff", "--cached", "--binary", "--full-index", w.base, raw=True)
        w.value["patch_sha256"] = delivery.digest(w.patch)
        w.value["result_tree"] = git(w.product, "write-tree")
        w.write_proof()
        w.commit_owner()
        self.refused(w.run(), "exact prerequisite perimeter")

    def test_patch_hash_base_tree_result_tree_and_individual_blobs_are_bound(self):
        for kind in ("patch", "base_tree", "result_tree", "before", "after"):
            with self.subTest(kind=kind):
                w = self.workspace()
                if kind == "patch":
                    w.patch += b"changed patch bytes\n"
                elif kind in {"before", "after"}:
                    w.value[kind][w.config["paths"][0]][2] = "a" * 40
                else:
                    w.value[kind] = "a" * 40
                w.write_proof()
                w.commit_owner()
                self.refused(w.run(), workspace=w)

    def test_validation_hash_exact_tree_and_all_passed_named_log_hashes_are_required(self):
        mutations = ("unbound", "failed", "stale-tree", "missing-check", "extra-check", "failed-check", "skipped-check", "bad-log", "unknown-field")
        for kind in mutations:
            with self.subTest(kind=kind):
                w = self.workspace()
                check = next(iter(delivery.CHECKS))
                if kind == "unbound":
                    w.value["validation_sha256"] = "a" * 64
                elif kind == "failed":
                    w.proof["status"] = "failed"
                elif kind == "stale-tree":
                    w.proof["result_tree"] = "a" * 40
                elif kind == "missing-check":
                    del w.proof["checks"][check]
                elif kind == "extra-check":
                    w.proof["checks"]["extra"] = {"status": "passed", "log_sha256": "a" * 64}
                elif kind in {"failed-check", "skipped-check"}:
                    w.proof["checks"][check]["status"] = kind.removesuffix("-check")
                elif kind == "bad-log":
                    w.proof["checks"][check]["log_sha256"] = "not-a-hash"
                else:
                    w.proof["unknown"] = True
                if kind != "unbound":
                    w.save_proof()
                w.commit_owner()
                self.refused(w.run(), workspace=w)

    def test_missing_wrong_and_overbroad_token_fail_without_write(self):
        w = self.w
        q = w.run()
        self.refused(w.deliver(q, token=""), "token unavailable")
        for inventory in ([], [{"full_name": "Hexalith/Hexalith.EventStore"}],
                          [{"full_name": "Hexalith/" + w.repository}, {"full_name": "Hexalith/Hexalith.CiCd"}]):
            with self.subTest(inventory=inventory):
                w.inventory = inventory
                self.refused(w.deliver(q), "repository scope")

    def test_token_repository_metadata_identity_and_main_are_checked(self):
        w = self.w
        q = w.run()
        for metadata in ({}, {"full_name": "Hexalith/" + w.repository, "default_branch": "product"},
                         {"full_name": "Hexalith/Wrong", "default_branch": "main"}):
            with self.subTest(metadata=metadata):
                w.metadata = metadata
                self.refused(w.deliver(q), "App repository/main identity")

    def test_owner_advance_between_qualification_and_delivery_requires_requalification(self):
        w = self.w
        q = w.run()
        w.advance(w.owner_remote)
        self.refused(w.deliver(q), "not current exact CiCd main")

    def test_target_advance_between_qualification_and_delivery_requires_requalification(self):
        w = self.w
        q = w.run()
        advanced = w.advance(tree=w.result_tree)
        result = w.deliver(q)
        self.assertEqual(result["status"], "failed")
        self.assertIn("binding mismatch", result["reason"])
        self.assertFalse(result["push_attempted"])
        self.assertEqual(git(w.remote, "rev-parse", "main"), advanced)

    def test_owner_and_target_are_reread_immediately_before_push(self):
        for selected, count in ((rt.CICD, 2), (self.w.repository, 2), (self.w.repository, 3)):
            with self.subTest(repository=selected, read=count):
                w = self.workspace()
                q = w.run()
                w.read_race = (selected, count)
                result = w.deliver(q)
                self.assertEqual(result["status"], "failed", result)
                self.assertFalse(result["push_attempted"])
                self.assertEqual(w.pushes, [])
                self.assertIsNotNone(result["candidate_sha"])

    def test_each_profile_blocks_full_registry_and_live_accepted_ref_case_insensitively(self):
        for profile in delivery.PROFILES:
            for selector in ("registry", "accepted"):
                with self.subTest(profile=profile, selector=selector):
                    w = self.workspace(profile)
                    if selector == "registry":
                        (w.owner / ("setup/" + w.repository.swapcase() + ".yml")).write_text("{}\n")
                        w.commit_owner()
                    else:
                        git(w.owner_remote, "update-ref", "refs/heads/delivered/" + w.repository.swapcase(), w.source)
                    self.refused(w.run(), "full-delivery", w)

    def test_live_accepted_ref_added_after_qualification_blocks_final_push(self):
        w = self.w
        q = w.run()
        w.accepted_race = True
        self.refused(w.deliver(q), "live full-delivery accepted ref")
        self.assertEqual(len(json.loads(w.report.read_text())["full_writer_exclusion"]), 2)

    def test_atomic_owner_main_advertisement_detects_advance_after_fetch(self):
        w = self.w
        original = w.before_remote
        calls = 0
        def boundary(selected):
            nonlocal calls
            original(selected)
            if selected == rt.CICD:
                calls += 1
                # configure, fetch, then the atomic main/accepted advertisement.
                if calls == 3:
                    w.advance(w.owner_remote)
        w.before_remote = boundary
        self.refused(w.run(), "advertised owner main differs")

    def test_non_direct_child_with_exact_result_tree_is_refused(self):
        w = self.w
        w.advance()
        head = w.advance(tree=w.result_tree)
        result = w.run()
        self.assertEqual(result["status"], "failed", result)
        self.assertIn("direct child", result["reason"])
        self.assertEqual(git(w.remote, "rev-parse", "main"), head)
        self.assertEqual(w.pushes, [])

    def test_idempotent_exact_direct_child_is_qualified_then_confirmed_without_push(self):
        w = self.w
        child = w.advance(tree=w.result_tree)
        q = w.run()
        self.assertEqual(q["status"], "qualified", q)
        result = w.deliver(q)
        self.assertEqual(result["status"], "unchanged", result)
        self.assertEqual(result["delivered_sha"], child)
        self.assertFalse(result["push_attempted"])
        self.assertEqual(w.pushes, [])

    def test_idempotent_confirmation_still_requires_scope_and_current_sources(self):
        w = self.w
        w.advance(tree=w.result_tree)
        q = w.run()
        w.inventory = []
        result = w.deliver(q)
        self.assertEqual(result["status"], "failed")
        self.assertIn("repository scope", result["reason"])
        self.assertEqual(w.pushes, [])
        w.inventory = [{"full_name": "Hexalith/" + w.repository}]
        w.read_race = (w.repository, 3)
        result = w.deliver(q)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(w.pushes, [])

    def test_push_refusal_retains_sanitized_bounded_diagnostics_and_never_retries(self):
        w = self.w
        w.push_mode = "refuse"
        result = w.deliver()
        self.assertEqual(result["status"], "failed", result)
        self.assertTrue(result["push_attempted"])
        self.assertEqual(len(w.pushes), 1)
        self.assertEqual(git(w.remote, "rev-parse", "main"), w.base)
        self.assertEqual(result["reconciliation"]["main"], w.base)
        self.assertIsNone(result["delivered_sha"])
        self.assertLessEqual(len(result["push_result"]["output"]), 2000)
        self.assertIn("[redacted]", result["push_result"]["output"])
        self.assertNotIn(w.token, w.report.read_text())

    def test_real_nonforce_git_push_rejects_concurrent_target_main_and_retains_stderr(self):
        w = self.w
        w.push_mode = "race-before"
        result = w.deliver()
        self.assertEqual(result["status"], "failed", result)
        self.assertTrue(result["push_attempted"])
        self.assertEqual(len(w.pushes), 1)
        self.assertNotEqual(result["push_result"]["exit_code"], 0)
        self.assertIn("rejected", result["push_result"]["output"])
        self.assertNotEqual(git(w.remote, "rev-parse", "main"), result["candidate_sha"])

    def test_ambiguous_accepted_error_or_timeout_stays_failed_and_records_exact_published_tree_without_retry(self):
        for mode in ("accepted-error", "accepted-timeout"):
            with self.subTest(mode=mode):
                w = self.workspace()
                w.push_mode = mode
                result = w.deliver()
                self.assertEqual(result["status"], "failed", result)
                self.assertTrue(result["push_attempted"])
                self.assertEqual(len(w.pushes), 1)
                self.assertEqual(result["delivered_sha"], result["candidate_sha"])
                self.assertEqual(result["delivered_tree"], w.result_tree)
                self.assertEqual(result["reconciliation"]["parents"], [w.base])
                self.assertIn("ambiguous", result["reason"])

    def test_ambiguous_push_with_unavailable_reconciliation_retains_failure(self):
        w = self.w
        w.push_mode = "accepted-timeout"
        w.fail_post_push_read = True
        result = w.deliver()
        self.assertEqual(result["status"], "failed", result)
        self.assertEqual(result["reconciliation"]["status"], "unavailable")
        self.assertEqual(len(w.pushes), 1)
        self.assertIsNone(result["delivered_sha"])

    def test_post_push_main_advance_is_failed_without_retry_or_reapply(self):
        w = self.w
        w.read_race = (w.repository, 4)
        result = w.deliver()
        self.assertEqual(result["status"], "failed", result)
        self.assertIn("changed after push", result["reason"])
        self.assertEqual(len(w.pushes), 1)
        self.assertIsNone(result["delivered_sha"])

    def test_failed_proposal_does_not_change_any_source_index_worktree_or_remote(self):
        w = self.w
        w.value["result_tree"] = "a" * 40
        w.write_proof()
        w.commit_owner()
        snapshots = self.snapshot(w)
        self.refused(w.run(), "output tree mismatch")
        self.assertEqual(self.snapshot(w), snapshots)
        self.assertEqual(git(w.owner_remote, "rev-parse", "main"), w.source)

    def test_unknown_profile_has_structured_failure_without_transport(self):
        result = delivery.execute("qualify", {}, self.w.report, profile="arbitrary", transport=self.w.transport)
        self.assertEqual(result["status"], "failed")
        self.assertIn("unknown closed", result["reason"])
        self.assertFalse(result["push_attempted"])
        self.assertEqual(self.w.fetches, [])

    def test_both_exact_public_prerequisites_are_checked_during_qualification_and_before_push(self):
        w = self.w
        urls = [delivery.public_url(fixed) for fixed in delivery.PUBLICATIONS]
        q = w.run()
        self.assertEqual(q["status"], "qualified", q)
        self.assertEqual(w.public_reads, urls)
        result = w.deliver(q)
        self.assertEqual(result["status"], "delivered", result)
        self.assertEqual(w.public_reads, urls + urls)
        self.assertEqual(result["public_prerequisites"][0]["phase"], "before push/confirmation")
        self.assertEqual([item["package_id"] for item in result["public_prerequisites"][0]["publications"]],
                         [fixed[0] for fixed in delivery.PUBLICATIONS])

    def test_pins_require_exact_receipts_for_both_fixed_publications(self):
        fields = {"status": "qualified", "package_id": "Hexalith.Other.Contracts", "version": "9.9.9",
                  "producer_source": "a" * 40, "archive_sha256": "a" * 64,
                  "public_archive_sha256": "a" * 64, "payload_entries_verified": False}
        for package in range(2):
            for field, value in fields.items():
                with self.subTest(package=package, field=field):
                    w = self.workspace()
                    receipts = copy.deepcopy(w.publication_receipts)
                    receipts[package][field] = value
                    w.commit_package_log({"publications": receipts})
                    self.refused(w.run(), workspace=w)

    def test_absent_duplicate_missing_fields_or_unclosed_publication_logs_refuse(self):
        w = self.w
        receipts = w.publication_receipts
        cases = ({}, {"publications": []}, {"publications": receipts[:1]},
                 {"publications": [receipts[0], receipts[0]]}, {"publications": [{}, receipts[1]]},
                 {"publications": receipts, "url": "https://arbitrary.invalid/evil"})
        for value in cases:
            with self.subTest(value=value):
                w = self.workspace()
                w.commit_package_log(value)
                self.refused(w.run(), workspace=w)
                self.assertEqual(w.public_reads, [])

    def test_unavailable_changed_or_oversized_public_archive_refuses_each_package(self):
        for fixed in delivery.PUBLICATIONS:
            for body in (None, b"changed public archive", b"x" * (rt.MAX_JSON + 1)):
                with self.subTest(package=fixed[0], size=None if body is None else len(body)):
                    w = self.workspace()
                    w.public_bodies[delivery.public_url(fixed)] = body
                    self.refused(w.run(), workspace=w)

    def test_public_archive_is_rechecked_before_push_after_successful_qualification(self):
        for fixed in delivery.PUBLICATIONS:
            with self.subTest(package=fixed[0]):
                w = self.workspace()
                q = w.run()
                self.assertEqual(q["status"], "qualified", q)
                w.public_bodies[delivery.public_url(fixed)] = b"archive changed since qualification"
                self.refused(w.deliver(q), "public prerequisite archive SHA256 mismatch", w)

    def test_publishers_can_deliver_without_any_public_prerequisites(self):
        for profile in ("eventstore-publisher", "projects-publisher"):
            with self.subTest(profile=profile):
                w = self.workspace(profile)
                w.public_bodies = {}
                q = w.run()
                self.assertEqual(q["status"], "qualified", q)
                result = w.deliver(q)
                self.assertEqual(result["status"], "delivered", result)
                self.assertEqual(w.public_reads, [])

    def test_actual_committed_log_bytes_must_match_each_named_validation_digest(self):
        for check in delivery.CHECKS:
            with self.subTest(check=check):
                w = self.workspace()
                (w.owner / w.config["logs"][check]).write_bytes(b"unreviewed replacement log\n")
                w.commit_owner()
                self.refused(w.run(), "committed validation log SHA256 mismatch: " + check, w)

    def test_missing_committed_log_is_refused(self):
        w = self.w
        (w.owner / w.config["logs"]["scope-preservation"]).unlink()
        w.commit_owner()
        self.refused(w.run(), "local owner payload missing")

    def test_accepted_push_interruption_leaves_durable_attempt_and_candidate_without_retry(self):
        w = self.w
        q = w.run()
        w.push_mode = "accepted-interrupt"
        with self.assertRaises(KeyboardInterrupt):
            w.deliver(q)
        checkpoint = json.loads(w.report.read_text())
        self.assertTrue(checkpoint["push_attempted"])
        self.assertEqual(checkpoint["candidate_sha"], git(w.remote, "rev-parse", "main"))
        self.assertEqual(checkpoint["candidate_tree"], w.result_tree)
        self.assertEqual(len(w.pushes), 1)
        self.assertEqual(w.pushes, [checkpoint["candidate_sha"]])
        self.assertIsNone(checkpoint["delivered_sha"])
        self.assertIn("git push ", checkpoint["failed_operation"])
        self.assertNotIn(w.token, w.report.read_text())

    def test_production_public_fetch_rejects_arbitrary_urls_without_network(self):
        with self.assertRaises(rt.DeliveryError):
            delivery.fetch_public("https://arbitrary.invalid/package.nupkg")

    def test_projects_policy_round_trip_uses_only_two_fixed_paths_without_public_prerequisites(self):
        w = self.workspace("projects-prerequisite-policy")
        self.assertEqual(w.config["paths"], ("tests/tools/run-ci-workflow-gates.ps1", "tests/tools/test_run_ci_workflow_gates.py"))
        w.public_bodies = {}
        q = w.run()
        self.assertEqual(q["status"], "qualified", q)
        result = w.deliver(q)
        self.assertEqual(result["status"], "delivered", result)
        self.assertEqual(w.public_reads, [])
        changed = {path for path in w.before.keys() | w.after.keys() if w.before.get(path) != w.after.get(path)}
        self.assertEqual(changed, set(w.config["paths"]))

    def test_projects_policy_refuses_extra_path_even_with_bound_patch_and_result_tree(self):
        w = self.workspace("projects-prerequisite-policy")
        (w.product / "foreign.txt").write_bytes(b"forbidden policy extension\n")
        git(w.product, "add", "foreign.txt")
        w.patch = git(w.product, "diff", "--cached", "--binary", "--full-index", w.base, raw=True)
        w.value["patch_sha256"] = delivery.digest(w.patch)
        w.value["result_tree"] = git(w.product, "write-tree")
        w.write_proof()
        w.commit_owner()
        self.refused(w.run(), "exact prerequisite perimeter", w)


if __name__ == "__main__":
    if sys.argv[1:2] == ["transport-driver"]:
        config = json.loads(Path(sys.argv[2]).read_text())
        selected = load(Path(config["source"]), "_contracts_isolated_driver")
        raise SystemExit(selected.main(sys.argv[3:], transport=file_transport(selected.rt, config["remotes"],
                                                                             config["repository"], config["token"]),
                                       public_fetch=lambda url: config["public_payloads"][url].encode()))
    unittest.main(verbosity=2)
