#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Secretless, bounded live-main cross-module duplicate scan."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import yaml

import delivery_runtime as rt
from scan_discovery import ActionLoader, Discovery, FORMATS

SCHEMA = "hexalith.duplicate-scan.v1"
MAX_REPORT = 16 * 1024 * 1024
MAX_EXPORT = 128 * 1024 * 1024
MAX_FINDINGS = 1000
VERSION = "5.4.3"
TYPESCRIPT_VERSION = "6.0.3"
# A located discovery error is "path:line: diagnostic". Only Python sources get
# statement digests: other files can hold embedded code whose line numbers use
# another split, and these separators make Python line numbering ambiguous.
LOCATED = re.compile(r"([1-9][0-9]*): (.*)\Z", re.S)
AMBIGUOUS_BREAK = re.compile("\r(?!\n)|[\x85\u2028\u2029]")
CALLER_LINE = re.compile(r"\bline ([0-9]+)\b")
# Diagnostics that stop discovery of a whole file, or of everything past a
# coverage limit, name no single site and are never located gaps.
WHOLE_FILE = ("invalid Python source", "discovery failed: ", "invalid action/discovery: ")
COMPOUND = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.If, ast.For, ast.AsyncFor, ast.While,
            ast.With, ast.AsyncWith, ast.Try, ast.TryStar, ast.Match)


class ScanTransport(rt.Transport):
    """Fetch committed dependencies for static scanning."""

    def pinned_source(self, git, repository, revision):
        repository, revision = rt.name(repository), rt.sha(revision)
        self.configure(git, repository)
        git.run("fetch", "--depth=1", "--filter=blob:none", "--no-tags", "--no-recurse-submodules",
                self.remote(repository), revision)
        if git.resolve("FETCH_HEAD^{commit}") != revision:
            raise rt.DeliveryError("pinned source revision mismatch")


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
        (self.root / "discover.cjs").write_bytes(git.blob(revision, "tools/jscpd/discover.cjs"))
        config = git.blob(revision, ".jscpd.json")
        self.policy = rt.json_read(config)
        if (not isinstance(self.policy, dict)
                or self.policy.get("format") != ["yaml", "bash", "powershell", "python", "javascript", "typescript"]
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
        if (package.get("dependencies") != {"jscpd": VERSION, "typescript": TYPESCRIPT_VERSION} or lock.get("lockfileVersion") != 3
                or lock.get("packages", {}).get("node_modules/jscpd", {}).get("version") != VERSION
                or lock.get("packages", {}).get("node_modules/typescript", {}).get("version") != TYPESCRIPT_VERSION):
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

    def javascript(self, path, text):
        """Parse trusted syntax in scratch, with module input only on stdin."""
        node = shutil.which("node", path=self.tool_path)
        if not node:
            raise rt.DeliveryError("Node unavailable for trusted TypeScript parser")
        try:
            result = subprocess.run([node, str(self.root / "discover.cjs")], cwd=self.root, env=self.env,
                                    input=json.dumps({"path": path, "text": text}),
                                    text=True, capture_output=True, timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise rt.DeliveryError("trusted TypeScript parser failed or timed out") from None
        if result.returncode or len(result.stdout.encode()) > MAX_REPORT or len(result.stderr.encode()) > MAX_REPORT:
            raise rt.DeliveryError("trusted TypeScript parser failed or exceeded output limit")
        parsed = read_json(result.stdout)
        if not isinstance(parsed, dict) or set(parsed) != {"imports", "literals", "commands", "errors"}:
            raise rt.DeliveryError("unsupported trusted TypeScript parser output")
        return parsed

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
            # jscpd counts only LF line breaks; str.splitlines also splits on
            # form feeds, Unicode separators and lone CR, shifting the slice.
            lines = item["text"].split("\n")
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


def statements(item):
    """A Python source's statements as (first line, last line, node), or None without a syntax tree."""
    if item["format"] != "python" or AMBIGUOUS_BREAK.search(item["text"]):
        return None
    try:
        tree = ast.parse(item["text"].removeprefix("\ufeff"))
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return None
    def first(node):
        return min([node.lineno, *(decorator.lineno for decorator in getattr(node, "decorator_list", ()))])
    return [(first(node), node.end_lineno, node) for node in ast.walk(tree) if isinstance(node, ast.stmt)]


def statement_span(nodes, line):
    """The first and last line of the innermost statement holding ``line``, or None.

    A compound statement contributes only its header when the line is there,
    and its whole extent for any other line it holds, such as an except clause.
    """
    holding = [(first, last, node) for first, last, node in nodes or () if first <= line <= last]
    if not holding:
        return None
    first, last, node = max(holding, key=lambda item: (item[0], -item[1]))
    if isinstance(node, COMPOUND):
        inner = node.cases[0].pattern if isinstance(node, ast.Match) else node.body[0]
        start = min([inner.lineno, *(decorator.lineno for decorator in getattr(inner, "decorator_list", ()))])
        if line < start:
            last = max(line, start - 1)
    return first, last


def error_sources(errors, selected, *, complete=True):
    """Each error's selected source location and statement digests, in error order.

    An entry is None unless the error names exactly one selected source as
    ``path:line: diagnostic``; an incomplete discovery has no located errors.
    ``span`` is the reported statement's first and last line, and ``lineSha256``
    the SHA-256 of those LF-split lines' exact UTF-8 bytes, joined by LF. Each
    ``line N`` the diagnostic names is a caller in the same source, with its
    own statement span and digest. ``lineSha256`` is None outside Python
    sources, for a whole-file or coverage-limit diagnostic, and when a statement
    is unknown. Module acceptance compares these with recorded coverage gaps.
    """
    result, parsed = [], {}
    for error in errors:
        entry = None
        located = [(path, match) for path in selected if complete and isinstance(error, str)
                   and error.startswith(path + ":") and (match := LOCATED.match(error, len(path) + 1))]
        if len(located) == 1:
            path, match = located[0]
            line, diagnostic, item = int(match[1]), match[2], selected[path]
            if path not in parsed:
                parsed[path] = statements(item)
            # A final LF ends the last line; it does not start another one.
            lines = item["text"].removesuffix("\n").split("\n")
            def site(number):
                span = statement_span(parsed[path], number) if number <= len(lines) else None
                if span is None:
                    return None, None
                return list(span), hashlib.sha256("\n".join(lines[span[0] - 1:span[1]]).encode()).hexdigest()
            span, digest = site(line)
            callers = [dict(zip(("line", "span", "sha256"), (number, *site(number))))
                       for number in map(int, CALLER_LINE.findall(diagnostic))]
            if (diagnostic.startswith(WHOLE_FILE) or "limit exceeded" in diagnostic
                    or any(caller["sha256"] is None for caller in callers)):
                digest = None
            entry = {"path": path, "line": line, "span": span, "diagnostic": diagnostic, "lineSha256": digest,
                     "callers": callers}
        result.append(entry)
    return result


def summary(report):
    lines = ["# Nightly cross-module duplicate scan: " + report["result"].upper(), "",
             "Detector: jscpd " + VERSION + ". Cross-module copies belong in Builds.", ""]
    for module in report["modules"]:
        observations = module.get("observations", [])
        boundary = (f"; {len(observations)} test boundary observation{'' if len(observations) == 1 else 's'}"
                    if observations else "")
        lines.append(f"- {module['module']}: {module['result']}; main `{module['revision'] or 'unavailable'}`; "
                     f"{len(module['files'])} selected files{boundary}")
        lines.extend("  - " + error for error in module["errors"])
        lines.extend(f"  - boundary: {item['path']}:{item['line']}: {item['reason']}" for item in observations)
    if not report["modules"]:
        lines.append("Empty committed registry: successful zero scope." if not report["errors"]
                     else "No registered module was scanned.")
    elif not any(module["files"] for module in report["modules"]) and not report["errors"] and all(
            module["result"] == "pass" for module in report["modules"]):
        lines.append("Registered modules have no supported action sources: successful zero scope.")
    lines.extend("- ERROR: " + error for error in report["errors"])
    for row in report["findings"]:
        lines.extend(["", "## Code to move to Builds", ""])
        for key in ("first", "second"):
            endpoint = row[key]
            lines.append(f"- {endpoint['module']}/{endpoint['path']}:{endpoint['start']}-{endpoint['end']}")
        # A top-level fence longer than any backtick run in the fragment keeps
        # module text inert; indentation after a list item would render it as
        # list Markdown. Exact original source also survives in report.json.
        fence = "`" * max(3, 1 + max((len(run) for run in re.findall(r"`+", row["fragment"])), default=0))
        lines.extend(["", fence + row["format"], *row["fragment"].split("\n"), fence])
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


class PinnedSources:
    """Acquire only direct gitlinks authorized by the controller's module setup."""

    def __init__(self, trusted, controller, module, git, revision, scratch, transport, git_factory):
        self.trusted, self.controller, self.module = trusted, controller, module
        self.git, self.revision = git, revision
        self.scratch, self.transport, self.git_factory = scratch, transport, git_factory
        self.acquired = {}

    def __call__(self, path, revision):
        parts = path.split("/")
        if len(parts) != 2 or parts[0] != "references":
            raise rt.DeliveryError("unsupported pinned source root: " + rt.clean(path))
        repository = rt.name(parts[1])
        setup_path = "setup/" + self.module + ".yml"
        try:
            setup = yaml.load(self.trusted.blob(self.controller, setup_path), Loader=ActionLoader)
        except (yaml.YAMLError, UnicodeError, RecursionError) as error:
            raise rt.DeliveryError("invalid pinned source setup: " + rt.clean(error)) from None
        allowed = setup.get("submodules") if isinstance(setup, dict) else None
        if not isinstance(allowed, list) or allowed.count(path) != 1:
            raise rt.DeliveryError("pinned source not authorized by committed setup: " + rt.clean(path))

        item = self.git.items(self.revision, ".gitmodules").get(".gitmodules")
        if item is None or item[:2] not in (("100644", "blob"), ("100755", "blob")):
            raise rt.DeliveryError("missing regular committed .gitmodules declaration")
        # Ask Git to apply its own config grammar to the blob, without includes.
        self.git.blob(self.revision, ".gitmodules")
        config = self.git.run("config", "--blob", item[2], "--no-includes", "--null", "--list").decode()
        entries = [entry.split("\n", 1) for entry in config.split("\0") if entry]
        paths = [key.removesuffix(".path") for key, *value in entries
                 if key.startswith("submodule.") and key.endswith(".path") and value == [path]]
        if len(paths) != 1 or any(key.startswith(("include.", "includeif.")) for key, *_ in entries):
            raise rt.DeliveryError("missing or ambiguous committed submodule declaration: " + rt.clean(path))
        section = paths[0]
        declared = [value for key, *value in entries if key == section + ".path"]
        urls = [value for key, *value in entries if key == section + ".url"]
        if declared != [[path]] or urls != [[rt.Transport().remote(repository)]]:
            raise rt.DeliveryError("submodule declaration origin or path mismatch: " + rt.clean(path))

        git = self.git_factory(self.scratch / str(len(self.acquired)))
        git.init()
        self.transport.pinned_source(git, repository, revision)
        source = git.resolve(revision + "^{commit}")
        if source != revision:
            raise rt.DeliveryError("pinned source revision mismatch")
        self.acquired[path] = {"repository": repository, "revision": source}
        return git


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
        transport = transport or ScanTransport()
        with tempfile.TemporaryDirectory(prefix="hexalith-duplicate-scan-") as temporary:
            scratch = Path(temporary)
            manifest, roots, total = {}, [], 0
            detector = None
            try:
                detector = detector_factory(trusted, revision, scratch)
                report["policy"] = detector.policy
                report["detector"].update({"signatures": "verified", "policySha256": detector.policy_sha256})
            except Exception as error:
                report["errors"].append(rt.clean(error))
            for index, module in enumerate(modules):
                row = {"module": module, "revision": "", "result": "fail", "files": [], "errors": [], "errorSources": [],
                       "observations": []}
                report["modules"].append(row)
                try:
                    git = git_factory(scratch / "git" / str(index))
                    git.init()
                    row["revision"] = rt.sha(transport.module(git, module))
                    pinned = PinnedSources(trusted, revision, module, git, row["revision"],
                                           scratch / "pins" / str(index), transport, git_factory)
                    discovery = Discovery(git, row["revision"], javascript_parser=getattr(detector, "javascript", None),
                                          pinned_source=pinned, module=module)
                    selected, row["errors"] = discovery.discover()
                    # Test boundary sites record coverage loss without failing the row.
                    row["observations"] = discovery.observations
                    # A coverage limit or a failed pinned-source acquisition
                    # leaves discovery incomplete: none of its errors is located.
                    complete = (getattr(discovery, "exhausted", True) is False
                                and not getattr(discovery, "pin_errors", True))
                    row["errorSources"] = error_sources(row["errors"], selected, complete=complete)
                    if pinned.acquired:
                        row["pinnedSources"] = pinned.acquired
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
                        extension = {"yaml": ".yml", "bash": ".sh", "python": ".py", "powershell": ".ps1",
                                     "javascript": ".js", "typescript": ".ts"}[item["format"]]
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
                    # A failure outside discovery leaves no error of the row located.
                    row["errorSources"] = [None] * len(row["errors"])
            # Verify tools/config even for zero scope, so unavailable installation
            # cannot be presented as a successful scan. No detector invocation is
            # needed for empty roots (jscpd otherwise scans its cwd).
            try:
                if roots and detector is not None:
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
            module["observations"] = []
            module["errorSources"] = [None] * len(module["errors"])
        persist(directory, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=os.environ.get("SCAN_DIRECTORY") or None)
    args = parser.parse_args(argv)
    if args.output is None:
        parser.error("--output or SCAN_DIRECTORY is required")
    report = scan(args.project_root, args.output)
    print("Nightly duplicate scan: " + report["result"].upper())
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
