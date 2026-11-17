#!/usr/bin/env python3
"""Read-only, pinned-tool inspection of the two retained public SDK versions."""

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

from verification_core import clean_environment, digest, owned_run, require

TOOL_VERSION = "0.28.0"
PACKAGES = {
    "5.1.1": "38d1e13eea64437584f2718f3aceb1345e76e2ae16dd048f94a392d7dc63f357",
    "5.2.0": "2b0ca2eebe215ec7dcc98163a61b575199b1f0354deac0da88a6ad7f1d84a324",
}
MISSING = "Hexalith.EventStore.Contracts.Queries.QueryResultContractAttribute"
PRESENT = "Hexalith.EventStore.Contracts.Queries.SubmitQueryRequest"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    scratch = Path(os.environ["TMPDIR"]).resolve()
    require(os.environ.get("TMP") == str(scratch) == os.environ.get("TEMP"), "Use run-with-temp")
    output = args.output.resolve()
    require(output != scratch and scratch not in output.parents, "Retain evidence outside scratch")
    output.mkdir(parents=True, exist_ok=False)
    for filename in ("inspect_public_api.py", "verification_core.py"):
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
        log = output / (name + ".log")
        with log.open("wb") as stream:
            receipt = owned_run(command, scratch, env, stream)
        result["commands"].append({"name": name, "command": [str(part) for part in command],
                                   "log": log.name, "log_sha256": digest(log), **receipt})
        return receipt["native_exit"], log.read_text()

    def fetch(package, version):
        name = f"{package.lower()}.{version}.nupkg"
        url = f"https://api.nuget.org/v3-flatcontainer/{package.lower()}/{version}/{name}"
        path = scratch / name
        with urllib.request.urlopen(url, timeout=30) as response:
            path.write_bytes(response.read())
        return path, url

    try:
        config = scratch / "NuGet.Config"
        config.write_text('''<configuration><packageSources><clear />
<add key="nuget.org" value="https://api.nuget.org/v3/index.json" />
</packageSources></configuration>''')
        tool_archive, tool_url = fetch("dotnet-inspect", TOOL_VERSION)
        result["tool"].update(url=tool_url, nupkg_sha256=digest(tool_archive))
        code, _ = run("install-pinned-inspector", ["dotnet", "tool", "install", "dotnet-inspect",
            "--version", TOOL_VERSION, "--tool-path", str(scratch / "inspector"), "--configfile", str(config)])
        require(code == 0, "Pinned inspector installation failed")
        executable = scratch / "inspector/dotnet-inspect"
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
                "type", MISSING, "--package", str(archive), "--oneline"])
            present, present_text = run(f"contracts-{version}-known-present-submit-query", [str(executable),
                "type", PRESENT, "--package", str(archive), "--oneline"])
            require(absent == 1 and "not found" in absent_text.lower(), "Absence was not a native type-not-found result")
            require(present == 0 and "SubmitQueryRequest" in present_text, "Known-present metadata control failed")
            result["packages"].append({"version": version, "url": url, "sha256": digest(archive),
                "source_commit": repository.get("commit"),
                "missing_type": {"name": MISSING, "native_exit": absent, "absent": True},
                "known_present_control": {"name": PRESENT, "native_exit": present, "present": True}})
        result["passed"] = True
        return 0
    finally:
        result["completed_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"passed": result["passed"], "output": str(output)}))


if __name__ == "__main__":
    sys.exit(main())
