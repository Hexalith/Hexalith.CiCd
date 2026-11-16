"""Check the prepared registry in a disposable committed CiCd candidate, offline.

Use the renderer's exported locked requirements and run-with-temp. Live module,
App, release, bootstrap and online linter checks remain pending; this does not
invoke or replace the complete tools/validate.py verdict.
"""

from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
scratch = Path(os.environ["TMPDIR"]).resolve()
project = scratch / "cicd"
report = {"started_at": datetime.now(timezone.utc).isoformat(), "checks": {},
          "scope": "offline local preparation candidate; not an acceptance verdict",
          "pending": ["module preparation publication and current-main gitlink",
                      "full committed/global/live-module tools/validate.py verdict",
                      "fresh immutable Builds release authentication", "online workflow audits",
                      "story 11 scheduled-night acceptance", "all AD-21 remote operations"]}


def command(arguments, cwd=ROOT):
    result = subprocess.run(list(map(str, arguments)), cwd=cwd, capture_output=True, timeout=180)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    return result.stdout


try:
    command(["git", "clone", "--quiet", "--no-hardlinks", "--no-recurse-submodules", ROOT, project])
    base = command(["git", "rev-parse", "HEAD"], ROOT).decode().strip()
    command(["git", "checkout", "--quiet", "--detach", base], project)
    for relative in ("setup", "rendered"):
        shutil.rmtree(project / relative)
        shutil.copytree(ROOT / relative, project / relative)
    builds = project / "references/Hexalith.Builds"
    command(["git", "clone", "--quiet", "--no-hardlinks", "--no-recurse-submodules",
             ROOT / "references/Hexalith.Builds", builds])
    tag = (project / "builds-version").read_text().strip()
    command(["git", "checkout", "--quiet", "--detach", tag], builds)
    sys.path.insert(0, str(builds / "Github/lib"))
    from guard_tools import Tools
    tools_directory = scratch / "guard-tools"
    tools_directory.mkdir()
    message = (HERE / "product-commit-message.txt").read_text()
    Tools(tools_directory).lint_message(message, "disposable local candidate message")
    command(["git", "add", "setup", "rendered"], project)
    command(["git", "-c", "user.name=Local qualification", "-c", "user.email=local@example.invalid",
             "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "commit", "--quiet",
             "--file", HERE / "product-commit-message.txt"], project)
    spec = importlib.util.spec_from_file_location("_story12_checks", ROOT / "tools/check_global.py")
    checks = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = checks
    spec.loader.exec_module(checks)
    checks.check_committed_inputs(project)
    report["checks"]["committed_render_inputs"] = "pass"
    checks.check_committed_render(project)
    report["checks"]["committed_render"] = "pass"
    with checks.selected_contract(project) as contract:
        checks.check_render(project, contract)
        report["checks"]["render_reproducibility"] = "pass"
        registrations = checks.renderer.registry(project)
        checks.check_documents(project, registrations, contract)
        report["checks"]["schemas_and_caller_interfaces"] = "pass"
    for name in ("Hexalith.Commons", "Hexalith.PolymorphicSerializations"):
        assert command(["git", "diff", "--name-only", base, "HEAD", "--", "setup/" + name + ".yml",
                        "rendered/" + name, "rendered/" + name + ".perimeter.json"], project) == b""
    report["checks"]["existing_registrations_and_renders_preserved"] = "pass"
    unchanged_link = command(["git", "ls-tree", "HEAD", "references/Hexalith.AI.Tools"], project).decode().strip()
    assert "736687b79c1e4fa8beabdab75c4675bb76c466b9" in unchanged_link
    report.update(result="pass", source_base=base,
                  disposable_candidate=command(["git", "rev-parse", "HEAD"], project).decode().strip(),
                  registration_names=[name for name, _ in registrations],
                  recorded_module_gitlink=unchanged_link,
                  unpushed_module_commit_recorded=False,
                  source_gitlink_updated=False, push_performed=False)
except Exception as error:
    report.update(result="failed", error=str(error))
    raise
finally:
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    (HERE / "local-candidate-check.json").write_text(json.dumps(report, indent=2) + "\n")

print("Offline committed-candidate checks passed; live validation remains pending.")
