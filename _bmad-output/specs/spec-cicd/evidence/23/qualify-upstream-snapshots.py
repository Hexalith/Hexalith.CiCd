"""Qualify isolated exact EventStore snapshot inputs; run beneath run-with-temp."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument("--attempt", required=True)
parser.add_argument("--red-configuration", action="store_true")
parser.add_argument("--projects", nargs="+", default=["Server"])
parser.add_argument("--classes", nargs="+", default=["Hexalith.EventStore.Server.Tests.Configuration.FoldedSnapshotActorConfigurationTests"])
args = parser.parse_args()
assert args.attempt.replace("-", "").isalnum()
source = Path("/home/administrator/projects/hexalith/eventstore-story-23-snapshots")
evidence = Path(__file__).resolve().parent
scratch = Path(os.environ["TMPDIR"])
root = scratch / "EventStore"
record = {"attempt": args.attempt, "startedAt": time.time(), "commands": [],
          "nativeRuntimeStarted": False, "redConfigurationOnly": args.red_configuration}

def git(repository, *arguments):
    return subprocess.check_output(["git", "-C", str(repository), *arguments], text=True).strip()

def clone(repository, target, revision):
    subprocess.run(["git", "clone", "--quiet", "--local", "--shared", "--no-recurse-submodules", "--no-checkout", str(repository), str(target)], check=True)
    subprocess.run(["git", "-C", str(target), "checkout", "--quiet", "--detach", revision], check=True)

record["base"] = git(source, "rev-parse", "HEAD")
clone(source, root, record["base"])
paths = set(subprocess.check_output(["git", "-C", str(source), "diff", "--name-only", "HEAD", "-z"]).split(b"\0")
    + subprocess.check_output(["git", "-C", str(source), "ls-files", "--others", "--exclude-standard", "-z"]).split(b"\0")) - {b""}
if args.red_configuration:
    paths = {b"tests/Hexalith.EventStore.Server.Tests/Configuration/FoldedSnapshotActorConfigurationTests.cs"}
for raw in paths:
    name = os.fsdecode(raw)
    path, target = source / name, root / name
    if path.is_file() and not path.is_symlink():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    elif not path.exists() and target.is_file():
        target.unlink()
subprocess.run(["git", "-C", str(root), "-c", "core.safecrlf=false", "add", "-A"], check=True)
record["candidateTree"] = git(root, "write-tree")
record["changedPaths"] = git(root, "diff", "--cached", "--name-only", "HEAD").splitlines()
record["normalizedInputs"] = {line.split("\t", 1)[1]: line.split()[1] for line in git(root, "ls-files", "--stage").splitlines()}
patch = subprocess.check_output(["git", "-C", str(root), "diff", "--cached", "--binary", "--no-ext-diff", "HEAD"])
(evidence / ("upstream-snapshot-" + args.attempt + ".patch")).open("xb").write(patch)
record["patchSha256"] = hashlib.sha256(patch).hexdigest()
subprocess.run(["git", "-C", str(root), "-c", "core.autocrlf=false", "checkout-index", "--force", "--all"], check=True)
manifest = {name: {"sha256": hashlib.sha256((source / name).read_bytes()).hexdigest(), "mode": oct((source / name).stat().st_mode & 0o777)}
            for name in record["normalizedInputs"] if (source / name).is_file() and not (source / name).is_symlink()}
(evidence / ("upstream-snapshot-manifest-" + args.attempt + ".json")).open("x").write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
pin = git(source, "rev-parse", "HEAD:references/Hexalith.Builds")
clone(Path("/home/administrator/projects/hexalith/eventstore/references/Hexalith.Builds"), root / "references/Hexalith.Builds", pin)
record["materializedDirectDependencies"] = {"Hexalith.Builds": pin}
environment = {**os.environ, "HOME": str(scratch / "home"), "DOTNET_CLI_HOME": str(scratch / "dotnet-home"),
    "NUGET_PACKAGES": str(scratch / "packages"), "XDG_CONFIG_HOME": str(scratch / "xdg-config"),
    "XDG_CACHE_HOME": str(scratch / "xdg-cache"), "XDG_DATA_HOME": str(scratch / "xdg-data"),
    "DOTNET_NOLOGO": "1", "DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER": "1", "DOTNET_CLI_USE_MSBUILD_SERVER": "0",
    "MSBUILDDISABLENODEREUSE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
for name in ("HOME", "DOTNET_CLI_HOME", "NUGET_PACKAGES", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"):
    Path(environment[name]).mkdir(parents=True, exist_ok=True)
record["sdk"] = subprocess.check_output(["dotnet", "--version"], cwd=root, env=environment, text=True).strip()
flags = ["-noAutoResponse", "-p:Configuration=Release", "-warnaserror", "-p:UseHexalithProjectReferences=false", "-p:UseNuGetDeps=true",
    "-p:EnableNETAnalyzers=true", "-p:RunAnalyzers=true", "-p:RunAnalyzersDuringBuild=true", "-p:UseSharedCompilation=false", "-nr:false", "-m:1",
    "-p:RestoreConfigFile=" + str(root / "references/Hexalith.Builds/NuGet.ci.Config")]

def run(arguments, timeout=600):
    print("RUN", json.dumps(arguments), flush=True)
    started = time.monotonic()
    result = subprocess.run(arguments, cwd=root, env=environment, timeout=timeout, check=False)
    item = {"arguments": arguments, "exitCode": result.returncode, "elapsedSeconds": time.monotonic() - started}
    record["commands"].append(item)
    print("RESULT", json.dumps(item), flush=True)
    return result.returncode

result = 0
try:
    for project in args.projects:
        target = f"tests/Hexalith.EventStore.{project}.Tests/Hexalith.EventStore.{project}.Tests.csproj"
        result = run(["dotnet", "restore", target, "--disable-build-servers", *flags])
        if result: break
        result = run(["dotnet", "build", target, "--no-restore", "--disable-build-servers", *flags])
        if result: break
        selected = [name for name in args.classes if name.startswith("Hexalith.EventStore." + project + ".Tests.")]
        for index, name in enumerate(selected):
            directory = scratch / (project + "-" + str(index))
            arguments = ["dotnet", "test", "--project", target, "--configuration", "Release", "--no-build", "--no-restore",
                "--filter-class", name, "--minimum-expected-tests", "47" if name.endswith("FoldedSnapshotActorConfigurationTests") else "20" if name.endswith("FoldedAggregateCaptureTests") else "1",
                "--fail-skips", "on", "--report-xunit-trx", "--report-xunit-trx-filename", "results.trx", "--results-directory", str(directory)]
            code = run(arguments)
            reports = list(directory.rglob("*.trx"))
            if len(reports) != 1: raise ValueError("One complete focused TRX is required.")
            report = ET.parse(reports[0])
            record.setdefault("suites", {})[name] = {"counters": report.find(".//{*}Counters").attrib,
                "cases": [{"name": case.get("testName"), "outcome": case.get("outcome")} for case in report.findall(".//{*}UnitTestResult")]}
            shutil.copyfile(reports[0], evidence / ("upstream-snapshot-" + args.attempt + "-" + project + "-" + str(index) + ".trx"))
            result = code or result
except BaseException as error:
    result = 1
    record["jobFailure"] = type(error).__name__
    raise
finally:
    record["exitCode"] = result
    record["finishedAt"] = time.time()
    (evidence / ("upstream-snapshot-" + args.attempt + ".json")).open("x").write(json.dumps(record, indent=2) + "\n")
raise SystemExit(result)
