#!/usr/bin/env python3
"""Run the real browser product gate with its exact private Node distribution."""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import time
import urllib.request


EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parents[4]
SOURCE = ROOT / "references/Hexalith.Parties"


def main() -> int:
    scratch = Path(os.environ["TMPDIR"])
    report = {"phase": "local browser product verification; no hosted/adoption credit", "commands": []}
    try:
        distribution = "node-v24.22.1-linux-x64"
        archive = distribution + ".tar.xz"
        origin = "https://nodejs.org/dist/v24.22.1/"
        sums = urllib.request.urlopen(origin + "SHASUMS256.txt", timeout=30).read().decode()
        expected = next(line.split()[0] for line in sums.splitlines() if line.split()[-1] == archive)
        payload = scratch / archive
        with urllib.request.urlopen(origin + archive, timeout=30) as response, payload.open("wb") as output:
            shutil.copyfileobj(response, output)
        actual = hashlib.sha256(payload.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("Node archive differs from the official distribution checksum")
        with tarfile.open(payload) as package:
            package.extractall(scratch, filter="data")
        report["nodeDistribution"] = {"url": origin + archive, "sha256": actual}
        environment = dict(os.environ, PATH=str(scratch / distribution / "bin") + os.pathsep + os.environ["PATH"],
                           CI="true", BASE_URL="http://127.0.0.1:5072", PLAYWRIGHT_SKIP_WEBSERVER="",
                           PLAYWRIGHT_BROWSERS_PATH=str(scratch / "browsers"), npm_config_cache=str(scratch / "npm-cache"))
        module = scratch / "Hexalith.Parties"
        subprocess.run(["git", "clone", "--quiet", "--shared", "--no-recurse-submodules", str(SOURCE), str(module)], check=True)
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=SOURCE, text=True).split("\0")
        untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=SOURCE, text=True).split("\0")
        for name in tracked + untracked:
            if not name:
                continue
            source, target = SOURCE / name, module / name
            if source.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            elif target.is_file():
                target.unlink()
        pin = (ROOT / "builds-version").read_text().strip()
        builds = module / "references/Hexalith.Builds"
        subprocess.run(["git", "clone", "--quiet", "--shared", "--no-checkout", "--no-recurse-submodules", str(ROOT / "references/Hexalith.Builds"), str(builds)], check=True)
        subprocess.run(["git", "-C", str(builds), "checkout", "--quiet", "--detach", pin], check=True)
        report["source"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip()
        report["buildsVersion"] = pin
        browser = module / "tests/e2e"
        commands = [
            ("node", ["node", "--version"], module),
            ("npm", ["npm", "--version"], module),
            ("install", ["npm", "ci", "--ignore-scripts"], browser),
            ("build", ["dotnet", "build", "src/Hexalith.Parties.UI/Hexalith.Parties.UI.csproj", "--configuration", "Release", "--disable-build-servers", "-m:1", "-warnaserror", "-p:UseHexalithProjectReferences=false", "-p:UseNuGetDeps=true", "-p:NuGetAudit=true", "-p:NuGetAuditMode=all", "-p:NuGetAuditLevel=low", "-p:HexalithEventStoreVersion=5.1.1"], module),
            ("configuration", ["npm", "run", "test:config"], browser),
            ("types", ["npm", "run", "typecheck"], browser),
            ("chromium", ["npx", "--no-install", "playwright", "install", "chromium"], browser),
            ("scenarios", ["npm", "run", "test:ui"], browser),
        ]
        for name, command, directory in commands:
            started = time.monotonic()
            with (EVIDENCE / ("browser-" + name + ".log")).open("w") as output:
                result = subprocess.run(command, cwd=directory, env=environment, stdout=output, stderr=subprocess.STDOUT)
            report["commands"].append({"argv": command, "exitCode": result.returncode, "durationSeconds": round(time.monotonic() - started, 3)})
            if result.returncode:
                return result.returncode
        results = browser / "test-results"
        if results.is_dir():
            shutil.copytree(results, EVIDENCE / "browser-results", dirs_exist_ok=True)
        return 0
    except Exception as error:
        report["failure"] = type(error).__name__ + ": " + str(error)
        return 1
    finally:
        (EVIDENCE / "browser-verification.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))


if __name__ == "__main__":
    raise SystemExit(main())
