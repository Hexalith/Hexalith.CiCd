#!/usr/bin/env python3
"""Rebuild/rerun only Architecture in the held exact build; retain the original failing lane."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

evidence = Path(__file__).resolve().parent
product = evidence.parents[4] / "references/Hexalith.ChatBot"
receipt = evidence / "product-architecture-amendment.json"
data = json.loads(receipt.read_text())
workspace = Path(data["workspace"])
root = workspace.parent / "references"
before_tree = "459a97cbfdb2708b4aa5e281c04d30b943fb5416"
log = (evidence / "product-architecture-amendment.log").open("w", buffering=1)
environment = dict(os.environ, CI="true", DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1")

def verify_lineage(directory):
    changed, count = [], 0
    for item in subprocess.check_output(["git", "ls-tree", "-r", "-z", before_tree], cwd=product).decode().split("\0"):
        if not item:
            continue
        metadata, name = item.split("\t", 1)
        mode, kind, expected = metadata.split()
        if kind != "blob":
            continue
        path = directory / name
        content = str(path.readlink()).encode() if mode == "120000" else path.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        if actual != expected:
            changed.append(name)
        count += 1
    assert changed == [data["amended_file"]], changed
    return {"before_proposal_tree": before_tree, "regular_blobs_checked": count, "changed_files": changed}

def run(command):
    log.write("$ " + " ".join(map(str, command)) + "\n")
    start = time.monotonic()
    child = subprocess.Popen(command, cwd=workspace, env=environment, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        code = child.wait(timeout=240)
    except BaseException:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        raise
    data.setdefault("commands", []).append({"command": list(map(str, command)), "exit": code, "seconds": round(time.monotonic() - start, 2)})
    log.write(f"exit={code}\n")
    assert code == 0, command

try:
    data["product_lineage"] = verify_lineage(product)
    data["built_workspace_lineage"] = verify_lineage(workspace)
    assert (product / data["amended_file"]).read_bytes() == (workspace / data["amended_file"]).read_bytes()
    host = workspace / "src/Hexalith.ChatBot.AppHost/bin/Release/net10.0/Hexalith.ChatBot.AppHost.dll"
    host_before = hashlib.sha256(host.read_bytes()).hexdigest()
    properties = ["-p:UseHexalithProjectReferences=false"]
    for name in sorted(path.name for path in root.iterdir()):
        if name not in {"Hexalith.AI.Tools", "Hexalith.PolymorphicSerializations"}:
            properties.append(f"-p:{name.replace('.', '')}Root={root / name}")
    project = "tests/Hexalith.ChatBot.Architecture.Tests/Hexalith.ChatBot.Architecture.Tests.csproj"
    run(["dotnet", "build", project, "--configuration", "Release", "--no-restore", "-warnaserror", "-m:1", "/nr:false", "-noAutoResponse", "-p:BuildProjectReferences=false", *properties])
    test_start = log.tell()
    run(["dotnet", "test", "--project", project, "--configuration", "Release", "--no-build", "--no-restore", *properties])
    log.flush()
    with (evidence / "product-architecture-amendment.log").open() as reader:
        reader.seek(test_start)
        output = reader.read()
    assert "Test run summary: Passed!" in output and "succeeded: 119" in output and "skipped: 0" in output
    assert hashlib.sha256(host.read_bytes()).hexdigest() == host_before
    data["apphost_binary_unchanged_sha256"] = host_before
    data["whole_architecture_rerun"] = {"passed": 119, "failed": 0, "skipped": 0}
    data["all_other_product_and_test_sources_unchanged"] = True
    data["original_architecture_failure_retained_in"] = "product-units-release-verification.log"
    print("Whole Architecture119 passed; only the stated test assertion changed and AppHost binary stayed unchanged.")
except BaseException as error:
    data["amendment_verification_error"] = str(error)
    raise
finally:
    receipt.write_text(json.dumps(data, indent=2) + "\n")
    log.close()
    os.kill(data["held_verifier_pid"], signal.SIGCONT)
