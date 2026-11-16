#!/usr/bin/env python3
"""Real SDK 11/net10 temporary author-trust probe; run with run-with-temp."""

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import zipfile
import xml.etree.ElementTree as ET


EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parents[4]


def main():
    scratch = Path(os.environ["TMPDIR"])
    environment = dict(os.environ, DOTNET_CLI_HOME=str(scratch / "cli-home"),
                       DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER="1", MSBUILDDISABLENODEREUSE="1",
                       DOTNET_GENERATE_ASPNET_CERTIFICATE="false")
    results = []
    log = (EVIDENCE / "candidate-signing-sdk-probe.log").open("w")

    def command(args, expected=0):
        outcome = subprocess.run(args, cwd=scratch, env=environment, text=True, capture_output=True)
        log.write(json.dumps(args) + "\n" + outcome.stdout + outcome.stderr + "\n")
        log.flush()
        results.append({"command": args, "exit": outcome.returncode, "expected": expected})
        if (outcome.returncode == 0) != (expected == 0):
            raise RuntimeError(outcome.stdout + outcome.stderr)
        return outcome.stdout

    try:
        (scratch / "global.json").write_text('{"sdk":{"version":"11.0.100","rollForward":"latestPatch"}}')
        (scratch / "Fixture.csproj").write_text('''<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>
<TargetFramework>net10.0</TargetFramework><PackageId>Fixture</PackageId><Version>1.2.3</Version>
<NuGetAudit>true</NuGetAudit><NuGetAuditMode>all</NuGetAuditMode>
</PropertyGroup></Project>''')
        (scratch / "Product.cs").write_text('namespace Fixture; public static class Product { public const int Marker = 42; }')
        base = ROOT / "references/Hexalith.Builds/NuGet.ci.Config"
        command(["dotnet", "pack", "Fixture.csproj", "-c", "Release", "-o", str(scratch / "unsigned"),
                 "-p:RestoreConfigFile=" + str(base), "-warnaserror", "-m:1", "/nr:false"])
        original = scratch / "unsigned/Fixture.1.2.3.nupkg"
        fingerprints = {}
        for name in ("job", "wrong", "expired"):
            directory = scratch / name
            directory.mkdir(mode=0o700)
            args = ["openssl", "req", "-x509", "-newkey", "rsa:3072", "-noenc", "-sha256",
                    "-keyout", str(directory / "key.pem"), "-out", str(directory / "cert.pem"),
                    "-subj", "/CN=Private candidate validation", "-days", "1",
                    "-addext", "basicConstraints=critical,CA:FALSE", "-addext", "keyUsage=critical,digitalSignature",
                    "-addext", "extendedKeyUsage=codeSigning"]
            if name == "expired":
                now = datetime.now(timezone.utc)
                expiry = now + timedelta(seconds=45)
                args.extend(["-not_before", (now - timedelta(minutes=1)).strftime("%Y%m%d%H%M%SZ"),
                             "-not_after", expiry.strftime("%Y%m%d%H%M%SZ")])
            command(args)
            command(["openssl", "pkcs12", "-export", "-inkey", str(directory / "key.pem"),
                     "-in", str(directory / "cert.pem"), "-out", str(directory / "signer.pfx"), "-passout", "pass:"])
            command(["openssl", "x509", "-in", str(directory / "cert.pem"), "-outform", "DER", "-out", str(directory / "cert.der")])
            fingerprint = hashlib.sha256((directory / "cert.der").read_bytes()).hexdigest().upper()
            fingerprints[name] = fingerprint
            document = ET.parse(base)
            author = ET.SubElement(document.getroot().find("trustedSigners"), "author", name="private-validation-job")
            ET.SubElement(author, "certificate", fingerprint=fingerprint, hashAlgorithm="SHA256", allowUntrustedRoot="true")
            document.write(directory / "NuGet.Config")
            package = directory / original.name
            shutil.copyfile(original, package)
            command(["dotnet", "nuget", "sign", str(package), "--certificate-path", str(directory / "signer.pfx"),
                     "--allow-untrusted-root", "--timestamper", "http://timestamp.digicert.com",
                     "--timestamp-hash-algorithm", "SHA256", "--verbosity", "minimal"])
        job = scratch / "job"
        verify = ["dotnet", "nuget", "verify", "--all", "--certificate-fingerprint", fingerprints["job"],
                  "--configfile", str(job / "NuGet.Config")]
        command([*verify, str(job / original.name)])
        command([*verify, str(original)], expected=1)
        command([*verify, str(scratch / "wrong" / original.name)], expected=1)
        tampered = scratch / "tampered.nupkg"
        shutil.copyfile(job / original.name, tampered)
        with zipfile.ZipFile(tampered, "a") as archive:
            archive.writestr("unexpected.txt", "tampered")
        command([*verify, str(tampered)], expected=1)
        expired = scratch / "expired"
        # Authenticate the genuinely signed archive against its own now-expired
        # identity, rather than merely proving a wrong-fingerprint failure.
        time.sleep(max(0, (expiry - datetime.now(timezone.utc)).total_seconds()) + 1)
        expired_sdk = command(["dotnet", "nuget", "verify", str(expired / original.name), "--all",
                               "--certificate-fingerprint", fingerprints["expired"], "--configfile", str(expired / "NuGet.Config")])
        assert "NU3037" not in expired_sdk, "timestamped signature unexpectedly expired in SDK verification"
        command(["openssl", "verify", "-trusted", str(expired / "cert.pem"), "-check_ss_sig", str(expired / "cert.pem")], expected=1)
        command(["openssl", "verify", "-trusted", str(job / "cert.pem"), "-check_ss_sig", str(job / "cert.pem")])
        with zipfile.ZipFile(original) as unsigned, zipfile.ZipFile(job / original.name) as signed:
            assert set(signed.namelist()) == set(unsigned.namelist()) | {".signature.p7s"}
            assert all(unsigned.read(name) == signed.read(name) for name in unsigned.namelist())
        report = {"scope": "real SDK 11/net10 trust, payload and negative candidates; no machine trust mutation",
                  "passed": True, "fingerprints": fingerprints, "results": results}
    except Exception as error:
        report = {"passed": False, "error": str(error), "results": results}
    finally:
        log.close()
    (EVIDENCE / "candidate-signing-sdk-probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "error": report.get("error"), "commands": len(results)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
