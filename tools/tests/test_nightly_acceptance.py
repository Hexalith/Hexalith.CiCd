#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Fixture runs for the read-only per-module nightly acceptance tool."""
import ast
import base64
import copy
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from delivery_support import ROOT, load

tool = load(ROOT / "tools/nightly_acceptance.py", "_nightly_acceptance_tests")

RUN = 44264031228
SOURCE = "c" * 40
CANDIDATE = "b" * 40
CREATED = "2026-11-18T08:05:35Z"
NOW = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc).timestamp()
MODULES = ("Hexalith.Alpha", "Hexalith.Beta", "Hexalith.Gamma")
API = "repos/Hexalith/Hexalith.CiCd/"
JOBS = ("dispatch", "wait", "publish-ready", "scan", "bump", "bump-push", "delivery-wait", "keepalive")


def zip_bytes(members):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for member, document in members.items():
            entry = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100600 << 16
            archive.writestr(entry, document if isinstance(document, bytes) else json.dumps(document).encode())
    return stream.getvalue()


def replaced(data):
    """A tamper that serves ``data`` with matching API size and digest."""
    def change(metadata, payload):
        metadata.update(size_in_bytes=len(data), digest="sha256:" + hashlib.sha256(data).hexdigest())
        return data
    return change


def corrupt_deflate(members):
    """A ZIP whose central directory is intact but whose first deflate block type is invalid."""
    payload = bytearray(zip_bytes(members))
    payload[30 + len(next(iter(members)))] = 0xFF
    return bytes(payload)


def head(module):
    return hashlib.sha1(module.encode()).hexdigest()


class FakeGitHub:
    """Exact-endpoint GET doubles; an unknown endpoint is GitHub's 404, a failing one a 502."""

    def __init__(self, routes, blobs):
        self.routes, self.blobs, self.calls, self.failing = routes, blobs, [], set()

    def answer(self, endpoint, values):
        self.calls.append(endpoint)
        if endpoint in self.failing:
            raise tool.TransportError(endpoint + ": gh: Bad Gateway (HTTP 502)")
        if endpoint not in values:
            raise tool.NotFound(endpoint + ": gh: Not Found (HTTP 404)")
        return values[endpoint]

    def json(self, endpoint):
        return copy.deepcopy(self.answer(endpoint, self.routes))

    def blob(self, endpoint):
        return self.answer(endpoint, self.blobs)


class World:
    """One coherent nightly run: CiCd run, jobs, artifacts, release runs and rendered configs."""

    def __init__(self, modules=MODULES, *, event="workflow_dispatch"):
        self.modules = list(modules)
        self.run = {"id": RUN, "event": event, "path": ".github/workflows/nightly.yml", "head_branch": "main",
                    "head_sha": SOURCE, "status": "completed", "conclusion": "failure", "run_attempt": 1,
                    "created_at": CREATED, "repository": {"full_name": "Hexalith/Hexalith.CiCd"}}
        self.jobs = {name: {"name": name, "status": "completed", "conclusion": "success"} for name in JOBS}
        self.jobs["bump-push"]["conclusion"] = self.jobs["delivery-wait"]["conclusion"] = "skipped"
        self.rows = {module: self.row(module, index) for index, module in enumerate(self.modules, 1)}
        self.builds = self.row("Hexalith.Builds", 99, workflow=".github/workflows/builds-release.yml")
        self.builds["deliveredSha"] = ""
        self.languages = {module: ["csharp"] for module in self.modules}
        self.release_jobs = {module: [
            {"name": "release / Resolve release identity", "status": "completed", "conclusion": "success"},
            {"name": "release / Release CodeQL (csharp)", "status": "completed", "conclusion": "success"},
            {"name": "release / Report release outcome", "status": "completed", "conclusion": "success"},
            {"name": "publish", "status": "completed", "conclusion": "success"}] for module in self.modules}
        self.remote_overrides = {}
        self.scan = {"schema": "hexalith.duplicate-scan.v1", "result": "pass", "controllerRevision": SOURCE,
                     "modules": [{"module": module, "revision": head(module), "result": "pass", "files": [],
                                  "errors": []} for module in self.modules],
                     "findings": [], "errors": [], "detector": {}, "policy": {}}
        self.scan_summary = b"# scan\n"
        self.bump = {"schema": "hexalith.nightly-bump-report.v1", "identity": self.bump_identity(),
                     "result": "no-change", "base": SOURCE, "candidate": "", "tag": "v6.2.0",
                     "reason": "no newer acceptable unskipped Builds tag"}
        self.push = None
        self.delivery = None
        self.keepalive = {"schema": "hexalith.nightly-keepalive.v1", "result": "pass", "enabled": {}, "base": SOURCE,
                          "candidate": None, "ageSeconds": 1, "commit": "not-needed", "errors": []}
        self.nightly_result = "fail"
        self.nightly_overrides = {}
        self.omit, self.tamper, self.duplicate = set(), {}, set()
        self.scan_runs = []
        self.scan_producers = []
        self.extra_routes = {}

    def bump_identity(self):
        return {"runId": RUN, "attempt": 1, "source": SOURCE, "night": "2026-11-18"}

    def row(self, module, index, *, workflow=".github/workflows/release.yml"):
        run_id = 7000 + index
        return {"repository": module, "workflow": workflow, "deliveredSha": SOURCE, "dispatchHead": head(module),
                "runId": run_id, "runAttempt": 1,
                "link": f"https://github.com/Hexalith/{module}/actions/runs/{run_id}",
                "eligibility": "eligible", "dispatch": "dispatched", "status": "completed", "conclusion": "success",
                "outcome": {"schema": "hexalith.release-outcome.v1", "sha": head(module), "outcome": "published",
                            "version": "1.2.3"},
                "outcomeError": "", "publication": "pending", "verdict": "pass", "reason": "release workflow succeeded"}

    def pushed(self, conclusions=None):
        """A pushed bump candidate observed by delivery-wait with per-module first CI conclusions."""
        conclusions = conclusions or {module: "success" for module in self.modules}
        self.jobs["bump-push"]["conclusion"] = self.jobs["delivery-wait"]["conclusion"] = "success"
        self.bump.update(result="candidate", candidate=CANDIDATE, tag="v6.3.0", reason="shared global checks passed")
        self.push = {"schema": "hexalith.nightly-bump-push.v1", "identity": self.bump_identity(), "result": "pushed",
                     "base": SOURCE, "candidate": CANDIDATE, "transport": "github-token", "deliveryDispatched": True,
                     "failed": False, "reason": "exact validated candidate confirmed on main", "remoteMain": CANDIDATE}
        self.delivery = {"schema": "hexalith.nightly-delivery-wait.v1",
                         "identity": {"runId": RUN, "attempt": 1, "source": SOURCE}, "bump": CANDIDATE,
                         "started": 1.0, "deadline": 5401.0, "since": CREATED, "repositories": self.modules,
                         "delivery": None, "errors": [], "result": "pass",
                         "modules": [{"repository": module, "pushed": "d" * 40, "runId": 9000 + index if conclusion else 0,
                                      "attempt": 1 if conclusion else 0, "head": "d" * 40 if conclusion else "",
                                      "link": "", "conclusion": conclusion, "completedAt": "", "error": ""}
                                     for index, (module, conclusion) in enumerate(conclusions.items(), 1)]}

    def nightly(self):
        return {"schema": "hexalith.nightly.v1", "phase": "nightly",
                "identity": {"runId": RUN, "attempt": self.run["run_attempt"], "source": SOURCE},
                "registry": sorted(self.rows), "builds": {"tag": "v6.2.0", "sha": "e" * 40},
                "targets": [self.rows[module] for module in sorted(self.rows)] + [self.builds],
                "errors": [], "wait": {"started": 1.0, "deadline": 18001.0}, "result": self.nightly_result,
                **self.nightly_overrides}

    def artifact_documents(self):
        documents = {"nightly": {"nightly.json": self.nightly()},
                     "scan": {"report.json": self.scan, "summary.md": self.scan_summary},
                     "bump-report": {"bump.json": self.bump}, "keepalive": {"keepalive.json": self.keepalive}}
        if self.push is not None:
            documents["bump-push"] = {"bump-push.json": self.push}
        if self.delivery is not None:
            documents["delivery-wait"] = {"report.json": self.delivery}
        return {kind: value for kind, value in documents.items() if kind not in self.omit}

    def add_artifacts(self, routes, blobs, run, documents, first_id):
        listed = []
        for offset, (kind, members) in enumerate(documents.items()):
            payload = zip_bytes(members)
            metadata = {"id": first_id + offset, "name": tool.ARTIFACTS[kind][1].format(attempt=run["run_attempt"]),
                        "size_in_bytes": len(payload), "digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
                        "expired": False, "expires_at": "2027-02-16T08:05:37Z",
                        "workflow_run": {"id": run["id"], "head_sha": run["head_sha"], "head_branch": "main"}}
            if kind in self.tamper and run["id"] == RUN:
                payload = self.tamper[kind](metadata, payload) or payload
            listed.append(metadata)
            if kind in self.duplicate and run["id"] == RUN:
                listed.append(dict(metadata, id=metadata["id"] + 1000))
            blobs[API + f"actions/artifacts/{metadata['id']}/zip"] = payload
        routes[API + f"actions/runs/{run['id']}/artifacts?per_page=100"] = {"total_count": len(listed),
                                                                            "artifacts": listed}

    def github(self):
        routes, blobs = {}, {}
        routes[API + f"actions/runs/{RUN}"] = self.run
        jobs = list(self.jobs.values())
        routes[API + f"actions/runs/{RUN}/attempts/{self.run['run_attempt']}/jobs?per_page=100"] = {
            "total_count": len(jobs), "jobs": jobs}
        self.add_artifacts(routes, blobs, self.run, self.artifact_documents(), 14410984147)
        for module, row in self.rows.items():
            remote = {"id": row["runId"], "path": row["workflow"], "event": "workflow_dispatch", "head_branch": "main",
                      "head_sha": row["dispatchHead"], "run_attempt": row["runAttempt"], "status": row["status"],
                      "conclusion": row["conclusion"], "repository": {"full_name": "Hexalith/" + module}}
            remote.update(self.remote_overrides.get(module, {}))
            routes[f"repos/Hexalith/{module}/actions/runs/{row['runId']}"] = remote
            jobs = self.release_jobs[module]
            routes[f"repos/Hexalith/{module}/actions/runs/{row['runId']}/attempts/{row['runAttempt']}/jobs"
                   "?per_page=100"] = {"total_count": len(jobs), "jobs": jobs}
            if module in self.languages:
                data = json.dumps({"schema": "hexalith.ci.v1", "codeql": self.languages[module]}, indent=2).encode()
                encoded = base64.b64encode(data).decode()
                path = f"rendered/{module}/.github/hexalith-ci.json"
                routes[API + f"contents/{path}?ref={row['deliveredSha']}"] = {
                    "type": "file", "path": path, "encoding": "base64", "size": len(data),
                    "sha": hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest(),
                    "content": "\n".join(encoded[i:i + 60] for i in range(0, len(encoded), 60)) + "\n"}
        if self.scan_runs or self.scan_producers:
            producers = list(self.scan_producers)
            for index, (created, report, *event) in enumerate(self.scan_runs, 1):
                run = {"id": 60000 + index, "path": ".github/workflows/scan.yml", "head_branch": "main",
                       "head_sha": SOURCE, "status": "completed", "conclusion": "success", "run_attempt": 1,
                       "event": (event or ["schedule"])[0], "created_at": created,
                       "repository": {"full_name": "Hexalith/Hexalith.CiCd"}}
                documents = {} if report is None else {"scan": {"report.json": report, "summary.md": b"# scan\n"}}
                producers.append((run, documents))
            for run, documents in producers:
                self.add_artifacts(routes, blobs, run, documents, 15000000000 + run["id"] - 60000)
            # GitHub lists newest first; the tool judges oldest first.
            listed = sorted((run for run, _ in producers), key=lambda run: run["created_at"], reverse=True)
            routes[API + "actions/workflows/scan.yml/runs?branch=main&status=completed"
                   "&created=%3E%3D2026-11-18T08%3A05%3A35Z&per_page=100"] = {
                "total_count": len(listed), "workflow_runs": listed}
        routes.update(self.extra_routes)
        return FakeGitHub(routes, blobs)

    def scan_report(self, **rows):
        """A scan.yml report whose rows carry the given (revision, result, errors) per module."""
        report = copy.deepcopy(self.scan)
        for row in report["modules"]:
            if row["module"] in rows:
                row["revision"], row["result"], row["errors"] = rows[row["module"]]
        return report


class Harness(unittest.TestCase):
    def judge(self, world, *modules, checkpoint=None, receipt=None):
        github = world.github() if isinstance(world, World) else world
        argv = ["--run", str(RUN)]
        for module in modules or MODULES:
            argv += ["--module", module]
        if checkpoint:
            argv += ["--checkpoint", checkpoint]
        if receipt:
            argv += ["--receipt", str(receipt)]
        stdout, stderr = io.StringIO(), io.StringIO()
        code = tool.main(argv, github=github, clock=lambda: NOW, stdout=stdout, stderr=stderr)
        self.stderr = stderr.getvalue()
        self.github_calls = github.calls
        if code == 2:
            self.assertEqual(stdout.getvalue(), "")
            return code, None
        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 0 if report["verdict"] == "pass" else 1)
        return code, report

    def verdicts(self, report):
        return {name: item["verdict"] for name, item in report["modules"].items()}

    def reasons(self, report, module):
        return " | ".join(report["modules"][module]["reasons"])


class RunAuthenticationTests(Harness):
    def test_schedule_and_dispatch_runs_are_accepted(self):
        for event in ("schedule", "workflow_dispatch"):
            with self.subTest(event=event):
                code, report = self.judge(World(event=event))
                self.assertEqual(code, 0)
                self.assertEqual(report["run"]["event"], event)
                self.assertEqual(self.verdicts(report), dict.fromkeys(MODULES, "pass"))

    def test_rejected_runs_give_no_verdict_and_no_receipt(self):
        def run(**values):
            return lambda world: world.run.update(values)
        def job(**values):
            return lambda world: world.jobs["dispatch"].update(values)
        def artifact(change):
            return lambda world: world.tamper.update(nightly=change)
        cases = {
            "qualify-bump": (job(conclusion="skipped"), "qualify-bump"),
            "dispatch job missing": (lambda world: world.jobs.pop("dispatch"), "dispatch job"),
            "non-main": (run(head_branch="feature"), "not main"),
            "other workflow": (run(path=".github/workflows/deliver.yml"), "not .github/workflows/nightly.yml"),
            "other repository": (run(repository={"full_name": "Hexalith/Hexalith.Builds"}), "not a Hexalith.CiCd"),
            "in progress": (run(status="in_progress", conclusion=None), "not completed"),
            "push event": (run(event="push"), "neither schedule"),
            "digest mismatch": (artifact(lambda metadata, payload: metadata.update(digest="sha256:" + "0" * 64)),
                                "do not match its API digest"),
            "byte mismatch": (artifact(lambda metadata, payload: payload[:-1] + bytes([payload[-1] ^ 1])),
                              "do not match its API digest"),
            "size mismatch": (artifact(lambda metadata, payload: payload + b"\0"), "API size"),
            "expired": (artifact(lambda metadata, payload: metadata.update(expired=True)), "expired"),
            "expiry passed": (artifact(lambda metadata, payload: metadata.update(expires_at="2026-11-18T11:00:00Z")),
                              "expired"),
            "other run's artifact": (artifact(lambda metadata, payload: metadata["workflow_run"].update(id=RUN + 1)),
                                     "not bound"),
            "nightly missing": (lambda world: world.omit.add("nightly"), "no nightly.json"),
            "nightly identity": (lambda world: world.nightly_overrides.update(
                identity={"runId": RUN, "attempt": 1, "source": "f" * 40}), "identity does not match"),
            "nightly qualification phase": (lambda world: world.nightly_overrides.update(phase="wait"),
                                            "not a final"),
            "jobs over one page": (lambda world: world.jobs.update(
                {f"extra-{index}": {"name": f"extra-{index}", "status": "completed", "conclusion": "success"}
                 for index in range(100)}), "over one page"),
            "unexpected member": (artifact(replaced(zip_bytes({"nightly.json": b"{}", "extra.txt": b"x"}))),
                                  "members ['extra.txt', 'nightly.json'] are not ['nightly.json']"),
            "missing member": (artifact(replaced(zip_bytes({"state.json": b"{}"}))),
                               "members ['state.json'] are not ['nightly.json']"),
            "not a ZIP": (artifact(replaced(b"digest-matching bytes that are not a ZIP")), "is not a readable ZIP"),
            "corrupt deflate": (artifact(replaced(corrupt_deflate({"nightly.json": b"{}" * 64}))),
                                "is not a readable ZIP"),
            "listed twice": (lambda world: world.duplicate.add("nightly"), "listed more than once"),
            "registry order": (lambda world: world.nightly_overrides.update(registry=list(reversed(MODULES))),
                               "registry is malformed"),
            "targets order": (lambda world: world.nightly_overrides.update(
                targets=list(reversed(World.nightly(world)["targets"]))), "targets do not follow"),
            "publish-ready seed": (lambda world: world.nightly_overrides.update(
                registry=[], targets=[dict(world.builds, eligibility="pending", dispatch="pending", runId=0,
                                           runAttempt=0, link="", dispatchHead="", status="", conclusion="",
                                           outcome=None, verdict="fail",
                                           reason="checkout or initialization did not complete")],
                builds={"tag": "", "sha": ""}, wait=None, errors=["checkout or initialization did not complete"]),
                "seed: checkout or initialization did not complete"),
        }
        for name, (change, message) in cases.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as directory:
                world = World()
                change(world)
                receipt = Path(directory) / "receipt.json"
                code, report = self.judge(world, receipt=receipt)
                self.assertEqual(code, 2)
                self.assertIn("rejected", self.stderr)
                self.assertIn(message, self.stderr)
                self.assertFalse(receipt.exists())

    def test_a_scan_artifact_digest_mismatch_also_rejects_the_run(self):
        world = World()
        world.tamper["scan"] = lambda metadata, payload: metadata.update(digest="sha256:" + "1" * 64)
        code, _ = self.judge(world)
        self.assertEqual(code, 2)
        self.assertIn("hexalith-nightly-scan-1 downloaded bytes do not match", self.stderr)

    def test_later_attempt_reads_its_own_artifacts(self):
        world = World()
        world.run["run_attempt"] = 2
        code, report = self.judge(world)
        self.assertEqual(code, 0)
        self.assertEqual([item["name"] for item in report["artifacts"]],
                         ["hexalith-nightly-nightly-2", "hexalith-nightly-scan-2"])

    def test_usage_errors(self):
        for argv, message in ((["--run", str(RUN), "--module", "Hexalith.Builds"], "Hexalith.Builds"),
                              (["--run", str(RUN), "--module", "hexalith.builds"], "Hexalith.Builds"),
                              (["--run", "0", "--module", MODULES[0]], "positive run id"),
                              (["--run", "12x", "--module", MODULES[0]], "positive run id"),
                              (["--run", str(RUN), "--module", "../Hexalith.Alpha"], "module repository")):
            with self.subTest(argv=argv):
                stdout, stderr = io.StringIO(), io.StringIO()
                github = World().github()
                self.assertEqual(tool.main(argv, github=github, stdout=stdout, stderr=stderr), 2)
                self.assertIn(message, stderr.getvalue())
                self.assertEqual((stdout.getvalue(), github.calls), ("", []))
        with mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(tool.main(["--run", str(RUN)], github=World().github()), 2)

    def test_transport_error_is_exit_2_without_verdict(self):
        github = World().github()
        github.failing.add(f"repos/Hexalith/{MODULES[1]}/actions/runs/7002")
        code, _ = self.judge(github, *MODULES)
        self.assertEqual(code, 2)
        self.assertIn("transport", self.stderr)
        self.assertIn("HTTP 502", self.stderr)
        github = World().github()
        github.routes.pop(API + f"actions/runs/{RUN}")
        code, _ = self.judge(github, *MODULES)
        self.assertEqual(code, 2)
        self.assertIn("HTTP 404", self.stderr)

    def test_non_json_nightly_member_rejects(self):
        world = World()
        world.nightly = lambda: b"not json"
        code, _ = self.judge(world)
        self.assertEqual(code, 2)
        self.assertIn("nightly.json is not JSON", self.stderr)


class ModuleVerdictTests(Harness):
    def test_published_and_nothing_pass(self):
        world = World()
        world.rows[MODULES[1]]["outcome"] = {"schema": "hexalith.release-outcome.v1", "sha": head(MODULES[1]),
                                             "outcome": "nothing"}
        code, report = self.judge(world)
        self.assertEqual(code, 0)
        self.assertEqual(report["modules"][MODULES[0]]["release"]["outcome"], "published")
        self.assertEqual(report["modules"][MODULES[1]]["release"]["outcome"], "nothing")

    def test_ready_passes_only_when_published_by_this_run(self):
        for publication, verdict in (("published", "pass"), ("pending", "fail"), ("failed", "fail")):
            with self.subTest(publication=publication):
                world = World()
                world.rows[MODULES[0]]["outcome"].update(outcome="ready", draftId=5, lastTag="v1.2.2")
                world.rows[MODULES[0]]["publication"] = publication
                _, report = self.judge(world)
                self.assertEqual(report["modules"][MODULES[0]]["verdict"], verdict)
                if verdict == "fail":
                    self.assertIn("not published by this run", self.reasons(report, MODULES[0]))

    def test_disabled_failed_and_unsuccessful_releases_fail(self):
        def outcome(value):
            return lambda row: row["outcome"].update(outcome=value)
        cases = {"disabled": (outcome("disabled"), "publishing is disabled"),
                 "failed outcome": (outcome("failed"), "release outcome is failed"),
                 "failed run": (lambda row: row.update(conclusion="failure"), "concluded failure"),
                 "outcome unreadable": (lambda row: row.update(outcome=None, outcomeError="artifact gone"),
                                        "outcome unreadable"),
                 "not dispatched": (lambda row: row.update(dispatch="failed", runId=0, link="", status="",
                                                           conclusion=""), "dispatch is failed"),
                 "ineligible": (lambda row: row.update(eligibility="failed", dispatch="failed", runId=0, link="",
                                                       reason="eligibility failed: drift"), "eligibility is failed"),
                 "not adopted": (lambda row: row.update(eligibility="not-adopted", dispatch="skipped", runId=0,
                                                        link="", deliveredSha="", dispatchHead=""), "not-adopted"),
                 "outcome for another source": (lambda row: row["outcome"].update(sha="f" * 40),
                                                "not the dispatched head"),
                 "malformed row": (lambda row: row.update(verdict="green"), "nightly row: verdict is malformed")}
        for name, (change, message) in cases.items():
            with self.subTest(case=name):
                world = World()
                change(world.rows[MODULES[0]])
                code, report = self.judge(world)
                self.assertEqual(code, 1)
                self.assertEqual(self.verdicts(report), {MODULES[0]: "fail", MODULES[1]: "pass", MODULES[2]: "pass"})
                self.assertIn(message, self.reasons(report, MODULES[0]))

    def test_linked_release_run_must_match_the_row(self):
        for field, value in (("head_sha", "f" * 40), ("run_attempt", 2), ("conclusion", "failure"),
                             ("path", ".github/workflows/ci.yml"), ("event", "push"), ("head_branch", "other"),
                             ("repository", {"full_name": "Hexalith/Hexalith.Beta"})):
            with self.subTest(field=field):
                world = World()
                world.remote_overrides[MODULES[0]] = {field: value}
                _, report = self.judge(world)
                self.assertEqual(self.verdicts(report)[MODULES[0]], "fail")
                self.assertIn("release run", self.reasons(report, MODULES[0]))
                self.assertEqual(self.verdicts(report)[MODULES[1]], "pass")

    def test_failed_skipped_or_missing_codeql_fails_a_declaring_module(self):
        def conclusion(value):
            return lambda jobs: jobs[1].update(conclusion=value)
        cases = {"failed": (conclusion("failure"), "concluded failure"),
                 "skipped": (conclusion("skipped"), "concluded skipped"),
                 "missing": (lambda jobs: jobs.pop(1), "no successful Release CodeQL (csharp) job"),
                 "other language": (lambda jobs: jobs[1].update(name="release / Release CodeQL (python)"),
                                    "no successful Release CodeQL (csharp) job"),
                 "extra failed language": (lambda jobs: jobs.append({"name": "release / Release CodeQL (python)",
                                                                     "status": "completed", "conclusion": "failure"}),
                                           "Release CodeQL (python) concluded failure")}
        for name, (change, message) in cases.items():
            with self.subTest(case=name):
                world = World()
                change(world.release_jobs[MODULES[0]])
                _, report = self.judge(world)
                self.assertEqual(self.verdicts(report)[MODULES[0]], "fail")
                self.assertIn(message, self.reasons(report, MODULES[0]))
                self.assertEqual(self.verdicts(report)[MODULES[1]], "pass")

    def test_module_without_codeql_languages_ignores_the_skipped_matrix_job(self):
        world = World()
        world.languages[MODULES[0]] = []
        world.release_jobs[MODULES[0]][1].update(name="release / Release CodeQL (${{ matrix.language }})",
                                                 conclusion="skipped")
        code, report = self.judge(world)
        self.assertEqual(code, 0)
        self.assertEqual(report["modules"][MODULES[0]]["codeql"]["languages"], [])

    def test_missing_module_evidence_fails_only_that_module(self):
        cases = {"render": (lambda world, github: github.routes.pop(
                     API + f"contents/rendered/{MODULES[0]}/.github/hexalith-ci.json?ref={SOURCE}"),
                     "hexalith-ci.json is not found at the delivered revision"),
                 "release run": (lambda world, github: github.routes.pop(
                     f"repos/Hexalith/{MODULES[0]}/actions/runs/7001"), "release run is not found"),
                 "release jobs": (lambda world, github: github.routes.pop(
                     f"repos/Hexalith/{MODULES[0]}/actions/runs/7001/attempts/1/jobs?per_page=100"),
                     "jobs listing is not found")}
        for name, (change, message) in cases.items():
            with self.subTest(case=name):
                world = World()
                github = world.github()
                change(world, github)
                code, report = self.judge(github, *MODULES)
                self.assertEqual(code, 1)
                self.assertEqual(self.verdicts(report), {MODULES[0]: "fail", MODULES[1]: "pass", MODULES[2]: "pass"})
                self.assertIn(message, self.reasons(report, MODULES[0]))

    def test_codeql_languages_come_from_the_delivered_render(self):
        world = World()
        github = world.github()
        path = f"rendered/{MODULES[0]}/.github/hexalith-ci.json"
        github.routes[API + f"contents/{path}?ref={SOURCE}"]["sha"] = "0" * 40
        _, report = self.judge(github, *MODULES)
        self.assertEqual(self.verdicts(report)[MODULES[0]], "fail")
        self.assertIn("CodeQL languages unproven", self.reasons(report, MODULES[0]))
        world = World()
        world.rows[MODULES[0]]["deliveredSha"] = ""
        _, report = self.judge(world)
        self.assertIn("no delivered CiCd revision", self.reasons(report, MODULES[0]))

    def test_release_jobs_over_one_page_fail_closed(self):
        world = World()
        world.release_jobs[MODULES[0]].extend({"name": f"job {index}", "status": "completed", "conclusion": "success"}
                                              for index in range(100))
        _, report = self.judge(world)
        self.assertEqual(self.verdicts(report)[MODULES[0]], "fail")
        self.assertIn("over one page", self.reasons(report, MODULES[0]))

    def test_module_outside_the_registry_fails(self):
        _, report = self.judge(World(), MODULES[0], "Hexalith.Unregistered")
        self.assertEqual(self.verdicts(report), {MODULES[0]: "pass", "Hexalith.Unregistered": "fail"})

    def test_other_rows_builds_and_overall_conclusion_never_change_a_verdict(self):
        world = World()
        world.rows[MODULES[1]].update(conclusion="failure", verdict="fail", reason="release run concluded failure")
        world.builds.update(conclusion="failure", verdict="fail", reason="release run concluded failure")
        world.nightly_result = "fail"
        world.run["conclusion"] = "failure"
        world.jobs["publish-ready"]["conclusion"] = world.jobs["bump"]["conclusion"] = "failure"
        code, report = self.judge(world, MODULES[0])
        self.assertEqual(code, 0)
        self.assertEqual(report["others"], {
            MODULES[1]: {"verdict": "fail", "reason": "release run concluded failure"},
            MODULES[2]: {"verdict": "pass", "reason": "release workflow succeeded"},
            "Hexalith.Builds": {"verdict": "fail", "reason": "release run concluded failure"}})
        self.assertEqual((report["night"]["result"], report["run"]["conclusion"]), ("fail", "failure"))
        # Non-selected targets are reported from nightly.json without re-authentication.
        self.assertFalse([call for call in self.github_calls if MODULES[1] in call or "Hexalith.Builds" in call])

    def test_a_disabled_row_that_nightly_passed_still_fails_d2(self):
        world = World()
        world.rows[MODULES[0]]["outcome"]["outcome"] = "disabled"
        _, report = self.judge(world, MODULES[0])
        self.assertEqual(self.verdicts(report), {MODULES[0]: "fail"})


class ScanTests(Harness):
    def test_own_scan_error_fails_it_while_another_modules_error_or_release_failure_does_not(self):
        world = World()
        world.scan["modules"][0].update(result="fail", errors=["scripts/a.py:1: local-script discovery: unsupported"])
        world.scan["result"] = "fail"
        world.rows[MODULES[2]].update(conclusion="failure")
        code, report = self.judge(world)
        self.assertEqual(code, 1)
        self.assertEqual(self.verdicts(report), {MODULES[0]: "fail", MODULES[1]: "pass", MODULES[2]: "fail"})
        self.assertIn("own scan row failed: scripts/a.py:1", self.reasons(report, MODULES[0]))
        self.assertNotIn("scan", self.reasons(report, MODULES[2]))
        code, report = self.judge(world, MODULES[1])
        self.assertEqual(code, 0)

    def test_scan_row_must_cover_the_dispatched_head(self):
        world = World()
        world.scan["modules"][0]["revision"] = "f" * 40
        _, report = self.judge(world)
        self.assertEqual(self.verdicts(report)[MODULES[0]], "fail")
        self.assertIn("is not the dispatched head", self.reasons(report, MODULES[0]))

    def test_missing_row_report_errors_findings_and_controller_fail_closed(self):
        finding = {"format": "python", "lines": 12, "tokens": 80, "fragment": "x",
                   "first": {"module": MODULES[0], "path": "a.py", "start": 1, "end": 12},
                   "second": {"module": MODULES[1], "path": "b.py", "start": 1, "end": 12}}
        cases = {"no row": (lambda scan: scan["modules"].pop(0), {MODULES[0]}, "no row"),
                 "run-level error": (lambda scan: scan["errors"].append("detector unavailable"), set(MODULES),
                                     "run-level errors"),
                 "finding": (lambda scan: scan["findings"].append(finding), {MODULES[0], MODULES[1]},
                             "cross-module duplicate findings"),
                 "controller": (lambda scan: scan.update(controllerRevision=""), set(MODULES), "controller revision"),
                 "schema": (lambda scan: scan.update(schema="other"), set(MODULES), "not hexalith.duplicate-scan.v1")}
        for name, (change, failed, message) in cases.items():
            with self.subTest(case=name):
                world = World()
                change(world.scan)
                _, report = self.judge(world)
                self.assertEqual({module for module, verdict in self.verdicts(report).items() if verdict == "fail"},
                                 failed)
                for module in failed:
                    self.assertIn(message, self.reasons(report, module))

    def test_missing_or_non_json_scan_report_fails_modules_without_rejecting(self):
        world = World()
        world.omit.add("scan")
        code, report = self.judge(world)
        self.assertEqual(code, 1)
        self.assertIn("scan artifact is missing", self.reasons(report, MODULES[0]))
        world = World()
        world.scan = b"{truncated"
        code, report = self.judge(world)
        self.assertEqual((code, set(self.verdicts(report).values())), (1, {"fail"}))
        self.assertIn("report.json is not JSON", self.reasons(report, MODULES[0]))

    def test_scan_yml_missing_workflow_fails_modules_without_rejecting(self):
        world = World()
        del world.jobs["scan"]
        world.omit.add("scan")
        code, report = self.judge(world, MODULES[0])
        self.assertEqual(code, 1)
        self.assertIn("scan.yml workflow_runs listing is not found", self.reasons(report, MODULES[0]))

    def test_scan_yml_fallback_uses_the_first_run_covering_the_dispatched_head(self):
        world = World()
        del world.jobs["scan"]
        world.omit.add("scan")
        stale = {module: ("f" * 40, "pass", []) for module in MODULES}
        world.scan_runs = [
            ("2026-11-18T08:00:00Z", world.scan_report(**{module: ("0" * 40, "fail", ["before"]) for module in MODULES})),
            ("2026-11-18T09:00:00Z", world.scan_report(**stale)),
            ("2026-11-18T09:30:00Z", None),
            ("2026-11-18T10:00:00Z", world.scan_report(**{MODULES[1]: (head(MODULES[1]), "fail", ["own error"])})),
            ("2026-11-18T11:00:00Z", world.scan_report()),
        ]
        code, report = self.judge(world)
        self.assertEqual(code, 1)
        self.assertEqual(self.verdicts(report), {MODULES[0]: "pass", MODULES[1]: "fail", MODULES[2]: "pass"})
        self.assertEqual(report["modules"][MODULES[0]]["scan"], {"source": "scan.yml", "runId": 60004})
        self.assertIn("own scan row failed: own error", self.reasons(report, MODULES[1]))
        # The run created before the nightly is never read; each report is downloaded once.
        self.assertFalse([call for call in self.github_calls if "runs/60001/" in call])
        self.assertEqual([item["id"] for item in report["artifacts"] if item["name"] == "hexalith-nightly-scan-1"],
                         [15000000002, 15000000004])
        world.scan_runs = world.scan_runs[:3]
        _, report = self.judge(world, MODULES[0])
        self.assertEqual(self.verdicts(report), {MODULES[0]: "fail"})
        self.assertIn("no completed scan.yml run", self.reasons(report, MODULES[0]))

    def test_scan_yml_fallback_skips_unreadable_runs_until_a_covering_run_decides(self):
        world = World()
        del world.jobs["scan"]
        world.omit.add("scan")
        seed = dict(world.scan_report(), controllerRevision="", modules=[], errors=["checkout unavailable"])
        failing = world.scan_report(**{module: (head(module), "fail", ["pull request row"]) for module in MODULES})
        world.scan_runs = [("2026-11-18T09:00:00Z", seed), ("2026-11-18T09:10:00Z", b"{not json"),
                           ("2026-11-18T09:20:00Z", failing, "pull_request"),
                           ("2026-11-18T10:00:00Z", world.scan_report())]
        code, report = self.judge(world)
        self.assertEqual(code, 0)
        self.assertEqual({item["scan"]["runId"] for item in report["modules"].values()}, {60004})
        # The pull_request run is never read; each other report is downloaded and recorded once.
        self.assertFalse([call for call in self.github_calls if "runs/60003/" in call])
        self.assertEqual([item["id"] for item in report["artifacts"] if item["name"] == "hexalith-nightly-scan-1"],
                         [15000000001, 15000000002, 15000000004])
        self.assertEqual(len([call for call in self.github_calls if call.endswith("artifacts/15000000002/zip")]), 1)
        world.scan_runs = world.scan_runs[:3]
        _, report = self.judge(world, MODULES[0])
        reason = self.reasons(report, MODULES[0])
        self.assertIn("no completed scan.yml run", reason)
        self.assertIn("skipped scan.yml run 60001: scan report controller revision", reason)
        self.assertIn("skipped scan.yml run 60002: hexalith-nightly-scan-1 report.json is not JSON", reason)

    def test_scan_yml_digest_mismatch_rejects(self):
        world = World()
        del world.jobs["scan"]
        world.omit.add("scan")
        world.scan_runs = [("2026-11-18T09:00:00Z", world.scan_report())]
        github = world.github()
        github.blobs[API + "actions/artifacts/15000000001/zip"] += b"\0"
        code, _ = self.judge(github, *MODULES)
        self.assertEqual(code, 2)
        self.assertIn("API size", self.stderr)


class DeliveryAndCheckpointTests(Harness):
    def test_pushed_bump_requires_each_modules_green_delivery_row(self):
        world = World()
        world.pushed({MODULES[0]: "success", MODULES[1]: "failure"})
        code, report = self.judge(world)
        self.assertEqual(code, 1)
        self.assertEqual(self.verdicts(report), {MODULES[0]: "pass", MODULES[1]: "fail", MODULES[2]: "fail"})
        self.assertIn("first CI is failure", self.reasons(report, MODULES[1]))
        self.assertIn("no delivery-wait row after pushed bump", self.reasons(report, MODULES[2]))
        self.assertEqual(report["push"], {"state": "pushed", "candidate": CANDIDATE})

    def test_unproven_push_or_delivery_fails_modules_without_rejecting(self):
        cases = {"push report missing": (lambda world: world.omit.add("bump-push"), "bump push result unproven"),
                 "delivery report missing": (lambda world: world.omit.add("delivery-wait"),
                                             "delivery-wait report is missing"),
                 "delivery for another candidate": (lambda world: world.delivery.update(bump="a" * 40),
                                                    "identity, candidate or rows are malformed"),
                 "push identity": (lambda world: world.push["identity"].update(night="2026-11-17"),
                                   "bump push result unproven"),
                 "push not JSON": (lambda world: setattr(world, "push", b"nope"), "bump-push.json is not JSON"),
                 "no bump-push job": (lambda world: world.jobs.pop("bump-push"), "the attempt has no bump-push job"),
                 "seeded push result": (lambda world: world.push.update(result="fail"), "bump-push result is fail"),
                 "qualification result": (lambda world: world.push.update(result="qualified"),
                                          "bump-push result is qualified")}
        for name, (change, message) in cases.items():
            with self.subTest(case=name):
                world = World()
                world.pushed()
                change(world)
                code, report = self.judge(world)
                self.assertEqual(code, 1)
                self.assertEqual(set(self.verdicts(report).values()), {"fail"})
                self.assertIn(message, self.reasons(report, MODULES[0]))

    def test_unpushed_bump_needs_no_delivery_row(self):
        world = World()
        world.pushed()
        world.push.update(result="failed", reason="main raced")
        world.omit.add("delivery-wait")
        code, report = self.judge(world)
        self.assertEqual(code, 0)
        self.assertEqual(report["push"], {"state": "failed"})

    def test_pilot_checkpoint_fails_on_the_44264031228_failed_bump(self):
        world = World()
        world.bump.update(result="failed", tag="v6.3.0", candidate="",
                          reason="candidate efb17b0a7d00f8d7945932fa4e919bed3de5aa02 failed shared global checks for v6.3.0")
        world.jobs["bump"]["conclusion"] = "failure"
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "r.json"
            code, report = self.judge(world, MODULES[0], MODULES[1], checkpoint="pilot", receipt=receipt)
            self.assertEqual(code, 1)
            self.assertEqual(self.verdicts(report), {MODULES[0]: "pass", MODULES[1]: "pass"})
            checkpoint = report["checkpoint"]
            self.assertEqual((checkpoint["name"], checkpoint["verdict"]), ("pilot", "fail"))
            self.assertEqual(checkpoint["reasons"], ["Builds bump to v6.3.0 failed: candidate efb17b0a7d00f8d7945932fa4e9"
                                                     "19bed3de5aa02 failed shared global checks for v6.3.0"])
            stored = json.loads(receipt.read_bytes())
            self.assertEqual(stored["checkpoint"], {"name": "pilot", "verdict": "fail",
                                                    "reasons": checkpoint["reasons"]})

    def test_bad_builds_pin_produces_no_candidate_and_fails_the_checkpoint(self):
        from bump_support import FixtureGit, Workspace, producer, rt

        world = World((MODULES[0],))
        with tempfile.TemporaryDirectory() as temporary:
            bump = Workspace(temporary)
            gate = bump.cicd / "tools/check_global.py"
            gate.parent.mkdir()
            gate.write_text(
                "import pathlib, subprocess, sys\n"
                "project = pathlib.Path.cwd()\n"
                "assert sys.flags.isolated\n"
                "assert sys.argv[1:] == ['--project-root', str(project), '--suites', 'pin']\n"
                "pin = subprocess.check_output(['git', 'show', 'HEAD:builds-version'], text=True).strip()\n"
                f"assert pin == {bump.new['tag']!r}\n"
                "print('controlled pin gate rejected ' + pin)\n"
                "raise SystemExit(1)\n")
            bump.commit()
            with mock.patch.object(rt, "Git", FixtureGit), mock.patch("sys.stdout", new=io.StringIO()):
                result = producer.produce(bump.transport, bump.directory, world.bump_identity(), render=bump.render)
            self.assertIn("controlled pin gate rejected " + bump.new["tag"],
                          (bump.directory / "global.log").read_text())
            self.assertEqual(result["result"], "failed")
            self.assertIn("failed shared global checks for " + bump.new["tag"], result["reason"])
            self.assertEqual(result["candidate"], "")
            self.assertFalse((bump.directory / "candidate.json").exists())
            world.bump = (bump.directory / "bump.json").read_bytes()

        world.jobs["bump"]["conclusion"] = "failure"
        code, report = self.judge(world, MODULES[0], checkpoint="pilot")
        self.assertEqual(code, 1)
        self.assertEqual(self.verdicts(report), {MODULES[0]: "pass"})
        self.assertEqual(report["push"], {"state": "not-run"})
        self.assertEqual(report["checkpoint"]["verdict"], "fail")
        self.assertIn("failed shared global checks for " + bump.new["tag"], " | ".join(report["checkpoint"]["reasons"]))

    def test_pilot_checkpoint_passes_on_no_change_or_pushed_and_delivered(self):
        world = World()
        code, report = self.judge(world, checkpoint="pilot")
        self.assertEqual((code, report["checkpoint"]["verdict"]), (0, "pass"))
        world = World()
        world.pushed()
        code, report = self.judge(world, checkpoint="pilot")
        self.assertEqual((code, report["checkpoint"]["verdict"]), (0, "pass"))
        self.assertEqual(report["checkpoint"]["bump"]["tag"], "v6.3.0")

    def test_pilot_checkpoint_failures(self):
        def pushed_then(change):
            def apply(world):
                world.pushed()
                change(world)
            return apply
        cases = {"keepalive failed": (lambda world: world.keepalive.update(result="fail", errors=["enable failed"]),
                                      "keepalive is fail: enable failed"),
                 "keepalive missing": (lambda world: world.omit.add("keepalive"), "keepalive report is missing"),
                 "keepalive not JSON": (lambda world: setattr(world, "keepalive", b"\xff"),
                                        "keepalive.json is not JSON"),
                 "bump not JSON": (lambda world: setattr(world, "bump", b"[1,"), "bump.json is not JSON"),
                 "bump missing": (lambda world: world.omit.add("bump-report"), "bump report is missing"),
                 "bump identity": (lambda world: world.bump["identity"].update(runId=RUN + 1),
                                   "bump report identity does not match"),
                 "candidate not pushed": (lambda world: world.bump.update(result="candidate", candidate=CANDIDATE,
                                                                         tag="v6.3.0"),
                                          "bump candidate for v6.3.0 was not pushed (bump-push not-run)"),
                 "delivery red": (pushed_then(lambda world: world.delivery.update(result="fail")),
                                  "delivery-wait after the v6.3.0 bump is fail")}
        for name, (change, message) in cases.items():
            with self.subTest(case=name):
                world = World()
                change(world)
                code, report = self.judge(world, MODULES[0], checkpoint="pilot")
                self.assertEqual(code, 1)
                self.assertEqual(report["checkpoint"]["verdict"], "fail")
                self.assertIn(message, " | ".join(report["checkpoint"]["reasons"]))


class ReceiptAndTransportTests(Harness):
    def test_receipt_holds_identities_only(self):
        world = World()
        world.rows[MODULES[1]].update(outcomeError="x" * 500, conclusion="failure")
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "receipt.json"
            code, report = self.judge(world, receipt=receipt)
            self.assertEqual(code, 1)
            data = receipt.read_bytes()
            self.assertLessEqual(len(data), 16 * 1024)
            value = json.loads(data)
            self.assertEqual(set(value), {"schema", "run", "artifacts", "modules", "checkpoint"})
            self.assertEqual(value["schema"], "hexalith.nightly-acceptance-receipt.v1")
            self.assertEqual(value["run"], {"id": RUN, "attempt": 1, "event": "workflow_dispatch", "head": SOURCE})
            self.assertEqual([set(item) for item in value["artifacts"]], [{"name", "id", "digest"}] * 2)
            self.assertEqual(value["artifacts"], report["artifacts"])
            self.assertEqual({set(item) == {"verdict", "reasons"} for item in value["modules"].values()}, {True})
            self.assertIsNone(value["checkpoint"])
            self.assertTrue(all(len(reason) <= 200 for item in value["modules"].values() for reason in item["reasons"]))
            self.assertEqual([path.name for path in Path(directory).iterdir()], ["receipt.json"])

    def test_each_reason_is_capped_at_200_characters(self):
        world = World()
        world.bump.update(result="failed", tag="v" + "9" * 80, reason="r" * 400)
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "receipt.json"
            _, report = self.judge(world, MODULES[0], checkpoint="pilot", receipt=receipt)
            reasons = json.loads(receipt.read_bytes())["checkpoint"]["reasons"]
        self.assertEqual(reasons, report["checkpoint"]["reasons"])
        self.assertEqual(len(reasons[0]), 200)
        self.assertTrue(reasons[0].endswith("..."))

    def test_unwritable_receipt_leaves_no_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "receipt.json"
            receipt.mkdir()
            code, _ = self.judge(World(), receipt=receipt)
            self.assertEqual(code, 2)
            self.assertIn("receipt not written", self.stderr)
            self.assertEqual([path.name for path in Path(directory).iterdir()], ["receipt.json"])

    def test_receipt_over_16_kib_is_not_written(self):
        modules = tuple(f"Hexalith.Module{index:02d}" for index in range(1, 18))
        world = World(modules)
        noise = "n" * 400
        for module, row in world.rows.items():
            row.update(conclusion="failure", outcomeError=noise, outcome=None)
            world.remote_overrides[module] = {"head_sha": "f" * 40, "run_attempt": 3, "path": noise}
            world.release_jobs[module][1].update(conclusion="failure", name="release / Release CodeQL (" + noise + ")")
        for row in world.scan["modules"]:
            row.update(revision="f" * 40, result="fail", errors=[noise])
        world.scan["errors"].append(noise)
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "receipt.json"
            code, _ = self.judge(world, *modules, receipt=receipt)
            self.assertEqual(code, 2)
            self.assertIn("over the 16 KiB limit", self.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])
        code, report = self.judge(world, *modules)
        self.assertEqual(code, 1)

    def test_transport_runs_only_get_through_the_callers_gh_profile(self):
        world = World()
        fake = world.github()
        observed = []
        def runner(argv, **options):
            observed.append((argv, options))
            endpoint = argv[-1]
            if endpoint in fake.blobs:
                return subprocess.CompletedProcess(argv, 0, fake.blobs[endpoint], b"")
            if endpoint in fake.routes:
                return subprocess.CompletedProcess(argv, 0, json.dumps(fake.routes[endpoint]).encode(), b"")
            return subprocess.CompletedProcess(argv, 1, b"", b"gh: Not Found (HTTP 404)")
        github = tool.GitHub(run=runner)
        github.calls = []
        code, report = self.judge(github, *MODULES, checkpoint="pilot")
        self.assertEqual(code, 0)
        self.assertGreater(len(observed), 10)
        for argv, options in observed:
            self.assertEqual(argv[:4], ["gh", "api", "--method", "GET"])
            self.assertEqual(len(argv), 5)
            self.assertTrue(argv[4].startswith("repos/Hexalith/"))
            # No env: the caller's unchanged gh environment and profile.
            self.assertNotIn("env", options)
            self.assertIs(options["stdin"], subprocess.DEVNULL)
        # gh's 404 is missing evidence; any other failure is a transport error.
        with self.assertRaises(tool.NotFound):
            github.json("repos/Hexalith/Hexalith.CiCd/actions/runs/1")
        failing = tool.GitHub(run=lambda argv, **options: subprocess.CompletedProcess(
            argv, 1, b"", b"gh: Bad Gateway (HTTP 502)"))
        with self.assertRaises(tool.TransportError) as raised:
            failing.blob("repos/Hexalith/Hexalith.CiCd/actions/artifacts/1/zip")
        self.assertNotIsInstance(raised.exception, tool.NotFound)
        def unavailable(argv, **options):
            raise FileNotFoundError("gh")
        with self.assertRaisesRegex(tool.TransportError, "gh"):
            tool.GitHub(run=unavailable).json("repos/Hexalith/Hexalith.CiCd/actions/runs/1")
        with self.assertRaisesRegex(tool.TransportError, "outside the Hexalith"):
            github.json("repos/Other/Repo/actions/runs/1")
        with self.assertRaisesRegex(tool.TransportError, "outside the Hexalith"):
            github.json("https://api.github.com/repos/Hexalith/Hexalith.CiCd")

    def test_listing_must_be_one_complete_page(self):
        world = World()
        github = world.github()
        listing = github.routes[API + f"actions/runs/{RUN}/artifacts?per_page=100"]
        listing["total_count"] = 101
        code, _ = self.judge(github, *MODULES)
        self.assertEqual(code, 2)
        self.assertIn("over one page", self.stderr)
        listing["total_count"] = len(listing["artifacts"]) + 1
        code, _ = self.judge(github, *MODULES)
        self.assertEqual(code, 2)
        self.assertIn("incomplete", self.stderr)


class ProducerContractTests(unittest.TestCase):
    """The tool mirrors, never imports, the contracts its producers write."""

    @staticmethod
    def source_schemas(path):
        """Every literal "schema" value written in a dict display of a producer without a constant."""
        found = set()
        for node in ast.walk(ast.parse((ROOT / path).read_bytes())):
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if isinstance(key, ast.Constant) and key.value == "schema" and isinstance(value, ast.Constant):
                        found.add(value.value)
        return found

    @staticmethod
    def source_constant(path, name):
        for node in ast.parse((ROOT / path).read_bytes()).body:
            if isinstance(node, ast.Assign) and [target.id for target in node.targets
                                                 if isinstance(target, ast.Name)] == [name]:
                return ast.literal_eval(node.value)
        raise AssertionError(f"{path} has no {name}")

    def test_mirrored_contracts_equal_their_producers(self):
        runtime = load(ROOT / "tools/nightly_runtime.py", "_nightly_acceptance_runtime")
        delivery_wait = load(ROOT / "tools/nightly_delivery_wait.py", "_nightly_acceptance_delivery_wait")
        self.assertEqual(tool.ROW_KEYS, runtime.ROW_KEYS)
        self.assertEqual(tool.STATE_KEYS, runtime.STATE_KEYS)
        self.assertEqual(tool.DIGEST.pattern, runtime.DIGEST.pattern)
        self.assertEqual(tool.NIGHTLY_SCHEMA, runtime.SCHEMA)
        self.assertEqual(tool.DELIVERY_SCHEMA, delivery_wait.SCHEMA)
        # scan.py's constant is read from source: importing it needs PyYAML,
        # which this stdlib-only suite does not carry.
        self.assertEqual(tool.SCAN_SCHEMA, self.source_constant("tools/scan.py", "SCHEMA"))
        # These producers write their schema inline and expose no constant.
        self.assertEqual(self.source_schemas("tools/bump.py"), {tool.BUMP_SCHEMA})
        self.assertEqual(self.source_schemas("tools/bump_push.py") - {"hexalith.nightly-bump-qualification.v1"},
                         {tool.PUSH_SCHEMA})
        self.assertEqual(self.source_schemas("tools/nightly_keepalive.py"), {tool.KEEPALIVE_SCHEMA})

    def test_fixture_nightly_state_passes_the_runtime_contract(self):
        runtime = load(ROOT / "tools/nightly_runtime.py", "_nightly_acceptance_runtime")
        world = World()
        value = runtime.validate_state(world.nightly(), MODULES, identity={"runId": RUN, "attempt": 1,
                                                                          "source": SOURCE}, phase="nightly")
        self.assertEqual(tool.validate_nightly(value, world.run), {row["repository"]: row for row in value["targets"]})


if __name__ == "__main__":
    unittest.main()
