"""Immutable stdlib selector and failure reporter for delivery.

This file and its sibling runtime are checked out at a literal source SHA.
It never imports scripts from the candidate. Selected scripts execute only in
isolated child Python processes, after ancestry and verdict selection.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time

_SPEC = importlib.util.spec_from_file_location("_delivery_bootstrap_runtime", Path(__file__).with_name("delivery_runtime.py"))
rt = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = rt
_SPEC.loader.exec_module(rt)


def report_path(root):
    return root / "report/delivery.json"


def failure(report, reason):
    reason = rt.clean(reason)
    if reason not in report["failures"]:
        report["failures"].append(reason)
    report["failed"] = True


def row(repository):
    return {"repository": repository, "accepted_sha": None, "advancement": "skipped",
            "application": "no-ref", "pushed_sha": None, "retries": 0, "reasons": [], "processed": False}


def verdict(raw):
    value = rt.json_read(raw)
    if (not isinstance(value, dict) or set(value) != {"global", "modules"}
            or type(value["global"]) is not bool or not isinstance(value["modules"], list)
            or len(value["modules"]) > rt.CAPACITY):
        raise rt.DeliveryError("malformed validation verdict")
    names = [rt.name(item) for item in value["modules"]]
    if names != sorted(set(names)) or len({n.casefold() for n in names}) != len(names):
        raise rt.DeliveryError("malformed validation module names")
    return value


def emit(outputs, path):
    if path:
        with open(path, "a", encoding="utf-8") as stream:
            for key, value in outputs.items():
                stream.write(key + "=" + value + "\n")


def select(root, context, *, transport=None):
    # Initialize the artifact before Git, verdict parsing, or source discovery.
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    report = {"schema": "hexalith.delivery.v1", "run_id": context.get("GITHUB_RUN_ID", ""),
              "run_attempt": context.get("GITHUB_RUN_ATTEMPT", ""), "event": context.get("GITHUB_EVENT_NAME", ""),
              "candidate_sha": context.get("GITHUB_SHA", ""), "tools_source_sha": None,
              "global": False, "failed": True, "failures": ["delivery did not finalize"],
              "freshness": {"status": "not-checked"}, "modules": []}
    rt.atomic(report_path(root), report)
    state = {"version": 1, "root": str(root), "started": time.monotonic(), "ready": False,
             "candidate": context.get("GITHUB_SHA", ""), "global": False, "passing": [], "registry": [],
             "source": None, "slots": [], "completed": [], "initialized": False}
    outputs = {"ready": "false", "checks": "false"} | {f"slot_{i:02}": "" for i in range(1, rt.CAPACITY + 1)}
    outputs.update({f"check_{i:02}": "false" for i in range(1, rt.CAPACITY + 1)})
    try:
        if context.get("GITHUB_REPOSITORY") != "Hexalith/Hexalith.CiCd" or context.get("GITHUB_REF") != "refs/heads/main":
            raise rt.DeliveryError("ineligible delivery repository/ref")
        candidate = rt.sha(state["candidate"])
        budget = rt.Budget(state["started"])
        transport = transport or rt.Transport(budget)
        git = rt.Git(root / "cicd.git", budget)
        git.init()
        transport.cicd(git)
        main = git.resolve("refs/heads/main^{commit}")
        if git.resolve(candidate + "^{commit}") != candidate or not git.ancestor(candidate, main):
            raise rt.DeliveryError("candidate is not ancestral to live CiCd main")
        try:
            value = verdict(context.get("DELIVERY_VERDICT", ""))
            state["global"] = report["global"] = value["global"]
            state["passing"] = value["modules"]
        except rt.DeliveryError as error:
            failure(report, "validation verdict unavailable or malformed: " + str(error))
        if not state["global"]:
            failure(report, "global validation failed")
        refs, valid, seen = {}, {}, set()
        for line in git.run("for-each-ref", "--format=%(refname) %(objectname)", "refs/heads/delivered/").decode().splitlines():
            ref, target = line.split(" ", 1)
            repository = ref.removeprefix("refs/heads/delivered/")
            item = row(repository)
            refs[repository] = item
            try:
                rt.name(repository)
                if repository.casefold() in seen:
                    raise rt.DeliveryError("case-colliding accepted ref")
                seen.add(repository.casefold())
                target = rt.sha(target)
                if git.resolve(target + "^{commit}") != target or not git.ancestor(target, main):
                    raise rt.DeliveryError("accepted ref is not ancestral to current CiCd main: " + target)
                item["accepted_sha"] = target
                valid[repository] = target
            except (rt.DeliveryError, ValueError) as error:
                item.update(advancement="failed", application="failed", processed=True)
                item["reasons"].append(rt.clean(error))
                failure(report, "invalid accepted ref " + repository + ": " + str(error))
        report["modules"] = [refs[key] for key in sorted(refs)]
        rt.atomic(report_path(root), report)
        source = candidate if state["global"] else next(
            (revision for revision in git.run("rev-list", "--topo-order", "refs/heads/main").decode().splitlines()
             if revision in set(valid.values())), None)
        if source is None:
            raise rt.DeliveryError("no valid accepted tools source; zero writes")
        report["tools_source_sha"] = state["source"] = source
        registry = rt.registry(git, source)
        state["registry"] = registry
        if state["global"] and not set(state["passing"]).issubset(registry):
            raise rt.DeliveryError("validation names outside committed candidate registry")
        # Existing refs are authoritative repair targets even after setup removal.
        targets = sorted(set(valid) | set(registry))
        if len(targets) > rt.CAPACITY or len({value.casefold() for value in targets}) != len(targets):
            raise rt.DeliveryError("delivery ref/registry union exceeds 17 slots or collides; zero writes")
        for repository in targets:
            if repository not in refs:
                refs[repository] = row(repository)
        report["modules"] = [refs[key] for key in sorted(refs)]
        # Export only regular trusted tools blobs; reject missing controller
        # rather than trying the rejected candidate as a fallback.
        for required in ("tools/deliver.py", "tools/delivery_runtime.py"):
            git.blob(source, required)
        git.export(source, "tools", root / "selected")
        state["slots"] = targets
        state["ready"] = True
        outputs.update(ready="true", checks="true" if state["global"] else "false")
        outputs.update({f"slot_{i:02}": value for i, value in enumerate(targets, 1)})
        outputs.update({f"check_{i:02}": "true" if state["global"] and value in registry else "false"
                        for i, value in enumerate(targets, 1)})
    except Exception as error:
        # Do not emit traceback, remote bodies, paths or arbitrary exception text.
        failure(report, str(error) if isinstance(error, rt.DeliveryError) else "delivery source setup failed: " + type(error).__name__)
    rt.atomic(root / "state.json", state)
    rt.atomic(report_path(root), report)
    emit(outputs, context.get("GITHUB_OUTPUT"))
    return 0


def invoke(root, operation, slot=None, *, context=None):
    context = os.environ if context is None else context
    try:
        state = rt.read_state(root / "state.json")
        if not state.get("ready"):
            if operation == "finalize":
                return fallback(root, "trusted controller unavailable")
            return 0
        rt.Budget(state["started"]).check()
        command = [sys.executable, "-I", str(root / "selected/tools/deliver.py"), operation,
                   "--state", str(root / "state.json")]
        if slot is not None:
            command.extend(("--slot", str(slot)))
        env = rt.environment()
        env.update({key: context.get(key, "") for key in ("CICD_TOKEN", "MODULE_TOKEN")})
        # Child diagnostics are deliberately not relayed: a failed operation has
        # a bounded report or this immutable fallback, never an unsanitized log.
        result = subprocess.run(command, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                timeout=rt.Budget(state["started"]).timeout() if operation != "module" else
                                min(600, max(1, 36 * 60 - (time.monotonic() - state["started"]))))
        if result.returncode and operation != "finalize":
            return fallback(root, "selected controller failed: " + operation, slot=slot, final=False)
        if operation == "finalize":
            # An early exit cannot leave a provisional success artifact.
            report = rt.read_state(report_path(root))
            if "delivery did not finalize" in report.get("failures", []) or any(not r.get("processed") for r in report.get("modules", [])):
                return fallback(root, "selected controller did not finalize")
            return 1 if report.get("failed") or result.returncode else 0
        return 0
    except Exception as error:
        return fallback(root, "delivery operation unavailable: " + operation, slot=slot, final=operation == "finalize")


def fallback(root, reason, *, slot=None, final=True):
    try:
        report = rt.read_state(report_path(root))
        if (not isinstance(report.get("failures"), list) or not isinstance(report.get("modules"), list)
                or any(not isinstance(r, dict) or not isinstance(r.get("reasons"), list) for r in report["modules"])):
            raise rt.DeliveryError("malformed report")
    except Exception:
        report = {"schema": "hexalith.delivery.v1", "run_id": "", "run_attempt": "", "event": "",
                  "candidate_sha": None, "tools_source_sha": None, "global": False,
                  "failed": True, "failures": [], "freshness": {"status": "not-checked"}, "modules": []}
    failure(report, reason)
    repository = None
    if slot is not None:
        try:
            repository = rt.read_state(root / "state.json")["slots"][slot - 1]
        except Exception:
            pass
    for item in report.get("modules", []):
        if not item.get("processed") and (final or repository == item.get("repository")):
            item.update(application="failed", processed=True)
            item["reasons"].append(rt.clean(reason))
    if final:
        report["failures"] = [r for r in report["failures"] if r != "delivery did not finalize"]
    rt.atomic(report_path(root), report)
    return 1 if final else 0


def main(argv=None, *, transport=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("select", "permit", "initialize", "module", "finalize"))
    parser.add_argument("--slot", type=int)
    args = parser.parse_args(argv)
    context = os.environ.copy()
    rt.sanitize()
    root = Path(context["DELIVERY_DIRECTORY"]).resolve()
    if args.operation == "select":
        return select(root, context, transport=transport)
    if args.operation == "permit":
        active = "false"
        try:
            state = rt.read_state(root / "state.json")
            budget = rt.Budget(state["started"])
            budget.check()
            if (state.get("ready") and type(args.slot) is int and 1 <= args.slot <= len(state["slots"])
                    and budget.clock() - budget.started < 35 * 60):
                active = "true"
        except Exception:
            pass
        emit({"active": active}, context.get("GITHUB_OUTPUT"))
        return 0
    return invoke(root, args.operation, args.slot, context=context)


if __name__ == "__main__":
    raise SystemExit(main())
