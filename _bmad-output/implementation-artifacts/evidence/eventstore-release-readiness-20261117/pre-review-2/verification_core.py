"""Internal, Linux-only input and owned-job boundaries for readiness evidence."""

import ctypes
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from urllib.parse import urlsplit, urlunsplit
import xml.etree.ElementTree as ET


SELECTORS = {
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE",
    "GIT_PREFIX", "GIT_SHALLOW_FILE", "GIT_GRAFT_FILE", "GIT_REPLACE_REF_BASE",
    "GIT_IMPLICIT_WORK_TREE", "GIT_CEILING_DIRECTORIES", "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_CONFIG", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS",
    "EVENTSTORE_PACKAGE_CONTRACT_DIR", "HEXALITH_BUILDS_SOURCE",
}
TYPED_CASES = {
    "Hexalith.EventStore.RestApi.Generators.Tests.TypedGatewayQueryGenerationTests."
    "ReferencedContractsExportTypedBindingsWithoutRestEnrollment",
    "Hexalith.EventStore.RestApi.Generators.Tests.TypedGatewayQueryGenerationTests."
    "TypedComputedQueryCompilesWithoutCreatingOrChangingRestRoutes",
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean_environment(inherited):
    removed = sorted(name for name in inherited if name in SELECTORS or
                     name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")))
    env = {name: value for name, value in inherited.items() if name not in removed}
    env.update(GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    return env, removed


def _processes():
    table = {}
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
                table[int(entry.name)] = (int(fields[1]), fields[19], fields[0])
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                pass
    return table


class JobInterrupted(KeyboardInterrupt):
    def __init__(self, receipt):
        super().__init__("Owned job interrupted after cleanup")
        self.receipt = receipt


class JobCleanupError(RuntimeError):
    def __init__(self, receipt):
        super().__init__(f"Owned descendant cleanup failed: {receipt}")
        self.receipt = receipt


def owned_run(command, cwd, env, stream, bound=None):
    """Track job ancestry and newly adopted children, without reading environments.

    Existing child trees are excluded by PID/start ticks before creation. The
    subreaper owns new orphaned descendants even after setsid, double fork or
    exec with an empty environment. Only owned identities are signalled/waited.
    Signal handlers defer cancellation until Popen returns its child identity.
    """
    libc = ctypes.CDLL(None, use_errno=True)
    require(libc.prctl(36, 1, 0, 0, 0) == 0, "Cannot enable child-subreaper custody")
    supervisor = os.getpid()
    process = None
    owned = {}
    foreign = {}
    prior_handlers = {}
    spawn_attempted = False
    interrupted = False
    timed_out = False
    cancellation_signal = None
    start = time.monotonic()
    receipt = {"timeout_seconds": bound, "timed_out": False, "cancelled": False,
               "custody": "subreaper, owned ancestry, newly adopted child identities and PID start ticks"}

    def extend_tree(identities, table):
        changed = True
        while changed:
            changed = False
            for pid, (parent, ticks, _) in table.items():
                if pid not in identities and parent in identities and table.get(parent, (None, None))[1] == identities[parent]:
                    identities[pid] = ticks
                    changed = True

    def collect():
        table = _processes()
        extend_tree(foreign, table)
        if process is not None and process.pid in table and process.pid not in owned:
            owned[process.pid] = table[process.pid][1]
        if spawn_attempted:
            for pid, (parent, ticks, _) in table.items():
                if parent == supervisor and foreign.get(pid) != ticks:
                    owned[pid] = ticks
        extend_tree(owned, table)
        return {pid: table[pid] for pid, ticks in owned.items()
                if pid in table and table[pid][1] == ticks}

    def signal_owned(sig):
        for pid in collect():
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass

    def reap():
        if process is not None:
            process.poll()
        for pid in list(owned):
            if process is not None and pid == process.pid:
                continue
            try:
                os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                pass

    def terminate_requested(signum, _frame):
        nonlocal cancellation_signal
        cancellation_signal = signum

    try:
        # Handler setup and creation are covered by cleanup. Handlers record
        # signals rather than raising between Popen's fork and its return.
        for signum in (signal.SIGINT, signal.SIGTERM):
            prior_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, terminate_requested)
        baseline = _processes()
        foreign.update({pid: ticks for pid, (parent, ticks, _) in baseline.items() if parent == supervisor})
        extend_tree(foreign, baseline)
        if cancellation_signal is None:
            spawn_attempted = True
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream,
                                       stderr=subprocess.STDOUT, start_new_session=True)
        while process is not None:
            collect()
            if cancellation_signal is not None:
                interrupted = True
                break
            if process.poll() is not None:
                break
            if bound is not None and time.monotonic() - start >= bound:
                timed_out = True
                break
            time.sleep(0.025)
        interrupted = interrupted or cancellation_signal is not None
    except KeyboardInterrupt:
        interrupted = True
        cancellation_signal = cancellation_signal or signal.SIGINT
    finally:
        # Repeated SIGINT must not interrupt the final cleanup/reap phase.
        for signum in prior_handlers:
            signal.signal(signum, signal.SIG_IGN)
        try:
            before = sorted(collect())
            signal_owned(signal.SIGTERM)
            deadline = time.monotonic() + 2
            while collect() and time.monotonic() < deadline:
                reap()
                time.sleep(0.025)
            if collect():
                signal_owned(signal.SIGKILL)
            deadline = time.monotonic() + 10
            while collect() and time.monotonic() < deadline:
                reap()
                signal_owned(signal.SIGKILL)
                time.sleep(0.025)
            reap()
            remaining = sorted(collect())
            receipt.update(native_exit=process.returncode if process is not None else None,
                           process_started=process is not None, timed_out=timed_out,
                           cancelled=interrupted, cancellation_signal=cancellation_signal,
                           owned_pids=sorted(owned),
                           remaining_owned_before_cleanup=before,
                           remaining_owned_after_cleanup=remaining,
                           process_tree_fully_waited=not remaining and
                           (process is None or process.returncode is not None))
        finally:
            for signum, handler in prior_handlers.items():
                signal.signal(signum, handler)
    if not receipt["process_tree_fully_waited"]:
        raise JobCleanupError(receipt)
    if interrupted:
        raise JobInterrupted(receipt)
    return receipt


def trx_inventory(path):
    ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
    root = ET.parse(path).getroot()
    rows = root.findall("t:Results/t:UnitTestResult", ns)
    counters = root.find("t:ResultSummary/t:Counters", ns)
    names = sorted(item.get("testName", "") for item in rows)
    return {"sha256": digest(path), "names": names,
            "inventory_sha256": hashlib.sha256(json.dumps(names, separators=(",", ":")).encode()).hexdigest(),
            "counters": counters.attrib if counters is not None else {},
            "result_rows": len(rows),
            "nonpassing": [dict(item.attrib) | {"detail": "".join(item.itertext()).strip()}
                           for item in rows if item.get("outcome") != "Passed"],
            "typed_query_compilation_tests": [dict(item.attrib) for item in rows
                                              if item.get("testName") in TYPED_CASES]}


def suite_complete(summary, frozen):
    reports = summary.get("reports", [])
    if len(reports) != 1:
        return False
    report = reports[0]
    try:
        return (int(report["counters"]["total"]) == frozen["result_rows"] and
                report["result_rows"] == frozen["result_rows"] and
                report["inventory_sha256"] == frozen["inventory_sha256"] and
                report["names"] == frozen["names"] and
                (not frozen.get("required_cases") or
                 {case["testName"] for case in report["typed_query_compilation_tests"]
                  if case.get("outcome") == "Passed"} == set(frozen["required_cases"])))
    except (KeyError, TypeError, ValueError):
        return False


def suite_passed(summary, frozen):
    if summary.get("native_exit") != 0 or not suite_complete(summary, frozen):
        return False
    report = summary["reports"][0]
    try:
        total = int(report["counters"]["total"])
        return (int(report["counters"]["passed"]) == total == int(report["counters"]["executed"]) and
                not report["nonpassing"] and all(int(value) == 0 for name, value in report["counters"].items()
                if name not in {"total", "passed", "executed", "completed"}))
    except (KeyError, TypeError, ValueError):
        return False


def repository_unchanged(recorded, final_head, diff_exit, initialized=()):
    return final_head == recorded and diff_exit == 0 and not initialized


def sanitized_source(value):
    parsed = urlsplit(value)
    if parsed.scheme and parsed.netloc:
        host = parsed.hostname or ""
        if parsed.port:
            host += ":" + str(parsed.port)
        return urlunsplit((parsed.scheme, host, parsed.path, "", ""))
    return value


def capture_graphs(root, output):
    """Keep compact resolved library identities and hashes, never credentials."""
    graphs = []
    for path in sorted(root.rglob("project.assets.json")):
        # Do not traverse .git object content or any unrelated shared location.
        data = json.loads(path.read_text())
        restore = data.get("project", {}).get("restore", {})
        record = {"path": str(path.relative_to(root)), "assets_sha256": digest(path),
                  "libraries": {key: {name: item[name] for name in ("type", "sha512", "path") if name in item}
                                for key, item in sorted(data.get("libraries", {}).items())},
                  "sources": sorted(sanitized_source(source) for source in restore.get("sources", {})),
                  "config_files": restore.get("configFilePaths", [])}
        graphs.append(record)
    target = output / "resolved-package-graphs.json"
    target.write_text(json.dumps(graphs, indent=2) + "\n")
    return {"path": target.name, "sha256": digest(target), "project_count": len(graphs)}
