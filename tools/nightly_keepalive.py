#!/usr/bin/env python3
"""Keep CiCd schedules enabled and refresh an idle main with an empty commit."""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import time

sys.dont_write_bytecode = True
_SPEC = importlib.util.spec_from_file_location("_nightly_keepalive_runtime", Path(__file__).with_name("nightly_runtime.py"))
rt = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = rt
_SPEC.loader.exec_module(rt)

IDLE_SECONDS = 50 * 24 * 3600
JOB_SECONDS = 8 * 60


def context(environment):
    if (environment.get("GITHUB_REPOSITORY") != "Hexalith/Hexalith.CiCd"
            or environment.get("GITHUB_REF") != "refs/heads/main"
            or environment.get("GITHUB_EVENT_NAME") not in {"schedule", "workflow_dispatch"}):
        raise rt.NightlyError("keepalive requires a nightly run on Hexalith.CiCd main")


def remote_main(git, transport):
    rows = git.run("ls-remote", "--heads", transport.remote(rt.CICD), "refs/heads/main").decode("ascii").splitlines()
    if len(rows) != 1 or rows[0].split("\t")[1:] != ["refs/heads/main"]:
        raise rt.NightlyError("keepalive remote main identity is ambiguous")
    return rt.sha(rows[0].split("\t")[0])


def run(directory, environment, token, transport, *, clock=time.time):
    report = {"schema": "hexalith.nightly-keepalive.v1", "result": "pending", "enabled": {},
              "base": None, "candidate": None, "ageSeconds": None, "commit": "pending", "errors": []}
    path = directory / "keepalive.json"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    rt.atomic(path, report)
    def fail(reason):
        report["errors"].append(rt.clean(reason))
        rt.atomic(path, report)
    try:
        context(environment)
        if environment.get("NIGHTLY_CANCELLED") == "true":
            raise rt.NightlyError("nightly cancelled; keepalive writes suppressed")
        # Attempt every enable even if an earlier request fails.
        for workflow in rt.KEEPALIVE_WORKFLOWS:
            try:
                transport.api.enable(workflow, token)
                report["enabled"][workflow] = "enabled"
            except Exception as error:
                report["enabled"][workflow] = "failed"
                fail(workflow + " enable failed: " + rt.clean(error))
        with tempfile.TemporaryDirectory(prefix="nightly-keepalive-", dir=directory) as temporary:
            git = rt.Git(Path(temporary) / "cicd.git", transport.budget)
            git.init()
            transport.cicd(git)
            base = git.resolve("refs/heads/main^{commit}")
            report["base"] = base
            raw_stamp = git.run("show", "-s", "--format=%ct", base).decode("ascii").strip()
            if not raw_stamp.isdecimal() or len(raw_stamp) > 20:
                raise rt.NightlyError("keepalive main committer timestamp is malformed")
            now = rt.number(clock(), positive=True)
            age = now - int(raw_stamp)
            if age < 0:
                raise rt.NightlyError("keepalive main committer timestamp is in the future")
            report["ageSeconds"] = age
            if age <= IDLE_SECONDS:
                report["commit"] = "not-needed"
            else:
                tree = git.resolve(base + "^{tree}")
                # commit-tree writes only an object; no checkout, filters or hooks execute.
                candidate = rt.sha(git.run("commit-tree", tree, "-p", base,
                                            data=b"build(cicd): keepalive\n").decode("ascii").strip())
                report["candidate"] = candidate
                if git.resolve(candidate + "^{tree}") != tree:
                    raise rt.NightlyError("keepalive candidate is not empty")
                if remote_main(git, transport) != base:
                    raise rt.NightlyError("keepalive main advanced; empty commit not pushed")
                code, _ = git.run("push", "--porcelain", "--no-verify", "--no-recurse-submodules",
                                  transport.remote(rt.CICD), candidate + ":refs/heads/main", token=token, check=False)
                if code:
                    raise rt.NightlyError("keepalive fast-forward push failed; write not retried")
                if remote_main(git, transport) != candidate:
                    raise rt.NightlyError("keepalive pushed main could not be confirmed; write not retried")
                report["commit"] = "pushed"
    except Exception as error:
        report["commit"] = "failed"
        fail(rt.clean(error))
    report["result"] = "fail" if report["errors"] else "pass"
    rt.atomic(path, report)
    summary = environment.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("\nNightly keepalive: **" + report["result"].upper() + "**; commit: " + report["commit"] + ".\n")
            for error in report["errors"]:
                stream.write("\n- " + error + "\n")
    return int(bool(report["errors"]))


def main(argv=None, *, transport=None, clock=time.time):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("run",), nargs="?", default="run")
    parser.parse_args(argv)
    environment = dict(os.environ)
    tokens = rt.sanitize()
    started = clock()
    epoch = environment.get("NIGHTLY_MINT_EPOCH", "")
    # The 15-minute job also reserves three minutes each for checkout and
    # artifact upload, plus the controller's usual trailing 30-second reserve.
    budget = rt.Budget(started, job_seconds=JOB_SECONDS, token_epoch=float(epoch) if epoch else started, clock=clock)
    transport = transport or rt.Transport(budget)
    transport.budget = transport.api.budget = budget
    transport.api.repositories = frozenset((rt.CICD,))
    directory = Path(environment["NIGHTLY_DIRECTORY"]).resolve()
    return run(directory, environment, tokens.get("CICD_TOKEN", ""), transport, clock=clock)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print("nightly keepalive failed: " + rt.clean(error), file=sys.stderr)
        raise SystemExit(2) from None
