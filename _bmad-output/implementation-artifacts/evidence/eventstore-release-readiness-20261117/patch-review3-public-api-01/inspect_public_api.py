#!/usr/bin/env python3
"""Read-only, pinned-tool inspection of the two retained public SDK versions."""

import argparse
import datetime as dt
import json
import hashlib
import traceback
import os
from pathlib import Path
import shutil
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

from verification_core import clean_environment, digest, owned_run, require, capture_restore_policy, verify_restore_policy

from artifact_resolver import resolve_artifact, ARTIFACT_ROOT

TOOL_VERSION = "0.28.0"
RID_SHA256 = "f72e538944c654759c5db922ef8749d897dd3a0af3072d9ac5d43c3b8319cfa3"
TOOL_SHA256 = "5614b4e044974ca002b883274a5dc29d569fe16c0ef356f6ad41025b3e4ab650"
PACKAGES = {
    "5.1.1": "38d1e13eea64437584f2718f3aceb1345e76e2ae16dd048f94a392d7dc63f357",
    "5.2.0": "2b0ca2eebe215ec7dcc98163a61b575199b1f0354deac0da88a6ad7f1d84a324",
}
MISSING = "Hexalith.EventStore.Contracts.Queries.QueryResultContractAttribute"
PRESENT = "Hexalith.EventStore.Contracts.Queries.SubmitQueryRequest"


def execute(result, output, scratch, env, name, command):
    """Register before execution; preserve interrupted/failed cleanup receipts."""
    log = output / (name + ".log")
    record = {"name": name, "command": [str(part) for part in command], "log": log.name}
    result["commands"].append(record)
    save = lambda: (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    save()
    try:
        with log.open("wb") as stream:
            record.update(owned_run(command, scratch, env, stream))
    except BaseException as error:
        record.update(getattr(error, "receipt", {}))
        record["lifecycle_exception"] = repr(error)
        raise
    finally:
        record["log_sha256"] = digest(log)
        save()
    return record["native_exit"], log.read_text()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    scratch = Path(os.environ["TMPDIR"]).resolve()
    require(os.environ.get("TMP") == str(scratch) == os.environ.get("TEMP"), "Use run-with-temp")
    output = args.output.resolve()
    require(output != scratch and scratch not in output.parents, "Retain evidence outside scratch")
    output.mkdir(parents=True, exist_ok=False)
    for filename in ("inspect_public_api.py", "verification_core.py", "artifact_resolver.py"):
        shutil.copy2(Path(__file__).resolve().parent / filename, output / filename)
    env, removed = clean_environment(os.environ)
    env.update(NUGET_PACKAGES=str(scratch / "packages"), NUGET_HTTP_CACHE_PATH=str(scratch / "http-cache"),
               DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1", MSBUILDDISABLENODEREUSE="1")
    result = {"started_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "commands": [],
              "tool": {"id": "dotnet-inspect", "version": TOOL_VERSION}, "packages": [],
              "quarantined_selector_names": removed, "scratch": str(scratch),
              "helper_sha256": digest(Path(__file__).resolve()), "original_inspection_logs_unchanged": True,
              "complete_release_acceptance": False, "passed": False}

    def run(name, command):
        return execute(result, output, scratch, env, name, command)

    def fetch(package, version):
        name = f"{package.lower()}.{version}.nupkg"
        url = f"https://api.nuget.org/v3-flatcontainer/{package.lower()}/{version}/{name}"
        path = scratch / name
        with urllib.request.urlopen(url, timeout=30) as response:
            path.write_bytes(response.read())
        return path, url

    try:
        local_feed = scratch / "inspector-feed"
        local_feed.mkdir()
        tool_url = f"https://api.nuget.org/v3-flatcontainer/dotnet-inspect/{TOOL_VERSION}/dotnet-inspect.{TOOL_VERSION}.nupkg"
        tool_metadata = {"filename":f"dotnet-inspect.{TOOL_VERSION}.nupkg", "url":tool_url,
                         "sha256":TOOL_SHA256,"local_path":str(ARTIFACT_ROOT/f"dotnet-inspect.{TOOL_VERSION}.nupkg")}
        tool_archive = resolve_artifact(tool_metadata, scratch)
        require(digest(tool_archive) == TOOL_SHA256, "Downloaded inspector differs from the pinned archive")
        captured = tool_archive
        shutil.copy2(tool_archive, local_feed / tool_metadata["filename"])
        rid_url = f"https://api.nuget.org/v3-flatcontainer/dotnet-inspect.linux-x64/{TOOL_VERSION}/dotnet-inspect.linux-x64.{TOOL_VERSION}.nupkg"
        rid_metadata = {"filename":f"dotnet-inspect.linux-x64.{TOOL_VERSION}.nupkg", "url":rid_url,
                        "sha256":RID_SHA256,"local_path":str(ARTIFACT_ROOT/f"dotnet-inspect.linux-x64.{TOOL_VERSION}.nupkg")}
        rid_archive = resolve_artifact(rid_metadata, scratch)
        require(digest(rid_archive) == RID_SHA256, "RID payload differs from pinned archive")
        rid_captured = rid_archive
        shutil.copy2(rid_archive, local_feed / rid_metadata["filename"])
        result["tool"]["runtime_archive"] = {"id": "dotnet-inspect.linux-x64", "version": TOOL_VERSION,
            "url": rid_url, "path": rid_metadata["filename"], "sha256": digest(rid_captured), "artifact":rid_metadata}
        config = scratch / "NuGet.Config"
        config.write_text(f'''<configuration><packageSources><clear />
<add key="captured-local-archive" value="{local_feed}" />
</packageSources></configuration>''')
        shutil.copy2(config, output / "inspector-NuGet.Config")
        result["tool"].update(url=tool_url, nupkg_sha256=digest(tool_archive),
                              archive=tool_metadata["filename"], archive_artifact=tool_metadata, installation_source="captured archive in isolated local-only feed")
        result["restore_policy"] = capture_restore_policy([config], output, "inspector-install")
        code, _ = run("install-pinned-inspector", ["dotnet", "tool", "install", "dotnet-inspect",
            "--version", TOOL_VERSION, "--tool-path", str(scratch / "inspector"), "--configfile", str(config)])
        require(code == 0, "Pinned inspector installation failed")
        verify_restore_policy(result["restore_policy"], output)
        payload = {}
        entrypoints = []
        with zipfile.ZipFile(rid_captured) as opened:
            for name in opened.namelist():
                if not name.startswith("tools/") or name.endswith("/"):
                    continue
                matches = [path for path in (scratch / "inspector").rglob(Path(name).name)
                           if path.is_file() and path.as_posix().endswith("/" + name)]
                require(len(matches) == 1, f"Installed payload missing/ambiguous: {name}")
                expected = hashlib.sha256(opened.read(name)).hexdigest()
                require(digest(matches[0]) == expected, f"Installed payload differs from captured archive: {name}")
                payload[name] = {"sha256": expected, "installed_relative_path": str(matches[0].relative_to(scratch / "inspector"))}
                if name.endswith("DotnetToolSettings.xml"):
                    settings = ET.fromstring(opened.read(name))
                    entry = settings.find("Commands/Command")
                    require(entry is not None, "Tool entry point missing")
                    entrypoints.append(matches[0].parent / entry.get("EntryPoint"))
        require(len(entrypoints) == 1, "Expected one pinned inspector entry point")
        executable = entrypoints[0]
        result["tool"].update(installed_payload=payload,
            executed_payload={"relative_path": str(executable.relative_to(scratch / "inspector")), "sha256": digest(executable)},
            command_prefix=[str(executable)])
        code, version_text = run("inspector-version", [str(executable), "--version"])
        require(code == 0 and TOOL_VERSION in version_text, "Inspector version identity mismatch")
        result["tool"]["reported_version"] = version_text.strip()
        for version, expected in PACKAGES.items():
            archive, url = fetch("Hexalith.EventStore.Contracts", version)
            require(digest(archive) == expected, f"Public archive changed from retained proof: {version}")
            with zipfile.ZipFile(archive) as opened:
                nuspec_name = next(name for name in opened.namelist() if name.endswith(".nuspec"))
                nuspec = opened.read(nuspec_name)
                metadata = ET.fromstring(nuspec)
                repository = next(item for item in metadata.iter() if item.tag.rsplit("}", 1)[-1] == "repository")
                (output / f"contracts-{version}.nuspec").write_bytes(nuspec)
            absent, absent_text = run(f"contracts-{version}-missing-query-result", [str(executable),
                "type", MISSING, "--package", str(archive), "--plaintext"])
            present, present_text = run(f"contracts-{version}-known-present-submit-query", [str(executable),
                "type", PRESENT, "--package", str(archive), "--plaintext"])
            require(absent == 1 and "not found" in absent_text.lower(), "Absence was not a native type-not-found result")
            require(present == 0 and "SubmitQueryRequest" in present_text, "Known-present metadata control failed")
            result["packages"].append({"version": version, "url": url, "sha256": digest(archive),
                "source_commit": repository.get("commit"),
                "missing_type": {"name": MISSING, "native_exit": absent, "absent": True},
                "known_present_control": {"name": PRESENT, "native_exit": present, "present": True}})
        verify_restore_policy(result["restore_policy"], output)
        result["supporting_sha256"] = {filename:digest(output/filename) for filename in ("verification_core.py","artifact_resolver.py")}
        result["retained_manifest"] = {str(path.relative_to(output)): digest(path) for path in output.rglob("*")
            if path.is_file() and path.name not in {"result.json", "helper-error.log"}}
        result["passed"] = True
        return 0
    except BaseException as error:
        result["fatal_error"] = repr(error)
        result["primary_error_type"] = type(error).__name__
        (output / "helper-error.log").write_text(traceback.format_exc())
        raise
    finally:
        result["completed_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"passed": result["passed"], "output": str(output)}))


if __name__ == "__main__":
    sys.exit(main())
