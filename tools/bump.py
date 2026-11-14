#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["Jinja2==3.1.6", "PyYAML==6.0.3", "jsonschema==4.26.0"]
# ///
"""Produce a globally checked nightly bump with read-only credentials."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bump_runtime as br
rt = br.rt
JOB_SECONDS = 40 * 60


def run_script(project, script, budget, log):
    """Run the shared committed tool unchanged, within the producer reserve."""
    # The uv script interpreter already contains the locked renderer/global
    # dependencies. A child isolates the controller from tool imports/signals
    # and enforces its aggregate timeout even when a check catches ValueError.
    with log.open("wb") as stream:
        try:
            completed = subprocess.run([sys.executable, "-I", str(project / "tools" / script),
                                        "--project-root", str(project)], cwd=project,
                                       stdout=stream, stderr=subprocess.STDOUT,
                                       timeout=budget.timeout(max_seconds=40 * 60), check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise rt.NightlyError(script + " failed or exceeded the producer budget") from None
    if log.stat().st_size > rt.delivery.MAX_GIT:
        raise rt.NightlyError(script + " log exceeds bounded output limit")
    text = log.read_text(encoding="utf-8", errors="replace")
    if text:
        # Preserve normal shared-check evidence in Actions, with credential
        # redaction applied before output or retained logs cross the boundary.
        for secret in rt.delivery._SECRETS:
            if secret:
                text = text.replace(secret, "[redacted]")
        log.write_text(text, encoding="utf-8")
        print(text, end="" if text.endswith("\n") else "\n")
    return completed.returncode == 0


def produce(transport, directory, expected, *, render=None, check=None):
    candidate_path = directory / "candidate.json"
    candidate_path.unlink(missing_ok=True)
    report = {"schema": "hexalith.nightly-bump-report.v1", "identity": expected,
              "result": "failed", "base": "", "candidate": "", "tag": "", "reason": ""}
    try:
        with tempfile.TemporaryDirectory(prefix="bump-") as temporary:
            project = Path(temporary) / "cicd"
            project.mkdir()
            git = rt.Git(project, transport.budget)
            git.run("init", "--quiet", "--template=", "--initial-branch=main")
            base = transport.main(git)
            report["base"] = base
            if br.already_bumped(git, base, expected["night"]):
                report.update(result="no-change", reason="automatic bump already reachable for UTC night " + expected["night"])
                return report
            current, skipped = br.policy(git, base)
            builds_path = project / "references/Hexalith.Builds"
            builds = rt.Git(builds_path, transport.budget)
            # Checkout committed main before rendering, including its exact
            # templates/setup/tools; no scheduler-SHA source substitutes for it.
            git.run("checkout", "--quiet", "--detach", "--force", base)
            builds.init()
            # The unchanged global gate's suites read older released tags from
            # this reference, like validate's full-tag Builds checkout. Fetch
            # all of them first; selection then reverifies each tag it uses.
            builds.run("fetch", "--no-tags", "--no-recurse-submodules", transport.remote(rt.BUILDS),
                       "+refs/heads/main:refs/remotes/origin/main", "refs/tags/*:refs/tags/*")
            selected = transport.select(builds, current, skipped)
            report["tag"] = selected["tag"]
            if br.version(selected["tag"]) <= br.version(current):
                report.update(result="no-change", reason="no newer acceptable unskipped Builds tag")
                return report
            old = transport.tag(builds, current)
            (project / "builds-version").write_text(selected["tag"] + "\n", encoding="utf-8")
            if render is None:
                if not run_script(project, "render.py", transport.budget, directory / "render.log"):
                    raise rt.NightlyError("render failed for " + selected["tag"])
            else:
                render(project)
            git.run("add", "--", "builds-version", "rendered")
            tree = git.run("write-tree").decode().strip()
            candidate = git.run("commit-tree", rt.sha(tree), "-p", base,
                                data=br.message(selected["tag"], expected["night"])).decode().strip()
            git.run("update-ref", "HEAD", rt.sha(candidate), base)
            # The shared gate compares committed inputs/render against HEAD;
            # it must run only after the local candidate exists.
            if check is None:
                passed = run_script(project, "check_global.py", transport.budget, directory / "global.log")
            else:
                passed = check(project)
            if not passed:
                raise rt.NightlyError("candidate " + candidate + " failed shared global checks for " + selected["tag"])
            value = br.envelope(git, expected, base, candidate, old, selected)
            # Local constraint verification catches an incompatible renderer
            # before producing a usable artifact; the writer repeats it.
            br.verify_diff(git, value, builds)
            rt.atomic(candidate_path, value)
            report.update(result="candidate", candidate=candidate, reason="shared global checks passed")
            return report
    except Exception as error:
        candidate_path.unlink(missing_ok=True)
        report["reason"] = rt.clean(error)
        return report
    finally:
        rt.atomic(directory / "bump.json", report)


def main(*, transport=None, clock=time.time):
    environment = dict(os.environ)
    token = environment.get("GITHUB_TOKEN", "")
    rt.delivery._SECRETS.append(token)
    # The secretless producer has only its job's read-only GITHUB_TOKEN.
    for name in rt.TOKEN_NAMES:
        os.environ.pop(name, None)
    directory = Path(environment["BUMP_DIRECTORY"]).resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    scratch = directory / "scratch"
    br.scratch(scratch)
    # Leave checkout/setup and both final uploads within the 55-minute job.
    budget = rt.Budget(clock(), job_seconds=JOB_SECONDS, token_epoch=clock(), clock=clock)
    transport = transport or br.Transport(budget)
    transport.budget = transport.api.budget = budget
    transport.token = token or None
    try:
        expected = br.identity(environment, transport.api, token or None)
        report = produce(transport, directory, expected)
    except Exception as error:
        (directory / "candidate.json").unlink(missing_ok=True)
        report = {"schema": "hexalith.nightly-bump-report.v1", "result": "failed", "reason": rt.clean(error)}
        rt.atomic(directory / "bump.json", report)
    br.output(environment.get("GITHUB_OUTPUT"), {key: report.get(key, "") for key in ("result", "candidate", "base")})
    summary = environment.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("Nightly Builds bump: " + report["result"] + " — " + report["reason"] + "\n")
    print("Nightly Builds bump: " + report["result"] + " — " + report["reason"])
    return int(report["result"] == "failed")


if __name__ == "__main__":
    raise SystemExit(main())
