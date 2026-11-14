#!/usr/bin/env python3
"""Observe the first real delivery and every pushed module's first completed main CI."""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import re
import sys
import tempfile
import time

sys.dont_write_bytecode = True
_SPEC = importlib.util.spec_from_file_location("_nightly_delivery_wait_runtime", Path(__file__).with_name("nightly_runtime.py"))
rt = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = rt
_SPEC.loader.exec_module(rt)

SCHEMA = "hexalith.nightly-delivery-wait.v1"
WAIT_SECONDS = 90 * 60
SLICE_SECONDS = 40 * 60
JOB_SECONDS = 100 * 60
STATE_KEYS = {"schema", "identity", "bump", "started", "deadline", "since", "repositories", "delivery", "modules", "errors", "result"}
REPORT_KEYS = {"schema", "run_id", "run_attempt", "event", "candidate_sha", "tools_source_sha", "global", "failed", "failures", "freshness", "modules"}
ROW_KEYS = {"repository", "accepted_sha", "advancement", "application", "pushed_sha", "retries", "reasons", "processed"}
STATUSES = {"queued", "requested", "waiting", "pending", "in_progress", "completed"}
CONCLUSIONS = {"success", "failure", "neutral", "cancelled", "skipped", "timed_out", "action_required", "stale", "startup_failure"}


def fail(state, message):
    message = rt.clean(message)
    if message not in state["errors"]:
        if len(state["errors"]) < 99:
            state["errors"].append(message)
        elif "further observation errors suppressed" not in state["errors"]:
            state["errors"].append("further observation errors suppressed")


def positive(value):
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal() or len(value) > 20:
        raise rt.NightlyError("invalid nightly run identity")
    return rt.positive(int(value))


def identity(environment):
    if (environment.get("GITHUB_REPOSITORY") != "Hexalith/Hexalith.CiCd"
            or environment.get("GITHUB_REF") != "refs/heads/main"
            or environment.get("GITHUB_EVENT_NAME") not in {"schedule", "workflow_dispatch"}):
        raise rt.NightlyError("delivery observation requires a nightly run on Hexalith.CiCd main")
    return {"runId": positive(environment.get("GITHUB_RUN_ID", "")),
            "attempt": positive(environment.get("GITHUB_RUN_ATTEMPT", "")),
            "source": rt.sha(environment.get("GITHUB_SHA", ""))}


def output(path, values):
    if path:
        with Path(path).open("a", encoding="utf-8") as stream:
            for key, value in values.items():
                value = str(value)
                if not key.replace("_", "").isalnum() or len(value) > 4096 or any(c in value for c in "\n\r\0"):
                    raise rt.NightlyError("invalid observer workflow output")
                stream.write(key + "=" + value + "\n")


def initial(expected, bump, started):
    return {"schema": SCHEMA, "identity": expected, "bump": bump, "started": started,
            "deadline": started + WAIT_SECONDS, "since": None, "repositories": [], "delivery": None,
            "modules": [], "errors": [], "result": "pending"}


def creation_time(value):
    if (not isinstance(value, str)
            or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value)):
        raise rt.NightlyError("nightly creation timestamp is not canonical UTC")
    rt.timestamp(value)
    return value


def bind_creation(state, api, environment):
    """Bound discovery history by this original run, including time spent queued."""
    expected = state["identity"]
    value = api.get(f"/repos/Hexalith/{rt.CICD}/actions/runs/{expected['runId']}")
    if (not isinstance(value, dict) or type(value.get("id")) is not int or value["id"] != expected["runId"]
            or type(value.get("run_attempt")) is not int or value["run_attempt"] != expected["attempt"]
            or value.get("head_sha") != expected["source"] or value.get("head_branch") != "main"
            or value.get("path") != ".github/workflows/nightly.yml"
            or value.get("event") != environment.get("GITHUB_EVENT_NAME")
            or value.get("html_url") != rt.run_link(rt.CICD, expected["runId"])
            or not isinstance(value.get("repository"), dict)
            or value["repository"].get("full_name") != "Hexalith/" + rt.CICD):
        raise rt.NightlyError("observer nightly creation run/attempt/source identity mismatch")
    since = creation_time(value.get("created_at"))
    if rt.timestamp(since).timestamp() > state["started"]:
        raise rt.NightlyError("nightly creation timestamp is in the future")
    state["since"] = since


def validate_state(value, expected):
    if (not isinstance(value, dict) or set(value) != STATE_KEYS or value["schema"] != SCHEMA
            or value["identity"] != expected or value["result"] not in {"pending", "pass", "fail"}):
        raise rt.NightlyError("invalid observer state or nightly run identity")
    rt.sha(value["bump"])
    rt.number(value["started"], positive=True)
    if value["deadline"] != value["started"] + WAIT_SECONDS:
        raise rt.NightlyError("observer aggregate deadline was changed")
    names = value["repositories"]
    if (not isinstance(names, list) or len(names) > rt.CAPACITY
            or names != sorted(set(rt.name(item) for item in names))
            or len({item.casefold() for item in names}) != len(names)):
        raise rt.NightlyError("observer authorized repository inventory is malformed")
    if not isinstance(value["errors"], list) or len(value["errors"]) > 100:
        raise rt.NightlyError("observer errors are malformed")
    for message in value["errors"]:
        if not isinstance(message, str) or rt.clean(message) != message:
            raise rt.NightlyError("observer diagnostic is malformed")
    if value["since"] is None:
        if "delivery observer initialization incomplete" not in value["errors"]:
            raise rt.NightlyError("observer nightly creation time is unavailable")
    else:
        if rt.timestamp(creation_time(value["since"])).timestamp() > value["started"]:
            raise rt.NightlyError("observer nightly creation timestamp is in the future")
    delivery = value["delivery"]
    if delivery is not None:
        if not isinstance(delivery, dict) or set(delivery) != {"runId", "attempt", "head", "link", "event", "status", "conclusion", "report"}:
            raise rt.NightlyError("observer selected delivery is malformed")
        rt.positive(delivery["runId"])
        rt.positive(delivery["attempt"])
        rt.sha(delivery["head"])
        if (delivery["link"] != rt.run_link(rt.CICD, delivery["runId"])
                or delivery["status"] not in STATUSES or delivery["conclusion"] not in CONCLUSIONS | {None}
                or delivery["event"] not in {"push", "schedule", "workflow_dispatch"}
                or delivery["report"] not in {"pending", "verified", "failed"}):
            raise rt.NightlyError("observer selected delivery identity is malformed")
    if not isinstance(value["modules"], list) or len(value["modules"]) > rt.CAPACITY:
        raise rt.NightlyError("observer module observations are malformed")
    seen = set()
    for row in value["modules"]:
        if (not isinstance(row, dict) or set(row) != {"repository", "pushed", "runId", "attempt", "head", "link", "conclusion", "completedAt", "error"}
                or row["repository"] not in names or row["repository"] in seen):
            raise rt.NightlyError("observer module identity is not authorized")
        seen.add(row["repository"])
        rt.sha(row["pushed"])
        if row["runId"]:
            rt.positive(row["runId"])
            rt.positive(row["attempt"])
            rt.sha(row["head"])
            rt.timestamp(row["completedAt"])
            if (row["link"] != rt.run_link(row["repository"], row["runId"])
                    or row["conclusion"] not in CONCLUSIONS - {"cancelled"}):
                raise rt.NightlyError("observer module CI identity is malformed")
        elif (type(row["runId"]) is not int or row["attempt"] != 0 or row["head"] or row["link"]
              or row["conclusion"] is not None or row["completedAt"]):
            raise rt.NightlyError("observer pending module identity is malformed")
        if not isinstance(row["error"], str) or rt.clean(row["error"]) != row["error"]:
            raise rt.NightlyError("observer module error is malformed")
    return value


def authorize(state, transport, directory):
    """Only bumped-main registry and independent live accepted refs authorize CI reads."""
    with tempfile.TemporaryDirectory(prefix="authorize-", dir=directory) as temporary:
        git = rt.Git(Path(temporary) / "cicd.git", transport.budget)
        git.init()
        transport.cicd(git)
        main = git.resolve("refs/heads/main^{commit}")
        if git.resolve(state["bump"] + "^{commit}") != state["bump"] or not git.ancestor(state["bump"], main):
            raise rt.NightlyError("confirmed bump is not ancestral to live CiCd main")
        names = set(rt.registry(git, state["bump"]))
        seen = set()
        for line in git.run("for-each-ref", "--format=%(refname) %(objectname)", "refs/heads/delivered/").decode("ascii").splitlines():
            ref, target = line.split(" ", 1)
            repository = rt.name(ref.removeprefix("refs/heads/delivered/"))
            if repository.casefold() in seen:
                raise rt.NightlyError("case-colliding delivered refs")
            seen.add(repository.casefold())
            target = rt.sha(target)
            if git.resolve(target + "^{commit}") != target or not git.ancestor(target, main):
                raise rt.NightlyError("delivered ref is not ancestral to live CiCd main: " + repository)
            names.add(repository)
        if len(names) > rt.CAPACITY or len({item.casefold() for item in names}) != len(names):
            raise rt.NightlyError("observer registry/delivered-ref union exceeds 17 or collides")
        state["repositories"] = sorted(names)


def run_document(value, repository, workflow):
    if (not isinstance(value, dict) or value.get("path") != ".github/workflows/" + workflow
            or value.get("head_branch") != "main" or value.get("event") not in {"push", "schedule", "workflow_dispatch"}
            or not isinstance(value.get("repository"), dict)
            or value["repository"].get("full_name") != "Hexalith/" + repository):
        return None
    identifier = rt.positive(value.get("id"))
    rt.positive(value.get("run_attempt"))
    rt.sha(value.get("head_sha"))
    if (value.get("html_url") != rt.run_link(repository, identifier) or value.get("status") not in STATUSES
            or value.get("conclusion") not in CONCLUSIONS | {None}):
        raise rt.NightlyError("malformed qualifying workflow run")
    rt.timestamp(value.get("created_at"))
    if value["conclusion"] == "cancelled":
        return None
    return value


def ancestry(api, repository, base, head, token):
    if base == head:
        return True
    value = api.get(f"/repos/Hexalith/{repository}/compare/{rt.sha(base)}...{rt.sha(head)}?per_page=1&page=2", token)
    if not isinstance(value, dict) or not isinstance(value.get("base_commit"), dict) or not isinstance(value.get("merge_base_commit"), dict):
        raise rt.NightlyError("workflow ancestry response is malformed")
    if value["base_commit"].get("sha") != base:
        raise rt.NightlyError("workflow ancestry base identity mismatch")
    rt.sha(value["merge_base_commit"].get("sha"))
    return value.get("status") in {"ahead", "identical"} and value["merge_base_commit"]["sha"] == base


def jobs(api, repository, run, token):
    return api.pages(f"/repos/Hexalith/{repository}/actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs", token, field="jobs")


def started_delivery(api, run, token):
    matches = []
    for job in jobs(api, rt.CICD, run, token):
        if not isinstance(job, dict):
            raise rt.NightlyError("delivery job inventory is malformed")
        if job.get("name") != "deliver":
            continue
        if (job.get("run_id") != run["id"] or job.get("run_attempt", run["run_attempt"]) != run["run_attempt"]
                or job.get("head_sha") != run["head_sha"]):
            raise rt.NightlyError("delivery attempt-job identity mismatch")
        if job.get("status") in {"in_progress", "completed"} and job.get("conclusion") not in {"skipped", "cancelled"}:
            rt.timestamp(job.get("started_at"))
            matches.append(job)
    if len(matches) > 1:
        raise rt.NightlyError("duplicate deliver job in selected attempt")
    return bool(matches)


def select_delivery(state, api, token):
    since = creation_time(state["since"])
    runs = api.pages(f"/repos/Hexalith/{rt.CICD}/actions/workflows/deliver.yml/runs?branch=main&created=>={since}", token, field="workflow_runs")
    eligible = []
    seen = set()
    for value in runs:
        run = run_document(value, rt.CICD, "deliver.yml")
        if run is None or rt.timestamp(run["created_at"]) < rt.timestamp(since):
            continue
        if run["id"] in seen:
            raise rt.NightlyError("duplicate delivery run identity")
        seen.add(run["id"])
        if ancestry(api, rt.CICD, state["bump"], run["head_sha"], token):
            eligible.append(run)
    for run in sorted(eligible, key=lambda item: (rt.timestamp(item["created_at"]), item["id"])):
        if started_delivery(api, run, token):
            state["delivery"] = {"runId": run["id"], "attempt": run["run_attempt"], "head": run["head_sha"],
                                 "link": run["html_url"], "event": run["event"], "status": run["status"], "conclusion": run["conclusion"], "report": "pending"}
            return


def report_document(value, state):
    selected = state["delivery"]
    if (not isinstance(value, dict) or set(value) != REPORT_KEYS or value["schema"] != "hexalith.delivery.v1"
            or value["run_id"] != str(selected["runId"]) or value["run_attempt"] != str(selected["attempt"])
            or value["candidate_sha"] != selected["head"] or value["event"] != selected["event"]
            or type(value["global"]) is not bool or type(value["failed"]) is not bool
            or not isinstance(value["failures"], list) or len(value["failures"]) > 100
            or not isinstance(value["freshness"], dict) or not isinstance(value["modules"], list)
            or len(value["modules"]) > rt.CAPACITY):
        raise rt.NightlyError("delivery report run/attempt/candidate or schema mismatch")
    rt.sha(value["tools_source_sha"])
    for message in value["failures"]:
        if not isinstance(message, str) or rt.clean(message) != message:
            raise rt.NightlyError("delivery report diagnostic is malformed")
    if value["freshness"].get("status") not in {"not-checked", "not-scheduled", "not-activated", "fresh", "stale", "failed"}:
        raise rt.NightlyError("delivery report freshness status is malformed")
    if value["freshness"]["status"] in {"stale", "failed"}:
        fail(state, "delivery freshness check failed")
    seen, pushed = set(), []
    for item in value["modules"]:
        if not isinstance(item, dict) or set(item) != ROW_KEYS:
            raise rt.NightlyError("delivery report module row is malformed")
        repository = rt.name(item["repository"])
        if repository not in state["repositories"] or repository in seen:
            raise rt.NightlyError("delivery report repository is not independently authorized: " + repository)
        seen.add(repository)
        if (item["advancement"] not in {"skipped", "advanced", "unchanged", "superseded", "failed"}
                or item["application"] not in {"no-ref", "unchanged", "pushed", "failed"}
                or type(item["processed"]) is not bool or type(item["retries"]) is not int or not 0 <= item["retries"] <= 4
                or not isinstance(item["reasons"], list) or len(item["reasons"]) > 100):
            raise rt.NightlyError("delivery report module verdict is malformed")
        for message in item["reasons"]:
            if not isinstance(message, str) or rt.clean(message) != message:
                raise rt.NightlyError("delivery report module diagnostic is malformed")
        if item["accepted_sha"] is not None:
            rt.sha(item["accepted_sha"])
        if item["pushed_sha"] is not None:
            rt.sha(item["pushed_sha"])
            if item["application"] != "pushed" or item["accepted_sha"] is None:
                raise rt.NightlyError("delivery report pushed commit contradicts application")
            pushed.append({"repository": repository, "pushed": item["pushed_sha"], "runId": 0, "attempt": 0,
                           "head": "", "link": "", "conclusion": None, "completedAt": "", "error": ""})
        elif item["application"] == "pushed":
            raise rt.NightlyError("delivery report pushed row has no commit")
        if not item["processed"] or item["advancement"] == "failed" or item["application"] == "failed":
            fail(state, "delivery module failed: " + repository + ": " + "; ".join(item["reasons"]))
    if seen != set(state["repositories"]):
        raise rt.NightlyError("delivery report omits independently authorized module targets")
    if not value["global"] or value["failed"] or value["failures"]:
        fail(state, "delivery report failed: " + "; ".join(value["failures"]))
    return sorted(pushed, key=lambda item: item["repository"])


def observe_delivery(state, api, token):
    selected = state["delivery"]
    path = f"/repos/Hexalith/{rt.CICD}/actions/runs/{selected['runId']}"
    raw = api.get(path, token)
    if (isinstance(raw, dict) and raw.get("id") == selected["runId"]
            and raw.get("run_attempt") == selected["attempt"] and raw.get("head_sha") == selected["head"]
            and raw.get("conclusion") == "cancelled" and selected["report"] == "pending"):
        # An executing run may be cancelled after discovery. It then leaves
        # the eligible set; the next noncancelled delivery can qualify.
        state["delivery"] = None
        return
    run = run_document(raw, rt.CICD, "deliver.yml")
    if run is None or (run["id"], run["run_attempt"], run["head_sha"]) != (selected["runId"], selected["attempt"], selected["head"]):
        raise rt.NightlyError("selected delivery attempt changed or was cancelled")
    selected.update(status=run["status"], conclusion=run["conclusion"])
    if run["status"] != "completed" or selected["report"] != "pending":
        return
    if not started_delivery(api, run, token):
        raise rt.NightlyError("selected delivery did not execute its deliver job")
    if run["conclusion"] != "success":
        fail(state, "delivery failed: " + selected["link"] + " (" + str(run["conclusion"]) + ")")
    artifacts = api.pages(path + "/artifacts", token, field="artifacts")
    matches = [item for item in artifacts if isinstance(item, dict) and item.get("name") == "hexalith-delivery"]
    if len(matches) != 1:
        raise rt.NightlyError("selected delivery report missing or duplicate across rerun attempts")
    metadata = matches[0]
    origin = metadata.get("workflow_run")
    if (not isinstance(origin, dict) or origin.get("id") != run["id"] or origin.get("head_sha") != run["head_sha"]
            or origin.get("head_branch") != "main"):
        raise rt.NightlyError("delivery artifact origin mismatch")
    document = api.artifact_member(rt.CICD, metadata, "delivery.json", token)
    modules = report_document(document, state)
    # Authentication after download prevents an attempt transition from blessing stale bytes.
    refreshed = run_document(api.get(path, token), rt.CICD, "deliver.yml")
    if (refreshed is None or refreshed["id"] != run["id"] or refreshed["run_attempt"] != run["run_attempt"]
            or refreshed["head_sha"] != run["head_sha"] or refreshed["status"] != "completed"
            or refreshed["conclusion"] != run["conclusion"]):
        raise rt.NightlyError("delivery attempt changed while reading report")
    state["modules"] = modules
    selected["report"] = "verified"


def completed_at(api, repository, run, token):
    completed = []
    inventory = jobs(api, repository, run, token)
    if not inventory:
        raise rt.NightlyError("completed CI has no attempt jobs")
    for job in inventory:
        if (not isinstance(job, dict) or job.get("run_id") != run["id"] or job.get("run_attempt", run["run_attempt"]) != run["run_attempt"]
                or job.get("head_sha") != run["head_sha"] or job.get("status") != "completed"):
            raise rt.NightlyError("completed CI attempt-job identity mismatch")
        completed.append(rt.timestamp(job.get("completed_at")))
    return max(completed).isoformat()


def observe_module(row, api, token, since):
    if row["runId"]:
        return
    repository = row["repository"]
    since = creation_time(since)
    values = api.pages(f"/repos/Hexalith/{repository}/actions/workflows/ci.yml/runs?branch=main&created=>={since}", token, field="workflow_runs")
    eligible, seen = [], set()
    for value in values:
        run = run_document(value, repository, "ci.yml")
        if run is None or run["status"] != "completed" or rt.timestamp(run["created_at"]) < rt.timestamp(since):
            continue
        if run["conclusion"] is None:
            raise rt.NightlyError("completed CI conclusion missing")
        if run["id"] in seen:
            raise rt.NightlyError("duplicate module CI run identity")
        seen.add(run["id"])
        if ancestry(api, repository, row["pushed"], run["head_sha"], token):
            completed = completed_at(api, repository, run, token)
            eligible.append((rt.timestamp(completed), run["id"], completed, run))
    if eligible:
        _, _, completed, selected = min(eligible, key=lambda item: item[:2])
        current = run_document(api.get(f"/repos/Hexalith/{repository}/actions/runs/{selected['id']}", token), repository, "ci.yml")
        if (current is None or current["id"] != selected["id"] or current["run_attempt"] != selected["run_attempt"]
                or current["head_sha"] != selected["head_sha"] or current["status"] != "completed"
                or current["conclusion"] != selected["conclusion"]):
            raise rt.NightlyError("module CI attempt changed while selecting its first result")
        row.update(runId=selected["id"], attempt=selected["run_attempt"], head=selected["head_sha"],
                   link=selected["html_url"], conclusion=selected["conclusion"], completedAt=completed)


def finished(state):
    return (state["delivery"] is not None and state["delivery"]["report"] != "pending"
            and all(row["runId"] or row["error"] for row in state["modules"]))


def poll(state, transport, token, persist, *, clock=time.time, sleep=time.sleep):
    if "delivery observer initialization incomplete" in state["errors"]:
        raise rt.NightlyError("delivery observer initialization did not authorize repository scope")
    if not token:
        fail(state, "delivery observer App mint unavailable; no older token reused")
        return 1
    transport.budget.check(token=True)
    end = min(state["deadline"], clock() + SLICE_SECONDS,
              transport.budget.token_epoch + SLICE_SECONDS, transport.budget.started + transport.budget.job_seconds - 30)
    # Whole HTTP operations and retries must fit the slice as well as the
    # aggregate deadline; a request begun at 39:59 cannot extend the token slice.
    transport.budget.deadline = end
    while clock() < end:
        if state["delivery"] is None:
            try:
                select_delivery(state, transport.api, token)
            except Exception as error:
                fail(state, "delivery discovery failed: " + rt.clean(error))
        if state["delivery"] is not None:
            try:
                observe_delivery(state, transport.api, token)
            except Exception as error:
                state["delivery"]["report"] = "failed"
                fail(state, "delivery observation failed: " + rt.clean(error))
            for row in state["modules"]:
                if row["runId"] or row["error"]:
                    continue
                try:
                    observe_module(row, transport.api, token, state["since"])
                except Exception as error:
                    row["error"] = rt.clean(error)
                    fail(state, row["repository"] + " CI observation failed: " + row["error"])
        persist()
        if finished(state):
            return 0
        remaining = end - clock()
        if remaining < 60:
            break
        sleep(60)
    return 0


def finalize(state, environment):
    if environment.get("NIGHTLY_CANCELLED") == "true":
        fail(state, "nightly was cancelled")
    selected = state["delivery"]
    if selected is None:
        fail(state, "qualifying delivery missing at aggregate deadline or interrupted wait")
    elif selected["report"] != "verified" or selected["status"] != "completed" or selected["conclusion"] != "success":
        fail(state, "delivery did not complete successfully with an authenticated current-attempt report: " + selected["link"])
    for row in state["modules"]:
        if not row["runId"]:
            fail(state, row["repository"] + " qualifying module CI missing at aggregate deadline or interrupted wait")
        elif row["conclusion"] != "success":
            fail(state, row["repository"] + " first qualifying module CI failed: " + row["link"] + " (" + row["conclusion"] + ")")
    state["result"] = "fail" if state["errors"] else "pass"
    summary = environment.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("\nNightly bump propagation: **" + state["result"].upper() + "**.\n")
            if selected:
                stream.write("\n- [Delivery](" + selected["link"] + "): " + str(selected["conclusion"] or selected["status"]) + "\n")
            for row in state["modules"]:
                stream.write("\n- " + ("[" + row["repository"] + "](" + row["link"] + ")" if row["link"] else row["repository"]) + ": " + str(row["conclusion"] or "missing") + "\n")
            for message in state["errors"]:
                stream.write("\n- " + message + "\n")
    return int(bool(state["errors"]))


def main(argv=None, *, transport=None, clock=time.time, sleep=time.sleep):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("initialize", "permit", "poll", "finalize"))
    args = parser.parse_args(argv)
    environment = dict(os.environ)
    tokens = rt.sanitize()
    expected = identity(environment)
    directory = Path(environment.get("NIGHTLY_DELIVERY_DIRECTORY", str(Path(environment["NIGHTLY_DIRECTORY"]) / "delivery-wait"))).resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = directory / "report.json"
    values, code = {}, 0
    if args.operation == "initialize":
        state = initial(expected, rt.sha(environment.get("BUMP_SHA", environment.get("BUMP_CANDIDATE_SHA", ""))), clock())
        fail(state, "delivery observer initialization incomplete")
        rt.atomic(path, state)
    else:
        state = validate_state(rt.json_read(path.read_bytes()), expected)
    epoch = environment.get("NIGHTLY_MINT_EPOCH", "")
    budget = rt.Budget(state["started"], job_seconds=JOB_SECONDS, token_epoch=float(epoch) if epoch else None,
                       deadline=state["deadline"], clock=clock)
    transport = transport or rt.Transport(budget)
    transport.budget = transport.api.budget = budget
    transport.api.repositories = frozenset((rt.CICD, *state["repositories"]))
    persist = lambda: rt.atomic(path, state)
    try:
        if environment.get("NIGHTLY_CANCELLED") == "true" and args.operation != "finalize":
            raise rt.NightlyError("nightly cancelled; new observer operations suppressed")
        if args.operation == "initialize":
            if environment.get("BUMP_PUSH_RESULT") != "pushed":
                raise rt.NightlyError("delivery wait requires an explicitly confirmed bump push")
            bind_creation(state, transport.api, environment)
            authorize(state, transport, directory)
            state["errors"].remove("delivery observer initialization incomplete")
            values = {"active": "true", "repositories": ",".join((rt.CICD, *state["repositories"]))}
        elif args.operation == "permit":
            active = ("delivery observer initialization incomplete" not in state["errors"] and not finished(state)
                      and clock() + 120 < state["deadline"] and budget.remaining() > 120)
            values = {"active": "true" if active else "false", "mint_epoch": str(clock()) if active else ""}
        elif args.operation == "poll":
            code = poll(state, transport, tokens.get("POLL_TOKEN", ""), persist, clock=clock, sleep=sleep)
        else:
            code = finalize(state, environment)
    except Exception as error:
        fail(state, args.operation + " failed: " + rt.clean(error))
        code = 1
        if args.operation == "finalize":
            state["result"] = "fail"
    persist()
    output(environment.get("GITHUB_OUTPUT"), values)
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print("nightly delivery observer failed: " + rt.clean(error), file=sys.stderr)
        raise SystemExit(2) from None
