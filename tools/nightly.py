#!/usr/bin/env python3
"""Nightly release orchestration. App jobs execute this stdlib-only controller."""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
def load(filename, identity):
    spec = importlib.util.spec_from_file_location(identity, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[identity] = module
    spec.loader.exec_module(module)
    return module

rt = load("nightly_runtime.py", "_nightly_controller_runtime")

# Controller budgets leave each 55/330-minute job its checkout, trailing mint,
# finalization and upload reserve after the last controller-scheduled work.
SECONDS = {"dispatch": 46 * 60, "wait": 320 * 60, "publish-ready": 46 * 60}
PHASES = {"dispatch": "dispatch", "wait": "wait", "publish-ready": "nightly"}
STATUSES = {"queued", "requested", "waiting", "pending", "in_progress", "completed"}
CONCLUSIONS = {"success", "failure", "neutral", "cancelled", "skipped", "timed_out", "action_required", "stale", "startup_failure"}
SUPPRESSED = "further orchestration errors suppressed"


def positive(value):
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal() or int(value) < 1 or len(value) > 20:
        raise rt.NightlyError("invalid positive workflow identity")
    return int(value)


def identity(environment):
    if environment.get("GITHUB_REPOSITORY") != "Hexalith/Hexalith.CiCd" or environment.get("GITHUB_REF") != "refs/heads/main":
        raise rt.NightlyError("nightly requires Hexalith.CiCd main")
    if environment.get("GITHUB_EVENT_NAME") not in {"schedule", "workflow_dispatch"}:
        raise rt.NightlyError("nightly requires schedule or workflow_dispatch")
    return {"runId": positive(environment.get("GITHUB_RUN_ID", "")),
            "attempt": positive(environment.get("GITHUB_RUN_ATTEMPT", "")),
            "source": rt.sha(environment.get("GITHUB_SHA", ""))}


def row(repository):
    return {"repository": repository, "workflow": ".github/workflows/" + ("builds-release.yml" if repository == rt.BUILDS else "release.yml"),
            "deliveredSha": "", "dispatchHead": "", "runId": 0, "runAttempt": 0, "link": "",
            "eligibility": "pending", "dispatch": "pending", "status": "", "conclusion": "", "outcome": None,
            "outcomeError": "", "publication": "pending", "verdict": "pending", "reason": ""}


def fail(state, reason, item=None):
    reason = rt.clean(reason)
    if item is None:
        # Stay inside the closed state's 100-error bound so observations survive.
        if reason not in state["errors"]:
            if len(state["errors"]) < 99:
                state["errors"].append(reason)
            elif SUPPRESSED not in state["errors"]:
                state["errors"].append(SUPPRESSED)
    else:
        item["reason"] = rt.clean((item["reason"] + "; " if item["reason"] else "") + reason)


def output(path, values):
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as stream:
        for key, value in values.items():
            value = str(value)
            if not key.replace("_", "").isalnum() or len(value) > 4096 or any(c in value for c in "\n\r\0"):
                raise rt.NightlyError("invalid bounded workflow output")
            stream.write(key + "=" + value + "\n")


def committed(project, expected):
    git = rt.Git(project)
    if git.resolve("HEAD^{commit}") != expected["source"]:
        raise rt.NightlyError("checkout does not match nightly source")
    modules = rt.registry(git, expected["source"])
    if len(modules) > rt.CAPACITY:
        raise rt.NightlyError(f"committed registry exceeds {rt.CAPACITY} modules")
    return git, modules


def initial(expected, modules):
    return {"schema": "hexalith.nightly.v1", "phase": "dispatch", "identity": expected,
            "registry": modules, "builds": {"tag": "", "sha": ""},
            "targets": [row(repo) for repo in [*modules, rt.BUILDS]], "errors": [], "wait": None, "result": "pending"}


def state_path(directory, phase):
    return directory / (PHASES[phase] + ".json")


def read_local(directory, phase, modules, expected):
    return rt.read_state(state_path(directory, phase), modules, identity=expected, phase=PHASES[phase])


def handoff(api, artifact, predecessor, expected, modules, token):
    identifier = positive(artifact)
    metadata = api.get(f"/repos/Hexalith/{rt.CICD}/actions/artifacts/{identifier}", token)
    if (not isinstance(metadata, dict) or metadata.get("id") != identifier
            or metadata.get("name") != f"hexalith-nightly-{predecessor}-{expected['attempt']}"
            or metadata.get("expired") is not False or not isinstance(metadata.get("workflow_run"), dict)
            or metadata["workflow_run"].get("id") != expected["runId"]):
        raise rt.NightlyError("handoff artifact does not belong to this nightly run/phase/attempt")
    value = api.artifact_member(rt.CICD, metadata, predecessor + ".json", token)
    return rt.validate_state(value, modules, identity=expected, phase=predecessor)


def initialize(phase, directory, project, expected, environment, transport, tokens, clock):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Persist conservative state before registry reads, HTTP, trusted imports or dispatch.
    state = initial(expected, [])
    state["phase"] = PHASES[phase]
    fail(state, "nightly initialization did not complete")
    rt.atomic(state_path(directory, phase), state)
    started = clock()
    rt.atomic(directory / "job.json", {"phase": phase, "started": started})
    try:
        git, modules = committed(project, expected)
        transport.api.repositories = frozenset([rt.CICD, rt.BUILDS, *modules])
        state = initial(expected, modules)
        state["phase"] = PHASES[phase]
        fail(state, "nightly initialization did not complete")
        rt.atomic(state_path(directory, phase), state)
        if phase != "dispatch":
            predecessor = "dispatch" if phase == "wait" else "wait"
            try:
                state = handoff(transport.api, environment.get("NIGHTLY_ARTIFACT_ID", ""), predecessor,
                                expected, modules, tokens.get("HANDOFF_TOKEN", ""))
            except Exception as error:
                state = initial(expected, modules)
                fail(state, "missing or invalid " + predecessor + " handoff: " + str(error))
            state["phase"] = PHASES[phase]
        if phase == "wait":
            state["wait"] = {"started": started, "deadline": started + 300 * 60}
        if not state["builds"]["tag"]:
            tag = git.blob(expected["source"], "builds-version").decode("utf-8").strip()
            if not rt.TAG.fullmatch(tag):
                raise rt.NightlyError("builds-version is not an exact stable tag")
            state["builds"]["tag"] = tag
        helpers = transport.helpers(state["builds"]["tag"], directory / "trusted")
        if state["builds"]["sha"] and state["builds"]["sha"] != helpers.source:
            raise rt.NightlyError("trusted Builds source changed across nightly handoff")
        state["builds"]["sha"] = helpers.source
        for item in state["targets"]:
            if item["outcome"] is not None:
                try:
                    item["outcome"] = helpers.outcome.validate_outcome(item["outcome"])
                except Exception as error:
                    item["outcome"] = None
                    item["outcomeError"] = rt.clean(error)
        state["errors"] = [error for error in state["errors"] if error != "nightly initialization did not complete"]
    except Exception as error:
        fail(state, "nightly initialization failed: " + str(error))
        for item in state["targets"]:
            if item["outcome"] is not None:
                item["outcome"] = None
                item["outcomeError"] = "trusted outcome validation did not complete"
    rt.atomic(state_path(directory, phase), state)
    if phase == "publish-ready":
        return {f"slot_{index:02d}": target["repository"] for index, target in enumerate(state["targets"], 1)
                if publishable(target)}
    return {}


def publishable(item):
    """One rule gates publication slots, write-scoped mints and target budgets."""
    return (item["eligibility"] == "eligible" and item["dispatch"] == "dispatched" and item["status"] == "completed"
            and item["conclusion"] == "success" and not item["outcomeError"] and isinstance(item["outcome"], dict)
            and item["outcome"].get("outcome") == "ready" and item["publication"] == "pending")


def needs_poll(item):
    # A failed dispatch's known run is observed for diagnostics until its
    # identity is shown irreconcilable; it can never pass either way.
    return item["runId"] > 0 and not (item["dispatch"] != "dispatched" and item["outcomeError"]) and (
        item["status"] != "completed" or item["outcome"] is None and not item["outcomeError"])


def permit(state, phase, slot, budget, clock):
    budget.check()
    values = {"active": "false"}
    if slot is not None:
        if not 1 <= slot <= len(state["targets"]):
            raise rt.NightlyError("invalid target slot")
        item = state["targets"][slot - 1]
        active = (item["eligibility"] == "eligible" and item["dispatch"] == "pending" if phase == "dispatch" else
                  publishable(item))
    elif phase == "wait":
        pending = [item["repository"] for item in state["targets"] if needs_poll(item)]
        active = bool(pending) and clock() < state["wait"]["deadline"]
        values["repositories"] = ",".join(pending)
    else:
        active = not state["errors"]
    if active:
        values.update(active="true", mint_epoch=str(clock()))
    return values


def delivery_barrier(state, transport, token, directory, clock, sleep):
    deadline = min(clock() + 30 * 60, transport.budget.started + SECONDS["dispatch"] - 120)
    previous = transport.budget.deadline
    if previous is not None:
        deadline = min(deadline, previous)
    transport.budget.deadline = deadline
    consecutive_idle = 0
    try:
        while True:
            # Observe queued work before running work: a queued→in_progress
            # transition must remain visible during this bounded scan.
            runs = []
            try:
                for status in ("requested", "waiting", "pending", "queued", "in_progress"):
                    if clock() >= deadline:
                        raise rt.NightlyError("delivery barrier exceeded 30 minutes")
                    runs.extend(transport.api.pages(
                        f"/repos/Hexalith/{rt.CICD}/actions/workflows/deliver.yml/runs?branch=main&status={status}",
                        token, field="workflow_runs", deadline=deadline))
            except rt.InventoryChanged:
                # Discard the whole scan. A fresh pass must observe queued work
                # again; no partial inventory can establish an idle barrier.
                busy = True
            else:
                busy = False
                for run in runs:
                    if (not isinstance(run, dict) or run.get("head_branch") != "main"
                            or run.get("path", "").split("@", 1)[0] != ".github/workflows/deliver.yml"
                            or run.get("status") not in STATUSES):
                        raise rt.NightlyError("delivery run status is unreadable")
                    busy |= run["status"] != "completed"
            if clock() >= deadline:
                raise rt.NightlyError("delivery barrier exceeded 30 minutes")
            # A run can move to waiting after we queried that status. Confirm
            # an empty scan on the next poll before allowing dispatch.
            consecutive_idle = 0 if busy else consecutive_idle + 1
            if consecutive_idle == 2:
                (directory / "barrier-cleared").write_text("cleared\n")
                return
            if clock() + 60 >= deadline:
                raise rt.NightlyError("delivery barrier did not clear within 30 minutes")
            sleep(60)
    finally:
        transport.budget.deadline = previous


def select(state, transport, directory):
    if state["errors"] or not (directory / "barrier-cleared").is_file():
        raise rt.NightlyError("delivery barrier or initialization failed; no release dispatched")
    cicd = rt.Git(directory / "cicd.git", transport.budget)
    cicd.init()
    values = {}
    for index, item in enumerate(state["targets"], 1):
        # A stalled anonymous module cannot spend the whole dispatch job before
        # the remaining slots (including Builds) receive their own attempt.
        parent_budget = transport.budget
        target_budget = rt.Budget(parent_budget.started, job_seconds=parent_budget.job_seconds,
            token_epoch=parent_budget.token_epoch,
            deadline=min(parent_budget.clock() + 20, parent_budget.started + SECONDS["dispatch"] - 10 * 60),
            clock=parent_budget.clock)
        transport.budget = target_budget
        transport.api.budget = target_budget
        cicd.budget = target_budget
        try:
            if item["repository"] != rt.BUILDS:
                accepted = transport.accepted(cicd, item["repository"])
                if accepted is None:
                    item.update(eligibility="not-adopted", dispatch="skipped", reason="no delivered ref; not adopted")
                    continue
                item["deliveredSha"] = accepted
                target = rt.Git(directory / f"target-{index}.git", transport.budget)
                target.init()
                head = transport.module(target, item["repository"])
                item["dispatchHead"] = head
                target.blob(head, ".github/hexalith-ci.json")
                for caller in ("ci.yml", "release.yml"):
                    actual = ".github/workflows/" + caller
                    expected = f"rendered/{item['repository']}/" + actual
                    left, right = target.items(head, actual).get(actual), cicd.items(accepted, expected).get(expected)
                    if left is None or right is None or left[:2] != right[:2] or target.blob(head, actual) != cicd.blob(accepted, expected):
                        raise rt.NightlyError("live caller differs from delivered state: " + caller)
            item["eligibility"] = "eligible"
            values[f"slot_{index:02d}"] = item["repository"]
        except Exception as error:
            item.update(eligibility="failed", dispatch="failed")
            fail(state, "eligibility failed: " + str(error), item)
        finally:
            transport.budget = parent_budget
            transport.api.budget = parent_budget
            cicd.budget = parent_budget
    return values


def run_identity(run, item):
    rt.run_identity(run, item["repository"], item["workflow"], item["runId"])
    if (not isinstance(run, dict) or run.get("id") != item["runId"] or type(run.get("run_attempt")) is not int
            or run["run_attempt"] < 1 or not isinstance(run.get("repository"), dict)
            or run["repository"].get("full_name") != "Hexalith/" + item["repository"]
            or run.get("path") != item["workflow"]
            or run.get("event") != "workflow_dispatch" or run.get("head_branch") != "main"
            or run.get("status") not in STATUSES):
        raise rt.NightlyError("correlated release run identity mismatch")
    rt.sha(run.get("head_sha"))
    if item["dispatchHead"] and run["head_sha"] != item["dispatchHead"]:
        raise rt.NightlyError("correlated release run source changed")
    if run["status"] == "completed" and run.get("conclusion") not in CONCLUSIONS:
        raise rt.NightlyError("correlated run conclusion is unreadable")
    if run["run_attempt"] < item["runAttempt"]:
        raise rt.NightlyError("correlated run attempt moved backwards")
    return run


def created_run_not_yet_visible(error):
    """GitHub may 404 a just-created run id; that is a read lag, not an uncertain write."""
    text = str(error)
    return "HTTP 404" in text and "GET " in text


def dispatch_target(state, item, transport, token, persist=lambda: None, sleep=time.sleep):
    if item["eligibility"] != "eligible" or item["dispatch"] != "pending":
        raise rt.NightlyError("target is not eligible for a new dispatch")
    if token and item["repository"] != rt.BUILDS:
        # The authenticated immutable-release setting completes eligibility;
        # an unverified setting is failed eligibility and nothing is dispatched.
        try:
            setting = transport.api.get(f"/repos/Hexalith/{item['repository']}/immutable-releases", token)
            if not isinstance(setting, dict) or setting.get("enabled") is not True:
                raise rt.NightlyError("immutable releases are not confirmed enabled")
        except Exception as error:
            item.update(eligibility="failed", dispatch="failed")
            fail(state, "eligibility failed: " + str(error), item)
            return False
    try:
        if not token:
            raise rt.NightlyError("target-scoped App mint unavailable")
        inputs = {} if item["repository"] == rt.BUILDS else {"delivered-sha": item["deliveredSha"]}
        created = transport.api.dispatch(item["repository"], item["workflow"].rsplit("/", 1)[-1], inputs, token)
        # Persist exact identities even if their subsequent authenticated read fails.
        item.update(runId=created["runId"], link=created["link"])
        persist()
        path = f"/repos/Hexalith/{item['repository']}/actions/runs/{item['runId']}"
        for attempt in range(3):
            try:
                run = transport.api.get(path, token)
                break
            except Exception as error:
                if not created_run_not_yet_visible(error) or attempt == 2:
                    raise
                delay = attempt + 1
                if transport.budget.remaining(token=True) < delay + 2:
                    raise
                sleep(delay)
        run_identity(run, item)
        item.update(dispatch="dispatched", dispatchHead=run["head_sha"], runAttempt=run["run_attempt"],
                    status=run["status"], conclusion=run.get("conclusion") or "")
        return True
    except Exception as error:
        item["dispatch"] = "failed"
        fail(state, "dispatch failed (not retried): " + str(error), item)
        return False


def outcome(item, run, transport, token, helpers):
    artifacts = transport.api.pages(f"/repos/Hexalith/{item['repository']}/actions/runs/{item['runId']}/artifacts", token,
                                        field="artifacts")
    matches = [value for value in artifacts if isinstance(value, dict) and value.get("name") == "hexalith-release-outcome"]
    if len(matches) != 1:
        raise rt.NightlyError("correlated run must have exactly one release outcome artifact")
    metadata = matches[0]
    producer = metadata.get("workflow_run")
    if (metadata.get("expired") is not False or not isinstance(producer, dict)
            or producer.get("id") != item["runId"] or producer.get("head_sha") != item["dispatchHead"]
            or rt.timestamp(metadata.get("created_at")) < rt.timestamp(run.get("run_started_at"))):
        raise rt.NightlyError("release outcome artifact is expired or from another run attempt")
    value = transport.api.artifact_member(item["repository"], metadata, "outcome.json", token)
    return helpers.outcome.validate_outcome(value)


def poll(state, transport, token, directory, persist, clock, sleep):
    if not token:
        raise rt.NightlyError("poll-scoped App mint unavailable; no stale token reused")
    limit = min(clock() + 40 * 60, state["wait"]["deadline"])
    transport.budget.deadline = limit
    helpers = transport.cached_helpers(state["builds"]["tag"], state["builds"]["sha"], directory / "trusted")
    unreadable = False
    def ending():
        # Every request keeps its full bounded timeout inside this slice. An
        # observation cut by the slice edge stays pollable for the next slice.
        return limit - clock() < 31
    while clock() < limit:
        cycle = clock()
        pending = [item for item in state["targets"] if needs_poll(item)]
        if not pending:
            break
        for item in pending:
            if ending():
                break
            try:
                run = transport.api.get(f"/repos/Hexalith/{item['repository']}/actions/runs/{item['runId']}", token)
            except Exception as error:
                fail(state, "run status read failed for " + item["repository"] + ": " + str(error))
                unreadable = True
                persist()
                continue
            try:
                run_identity(run, item)
            except Exception as error:
                if item["dispatch"] != "dispatched":
                    # A readable run that can never match its failed dispatch
                    # is final target data, not an unreadable status.
                    item["outcomeError"] = rt.clean("correlated run cannot be accepted: " + str(error))
                else:
                    fail(state, "run status read failed for " + item["repository"] + ": " + str(error))
                    unreadable = True
                persist()
                continue
            item.update(dispatchHead=run["head_sha"], runAttempt=run["run_attempt"],
                        status=run["status"], conclusion=run.get("conclusion") or "")
            persist()
            if run["status"] == "completed":
                try:
                    document = outcome(item, run, transport, token, helpers)
                except Exception as error:
                    if not ending():
                        item["outcomeError"] = rt.clean(error)
                    persist()
                    continue
                try:
                    current = transport.api.get(f"/repos/Hexalith/{item['repository']}/actions/runs/{item['runId']}", token)
                    run_identity(current, item)
                    item.update(runAttempt=current["run_attempt"], status=current["status"], conclusion=current.get("conclusion") or "")
                    if current["run_attempt"] != run["run_attempt"] or current["status"] != "completed":
                        item["outcome"] = None
                        item["outcomeError"] = "release run/attempt changed while reading outcome"
                    else:
                        item["outcome"] = document
                        item["outcomeError"] = ""
                except Exception as error:
                    item["outcome"] = None
                    if ending():
                        item["outcomeError"] = ""
                    else:
                        item["outcomeError"] = rt.clean(error)
                        fail(state, "run status recheck failed for " + item["repository"] + ": " + str(error))
                        unreadable = True
                persist()
        if not any(needs_poll(item) for item in state["targets"]):
            break
        pause = min(max(0, 60 - (clock() - cycle)), max(0, limit - clock()))
        if pause:
            sleep(pause)
    return int(unreadable)


def target_budget(parent, state, phase, slot):
    """Bound one target while keeping a fair share and report reserve for others."""
    later = state["targets"][slot:]
    if phase == "dispatch":
        remaining = sum(item["eligibility"] == "eligible" and item["dispatch"] == "pending" for item in later)
    else:
        remaining = sum(publishable(item) for item in later)
    share = max(1, (parent.remaining() - 120) / (remaining + 1))
    deadline = parent.clock() + min(60, share)
    if parent.deadline is not None:
        deadline = min(deadline, parent.deadline)
    return rt.Budget(parent.started, job_seconds=parent.job_seconds, token_epoch=parent.token_epoch,
                     deadline=deadline, clock=parent.clock)


def finalize(state, phase, cancelled, summary):
    if cancelled:
        fail(state, "nightly orchestration was cancelled")
    if phase == "dispatch":
        for item in state["targets"]:
            if item["dispatch"] == "pending":
                item["dispatch"] = "failed"
                fail(state, "target dispatch did not complete", item)
        return int(bool(state["errors"] or any(item["dispatch"] == "failed" for item in state["targets"])))
    if phase == "wait":
        for item in state["targets"]:
            if item["dispatch"] == "dispatched" and item["status"] != "completed":
                fail(state, "release unfinished at wait deadline or interrupted wait", item)
        return int(bool(state["errors"]))
    publisher = load("nightly_publish.py", "_nightly_controller_publisher")
    return int(publisher.reduce_report(state, summary))


def main(argv=None, *, transport=None, clock=time.time, sleep=time.sleep):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("initialize", "permit", "barrier", "select", "dispatch", "poll", "publish", "finalize"))
    parser.add_argument("--phase", choices=tuple(SECONDS), required=True)
    parser.add_argument("--slot", type=int)
    args = parser.parse_args(argv)
    environment = dict(os.environ)
    tokens = rt.sanitize()
    expected = identity(environment)
    project = Path(environment.get("GITHUB_WORKSPACE", ".")).resolve()
    directory = Path(environment["NIGHTLY_DIRECTORY"]).resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Every temporary Git store, export and HTTP scratch file stays in this job root.
    os.environ.update(TMPDIR=str(directory), TMP=str(directory), TEMP=str(directory))
    import tempfile
    tempfile.tempdir = str(directory)
    try:
        started = clock() if args.operation == "initialize" else rt.json_read((directory / "job.json").read_bytes())["started"]
    except Exception:
        if args.operation != "finalize":
            raise rt.NightlyError("local job clock is unavailable") from None
        started = clock()
    epoch = environment.get("NIGHTLY_MINT_EPOCH", "")
    budget = rt.Budget(started, job_seconds=SECONDS[args.phase], token_epoch=float(epoch) if epoch else
                       started if args.operation == "initialize" else None, clock=clock)
    transport = transport or rt.Transport(budget)
    transport.budget = budget
    transport.api.budget = budget
    if args.operation == "initialize":
        values = initialize(args.phase, directory, project, expected, environment, transport, tokens, clock)
        output(environment.get("GITHUB_OUTPUT"), values)
        return 0
    try:
        _, modules = committed(project, expected)
    except Exception as error:
        if args.operation != "finalize":
            raise
        modules = []
        registry_error = rt.clean(error)
    else:
        registry_error = ""
    transport.api.repositories = frozenset([rt.CICD, rt.BUILDS, *modules])
    try:
        state = read_local(directory, args.phase, modules, expected)
    except Exception as error:
        if args.operation != "finalize":
            raise
        state = initial(expected, modules)
        state["phase"] = PHASES[args.phase]
        fail(state, "local state unavailable: " + str(error))
    if registry_error:
        fail(state, "committed registry unavailable: " + registry_error)
    path = state_path(directory, args.phase)
    persist = lambda: rt.atomic(path, state)
    code, values = 0, {}
    try:
        if environment.get("NIGHTLY_CANCELLED") == "true" and args.operation != "finalize":
            raise rt.NightlyError("nightly was cancelled; operation suppressed")
        if args.operation in {"dispatch", "publish"}:
            if args.slot is None or not 1 <= args.slot <= len(state["targets"]):
                raise rt.NightlyError("invalid target slot")
            budget = target_budget(budget, state, args.phase, args.slot)
            transport.budget = budget
            transport.api.budget = budget
        if args.operation == "permit":
            values = permit(state, args.phase, args.slot, budget, clock)
        elif args.operation == "barrier":
            delivery_barrier(state, transport, tokens.get("CICD_TOKEN", ""), directory, clock, sleep)
        elif args.operation == "select":
            values = select(state, transport, directory)
        elif args.operation == "dispatch":
            # A failed target step is visible in Actions; continue-on-error keeps siblings running.
            code = int(not dispatch_target(state, state["targets"][args.slot - 1], transport,
                                           tokens.get("TARGET_TOKEN", ""), persist, sleep))
        elif args.operation == "poll":
            code = poll(state, transport, tokens.get("POLL_TOKEN", ""), directory, persist, clock, sleep)
        elif args.operation == "publish":
            item = state["targets"][args.slot - 1]
            helpers = transport.cached_helpers(state["builds"]["tag"], state["builds"]["sha"], directory / "trusted")
            publisher = load("nightly_publish.py", "_nightly_controller_publisher")
            code = int(not publisher.publish_target(item, helpers, transport, directory / ("publication-" + str(args.slot)),
                                                    budget, tokens.get("TARGET_TOKEN", "")))
        else:
            code = finalize(state, args.phase, environment.get("NIGHTLY_CANCELLED") == "true", environment.get("GITHUB_STEP_SUMMARY"))
    except Exception as error:
        if args.operation == "publish" and args.slot is not None and 1 <= args.slot <= len(state["targets"]):
            state["targets"][args.slot - 1].update(publication="failed", reason="publication failed: " + rt.clean(error))
        fail(state, args.operation + " failed: " + str(error))
        if args.operation == "finalize" and args.phase == "publish-ready":
            state["result"] = "fail"
        code = 1
    persist()
    output(environment.get("GITHUB_OUTPUT"), values)
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print("nightly controller failed: " + rt.clean(error), file=sys.stderr)
        raise SystemExit(2) from None
