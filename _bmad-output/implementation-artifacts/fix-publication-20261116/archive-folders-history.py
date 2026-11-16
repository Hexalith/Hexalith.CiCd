"""Preserve inactive historical inputs as exact, non-executable gzip evidence."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import subprocess

root = Path(__file__).resolve().parents[3]
module = root / "references/Hexalith.Folders"
evidence = root / "_bmad-output/specs/spec-cicd/evidence/17/final-candidate.json"
diagnostics = json.loads(evidence.read_text())["audit_lint"]
paths = sorted(set(re.findall(r"(?:guard: )?(_bmad-output/[^\n]+?): audit-lint:", diagnostics)))
assert len(paths) == 8
files = []
for path in paths:
    blob = subprocess.check_output(["git", "-C", str(module), "rev-parse", "HEAD:" + path], text=True).strip()
    original = subprocess.check_output(["git", "-C", str(module), "cat-file", "blob", blob])
    assert (module / path).read_bytes() == original
    references = subprocess.run(["git", "-C", str(module), "grep", "-n", "-F", "-e", path,
                                 "--", ".", ":(exclude)_bmad-output/**"], capture_output=True, text=True)
    if references.returncode != 1:
        raise RuntimeError("An active reference requires investigation: " + path)
    mode = subprocess.check_output(["git", "-C", str(module), "ls-tree", "HEAD", "--", path], text=True).split()[0]
    compressed = gzip.compress(original, mtime=0)
    assert gzip.decompress(compressed) == original
    files.append(({"originalPath": path, "archivePath": path + ".gz", "originalMode": mode,
                   "originalGitBlob": blob, "originalBytes": len(original),
                   "originalSha256": hashlib.sha256(original).hexdigest(),
                   "archiveSha256": hashlib.sha256(compressed).hexdigest()}, compressed))

directory = module / "_bmad-output/implementation-artifacts/evidence/audit-policy-history"
directory.mkdir(exist_ok=False)
manifest = {"format": "hexalith.historical-artifacts.v1",
            "sourceCommit": subprocess.check_output(["git", "-C", str(module), "rev-parse", "HEAD"], text=True).strip(),
            "purpose": "Lossless archival of inactive historical configuration evidence; active audit enforcement is unchanged.",
            "files": [item for item, _ in files]}
for item, compressed in files:
    with (module / item["archivePath"]).open("xb") as output:
        output.write(compressed)
(directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
(directory / "README.md").write_text("# Historical configuration evidence\n\n"
    "The eight files in [manifest.json](manifest.json) preserve inactive historical NuGet inputs as deterministic gzip data. "
    "No active build configuration, audit rule or original receipt changed. Each archive decompresses to its original Git blob; "
    "the manifest preserves the original path, mode, size and SHA-256.\n\n"
    "Historical receipts still name the original paths. Reconstruct their exact layout only under the private TMPDIR of "
    "run-with-temp when inspecting or replaying them. These archives are evidence, not inputs for active restore, build or release.\n")
for item, _ in files:
    original = module / item["originalPath"]
    assert hashlib.sha256(original.read_bytes()).hexdigest() == item["originalSha256"]
    original.unlink()
print(json.dumps({"files": len(files), "manifest": str(directory / "manifest.json"),
                  "audit_rules_changed": False, "original_bytes_preserved": True}))
