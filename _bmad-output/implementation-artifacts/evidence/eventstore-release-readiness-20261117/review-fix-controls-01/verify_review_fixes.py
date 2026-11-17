#!/usr/bin/env python3
"""Focused custody and synthetic C# layout controls; no producer/package runs."""

import argparse
import ast
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
from unittest.mock import patch

import verification_core as core


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    packet = Path(__file__).resolve().parent
    scratch = Path(os.environ["TMPDIR"]).resolve()
    core.require(os.environ.get("TMP") == str(scratch) == os.environ.get("TEMP"), "Use run-with-temp")
    output = args.output.resolve()
    core.require(output != scratch and scratch not in output.parents, "Retain results outside scratch")
    output.mkdir(parents=True, exist_ok=False)
    for name in ("verification_core.py", "query_package_probe.py", "verify_review_fixes.py"):
        shutil.copy2(packet / name, output / name)
    checks, receipts = {}, {}
    complete = False

    def check(name, condition):
        checks[name] = bool(condition)
        core.require(condition, name)

    def run(name, command, bound=None):
        with (output / (name + ".log")).open("wb") as stream:
            try:
                receipt = core.owned_run(command, scratch, os.environ.copy(), stream, bound)
            except core.JobInterrupted as error:
                receipts[name] = error.receipt
                raise
        receipts[name] = receipt
        return receipt

    def wait_path(path):
        deadline = time.monotonic() + 3
        while not path.exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        core.require(path.exists(), f"Fixture did not become ready: {path.name}")

    def alive(pid):
        return Path(f"/proc/{pid}").exists()

    def escaped_command(path, stay):
        # The grandchild execs with an empty environment after both forks and
        # setsid. No observer needs to catch the transient ancestry links.
        sleeper = "import os,time;from pathlib import Path;Path(" + repr(str(path)) + ").write_text(str(os.getpid()));time.sleep(60)"
        source = ("import os,sys,time\n"
                  "child=os.fork()\n"
                  "if child:\n    " + ("time.sleep(60)" if stay else "os._exit(0)") + "\n"
                  "else:\n"
                  "    os.setsid()\n"
                  "    if os.fork(): os._exit(0)\n"
                  "    os.execve(sys.executable,[sys.executable,'-c'," + repr(sleeper) + "],{})\n")
        return [sys.executable, "-c", source]

    def forbid_environment_reads(event, arguments):
        if event == "open" and isinstance(arguments[0], (str, bytes, os.PathLike)):
            name = os.fsdecode(arguments[0])
            if name.startswith("/proc/") and name.endswith("/environ"):
                raise RuntimeError("Process environments must never be read")

    sys.addaudithook(forbid_environment_reads)
    foreign = None
    foreign_pid = None
    try:
        child_path = scratch / "foreign-child.pid"
        foreign_child = "import os,time;from pathlib import Path;Path(" + repr(str(child_path)) + ").write_text(str(os.getpid()));time.sleep(60)"
        foreign_source = ("import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," +
                          repr(foreign_child) + "],env={},start_new_session=True);time.sleep(60)")
        foreign = subprocess.Popen([sys.executable, "-c", foreign_source], start_new_session=True)
        wait_path(child_path)
        foreign_pid = int(child_path.read_text())
        success = run("native-success", [sys.executable, "-c", "raise SystemExit(0)"])
        failure = run("native-failure", [sys.executable, "-c", "raise SystemExit(7)"], 5)
        check("native-zero-preserved", success["native_exit"] == 0 and success["timeout_seconds"] is None)
        check("native-seven-and-bound-preserved", failure["native_exit"] == 7 and failure["timeout_seconds"] == 5)
        # Hold the first post-spawn observation until the fast double fork and
        # empty-environment exec have finished. Adoption alone must retain it.
        ready = scratch / "fast-cleared.pid"
        original_processes = core._processes
        observations = 0

        def delayed_first_observation():
            nonlocal observations
            observations += 1
            if observations == 2:
                wait_path(ready)
            return original_processes()

        with patch.object(core, "_processes", delayed_first_observation):
            escaped = run("fast-double-fork-cleared-environment", escaped_command(ready, False))
        escaped_pid = int(ready.read_text())
        check("fast-cleared-descendant-adopted", escaped_pid in escaped["owned_pids"])
        check("fast-cleared-descendant-reaped", escaped["native_exit"] == 0 and
              escaped["process_tree_fully_waited"] and not alive(escaped_pid))
        ready = scratch / "timeout-cleared.pid"
        timeout = run("timeout-cleared-environment", escaped_command(ready, True), 0.3)
        wait_path(ready)
        check("timeout-and-bound-preserved", timeout["timed_out"] and timeout["timeout_seconds"] == 0.3 and
              timeout["native_exit"] == -signal.SIGTERM)
        check("timeout-cleared-descendant-reaped", int(ready.read_text()) in timeout["owned_pids"] and
              timeout["process_tree_fully_waited"] and not alive(int(ready.read_text())))
        original_popen = subprocess.Popen
        for signum in (signal.SIGINT, signal.SIGTERM):
            for stage in ("before-child", "after-child"):
                def cancel_startup(*arguments, **keywords):
                    if stage == "before-child":
                        os.kill(os.getpid(), signum)
                    process = original_popen(*arguments, **keywords)
                    if stage == "after-child":
                        os.kill(os.getpid(), signum)
                    return process

                name = f"startup-{signum}-{stage}"
                with patch.object(core.subprocess, "Popen", cancel_startup):
                    try:
                        run(name, [sys.executable, "-c", "import time;time.sleep(60)"])
                        raise RuntimeError("Startup cancellation was ignored")
                    except core.JobInterrupted as error:
                        check(name, error.receipt["cancelled"] and error.receipt["process_started"] and
                              error.receipt["cancellation_signal"] == signum and
                              error.receipt["process_tree_fully_waited"] and
                              not any(alive(pid) for pid in error.receipt["owned_pids"]))
        original_signal = signal.signal
        injected = False

        def cancel_during_handler_setup(signum, handler):
            nonlocal injected
            previous = original_signal(signum, handler)
            if signum == signal.SIGTERM and callable(handler) and not injected:
                injected = True
                os.kill(os.getpid(), signal.SIGINT)
            return previous

        with patch.object(core.signal, "signal", cancel_during_handler_setup):
            try:
                run("handler-setup-cancellation", [sys.executable, "-c", "raise SystemExit(0)"])
                raise RuntimeError("Handler setup cancellation was ignored")
            except core.JobInterrupted as error:
                check("handler-setup-cancellation-starts-no-child", not error.receipt["process_started"] and
                      error.receipt["native_exit"] is None and error.receipt["process_tree_fully_waited"])
        for signum in (signal.SIGINT, signal.SIGTERM):
            ready = scratch / f"cancel-cleared-{signum}.pid"
            timer = threading.Timer(0.3, os.kill, args=(os.getpid(), signum))
            timer.start()
            try:
                run(f"cancel-cleared-environment-{signum}", escaped_command(ready, True))
                raise RuntimeError("Cancellation was ignored")
            except core.JobInterrupted as error:
                wait_path(ready)
                pid = int(ready.read_text())
                check(f"cancel-cleared-descendant-{signum}", pid in error.receipt["owned_pids"] and
                      error.receipt["process_tree_fully_waited"] and not alive(pid))
            finally:
                timer.join()
        check("foreign-child-and-descendant-survive", foreign.poll() is None and alive(foreign_pid) and
              all(foreign.pid not in receipt["owned_pids"] and foreign_pid not in receipt["owned_pids"]
                  for receipt in receipts.values()))
        # Extract only the two C# file literals. No packing or producer checks
        # are needed for this one-object-per-file layout correction.
        module = ast.parse((packet / "query_package_probe.py").read_text())
        files = {}
        for node in ast.walk(module):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                    node.func.attr == "write_text" and isinstance(node.func.value, ast.BinOp) and
                    isinstance(node.func.value.right, ast.Constant) and
                    node.func.value.right.value in {"Query.cs", "Result.cs"}):
                files[node.func.value.right.value] = ast.literal_eval(node.args[0])
        original = (packet / "attempt-05-query-api-packages/synthetic-consumer-inputs/Owner.Contracts/Query.cs").read_text()
        check("query-layout-only-unchanged-binding", files["Query.cs"] == original.replace("public sealed record Result(string OpaqueId);\n", ""))
        check("result-layout-only-unchanged-type", files["Result.cs"] == "namespace Owner;\npublic sealed record Result(string OpaqueId);\n")
        check("one-csharp-object-per-file", all(text.count("public sealed record ") == 1 for text in files.values()))
        check("no-environment-inspection", "/environ" not in (packet / "verification_core.py").read_text())
        complete = True
        return 0
    finally:
        if foreign is not None:
            foreign.terminate()
            foreign.wait(timeout=5)
        if foreign_pid is not None and alive(foreign_pid):
            os.kill(foreign_pid, signal.SIGTERM)
            os.waitpid(foreign_pid, 0)
        result = {"completed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                  "invocation": "run-with-temp python3 -O -B " + str(Path(__file__).resolve()) + " --output " + str(output),
                  "python_optimization": sys.flags.optimize, "scratch": str(scratch),
                  "scope": "owned-job lifecycle and C# source layout only; no producer/package runs",
                  "source_sha256": {name: core.digest(output / name) for name in
                                    ("verification_core.py", "query_package_probe.py", "verify_review_fixes.py")},
                  "checks": checks, "lifecycle_receipts": receipts,
                  "passed": complete and bool(checks) and all(checks.values()), "complete_release_acceptance": False}
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"checks": len(checks), "passed": result["passed"], "output": str(output)}))


if __name__ == "__main__":
    sys.exit(main())
