#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Secretless, bounded live-main cross-module duplicate scan."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import delivery_runtime as rt
from scan_discovery import Discovery, FORMATS

SCHEMA = "hexalith.duplicate-scan.v1"
MAX_REPORT = 16 * 1024 * 1024
MAX_EXPORT = 128 * 1024 * 1024
MAX_FINDINGS = 1000
VERSION = "5.4.3"


def read_json(data):
    if len(data) > MAX_REPORT:
        raise rt.DeliveryError("detector report exceeds 16 MiB limit")
    # Reuse the strict duplicate-key/constant decoder, with its conservative
    # 2 MiB cap removed only for the bounded detector report.
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise rt.DeliveryError("duplicate detector JSON key")
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError):
        raise rt.DeliveryError("invalid detector JSON") from None


class Detector:
    """All installation, package configuration and output lives in scratch."""
    def __init__(self, git, revision, scratch, *, path=None):
        self.root = Path(scratch) / "detector"
        self.root.mkdir(mode=0o700)
        self.tool_path = path or os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")
        self.env = {"PATH": self.tool_path, "HOME": str(self.root / "home"),
                    "TMPDIR": str(scratch), "TMP": str(scratch), "TEMP": str(scratch),
                    "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "CI": "true",
                    "NPM_CONFIG_USERCONFIG": str(self.root / "user.npmrc"),
                    "NPM_CONFIG_GLOBALCONFIG": str(self.root / "global.npmrc"),
                    "NPM_CONFIG_CACHE": str(self.root / "cache"), "JSCPD_NO_TIPS": "1"}
        for target in ("package.json", "package-lock.json"):
            (self.root / target).write_bytes(git.blob(revision, "tools/jscpd/" + target))
        config = git.blob(revision, ".jscpd.json")
        self.policy = rt.json_read(config)
        if (not isinstance(self.policy, dict)
                or self.policy.get("format") != ["yaml", "bash", "powershell", "python"]
                or self.policy.get("skipLocal") is not True or self.policy.get("noGitignore") is not True
                or self.policy.get("absolute") is not True
                or self.policy.get("reporters") != ["json"]
                or any(k in self.policy for k in ("ignore", "ignorePattern", "threshold", "baseline", "pattern"))):
            raise rt.DeliveryError("invalid central detector policy")
        self.config = self.root / "policy.json"
        self.config.write_bytes(config)
        self.policy_sha256 = hashlib.sha256(config).hexdigest()
        package = rt.json_read((self.root / "package.json").read_bytes())
        lock = rt.json_read((self.root / "package-lock.json").read_bytes())
        if (package.get("dependencies") != {"jscpd": VERSION} or lock.get("lockfileVersion") != 3
                or lock.get("packages", {}).get("node_modules/jscpd", {}).get("version") != VERSION):
            raise rt.DeliveryError("detector manifest/lock version mismatch")
        for key, value in lock.get("packages", {}).items():
            if key and (not isinstance(value.get("integrity"), str)
                        or not value["integrity"].startswith("sha512-")
                        or not value.get("resolved", "").startswith("https://registry.npmjs.org/")):
                raise rt.DeliveryError("detector dependency lacks registry integrity pin")
        self.npm = shutil.which("npm", path=self.tool_path)
        if not self.npm:
            raise rt.DeliveryError("npm unavailable")
        self.run([self.npm, "ci", "--ignore-scripts", "--no-fund", "--no-audit"], "npm locked install", 180)
        self.run([self.npm, "audit", "signatures"], "npm signature verification", 180)
        self.binary = self.root / "node_modules/.bin/jscpd"
        version = self.run([str(self.binary), "--version"], "detector version verification", 20).decode().strip()
        if version != "jscpd " + VERSION:
            raise rt.DeliveryError("detector reported unexpected version")

    def run(self, command, operation, timeout):
        with tempfile.TemporaryFile(dir=self.root) as out, tempfile.TemporaryFile(dir=self.root) as err:
            try:
                result = subprocess.run(command, cwd=self.root, env=self.env, stdout=out, stderr=err,
                                        timeout=timeout)
            except (OSError, subprocess.TimeoutExpired):
                raise rt.DeliveryError(operation + " failed or timed out") from None
            out.seek(0)
            err.seek(0)
            data, diagnostic = out.read(MAX_REPORT + 1), err.read(MAX_REPORT + 1)
            if len(data) > MAX_REPORT or len(diagnostic) > MAX_REPORT:
                raise rt.DeliveryError(operation + " output limit exceeded")
            if result.returncode:
                # npm/git/module diagnostics can contain arbitrary source or
                # inherited credentials; report only the named failed boundary.
                raise rt.DeliveryError(operation + " failed (exit " + str(result.returncode) + ")")
            return data

    def detect(self, roots):
        destination = self.root / "result"
        self.run([str(self.binary), *map(str, roots), "--config", str(self.config), "--output", str(destination)],
                 "duplicate detector", 600)
        report = destination / "jscpd-report.json"
        if report.is_symlink() or not report.is_file() or report.stat().st_size > MAX_REPORT:
            raise rt.DeliveryError("detector report missing or oversized")
        return read_json(report.read_bytes())


def findings(value, manifest):
    if (not isinstance(value, dict) or not isinstance(value.get("duplicates"), list)
            or not isinstance(value.get("statistics"), dict)
            or not isinstance(value["statistics"].get("formats"), dict)
            or not isinstance(value["statistics"].get("total"), dict)):
        raise rt.DeliveryError("unsupported/incomplete detector report")
    if len(value["duplicates"]) > MAX_FINDINGS:
        raise rt.DeliveryError("detector finding limit exceeded")
    statistics = value["statistics"]
    total = statistics["total"]
    counters = ("sources", "clones", "lines", "tokens", "duplicatedLines", "duplicatedTokens")
    if (any(type(total.get(key)) is not int or total[key] < 0 for key in counters)
            or total["sources"] > len(manifest) or total["clones"] != len(value["duplicates"])):
        raise rt.DeliveryError("incomplete detector statistics")
    for fmt, counters_by_format in statistics["formats"].items():
        if (fmt not in set(FORMATS.values()) or not isinstance(counters_by_format, dict)
                or any(type(counters_by_format.get(key)) is not int or counters_by_format[key] < 0 for key in counters)):
            raise rt.DeliveryError("unsupported/incomplete detector format statistics")
    if sum(row["sources"] for row in statistics["formats"].values()) != total["sources"]:
        raise rt.DeliveryError("inconsistent detector source statistics")
    result, seen = [], set()
    for duplicate in value["duplicates"]:
        if (not isinstance(duplicate, dict) or duplicate.get("format") not in set(FORMATS.values())
                or not isinstance(duplicate.get("fragment"), str) or not duplicate["fragment"]
                or any(type(duplicate.get(k)) is not int or duplicate[k] <= 0 for k in ("lines", "tokens"))):
            raise rt.DeliveryError("invalid detector fragment metadata")
        endpoints, originals = [], []
        for key in ("firstFile", "secondFile"):
            source = duplicate.get(key)
            if not isinstance(source, dict) or not isinstance(source.get("name"), str):
                raise rt.DeliveryError("invalid detector endpoint")
            raw = source["name"]
            path = Path(raw)
            if (not path.is_absolute() or str(path) != raw or ".." in path.parts
                    or raw not in manifest or path.is_symlink()):
                raise rt.DeliveryError("detector endpoint is not a staged known source")
            item = manifest[raw]
            start, end = source.get("start"), source.get("end")
            lines = item["text"].splitlines()
            if (type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines)
                    or item["format"] != duplicate["format"]):
                raise rt.DeliveryError("detector source range/format mismatch")
            for location, number in (("startLoc", start), ("endLoc", end)):
                if (not isinstance(source.get(location), dict) or source[location].get("line") != number
                        or any(type(source[location].get(k)) is not int or source[location][k] < 0 for k in ("column", "position"))):
                    raise rt.DeliveryError("incomplete detector source locations")
            endpoints.append({"module": item["module"], "path": item["path"], "start": start, "end": end})
            originals.append("\n".join(lines[start - 1:end]))
        if endpoints[0]["module"] == endpoints[1]["module"]:
            # Controller policy is authoritative even if the engine changes
            # skipLocal semantics: within-module repetition never fails.
            continue
        ordered = sorted(zip(endpoints, originals), key=lambda row: (row[0]["module"], row[0]["path"], row[0]["start"]))
        identity = json.dumps([row[0] for row in ordered], sort_keys=True)
        if identity in seen:
            continue
        seen.add(identity)
        result.append({"format": duplicate["format"], "lines": duplicate["lines"], "tokens": duplicate["tokens"],
                       "first": ordered[0][0], "second": ordered[1][0], "fragment": ordered[0][1]})
    return sorted(result, key=lambda row: json.dumps(row, sort_keys=True))


def summary(report):
    lines = ["# Nightly cross-module duplicate scan: " + report["result"].upper(), "",
             "Detector: jscpd " + VERSION + ". Cross-module copies belong in Builds.", ""]
    for module in report["modules"]:
        lines.append(f"- {module['module']}: {module['result']}; main `{module['revision'] or 'unavailable'}`; "
                     f"{len(module['files'])} selected files")
        lines.extend("  - " + error for error in module["errors"])
    if not report["modules"]:
        lines.append("Empty committed registry: successful zero scope." if not report["errors"] else "Registry unavailable.")
    elif not any(module["files"] for module in report["modules"]) and not report["errors"] and all(
            module["result"] == "pass" for module in report["modules"]):
        lines.append("Registered modules have no supported action sources: successful zero scope.")
    lines.extend("- ERROR: " + error for error in report["errors"])
    for row in report["findings"]:
        lines.extend(["", "## Code to move to Builds", ""])
        for key in ("first", "second"):
            endpoint = row[key]
            lines.append(f"- {endpoint['module']}/{endpoint['path']}:{endpoint['start']}-{endpoint['end']}")
        # Indentation makes all module text inert Markdown, including backticks
        # and HTML. Exact original source also survives in report.json.
        lines.extend(["", *["    " + line for line in row["fragment"].splitlines()]])
    if not report["findings"]:
        lines.extend(["", "No cross-module copies observed in the selected scope." if report["result"] == "pass"
                      else "Coverage is incomplete; this result does not establish a clean scan."])
    return "\n".join(lines) + "\n"


def persist(directory, report):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    data = (json.dumps(report, sort_keys=True, ensure_ascii=True, indent=2) + "\n").encode()
    rendered = summary(report).encode()
    if len(data) > MAX_REPORT or len(rendered) > MAX_REPORT:
        raise rt.DeliveryError("scan report/summary size limit exceeded")
    for name, content in (("report.json", data), ("summary.md", rendered)):
        destination = directory / name
        temporary = directory / (name + ".writing")
        temporary.write_bytes(content)
        temporary.replace(destination)


def scan(project, directory, *, transport=None, git_factory=rt.Git, detector_factory=Detector):
    project, directory = Path(project).resolve(), Path(directory).resolve()
    report = {"schema": SCHEMA, "result": "fail", "controllerRevision": "", "modules": [], "findings": [],
              "errors": ["scan initialization incomplete"],
              "detector": {"name": "jscpd", "version": VERSION, "signatures": "unverified"}, "policy": {}}
    persist(directory, report)
    report["errors"] = []
    try:
        trusted = git_factory(project)
        revision = trusted.resolve("HEAD^{commit}")
        report["controllerRevision"] = revision
        modules = rt.registry(trusted, revision)
        if len(modules) > rt.CAPACITY:
            raise rt.DeliveryError("committed registry exceeds 17-module capacity")
        with tempfile.TemporaryDirectory(prefix="hexalith-duplicate-scan-") as temporary:
            scratch = Path(temporary)
            manifest, roots, total = {}, [], 0
            for index, module in enumerate(modules):
                row = {"module": module, "revision": "", "result": "fail", "files": [], "errors": []}
                report["modules"].append(row)
                try:
                    git = git_factory(scratch / "git" / str(index))
                    git.init()
                    row["revision"] = rt.sha((transport or rt.Transport()).module(git, module))
                    selected, row["errors"] = Discovery(git, row["revision"]).discover()
                    root = scratch / "sources" / module
                    for path, item in sorted(selected.items()):
                        data = item["text"].encode()
                        total += len(data)
                        if total > MAX_EXPORT:
                            raise rt.DeliveryError("aggregate selected-source limit exceeded")
                        # Source directives never override central policy. Keep
                        # byte length and source coordinates identical.
                        staged = item["text"].replace("jscpd:ignore", "jscpd:allow_")
                        # A unique flat staged name prevents a literal source
                        # such as helper and helper.sh from overwriting each
                        # other when the shebang-only source needs an extension.
                        extension = {"yaml": ".yml", "bash": ".sh", "python": ".py", "powershell": ".ps1"}[item["format"]]
                        target = root / (str(len(row["files"])) + extension)
                        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                        target.write_text(staged, encoding="utf-8")
                        manifest[str(target)] = item | {"module": module, "path": path}
                        row["files"].append({"path": path, "format": item["format"], "sha256": hashlib.sha256(data).hexdigest()})
                    if selected:
                        roots.append(root)
                    row["result"] = "fail" if row["errors"] else "pass"
                except Exception as error:
                    row["errors"].append(rt.clean(error))
            # Verify tools/config even for zero scope, so unavailable installation
            # cannot be presented as a successful scan. No detector invocation is
            # needed for empty roots (jscpd otherwise scans its cwd).
            try:
                detector = detector_factory(trusted, revision, scratch)
                report["policy"] = detector.policy
                report["detector"].update({"signatures": "verified", "policySha256": detector.policy_sha256})
                if roots:
                    report["findings"] = findings(detector.detect(roots), manifest)
            except Exception as error:
                report["errors"].append(rt.clean(error))
        report["result"] = "fail" if (report["errors"] or report["findings"] or any(
            module["result"] != "pass" for module in report["modules"])) else "pass"
    except Exception as error:
        report["errors"].append(rt.clean(error))
    try:
        persist(directory, report)
    except Exception:
        report["result"] = "fail"
        report["errors"].append("report generation failed; detailed observations exceeded output bounds")
        report["findings"] = []
        for module in report["modules"]:
            module["files"] = []
        persist(directory, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=os.environ.get("SCAN_DIRECTORY"))
    args = parser.parse_args(argv)
    if args.output is None:
        parser.error("--output or SCAN_DIRECTORY is required")
    report = scan(args.project_root, args.output)
    print("Nightly duplicate scan: " + report["result"].upper())
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
