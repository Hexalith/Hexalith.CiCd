"""Refresh only disposable inputs, then run the complete approved product proof."""
from pathlib import Path
import hashlib
import json
import os
import runpy
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SCRATCH = Path(os.environ["TMPDIR"])
MODULE = SCRATCH / "Hexalith.Projects"
PROJECTS_SOURCE = Path(os.environ.get("HEXALITH_PUBLICATION_PROJECTS_SOURCE", ROOT / "references/Hexalith.Projects"))
FOLDERS_SOURCE = Path(os.environ.get("HEXALITH_PUBLICATION_FOLDERS_SOURCE", ROOT / "references/Hexalith.Folders"))


def git(directory, *args):
    return subprocess.check_output(["git", "-c", "submodule.recurse=false", "-C", str(directory), *args])


def source_digest(directory):
    names = set((git(directory, "ls-files", "-z") + git(directory, "ls-files", "--others", "--exclude-standard", "-z")).split(b"\0")) - {b""}
    digest = hashlib.sha256()
    for name in sorted(names):
        path = directory / os.fsdecode(name)
        if path.is_dir() and not path.is_symlink():
            continue
        if not path.exists() and not path.is_symlink():
            # A staged deletion and an unstaged deletion are the same absent
            # build input; index membership must not change the source digest.
            continue
        digest.update(name + b"\0")
        if path.is_symlink():
            digest.update(b"link\0" + os.fsencode(os.readlink(path)))
        elif path.is_file():
            digest.update(b"file\0" + str(path.stat().st_mode & 0o777).encode() + b"\0" + hashlib.sha256(path.read_bytes()).digest())
        else:
            digest.update(b"absent")
        digest.update(b"\0")
    return digest.hexdigest()


snapshots = {}
for name in ("Projects", "Builds", "EventStore", "Tenants", "Folders", "Platform"):
    full = "Hexalith." + name
    source = PROJECTS_SOURCE if name == "Projects" else FOLDERS_SOURCE if name == "Folders" else ROOT / "references" / full
    target = MODULE if name == "Projects" else MODULE / "references" / full
    before = git(target, "rev-parse", "HEAD").decode().strip()
    revision = git(source, "rev-parse", "HEAD").decode().strip()
    if name not in ("Projects", "Folders") and "HEXALITH_PUBLICATION_PROJECTS_SOURCE" in os.environ:
        # Qualify the fresh module's actual direct pins, rather than whatever
        # revision another session currently has checked out in the umbrella.
        revision = git(PROJECTS_SOURCE, "rev-parse", "HEAD:references/" + full).decode().strip()
        for raw in git(target, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0"):
            if raw:
                pending = target / os.fsdecode(raw)
                if pending.is_file() or pending.is_symlink():
                    pending.unlink()
        git(target, "read-tree", "--reset", "-u", revision)
        git(target, "update-ref", "HEAD", revision)
        if git(target, "status", "--porcelain=v1", "--ignore-submodules=all").strip():
            raise RuntimeError("Pinned dependency is not clean: " + full)
        snapshots[full] = {"revision": revision, "tree": git(target, "rev-parse", "HEAD^{tree}").decode().strip(),
                           "qualificationDigest": source_digest(target), "scope": "exact committed direct dependency"}
        print("SOURCE", full, json.dumps(snapshots[full]), flush=True)
        continue
    names = set((git(source, "diff", "--name-only", "HEAD", "-z")
                 + git(source, "ls-files", "--others", "--exclude-standard", "-z")
                 + git(target, "diff", "--name-only", "HEAD", "-z")
                 + git(target, "ls-files", "--others", "--exclude-standard", "-z")
                 + git(source, "diff", "--name-only", before, revision, "-z")).split(b"\0")) - {b""}
    for raw in sorted(names):
        relative = os.fsdecode(raw)
        original, copy = source / relative, target / relative
        if original.is_symlink():
            if copy.is_symlink() or copy.is_file():
                copy.unlink()
            copy.parent.mkdir(parents=True, exist_ok=True)
            copy.symlink_to(os.readlink(original))
        elif original.is_file():
            if copy.is_symlink():
                copy.unlink()
            copy.parent.mkdir(parents=True, exist_ok=True)
            if not copy.exists() or copy.read_bytes() != original.read_bytes():
                shutil.copy2(original, copy)
            copy.chmod(original.stat().st_mode & 0o777)
        elif not original.exists() and (copy.is_file() or copy.is_symlink()):
            copy.unlink()
    git(target, "read-tree", revision)
    git(target, "update-ref", "HEAD", revision)
    # Git records executable bits, while a clone's umask can add group-write
    # permission. Preserve all source permission bits for the byte/mode proof.
    for raw in set((git(source, "ls-files", "-z") + git(source, "ls-files", "--others", "--exclude-standard", "-z")).split(b"\0")) - {b""}:
        original, copy = source / os.fsdecode(raw), target / os.fsdecode(raw)
        if original.is_file() and not original.is_symlink() and not copy.is_symlink():
            if not copy.exists() or copy.read_bytes() != original.read_bytes():
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original, copy)
            if original.stat().st_mode & 0o777 != copy.stat().st_mode & 0o777:
                copy.chmod(original.stat().st_mode & 0o777)
    snapshots[full] = {"revision": revision, "sourceDigest": source_digest(source),
                       "qualificationDigest": source_digest(target)}
    if snapshots[full]["sourceDigest"] != snapshots[full]["qualificationDigest"]:
        raise RuntimeError("Disposable source differs from current source: " + full)
    print("SOURCE", full, json.dumps(snapshots[full]), flush=True)
(HERE / "product-source-snapshot.json").write_text(json.dumps(snapshots, indent=2) + "\n")

os.environ.update(DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1", DOTNET_CLI_USE_MSBUILD_SERVER="0", MSBUILDDISABLENODEREUSE="1")
os.environ.update(GIT_PAGER="cat", PAGER="cat", NO_COLOR="1", TERM="dumb")
config = MODULE / "references/Hexalith.Builds/NuGet.ci.Config"
flags = ["-noAutoResponse", "-p:Configuration=Release", "-warnaserror", "-p:UseHexalithProjectReferences=false",
         "-p:ShouldUnsetParentConfigurationAndPlatform=false", "-p:RestoreConfigFile=" + str(config),
         "-p:EnableNETAnalyzers=true", "-p:RunAnalyzers=true", "-p:RunAnalyzersDuringBuild=true",
         "-p:UseSharedCompilation=false", "-nr:false", "-m:1"]
results = []


def run(label, command, cwd=MODULE):
    print("RUN", label, json.dumps(command), flush=True)
    result = subprocess.run(command, cwd=cwd)
    results.append({"check": label, "command": command, "exitCode": result.returncode})
    (HERE / "product-commands.json").write_text(json.dumps(results, indent=2) + "\n")
    print("RESULT", label, result.returncode, flush=True)
    return result.returncode


for label, command in [
    ("restore", ["dotnet", "restore", "Hexalith.Projects.CI.slnx", "--disable-build-servers", *flags]),
    ("build", ["dotnet", "build", "Hexalith.Projects.CI.slnx", "--no-restore", "--disable-build-servers", *flags]),
]:
    code = run(label, command)
    if code:
        raise SystemExit(code)

sys.path.insert(0, str(MODULE / "references/Hexalith.Builds/Github/lib"))
import ci_pipeline
projects = ci_pipeline.discover_test_projects(MODULE, "Hexalith.Projects.CI.slnx")
ci_pipeline.execute_test_projects(MODULE, projects, runner=ci_pipeline.test_runner(MODULE), stage="Preserved product")

for label, command in [
    ("tools", ["dotnet", "tool", "restore", "--tool-manifest", ".config/dotnet-tools.json", "--configfile", str(config)]),
    ("generator-output", ["python3", "scripts/check-frontcomposer-output.py"]),
    ("package-consumers", ["python3", "scripts/check-package-dependencies.py"]),
    ("package-regressions", ["python3", "-B", "-m", "unittest", "discover", "-s", "tests/tools", "-p", "test_release_package_tools.py", "-v"]),
]:
    run(label, command)

for label, command in [
    ("npm-locked", ["npm", "ci", "--ignore-scripts"]),
    ("npm-signatures", ["npm", "audit", "signatures"]),
    ("browser-typecheck", ["npm", "run", "typecheck"]),
    ("browser-configuration", ["node", "node_modules/@playwright/test/cli.js", "test", "specs/browser-configuration.spec.ts", "--project", "chromium", "--workers", "1", "--retries", "0"]),
    ("browser-install", ["node", "node_modules/@playwright/test/cli.js", "install"]),
    ("browser-product", ["npm", "run", "test:package"]),
]:
    if run(label, command, MODULE / "tests/e2e"):
        break

owning = HERE / "qualify-owning-g6.py.txt"
original = ROOT / "_bmad-output/specs/spec-cicd/evidence/18/qualify-owning-g6.py"
owning.write_bytes(original.read_bytes())
try:
    runpy.run_path(str(owning))["run"](MODULE, SCRATCH)
    results.append({"check": "owning-g6", "exitCode": 0})
except Exception as error:
    print("OWNING G6 FAILURE", type(error).__name__, str(error), flush=True)
    results.append({"check": "owning-g6", "exitCode": 1})
(HERE / "product-commands.json").write_text(json.dumps(results, indent=2) + "\n")
failures = [row for row in results if row["exitCode"]]
print("QUALIFICATION FAILURES", json.dumps(failures), flush=True)
raise SystemExit(bool(failures))
