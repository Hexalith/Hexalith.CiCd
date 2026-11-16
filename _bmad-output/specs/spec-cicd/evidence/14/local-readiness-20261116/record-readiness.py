"""Record local readiness and explicit adoption blockers without external reads."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
BUILDS = ROOT / "references/Hexalith.Builds"
AGENTS = ROOT / "references/Hexalith.Agents"


def git(repository, *arguments):
    return subprocess.check_output(["git", "-C", str(repository), *arguments])


tag = (ROOT / "builds-version").read_text().strip()
schema = json.loads(git(BUILDS, "show", tag + ":schemas/hexalith.ci.v1.json"))
tag_props = ET.fromstring(git(BUILDS, "show", tag + ":Props/Directory.Packages.props"))
source_props = ET.parse(BUILDS / "Props/Directory.Packages.props").getroot()
policy = ("minimumExpectedTests", "failSkips")
tag_fields = schema["properties"]["tests"]["properties"]
qualified = json.loads((HERE.parent / "publication/agents-qualification.json").read_text())
protected = (".gitmodules", "AGENTS.md", "CLAUDE.md", ".claude/settings.json",
             ".github/copilot-instructions.md", ".github/dependabot.yml", ".github/workflows",
             "references/Hexalith.Builds")
prior_shared = qualified["qualifiedSharedCandidate"]
shared_paths = ("schemas/hexalith.ci.v1.json", "Github/lib/ci_config.py", "Github/lib/ci_pipeline.py",
                "Github/lib/local_check.py", "Props/Directory.Packages.props")
pilot = ROOT / "_bmad-output/implementation-artifacts/spec-11-pilot-migration-commons-and-polymorphicserializations.md"
pilot_status = re.search(r"^status: '([^']+)'$", pilot.read_text(), re.MULTILINE).group(1)


def warnings(tree):
    return [element.text for element in tree.iter("WarningsNotAsErrors")]


report = {"observedAt": datetime.now(timezone.utc).isoformat(),
    "scope": "local Git objects and saved evidence only; no remote reads or writes",
    "controllerRevision": git(ROOT, "rev-parse", "HEAD").decode().strip(),
    "agents": {"revision": git(AGENTS, "rev-parse", "HEAD").decode().strip(),
        "worktreeChanges": git(AGENTS, "status", "--short").decode().splitlines(),
        "recordedFullProof": "../publication/agents-qualification.json",
        "recordedProofSourceStillCurrent": qualified["head"] == git(AGENTS, "rev-parse", "HEAD").decode().strip(),
        "recordedPreparationBase": qualified["freshMainBase"],
        "ownedDifferenceFromRecordedBase": git(AGENTS, "diff", "--raw", qualified["freshMainBase"],
            "HEAD", "--", *protected).decode().splitlines(),
        "ordinaryCheckerAfterDelivery": "required; no adoption or post-delivery check claimed"},
    "builds": {"revision": git(BUILDS, "rev-parse", "HEAD").decode().strip(),
        "worktreeChanges": git(BUILDS, "status", "--short").decode().splitlines(),
        "selectedTag": tag,
        "selectedTagRevision": git(BUILDS, "rev-parse", tag + "^{commit}").decode().strip(),
        "selectedTagTestFields": {field: field in tag_fields for field in policy},
        "selectedTagWarningsNotAsErrors": warnings(tag_props),
        "preparedWarningsNotAsErrors": warnings(source_props),
        "preparedFilesUnchangedFromRecordedProof": {
            path: git(BUILDS, "show", prior_shared + ":" + path) == git(BUILDS, "show", "HEAD:" + path)
            for path in shared_paths},
        "locallyKnownTagsContainingSharedPolicyCommit": git(BUILDS, "tag", "--contains", prior_shared).decode().splitlines(),
        "acceptableRelease": "not established by local evidence; remote release inventory was not refreshed"},
    "pilot": {"spec": str(pilot.relative_to(ROOT)), "status": pilot_status,
        "acceptance": "pending genuine scheduled-night checkpoint; no acceptance inferred"},
    "registration": {"productionSetupExists": (ROOT / "setup/Hexalith.Agents.yml").exists(),
        "candidate": "../local-implementation/Hexalith.Agents.yml", "enabled": False},
    "pending": ["pilot acceptance", "acceptable Builds release containing shared test/audit policy",
        "fresh authenticated AD-21 prerequisite/provisioning evidence", "fresh live-main duplicate qualification",
        "committed production registration/render and global/live validation", "authenticated App adoption",
        "ordinary standalone checker and immediate legacy credential cleanup", "green adopted CI",
        "Agents next genuine scheduled nightly including both CodeQL languages"],
    "result": "local preparation only; story remains in progress"}
(HERE / "readiness.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
