"""AD-6 delivery controller: initialize, one isolated module slot, finalize.

The immutable bootstrap supplies private state and invokes these operations
under python -I. No renderer, validator, YAML parser, or module code is loaded.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path
import sys
import tempfile

_SPEC = importlib.util.spec_from_file_location("_delivery_controller_runtime", Path(__file__).with_name("delivery_runtime.py"))
rt = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = rt
_SPEC.loader.exec_module(rt)


def failed(report, reason, item=None):
    reason = rt.clean(reason)
    if item is not None and reason not in item["reasons"]:
        item["reasons"].append(reason)
    if item is None and reason not in report["failures"]:
        report["failures"].append(reason)
    report["failed"] = True


def app_checks(transport, repository, token):
    """Closed AD-3 checks; do not infer compliance from generic 403/404."""
    prefix = "/repos/Hexalith/" + rt.name(repository)
    api = transport.api
    repositories = api.pages("/installation/repositories", token, field="repositories")
    if not any(isinstance(r, dict) and r.get("full_name") == "Hexalith/" + repository for r in repositories):
        raise rt.DeliveryError("App installation accessibility check failed")
    metadata = api.get(prefix, token)
    if not isinstance(metadata, dict) or metadata.get("full_name") != "Hexalith/" + repository or metadata.get("default_branch") != "main":
        raise rt.DeliveryError("App repository/main identity check failed")
    rulesets = api.pages(prefix + "/rulesets?includes_parents=true", token)
    actual = set()
    for summary in rulesets:
        if not isinstance(summary, dict) or type(summary.get("id")) is not int or summary["id"] <= 0:
            raise rt.DeliveryError("malformed ruleset inventory")
        detail = api.get(prefix + "/rulesets/" + str(summary["id"]), token)
        if not isinstance(detail, dict) or detail.get("enforcement") != "active":
            raise rt.DeliveryError("rulesets must be exactly active AD-21 rulesets")
        conditions = detail.get("conditions")
        if not isinstance(conditions, dict) or set(conditions) != {"ref_name"}:
            raise rt.DeliveryError("AD-21 ruleset conditions check failed")
        refs = conditions["ref_name"]
        if (not isinstance(refs, dict) or set(refs) != {"include", "exclude"}
                or not isinstance(refs["include"], list) or refs["exclude"] != []
                or not all(isinstance(v, str) for v in refs["include"])):
            raise rt.DeliveryError("AD-21 ruleset ref conditions check failed")
        rules = detail.get("rules")
        if (not isinstance(rules, list) or any(not isinstance(r, dict) or not isinstance(r.get("type"), str)
                or set(r) - {"type", "parameters"} or r.get("parameters", {}) != {} for r in rules)):
            raise rt.DeliveryError("AD-21 ruleset rules check failed")
        value = (detail.get("target"), tuple(sorted(set(refs["include"]))), tuple(sorted({r["type"] for r in rules})))
        if value in actual:
            raise rt.DeliveryError("duplicate AD-21 ruleset")
        actual.add(value)
    expected = {("branch", ("refs/heads/main",), ("deletion", "non_fast_forward")),
                ("tag", ("refs/tags/v*",), ("deletion", "update"))}
    if actual != expected:
        raise rt.DeliveryError("AD-21 main/v* rulesets check failed")
    # This Administration-protected read must succeed before interpreting the
    # security-updates endpoint's documented disabled=404 response.
    retention = api.get(prefix + "/actions/permissions/artifact-and-log-retention", token)
    if not isinstance(retention, dict) or type(retention.get("days")) is not int or retention["days"] != 90:
        raise rt.DeliveryError("artifact/log retention check failed: expected 90 days")
    setup = api.get(prefix + "/code-scanning/default-setup", token)
    if not isinstance(setup, dict) or setup.get("state") != "not-configured":
        raise rt.DeliveryError("code-scanning default setup check failed")
    if api.get(prefix + "/automated-security-fixes", token, absent=True) is not None:
        raise rt.DeliveryError("Dependabot security updates check failed: enabled")


def nightly(transport, token, *, now=None):
    now = now or datetime.now(timezone.utc)
    api = transport.api
    prefix = "/repos/Hexalith/Hexalith.CiCd/actions/"
    workflows = api.pages(prefix + "workflows", token, field="workflows")
    matches = [w for w in workflows if isinstance(w, dict) and w.get("path") == ".github/workflows/nightly.yml"]
    if len(matches) > 1:
        raise rt.DeliveryError("ambiguous nightly workflow inventory")
    if matches:
        identifier = matches[0].get("id")
        if type(identifier) is not int or identifier <= 0:
            raise rt.DeliveryError("invalid nightly workflow identity")
        document = api.get(prefix + f"workflows/{identifier}/runs?branch=main&per_page=1&page=1", token)
        if (not isinstance(document, dict) or type(document.get("total_count")) is not int
                or document["total_count"] < 0 or not isinstance(document.get("workflow_runs"), list)
                or len(document["workflow_runs"]) != min(document["total_count"], 1)):
            raise rt.DeliveryError("malformed nightly run history")
        runs = document["workflow_runs"]
    else:
        # A deleted workflow file must not hide retained path-matched history.
        runs = api.pages(prefix + "runs?branch=main", token, field="workflow_runs")
        if any(not isinstance(run, dict) or not isinstance(run.get("path"), str) for run in runs):
            raise rt.DeliveryError("malformed repository run history")
        runs = [r for r in runs if r["path"].split("@", 1)[0] == ".github/workflows/nightly.yml"]
    if not runs:
        return {"status": "not-activated"}
    dates = []
    for run in runs:
        if (not isinstance(run, dict) or run.get("head_branch") != "main"
                or not isinstance(run.get("path"), str)
                or run["path"].split("@", 1)[0] != ".github/workflows/nightly.yml"
                or type(run.get("id")) is not int or run["id"] <= 0):
            raise rt.DeliveryError("nightly run identity mismatch")
        dates.append((rt.timestamp(run.get("created_at")), run["id"]))
    created, identifier = max(dates)
    age = (now - created).total_seconds()
    if age < 0:
        raise rt.DeliveryError("nightly run creation time is in the future")
    return {"status": "stale" if age > 26 * 3600 else "fresh", "run_id": identifier,
            "created_at": created.isoformat(), "age_seconds": age}


def trusted_state(git, revision, repository, transport, directory):
    tag = git.blob(revision, "builds-version").decode("utf-8").strip()
    if not rt.TAG.fullmatch(tag):
        raise rt.DeliveryError("accepted Builds version is not an exact stable tag")
    builds, root = transport.builds(tag, directory)
    library = rt.load_library(root, transport.budget)
    document = library.config.load_bytes(git.blob(revision, f"rendered/{repository}.perimeter.json"),
                                         source="accepted perimeter")
    if any(entry["kind"] == "gitlink" and entry["buildsTag"] != tag for entry in document["entries"]):
        raise rt.DeliveryError("accepted perimeter/Builds tag mismatch")
    expected = library.Snapshot(library.Git(git.root), revision)
    # Preload bounded regular expected blobs before any mutation. Never read a
    # symlink render or obtain executable content from the module.
    for entry in document["entries"]:
        if entry["kind"] in {"whole", "whole-dir"}:
            prefix = f"rendered/{repository}/" + entry["path"]
            paths = [prefix] if entry["kind"] == "whole" else [p for p in expected.items if p.startswith(prefix + "/")]
            if not paths:
                raise rt.DeliveryError("accepted whole source is missing")
            for path in paths:
                git.blob(revision, path)
    return library, document, expected, builds


def advance(git, repository, candidate, token, transport):
    for _ in range(4):
        current = transport.accepted(git, repository)
        if current == candidate:
            return "unchanged", current
        if current and not git.ancestor(current, candidate):
            return "superseded", current
        if not token:
            raise rt.DeliveryError("CiCd-scoped App mint unavailable; accepted ref retained")
        code, output = transport.advance(git, repository, candidate, token)
        if not code:
            # Re-read after successful creation/update as another writer may
            # already have advanced it to a newer descendant.
            actual = transport.accepted(git, repository)
            if actual == candidate:
                return "advanced", actual
            if actual and git.ancestor(candidate, actual):
                return "superseded", actual
            raise rt.DeliveryError("accepted ref changed unexpectedly after advancement")
        if not (b"[rejected]" in output and any(value in output for value in
                (b"(fetch first)", b"(non-fast-forward)"))):
            raise rt.DeliveryError("accepted ref push failed (authentication or transport); previous ref retained")
        refreshed = transport.accepted(git, repository)
        if refreshed != current:
            continue
        raise rt.DeliveryError("accepted ref push failed; previous ref retained")
    raise rt.DeliveryError("accepted ref race retries exhausted")


def apply_module(git, repository, transport, token, root, item):
    # Private bare object store and index contain no module configuration or
    # hooks. All product files remain Git blobs throughout the transaction.
    with tempfile.TemporaryDirectory(prefix="module-", dir=root) as temporary:
        directory = Path(temporary)
        actual = rt.Git(directory / "module.git", transport.budget, index=directory / "index")
        actual.init()
        for attempt in range(4):
            transport.budget.check()
            accepted = transport.accepted(git, repository)
            item["accepted_sha"] = accepted
            if accepted is None:
                item["application"] = "no-ref"
                return
            library, document, expected, builds = trusted_state(git, accepted, repository, transport,
                                                               directory / f"builds-{attempt}")
            head = transport.module(actual, repository)
            actual.run("read-tree", head)
            engine_git = library.Git(actual.root, index_file=directory / "index")
            library.apply(document, engine_git, expected=expected, rendered_root=f"rendered/{repository}",
                          builds=library.Git(builds.root))
            remaining = library.compare(document, library.Snapshot(engine_git, "index"), expected=expected,
                                        rendered_root=f"rendered/{repository}", builds=library.Git(builds.root))
            if remaining:
                raise rt.DeliveryError("accepted perimeter recompare failed")
            tree = rt.sha(actual.run("write-tree").decode().strip())
            if tree == actual.resolve(head + "^{tree}"):
                item["application"] = "unchanged"
                return
            commit = rt.sha(actual.run("commit-tree", tree, "-p", head,
                data=f"build(cicd): apply {accepted} from Hexalith.CiCd\n".encode()).decode().strip())
            code, output = transport.push(actual, repository, commit, token)
            if not code:
                item.update(application="pushed", pushed_sha=commit)
                return
            # Retry only a genuine rejected fast-forward and an observed new
            # main. Authentication and transport failures are never retried.
            non_ff = b"[rejected]" in output and any(v in output for v in (b"(fetch first)", b"(non-fast-forward)"))
            if not non_ff:
                raise rt.DeliveryError("module push failed (authentication or transport)")
            changed = transport.module(actual, repository)
            if changed == head:
                raise rt.DeliveryError("module push rejected without a changed main")
            if attempt == 3:
                raise rt.DeliveryError("module non-fast-forward retries exhausted")
            item["retries"] += 1


def operate(operation, state_path, *, slot=None, transport=None, tokens=None, now=None):
    state = rt.read_state(state_path)
    root = Path(state["root"])
    report_path = root / "report/delivery.json"
    report = rt.read_state(report_path)
    tokens = tokens or {}
    transport = transport or rt.Transport(rt.Budget(state["started"]))
    git = rt.Git(root / "cicd.git", transport.budget)
    if operation == "initialize":
        if not tokens.get("CICD_TOKEN"):
            failed(report, "CiCd-scoped App mint unavailable; ref writes blocked")
        if report["event"] == "schedule":
            try:
                report["freshness"] = nightly(transport, tokens.get("CICD_TOKEN", ""), now=now)
                if report["freshness"]["status"] == "stale":
                    failed(report, "nightly is older than 26 hours")
            except Exception as error:
                report["freshness"] = {"status": "failed", "reason": rt.clean(error)}
                failed(report, "nightly freshness check failed: " + str(error))
        else:
            report["freshness"] = {"status": "not-scheduled"}
        state["initialized"] = True
    elif operation == "module":
        if type(slot) is not int or not 1 <= slot <= len(state["slots"]):
            raise rt.DeliveryError("invalid ordinal module slot")
        repository = rt.name(state["slots"][slot - 1])
        item = next(r for r in report["modules"] if r["repository"] == repository)
        if item["processed"]:
            raise rt.DeliveryError("module slot already processed")
        token = tokens.get("MODULE_TOKEN", "")
        try:
            transport.budget.check()
            if not token:
                raise rt.DeliveryError("module-scoped App mint unavailable")
            if state["global"] and repository in state["registry"]:
                eligible = repository in state["passing"]
                if not eligible:
                    failed(report, "anonymous module validation failed", item)
                try:
                    app_checks(transport, repository, token)
                except Exception as error:
                    failed(report, "App precondition check failed: " + str(error), item)
                    eligible = False
                if eligible:
                    try:
                        # An unusable release must leave the prior accepted ref.
                        with tempfile.TemporaryDirectory(prefix="preflight-", dir=root) as temporary:
                            trusted_state(git, state["candidate"], repository, transport, Path(temporary))
                        item["advancement"], item["accepted_sha"] = advance(git, repository, state["candidate"],
                            tokens.get("CICD_TOKEN", ""), transport)
                        if item["advancement"] == "superseded":
                            item["reasons"].append("superseded by " + item["accepted_sha"])
                    except Exception as error:
                        item["advancement"] = "failed"
                        failed(report, str(error), item)
            try:
                apply_module(git, repository, transport, token, root, item)
            except Exception as error:
                item["application"] = "failed"
                failed(report, "application failed: " + str(error), item)
        except Exception as error:
            item["application"] = "failed"
            failed(report, str(error), item)
        item["processed"] = True
        state["completed"].append(repository)
    elif operation == "finalize":
        if not state.get("initialized"):
            failed(report, "delivery initialization did not complete")
        for item in report["modules"]:
            if not item["processed"]:
                item.update(application="failed", processed=True)
                failed(report, "module slot did not complete", item)
        report["failures"] = [r for r in report["failures"] if r != "delivery did not finalize"]
        report["failed"] = bool(report["failures"] or any(r["reasons"] and any(
            not reason.startswith("superseded by ") for reason in r["reasons"]) for r in report["modules"]))
    rt.atomic(state_path, state)
    rt.atomic(report_path, report)
    return 1 if operation == "finalize" and report["failed"] else 0


def main(argv=None, *, transport=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("initialize", "module", "finalize"))
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--slot", type=int)
    args = parser.parse_args(argv)
    tokens = rt.sanitize()
    return operate(args.operation, args.state, slot=args.slot, transport=transport, tokens=tokens)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        # The immutable caller records crashes without exposing secret context.
        raise SystemExit(2) from None
