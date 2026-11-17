"""Secret-free behavioral qualification of the fixed prerequisite dispatcher.

All transports and clocks enter through main(). Real Git creates immutable
source/tree/blob fixtures; no test request can reach the network.
"""
from __future__ import annotations

import base64
from email.message import Message
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("contracts_dispatch_under_test", ROOT / "tools/dispatch_contracts_prerequisite.py")
dispatch = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = dispatch
SPEC.loader.exec_module(dispatch)
TOKEN = "offline-test-token-never-a-real-credential"


def encoded(path, data):
    return {"type": "file", "path": path, "encoding": "base64", "size": len(data),
            "sha": dispatch.blob_sha(data), "content": base64.b64encode(data).decode()}


class Clock:
    def __init__(self):
        self.now, self.sleeps = 0.0, []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        assert 0 < seconds <= 10
        self.sleeps.append(seconds)
        self.now += seconds


class Response:
    def __init__(self, value, status=200, headers=None):
        self.data = value if isinstance(value, bytes) else json.dumps(value).encode()
        self.status = status
        self.headers = headers or {"X-GitHub-Request-Id": "offline-correlation-id"}

    def read(self, maximum):
        return self.data[:maximum]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Fixture:
    def __init__(self, root):
        self.root, self.owner, self.target = root, root / "owner", root / "target"
        self.owner.mkdir()
        self.target.mkdir()
        self.git(self.target, "init", "--quiet", "--initial-branch=main", "--template=")
        release = self.target / dispatch.RELEASE
        release.parent.mkdir(parents=True)
        release.write_bytes(b"name: previous release\non: workflow_dispatch\n")
        (self.target / "pins.txt").write_text("old pins\n")
        for path in dispatch.POLICY_PATHS:
            destination = self.target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(b"previous completed workflow policy\n")
        self.base = self.commit(self.target)
        self.base_tree = self.git(self.target, "rev-parse", "HEAD^{tree}").strip().decode()
        self.release_bytes = b"name: approved fixed publisher\non: workflow_dispatch\n"
        release.write_bytes(self.release_bytes)
        self.live = self.commit(self.target)
        self.result_tree = self.git(self.target, "rev-parse", "HEAD^{tree}").strip().decode()
        for path in set(dispatch.source_paths("eventstore")) | set(dispatch.source_paths("projects")):
            if path.startswith("docs/"):
                continue
            destination = self.owner / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / path).read_bytes())
        self.git(self.owner, "init", "--quiet", "--initial-branch=main", "--template=")
        for owner in dispatch.OWNERS:
            value = {"schema": "hexalith.contracts-prerequisites.v1", "repository": dispatch.OWNERS[owner],
                     "base_commit": self.base, "base_tree": self.base_tree, "result_tree": self.result_tree,
                     "after": {dispatch.RELEASE: ["100644", "blob", dispatch.blob_sha(self.release_bytes)]}}
            destination = self.owner / dispatch.proposal_path(owner)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(value))
        self.save_owner()

    def git(self, root, *args):
        # A separate plain environment prevents ambient credentials/config from
        # entering even these local fixture-construction subprocesses.
        result = subprocess.run(["git", "-C", str(root), *args], env=dispatch.rt.environment(),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, check=True)
        return result.stdout

    def commit(self, root):
        self.git(root, "add", "--all")
        self.git(root, "commit", "--quiet", "--no-gpg-sign", "--allow-empty", "-m", "build(test): fixture")
        return self.git(root, "rev-parse", "HEAD").strip().decode()

    def save_owner(self):
        self.source = self.commit(self.owner)
        paths = set(dispatch.source_paths("eventstore")) | set(dispatch.source_paths("projects"))
        if (self.owner / dispatch.POLICY_PROPOSAL).exists():
            paths.add(dispatch.POLICY_PROPOSAL)
        self.sources = {path: self.git(self.owner, "show", self.source + ":" + path) for path in paths}

    def change_proposal(self, owner, change):
        destination = self.owner / dispatch.proposal_path(owner)
        value = json.loads(destination.read_text())
        change(value)
        destination.write_text(json.dumps(value))
        self.save_owner()

    def pins_advance(self):
        (self.target / "pins.txt").write_text("later prerequisite pins\n")
        self.live = self.commit(self.target)

    def policy_correction(self, *, commit_proof=True):
        base = self.live
        base_tree = self.git(self.target, "rev-parse", base + "^{tree}").strip().decode()
        before, after = {}, {}
        for path in dispatch.POLICY_PATHS:
            destination = self.target / path
            before[path] = ["100644", "blob", dispatch.blob_sha(destination.read_bytes())]
            destination.write_bytes(b"approved fixed prerequisite workflow policy\n")
            after[path] = ["100644", "blob", dispatch.blob_sha(destination.read_bytes())]
        self.live = self.commit(self.target)
        tree = self.git(self.target, "rev-parse", self.live + "^{tree}").strip().decode()
        if commit_proof:
            destination = self.owner / dispatch.POLICY_PROPOSAL
            destination.write_text(json.dumps({"schema": "hexalith.contracts-prerequisites.v1",
                "repository": "Hexalith.Projects", "base_commit": base, "base_tree": base_tree,
                "result_tree": tree, "before": before, "after": after}))
            self.save_owner()

    def commit_object(self, source):
        rows = self.git(self.target, "cat-file", "commit", source).split(b"\n\n", 1)[0].splitlines()
        return {"sha": source, "tree": {"sha": next(row[5:].decode() for row in rows if row.startswith(b"tree "))},
                "parents": [{"sha": row[7:].decode()} for row in rows if row.startswith(b"parent ")]}


class Opener:
    def __init__(self, fixture, owner, report):
        self.fixture, self.owner, self.report = fixture, owner, report
        self.repository = dispatch.OWNERS[owner]
        self.prefix = "/repos/Hexalith/" + self.repository
        self.calls, self.posts = [], []
        self.pre_runs = [self.run(1)]
        self.post_runs = [self.run(1), self.run(2)]
        self.poll_batches = []
        self.owner_heads, self.target_heads = [], []
        self.inventory = {"total_count": 1, "repositories": [{"full_name": "Hexalith/" + self.repository}]}
        self.metadata = {"full_name": "Hexalith/" + self.repository, "default_branch": "main"}
        self.workflow = {"id": 81, "path": dispatch.RELEASE, "state": "active"}
        self.commit_change = None
        self.blob_change = None
        self.override = None
        self.post_error = None
        self.post_status = 200
        self.post_body = self.response_body(2)
        self.inventory_total = None
        self.request_delay = 0
        self.clock = None
        self.poll_started = None

    def run(self, identity):
        return {"id": identity, "path": dispatch.RELEASE, "workflow_id": 81,
                "head_sha": self.fixture.live, "head_branch": "main", "event": "workflow_dispatch",
                "actor": {"login": "hexalith-cicd[bot]"}, "run_attempt": 1,
                "repository": {"full_name": "Hexalith/" + self.repository},
                "html_url": "https://github.com/Hexalith/" + self.repository + "/actions/runs/" + str(identity)}

    def response_body(self, identity):
        return {"workflow_run_id": identity,
                "run_url": "https://api.github.com" + self.prefix + "/actions/runs/" + str(identity),
                "html_url": "https://github.com/Hexalith/" + self.repository + "/actions/runs/" + str(identity)}

    def open(self, request, *, timeout):
        parsed = urlsplit(request.full_url)
        assert parsed.scheme == "https" and parsed.netloc == "api.github.com"
        assert 0 < timeout <= 30
        assert request.get_header("X-github-api-version") == "2026-03-10"
        assert "MODULE_TOKEN" not in os.environ and "GITHUB_TOKEN" not in os.environ
        assert request.get_header("Authorization") == (None if parsed.path.startswith(dispatch.OWNER_PREFIX)
                                                       else "Bearer " + TOKEN)
        self.calls.append((request.get_method(), parsed.path, parsed.query, timeout))
        if self.posts and parsed.path.endswith("/runs") and self.poll_started is None:
            self.poll_started = self.clock.now
        if self.clock is not None:
            self.clock.now += min(timeout, self.request_delay)
        if self.override:
            response = self.override(request)
            if response is not None:
                return response
        query = parse_qs(parsed.query)
        if request.get_method() == "POST":
            checkpoint = json.loads(self.report.read_text())
            assert checkpoint["dispatch_attempted"] is True
            assert checkpoint["target_sha"] == self.fixture.live
            assert checkpoint["pre_dispatch_run_ids"] == sorted(run["id"] for run in self.pre_runs)
            payload = json.loads(request.data)
            assert parsed.path == self.prefix + "/actions/workflows/release.yml/dispatches"
            assert set(payload) == {"ref", "inputs"} and payload["ref"] == "main"
            assert set(payload["inputs"]) == {"release-profile"}
            assert payload["inputs"]["release-profile"] in dispatch.OPERATIONS.values()
            self.posts.append(payload)
            if self.post_error == "terminate":
                os.kill(os.getpid(), signal.SIGTERM)
            if self.post_error == "kill":
                os.kill(os.getpid(), signal.SIGKILL)
            if self.post_error:
                raise self.post_error
            return Response(b"" if self.post_status == 204 else self.post_body, self.post_status)
        if parsed.path == dispatch.OWNER_PREFIX + "/git/ref/heads/main":
            source = self.owner_heads.pop(0) if self.owner_heads else self.fixture.source
            return Response({"ref": "refs/heads/main", "object": {"type": "commit", "sha": source}})
        if parsed.path.startswith(dispatch.OWNER_PREFIX + "/contents/"):
            assert query == {"ref": [self.fixture.source]}
            path = parsed.path.removeprefix(dispatch.OWNER_PREFIX + "/contents/")
            if path not in self.fixture.sources:
                assert path == dispatch.POLICY_PROPOSAL
                raise HTTPError(request.full_url, 404, "missing optional fixed proposal", Message(), io.BytesIO())
            value = encoded(path, self.fixture.sources[path])
            if self.blob_change:
                self.blob_change(path, value)
            return Response(value)
        if parsed.path == "/installation/repositories":
            assert query == {"per_page": ["100"], "page": ["1"]}
            return Response(self.inventory)
        if parsed.path == self.prefix:
            return Response(self.metadata)
        if parsed.path == self.prefix + "/git/ref/heads/main":
            source = self.target_heads.pop(0) if self.target_heads else self.fixture.live
            return Response({"ref": "refs/heads/main", "object": {"type": "commit", "sha": source}})
        if parsed.path.startswith(self.prefix + "/git/commits/"):
            source = parsed.path.rsplit("/", 1)[1]
            value = self.fixture.commit_object(source)
            if self.commit_change:
                self.commit_change(value)
            return Response(value)
        if parsed.path == self.prefix + "/contents/" + dispatch.RELEASE:
            assert query == {"ref": [self.fixture.live]}
            return Response(encoded(dispatch.RELEASE, self.fixture.git(
                self.fixture.target, "show", self.fixture.live + ":" + dispatch.RELEASE)))
        if parsed.path == self.prefix + "/actions/workflows/release.yml":
            return Response(self.workflow)
        if parsed.path == self.prefix + "/actions/workflows/release.yml/runs":
            assert query["event"] == ["workflow_dispatch"] and query["branch"] == ["main"]
            assert query["head_sha"] == [self.fixture.live]
            page = int(query["page"][0])
            if self.posts and self.poll_batches:
                runs = self.poll_batches.pop(0)
            else:
                runs = self.post_runs if self.posts else self.pre_runs
            return Response({"total_count": len(runs) if self.inventory_total is None else self.inventory_total,
                             "workflow_runs": runs[(page - 1) * 100:page * 100]})
        raise AssertionError("unexpected offline endpoint: " + parsed.path)


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fixed-owner-dispatch-test-")
        self.addCleanup(self.temporary.cleanup)
        self.fixture = Fixture(Path(self.temporary.name))
        self.sequence = 0

    def context(self, owner, operation):
        return {"GITHUB_REPOSITORY": "Hexalith/Hexalith.CiCd", "GITHUB_REF": "refs/heads/main",
                "GITHUB_RUN_ID": "100", "GITHUB_RUN_ATTEMPT": "1",
                "GITHUB_EVENT_NAME": "workflow_dispatch",
                "GITHUB_WORKFLOW_REF": "Hexalith/Hexalith.CiCd/" + dispatch.WORKFLOW + "@refs/heads/main",
                "PREREQUISITE_OWNER_SOURCE": self.fixture.source, "GITHUB_SHA": self.fixture.source,
                "GITHUB_WORKFLOW_SHA": self.fixture.source, "PREREQUISITE_OWNER": owner,
                "PREREQUISITE_OPERATION": operation, "PREREQUISITE_BEHAVIORAL_RESULT": "success",
                "PREREQUISITE_WRITER_STATUS": "success", "PREREQUISITE_TOKEN_RESULT": "success",
                "PREREQUISITE_INSTALLATION_ID": "179966090", "PREREQUISITE_APP_SLUG": "hexalith-cicd",
                "MODULE_TOKEN": TOKEN, "GITHUB_TOKEN": "ambient-test-token-also-must-disappear"}

    def invoke(self, *, owner="eventstore", operation="publish", change=None, context=None,
               opener=None, report=None):
        self.sequence += 1
        report = report or self.fixture.root / ("receipt-" + str(self.sequence) + ".json")
        opener = opener or Opener(self.fixture, owner, report)
        clock = Clock()
        opener.clock = clock
        if change:
            change(opener)
        values = self.context(owner, operation)
        if context:
            values.update(context)
            values = {key: value for key, value in values.items() if value is not None}
        with patch.dict(os.environ, values, clear=True):
            code = dispatch.main([operation, "--owner", owner, "--report", str(report)],
                                 api=dispatch.API(opener=opener), clock=clock, sleep=clock.sleep,
                                 local_root=self.fixture.owner)
        return code, json.loads(report.read_text()), opener, clock

    def refused(self, **kwargs):
        code, receipt, opener, clock = self.invoke(**kwargs)
        self.assertEqual(code, 1, receipt)
        self.assertEqual(receipt["status"], "failed", receipt)
        self.assertFalse(receipt["dispatch_attempted"])
        self.assertEqual(opener.posts, [])
        return receipt

    def test_both_owners_both_operations_dispatch_exactly_once_and_correlate(self):
        for owner in dispatch.OWNERS:
            for operation, profile in dispatch.OPERATIONS.items():
                with self.subTest(owner=owner, operation=operation):
                    code, receipt, opener, clock = self.invoke(owner=owner, operation=operation)
                    self.assertEqual(code, 0, receipt)
                    self.assertEqual(opener.posts, [{"ref": "main", "inputs": {"release-profile": profile}}])
                    self.assertEqual(receipt["run"], {"id": 2, "url": "https://github.com/Hexalith/"
                        + dispatch.OWNERS[owner] + "/actions/runs/2", "head_sha": self.fixture.live,
                        "attempt": 1, "actor": "hexalith-cicd[bot]", "workflow": dispatch.RELEASE})
                    self.assertEqual(receipt["pre_dispatch_run_ids"], [1])
                    self.assertEqual(receipt["correlation"]["status"], "correlated")

    def test_wrong_owner_repository_ref_event_workflow_and_operation_bindings_refuse(self):
        invalid = {"GITHUB_REPOSITORY": "Hexalith/Hexalith.Projects", "GITHUB_REF": "refs/heads/other",
                   "GITHUB_EVENT_NAME": "push", "GITHUB_WORKFLOW_REF": "wrong-release.yml@refs/heads/main",
                   "PREREQUISITE_OWNER": "projects", "PREREQUISITE_OPERATION": "contracts-prerequisite"}
        for key, value in invalid.items():
            with self.subTest(key=key):
                self.refused(context={key: value})

    def test_source_requires_three_identical_full_lowercase_commit_identities(self):
        for key in ("PREREQUISITE_OWNER_SOURCE", "GITHUB_SHA", "GITHUB_WORKFLOW_SHA"):
            for value in ("a" * 40, "A" * 40, self.fixture.source[:12], "", None):
                with self.subTest(key=key, value=value):
                    self.refused(context={key: value})

    def test_missing_failed_skipped_qualification_or_cancelled_writer_refuse(self):
        for key in ("PREREQUISITE_BEHAVIORAL_RESULT", "PREREQUISITE_WRITER_STATUS"):
            for value in ("failure", "skipped", "cancelled", ""):
                with self.subTest(key=key, value=value):
                    self.refused(context={key: value})

    def test_workflow_rerun_without_prior_checkpoint_cannot_dispatch_again(self):
        for attempt in ("2", "", None):
            with self.subTest(attempt=attempt):
                self.refused(context={"GITHUB_RUN_ATTEMPT": attempt})

    def test_missing_failed_skipped_token_and_wrong_existing_app_identity_refuse(self):
        for key, value in (("MODULE_TOKEN", ""), ("PREREQUISITE_TOKEN_RESULT", "failure"),
                           ("PREREQUISITE_TOKEN_RESULT", "skipped"), ("PREREQUISITE_INSTALLATION_ID", "1"),
                           ("PREREQUISITE_APP_SLUG", "another-app")):
            with self.subTest(key=key):
                self.refused(context={key: value})

    def test_inventory_must_be_complete_exactly_one_chosen_repository(self):
        for value in ({}, {"total_count": 0, "repositories": []},
                      {"total_count": 1, "repositories": [{"full_name": "Hexalith/Hexalith.Projects"}]},
                      {"total_count": 2, "repositories": [{"full_name": "Hexalith/Hexalith.EventStore"}]},
                      {"total_count": 1, "repositories": [{"full_name": "Hexalith/Hexalith.EventStore"}] * 2}):
            with self.subTest(inventory=value):
                self.refused(change=lambda opener: setattr(opener, "inventory", value))

    def test_repository_default_branch_and_release_workflow_identity_refuse(self):
        for attribute, key, value in (("metadata", "full_name", "Hexalith/other"),
                                      ("metadata", "default_branch", "develop"),
                                      ("workflow", "path", ".github/workflows/other.yml"),
                                      ("workflow", "state", "disabled_manually"), ("workflow", "id", 0)):
            with self.subTest(attribute=attribute, key=key):
                self.refused(change=lambda opener: getattr(opener, attribute).__setitem__(key, value))

    def test_owner_main_stale_at_start_or_just_before_post_refuses(self):
        for heads in (["a" * 40], [self.fixture.source, "a" * 40]):
            with self.subTest(heads=heads):
                self.refused(change=lambda opener: setattr(opener, "owner_heads", heads.copy()))

    def test_target_main_advanced_just_before_post_refuses(self):
        self.refused(change=lambda opener: setattr(opener, "target_heads", [self.fixture.live, "a" * 40]))

    def test_every_local_script_runtime_workflow_suite_and_proposal_is_source_bound(self):
        for path in dispatch.source_paths("eventstore"):
            with self.subTest(path=path):
                destination = self.fixture.owner / path
                original = destination.read_bytes()
                try:
                    destination.write_bytes(original + b"\nchanged locally\n")
                    self.refused()
                finally:
                    destination.write_bytes(original)

    def test_local_source_symlink_is_refused(self):
        destination = self.fixture.owner / "tools/delivery_runtime.py"
        other = self.fixture.root / "copied-runtime.py"
        destination.rename(other)
        destination.symlink_to(other)
        self.refused()

    def test_committed_blob_body_hash_path_encoding_and_size_are_verified(self):
        for key, value in (("sha", "a" * 40), ("path", "different.py"), ("encoding", "none"),
                           ("size", dispatch.rt.MAX_JSON + 1), ("content", "*invalid*"), ("type", "symlink")):
            with self.subTest(key=key):
                self.refused(change=lambda opener: setattr(opener, "blob_change", lambda path, blob: blob.__setitem__(key, value)))

    def test_wrong_committed_proposal_repository_schema_and_release_scope_refuse(self):
        destination = self.fixture.owner / dispatch.proposal_path("eventstore")
        original = destination.read_bytes()
        changes = [lambda value: value.__setitem__("schema", "wrong"),
                   lambda value: value.__setitem__("repository", "Hexalith.Projects"),
                   lambda value: value.__setitem__("base_commit", "short"),
                   lambda value: value["after"].__setitem__("unrelated", ["100644", "blob", "a" * 40]),
                   lambda value: value["after"][dispatch.RELEASE].__setitem__(0, "120000")]
        for change in changes:
            with self.subTest(change=change):
                destination.write_bytes(original)
                self.fixture.change_proposal("eventstore", change)
                self.refused()

    def test_publish_requires_full_tree_and_exact_single_direct_parent(self):
        for change in (lambda commit: commit["tree"].__setitem__("sha", "a" * 40),
                       lambda commit: commit.__setitem__("parents", []),
                       lambda commit: commit.__setitem__("parents", [{"sha": "a" * 40}]),
                       lambda commit: commit["parents"].append({"sha": "a" * 40})):
            with self.subTest(change=change):
                self.refused(change=lambda opener: setattr(opener, "commit_change", change))

    def test_verify_permits_later_pin_changes_with_the_same_exact_release_blob(self):
        self.fixture.pins_advance()
        self.refused(operation="publish")
        code, receipt, opener, _ = self.invoke(operation="verify")
        self.assertEqual(code, 0, receipt)
        self.assertEqual(opener.posts[0]["inputs"], {"release-profile": "contracts-prerequisite-verify"})
        self.assertNotEqual(receipt["target_tree"], self.fixture.result_tree)

    def test_verify_rejects_a_later_changed_release_blob(self):
        (self.fixture.target / dispatch.RELEASE).write_bytes(b"name: unapproved release\n")
        self.fixture.live = self.fixture.commit(self.fixture.target)
        self.refused(operation="verify")

    def test_projects_publish_accepts_exact_committed_policy_result_and_single_base_parent(self):
        self.fixture.policy_correction()
        code, receipt, opener, _ = self.invoke(owner="projects")
        self.assertEqual(code, 0, receipt)
        self.assertEqual(receipt["publish_binding"]["profile"], "projects-prerequisite-policy")
        self.assertEqual(receipt["release_blob"], dispatch.blob_sha(self.fixture.release_bytes))
        self.assertEqual(len(opener.posts), 1)

    def test_policy_tree_without_committed_proof_cannot_publish(self):
        self.fixture.policy_correction(commit_proof=False)
        self.refused(owner="projects")

    def test_committed_policy_proof_requires_identical_present_local_bytes(self):
        self.fixture.policy_correction()
        destination = self.fixture.owner / dispatch.POLICY_PROPOSAL
        original = destination.read_bytes()
        destination.write_bytes(original + b"\nchanged locally\n")
        self.refused(owner="projects")
        destination.unlink()
        self.refused(owner="projects")

    def test_policy_proof_schema_repository_two_paths_modes_and_full_shas_are_closed(self):
        self.fixture.policy_correction()
        destination = self.fixture.owner / dispatch.POLICY_PROPOSAL
        original = destination.read_bytes()
        changes = [lambda value: value.__setitem__("schema", "other"),
                   lambda value: value.__setitem__("repository", "Hexalith.EventStore"),
                   lambda value: value.__setitem__("base_commit", "short"),
                   lambda value: value["after"].__setitem__(dispatch.RELEASE, ["100644", "blob", "a" * 40]),
                   lambda value: value["before"].pop("tests/tools/run-ci-workflow-gates.ps1"),
                   lambda value: value["after"]["tests/tools/run-ci-workflow-gates.ps1"].__setitem__(0, "120000")]
        for change in changes:
            with self.subTest(change=change):
                value = json.loads(original)
                change(value)
                destination.write_text(json.dumps(value))
                self.fixture.save_owner()
                self.refused(owner="projects")

    def test_policy_binding_still_requires_exact_tree_and_one_direct_parent(self):
        self.fixture.policy_correction()
        self.refused(owner="projects", change=lambda opener: setattr(opener, "commit_change",
                     lambda commit: commit["parents"].append({"sha": "a" * 40})))
        self.fixture.pins_advance()
        self.refused(owner="projects")
        code, receipt, _, _ = self.invoke(owner="projects", operation="verify")
        self.assertEqual(code, 0, receipt)

    def test_policy_binding_cannot_authorize_a_changed_release_workflow_blob(self):
        self.fixture.policy_correction()
        (self.fixture.target / dispatch.RELEASE).write_bytes(b"unapproved changed workflow\n")
        self.fixture.live = self.fixture.commit(self.fixture.target)
        destination = self.fixture.owner / dispatch.POLICY_PROPOSAL
        value = json.loads(destination.read_text())
        commit = self.fixture.commit_object(self.fixture.live)
        value.update(base_commit=commit["parents"][0]["sha"], result_tree=commit["tree"]["sha"])
        destination.write_text(json.dumps(value))
        self.fixture.save_owner()
        receipt = self.refused(owner="projects")
        self.assertIn("release workflow differs", receipt["reason"])

    def test_optional_policy_transport_error_or_null_is_not_treated_as_absence(self):
        for failure in ("http", "null"):
            def change(opener):
                def override(request):
                    if dispatch.POLICY_PROPOSAL in request.full_url:
                        if failure == "http":
                            raise HTTPError(request.full_url, 500, "unavailable", Message(), io.BytesIO())
                        return Response(None)
                    return None
                opener.override = override
            with self.subTest(failure=failure):
                self.refused(owner="projects", change=change)

    def test_pre_dispatch_inventory_bound_and_incomplete_inventory_refuse(self):
        for total in (1001, -1, 2, True):
            with self.subTest(total=total):
                self.refused(change=lambda opener: setattr(opener, "inventory_total", total))

    def test_paginated_pre_dispatch_inventory_and_exact_new_run(self):
        def change(opener):
            opener.pre_runs = [opener.run(identity) for identity in range(1, 102)]
            opener.post_runs = opener.pre_runs + [opener.run(102)]
            opener.post_body = opener.response_body(102)
        code, receipt, opener, _ = self.invoke(change=change)
        self.assertEqual(code, 0, receipt)
        self.assertEqual(len(receipt["pre_dispatch_run_ids"]), 101)
        self.assertEqual(receipt["run"]["id"], 102)

    def test_new_run_must_match_sha_bot_event_branch_workflow_repository_url_and_attempt(self):
        invalid = {"head_sha": "a" * 40, "actor": {"login": "github-actions[bot]"},
                   "event": "push", "head_branch": "other", "path": ".github/workflows/other.yml",
                   "workflow_id": 99, "repository": {"full_name": "Hexalith/other"},
                   "html_url": "https://example.org/steal", "run_attempt": 0}
        for key, value in invalid.items():
            with self.subTest(key=key):
                code, receipt, opener, clock = self.invoke(change=lambda opener: opener.post_runs[1].__setitem__(key, value))
                self.assertEqual(code, 1, receipt)
                self.assertEqual(receipt["status"], "unresolved")
                self.assertIsNone(receipt["run"])
                self.assertEqual(len(opener.posts), 1)
                self.assertLessEqual(clock.now, 60)
                self.assertEqual(receipt["correlation"]["other_new_ids"], [2])

    def test_returned_id_is_selected_independently_of_other_matching_runs(self):
        def change(opener):
            opener.post_runs[1]["display_title"] = "Full nightly release"
            opener.post_runs.append(opener.run(3))
            opener.post_body = opener.response_body(3)
        code, receipt, opener, _ = self.invoke(change=change)
        self.assertEqual(code, 0, receipt)
        self.assertEqual(receipt["correlation"]["candidate_ids"], [2, 3])
        self.assertEqual(receipt["run"]["id"], 3)
        self.assertEqual(len(opener.posts), 1)

    def test_only_preexisting_runs_remain_unresolved_within_sixty_seconds(self):
        code, receipt, opener, clock = self.invoke(change=lambda opener: setattr(opener, "post_runs", opener.pre_runs.copy()))
        self.assertEqual(code, 1)
        self.assertEqual(receipt["status"], "unresolved")
        self.assertEqual(clock.now, 60)
        self.assertLessEqual(max(clock.sleeps), 10)
        self.assertEqual(len(opener.posts), 1)

    def test_delayed_run_and_real_attempt_number_are_recorded(self):
        def change(opener):
            opener.poll_batches = [opener.pre_runs.copy()]
            opener.post_runs[1]["run_attempt"] = 2
        code, receipt, opener, clock = self.invoke(change=change)
        self.assertEqual(code, 0, receipt)
        self.assertEqual(receipt["run"]["attempt"], 2)
        self.assertEqual(clock.sleeps, [5])

    def test_new_api_dispatch_response_is_cross_checked_against_independent_inventory(self):
        def change(opener):
            other_operation = opener.run(3)
            other_operation["display_title"] = "Verify existing contracts prerequisite"
            opener.post_runs.append(other_operation)
        code, receipt, opener, _ = self.invoke(change=change)
        self.assertEqual(code, 0, receipt)
        self.assertEqual(receipt["dispatch_response"]["body"]["workflow_run_id"], 2)
        self.assertEqual(receipt["run"]["id"], 2)
        self.assertEqual(receipt["correlation"]["candidate_ids"], [2, 3])
        self.assertEqual(opener.posts, [{"ref": "main", "inputs": {"release-profile": "contracts-prerequisite"}}])

    def test_response_for_different_run_remains_unresolved_without_retry(self):
        def change(opener):
            opener.post_status = 200
            opener.post_body = {"workflow_run_id": 3,
                "run_url": "https://api.github.com" + opener.prefix + "/actions/runs/3",
                "html_url": "https://github.com/Hexalith/" + opener.repository + "/actions/runs/3"}
        code, receipt, opener, _ = self.invoke(change=change)
        self.assertEqual(code, 1)
        self.assertEqual(receipt["status"], "unresolved")
        self.assertIn("returned dispatch run not observed", receipt["correlation"]["reason"])
        self.assertEqual(len(opener.posts), 1)

    def test_invalid_response_id_or_urls_never_attribute_a_candidate_run(self):
        invalid = [("workflow_run_id", value) for value in (0, -1, "2", True, None)] + [
            ("run_url", "https://api.github.com/repos/Hexalith/other/actions/runs/2"),
            ("html_url", "https://github.com/Hexalith/other/actions/runs/2"),
            ("html_url", "https://example.org/actions/runs/2")]
        for key, value in invalid:
            with self.subTest(key=key, value=value):
                code, receipt, opener, _ = self.invoke(change=lambda opener: opener.post_body.__setitem__(key, value))
                self.assertEqual(code, 1, receipt)
                self.assertEqual(receipt["status"], "unresolved")
                self.assertIsNone(receipt["run"])
                self.assertEqual(receipt["correlation"]["candidate_ids"], [2])
                self.assertEqual(len(opener.posts), 1)

    def test_returned_preexisting_run_id_is_not_a_successful_dispatch(self):
        code, receipt, opener, _ = self.invoke(change=lambda opener: setattr(opener, "post_body", opener.response_body(1)))
        self.assertEqual(code, 1, receipt)
        self.assertEqual(receipt["status"], "unresolved")
        self.assertIsNone(receipt["run"])
        self.assertIn("already in the pre-dispatch inventory", receipt["reason"])
        self.assertEqual(len(opener.posts), 1)

    def test_204_with_only_unrelated_run_retains_unresolved_observations(self):
        code, receipt, opener, clock = self.invoke(change=lambda opener: setattr(opener, "post_status", 204))
        self.assertEqual(code, 1, receipt)
        self.assertEqual(receipt["status"], "unresolved")
        self.assertIsNone(receipt["run"])
        self.assertEqual(receipt["dispatch_response"]["http"]["status"], 204)
        self.assertEqual(receipt["correlation"]["candidate_ids"], [2])
        self.assertEqual(clock.now, 60)
        self.assertEqual(len(opener.posts), 1)

    def test_malformed_accepted_result_retains_only_unresolved_candidate_observations(self):
        for body in (None, {}, [], b"not-json"):
            with self.subTest(body=body):
                code, receipt, opener, _ = self.invoke(change=lambda opener: setattr(opener, "post_body", body))
                self.assertEqual(code, 1, receipt)
                self.assertEqual(receipt["status"], "unresolved")
                self.assertIsNone(receipt["run"])
                self.assertEqual(receipt["correlation"]["candidate_ids"], [2])
                self.assertEqual(len(opener.posts), 1)

    def test_lost_response_with_only_unrelated_run_is_unresolved_and_redacts_token(self):
        code, receipt, opener, _ = self.invoke(change=lambda opener: setattr(opener, "post_error", URLError(TOKEN)))
        self.assertEqual(code, 1, receipt)
        self.assertEqual(receipt["status"], "unresolved")
        self.assertIsNone(receipt["run"])
        self.assertEqual(receipt["correlation"]["candidate_ids"], [2])
        self.assertEqual(len(opener.posts), 1)
        self.assertIn("timed out", receipt["dispatch_error"])
        self.assertNotIn(TOKEN, json.dumps(receipt))

    def test_http_error_retains_request_correlation_without_body_or_token(self):
        def change(opener):
            headers = Message()
            headers["X-GitHub-Request-Id"] = "correlation-" + TOKEN
            opener.post_error = HTTPError("https://api.github.com", 403, TOKEN, headers, io.BytesIO(TOKEN.encode()))
            opener.post_runs.append(opener.run(3))
        code, receipt, opener, _ = self.invoke(change=change)
        self.assertEqual(code, 1)
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["correlation"]["status"], "refused")
        self.assertEqual(receipt["correlation"]["polls"], 0)
        self.assertIsNone(receipt["run"])
        self.assertEqual(receipt["dispatch_http_error"]["status"], 403)
        self.assertIn("[redacted]", receipt["dispatch_http_error"]["request_id"])
        self.assertNotIn(TOKEN, json.dumps(receipt))
        self.assertEqual(len(opener.posts), 1)
        code, repeated, _, _ = self.invoke(report=opener.report, opener=opener)
        self.assertEqual(code, 1, repeated)
        self.assertEqual(repeated["status"], "failed")
        self.assertEqual(repeated["correlation"]["polls"], 0)
        self.assertEqual(len(opener.posts), 1)

    def test_returned_identity_can_be_observed_later_under_current_main_without_repost(self):
        report = self.fixture.root / "durable-attempt.json"
        opener = Opener(self.fixture, "eventstore", report)
        opener.post_runs = opener.pre_runs.copy()
        code, receipt, _, _ = self.invoke(report=report, opener=opener)
        self.assertEqual(code, 1)
        self.assertTrue(receipt["dispatch_attempted"])
        opener.post_runs.append(opener.run(2))
        code, receipt, _, _ = self.invoke(report=report, opener=opener)
        self.assertEqual(code, 0, receipt)
        self.assertTrue(receipt["recovery_only"])
        self.assertEqual(len(opener.posts), 1)

    def test_lost_identity_cannot_be_recovered_by_attributing_a_later_candidate(self):
        report = self.fixture.root / "lost-response.json"
        opener = Opener(self.fixture, "eventstore", report)
        opener.post_error = URLError("response lost")
        self.invoke(report=report, opener=opener)
        code, receipt, _, _ = self.invoke(report=report, opener=opener)
        self.assertEqual(code, 1, receipt)
        self.assertEqual(receipt["status"], "unresolved")
        self.assertIsNone(receipt["run"])
        self.assertEqual(receipt["correlation"]["candidate_ids"], [2])
        self.assertEqual(len(opener.posts), 1)

    def test_prior_attempt_still_requires_current_main_for_automated_observation(self):
        report = self.fixture.root / "older-source-attempt.json"
        opener = Opener(self.fixture, "eventstore", report)
        opener.post_runs = opener.pre_runs.copy()
        self.invoke(report=report, opener=opener)
        opener.owner_heads = ["a" * 40]
        code, receipt, _, _ = self.invoke(report=report, opener=opener)
        self.assertEqual(code, 1, receipt)
        self.assertIn("not current exact CiCd main", receipt["reason"])
        self.assertEqual(len(opener.posts), 1)

    def test_correlated_attempt_reinvocation_never_posts_again(self):
        report = self.fixture.root / "correlated-attempt.json"
        opener = Opener(self.fixture, "eventstore", report)
        self.assertEqual(self.invoke(report=report, opener=opener)[0], 0)
        self.assertEqual(self.invoke(report=report, opener=opener)[0], 0)
        self.assertEqual(len(opener.posts), 1)

    def test_prior_attempt_wrong_operation_cannot_be_rebound_or_retried(self):
        report = self.fixture.root / "prior-operation.json"
        opener = Opener(self.fixture, "eventstore", report)
        self.invoke(report=report, opener=opener)
        code, receipt, _, _ = self.invoke(operation="verify", report=report, opener=opener)
        self.assertEqual(code, 1)
        self.assertTrue(receipt["dispatch_attempted"])
        self.assertEqual(receipt["operation"], "publish")
        self.assertEqual(len(opener.posts), 1)

    def test_sigterm_and_keyboard_interrupt_leave_attempt_checkpoint_and_do_not_retry(self):
        for interruption in ("terminate", KeyboardInterrupt()):
            with self.subTest(interruption=interruption):
                report = self.fixture.root / ("interrupted-" + str(self.sequence) + ".json")
                opener = Opener(self.fixture, "eventstore", report)
                opener.post_error = interruption
                code, receipt, _, _ = self.invoke(report=report, opener=opener)
                self.assertEqual(code, 1)
                self.assertTrue(receipt["dispatch_attempted"])
                self.assertTrue(receipt["interrupted"])
                opener.post_error = None
                code, receipt, _, _ = self.invoke(report=report, opener=opener)
                self.assertEqual(code, 1, receipt)
                self.assertEqual(receipt["status"], "unresolved")
                self.assertIsNone(receipt["run"])
                self.assertEqual(receipt["correlation"]["candidate_ids"], [2])
                self.assertEqual(len(opener.posts), 1)

    def test_unreadable_prior_checkpoint_is_preserved_and_never_dispatches(self):
        report = self.fixture.root / "unreadable.json"
        report.write_text('{"dispatch_attempted": true, truncated')
        opener = Opener(self.fixture, "eventstore", report)
        for _ in range(2):
            with patch.dict(os.environ, self.context("eventstore", "publish"), clear=True):
                code = dispatch.main(["publish", "--owner", "eventstore", "--report", str(report)],
                                     api=dispatch.API(opener=opener), local_root=self.fixture.owner)
            self.assertEqual(code, 1)
            self.assertEqual(report.read_text(), '{"dispatch_attempted": true, truncated')
            self.assertFalse(opener.posts)

    def test_api_rejects_duplicate_non_json_oversized_and_redirected_source_responses(self):
        for body in (b'{"ref":0,"ref":1}', b'{"value":NaN}', b"x" * (dispatch.rt.MAX_JSON + 1)):
            with self.subTest(body_length=len(body)):
                self.refused(change=lambda opener: setattr(opener, "override", lambda request: Response(body)))
        def redirected(opener):
            def redirect(request):
                raise HTTPError(request.full_url, 302, "redirect", Message(), io.BytesIO())
            opener.override = redirect
        self.refused(change=redirected)

    def test_initial_failure_receipt_survives_token_mint_failure_with_diagnosis(self):
        report = self.fixture.root / "initial-failure.json"
        report.write_text(json.dumps({"schema": dispatch.SCHEMA, "status": "failed", "dispatch_attempted": False}))
        receipt = self.refused(report=report, context={"MODULE_TOKEN": "", "PREREQUISITE_TOKEN_RESULT": "failure"})
        self.assertEqual(receipt["invocation"]["PREREQUISITE_TOKEN_RESULT"], "failure")
        self.assertEqual(receipt["failed_operation"], "verify scoped existing App token")

    def test_unknown_owner_operation_or_profile_is_rejected_before_api_use(self):
        report = self.fixture.root / "invalid-arguments.json"
        opener = Opener(self.fixture, "eventstore", report)
        for arguments in (["publish", "--owner", "arbitrary-repo"],
                          ["contracts-prerequisite", "--owner", "eventstore"],
                          ["publish", "--owner", "eventstore", "--profile", "upload"]):
            with self.subTest(arguments=arguments), patch("sys.stderr", io.StringIO()):
                with self.assertRaises(SystemExit):
                    dispatch.main(arguments + ["--report", str(report)], api=dispatch.API(opener=opener))
                self.assertFalse(opener.calls)

    def test_poll_budget_includes_network_time_and_shortens_final_request_timeout(self):
        def change(opener):
            opener.post_runs = opener.pre_runs.copy()
            opener.request_delay = 30
        code, receipt, opener, clock = self.invoke(change=change)
        self.assertEqual(code, 1)
        self.assertLessEqual(clock.now - opener.poll_started, 60)
        self.assertLess(opener.calls[-1][3], 30)
        self.assertEqual(len(opener.posts), 1)

    def test_sigkill_preserves_the_pre_post_checkpoint_and_recovery_never_reposts(self):
        report = self.fixture.root / "hard-kill.json"
        child = os.fork()
        if child == 0:
            try:
                opener = Opener(self.fixture, "eventstore", report)
                opener.post_error = "kill"
                self.invoke(report=report, opener=opener)
            finally:
                os._exit(99)
        _, status = os.waitpid(child, 0)
        self.assertTrue(os.WIFSIGNALED(status))
        self.assertEqual(os.WTERMSIG(status), signal.SIGKILL)
        retained = json.loads(report.read_text())
        self.assertTrue(retained["dispatch_attempted"])
        self.assertEqual(retained["pre_dispatch_run_ids"], [1])
        self.assertEqual(retained["correlation"]["status"], "unresolved")
        opener = Opener(self.fixture, "eventstore", report)
        opener.posts = [{"previous": "accepted but killed before response"}]
        code, receipt, opener, _ = self.invoke(report=report, opener=opener)
        self.assertEqual(code, 1, receipt)
        self.assertEqual(receipt["status"], "unresolved")
        self.assertIsNone(receipt["run"])
        self.assertEqual(receipt["correlation"]["candidate_ids"], [2])
        self.assertFalse([call for call in opener.calls if call[0] == "POST"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
