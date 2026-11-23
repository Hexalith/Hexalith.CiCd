#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Real bare Git keepalive writes, independent schedule enables and idle thresholds."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from delivery_support import ROOT, git, load
from nightly_support import Clock

controller = load(ROOT / "tools/nightly_keepalive.py", "_keepalive_tests")
rt = controller.rt
WORKFLOWS = ["nightly.yml", "deliver.yml", "scan.yml"]


class Fixture:
    def __init__(self, root, *, idle=controller.IDLE_SECONDS + 1):
        self.root = Path(root)
        self.clock = Clock()
        self.source = self.root / "source"
        self.source.mkdir()
        git(self.source, "init", "--quiet", "--initial-branch=main")
        (self.source / "product").write_text("inert\n")
        git(self.source, "add", ".")
        env = os.environ | {"GIT_AUTHOR_DATE": str(int(self.clock() - idle)) + " +0000",
                           "GIT_COMMITTER_DATE": str(int(self.clock() - idle)) + " +0000"}
        subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-C",
                        str(self.source), "commit", "--quiet", "-m", "Initial"], env=env, check=True)
        self.base = git(self.source, "rev-parse", "HEAD")
        self.remote = self.root / "remote.git"
        git(self.root, "clone", "--quiet", "--bare", self.source, self.remote)
        self.directory = self.root / "result"
        self.calls, self.enable_failures = [], set()
        self.race = False
        self.push_fail = False

    def transport(self):
        fixture = self
        budget = rt.Budget(fixture.clock(), job_seconds=12 * 60, token_epoch=fixture.clock(), clock=fixture.clock)
        class API:
            def enable(self, workflow, token):
                budget.check(token=True)
                fixture.calls.append(workflow)
                if workflow in fixture.enable_failures:
                    raise rt.NightlyError("GitHub API PUT enable rejected: HTTP 403")
        class Transport(rt.Transport):
            def remote(self, repository):
                return fixture.remote.as_uri()
            def cicd(self, store):
                # Production's hardened transport remains in use; fixture alone allows file://.
                store.env["GIT_CONFIG_COUNT"] = str(int(store.env["GIT_CONFIG_COUNT"]) + 1)
                index = int(store.env["GIT_CONFIG_COUNT"]) - 1
                store.env[f"GIT_CONFIG_KEY_{index}"] = "protocol.file.allow"
                store.env[f"GIT_CONFIG_VALUE_{index}"] = "always"
                super().cicd(store)
                if fixture.race:
                    git(fixture.source, "commit", "--allow-empty", "--quiet", "-m", "Racing main")
                    git(fixture.source, "push", "--quiet", fixture.remote, "HEAD:main")
                if fixture.push_fail:
                    hook = fixture.remote / "hooks/pre-receive"
                    hook.write_text("#!/bin/sh\nexit 1\n")
                    hook.chmod(0o755)
        return Transport(budget, API())

    def run(self, **extra):
        environment = {"GITHUB_REPOSITORY": "Hexalith/Hexalith.CiCd", "GITHUB_REF": "refs/heads/main",
                       "GITHUB_EVENT_NAME": "schedule", "GITHUB_STEP_SUMMARY": str(self.root / "summary"), **extra}
        self.code = controller.run(self.directory, environment, "inert", self.transport(), clock=self.clock)
        return json.loads((self.directory / "keepalive.json").read_bytes())


class KeepaliveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)

    def fixture(self, **kwargs):
        return Fixture(self.temporary.name, **kwargs)

    def test_old_main_gets_one_exact_empty_fast_forward_commit(self):
        fixture = self.fixture()
        report = fixture.run()
        self.assertEqual(fixture.code, 0)
        self.assertEqual(fixture.calls, WORKFLOWS)
        self.assertEqual(report["enabled"], dict.fromkeys(WORKFLOWS, "enabled"))
        self.assertEqual(report["commit"], "pushed")
        head = git(fixture.remote, "rev-parse", "main")
        self.assertEqual(head, report["candidate"])
        self.assertEqual(git(fixture.remote, "show", "-s", "--format=%s", head), "build(cicd): keepalive")
        self.assertEqual(git(fixture.remote, "rev-parse", head + "^"), fixture.base)
        self.assertEqual(git(fixture.remote, "diff", "--stat", fixture.base, head), "")

    def test_threshold_is_strictly_older_than_fifty_days(self):
        for idle in (0, controller.IDLE_SECONDS - 1, controller.IDLE_SECONDS):
            with self.subTest(idle=idle), tempfile.TemporaryDirectory(dir=self.temporary.name) as root:
                fixture = Fixture(root, idle=idle)
                report = fixture.run()
                self.assertEqual(report["commit"], "not-needed")
                self.assertEqual(git(fixture.remote, "rev-parse", "main"), fixture.base)

    def test_all_enables_attempted_after_first_error_and_idle_main_is_maintained(self):
        fixture = self.fixture()
        fixture.enable_failures.add("nightly.yml")
        report = fixture.run()
        self.assertEqual(fixture.calls, WORKFLOWS)
        self.assertEqual(fixture.code, 1)
        self.assertEqual(report["enabled"], {"nightly.yml": "failed", "deliver.yml": "enabled", "scan.yml": "enabled"})
        self.assertEqual(report["commit"], "pushed")
        self.assertIn("HTTP 403", report["errors"][0])

    def test_all_enable_errors_remain_visible(self):
        fixture = self.fixture(idle=0)
        fixture.enable_failures.update(WORKFLOWS)
        report = fixture.run()
        self.assertEqual(report["enabled"], dict.fromkeys(WORKFLOWS, "failed"))
        self.assertEqual(report["errors"], [f"{name} enable failed: GitHub API PUT enable rejected: HTTP 403"
                                             for name in WORKFLOWS])
        self.assertEqual(report["result"], "fail")

    def test_racing_main_never_overwritten(self):
        fixture = self.fixture()
        fixture.race = True
        report = fixture.run()
        self.assertEqual(report["result"], "fail")
        self.assertIn("main advanced", report["errors"][0])
        self.assertEqual(git(fixture.remote, "show", "-s", "--format=%s", "main"), "Racing main")

    def test_push_failure_is_reported_without_retry(self):
        fixture = self.fixture()
        fixture.push_fail = True
        report = fixture.run()
        self.assertEqual(report["result"], "fail")
        self.assertIn("push failed", report["errors"][0])
        self.assertEqual(git(fixture.remote, "rev-parse", "main"), fixture.base)

    def test_cancelled_or_nonmain_run_never_enables_or_pushes(self):
        for extra in ({"NIGHTLY_CANCELLED": "true"}, {"GITHUB_REF": "refs/heads/other"}):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory(dir=self.temporary.name) as root:
                fixture = Fixture(root)
                report = fixture.run(**extra)
                self.assertEqual(fixture.calls, [])
                self.assertEqual(report["result"], "fail")
                self.assertEqual(git(fixture.remote, "rev-parse", "main"), fixture.base)

    def test_future_timestamp_fails_closed(self):
        fixture = self.fixture(idle=-1)
        report = fixture.run()
        self.assertEqual(report["result"], "fail")
        self.assertIn("future", report["errors"][0])

    def test_isolated_main_uses_job_token_without_persisting_it(self):
        fixture = self.fixture()
        config = fixture.root / "fixture.json"
        config.write_text(json.dumps({"remote": str(fixture.remote), "calls": str(fixture.root / "calls")}))
        environment = os.environ | {"NIGHTLY_DIRECTORY": str(fixture.directory), "CICD_TOKEN": "inert",
            "GITHUB_REPOSITORY": "Hexalith/Hexalith.CiCd", "GITHUB_REF": "refs/heads/main", "GITHUB_EVENT_NAME": "schedule"}
        process = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "driver", str(config)],
                                 capture_output=True, env=environment)
        self.assertEqual(process.returncode, 0, process.stderr.decode())
        self.assertEqual(process.stdout, b"")
        self.assertEqual((fixture.root / "calls").read_text().splitlines(), WORKFLOWS)
        raw = (fixture.directory / "keepalive.json").read_text()
        self.assertNotIn("inert", raw)
        self.assertEqual(json.loads(raw)["commit"], "pushed")


def driver():
    config = json.loads(Path(sys.argv[2]).read_bytes())
    clock = Clock()
    budget = rt.Budget(clock(), job_seconds=12 * 60, token_epoch=clock(), clock=clock)
    class API:
        def enable(self, workflow, token):
            self.budget.check(token=True)
            if token != "inert":
                raise rt.NightlyError("wrong fixture token")
            with Path(config["calls"]).open("a") as stream:
                stream.write(workflow + "\n")
    class Transport(rt.Transport):
        def remote(self, repository):
            return Path(config["remote"]).as_uri()
        def cicd(self, store):
            index = int(store.env["GIT_CONFIG_COUNT"])
            store.env.update(GIT_CONFIG_COUNT=str(index + 1))
            store.env[f"GIT_CONFIG_KEY_{index}"] = "protocol.file.allow"
            store.env[f"GIT_CONFIG_VALUE_{index}"] = "always"
            super().cicd(store)
    raise SystemExit(controller.main([], transport=Transport(budget, API()), clock=clock))


if __name__ == "__main__":
    if sys.argv[1:2] == ["driver"]:
        driver()
    else:
        unittest.main()
