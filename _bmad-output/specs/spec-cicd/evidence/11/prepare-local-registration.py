"""Prepare and check local pilot registration inputs without publishing adoption.

Run under run-with-temp. Preserve all existing root staging. This deliberately
does not run the full committed/live-main candidate verdict before product
preparation mains and the cleanup prerequisite exist.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
assert not any(name in os.environ for name in ("GH_TOKEN", "GITHUB_TOKEN"))
release = json.loads((HERE / "builds-released-pin.json").read_text())
proof = json.loads((HERE / "pre-adoption-verification.json").read_text())
preparation = json.loads((HERE / "local-product-preparation.json").read_text())
assert release["result"] == "acceptable released shared behavior"
assert proof["result"] == "pass" and proof["purpose"] == "preparation"
assert proof["builds_tag"] == release["release"]["tag_name"] == "v6.0.6"
for name, module in preparation["modules"].items():
    assert all(proof["modules"][name][key] == module[key] for key in ("base", "head"))


def command(arguments, repository=ROOT):
    return subprocess.run(arguments, cwd=repository, capture_output=True, check=True, timeout=180).stdout


staging = command(["git", "diff", "--cached", "--binary", "--no-ext-diff"])
staging_sha = hashlib.sha256(staging).hexdigest()
assert (ROOT / "builds-version").read_text() == "v5.2.2\n"
registrations = {"Hexalith.Commons": "solution: Hexalith.Commons.slnx\nhooks: [after-unit-tests]\n",
                 "Hexalith.PolymorphicSerializations": "solution: Hexalith.PolymorphicSerializations.slnx\n"}
for name, body in registrations.items():
    path = ROOT / "setup" / (name + ".yml")
    assert not path.exists()
    path.write_text(body)
(ROOT / "builds-version").write_text("v6.0.6\n")
result = subprocess.run(["uv", "run", "--locked", "--script", "tools/render.py"], cwd=ROOT, check=False)
assert result.returncode == 0
result = subprocess.run(["uv", "run", "--locked", "--script", "tools/render.py", "--check"], cwd=ROOT, check=False)
assert result.returncode == 0
scratch = Path(os.environ["TMPDIR"]) / "local-registration-contract"
scratch.mkdir()
driver = scratch / "check.py"
source = (ROOT / "tools/check_global.py").read_text()
header = re.search(r"(?ms)^# /// script\n.*?^# ///\n", source).group()
driver.write_text(header + r'''
import json, pathlib, subprocess, sys
sys.dont_write_bytecode=True
root=pathlib.Path(sys.argv[1])
sys.path.insert(0,str(root/'tools'))
import check_global as checks
def github(path):
    result=subprocess.run(['gh','api','repos/Hexalith/Hexalith.Builds/'+path],capture_output=True,text=True,check=True,timeout=60)
    return json.loads(result.stdout)
with checks.selected_contract(root) as contract:
    checks.check_render(root,contract)
    checks.check_documents(root,checks.renderer.registry(root),contract)
    checks.check_release(contract,api=github)
    print(json.dumps({'local_render_reproducibility':'pass','tagged_schemas_and_caller_interfaces':'pass',
                      'actual_acceptable_published_release':'pass','tag':contract.tag,'revision':contract.revision}))
''')
shutil.copyfile(ROOT / "tools/check_global.py.lock", driver.with_suffix(".py.lock"))
result = subprocess.run(["uv", "run", "--locked", "--script", str(driver), str(ROOT)], cwd=ROOT, check=False)
assert result.returncode == 0
after = command(["git", "diff", "--cached", "--binary", "--no-ext-diff"])
assert after == staging, "Root staging changed"
paths = [ROOT / "builds-version", *(ROOT / "setup" / (name + ".yml") for name in registrations)]
paths += [path for path in (ROOT / "templates").rglob("*") if path.is_file()]
paths += [path for path in (ROOT / "rendered").rglob("*") if path.is_file()]
inputs = {str(path.relative_to(ROOT)): {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
          "mode": "100755" if path.stat().st_mode & 0o111 else "100644"} for path in sorted(paths)}
desired_gitlinks = {name: command(["git", "rev-parse", "HEAD"], ROOT / "references" / name).decode().strip()
                    for name in ("Hexalith.Builds", *registrations)}
assert desired_gitlinks["Hexalith.Builds"] == release["source_sha"]
report = {"observed_at": datetime.now(timezone.utc).isoformat(), "builds_tag": "v6.0.6",
          "local_render_reproducibility": "pass", "tagged_schemas_and_caller_interfaces": "pass",
          "actual_acceptable_published_release": "pass", "registrations": registrations,
          "candidate_file_inputs": inputs, "desired_direct_gitlinks": desired_gitlinks,
          "original_staging_before_sha256": staging_sha,
          "original_staging_after_sha256": hashlib.sha256(after).hexdigest(), "original_staging_preserved": True,
          "committed_candidate_created": False, "delivery_triggering_push_performed": False,
          "full_candidate_verdict": "not performed: pending Zot disposition, live product-preparation mains and committed candidate",
          "result": "reviewable local registration/render/pin only"}
(HERE / "local-registration-preparation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({key: value for key, value in report.items() if key != "candidate_file_inputs"}, indent=2), flush=True)
