#!/usr/bin/env python3
"""Independently authenticate and constrain a nightly bump before pushing it."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import secrets
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bump_runtime as br
rt = br.rt


def artifact(api, expected, artifact_id, digest, token):
    artifact_id = rt.positive(int(artifact_id))
    if not digest.startswith("sha256:"):
        digest = "sha256:" + digest
    if not rt.DIGEST.fullmatch(digest):
        raise rt.NightlyError("candidate upload digest unavailable or malformed")
    artifacts = api.pages(f"/repos/Hexalith/{rt.CICD}/actions/runs/{expected['runId']}/artifacts", token, field="artifacts")
    name = "hexalith-nightly-bump-" + str(expected["attempt"])
    matches = [item for item in artifacts if isinstance(item, dict) and item.get("name") == name]
    if len(matches) != 1:
        raise rt.NightlyError("candidate artifact missing or duplicated for run attempt")
    item = matches[0]
    producer = item.get("workflow_run")
    if (item.get("id") != artifact_id or type(item.get("id")) is not int or item.get("digest") != digest
            or not isinstance(producer, dict) or producer.get("id") != expected["runId"]
            or producer.get("head_sha") != expected["source"]):
        raise rt.NightlyError("candidate artifact id/name/digest/producer mismatch")
    value = api.artifact_member(rt.CICD, item, "candidate.json", token)
    br.validate_envelope(value, expected)
    return value


def verify(transport, git, builds, value, expected):
    br.validate_envelope(value, expected)
    base = transport.main(git)
    if base != value["base"]:
        raise rt.NightlyError("CiCd main advanced beyond captured candidate parent")
    if br.already_bumped(git, base, expected["night"]):
        raise rt.NightlyError("automatic bump already reachable for UTC night " + expected["night"])
    current, skipped = br.policy(git, base)
    if current != value["old"]["tag"]:
        raise rt.NightlyError("builds-version: current parent tag mismatch")
    selected = transport.select(builds, current, skipped)
    if selected != value["new"]:
        raise rt.NightlyError("newest acceptable Builds release changed after candidate validation")
    if transport.tag(builds, current) != value["old"]:
        raise rt.NightlyError("old Builds tag/commit identity changed")
    candidate = br.reconstruct(git, value, expected)
    br.verify_diff(git, value, builds)
    # Reject unused object baggage, including artifact-supplied source that
    # does not participate in the exact candidate reachable from its base.
    required = set(git.run("rev-list", "--objects", "--no-object-names", candidate, "^" + base).decode().splitlines())
    if required != {item["id"] for item in value["objects"]}:
        raise rt.NightlyError("candidate Git object envelope has missing or unrelated objects")
    return candidate


def push(transport, directory, expected, value, token, *, mode="github-token"):
    if mode not in {"github-token", "app"}:
        raise rt.NightlyError("unqualified bump transport mode")
    report = {"schema": "hexalith.nightly-bump-push.v1", "identity": expected, "result": "failed",
              "base": value.get("base", ""), "candidate": "", "transport": mode,
              "deliveryDispatched": False, "failed": True, "reason": ""}
    try:
        with tempfile.TemporaryDirectory(prefix="bump-writer-") as temporary:
            git = rt.Git(Path(temporary) / "cicd", transport.budget)
            builds = rt.Git(Path(temporary) / "builds", transport.budget)
            git.init()
            builds.init()
            candidate = verify(transport, git, builds, value, expected)
            # Reobserve both independent freshness boundaries after all object
            # and schema work; neither stale main nor a new release is rebased.
            current, skipped = br.policy(git, value["base"])
            if transport.select(builds, current, skipped) != value["new"]:
                raise rt.NightlyError("newest acceptable Builds release raced before push")
            if transport.main(git) != value["base"]:
                raise rt.NightlyError("CiCd main raced before fast-forward push")
            if br.already_bumped(git, value["base"], expected["night"]):
                raise rt.NightlyError("UTC night already contains an automatic bump")
            code, output = git.run("push", "--porcelain", "--no-verify", "--no-recurse-submodules",
                                   transport.remote(rt.CICD), candidate + ":refs/heads/main", token=token, check=False)
            if code:
                raise rt.NightlyError("bump fast-forward push rejected or uncertain; not retried: " + rt.clean(output.decode("utf-8", "replace")))
            live = transport.main(git)
            if not git.ancestor(candidate, live):
                raise rt.NightlyError("bump push remote confirmation failed; not retried")
            # Persist the confirmed write even if the subsequent dispatch fails.
            report.update(result="pushed", candidate=candidate, remoteMain=live)
            rt.atomic(directory / "bump-push.json", report)
            if mode == "github-token":
                transport.api.dispatch_delivery(token)
                report["deliveryDispatched"] = True
            report.update(failed=False, reason="exact validated candidate confirmed on main")
    except Exception as error:
        report["reason"] = rt.clean(error)
    rt.atomic(directory / "bump-push.json", report)
    return report


def qualify(transport, directory, expected, token):
    """Exercise this job token on an isolated inert nested-workflow ref only."""
    report = {"schema": "hexalith.nightly-bump-qualification.v1", "identity": expected,
              "result": "incomplete", "base": "", "candidate": "", "tree": "", "remoteSha": "",
              "remoteTree": "", "ref": "", "cleaned": False, "reason": "",
              "run": rt.run_link(rt.CICD, expected["runId"])}
    reference = f"refs/heads/nightly-bump-probe-{expected['runId']}-{expected['attempt']}-{secrets.token_hex(8)}"
    report["ref"] = reference
    rt.atomic(directory / "bump-push.json", report)
    with tempfile.TemporaryDirectory(prefix="bump-probe-") as temporary:
        git = rt.Git(Path(temporary) / "cicd", transport.budget, index=Path(temporary) / "index")
        git.init()
        try:
            base = transport.main(git)
            report["base"] = base
            if git.run("ls-remote", "--heads", transport.remote(rt.CICD), reference):
                raise rt.NightlyError("isolated probe ref already exists")
            git.run("read-tree", base)
            blob = git.run("hash-object", "-w", "--stdin", data=(
                b"# Inert nested-path permission probe; never a runnable root workflow.\n"
                b"name: Nightly nested path probe\non: workflow_dispatch\njobs:\n"
                b"  inert:\n    runs-on: ubuntu-latest\n    steps:\n      - run: 'true'\n")).decode().strip()
            path = "rendered/Hexalith.Probe/.github/workflows/probe.yml"
            git.run("update-index", "--add", "--cacheinfo", "100644", rt.sha(blob), path)
            tree = rt.sha(git.run("write-tree").decode().strip())
            candidate = rt.sha(git.run("commit-tree", tree, "-p", base,
                                       data=b"build(cicd): qualify nested workflow transport\n").decode().strip())
            changes = git.run("diff-tree", "--no-commit-id", "--name-only", "-r", base, candidate).decode().splitlines()
            if changes != [path]:
                raise rt.NightlyError("probe must change exactly its inert nested workflow")
            report.update(candidate=candidate, tree=tree)
            rt.atomic(directory / "bump-push.json", report)
            code, output = git.run("push", "--porcelain", "--no-verify", "--no-recurse-submodules",
                                   transport.remote(rt.CICD), candidate + ":" + reference, token=token, check=False)
            if code:
                # Only the service's explicit workflow-permission rejection
                # qualifies the App fallback. Generic auth/transport is unknown.
                reason = output.decode("utf-8", "replace")
                if re_permission_rejection(reason):
                    report.update(result="rejected", reason=rt.clean(reason), transport="app")
                else:
                    raise rt.NightlyError("probe push failed without definite workflow-permission rejection: " + rt.clean(reason))
            else:
                git.run("fetch", "--no-tags", "--no-recurse-submodules", transport.remote(rt.CICD),
                        reference + ":refs/remotes/probe")
                remote = git.resolve("refs/remotes/probe^{commit}")
                remote_tree = git.resolve(remote + "^{tree}")
                report.update(remoteSha=remote, remoteTree=remote_tree)
                if remote != candidate or remote_tree != tree:
                    raise rt.NightlyError("probe remote SHA/tree mismatch")
                report.update(result="qualified", reason="job token accepted exact inert nested workflow child", transport="github-token")
        except Exception as error:
            report.update(result="incomplete", reason=rt.clean(error))
        finally:
            try:
                live = git.run("ls-remote", "--heads", transport.remote(rt.CICD), reference)
                if live:
                    oid, ref = live.decode().strip().split("\t")
                    if ref != reference or oid != report["candidate"]:
                        raise rt.NightlyError("probe cleanup refused a racing ref")
                    code, _ = git.run("push", "--porcelain", "--no-verify", "--no-recurse-submodules",
                                      transport.remote(rt.CICD), ":" + reference, token=token, check=False)
                    if code:
                        raise rt.NightlyError("probe ref cleanup push failed")
                if git.run("ls-remote", "--heads", transport.remote(rt.CICD), reference):
                    raise rt.NightlyError("probe ref cleanup not confirmed")
                report["cleaned"] = True
            except Exception as error:
                report.update(result="incomplete", reason=report["reason"] + "; " + rt.clean(error))
    rt.atomic(directory / "bump-push.json", report)
    return report


def re_permission_rejection(reason):
    import re
    return bool(re.search(r"refusing to allow .* to (?:create|update).*workflow.*without.*workflows?.*(?:permission|scope)", reason, re.I))


def main(argv=None, *, transport=None, clock=time.time):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("push", "qualify"), nargs="?", default="push")
    args = parser.parse_args(argv)
    environment = dict(os.environ)
    tokens = rt.sanitize()
    directory = Path(environment["BUMP_DIRECTORY"]).resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    br.scratch(directory / "scratch")
    token = tokens.get("CICD_TOKEN", "")
    # The conditional App route needs only Contents/Workflows write. Its own
    # job's Actions-read GITHUB_TOKEN can authenticate the artifact separately;
    # neither credential is ever received from another job.
    read_token = tokens.get("HANDOFF_TOKEN", "") or token
    epoch = float(environment.get("NIGHTLY_MINT_EPOCH") or clock())
    budget = rt.Budget(clock(), job_seconds=46 * 60, token_epoch=epoch, clock=clock)
    transport = transport or br.Transport(budget)
    transport.budget = transport.api.budget = budget
    try:
        expected = br.identity(environment, transport.api, read_token)
        if args.operation == "qualify":
            report = qualify(transport, directory, expected, token)
        else:
            value = artifact(transport.api, expected, environment.get("BUMP_ARTIFACT_ID", ""),
                             environment.get("BUMP_ARTIFACT_DIGEST", ""), read_token)
            # Detect a rerun that began while the artifact was authenticated.
            if br.identity(environment, transport.api, read_token) != expected:
                raise rt.NightlyError("nightly attempt changed while authenticating candidate")
            report = push(transport, directory, expected, value, token,
                          mode=environment.get("BUMP_TRANSPORT", "github-token"))
    except Exception as error:
        report = {"schema": "hexalith.nightly-bump-push.v1", "result": "failed", "reason": rt.clean(error)}
        rt.atomic(directory / "bump-push.json", report)
    br.output(environment.get("GITHUB_OUTPUT"), {key: report.get(key, "") for key in ("result", "candidate", "base")})
    if environment.get("GITHUB_STEP_SUMMARY"):
        with Path(environment["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
            stream.write("Nightly Builds push: " + report["result"] + " — " + report["reason"] + "\n")
    print("Nightly Builds push: " + report["result"] + " — " + report["reason"])
    return int(report.get("failed", False) or report["result"] not in {"pushed", "qualified", "rejected"})


if __name__ == "__main__":
    raise SystemExit(main())
