#!/usr/bin/env python3
"""Offline real-Git controls for the fixed EventStore branch and draft-PR route."""
from __future__ import annotations

from contextlib import chdir, redirect_stderr
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.error import HTTPError

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


fixtures = load(ROOT / "tools/tests/test_deliver_contracts_prerequisites.py", "_eventstore_proposal_fixtures")
proposal = load(ROOT / "tools/propose_eventstore_contracts_prerequisite.py", "_eventstore_proposal_tests")
rt = proposal.rt
git = fixtures.git


class Workspace:
    def __init__(self, root):
        self.w = fixtures.Workspace(root, "eventstore-publisher")
        self.root = self.w.root
        for path in proposal.EXTRA_SOURCES:
            target = self.w.owner / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / path).read_bytes())
        self.w.commit_owner()
        self.pushes = []
        self.posts = 0
        self.pr_reads = 0
        self.push_mode = None
        self.post_mode = None
        self.read_counts = {}
        self.read_race = None
        self.inventory = [{"full_name": "Hexalith/Hexalith.EventStore"}]
        self.prs = []
        self.pr_forbidden = False
        workspace = self

        class API:
            def pages(self, path, token=None, *, field=None):
                if token != workspace.w.token:
                    raise AssertionError("unexpected token")
                if path == "/installation/repositories" and field == "repositories":
                    return workspace.inventory
                if path != proposal.QUERY or field is not None:
                    raise AssertionError("API route broadened")
                workspace.pr_reads += 1
                if workspace.pr_forbidden:
                    raise rt.DeliveryError("PR GET forbidden: HTTP 403")
                return copy.deepcopy(workspace.prs)

            def get(self, path, token=None):
                if path != "/repos/Hexalith/Hexalith.EventStore" or token != workspace.w.token:
                    raise AssertionError("API repository broadened")
                return {"full_name": "Hexalith/Hexalith.EventStore", "default_branch": "main"}

            def create(self, token):
                if token != workspace.w.token:
                    raise AssertionError("POST token broadened")
                workspace.posts += 1
                if workspace.post_mode == "forbidden":
                    raise rt.DeliveryError("draft PR POST refused: HTTP 403; no permission expansion")
                if workspace.post_mode == "unobserved":
                    raise rt.DeliveryError("draft PR POST transport failed; outcome is ambiguous; no retry")
                created = workspace.pr()
                workspace.prs = [created]
                if workspace.post_mode == "ambiguous":
                    raise rt.DeliveryError("draft PR POST transport failed; outcome is ambiguous; no retry")
                if workspace.post_mode == "interrupt":
                    raise KeyboardInterrupt("accepted POST interrupted")
                return copy.deepcopy(created)

        class Transport(proposal.Transport):
            def __init__(self):
                super().__init__(api=API())

            def remote(self, selected):
                if selected == rt.CICD:
                    return workspace.w.owner_remote.as_uri()
                if selected != proposal.REPOSITORY:
                    raise AssertionError("Git repository broadened")
                return workspace.w.remote.as_uri()

            def configure(self, target, selected):
                super().configure(target, selected)
                target.env = fixtures.allow_fixture_files(target.env)

            def module(self, target, selected):
                if any(workspace.w.token in value for value in target.env.values()):
                    raise AssertionError("token leaked into anonymous Git environment")
                count = workspace.read_counts[selected] = workspace.read_counts.get(selected, 0) + 1
                if workspace.read_race == (selected, count):
                    workspace.w.advance(workspace.w.owner_remote if selected == rt.CICD else workspace.w.remote)
                return super().module(target, selected)

            def push_branch(self, target, candidate, token):
                if token != workspace.w.token:
                    raise AssertionError("branch token differs")
                workspace.pushes.append((proposal.TARGET_REF, candidate))
                if workspace.push_mode == "refuse":
                    return 1, ("denied " + token + "\n" + "x" * 4000).encode()
                if workspace.push_mode == "race":
                    workspace.branch(tree=workspace.w.base_tree)
                if workspace.push_mode == "ancestor-race":
                    git(workspace.w.remote, "update-ref", proposal.TARGET_REF, workspace.w.base)
                result = super().push_branch(target, candidate, token)
                if workspace.push_mode == "ambiguous":
                    raise rt.DeliveryError("fixed branch push timed out; outcome is ambiguous; no retry")
                if workspace.push_mode == "interrupt":
                    raise KeyboardInterrupt("accepted push interrupted")
                return result
        self.transport = Transport()

    def context(self):
        return self.w.context() | {"GITHUB_WORKFLOW_REF": "Hexalith/Hexalith.CiCd/" + proposal.WORKFLOW + "@refs/heads/main"}

    def run(self, operation="qualify", qualified=None, token=None, **overrides):
        self.read_counts.clear()
        context = self.context()
        if operation != "qualify":
            context.update(PREREQUISITE_QUALIFICATION="success", PREREQUISITE_PLAN=json.dumps(qualified["plan"]))
        with chdir(self.root):
            return proposal.execute(operation, context | overrides, transport=self.transport,
                                    token=self.w.token if token is None and operation != "qualify" else token or "",
                                    scratch=self.root, local_root=self.w.owner)

    def propose(self):
        qualified = self.run()
        return qualified, self.run("propose", qualified)

    def branch(self, *, tree=None, parent=None):
        revision = git(self.w.remote, "commit-tree", tree or self.w.result_tree, "-p", parent or self.w.base,
                       data=b"test: fixed branch fixture\n")
        git(self.w.remote, "update-ref", proposal.TARGET_REF, revision)
        return revision

    def pr(self):
        branch = git(self.w.remote, "rev-parse", proposal.TARGET_REF)
        return {"number": 17, "state": "open", "draft": True, "title": proposal.TITLE, "body": proposal.BODY,
                "head": {"ref": proposal.BRANCH, "sha": branch, "repo": {"full_name": "Hexalith/Hexalith.EventStore"}},
                "base": {"ref": "main", "sha": self.w.base, "repo": {"full_name": "Hexalith/Hexalith.EventStore"}},
                "html_url": "https://github.com/Hexalith/Hexalith.EventStore/pull/17"}

    def receipt(self, operation):
        return json.loads((self.root / proposal.REPORTS[operation]).read_text())

    def cli(self, operation, **overrides):
        config = self.root / "cli-transport.json"
        config.write_text(json.dumps({"source": str(self.w.owner / "tools/propose_eventstore_contracts_prerequisite.py"),
                                      "remotes": {rt.CICD: str(self.w.owner_remote), proposal.REPOSITORY: str(self.w.remote)},
                                      "token": self.w.token}))
        output = self.root / "cli-outputs"
        output.unlink(missing_ok=True)
        result = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "transport-driver", str(config), operation],
                                cwd=self.root, capture_output=True,
                                env=os.environ | self.context() | {"TMPDIR": str(self.root), "GITHUB_OUTPUT": str(output),
                                    "GITHUB_RUN_ID": "123456", "GITHUB_RUN_ATTEMPT": "1", "CICD_TOKEN": "",
                                    "MODULE_TOKEN": self.w.token if operation != "qualify" else ""} | overrides)
        return result, output.read_text() if output.exists() else ""


class EventStoreProposalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.serial = 0
        self.w = self.workspace()

    def workspace(self):
        self.serial += 1
        return Workspace(self.root / str(self.serial))

    def test_exact_branch_only_preserves_main_all_foreign_objects_and_working_indexes(self):
        w = self.w
        snapshots = [(root, (root / ".git/index").read_bytes(), git(root, "status", "--porcelain"))
                     for root in (w.w.product, w.w.owner)]
        q, result = w.propose()
        self.assertEqual(q["status"], "qualified", q)
        self.assertEqual(result["status"], "proposed", result)
        self.assertEqual(w.pushes, [(proposal.TARGET_REF, result["candidate_sha"])])
        self.assertEqual(git(w.w.remote, "rev-parse", "main"), w.w.base)
        self.assertEqual(fixtures.items(w.w.remote, proposal.TARGET_REF), w.w.after)
        self.assertEqual(git(w.w.remote, "rev-list", "--parents", "-n", "1", proposal.TARGET_REF).split(),
                         [result["delivered_sha"], w.w.base])
        for root, index, status in snapshots:
            self.assertEqual((root / ".git/index").read_bytes(), index)
            self.assertEqual(git(root, "status", "--porcelain"), status)

    def test_cli_has_no_repository_ref_profile_title_or_body_inputs(self):
        for option in ("--target-ref", "--repository", "--profile", "--title", "--body"):
            for value in ("refs/heads/main", "refs/heads/unrelated"):
                with self.subTest(option=option, value=value), redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        proposal.main(["propose", option, value], transport=self.w.transport)
                    self.assertEqual(error.exception.code, 2)
        self.assertEqual(self.w.pushes, [])

    def test_wrong_owner_dispatch_ref_workflow_behavior_and_source_are_refused(self):
        cases = {"GITHUB_REPOSITORY": "Hexalith/Hexalith.EventStore", "GITHUB_REF": "refs/heads/other",
                 "GITHUB_WORKFLOW_REF": "Hexalith/Hexalith.CiCd/.github/workflows/deliver-contracts-prerequisites.yml@refs/heads/main",
                 "GITHUB_SHA": "a" * 40, "GITHUB_WORKFLOW_SHA": "a" * 40, "GITHUB_EVENT_NAME": "push",
                 "PREREQUISITE_BEHAVIORAL_RESULT": "skipped"}
        for field, value in cases.items():
            with self.subTest(field=field):
                result = self.w.run(**{field: value})
                self.assertEqual(result["status"], "failed", result)
        self.assertEqual(self.w.pushes, [])

    def test_helper_runtime_and_workflow_must_equal_committed_owner_bytes(self):
        for path in (*proposal.EXTRA_SOURCES, "tools/delivery_runtime.py", "tools/deliver_contracts_prerequisites.py"):
            with self.subTest(path=path):
                local = self.w.w.owner / path
                original = local.read_bytes()
                local.write_bytes(original + b"modified\n")
                result = self.w.run()
                self.assertEqual(result["status"], "failed")
                self.assertIn("source differs", result["reason"])
                local.write_bytes(original)

    def test_stale_owner_or_main_is_refused_without_any_branch_write(self):
        for selected in (rt.CICD, proposal.REPOSITORY):
            with self.subTest(repository=selected):
                w = self.workspace()
                w.w.advance(w.w.owner_remote if selected == rt.CICD else w.w.remote)
                result = w.run()
                self.assertEqual(result["status"], "failed", result)
                self.assertEqual(w.pushes, [])

    def test_final_owner_and_main_rereads_refuse_advance_after_qualification(self):
        for selected in (rt.CICD, proposal.REPOSITORY):
            with self.subTest(repository=selected):
                w = self.workspace()
                q = w.run()
                w.read_race = (selected, 2)
                result = w.run("propose", q)
                self.assertEqual(result["status"], "failed", result)
                self.assertFalse(result["push_attempted"])
                self.assertEqual(w.pushes, [])

    def test_wrong_tree_and_extra_changed_path_are_refused(self):
        for kind in ("tree", "path"):
            with self.subTest(kind=kind):
                w = self.workspace()
                if kind == "tree":
                    w.w.value["result_tree"] = "a" * 40
                else:
                    (w.w.product / "foreign.txt").write_bytes(b"forbidden extra path\n")
                    git(w.w.product, "add", "foreign.txt")
                    w.w.patch = git(w.w.product, "diff", "--cached", "--binary", "--full-index", w.w.base, raw=True)
                    w.w.value["patch_sha256"] = proposal.core.digest(w.w.patch)
                    w.w.value["result_tree"] = git(w.w.product, "write-tree")
                w.w.write_proof()
                w.w.commit_owner()
                result = w.run()
                self.assertEqual(result["status"], "failed", result)
                self.assertEqual(w.pushes, [])

    def test_existing_unrelated_branch_or_wrong_direct_parent_is_never_overwritten(self):
        for kind in ("tree", "parent"):
            with self.subTest(kind=kind):
                w = self.workspace()
                if kind == "tree":
                    branch = w.branch(tree=w.w.base_tree)
                else:
                    parent = w.branch(tree=w.w.base_tree)
                    branch = w.branch(parent=parent)
                result = w.run()
                self.assertEqual(result["status"], "failed", result)
                self.assertIn("never overwrite", result["reason"])
                self.assertEqual(git(w.w.remote, "rev-parse", proposal.TARGET_REF), branch)
                self.assertEqual(w.pushes, [])

    def test_exact_existing_branch_is_idempotent_without_push(self):
        w = self.w
        branch = w.branch()
        q = w.run()
        result = w.run("propose", q)
        self.assertEqual(result["status"], "unchanged", result)
        self.assertEqual(result["delivered_sha"], branch)
        self.assertFalse(result["push_attempted"])
        self.assertEqual(w.pushes, [])

    def test_exact_qualification_plan_and_single_repository_token_scope_are_required(self):
        w = self.w
        q = w.run()
        bad = copy.deepcopy(q)
        bad["plan"]["target_ref"] = "refs/heads/main"
        result = w.run("propose", bad)
        self.assertEqual(result["status"], "failed")
        self.assertIn("binding mismatch", result["reason"])
        for inventory in ([], [{"full_name": "Hexalith/Hexalith.Projects"}],
                          [{"full_name": "Hexalith/Hexalith.EventStore"}, {"full_name": "Hexalith/Hexalith.CiCd"}]):
            w.inventory = inventory
            result = w.run("propose", q)
            self.assertEqual(result["status"], "failed", result)
        self.assertEqual(w.pushes, [])

    def test_full_writer_registry_and_live_accepted_ref_exclusions_are_reused(self):
        for kind in ("registry", "accepted"):
            with self.subTest(kind=kind):
                w = self.workspace()
                if kind == "registry":
                    (w.w.owner / "setup/Hexalith.EventStore.yml").write_text("{}\n")
                    w.w.commit_owner()
                else:
                    git(w.w.owner_remote, "update-ref", "refs/heads/delivered/Hexalith.EventStore", w.w.source)
                result = w.run()
                self.assertEqual(result["status"], "failed", result)
                self.assertIn("full-delivery", result["reason"])

    def test_refused_or_accepted_ambiguous_push_is_not_retried_and_main_is_unchanged(self):
        for mode in ("refuse", "ambiguous", "race"):
            with self.subTest(mode=mode):
                w = self.workspace()
                q = w.run()
                w.push_mode = mode
                result = w.run("propose", q)
                self.assertEqual(result["status"], "failed", result)
                self.assertTrue(result["push_attempted"])
                self.assertEqual(len(w.pushes), 1)
                self.assertEqual(git(w.w.remote, "rev-parse", "main"), w.w.base)
                self.assertIn("reconciliation", result)
                if mode == "refuse":
                    self.assertIn("[redacted]", result["push_result"]["output"])
                    self.assertLessEqual(len(result["push_result"]["output"]), 2000)
                if mode == "ambiguous":
                    self.assertTrue(result["branch_success"])
                self.assertNotIn(w.w.token, (w.root / proposal.REPORTS["propose"]).read_text())

    def test_interrupted_accepted_push_retains_durable_candidate_attempt_and_target_ref(self):
        w = self.w
        q = w.run()
        w.push_mode = "interrupt"
        with self.assertRaises(KeyboardInterrupt):
            w.run("propose", q)
        result = w.receipt("propose")
        self.assertTrue(result["push_attempted"])
        self.assertEqual(result["target_ref"], proposal.TARGET_REF)
        self.assertEqual(result["candidate_sha"], git(w.w.remote, "rev-parse", proposal.TARGET_REF))
        self.assertEqual(len(w.pushes), 1)
        self.assertEqual(git(w.w.remote, "rev-parse", "main"), w.w.base)

    def test_fixed_draft_pr_is_created_once_without_any_main_write(self):
        w = self.w
        q, branch = w.propose()
        result = w.run("pull-request", q)
        self.assertEqual(result["status"], "pr-created", result)
        self.assertTrue(result["post_attempted"])
        self.assertEqual(w.posts, 1)
        self.assertEqual(result["pr"]["head_sha"], branch["delivered_sha"])
        self.assertEqual(git(w.w.remote, "rev-parse", "main"), w.w.base)

    def test_existing_exact_draft_pr_is_retained_without_post(self):
        w = self.w
        q, _ = w.propose()
        w.prs = [w.pr()]
        result = w.run("pull-request", q)
        self.assertEqual(result["status"], "pr-existing", result)
        self.assertEqual(w.posts, 0)

    def test_unrelated_or_changed_existing_pr_is_blocked_without_creating_another(self):
        for field in ("draft", "body", "head"):
            with self.subTest(field=field):
                w = self.workspace()
                q, _ = w.propose()
                value = w.pr()
                value[field] = False if field == "draft" else "unexpected"
                w.prs = [value]
                result = w.run("pull-request", q)
                self.assertEqual(result["status"], "pr-blocked", result)
                self.assertTrue(result["branch_success"])
                self.assertEqual(w.posts, 0)

    def test_missing_or_forbidden_pr_token_retains_branch_success_and_comparison_url(self):
        w = self.w
        q, branch = w.propose()
        before = (w.root / proposal.REPORTS["propose"]).read_bytes()
        result = w.run("pull-request", q, token="")
        self.assertEqual(result["status"], "pr-blocked", result)
        self.assertIn("PR token unavailable", result["reason"])
        self.assertTrue(result["branch_success"])
        self.assertEqual(result["comparison_url"], proposal.COMPARE)
        self.assertEqual(result["delivered_sha"], branch["delivered_sha"])
        self.assertEqual((w.root / proposal.REPORTS["propose"]).read_bytes(), before)
        w.pr_forbidden = True
        result = w.run("pull-request", q)
        self.assertEqual(result["status"], "pr-blocked", result)
        self.assertIn("HTTP 403", result["reason"])
        self.assertEqual(w.posts, 0)

    def test_forbidden_pr_post_retains_precise_blocker_and_observes_once_without_retry(self):
        w = self.w
        q, _ = w.propose()
        w.post_mode = "forbidden"
        result = w.run("pull-request", q)
        self.assertEqual(result["status"], "pr-blocked", result)
        self.assertIn("HTTP 403", result["reason"])
        self.assertTrue(result["branch_success"])
        self.assertTrue(result["post_attempted"])
        self.assertEqual(w.posts, 1)
        self.assertEqual(w.pr_reads, 2)

    def test_ambiguous_accepted_post_observes_exact_pr_once_and_never_reposts(self):
        w = self.w
        q, _ = w.propose()
        w.post_mode = "ambiguous"
        result = w.run("pull-request", q)
        self.assertEqual(result["status"], "pr-blocked", result)
        self.assertEqual(result["pr_reconciliation"], "observed")
        self.assertIsNotNone(result["pr"])
        self.assertEqual(w.posts, 1)
        self.assertEqual(w.pr_reads, 2)
        result = w.run("pull-request", q)
        self.assertEqual(result["status"], "pr-existing", result)
        self.assertEqual(w.posts, 1)

    def test_unobserved_ambiguous_post_keeps_attempt_checkpoint_across_repeated_invocations(self):
        w = self.w
        q, _ = w.propose()
        w.post_mode = "unobserved"
        for _ in range(3):
            result = w.run("pull-request", q)
            self.assertEqual(result["status"], "pr-blocked", result)
            self.assertTrue(result["post_attempted"])
        self.assertEqual(w.posts, 1)

    def test_interrupted_accepted_pr_post_has_durable_attempt_without_final_return(self):
        w = self.w
        q, _ = w.propose()
        w.post_mode = "interrupt"
        with self.assertRaises(KeyboardInterrupt):
            w.run("pull-request", q)
        result = w.receipt("pull-request")
        self.assertTrue(result["post_attempted"])
        self.assertTrue(result["branch_success"])
        self.assertEqual(result["target_ref"], proposal.TARGET_REF)
        self.assertEqual(w.posts, 1)

    def test_pr_creation_refuses_live_main_or_branch_changes_after_branch_success(self):
        for kind in ("main", "branch"):
            with self.subTest(kind=kind):
                w = self.workspace()
                q, _ = w.propose()
                if kind == "main":
                    w.w.advance()
                else:
                    w.branch(tree=w.w.base_tree)
                result = w.run("pull-request", q)
                self.assertEqual(result["status"], "pr-blocked", result)
                self.assertEqual(w.posts, 0)

    def test_production_api_posts_only_the_fixed_draft_document_to_fixed_origin(self):
        w = self.w
        w.branch()
        observed = []
        class Response(io.BytesIO):
            status = 201
        class Opener:
            def open(self, request, timeout):
                observed.append(request)
                self.timeout = timeout
                return Response(json.dumps(w.pr()).encode())
        api = proposal.API(opener=Opener())
        created = api.create(w.w.token)
        self.assertEqual(created["draft"], True)
        self.assertEqual(len(observed), 1)
        request = observed[0]
        self.assertEqual(request.full_url, "https://api.github.com/repos/Hexalith/Hexalith.EventStore/pulls")
        self.assertEqual(request.method, "POST")
        self.assertEqual(json.loads(request.data), {"title": proposal.TITLE, "body": proposal.BODY, "head": proposal.BRANCH,
                                                   "base": "main", "draft": True, "maintainer_can_modify": False})

    def test_successful_main_round_trip_emits_exact_plan_and_branch_success_with_zero_exit_codes(self):
        w = self.w
        result, output = w.cli("qualify")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout + result.stderr, b"")
        self.assertTrue(output.startswith("plan="))
        plan = json.loads(output.removeprefix("plan="))
        self.assertEqual(plan, w.receipt("qualify")["plan"])
        result, output = w.cli("propose", PREREQUISITE_QUALIFICATION="success", PREREQUISITE_PLAN=json.dumps(plan))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout + result.stderr, b"")
        self.assertEqual(output, "branch-success=true\n")
        self.assertEqual(w.receipt("propose")["status"], "proposed")
        self.assertEqual(git(w.w.remote, "rev-parse", "main"), w.w.base)

    def test_production_api_opener_http403_retains_precise_safe_diagnostic(self):
        calls = []
        class Opener:
            def open(self, request, timeout):
                calls.append(request.full_url)
                raise HTTPError(request.full_url, 403, "Forbidden", {}, io.BytesIO(b"private server detail"))
        api = proposal.API(opener=Opener())
        with self.assertRaises(rt.DeliveryError) as error:
            api.create(self.w.w.token)
        self.assertIn("draft PR POST refused: HTTP 403", str(error.exception))
        self.assertIn("no retry or permission expansion", str(error.exception))
        self.assertNotIn("private server detail", str(error.exception))
        self.assertNotIn(self.w.w.token, str(error.exception))
        self.assertEqual(calls, ["https://api.github.com/repos/Hexalith/Hexalith.EventStore/pulls"])

    def test_atomic_absence_lease_preserves_competing_branch_even_at_candidate_ancestor(self):
        w = self.w
        q = w.run()
        w.push_mode = "ancestor-race"
        result = w.run("propose", q)
        self.assertEqual(result["status"], "failed", result)
        self.assertTrue(result["push_attempted"])
        self.assertEqual(len(w.pushes), 1)
        self.assertEqual(git(w.w.remote, "rev-parse", proposal.TARGET_REF), w.w.base)
        self.assertEqual(git(w.w.remote, "rev-parse", "main"), w.w.base)
        self.assertNotEqual(result["push_result"]["exit_code"], 0)
        self.assertIn("stale info", result["push_result"]["output"])

    def test_clean_actions_rerun_cannot_create_branch_or_promote_its_own_refusal_to_authority(self):
        w = self.w
        q = w.run()
        (w.root / proposal.REPORTS["propose"]).write_text('{"status":"failed","push_attempted":false}\n')
        for _ in range(2):
            result = w.run("propose", q, GITHUB_RUN_ATTEMPT="2")
            self.assertEqual(result["status"], "failed", result)
            self.assertIn("no valid preserved pre-write checkpoint", result["reason"])
            self.assertFalse(result["push_attempted"])
            self.assertIsNone(result["write_checkpoint_origin_attempt"])
        self.assertEqual(w.pushes, [])

    def test_clean_actions_rerun_after_ambiguous_post_cannot_post_again(self):
        w = self.w
        q, _ = w.propose()
        w.post_mode = "unobserved"
        first = w.run("pull-request", q)
        self.assertTrue(first["post_attempted"])
        self.assertEqual(w.posts, 1)
        # A clean runner has only the initializer, rather than the old artifact.
        (w.root / proposal.REPORTS["pull-request"]).write_text('{"status":"pr-blocked","post_attempted":false}\n')
        for _ in range(2):
            result = w.run("pull-request", q, GITHUB_RUN_ATTEMPT="2")
            self.assertEqual(result["status"], "pr-blocked", result)
            self.assertIn("no valid preserved pre-write checkpoint", result["reason"])
            self.assertTrue(result["branch_success"])
            self.assertIsNone(result["write_checkpoint_origin_attempt"])
        self.assertEqual(w.posts, 1)

    def test_actions_rerun_can_observe_exact_existing_branch_and_pr_without_preserved_checkpoint(self):
        w = self.w
        q, _ = w.propose()
        w.prs = [w.pr()]
        (w.root / proposal.REPORTS["propose"]).write_text('{"status":"failed","push_attempted":false}\n')
        (w.root / proposal.REPORTS["pull-request"]).write_text('{"status":"pr-blocked","post_attempted":false}\n')
        result = w.run("propose", q, GITHUB_RUN_ATTEMPT="2")
        self.assertEqual(result["status"], "unchanged", result)
        result = w.run("pull-request", q, GITHUB_RUN_ATTEMPT="2")
        self.assertEqual(result["status"], "pr-existing", result)
        self.assertEqual(len(w.pushes), 1)
        self.assertEqual(w.posts, 0)

    def test_actions_rerun_write_requires_bound_preserved_checkpoint_proving_no_prior_write(self):
        w = self.w
        q = w.run()
        w.inventory = []
        first = w.run("propose", q)
        self.assertEqual(first["status"], "failed")
        self.assertFalse(first["push_attempted"])
        self.assertEqual(first["write_checkpoint_origin_attempt"], 1)
        w.inventory = [{"full_name": "Hexalith/Hexalith.EventStore"}]
        result = w.run("propose", q, GITHUB_RUN_ATTEMPT="2")
        self.assertEqual(result["status"], "proposed", result)
        self.assertEqual(len(w.pushes), 1)


if __name__ == "__main__":
    if sys.argv[1:2] == ["transport-driver"]:
        config = json.loads(Path(sys.argv[2]).read_text())
        selected = load(Path(config["source"]), "_eventstore_proposal_cli_driver")
        class API:
            def pages(self, path, token=None, *, field=None):
                if path != "/installation/repositories" or field != "repositories" or token != config["token"]:
                    raise AssertionError("unexpected CLI authenticated inventory request")
                return [{"full_name": "Hexalith/Hexalith.EventStore"}]
            def get(self, path, token=None):
                if path != "/repos/Hexalith/Hexalith.EventStore" or token != config["token"]:
                    raise AssertionError("unexpected CLI authenticated repository request")
                return {"full_name": "Hexalith/Hexalith.EventStore", "default_branch": "main"}
        class Transport(selected.Transport):
            def __init__(self):
                super().__init__(api=API())
            def remote(self, repository):
                if repository not in config["remotes"]:
                    raise AssertionError("CLI repository broadened")
                return Path(config["remotes"][repository]).as_uri()
            def configure(self, target, repository):
                super().configure(target, repository)
                target.env = fixtures.allow_fixture_files(target.env)
        raise SystemExit(selected.main(sys.argv[3:], transport=Transport()))
    unittest.main(verbosity=2)
