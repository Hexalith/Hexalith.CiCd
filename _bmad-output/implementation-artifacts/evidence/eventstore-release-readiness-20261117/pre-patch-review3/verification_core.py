"""Internal, Linux-only input and owned-job boundaries for readiness evidence."""

import ctypes
import hashlib
import json
import os
from pathlib import Path
import signal
import select
import sys
import traceback
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
    "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM", "GIT_TEMPLATE_DIR",
    "MSBuildSDKsPath", "MSBUILD_EXE_PATH", "MSBuildExtensionsPath",
    "MSBuildUserExtensionsPath", "DirectoryBuildPropsPath", "DirectoryBuildTargetsPath",
    "DirectoryPackagesPropsPath", "CustomBeforeMicrosoftCommonProps",
    "CustomAfterMicrosoftCommonProps", "CustomBeforeMicrosoftCommonTargets",
    "CustomAfterMicrosoftCommonTargets", "NuGetAudit", "NuGetAuditMode", "NuGetAuditLevel",
    "NoWarn", "WarningsNotAsErrors", "TreatWarningsAsErrors", "EnableNETAnalyzers",
    "RunAnalyzers", "RunAnalyzersDuringBuild", "UseNuGetDeps", "UseHexalithProjectReferences",
    "WarningsAsErrors", "WarningsAsMessages", "BaseIntermediateOutputPath", "IntermediateOutputPath",
    "BaseOutputPath", "OutputPath", "MSBuildProjectExtensionsPath", "RestoreSources",
    "RestoreAdditionalProjectSources", "RestoreConfigFile", "RestorePackagesPath",
    "ImportDirectoryBuildProps", "ImportDirectoryBuildTargets", "ImportDirectoryPackagesProps",
    "EnableDefaultCompileItems", "BuildProjectReferences", "NUGET_RESTORE_MSBUILD_ARGS",
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
    selector_names = {name.casefold() for name in SELECTORS}
    removed = sorted(name for name in inherited if name.casefold() in selector_names or
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


def _custodian(command, cwd, env, stream, bound, control_fd):
    """Only this fresh process is a subreaper; every child here belongs to its job."""
    libc = ctypes.CDLL(None, use_errno=True)
    require(libc.prctl(36, 1, 0, 0, 0) == 0, "Cannot enable dedicated subreaper")
    supervisor = os.getpid()
    process = None
    owned = {}
    cancelled = None
    timed_out = False
    started = time.monotonic()
    receipt = {"custody": "dedicated per-job subreaper; isolated descendant adoption",
               "custodian_pid": supervisor, "timeout_seconds": bound}

    def collect():
        table = _processes()
        # No unrelated tree can be adopted by this process: it was created
        # solely for this job, never forks anything else, and never shares its
        # subreaper role with the calling helper or other jobs.
        for pid, (parent, ticks, _) in table.items():
            if parent == supervisor:
                owned[pid] = ticks
        changed = True
        while changed:
            changed = False
            for pid, (parent, ticks, _) in table.items():
                if pid not in owned and parent in owned and table.get(parent, (None, None))[1] == owned[parent]:
                    owned[pid] = ticks
                    changed = True
        return {pid: row for pid, row in table.items() if owned.get(pid) == row[1]}

    def reap():
        if process is not None:
            process.poll()
        for pid, (parent, _, _) in collect().items():
            if parent == supervisor and (process is None or pid != process.pid):
                try:
                    os.waitpid(pid, os.WNOHANG)
                except ChildProcessError:
                    pass

    def signal_owned(signum):
        for pid in collect():
            try:
                os.kill(pid, signum)
            except ProcessLookupError:
                pass

    def cancellation():
        nonlocal cancelled
        if select.select([control_fd], [], [], 0)[0]:
            raw = os.read(control_fd, 64)
            cancelled = raw[-1] if raw else signal.SIGTERM
        return cancelled

    try:
        # Defer signals sent to the invoking process group. The private pipe
        # carries cancellation; job processes start in their own session.
        signal.signal(signal.SIGINT, lambda *_: None)
        signal.signal(signal.SIGTERM, lambda *_: None)
        if not cancellation():
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=stream,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            collect()
        while process is not None:
            collect()
            if cancellation() or process.poll() is not None:
                break
            if bound is not None and time.monotonic() - started >= bound:
                timed_out = True
                break
            time.sleep(0.01)
    except BaseException as error:
        receipt.update(lifecycle_error=repr(error), lifecycle_traceback=traceback.format_exc())
    finally:
        try:
            before = sorted(collect())
            signal_owned(signal.SIGTERM)
            deadline = time.monotonic() + 2
            while collect() and time.monotonic() < deadline:
                reap()
                time.sleep(0.01)
            deadline = time.monotonic() + 10
            while collect() and time.monotonic() < deadline:
                signal_owned(signal.SIGKILL)
                reap()
                time.sleep(0.01)
            reap()
            remaining = sorted(collect())
            receipt.update(native_exit=process.returncode if process else None,
                           process_started=process is not None, timed_out=timed_out,
                           cancelled=cancelled is not None, cancellation_signal=cancelled,
                           owned_pids=sorted(owned), remaining_owned_before_cleanup=before,
                           remaining_owned_after_cleanup=remaining,
                           process_tree_fully_waited=not remaining and
                           (process is None or process.returncode is not None))
        except BaseException as error:
            receipt.update(cleanup_error=repr(error), process_tree_fully_waited=False)
    return receipt


def owned_run(command, cwd, env, stream, bound=None):
    """Run one job below its own custodian; never adopt or scan caller children.

    Only the custodian enables subreaping, scans ownership and reaps descendants.
    The caller waits for that exact PID and receives a receipt over private IPC.
    No environment contents or IPC payloads are saved in evidence.
    """
    handlers = {}
    cancellation_signal = None
    custodian_pid = None
    control_read, control_write = os.pipe()
    receipt_read, receipt_write = os.pipe()
    receipt = {"custody": "dedicated per-job subreaper; isolated descendant adoption",
               "timeout_seconds": bound, "native_exit": None, "process_started": False,
               "owned_pids": [], "remaining_owned_after_cleanup": [],
               "process_tree_fully_waited": False, "timed_out": False}

    def requested(signum, _frame):
        nonlocal cancellation_signal
        cancellation_signal = signum

    payload = bytearray()
    waited = False
    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, requested)
        if cancellation_signal is None:
            custodian_pid = os.fork()
            if custodian_pid == 0:
                os.close(control_write)
                os.close(receipt_read)
                try:
                    child_receipt = _custodian(command, cwd, env, stream, bound, control_read)
                    raw = json.dumps(child_receipt).encode()
                    while raw:
                        count = os.write(receipt_write, raw)
                        raw = raw[count:]
                except BaseException:
                    os._exit(70)
                os._exit(0)
            os.close(control_read)
            os.close(receipt_write)
            control_read = receipt_write = None
            sent = None
            while True:
                if cancellation_signal is not None and sent != cancellation_signal:
                    try:
                        os.write(control_write, bytes([cancellation_signal]))
                    except BrokenPipeError:
                        pass
                    sent = cancellation_signal
                if select.select([receipt_read], [], [], 0.02)[0]:
                    block = os.read(receipt_read, 65536)
                    if not block:
                        break
                    payload.extend(block)
            _, status = os.waitpid(custodian_pid, 0)
            waited = True
            require(os.waitstatus_to_exitcode(status) == 0, "Job custodian exited without complete receipt")
            receipt.update(json.loads(payload))
        else:
            receipt["process_tree_fully_waited"] = True
    except BaseException as error:
        # Save lifecycle failure and still wait for the dedicated custodian.
        receipt["parent_lifecycle_error"] = repr(error)
    finally:
        for signum in handlers:
            signal.signal(signum, signal.SIG_IGN)
        try:
            if custodian_pid and not waited:
                try:
                    os.write(control_write, bytes([cancellation_signal or signal.SIGTERM]))
                except (BrokenPipeError, OSError):
                    pass
                # The custodian's cleanup has its own bounded finalization.
                while True:
                    block = os.read(receipt_read, 65536)
                    if not block:
                        break
                    payload.extend(block)
                _, status = os.waitpid(custodian_pid, 0)
                waited = True
                if payload:
                    receipt.update(json.loads(payload))
            if cancellation_signal is not None:
                receipt.update(cancelled=True, cancellation_signal=cancellation_signal)
            receipt["custodian_waited"] = custodian_pid is None or waited
        finally:
            for fd in (control_read, control_write, receipt_read, receipt_write):
                if fd is not None:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
            for signum, handler in handlers.items():
                signal.signal(signum, handler)
    if (not receipt["process_tree_fully_waited"] or not receipt["custodian_waited"] or
            any(key in receipt for key in ("lifecycle_error", "cleanup_error", "parent_lifecycle_error"))):
        raise JobCleanupError(receipt)
    if receipt.get("cancelled"):
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


def capture_graphs(root, output, active_assets=()):
    """Capture only evaluated active paths, with compact hashes and sanitized sources."""
    graphs = []
    for item in active_assets:
        path = Path(item["assets_path"]).resolve()
        require(path.is_relative_to(root.resolve()), "Active assets must remain in private scratch")
        data = json.loads(path.read_text())
        restore = data.get("project", {}).get("restore", {})
        project_path = Path(item["project_path"]).resolve()
        require(Path(restore["projectPath"]).resolve() == project_path,
                "Active assets do not belong to the evaluated project")
        record = {"path": str(path.relative_to(root)), "project_path": str(project_path.relative_to(root)),
                  "evaluation_command": item["evaluation_command"], "assets_sha256": digest(path),
                  "libraries": {key: {name: value[name] for name in ("type", "sha512", "path") if name in value}
                                for key, value in sorted(data.get("libraries", {}).items())},
                  "sources": sorted(sanitized_source(source) for source in restore.get("sources", {})),
                  "config_files": [str(Path(value)) for value in restore.get("configFilePaths", [])]}
        graphs.append(record)
    target = output / "resolved-package-graphs.json"
    target.write_text(json.dumps(graphs, indent=2) + "\n")
    return {"path": target.name, "sha256": digest(target), "project_count": len(graphs),
            "selection": "explicit evaluated active ProjectAssetsFile paths only"}


def file_manifest(root):
    return {str(path.relative_to(root)): digest(path) for path in sorted(root.rglob("*")) if path.is_file()}


def verify_manifest(root, manifest):
    return file_manifest(root) == manifest


def unexpected_inputs(root, tracked, output_directories=(), dependency_directories=()):
    """Reject ignored and untracked inputs too; only designated outputs are exempt."""
    allowed = {str(Path(value)) for value in tracked}
    outputs = tuple(Path(value) for value in (*output_directories, *dependency_directories))
    unexpected = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative.parts[0] == ".git" or any(relative == out or relative.is_relative_to(out) for out in outputs):
            continue
        if (path.is_file() or path.is_symlink()) and str(relative) not in allowed:
            unexpected.append(str(relative))
    return sorted(unexpected)
