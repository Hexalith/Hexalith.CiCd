#!/usr/bin/env python3
"""Replay immutable evidence and exercise boundary controls without producer tests.

Run: run-with-temp python3 -O -B <packet>/audit_evidence.py --output <fresh-directory>
"""

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import threading

from verification_core import (TYPED_CASES, JobInterrupted, clean_environment, digest,
                               owned_run, require, suite_complete, suite_passed, trx_inventory,
                               sanitized_source, repository_unchanged)
from verify import validate_properties, SOURCE, BUILDS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    packet = Path(__file__).resolve().parent
    scratch = Path(os.environ["TMPDIR"]).resolve()
    require(os.environ.get("TMP") == str(scratch) == os.environ.get("TEMP"), "Use run-with-temp")
    output = args.output.resolve()
    require(output != scratch and scratch not in output.parents, "Retain evidence outside scratch")
    output.mkdir(parents=True, exist_ok=False)
    for filename in ("audit_evidence.py", "verify.py", "verification_core.py", "frozen-suite-inventories.json"):
        shutil.copy2(packet / filename, output / filename)
    checks = {}
    receipts = {}
    evidence = {}
    completed = False

    def check(name, value):
        checks[name] = bool(value)
        require(value, name)

    def run(name, command, env=None, bound=None):
        with (output / (name + ".log")).open("wb") as stream:
            result = owned_run(command, scratch, env or os.environ.copy(), stream, bound)
        receipts[name] = result
        return result

    try:
        frozen = json.loads((packet / "frozen-suite-inventories.json").read_text())["suites"]
        historical_integrity = json.loads((packet / "integrity.json").read_text())["attempts"]
        for name in ("attempt-01", "attempt-02-local-packages", "attempt-03-local-packages", "attempt-04-authority"):
            directory = packet / name
            result = json.loads((directory / "result.json").read_text())
            check(name + "-original-result-unchanged", digest(directory / "result.json") ==
                  historical_integrity[name]["result_sha256"])
            check(name + "-frozen-identities", result["source"] == SOURCE and result["builds"] == BUILDS)
            check(name + "-helper-hash", digest(directory / "verify.py") == result["helper_sha256"])
            for record in result["commands"]:
                check(name + "-log-" + record["name"], digest(directory / record["log"]) == record["log_sha256"])
            for relative, record in result["inputs"].items():
                path = directory / "committed-inputs" / relative
                raw = path.read_bytes()
                blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
                check(name + "-input-" + relative, digest(path) == record["sha256"] and blob == record["blob"])
            check(name + "-scratch-removed", not Path(result["scratch"]).exists())
            evidence[name] = {"result_sha256": digest(directory / "result.json"),
                              "resolved_external_graph": "unavailable; historical scratch was removed; not reconstructed",
                              "custody_boundary": "original receipt retained; strengthened custody controls apply to new jobs"}
        for name in ("attempt-05-query-api-packages", "public-api-recheck-02"):
            directory = packet / name
            result = json.loads((directory / "result.json").read_text())
            check(name + "-helper-snapshot", digest(directory / ("verify.py" if name.startswith("attempt-") else
                  "inspect_public_api.py")) == result["helper_sha256"])
            for filename, expected in result.get("supporting_sha256", {}).items():
                check(name + "-supporting-" + filename, digest(directory / filename) == expected)
            for record in result["commands"]:
                check(name + "-log-" + record["name"], digest(directory / record["log"]) == record["log_sha256"])
                check(name + "-custody-" + record["name"], record["process_tree_fully_waited"] and
                      not record["remaining_owned_after_cleanup"])
            check(name + "-scratch-removed", not Path(result["scratch"]).exists())
            if name.startswith("attempt-"):
                check(name + "-query-boundary-passed", result["query_api_package_probe"]["passed"])
                binding = result["query_api_package_probe"]["generated_binding"]
                check(name + "-generated-binding-hash", digest(directory / binding["path"]) == binding["sha256"])
                for dependency in result["dependencies"].values():
                    check(name + "-final-" + dependency["commit"], dependency["tracked_source_unchanged"] and
                          dependency["final_head_matches_recorded_commit"] and
                          dependency["final_head"] == dependency["commit"])
                graph = result["resolved_package_graphs"]
                check(name + "-graph-hash", digest(directory / graph["path"]) == graph["sha256"] and graph["project_count"] >= 2)
            else:
                check(name + "-public-api-controls", result["passed"] and len(result["packages"]) == 2 and
                      all(item["known_present_control"]["present"] and item["missing_type"]["absent"]
                          for item in result["packages"]))
            evidence[name] = {"result_sha256": digest(directory / "result.json"), "passed": True}
        original = json.loads((packet / "attempt-01/result.json").read_text())
        summaries = {}
        for name in frozen:
            report = trx_inventory(packet / f"attempt-01/test-results/{name}/{name}.trx")
            summary = {"native_exit": original["test_results"][name]["native_exit"], "reports": [report]}
            summaries[name] = summary
            check(name + "-complete-frozen-inventory", suite_complete(summary, frozen[name]))
        check("generators-real-203-pass", suite_passed(summaries["generators"], frozen["generators"]))
        check("contracts-original-exit-2-remains-failed", summaries["contracts"]["native_exit"] == 2 and
              not suite_passed(summaries["contracts"], frozen["contracts"]))
        check("contracts-original-1805-two-fail-two-skip", summaries["contracts"]["reports"][0]["counters"] |
              {} == original["test_results"]["contracts"]["reports"][0]["counters"])
        for label, mutate in {
            "internally-consistent-202": lambda item: (item["reports"][0]["counters"].update(total="202", passed="202", executed="202"),
                                                       item["reports"][0].update(result_rows=202)),
            "missing-name": lambda item: item["reports"][0]["names"].pop(),
            "substituted-name": lambda item: item["reports"][0]["names"].__setitem__(0, "Foreign.Test"),
            "missing-required-case": lambda item: item["reports"][0]["typed_query_compilation_tests"].pop(),
            "failed-required-case": lambda item: item["reports"][0]["typed_query_compilation_tests"][0].update(outcome="Failed"),
            "native-failure": lambda item: item.update(native_exit=7),
            "no-report": lambda item: item.update(reports=[]),
        }.items():
            altered = copy.deepcopy(summaries["generators"])
            mutate(altered)
            check("reject-" + label, not suite_passed(altered, frozen["generators"]))
        properties = {"Configuration": "Release", "UseHexalithProjectReferences": "false", "UseNuGetDeps": "true",
                      "NuGetAudit": "true", "NuGetAuditMode": "all", "NuGetAuditLevel": "low",
                      "TreatWarningsAsErrors": "true", "EnableNETAnalyzers": "true",
                      "RunAnalyzers": "", "RunAnalyzersDuringBuild": "", "_SkipAnalyzers": "", "_ImplicitlySkipAnalyzers": ""}
        check("valid-audit-analyzers-policy", not validate_properties(properties))
        for key in properties:
            altered = dict(properties, **{key: "invalid"})
            check("reject-policy-" + key, bool(validate_properties(altered)))
        sentinel = scratch / "sentinel-index"
        sentinel.write_bytes(b"isolated sentinel, never a real index")
        before = digest(sentinel)
        poisoned = dict(os.environ, GIT_DIR=str(scratch / "foreign.git"), GIT_INDEX_FILE=str(sentinel),
                        GIT_OBJECT_DIRECTORY=str(scratch / "foreign-objects"),
                        EVENTSTORE_PACKAGE_CONTRACT_DIR=str(scratch / "foreign-packages"),
                        GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.worktree", GIT_CONFIG_VALUE_0="foreign")
        clean, removed = clean_environment(poisoned)
        check("selectors-quarantined", all(key not in clean for key in (
            "GIT_DIR", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "EVENTSTORE_PACKAGE_CONTRACT_DIR",
            "GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0")))
        check("credential-profile-preserved", all(clean.get(key) == poisoned.get(key)
              for key in ("GH_CONFIG_DIR", "GH_TOKEN", "GITHUB_TOKEN", "GIT_SSH_COMMAND")))
        init = run("sentinel-git-init", ["git", "init", "--initial-branch=main", str(scratch / "repository")], clean)
        check("sentinel-repository-init", init["native_exit"] == 0)
        read = run("sentinel-git-identity", ["git", "-C", str(scratch / "repository"), "rev-parse", "--git-path", "index"], clean)
        check("sentinel-repository-selected", read["native_exit"] == 0 and
              (output / "sentinel-git-identity.log").read_text().strip() == ".git/index")
        check("sentinel-index-unmodified", digest(sentinel) == before)
        record = run("package-selector-unset", [sys.executable, "-c",
                     "import os;raise SystemExit(0 if 'EVENTSTORE_PACKAGE_CONTRACT_DIR' not in os.environ else 1)"], clean)
        check("baseline-package-selector-unset", record["native_exit"] == 0)
        check("source-url-sanitized", sanitized_source("https://user:password@example.com/feed?token=secret#fragment") ==
              "https://example.com/feed")
        success = run("native-success", [sys.executable, "-c", "raise SystemExit(0)"])
        failure = run("native-failure", [sys.executable, "-c", "raise SystemExit(7)"])
        check("success-native-exit", success["native_exit"] == 0)
        check("failure-native-exit-preserved", failure["native_exit"] == 7)
        child = "import os,time;os.setsid();time.sleep(60)"
        parent = "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child) + "]);time.sleep(60)"
        timeout = run("session-escape-timeout", [sys.executable, "-c", parent], bound=0.3)
        check("timeout-session-escape-reaped", timeout["timed_out"] and timeout["process_tree_fully_waited"] and
              len(timeout["owned_pids"]) >= 2 and timeout["remaining_owned_after_cleanup"] == [])
        detached = "import subprocess,sys;subprocess.Popen([sys.executable,'-c'," + repr(child) + "])"
        escaped = run("session-escape-success", [sys.executable, "-c", detached])
        check("native-zero-escaped-descendant-reaped", escaped["native_exit"] == 0 and
              len(escaped["owned_pids"]) >= 2 and escaped["process_tree_fully_waited"])
        foreign = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(60)"], start_new_session=True)
        try:
            timer = threading.Timer(0.3, os.kill, args=(os.getpid(), signal.SIGINT))
            timer.start()
            try:
                run("sigint-session-escape", [sys.executable, "-c", parent])
                raise RuntimeError("SIGINT control did not interrupt")
            except JobInterrupted as error:
                receipts["sigint-session-escape"] = error.receipt
                check("sigint-cleanup-reaped", error.receipt["cancelled"] and
                      error.receipt["process_tree_fully_waited"] and len(error.receipt["owned_pids"]) >= 2)
            finally:
                timer.join()
            check("foreign-process-survived", foreign.poll() is None and
                  all(foreign.pid not in record.get("owned_pids", []) for record in receipts.values()))
            timer = threading.Timer(0.3, os.kill, args=(os.getpid(), signal.SIGTERM))
            timer.start()
            try:
                run("sigterm-session-escape", [sys.executable, "-c", parent])
                raise RuntimeError("SIGTERM control did not interrupt")
            except JobInterrupted as error:
                receipts["sigterm-session-escape"] = error.receipt
                check("sigterm-cleanup-reaped", error.receipt["cancelled"] and
                      error.receipt["cancellation_signal"] == signal.SIGTERM and
                      error.receipt["process_tree_fully_waited"] and len(error.receipt["owned_pids"]) >= 2)
            finally:
                timer.join()
            check("foreign-process-survived-term", foreign.poll() is None and
                  foreign.pid not in receipts["sigterm-session-escape"]["owned_pids"])
        finally:
            foreign.terminate()
            foreign.wait(timeout=5)
        check("authority-bound-remains-480", "timeout_seconds=480" in (packet / "verify.py").read_text())
        # Real isolated checkouts reproduce the clean-changed-HEAD false pass.
        checkout = scratch / "identity-repository"
        store = packet.parents[3] / "references/Hexalith.EventStore"
        cloned = run("identity-clone", ["git", "-c", "submodule.recurse=false", "clone", "--no-checkout",
                     "--no-hardlinks", str(store), str(checkout)], clean)
        check("identity-isolated-clone", cloned["native_exit"] == 0)
        checked = run("identity-frozen-checkout", ["git", "-C", str(checkout), "checkout", "--detach", SOURCE], clean)
        same = run("identity-frozen-diff", ["git", "-C", str(checkout), "diff", "--exit-code", SOURCE, "--"], clean)
        check("accept-frozen-clean-checkout", checked["native_exit"] == 0 and
              repository_unchanged(SOURCE, SOURCE, same["native_exit"]))
        moved = run("identity-moved-checkout", ["git", "-C", str(checkout), "checkout", "--detach", SOURCE + "^"], clean)
        head = run("identity-moved-head", ["git", "-C", str(checkout), "rev-parse", "HEAD"], clean)
        against_head = run("identity-moved-clean-head-diff", ["git", "-C", str(checkout), "diff", "--exit-code", "HEAD", "--"], clean)
        against_recorded = run("identity-moved-recorded-diff", ["git", "-C", str(checkout), "diff", "--exit-code", SOURCE, "--"], clean)
        final_head = (output / "identity-moved-head.log").read_text().strip()
        check("reject-clean-changed-final-head", moved["native_exit"] == 0 and head["native_exit"] == 0 and
              against_head["native_exit"] == 0 and final_head != SOURCE and
              not repository_unchanged(SOURCE, final_head, against_head["native_exit"]))
        check("frozen-diff-detects-change", against_recorded["native_exit"] == 1 and
              not repository_unchanged(SOURCE, final_head, against_recorded["native_exit"]))
        check("reject-dirty-frozen-head", not repository_unchanged(SOURCE, SOURCE, 1))
        check("reject-nested-initialization", not repository_unchanged(SOURCE, SOURCE, 0, ["foreign"]))
        completed = True
        return 0
    finally:
        result = {"completed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                  "invocation": "run-with-temp python3 -O -B " + str(Path(__file__).resolve()) + " --output " + str(output),
                  "python_optimization": sys.flags.optimize,
                  "helper_sha256": digest(packet / "verify.py"),
                  "core_sha256": digest(packet / "verification_core.py"),
                  "verifier_sha256": digest(Path(__file__).resolve()),
                  "evidence": evidence, "checks": checks, "lifecycle_receipts": receipts,
                  "passed": completed and bool(checks) and all(checks.values()), "complete_release_acceptance": False}
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"checks": len(checks), "passed": result["passed"], "output": str(output)}))


if __name__ == "__main__":
    sys.exit(main())
