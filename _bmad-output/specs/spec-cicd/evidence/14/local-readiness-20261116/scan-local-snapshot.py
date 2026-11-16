"""Run the unchanged scan on committed local snapshots, with offline npm only.

This qualifies a disposable prospective registry, never a live-main readback or
production registration. The real detector still enforces its lock, signatures,
parser version and duplicate policy; missing cached inputs fail the check.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
SCRATCH = Path(os.environ["TMPDIR"])
sys.path.insert(0, str(ROOT / "tools"))
import delivery_runtime as rt
import scan


def git(repository, *arguments, data=None):
    return subprocess.check_output(["git", "-C", str(repository), *arguments], input=data)


# A bare disposable controller contains only a prospective registry change.
# No branch/ref/index/worktree in the real repository is modified.
controller = SCRATCH / "controller.git"
subprocess.run(["git", "-c", "submodule.recurse=false", "clone", "--quiet", "--shared", "--bare",
                str(ROOT), str(controller)], check=True)
revision = git(ROOT, "rev-parse", "HEAD").decode().strip()
git(controller, "read-tree", revision)
candidate = ROOT / "_bmad-output/specs/spec-cicd/evidence/14/local-implementation/Hexalith.Agents.yml"
blob = git(controller, "hash-object", "-w", "--stdin", data=candidate.read_bytes()).decode().strip()
git(controller, "update-index", "--add", "--cacheinfo", "100644," + blob + ",setup/Hexalith.Agents.yml")
tree = git(controller, "write-tree").decode().strip()
prospective = git(controller, "-c", "user.name=Local qualification", "-c", "user.email=local@example.invalid",
                  "commit-tree", tree, "-p", revision, data=b"test(cicd): qualify prospective Agents scan scope\n").decode().strip()
git(controller, "update-ref", "HEAD", prospective)

modules = rt.registry(rt.Git(controller), prospective)
snapshots = {name: {"path": str(ROOT / "references" / name),
    "revision": git(ROOT / "references" / name, "rev-parse", "HEAD").decode().strip()} for name in modules}
scanner_sources = ("tools/scan.py", "tools/scan_discovery.py", "tools/delivery_runtime.py",
                   ".jscpd.json", "tools/jscpd/package.json", "tools/jscpd/package-lock.json",
                   "tools/jscpd/discover.cjs")
for path in scanner_sources:
    assert (ROOT / path).read_bytes() == git(ROOT, "show", revision + ":" + path), path

# Copy the existing public npm cache into scratch. The forced offline shim
# cannot contact the registry and never mutates the shared cache.
cache = SCRATCH / "npm-cache"
subprocess.run(["cp", "-a", "--reflink=auto", str(Path.home() / ".npm"), str(cache)], check=True)
binary = SCRATCH / "bin"
binary.mkdir()
npm = shutil.which("npm")
assert npm
shim = binary / "npm"
shim.write_text("#!/bin/sh\nexec " + shlex.quote(npm) + " --offline --cache " + shlex.quote(str(cache)) + " \"$@\"\n")
shim.chmod(0o755)


class LocalTransport:
    """Transfer only the selected local commit objects, without a network URL."""
    def module(self, repository, module):
        source = snapshots[module]
        repository.run("-c", "protocol.file.allow=always", "fetch", "--quiet", "--no-tags",
                       "--no-recurse-submodules", source["path"], source["revision"])
        return repository.resolve("FETCH_HEAD")


def detector(git_source, source_revision, scratch):
    return scan.Detector(git_source, source_revision, scratch,
                         path=str(binary) + os.pathsep + os.environ["PATH"])


report = scan.scan(controller, HERE / "scan", transport=LocalTransport(), detector_factory=detector)
scope = {"observedAt": datetime.now(timezone.utc).isoformat(),
    "scope": "prospective committed registry and local committed module snapshots; no network",
    "controllerBase": revision, "prospectiveController": prospective, "prospectiveTree": tree,
    "candidateSetupSha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
    "modules": snapshots, "scannerSourcesUnchanged": True,
    "scannerSourceSha256": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in scanner_sources},
    "npmTransport": "forced offline; existing public cache copied into disposable scratch",
    "result": report["result"],
    "limitation": "Does not replace fresh live-main scan, accepted release or adoption prerequisites."}
(HERE / "scan-scope.json").write_text(json.dumps(scope, indent=2) + "\n")
print(json.dumps({"result": report["result"], "errors": report["errors"],
    "modules": [{"module": row["module"], "revision": row["revision"], "result": row["result"],
                 "files": len(row["files"]), "errors": row["errors"]} for row in report["modules"]],
    "findings": len(report["findings"])}, indent=2))
raise SystemExit(report["result"] != "pass")
