#!/usr/bin/env python3
"""Prove the real MTP/xUnit configuration turns a deliberately disposable skip into a failure."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

evidence = Path(__file__).resolve().parent
product = evidence.parents[4] / "references/Hexalith.ChatBot"
scratch = Path(os.environ["TMPDIR"]) / "required-runner-probe"
scratch.mkdir()
shutil.copy2(product / "global.json", scratch / "global.json")
(scratch / "Probe.csproj").write_text('''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><IsPackable>false</IsPackable></PropertyGroup>
  <ItemGroup><PackageReference Include="Microsoft.NET.Test.Sdk" Version="18.12.0" /><PackageReference Include="xunit.v3" Version="4.0.3" /><PackageReference Include="xunit.runner.visualstudio" Version="4.0.1" /></ItemGroup>
</Project>
''')
(scratch / "Probe.cs").write_text('''using Xunit;
public sealed class DisposableRunnerProbe
{
    [Fact(Skip = "Deliberate disposable probe; never a product test")]
    public void SkipMustFailInARequiredProject() { }
}
''')
log_path = evidence / "product-required-runner-probe.log"
results = {"sdk": json.loads((product / "global.json").read_text())["sdk"], "xunit_version": "4.0.3", "steps": [],
           "documentation": "https://xunit.net/docs/config-xunit-runner-json#failSkips"}
with log_path.open("w") as log:
    for enabled in [False, True]:
        configuration = scratch / "bin/Release/net10.0/xunit.runner.json"
        if enabled:
            shutil.copy2(product / "tests/required-live.xunit.runner.json", configuration)
        command = ["dotnet", "test", "--project", "Probe.csproj", "--configuration", "Release"]
        if enabled:
            command.extend(["--no-build", "--no-restore"])
        completed = subprocess.run(command, cwd=scratch, capture_output=True, text=True, timeout=180)
        output = completed.stdout + completed.stderr
        log.write("$ " + " ".join(command) + "\n" + output + "\n")
        results["steps"].append({"required_configuration_enabled": enabled, "exit": completed.returncode})
        if enabled:
            assert completed.returncode != 0 and "failed: 1" in output and "succeeded: 0" in output, output
        else:
            assert completed.returncode == 0 and "skipped: 1" in output, output
results["configuration_sha256"] = hashlib.sha256((product / "tests/required-live.xunit.runner.json").read_bytes()).hexdigest()
results["required_skip_rejected"] = True
(evidence / "product-required-runner-probe.json").write_text(json.dumps(results, indent=2) + "\n")
print("The same complete disposable project skips without the configuration and fails with the required-live configuration.")
