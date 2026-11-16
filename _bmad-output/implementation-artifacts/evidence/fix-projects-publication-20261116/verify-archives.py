"""Verify exact historical reconstruction and the unchanged released audit policy."""
from pathlib import Path
import gzip
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MODULE = Path(os.environ.get("HEXALITH_PUBLICATION_PROJECTS_SOURCE", ROOT / "references/Hexalith.Projects"))
SCRATCH = Path(os.environ["TMPDIR"])
RELEASE = "fdda17c0a4538b0f7c99f813c20ca24b49006530"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)

released = SCRATCH / "released"
released.mkdir()
archive = subprocess.check_output(["git", "-C", str(ROOT / "references/Hexalith.Builds"),
                                   "archive", RELEASE, "Github/lib", "schemas"])
with tarfile.open(fileobj=io.BytesIO(archive)) as contents:
    contents.extractall(released, filter="data")
sys.path.insert(0, str(released / "Github/lib"))
import audit_lint
from expected_state import ExpectedStateError, Git, tree_snapshot

environment = {**os.environ, "GIT_INDEX_FILE": str(SCRATCH / "candidate.index")}
for command in (["git", "read-tree", "HEAD"], ["git", "add", "-A"]):
    subprocess.run(command, cwd=MODULE, env=environment, check=True)
tree = subprocess.check_output(["git", "write-tree"], cwd=MODULE, env=environment, text=True).strip()
snapshot = tree_snapshot(Git(MODULE), tree)
manifest_path = "_bmad-output/implementation-artifacts/evidence/audit-policy-history/manifest.json"
manifest = json.loads(snapshot.read(manifest_path))
prior = json.loads((ROOT / "_bmad-output/implementation-artifacts/push-all-20261116T194845Z/projects-released-audit.json").read_text())
expected = {line.split(": audit-lint:", 1)[0].removeprefix("guard: ")
            for line in prior["results"]["candidate"]["diagnostics"].splitlines() if ": audit-lint:" in line}
originals = [entry["originalPath"] for entry in manifest["files"]]
archives = [entry["archivePath"] for entry in manifest["files"]]
require(manifest["sourceCommit"] == prior["base"], "Historical source commit changed")
require(len(originals) == len(set(originals)) == len(expected) == 12, "Expected twelve distinct originals")
require(set(originals) == expected, "Historical archive scope differs from the twelve reported files")
require(len(archives) == len(set(archives)), "Duplicate archive paths")
rows = []
for entry in manifest["files"]:
    path, archive_path = entry["originalPath"], entry["archivePath"]
    require(archive_path == path + ".gz", "Unexpected archive mapping: " + path)
    require(path not in snapshot.items, "Original XML remains in the candidate: " + path)
    require(archive_path in snapshot.items, "Archive is absent from the candidate: " + archive_path)
    packed = snapshot.read(archive_path)
    require(hashlib.sha256(packed).hexdigest() == entry["archiveSha256"], "Archive hash mismatch: " + path)
    original = gzip.decompress(packed)
    require(len(original) == entry["originalBytes"], "Original size mismatch: " + path)
    require(hashlib.sha256(original).hexdigest() == entry["originalSha256"], "Original hash mismatch: " + path)
    base = subprocess.check_output(["git", "-C", str(MODULE), "show", manifest["sourceCommit"] + ":" + path])
    mode, kind, blob = subprocess.check_output(["git", "-C", str(MODULE), "ls-tree", manifest["sourceCommit"], "--", path], text=True).split("\t", 1)[0].split()
    require(kind == "blob" and blob == entry["originalGitBlob"], "Original Git blob mismatch: " + path)
    require(mode == entry["originalMode"] == snapshot.items[archive_path].mode, "Original/archive Git mode mismatch: " + path)
    require(original == base, "Historical bytes changed: " + path)
    restored = SCRATCH / "restored" / path
    restored.resolve().relative_to(SCRATCH.resolve())
    restored.parent.mkdir(parents=True, exist_ok=True)
    restored.write_bytes(original)
    restored.chmod(int(mode, 8) & 0o777)
    require(restored.stat().st_mode & 0o777 == int(mode, 8) & 0o777, "Restored mode mismatch: " + path)
    require(restored.read_bytes() == base, "Restored bytes mismatch: " + path)
    rows.append({"path": path, "result": "exact bytes, mode, Git blob and hashes preserved"})
audit_lint.lint(snapshot)


class Fixture:
    def __init__(self, files):
        self.files = files
        self.items = {path: SimpleNamespace(mode="100644") for path in files}

    def read(self, path):
        return self.files[path]


negative = []
for path, data, declaration in [
    ("NuGet.Config", b"<configuration><auditSources><clear/></auditSources></configuration>", "auditSources"),
    ("arbitrary.txt", b"<Project><PropertyGroup><MSBuildWarningsAsMessages>NU1904</MSBuildWarningsAsMessages></PropertyGroup></Project>", "MSBuildWarningsAsMessages"),
]:
    try:
        audit_lint.lint(Fixture({path: data}))
    except ExpectedStateError as error:
        require(declaration in str(error), "Negative control failed for an unexpected reason")
        negative.append({"path": path, "declaration": declaration, "result": "rejected"})
    else:
        raise AssertionError("Active forbidden input was accepted: " + path)

report = {"releasedValidatorCommit": RELEASE, "candidateTree": tree,
          "historicalFiles": rows, "releasedFullTreeAudit": "pass", "activeNegativeControls": negative}
(HERE / "archives.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
