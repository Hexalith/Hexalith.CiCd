"""Compare integration source method bodies/attributes across the local split."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path("/home/administrator/projects/hexalith/memories-story-22")
EVIDENCE = Path(__file__).resolve().parent
BASELINE = "c64e292a46858058f6764095c8e01c2faa0ff3e0"
REMOVED_CI_ASSERTION = "OpenBaoTopologyTraits_FastSlowAndPerformanceLanesRemainSeparated"


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT, text=True).strip()


def methods(source):
    found = []
    for match in re.finditer(r"^    \[(?:Fact|Theory)\b", source, re.MULTILINE):
        end = re.search(r"^    }\s*$", source[match.end():], re.MULTILINE)
        if end is None:
            raise RuntimeError("Missing test member end")
        block = source[match.start():match.end() + end.end()].rstrip()
        name = re.search(r"public (?:async )?(?:Task(?:<[^>]+>)?|void) (\w+)\(", block)
        if name is None:
            raise RuntimeError("Unexpected test member declaration: " + block[:200])
        found.append((name[1], hashlib.sha256(block.encode()).hexdigest()))
    return found


before = []
for path in git("ls-tree", "-r", "--name-only", BASELINE, "--",
                "tests/Hexalith.Memories.IntegrationTests").splitlines():
    if path.endswith(".cs"):
        before.extend(methods(git("show", BASELINE + ":" + path) + "\n"))
after = []
for folder in ("Hexalith.Memories.IntegrationTests", "Hexalith.Memories.Integration.NightlyTests"):
    for path in (ROOT / "tests" / folder).rglob("*.cs"):
        after.extend(methods(path.read_text()))

classified = [entry for entry in before if entry[0] == REMOVED_CI_ASSERTION]
assert len(classified) == 1
product_before = [entry for entry in before if entry[0] != REMOVED_CI_ASSERTION]
missing = Counter(product_before) - Counter(after)
added = Counter(after) - Counter(product_before)
result = {"baseline": BASELINE, "candidate": git("rev-parse", "HEAD"),
    "baselineSourceTestMethods": len(before), "candidateSourceTestMethods": len(after),
    "removedCiAssertions": [{"method": name, "sha256": digest,
        "classification": "CAP-10 CI test inventory/trait-selection gate; no OpenBao product behavior"}
        for name, digest in classified],
    "missingOrChangedProductMethods": list(missing.elements()),
    "addedOrChangedProductMethods": list(added.elements()),
    "allProductMethodBodiesAndAttributesPreserved": not missing and not added}
(EVIDENCE / "integration-method-preservation.json").write_text(json.dumps(result, indent=2) + "\n")
assert result["allProductMethodBodiesAndAttributesPreserved"]
print(json.dumps(result))
