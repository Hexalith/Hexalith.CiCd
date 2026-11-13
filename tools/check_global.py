#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["Jinja2==3.1.6", "PyYAML==6.0.3", "jsonschema==4.26.0"]
# ///
"""Read-only global delivery checks, also shared by the future nightly bump."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
import http.client
import importlib.util
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


renderer = load_module("_cicd_global_renderer", Path(__file__).with_name("render.py"))
CheckError = renderer.RenderError
SHA = re.compile(r"[0-9a-f]{40}")
FAILURES = (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError, RecursionError, RuntimeError,
            subprocess.SubprocessError, http.client.HTTPException, renderer.SchemaError)


def log(message: object) -> None:
    # Each line is escaped separately: multi-line child output stays readable,
    # while every other control character remains escaped.
    for line in str(message).splitlines() or [""]:
        print(renderer.diagnostic(line), file=sys.stderr, flush=True)


def command(arguments, *, cwd=None, timeout=180, env=None):
    result = subprocess.run(list(map(str, arguments)), cwd=cwd, env=env,
                            capture_output=True, timeout=timeout, check=False)
    if result.returncode:
        raise CheckError(f"{Path(str(arguments[0])).name} exited {result.returncode}: "
                         f"{result.stdout.decode('utf-8', 'backslashreplace')}"
                         f"{result.stderr.decode('utf-8', 'backslashreplace')}")
    if result.stderr:
        log(result.stderr.decode('utf-8', 'backslashreplace').rstrip())
    return result.stdout


@contextmanager
def selected_contract(project: Path):
    """Fail the story 4-1 prerequisite before loading any perimeter reader."""
    tag = renderer.safe_path(project, "builds-version").read_text(encoding="utf-8").removesuffix("\n")
    if renderer.STABLE_TAG.fullmatch(tag) is None:
        raise CheckError("builds-version: expected one exact stable vMAJOR.MINOR.PATCH tag")
    builds = renderer.safe_path(project, "references/Hexalith.Builds")
    revision = renderer.git(builds, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}").decode().strip()
    paths = renderer.git(builds, "ls-tree", "-r", "--name-only", revision,
                         "--", "schemas", "Github/lib").decode().splitlines()
    if (not any(re.fullmatch(r"schemas/hexalith\.perimeter\.v[0-9]+\.json", path) for path in paths)
            or not {"Github/lib/perimeter.py", "Github/lib/perimeter_config.py"} <= set(paths)):
        raise CheckError(f"Builds {tag}: perimeter capability prerequisite failed: "
                         "release must contain story 4-1's schema, reader and library")
    with renderer.pinned_contract(project) as contract:
        contract.repository = builds
        yield contract


def check_render(project: Path, contract) -> None:
    registrations = renderer.registry(project)
    environment = renderer.templates(project)
    desired = renderer.desired_tree(project, registrations, environment, contract)
    repeated = renderer.desired_tree(project, registrations, environment, contract)
    if desired != repeated:
        raise CheckError("render reproducibility: repeated renders differ")
    output = renderer.safe_path(project, "rendered")
    actual, directories = renderer.existing_tree(output)
    desired[".gitkeep"] = actual.get(".gitkeep", b"")
    mismatches = {path for path in desired.keys() | actual.keys()
                  if desired.get(path) != actual.get(path)}
    mismatches |= directories - renderer.tree_directories(desired)
    for path in actual:
        if (output / path).stat().st_mode & 0o111:
            mismatches.add(path)
    if mismatches:
        raise CheckError("render differs: " + ", ".join(f"rendered/{path}" for path in sorted(mismatches)))


def check_committed_render(project: Path) -> None:
    """Compare only generated paths with HEAD, including blobs and Git modes."""
    output = renderer.safe_path(project, "rendered")
    actual, _ = renderer.existing_tree(output)
    committed = {}
    records = renderer.git(project, "ls-tree", "-r", "-z", "HEAD", "--", "rendered")
    for record in records.split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        mode, kind, oid = header.decode("ascii").split()
        path = raw_path.decode("utf-8").removeprefix("rendered/")
        if mode != "100644" or kind != "blob":
            raise CheckError(f"rendered/{path}: committed generated mode must be 100644 (found {mode})")
        committed[path] = renderer.git(project, "cat-file", "blob", oid)
    differences = {path for path in actual.keys() | committed.keys()
                   if actual.get(path) != committed.get(path)}
    differences |= {path for path in actual if (output / path).stat().st_mode & 0o111}
    if differences:
        raise CheckError("uncommitted rendered paths/bytes/modes: " + ", ".join(sorted(differences)))


def check_committed_inputs(project: Path) -> None:
    """The inputs that explain the render must belong to the candidate HEAD."""
    template_paths = {f"templates/{path}" for path in
                      (*renderer.TEMPLATES.values(), renderer.PERIMETER, *renderer.PARTIALS)}
    paths = {"builds-version", *template_paths,
             *(path.relative_to(project).as_posix() for _, path in renderer.registry(project))}
    committed = {}
    records = renderer.git(project, "ls-tree", "-r", "-z", "HEAD", "--", "builds-version", "setup", "templates")
    for record in records.split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        path = raw_path.decode("utf-8")
        if (path != "builds-version" and path not in template_paths
                and not (path.startswith("setup/") and path.count("/") == 1 and path.endswith(".yml"))):
            continue
        mode, kind, oid = header.decode("ascii").split()
        if mode not in ("100644", "100755") or kind != "blob":
            raise CheckError(f"{path}: committed render input must be a regular file")
        committed[path] = (mode, renderer.git(project, "cat-file", "blob", oid))
    actual = {}
    for relative in paths:
        path = renderer.safe_path(project, relative)
        if not path.is_file():
            raise CheckError(f"{relative}: render input must be a regular file")
        mode = "100755" if path.stat().st_mode & 0o111 else "100644"
        actual[relative] = (mode, path.read_bytes())
    differences = {path for path in actual.keys() | committed.keys() if actual.get(path) != committed.get(path)}
    if differences:
        raise CheckError("uncommitted render inputs: " + ", ".join(sorted(differences)))


def arguments_supplied(supplied: dict, declarations: dict, source: str) -> None:
    if not isinstance(supplied, dict) or not isinstance(declarations, dict):
        raise CheckError(f"{source}: expected explicit argument declarations and mapping")
    unknown = supplied.keys() - declarations.keys()
    required = {key for key, options in declarations.items() if options.get("required") is True}
    missing = required - supplied.keys()
    if unknown or missing:
        raise CheckError(f"{source}: unknown arguments {sorted(unknown)}; missing required arguments {sorted(missing)}")
    for key, value in supplied.items():
        declared_type = declarations[key].get("type")
        if declared_type is None or (isinstance(value, str) and "${{" in value):
            continue
        valid = {"string": isinstance(value, str), "boolean": type(value) is bool,
                 "number": type(value) in (int, float)}
        if declared_type not in valid or not valid[declared_type]:
            raise CheckError(f"{source}/{key}: literal value must have declared type {declared_type}")


def permission_union(document: dict) -> dict:
    union = {}
    ranks = {"none": 0, "read": 1, "write": 2}
    for job in document["jobs"].values():
        for scope, permission in job.get("permissions", document.get("permissions", {})).items():
            if permission not in ranks:
                raise CheckError(f"invalid pinned permission {scope}: {permission}")
            if ranks[permission] >= ranks.get(union.get(scope), -1):
                union[scope] = permission
    return union


def string_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from string_values(item)
    elif isinstance(value, str):
        yield value


def check_interfaces(project: Path, repository: str, contract) -> None:
    """Qualify actual caller arguments, outputs, permissions and every Builds ref."""
    prefix = "Hexalith/Hexalith.Builds/"
    manifests = {}
    for path in (".github/workflows/ci.yml", ".github/workflows/release.yml",
                 "Github/prepare/action.yml", "Github/publish/action.yml"):
        manifests[path] = renderer.yaml_document((contract.root / path).read_bytes(), f"Builds {contract.tag}/{path}")
    for filename in ("ci.yml", "release.yml"):
        source = f"rendered/{repository}/.github/workflows/{filename}"
        path = renderer.safe_path(project, source)
        document = renderer.yaml_document(path.read_bytes(), source)
        jobs = document["jobs"]
        outputs = {}
        for name, job in jobs.items():
            reference = job.get("uses", "")
            if reference:
                if not isinstance(reference, str) or not reference.startswith(prefix):
                    raise CheckError(f"{source}/{name}: expected a pinned Builds reusable workflow")
                target, separator, tag = reference[len(prefix):].partition("@")
                if not separator or tag != contract.tag or target not in manifests or not target.startswith(".github/workflows/"):
                    raise CheckError(f"{source}/{name}: inconsistent Builds workflow tag or unsupported callable {reference}")
                manifest = manifests[target]
                api = manifest["on"]["workflow_call"]
                arguments_supplied(job.get("with", {}), api.get("inputs", {}), f"{source}/{name}/with")
                arguments_supplied(job.get("secrets", {}), api.get("secrets", {}), f"{source}/{name}/secrets")
                if job.get("permissions", document.get("permissions", {})) != permission_union(manifest):
                    raise CheckError(f"{source}/{name}: caller permissions differ from pinned workflow permission union")
                outputs[name] = api.get("outputs", {})
            else:
                outputs[name] = job.get("outputs", {})
            for step in job.get("steps", []):
                reference = step.get("uses", "")
                if isinstance(reference, str) and reference.startswith(prefix):
                    target, separator, tag = reference[len(prefix):].partition("@")
                    manifest = target + "/action.yml"
                    if not separator or tag != contract.tag or manifest not in manifests:
                        raise CheckError(f"{source}/{name}: inconsistent Builds action tag or unsupported callable {reference}")
                    arguments_supplied(step.get("with", {}), manifests[manifest].get("inputs", {}),
                                       f"{source}/{name}/{target}/with")
        # Output references must name the declared output of the reusable job,
        # and their consumer must explicitly depend on that job.
        for name, job in jobs.items():
            serialized = "\n".join(string_values(job))
            serialized = re.sub(r"\[\s*(['\"])([A-Za-z0-9_-]+)\1\s*\]", r".\2", serialized)
            references = re.findall(r"\bneeds\s*\.\s*([A-Za-z0-9_-]+)\s*\.\s*outputs\s*\.\s*([A-Za-z0-9_-]+)", serialized)
            needs = job.get("needs", [])
            needs = [needs] if isinstance(needs, str) else needs
            for producer, output in references:
                if producer not in needs or output not in outputs.get(producer, {}):
                    raise CheckError(f"{source}/{name}: undeclared output reference needs.{producer}.outputs.{output}")


def check_documents(project: Path, registrations, contract) -> None:
    failures = []
    for repository, _ in registrations:
        try:
            source = f"rendered/{repository}/.github/hexalith-ci.json"
            config = contract.validate("ci", renderer.safe_path(project, source).read_bytes(), source, repository)
            if config["buildsTag"] != contract.tag:
                raise CheckError(f"{source}: buildsTag differs from builds-version")
            source = f"rendered/{repository}.perimeter.json"
            perimeter = contract.validate("perimeter", renderer.safe_path(project, source).read_bytes(), source)
            if any(entry.get("buildsTag", contract.tag) != contract.tag for entry in perimeter["entries"]):
                raise CheckError(f"{source}: perimeter gitlink tag differs from builds-version")
            check_interfaces(project, repository, contract)
        except FAILURES as error:
            failures.append(f"{repository}: {error}")
    if failures:
        raise CheckError("; ".join(failures))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        raise CheckError(f"GitHub API redirected (HTTP {code}); release remains unverified")


def github_api(path: str) -> dict:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise CheckError("GitHub API verification requires a read-only GITHUB_TOKEN or GH_TOKEN")
    request = urllib.request.Request("https://api.github.com/repos/Hexalith/Hexalith.Builds/" + path,
                                    headers={"Authorization": "Bearer " + token,
                                             "Accept": "application/vnd.github+json",
                                             "X-GitHub-Api-Version": "2022-11-28",
                                             "User-Agent": "Hexalith.CiCd-global-check"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
            data = response.read(2 * 1024 * 1024 + 1)
    except urllib.error.HTTPError as error:
        error.close()
        raise CheckError(f"GitHub API GET {path}: HTTP {error.code}; release remains unverified") from error
    if len(data) > 2 * 1024 * 1024:
        raise CheckError(f"GitHub API GET {path}: oversized response")
    document = renderer.json_document(data, f"GitHub API GET {path}")
    if not isinstance(document, dict):
        raise CheckError(f"GitHub API GET {path}: expected an object")
    return document


def git_object(document: dict, source: str) -> tuple[str, str]:
    value = document.get("object") if isinstance(document, dict) else None
    if not isinstance(value, dict):
        raise CheckError(f"{source}: invalid Git object")
    kind, sha = value.get("type"), value.get("sha")
    if kind not in ("commit", "tag") or not isinstance(sha, str) or SHA.fullmatch(sha) is None:
        raise CheckError(f"{source}: invalid Git object")
    return kind, sha


def check_release(contract, api=None) -> None:
    api = github_api if api is None else api
    def read(path):
        document = api(path)
        if not isinstance(document, dict):
            raise CheckError(f"GitHub API GET {path}: expected an object")
        return document
    tag = contract.tag
    release = read("releases/tags/" + urllib.parse.quote(tag, safe=""))
    author = release.get("author")
    published = release.get("published_at")
    if (release.get("tag_name") != tag or release.get("draft") is not False
            or release.get("immutable") is not True or not isinstance(published, str)
            or not published or not isinstance(author, dict) or author.get("login") != "github-actions[bot]"):
        raise CheckError(f"Builds {tag}: release must be published, immutable and authored by github-actions[bot]")
    try:
        if datetime.fromisoformat(published).tzinfo is None:
            raise ValueError("missing timezone")
    except ValueError as error:
        raise CheckError(f"Builds {tag}: malformed published_at timestamp") from error
    reference = read("git/ref/tags/" + tag)
    if reference.get("ref") != "refs/tags/" + tag:
        raise CheckError(f"Builds {tag}: remote tag ref mismatch")
    kind, sha = git_object(reference, f"Builds {tag}")
    local = renderer.git(contract.repository, "rev-parse", "--verify", "refs/tags/" + tag).decode().strip()
    if sha != local:
        raise CheckError(f"Builds {tag}: remote/local tag-object mismatch")
    seen = set()
    while kind == "tag":
        if sha in seen or len(seen) >= 16:
            raise CheckError(f"Builds {tag}: annotated-tag cycle or excessive depth")
        seen.add(sha)
        annotated = read("git/tags/" + sha)
        if annotated.get("sha") != sha:
            raise CheckError(f"Builds {tag}: annotated tag-object mismatch")
        kind, sha = git_object(annotated, f"Builds {tag}")
    if sha != contract.revision:
        raise CheckError(f"Builds {tag}: remote/local peeled commit mismatch")
    main = read("git/ref/heads/main")
    if main.get("ref") != "refs/heads/main":
        raise CheckError("Builds live main: remote ref mismatch")
    kind, main_sha = git_object(main, "Builds live main")
    if kind != "commit":
        raise CheckError("Builds live main must name a commit")
    # Changed files appear only on the first page. A later page keeps status
    # and merge base, so a long gap cannot exceed the bounded response size.
    comparison = read(f"compare/{sha}...{main_sha}?per_page=1&page=2")
    base, merge_base = comparison.get("base_commit"), comparison.get("merge_base_commit")
    if (comparison.get("status") not in ("ahead", "identical")
            or not isinstance(base, dict) or base.get("sha") != sha
            or not isinstance(merge_base, dict) or merge_base.get("sha") != sha):
        raise CheckError(f"Builds {tag}: release commit is not a verified ancestor of live main")


def run_tool_tests(project: Path) -> None:
    suites = sorted(renderer.safe_path(project, "tools/tests").glob("test_*.py"))
    if not suites:
        raise CheckError("tool tests: no suites found")
    failures = []
    for suite in suites:
        try:
            output = command(["uv", "run", "--locked", "--script", "--python", sys.executable, suite],
                             cwd=project, timeout=600)
            if output:
                log(output.decode("utf-8", "backslashreplace").rstrip())
        except FAILURES as error:
            failures.append(str(error))
    if failures:
        raise CheckError("; ".join(failures))


def workflow_paths(project: Path) -> list[str]:
    paths = []
    for directory in (renderer.safe_path(project, ".github/workflows"),):
        if directory.exists():
            for path in directory.iterdir():
                if path.suffix in (".yml", ".yaml"):
                    paths.append(path.relative_to(project).as_posix())
    paths += [path.relative_to(project).as_posix()
              for suffix in ("yml", "yaml")
              for path in renderer.safe_path(project, "rendered").glob(f"*/.github/workflows/*.{suffix}")]
    for path in paths:
        target = renderer.safe_path(project, path)
        if not target.is_file():
            raise CheckError(f"{path}: workflow must be a regular file")
    if not paths:
        raise CheckError("lint: no explicit workflow paths found")
    return sorted(set(paths))


def lint_workflows(project: Path, contract) -> None:
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "AMD64"):
        raise CheckError("Pinned linter archives target Linux x86_64")
    if any(os.environ.get(key) for key in ("ZIZMOR_OFFLINE", "ZIZMOR_NO_ONLINE_AUDITS")):
        raise CheckError("Online zizmor audits are required; remove offline overrides")
    if not any(os.environ.get(key) for key in ("GITHUB_TOKEN", "GH_TOKEN", "ZIZMOR_GITHUB_TOKEN")):
        raise CheckError("Online audits require a read-only GitHub token")
    paths = workflow_paths(project)
    installer = load_module("_cicd_tagged_linter_installer", contract.root / "Tools/ci/lint_workflows.py")
    pins = renderer.json_document((contract.root / "Tools/ci/tools.json").read_bytes(), "tagged tool pins")
    with tempfile.TemporaryDirectory(prefix="hexalith-global-lint-") as directory:
        binaries = {}
        for name in ("actionlint", "zizmor"):
            try:
                binaries[name] = installer.install_tool(name, pins[name], Path(directory))
            except FAILURES as error:
                raise CheckError(f"{name}: pinned tool installation failed: {error}") from error
        output = command([binaries["actionlint"], "-shellcheck=", "-pyflakes=", "-config-file",
                          project / "tools/actionlint.yaml", *paths], cwd=project)
        if output:
            log(output.decode("utf-8", "backslashreplace").rstrip())
        result = subprocess.run([str(binaries["zizmor"]), "--strict-collection", "--no-progress", "--format=json",
                                 "--config", str(project / "tools/zizmor.yml"), *paths], cwd=project,
                                capture_output=True, timeout=300, check=False)
        if result.stderr:
            log(result.stderr.decode("utf-8", "backslashreplace").rstrip())
        if result.returncode not in (0, 11, 12, 13, 14):
            raise CheckError(f"zizmor failed/incomplete scan (exit {result.returncode})")
        findings = renderer.json_document(result.stdout, "zizmor result")
        if not isinstance(findings, list):
            raise CheckError("zizmor did not return a complete JSON finding list")
        if any(not isinstance(item, dict) or type(item.get("ignored")) is not bool
               or not isinstance(item.get("ident"), str) or not isinstance(item.get("desc"), str)
               for item in findings):
            raise CheckError("zizmor returned malformed findings")
        failures = [item for item in findings if not item["ignored"]]
        for finding in failures:
            log(f"zizmor {finding['ident']}: {finding['desc']}")
        if failures or result.returncode:
            raise CheckError(f"zizmor reported {len(failures)} findings (exit {result.returncode})")
        log(f"actionlint {pins['actionlint']['version']} and zizmor {pins['zizmor']['version']}: "
            f"{len(paths)} explicit workflows passed online audits")


def run(project: Path) -> bool:
    project = project.resolve()
    failures = []

    def check(label, callback):
        try:
            callback()
            log(f"global {label}: passed")
        except FAILURES as error:
            failures.append(label)
            log(f"global {label}: {error}")

    check("committed render inputs", lambda: check_committed_inputs(project))
    check("committed render", lambda: check_committed_render(project))
    try:
        with selected_contract(project) as contract:
            check("render reproducibility", lambda: check_render(project, contract))
            check("schemas and caller interfaces", lambda: check_documents(project, renderer.registry(project), contract))
            check("acceptable Builds publication", lambda: check_release(contract))
            check("workflow lints", lambda: lint_workflows(project, contract))
    except FAILURES as error:
        failures.append("selected contract")
        log(f"global selected contract/prerequisite: {error}")
    check("tool suites", lambda: run_tool_tests(project))
    return not failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        log("Python 3.12 or later is required")
        return 1
    return int(not run(args.project_root))


if __name__ == "__main__":
    raise SystemExit(main())
