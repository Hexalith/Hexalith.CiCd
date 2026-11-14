#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Authenticated delivery reports, first-result CI ordering and persistent wait budgets."""
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from delivery_support import ROOT, git, load
from nightly_support import Clock, Response, metadata, zip_document

controller = load(ROOT / "tools/nightly_delivery_wait.py", "_delivery_wait_tests")
rt = controller.rt
SOURCE = "a" * 40
BUMP = "b" * 40
PUSHED = "c" * 40
DESCENDANT = "d" * 40
IDENTITY = {"runId": 101, "attempt": 1, "source": SOURCE}
ALPHA = "Hexalith.Alpha"
BETA = "Hexalith.Beta"


def stamp(seconds=0):
    return datetime.fromtimestamp(Clock()() + seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(repository=rt.CICD, workflow="deliver.yml", identifier=201, *, head=BUMP,
        conclusion="success", created=0, status="completed", attempt=1, event="push"):
    return {"id": identifier, "run_attempt": attempt, "path": ".github/workflows/" + workflow,
            "head_branch": "main", "head_sha": head, "event": event, "status": status,
            "conclusion": conclusion, "created_at": stamp(created), "repository": {"full_name": "Hexalith/" + repository},
            "html_url": rt.run_link(repository, identifier)}


def job(run, name="deliver", *, completed=20, conclusion=None):
    # The official endpoint's sample omits run_attempt: the endpoint itself
    # selects it and the controller rechecks current run identity afterward.
    return {"run_id": run["id"], "head_sha": run["head_sha"], "name": name, "status": "completed",
            "started_at": stamp(10), "completed_at": stamp(completed),
            "conclusion": conclusion or run["conclusion"]}


def row(repository=ALPHA, *, pushed=PUSHED):
    return {"repository": repository, "accepted_sha": BUMP, "advancement": "advanced", "application": "pushed",
            "pushed_sha": pushed, "retries": 0, "reasons": [], "processed": True}


def report(delivery, rows=None):
    return {"schema": "hexalith.delivery.v1", "run_id": str(delivery["id"]), "run_attempt": str(delivery["run_attempt"]),
            "event": delivery["event"], "candidate_sha": delivery["head_sha"], "tools_source_sha": BUMP,
            "global": True, "failed": False, "failures": [], "freshness": {"status": "not-scheduled"},
            "modules": rows if rows is not None else [row()]}


class API:
    def __init__(self, clock, budget):
        self.clock, self.budget = clock, budget
        self.repositories = frozenset((rt.CICD, ALPHA, BETA))
        self.deliveries, self.ci = [], {}
        self.jobs, self.reports, self.origins = {}, {}, {}
        self.extra_artifacts = []
        self.current = {}
        self.ancestor_pairs = set()
        self.calls = []
        self.rerun_on_download = False
        self.corrupt_digest = False
        self.fail_ci = set()

    def register(self, value, document=None, *, jobs=None):
        repository = value["repository"]["full_name"].split("/")[1]
        self.current[repository, value["id"]] = deepcopy(value)
        self.jobs[repository, value["id"], value["run_attempt"]] = jobs if jobs is not None else [job(value)]
        if repository == rt.CICD:
            self.deliveries.append(value)
            if document is not None:
                self.reports[value["id"]] = document
        else:
            self.ci.setdefault(repository, []).append(value)

    def check(self, token):
        if token != "inert":
            raise rt.NightlyError("wrong fixture token")
        self.budget.check(token=True)

    def pages(self, path, token, *, field=None):
        self.check(token)
        self.calls.append(path)
        repository = path.split("/")[3]
        if repository not in self.repositories:
            raise rt.NightlyError("fixture API scope violation")
        if "/attempts/" in path:
            pieces = path.split("/")
            return deepcopy(self.jobs[repository, int(pieces[6]), int(pieces[8])])
        if path.endswith("/artifacts"):
            identity = int(path.split("/")[6])
            if identity not in self.reports:
                return []
            value = self.current[repository, identity]
            payload = zip_document("delivery.json", self.reports[identity])
            origin = metadata(identity + 1000, "hexalith-delivery", payload, identity, value["head_sha"])
            origin.update(self.origins)
            if self.corrupt_digest:
                origin["digest"] = "sha256:" + "0" * 64
            return [origin, *deepcopy(self.extra_artifacts)]
        if "/workflows/deliver.yml/runs" in path:
            return self.filtered_runs(path, self.deliveries)
        if "/workflows/ci.yml/runs" in path:
            if repository in self.fail_ci:
                raise rt.NightlyError("CI HTTP 403")
            return self.filtered_runs(path, self.ci.get(repository, []))
        raise AssertionError(path)

    def filtered_runs(self, path, values):
        query = parse_qs(urlsplit(path).query)
        created = query.get("created", [])
        if len(created) != 1 or not created[0].startswith(">="):
            raise rt.NightlyError("unbounded fixture run history")
        since = rt.timestamp(created[0][2:])
        result = [value for value in values if rt.timestamp(value["created_at"]) >= since]
        if len(result) > rt.MAX_PAGES * 100:
            raise rt.NightlyError("GitHub API pagination limit exceeded")
        return deepcopy(result)

    def get(self, path, token=None):
        if token is None:
            self.budget.check()
        else:
            self.check(token)
        self.calls.append(path)
        repository = path.split("/")[3]
        if "/compare/" in path:
            base, head = path.split("/compare/")[1].split("?", 1)[0].split("...")
            return {"base_commit": {"sha": base}, "merge_base_commit": {"sha": base if (base, head) in self.ancestor_pairs else "f" * 40},
                    "status": "ahead" if (base, head) in self.ancestor_pairs else "diverged"}
        return deepcopy(self.current[repository, int(path.split("/")[6])])

    def artifact_member(self, repository, info, member, token):
        self.check(token)
        if member != "delivery.json" or repository != rt.CICD:
            raise AssertionError("wrong exact member")
        identity = info["workflow_run"]["id"]
        payload = zip_document("delivery.json", self.reports[identity])
        if self.corrupt_digest:
            raise rt.NightlyError("artifact ZIP size or digest mismatch")
        if self.rerun_on_download:
            self.current[repository, identity]["run_attempt"] += 1
        # Use the production exact-member parser for the ZIP data boundary.
        class Opener:
            def open(self, request, timeout):
                return Response(payload)
        real = rt.API(self.budget, repositories=(rt.CICD,), opener=Opener())
        return real.artifact_member(repository, info, member, token)


class ObserverTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.state = controller.initial(IDENTITY, BUMP, self.clock())
        self.state["since"] = stamp(-3600)
        self.state["repositories"] = [ALPHA]
        self.budget = rt.Budget(self.clock(), job_seconds=100 * 60, token_epoch=self.clock(),
                                deadline=self.state["deadline"], clock=self.clock)
        self.api = API(self.clock, self.budget)
        self.transport = rt.Transport(self.budget, self.api)
        self.persisted = []

    def poll(self, token="inert"):
        return controller.poll(self.state, self.transport, token, lambda: self.persisted.append(deepcopy(self.state)),
                               clock=self.clock, sleep=self.clock.sleep)

    def complete(self, *, rows=None, ci_conclusion="success"):
        delivery = run()
        self.api.register(delivery, report(delivery, rows))
        ci = run(ALPHA, "ci.yml", 301, head=PUSHED, conclusion=ci_conclusion)
        self.api.register(ci)
        return delivery, ci

    def test_success_authenticates_report_and_links_every_actual_push(self):
        self.complete()
        self.assertEqual(self.poll(), 0)
        self.assertEqual(self.state["delivery"]["report"], "verified")
        self.assertEqual(self.state["modules"][0]["runId"], 301)
        self.assertEqual(controller.finalize(self.state, {}), 0)
        self.assertTrue(self.persisted)

    def test_first_completed_result_wins_by_completion_then_run_id(self):
        self.complete(ci_conclusion="failure")
        earlier_id = run(ALPHA, "ci.yml", 300, head=PUSHED, conclusion="neutral")
        self.api.register(earlier_id, jobs=[job(earlier_id, completed=20)])
        later = run(ALPHA, "ci.yml", 299, head=PUSHED)
        self.api.register(later, jobs=[job(later, completed=30)])
        self.api.ci[ALPHA].reverse()
        self.poll()
        selected = self.state["modules"][0]
        self.assertEqual(selected["runId"], 300)
        self.assertEqual(selected["conclusion"], "neutral")
        self.assertEqual(controller.finalize(self.state, {}), 1)
        self.assertIn("first qualifying", self.state["errors"][-1])

    def test_green_rerun_cannot_replace_selected_red_result(self):
        _, ci = self.complete(ci_conclusion="failure")
        self.poll()
        self.api.current[ALPHA, ci["id"]].update(conclusion="success", run_attempt=2)
        self.poll()
        self.assertEqual(self.state["modules"][0]["conclusion"], "failure")
        self.assertEqual(controller.finalize(self.state, {}), 1)

    def test_descendant_ci_qualifies_while_pr_cancelled_and_unrelated_runs_do_not(self):
        delivery, _ = self.complete()
        self.api.ci[ALPHA] = []
        for identifier, head, event, conclusion in ((299, PUSHED, "pull_request", "success"),
                (298, PUSHED, "push", "cancelled"), (297, SOURCE, "push", "failure"),
                (303, DESCENDANT, "push", "success")):
            value = run(ALPHA, "ci.yml", identifier, head=head, event=event, conclusion=conclusion)
            self.api.register(value)
        self.api.ancestor_pairs.add((PUSHED, DESCENDANT))
        self.poll()
        self.assertEqual(self.state["modules"][0]["runId"], 303)
        self.assertEqual(controller.finalize(self.state, {}), 0)

    def test_first_started_delivery_wins_even_if_later_delivery_green(self):
        first = run(identifier=200, conclusion="failure", created=-10)
        document = report(first)
        document["global"] = False
        document["failed"] = True
        document["failures"] = ["global validation failed"]
        self.api.register(first, document)
        self.complete()
        self.poll()
        self.assertEqual(self.state["delivery"]["runId"], 200)
        self.assertEqual(self.state["modules"][0]["runId"], 301)
        self.assertEqual(controller.finalize(self.state, {}), 1)

    def test_skipped_deliver_job_and_cancelled_run_do_not_qualify(self):
        skipped = run(identifier=199, created=-30)
        self.api.register(skipped, report(skipped), jobs=[job(skipped, conclusion="skipped")])
        cancelled = run(identifier=198, created=-40, conclusion="cancelled")
        self.api.register(cancelled, report(cancelled))
        self.complete()
        self.poll()
        self.assertEqual(self.state["delivery"]["runId"], 201)

    def test_report_identity_artifact_origin_digest_and_duplicates_fail_closed(self):
        for kind in ("attempt", "run", "candidate", "origin", "duplicate", "digest"):
            with self.subTest(kind=kind):
                self.setUp()
                self.complete()
                document = self.api.reports[201]
                if kind == "attempt":
                    document["run_attempt"] = "2"
                elif kind == "run":
                    document["run_id"] = "999"
                elif kind == "candidate":
                    document["candidate_sha"] = SOURCE
                elif kind == "origin":
                    self.api.origins["workflow_run"] = {"id": 999, "head_sha": BUMP, "head_branch": "main"}
                elif kind == "duplicate":
                    self.api.extra_artifacts = [{"name": "hexalith-delivery"}]
                else:
                    self.api.corrupt_digest = True
                self.poll()
                self.assertEqual(self.state["delivery"]["report"], "failed")
                self.assertEqual(self.state["modules"], [])
                self.assertEqual(controller.finalize(self.state, {}), 1)

    def test_attempt_transition_during_download_rejects_old_report(self):
        self.complete()
        self.api.rerun_on_download = True
        self.poll()
        self.assertEqual(self.state["delivery"]["report"], "failed")
        self.assertIn("attempt changed", self.state["errors"][0])

    def test_delivery_cancelled_after_discovery_leaves_eligible_set(self):
        delivery = run(status="in_progress", conclusion=None)
        self.api.register(delivery, jobs=[{**job(delivery), "status": "in_progress"}])
        controller.select_delivery(self.state, self.api, "inert")
        self.api.current[rt.CICD, delivery["id"]]["conclusion"] = "cancelled"
        controller.observe_delivery(self.state, self.api, "inert")
        self.assertIsNone(self.state["delivery"])
        self.assertEqual(self.state["errors"], [])

    def test_untrusted_report_cannot_authorize_another_repository_or_builds(self):
        for repository in ("Hexalith.Foreign", rt.BUILDS):
            with self.subTest(repository=repository):
                self.setUp()
                self.complete(rows=[row(repository)])
                self.poll()
                self.assertEqual(self.state["delivery"]["report"], "failed")
                self.assertFalse(any(repository + "/actions/workflows/ci.yml" in path for path in self.api.calls))

    def test_failed_sibling_does_not_hide_another_modules_observation(self):
        self.state["repositories"] = [ALPHA, BETA]
        self.complete(rows=[row(ALPHA), row(BETA, pushed=DESCENDANT)])
        beta = run(BETA, "ci.yml", 302, head=DESCENDANT)
        self.api.register(beta)
        self.api.fail_ci.add(ALPHA)
        self.poll()
        alpha, beta = self.state["modules"]
        self.assertIn("403", alpha["error"])
        self.assertEqual(beta["conclusion"], "success")
        self.assertEqual(controller.finalize(self.state, {}), 1)

    def test_repair_push_is_observed_after_skipped_advancement(self):
        repair = row()
        repair["advancement"] = "skipped"
        self.complete(rows=[repair])
        self.poll()
        self.assertEqual(self.state["modules"][0]["pushed"], PUSHED)
        self.assertEqual(controller.finalize(self.state, {}), 0)

    def test_three_slices_share_one_ninety_minute_deadline(self):
        started = self.clock()
        for _ in range(3):
            self.budget.token_epoch = self.clock()
            self.budget.deadline = self.state["deadline"]
            self.poll()
        self.assertEqual(self.clock() - started, controller.WAIT_SECONDS)
        self.assertTrue(all(value == 60 for value in self.clock.sleeps))
        self.assertEqual(controller.finalize(self.state, {}), 1)
        self.assertIn("delivery missing", self.state["errors"][0])

    def test_failed_mint_never_reuses_an_earlier_token_and_can_still_collect_results(self):
        self.complete()
        before = list(self.api.calls)
        self.assertEqual(self.poll(token=""), 1)
        self.assertEqual(self.api.calls, before)
        self.budget.token_epoch = self.clock()
        self.poll()
        self.assertEqual(self.state["modules"][0]["conclusion"], "success")
        self.assertEqual(controller.finalize(self.state, {}), 1)

    def test_slice_age_includes_action_mint_time_and_token_reserve(self):
        self.budget.token_epoch = self.clock() - controller.SLICE_SECONDS + 60
        self.poll()
        self.assertEqual(self.clock.sleeps, [60])
        self.budget.token_epoch = self.clock() - 50 * 60 + 30
        with self.assertRaises(rt.NightlyError):
            self.poll()

    def test_state_rejects_changed_deadline_identity_and_unauthorized_rows(self):
        controller.validate_state(self.state, IDENTITY)
        for mutation in (lambda value: value.update(deadline=value["deadline"] + 1),
                         lambda value: value.update(identity={**IDENTITY, "attempt": 2}),
                         lambda value: value.update(repositories=[rt.BUILDS]),
                         lambda value: value.update(since=None),
                         lambda value: value.update(since=stamp(1))):
            value = deepcopy(self.state)
            mutation(value)
            with self.assertRaises(rt.NightlyError):
                controller.validate_state(value, IDENTITY)

    def test_creation_filter_excludes_thousands_of_historic_runs_without_hiding_earlier_red(self):
        self.api.deliveries.extend(run(identifier=10000 + i, head=SOURCE, created=-7200) for i in range(2001))
        self.api.ci[ALPHA] = [run(ALPHA, "ci.yml", 20000 + i, head=SOURCE, created=-7200) for i in range(2001)]
        delivery = run(created=-600)
        self.api.register(delivery, report(delivery))
        early = run(ALPHA, "ci.yml", 300, head=PUSHED, conclusion="failure", created=-300)
        self.api.register(early, jobs=[job(early, completed=-200)])
        later = run(ALPHA, "ci.yml", 301, head=PUSHED, created=-100)
        self.api.register(later, jobs=[job(later, completed=-50)])
        self.poll()
        self.assertEqual(self.state["delivery"]["runId"], 201)
        self.assertEqual(self.state["modules"][0]["runId"], 300)
        self.assertEqual(controller.finalize(self.state, {}), 1)
        histories = [path for path in self.api.calls if "/workflows/" in path]
        self.assertEqual(len(histories), 2)
        self.assertTrue(all("created=>=" + self.state["since"] in path for path in histories))

    def test_original_nightly_creation_is_independently_bound_before_filtering(self):
        nightly = run(workflow="nightly.yml", identifier=101, head=SOURCE, created=-3600, event="schedule")
        self.api.register(nightly)
        controller.bind_creation(self.state, self.api, {"GITHUB_EVENT_NAME": "schedule"})
        self.assertEqual(self.state["since"], nightly["created_at"])
        for key, wrong in (("id", 102), ("run_attempt", 2), ("head_sha", BUMP), ("path", ".github/workflows/deliver.yml"),
                ("event", "workflow_dispatch"), ("created_at", None), ("created_at", stamp(1)),
                ("created_at", stamp(-3600).replace("Z", "+00:00"))):
            with self.subTest(key=key, wrong=wrong):
                self.api.current[rt.CICD, 101] = {**nightly, key: wrong}
                with self.assertRaises(rt.NightlyError):
                    controller.bind_creation(self.state, self.api, {"GITHUB_EVENT_NAME": "schedule"})


class AuthorizationTests(unittest.TestCase):
    def test_removed_setup_keeps_independently_verified_delivered_ref_in_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            git(source, "init", "--quiet", "--initial-branch=main")
            (source / "setup").mkdir()
            (source / "setup" / (ALPHA + ".yml")).write_text("{}\n")
            git(source, "add", ".")
            git(source, "commit", "--quiet", "-m", "Adopt fixture")
            accepted = git(source, "rev-parse", "HEAD")
            git(source, "rm", "setup/" + ALPHA + ".yml")
            git(source, "commit", "--quiet", "-m", "Remove fixture setup")
            bump = git(source, "rev-parse", "HEAD")
            remote = root / "remote.git"
            git(root, "clone", "--quiet", "--bare", source, remote)
            git(remote, "update-ref", "refs/heads/delivered/" + ALPHA, accepted)
            clock = Clock()
            budget = rt.Budget(clock(), job_seconds=100 * 60, clock=clock)
            class Transport(rt.Transport):
                def remote(self, repository):
                    return remote.as_uri()
                def cicd(self, store):
                    index = int(store.env["GIT_CONFIG_COUNT"])
                    store.env.update(GIT_CONFIG_COUNT=str(index + 1))
                    store.env[f"GIT_CONFIG_KEY_{index}"] = "protocol.file.allow"
                    store.env[f"GIT_CONFIG_VALUE_{index}"] = "always"
                    super().cicd(store)
            state = controller.initial(IDENTITY, bump, clock())
            controller.authorize(state, Transport(budget), root)
            self.assertEqual(state["repositories"], [ALPHA])
            git(remote, "update-ref", "refs/heads/delivered/" + rt.BUILDS, accepted)
            with self.assertRaises(rt.NightlyError):
                controller.authorize(state, Transport(budget), root)

    def test_isolated_entrypoint_retains_state_between_action_mint_slices(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            git(source, "init", "--quiet", "--initial-branch=main")
            (source / "setup").mkdir()
            (source / "setup" / (ALPHA + ".yml")).write_text("{}\n")
            git(source, "add", ".")
            git(source, "commit", "--quiet", "-m", "Fixture bump")
            bump = git(source, "rev-parse", "HEAD")
            remote = root / "remote.git"
            git(root, "clone", "--quiet", "--bare", source, remote)
            config = root / "fixture.json"
            config.write_text(json.dumps({"remote": str(remote), "bump": bump}))
            directory = root / "observer"
            outputs = root / "outputs"
            environment = os.environ | {"GITHUB_REPOSITORY": "Hexalith/Hexalith.CiCd", "GITHUB_REF": "refs/heads/main",
                "GITHUB_EVENT_NAME": "schedule", "GITHUB_SHA": bump, "GITHUB_RUN_ID": "101", "GITHUB_RUN_ATTEMPT": "1",
                "BUMP_SHA": bump, "BUMP_PUSH_RESULT": "pushed", "NIGHTLY_DIRECTORY": str(directory),
                "GITHUB_OUTPUT": str(outputs), "POLL_TOKEN": "inert", "NIGHTLY_MINT_EPOCH": str(Clock()())}
            for operation in ("initialize", "permit", "poll", "finalize"):
                process = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "driver", str(config), operation],
                                         capture_output=True, env=environment)
                self.assertEqual(process.returncode, 0, process.stderr.decode())
                self.assertEqual(process.stdout, b"")
            document = json.loads((directory / "delivery-wait/report.json").read_bytes())
            self.assertEqual(document["result"], "pass")
            self.assertEqual(document["since"], stamp(-3600))
            self.assertEqual(document["modules"][0]["runId"], 301)
            self.assertNotIn("inert", (directory / "delivery-wait/report.json").read_text())
            self.assertIn("repositories=Hexalith.CiCd,Hexalith.Alpha", outputs.read_text())
            # An unreadable/mismatched own run cannot supply a guessed time
            # bound or authorize a subsequent token mint.
            config.write_text(json.dumps({"remote": str(remote), "bump": bump, "bad_nightly": True}))
            process = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "driver", str(config), "initialize"],
                                     capture_output=True, env=environment)
            self.assertEqual(process.returncode, 1, process.stderr.decode())
            failed = json.loads((directory / "delivery-wait/report.json").read_bytes())
            self.assertIsNone(failed["since"])
            self.assertEqual(failed["repositories"], [])
            process = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "driver", str(config), "permit"],
                                     capture_output=True, env=environment)
            self.assertEqual(process.returncode, 0, process.stderr.decode())
            self.assertIn("active=false", outputs.read_text())


def driver():
    config = json.loads(Path(sys.argv[2]).read_bytes())
    clock = Clock()
    budget = rt.Budget(clock(), job_seconds=100 * 60, token_epoch=clock(), clock=clock)
    api = API(clock, budget)
    api.register(run(workflow="nightly.yml", identifier=101,
                     head=SOURCE if config.get("bad_nightly") else config["bump"], created=-3600, event="schedule"))
    delivery = run(head=config["bump"])
    api.register(delivery, report(delivery))
    api.register(run(ALPHA, "ci.yml", 301, head=PUSHED))
    class Transport(rt.Transport):
        def remote(self, repository):
            return Path(config["remote"]).as_uri()
        def cicd(self, store):
            index = int(store.env["GIT_CONFIG_COUNT"])
            store.env.update(GIT_CONFIG_COUNT=str(index + 1))
            store.env[f"GIT_CONFIG_KEY_{index}"] = "protocol.file.allow"
            store.env[f"GIT_CONFIG_VALUE_{index}"] = "always"
            super().cicd(store)
    raise SystemExit(controller.main(sys.argv[3:], transport=Transport(budget, api), clock=clock, sleep=clock.sleep))


if __name__ == "__main__":
    if sys.argv[1:2] == ["driver"]:
        driver()
    else:
        unittest.main()
