"""Compute real module versions without dispatching or publishing anything.

Run under run-with-temp. Use the unmodified released resolver and pinned real
plugins against fresh anonymous main/tag objects, not stale local tag refs.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
builds = ROOT / "references/Hexalith.Builds"
path = builds / "Github/lib/release_version.py"
released = subprocess.run(["git", "show", "v6.0.6:Github/lib/release_version.py"], cwd=builds,
                          capture_output=True, check=True).stdout
assert released == path.read_bytes()
sys.path.insert(0, str(path.parent))
from release_version import Plugins, compute_version
from release_state import Git

scratch = Path(os.environ["TMPDIR"]) / "actual-version-assessment"
scratch.mkdir()
plugins_directory = scratch / "plugins"
plugins_directory.mkdir()
plugins = Plugins(plugins_directory)
preparation = json.loads((HERE / "local-product-preparation.json").read_text())
removed = {"Hexalith.Commons": ["2.30.2"], "Hexalith.PolymorphicSerializations": ["1.19.4", "1.19.0"]}
report = {"started_at": datetime.now(timezone.utc).isoformat(), "builds_tag": "v6.0.6",
          "unmodified_resolver_sha256": hashlib.sha256(released).hexdigest(),
          "real_locked_plugin_package_sha256": hashlib.sha256((builds / "Github/release-version/package-lock.json").read_bytes()).hexdigest(),
          "workflow_dispatch_performed": False, "publication_performed": False, "version_override": False,
          "modules": {}}
for name, module in preparation["modules"].items():
    directory = scratch / name
    directory.mkdir()
    git = Git.fetch(directory, "Hexalith/" + name)
    main = git.run("rev-parse", "refs/heads/main").stdout.decode().strip()
    assert main == module["head"]
    missing_tags = []
    for version in removed[name]:
        reference = git.run("show-ref", "--verify", "refs/tags/v" + version, allowed=(0, 1, 128))
        assert reference.returncode != 0
        missing_tags.append("v" + version)
    result = compute_version(git, plugins, repository="Hexalith/" + name, sha=main, selection="module")
    last = tuple(map(int, result["last-tag"][1:].split("."))) if result["last-tag"] else (0, 0, 0)
    selected = tuple(map(int, result["version"].split("."))) if result["version"] else None
    report["modules"][name] = {"frozen_main": main, "last_tag": result["last-tag"], "no_version": result["no-version"],
        "computed_version": result["version"], "notes_sha256": hashlib.sha256(result["notes"].encode()).hexdigest(),
        "removed_tags_absent_from_fresh_remote_fetch": missing_tags,
        "orphan_comparison": [{"version": value, "last_tag_is_newer": last > tuple(map(int, value.split("."))),
                               "computed_version_is_newer": selected > tuple(map(int, value.split("."))) if selected else None}
                              for value in removed[name]]}
report["completed_at"] = datetime.now(timezone.utc).isoformat()
report["result"] = "unmodified shared version computation completed; no release manufactured"
(HERE / "actual-next-version-assessment.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2), flush=True)
