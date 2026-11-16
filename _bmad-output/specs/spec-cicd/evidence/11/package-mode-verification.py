"""Run with run-with-temp: export direct repositories, build/test and consume packages.

No nested submodule is initialized and no owned module file is authored. The
shared pipeline receives an in-memory prospective configuration for this check.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

SOURCE = Path(__file__).resolve().parents[5]
WORKSPACE = Path(os.environ["TMPDIR"]) / "package-mode"
(WORKSPACE / "references").mkdir(parents=True)
for name in ("Hexalith.Builds", "Hexalith.Commons", "Hexalith.PolymorphicSerializations"):
    repository = SOURCE / "references" / name
    destination = WORKSPACE / "references" / name
    destination.mkdir()
    archive = WORKSPACE / (name + ".tar")
    with archive.open("wb") as output:
        subprocess.run(["git", "archive", "HEAD"], cwd=repository, stdout=output, check=True)
    with tarfile.open(archive) as payload:
        payload.extractall(destination, filter="data")
    archive.unlink()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()
    print(json.dumps({"repository": name, "revision": revision}), flush=True)

commons = WORKSPACE / "references/Hexalith.Commons"
for relative in ("scripts/pack-release-packages.py", "scripts/validate-consumer-package-references.py",
                 ".github/actions/after-unit-tests/action.yml"):
    source = SOURCE / "references/Hexalith.Commons" / relative
    target = commons / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    print(json.dumps({"overlay": relative, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}), flush=True)

os.environ.update(NUGET_PACKAGES=str(WORKSPACE / ".nuget/packages"),
                  NUGET_HTTP_CACHE_PATH=str(WORKSPACE / ".nuget/http"),
                  NUGET_PLUGINS_CACHE_PATH=str(WORKSPACE / ".nuget/plugins"),
                  DOTNET_CLI_HOME=str(WORKSPACE / ".dotnet"), MinVerVersionOverride="0.0.0")
builds = WORKSPACE / "references/Hexalith.Builds"
sys.path.insert(0, str(builds / "Github/lib"))
import ci_pipeline as pipeline

for name in ("Hexalith.Commons", "Hexalith.PolymorphicSerializations"):
    root = WORKSPACE / "references" / name
    document = {"schema": "hexalith.ci.v1", "buildsTag": "v5.2.2", "solution": name + ".slnx",
                "dapr": False, "browsers": False, "registry": False, "codeql": ["csharp"],
                "tests": {"integration": [], "exclude": {}}, "hooks": [], "jobs": {}, "submodules": []}
    pipeline.validate_config(document, repository="Hexalith/" + name)
    prepared = pipeline.PreparedConfig(WORKSPACE, root, document, document["solution"], "global.json", ())
    print("Package-mode restore/build and all unit projects:", name, flush=True)
    pipeline.restore_and_build(prepared)
    classified = pipeline.run_unit_tests(prepared, repository="Hexalith/" + name)
    assert len(classified.unit) == (8 if name == "Hexalith.Commons" else 1), classified
    if name == "Hexalith.Commons":
        packages = WORKSPACE / "commons-packages"
        subprocess.run([sys.executable, "scripts/pack-release-packages.py", str(packages), "0.0.0",
                        "--nuget-config", str(builds / "NuGet.ci.Config")], cwd=root, check=True)
        subprocess.run([sys.executable, "scripts/validate-nuget-packages.py", str(packages)], cwd=root, check=True)
        subprocess.run([sys.executable, "scripts/validate-consumer-package-references.py", str(packages)],
                       cwd=root, check=True)
print("Both pilot package-mode builds, all nine C# suites and Commons package consumption passed.", flush=True)
