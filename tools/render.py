#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["Jinja2==3.1.6", "PyYAML==6.0.3", "jsonschema==4.26.0"]
# ///
"""Materialize the setup registry using only the locally pinned Builds Git objects.

Run with uv run --locked --script tools/render.py [--check]. No module checkout,
remote service, or implicit configuration source participates in rendering.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
from dataclasses import dataclass
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any, Iterator

from jinja2 import DictLoader, Environment, StrictUndefined, TemplateError, Undefined
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Registry
from referencing.exceptions import NoSuchResource, Unresolvable
import yaml


ROOT = Path(__file__).resolve().parents[1]
STABLE_TAG = re.compile(r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
REPOSITORY = re.compile(r"[A-Za-z0-9._-]{1,100}")
# Each module output is a whole owned file. The perimeter is a sibling manifest.
TEMPLATES = {
    ".github/hexalith-ci.json": ".github/hexalith-ci.json.j2",
    ".github/workflows/ci.yml": ".github/workflows/ci.yml.j2",
    ".github/workflows/release.yml": ".github/workflows/release.yml.j2",
    ".github/dependabot.yml": ".github/dependabot.yml.j2",
}
PERIMETER = "perimeter.json.j2"
QUALIFICATION = ".github/workflows/qualification.yml.j2"
PARTIALS = ("partials/ownership-block.txt.j2", "partials/deny-entries.json.j2")
EXPORT_PATHS = (
    "schemas", "Github/lib", ".github/workflows/ci.yml", ".github/workflows/release.yml",
    "Github/prepare/action.yml", "Github/publish/action.yml",
    "Tools/ci/lint_workflows.py", "Tools/ci/tools.json",
)


class RenderError(ValueError):
    """A contextual error, escaped by the CLI before it reaches a log."""


def diagnostic(value: object) -> str:
    return "".join(
        f"\\u{ord(char):04x}" if ord(char) < 32 or 127 <= ord(char) <= 159
        or 0xD800 <= ord(char) <= 0xDFFF or char in "\u2028\u2029" else char
        for char in str(value))


class StrictLoader(yaml.SafeLoader):
    """GitHub boolean spelling, string keys only, and no duplicate/merge keys."""

    yaml_implicit_resolvers = copy.deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise RenderError(f"YAML key {key!r}: object keys must be strings")
            if key in result:
                raise RenderError(f"duplicate YAML key {key!r}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


for _letter, _resolvers in StrictLoader.yaml_implicit_resolvers.items():
    StrictLoader.yaml_implicit_resolvers[_letter] = [
        item for item in _resolvers if item[0] != "tag:yaml.org,2002:bool"]
StrictLoader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$"), list("tf"))


def json_values(value: Any, location: str = "$", active: set[int] | None = None) -> None:
    """Reject YAML-only values, nonfinite numbers, invalid Unicode and cycles."""
    active = set() if active is None else active
    if isinstance(value, dict | list):
        if id(value) in active:
            raise RenderError(f"{location}: recursive YAML aliases are unsupported")
        active.add(id(value))
        items = value.items() if isinstance(value, dict) else enumerate(value)
        for key, item in items:
            if isinstance(value, dict):
                if not isinstance(key, str):
                    raise RenderError(f"{location}: object keys must be strings")
                json_values(key, location, active)
            json_values(item, f"{location}/{key}", active)
        active.remove(id(value))
    elif isinstance(value, str):
        value.encode("utf-8")
    elif type(value) not in (int, float, bool, type(None)):
        raise RenderError(f"{location}: unsupported YAML value {type(value).__name__}")
    elif isinstance(value, float) and not math.isfinite(value):
        raise RenderError(f"{location}: nonfinite numbers are unsupported")


def yaml_document(data: bytes, source: str) -> Any:
    try:
        value = yaml.load(data.decode("utf-8"), Loader=StrictLoader)
        json_values(value)
        return value
    except (yaml.YAMLError, ValueError, UnicodeError, RecursionError) as error:
        raise RenderError(f"{source}: {error}") from error


def json_document(data: bytes, source: str) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise RenderError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    def constant(value):
        raise RenderError(f"non-JSON constant {value}")

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
        json_values(value)
        return value
    except (ValueError, UnicodeError, RecursionError) as error:
        raise RenderError(f"{source}: {error}") from error


def safe_path(root: Path, relative: str) -> Path:
    """Reject symlink traversal even for a trusted input directory."""
    current = root
    for component in PurePosixPath(relative).parts:
        current /= component
        if current.is_symlink():
            raise RenderError(f"{current}: symlinks are not allowed")
    return current


def git(repository: Path, *arguments: str, data: bytes | None = None) -> bytes:
    environment = os.environ.copy()
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    environment["GIT_NO_LAZY_FETCH"] = "1"
    # An uninitialized submodule directory must not resolve to the superproject.
    environment["GIT_CEILING_DIRECTORIES"] = str(repository.parent)
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_PREFIX"):
        environment.pop(key, None)
    result = subprocess.run([
        "git", "-c", "core.hooksPath=/dev/null", "-c", "submodule.recurse=false",
        "-C", str(repository), *arguments,
    ], input=data, capture_output=True, env=environment, timeout=60, check=False)
    if result.returncode:
        raise RenderError(f"{repository}: git {arguments[0]}: "
                          f"{result.stderr.decode('utf-8', 'backslashreplace').strip()}")
    return result.stdout


def deny_schema_retrieval(uri: str):
    """Schemas must resolve within the trusted tagged document, never externally."""
    raise NoSuchResource(ref=uri)


def schema_validator(schema: dict) -> Draft202012Validator:
    return Draft202012Validator(schema, format_checker=FormatChecker(),
                                registry=Registry(retrieve=deny_schema_retrieval))


@dataclass
class Contract:
    root: Path
    tag: str
    revision: str
    schemas: dict[str, dict]

    def validate(self, kind: str, data: bytes, source: str, repository: str = "") -> dict:
        document = json_document(data, source)
        validator = schema_validator(self.schemas[kind])
        try:
            errors = sorted(validator.iter_errors(document), key=lambda error: str(list(error.absolute_path)))
        except Unresolvable as error:
            raise RenderError(f"{source}: schema reference resolution failed: {error}") from error
        if errors:
            error = errors[0]
            location = "/".join(map(str, error.absolute_path))
            raise RenderError(f"{source}: $/{location}: {error.message}")
        # Invoke the *strict reader*, on the exact serialized document. Its own
        # schema-relative layout is retained in the trusted tagged export.
        with tempfile.TemporaryDirectory(prefix="hexalith-render-validation-") as directory:
            path = Path(directory) / ("hexalith-ci.json" if kind == "ci" else "perimeter.json")
            path.write_bytes(data)
            arguments = [sys.executable, "-I", str(self.root / f"Github/lib/{kind}_config.py"), str(path)]
            if kind == "ci":
                arguments += ["--repository", f"Hexalith/{repository}"]
            result = subprocess.run(arguments, capture_output=True, text=True, timeout=60, check=False)
            if result.returncode:
                raise RenderError(f"{source}: pinned {kind} loader: {result.stderr.strip()}")
        return document


@contextmanager
def pinned_contract(project: Path) -> Iterator[Contract]:
    pin = safe_path(project, "builds-version")
    tag = pin.read_text(encoding="utf-8").removesuffix("\n")
    if STABLE_TAG.fullmatch(tag) is None:
        raise RenderError(f"{pin}: expected one exact stable vMAJOR.MINOR.PATCH tag")
    repository = safe_path(project, "references/Hexalith.Builds")
    revision = git(repository, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}").decode().strip()
    with tempfile.TemporaryDirectory(prefix="hexalith-builds-contract-") as directory:
        root = Path(directory)
        # Copy exact blobs, bypassing worktree bytes and archive/filter attributes.
        # A single batch keeps this cheap even for the stdlib library's imports.
        records = git(repository, "ls-tree", "-r", "-z", revision, "--", *EXPORT_PATHS)
        entries = []
        for record in records.split(b"\0"):
            if not record:
                continue
            header, raw_path = record.split(b"\t", 1)
            mode, kind, oid = header.decode("ascii").split()
            path = PurePosixPath(raw_path.decode("utf-8"))
            if mode not in ("100644", "100755") or kind != "blob" or path.is_absolute() or ".." in path.parts:
                raise RenderError(f"Builds {tag}: unsafe exported path {path}")
            entries.append((path, oid))
        objects = list(dict.fromkeys(oid for _, oid in entries))
        batch = io.BytesIO(git(repository, "cat-file", "--batch", data="".join(oid + "\n" for oid in objects).encode()))
        blobs = {}
        for expected in objects:
            header = batch.readline().decode("ascii").split()
            if len(header) == 2 and header[1] == "missing":
                raise RenderError(f"Builds {tag}: missing local Git blob {expected}; rendering does not fetch")
            if len(header) != 3:
                raise RenderError(f"Builds {tag}: invalid Git blob batch")
            oid, kind, size = header
            if oid != expected or kind != "blob":
                raise RenderError(f"Builds {tag}: invalid Git blob batch")
            blobs[oid] = batch.read(int(size))
            if len(blobs[oid]) != int(size) or batch.read(1) != b"\n":
                raise RenderError(f"Builds {tag}: incomplete Git blob batch")
        for path, oid in entries:
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blobs[oid])
        schemas = {}
        for kind in ("ci", "perimeter"):
            paths = sorted((root / "schemas").glob(f"hexalith.{kind}.v*.json"))
            paths = [path for path in paths if re.fullmatch(rf"hexalith\.{kind}\.v[0-9]+\.json", path.name)]
            if len(paths) != 1:
                raise RenderError(f"Builds {tag}: expected exactly one {kind} schema; found {len(paths)}")
            schema = json_document(paths[0].read_bytes(), str(paths[0]))
            def local_references(value):
                if isinstance(value, dict):
                    for keyword in ("$ref", "$dynamicRef"):
                        if keyword in value and (not isinstance(value[keyword], str)
                                                 or not value[keyword].startswith("#")):
                            raise RenderError(f"Builds {tag}: {paths[0].name}: nonlocal schema reference {keyword}")
                    for child in value.values():
                        local_references(child)
                elif isinstance(value, list):
                    for child in value:
                        local_references(child)
            local_references(schema)
            Draft202012Validator.check_schema(schema)
            identity = schema.get("properties", {}).get("schema", {}).get("const")
            if not isinstance(identity, str) or not identity:
                raise RenderError(f"Builds {tag}: {paths[0].name}: missing schema const identity")
            schemas[kind] = schema
        yield Contract(root, tag, revision, schemas)


def local_reference(root: dict, reference: str) -> dict:
    if not reference.startswith("#/"):
        raise RenderError(f"unsupported default reference {reference}")
    target = root
    for component in reference[2:].split("/"):
        target = target[component.replace("~1", "/").replace("~0", "~")]
    return target


def default_source(schema: dict, root: dict) -> dict:
    if "default" not in schema and "$ref" in schema:
        return default_source(local_reference(root, schema["$ref"]), root)
    return schema


def defaults(value: Any, schema: dict, root: dict) -> Any:
    """Apply only defaults declared at the pinned schema, including conditionals."""
    if "$ref" in schema:
        defaults(value, local_reference(root, schema["$ref"]), root)
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key, subschema in properties.items():
            if key not in value:
                source = default_source(subschema, root)
                if "default" in source:
                    value[key] = copy.deepcopy(source["default"])
            if key in value:
                defaults(value[key], subschema, root)
        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            for key in value.keys() - properties.keys():
                defaults(value[key], additional, root)
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for item in value:
            defaults(item, schema["items"], root)
    for subschema in schema.get("allOf", []):
        defaults(value, subschema, root)
    if "if" in schema:
        validator = schema_validator(root).evolve(schema=schema["if"])
        branch = "then" if validator.is_valid(value) else "else"
        defaults(value, schema.get(branch, {}), root)
    return value


def registry(project: Path) -> list[tuple[str, Path]]:
    setup = safe_path(project, "setup")
    if not setup.is_dir():
        raise RenderError(f"{setup}: expected the setup registry directory")
    result = []
    names = set()
    for path in sorted(setup.glob("*.yml")):
        name = path.name[:-len(".yml")]
        if (REPOSITORY.fullmatch(name) is None or name in (".", "..")
                or name.casefold() == "hexalith.builds"):
            raise RenderError(f"{path}: invalid or reserved repository name {name!r}")
        if name.casefold() in names:
            raise RenderError(f"{path}: case-insensitive repository/output name collision")
        names.add(name.casefold())
        if path.is_symlink() or not path.is_file():
            raise RenderError(f"{path}: setup must be a regular file, without symlinks")
        result.append((name, path))
    return result


def templates(project: Path) -> Environment:
    sources = {}
    for name in (*TEMPLATES.values(), QUALIFICATION, PERIMETER, *PARTIALS):
        path = safe_path(project, f"templates/{name}")
        try:
            sources[name] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise RenderError(f"{path}: {error}") from error
    environment = Environment(
        loader=DictLoader(sources), undefined=StrictUndefined, autoescape=False,
        variable_start_string="[[", variable_end_string="]]",
        block_start_string="[%", block_end_string="%]",
        trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True,
    )
    # Jinja's JSON encoder emits stable, ASCII-safe JSON strings, including YAML
    # keys and complete uses references. Strict JSON rejects nonfinite values.
    def encode_json(value, **kwargs):
        def unsupported(item):
            if isinstance(item, Undefined):
                # Preserve StrictUndefined's variable name, even inside a JSON
                # collection, instead of the encoder's generic TypeError.
                str(item)
            raise TypeError(f"Object of type {type(item).__name__} is not JSON serializable")
        return json.dumps(value, default=unsupported, **kwargs)
    environment.policies["json.dumps_function"] = encode_json
    environment.policies["json.dumps_kwargs"] = {"sort_keys": True, "allow_nan": False}
    # Workflow expressions must remain ordinary YAML scalars. Jinja's HTML-safe
    # JSON filter escapes apostrophes and &&, preventing security tools from
    # analyzing the expression even though a YAML reader decodes the string.
    environment.filters["toyaml"] = lambda value: yaml.safe_dump(
        value, sort_keys=True, allow_unicode=False, width=1_000_000).rstrip("\n")
    for name in sources:
        try:
            environment.get_template(name)
        except TemplateError as error:
            raise RenderError(f"templates/{name}: {error}") from error
    return environment


def rendered_bytes(environment: Environment, template: str, context: dict) -> bytes:
    try:
        text = environment.get_template(template).render(context)
        if text.startswith("\ufeff"):
            raise RenderError("UTF-8 BOM is not allowed")
        return (text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n").encode("utf-8")
    except (TemplateError, ValueError, TypeError, UnicodeError) as error:
        raise RenderError(f"templates/{template}: {error}") from error


def permission_union(document: dict) -> dict:
    """Maximum effective job access required by a selected reusable workflow."""
    union = {}
    ranks = {"none": 0, "read": 1, "write": 2}
    for job in document["jobs"].values():
        for scope, permission in job.get("permissions", document.get("permissions", {})).items():
            if permission not in ranks:
                raise RenderError(f"invalid pinned permission {scope}: {permission}")
            if ranks[permission] >= ranks.get(union.get(scope), -1):
                union[scope] = permission
    return union


def shared_ci_call(config: dict, interfaces: dict | None = None) -> dict:
    """Construct one caller from capabilities declared by the exact tagged API."""
    arguments = {}
    timeout = config.get("job-timeout-minutes", config.get("ciTimeoutMinutes"))
    if timeout is not None:
        arguments["job-timeout-minutes"] = timeout
    if "additionalSdkVersion" in config:
        arguments["additional-sdk-version"] = config["additionalSdkVersion"]
    if interfaces is not None:
        for key, value in arguments.items():
            expected = "number" if key == "job-timeout-minutes" else "string"
            if interfaces["ci_inputs"].get(key, {}).get("type") != expected:
                if key == "job-timeout-minutes":
                    raise RenderError("ciTimeoutMinutes requires the numeric job-timeout-minutes input")
                raise RenderError(f"selected Builds contract lacks the {expected} {key} input")
    job = {"uses": f"Hexalith/Hexalith.Builds/.github/workflows/ci.yml@{config['buildsTag']}",
           "permissions": interfaces["ci_permissions"] if interfaces is not None else {"contents": "read"},
           "secrets": {"registry-pull-username": "${{ secrets.HEXALITH_REGISTRY_PULL_USERNAME }}",
                       "registry-pull-password": "${{ secrets.HEXALITH_REGISTRY_PULL_PASSWORD }}"}}
    if arguments:
        job["with"] = arguments
    return job


CHECKOUT_ACTION = re.compile(r"(?m)^\s+uses:\s+(actions/checkout@[0-9a-f]{40})\s*(?:#.*)?$")
PUBLISHED_BUILDS_BIND = """set -euo pipefail
git --literal-pathspecs -c protocol.file.allow=never -c submodule.recurse=false submodule update --init --checkout -- references/Hexalith.Builds
python3 -I - <<'PY'
from pathlib import Path
from types import SimpleNamespace
import os
import sys
root = Path(os.environ["GITHUB_WORKSPACE"])
temporary = Path(os.environ["RUNNER_TEMP"])
channel = Path(os.environ["GITHUB_ENV"])
if not root.is_dir() or not temporary.is_dir():
    raise SystemExit("published Builds bind requires GITHUB_WORKSPACE and RUNNER_TEMP")
sys.path.insert(0, str(root / "references/Hexalith.Builds/Github/lib"))
from ci_config import _read_json
import published_builds
document = _read_json(root / ".github/hexalith-ci.json")
if not document.get("publishedBuilds"):
    raise SystemExit("published Builds bind requires a committed tuple")
workspace = temporary / "hexalith-published-builds"
if workspace.exists():
    raise SystemExit("published Builds workspace already exists")
values = published_builds.prepare(SimpleNamespace(root=root, document=document), workspace)
tool_root = values["HexalithBuildsPublishedToolRoot"]
if not (Path(tool_root) / "Hexalith.Builds.Tooling.dll").is_file():
    raise SystemExit("published Builds tooling assembly is missing")
if any(ord(character) < 32 for character in tool_root):
    raise SystemExit("invalid published Builds environment value")
# Tagged restore_and_build already supplies Release. Only the published
# tooling root is required for Platform's foreign-reference guard.
with channel.open("a", encoding="utf-8", newline="\\n") as stream:
    stream.write("HexalithBuildsPublishedToolRoot=" + tool_root + "\\n")
print(tool_root)
PY
"""


def linux_prepare_binds_published_builds(root: Path) -> bool:
    """True when tagged Linux prepare already authenticates publishedBuilds."""
    path = root / "Github/prepare/prepare_linux.py"
    return path.is_file() and 'document.get("publishedBuilds")' in path.read_text(encoding="utf-8")


def prepare_checkout_pin(root: Path) -> str:
    """Reuse the selected prepare composite's pinned checkout action."""
    match = CHECKOUT_ACTION.search((root / "Github/prepare/action.yml").read_text(encoding="utf-8"))
    if match is None:
        raise RenderError("selected Builds prepare does not pin actions/checkout")
    return match.group(1)


def published_builds_bind_steps(checkout: str) -> list[dict]:
    """Authenticate the committed tuple before tagged prepare restore_and_build."""
    if "${{" in checkout or any(ord(character) < 32 for character in checkout):
        raise RenderError("published Builds checkout pin is invalid")
    return [{"uses": checkout, "with": {"submodules": False, "persist-credentials": False}},
            {"name": "Bind verified published Builds tooling", "shell": "bash",
             "run": PUBLISHED_BUILDS_BIND}]


def execution_jobs(config: dict, schema: dict, interfaces: dict | None = None,
                   published_builds_checkout: str | None = None) -> tuple[dict, dict, dict]:
    """Render fresh product jobs; private fixtures require green-source authority."""
    configured = config["jobs"]
    legacy, ci, qualification = {}, {}, {}
    identifiers = {name: ("windows-" if options["runner"] in ("windows-latest", "macos-latest")
                          else "custom-") + name for name, options in configured.items()}
    manual = sorted(name for name, options in configured.items() if options.get("trigger", "ci") == "manual")
    closures = {}
    for target in manual:
        pending, seen = [target], set()
        while pending:
            current = pending.pop()
            if current not in seen:
                seen.add(current)
                pending.extend(configured[current].get("needs", []))
        closures[target] = seen
    platform_fields = []
    if interfaces is not None:
        platform_fields = [key for key in ("module-manifest", "windows-checkout", "source-revision", "module-authority")
                           if key in interfaces["ci_outputs"] and key in interfaces["prepare_inputs"]]
        required = set()
        if config.get("moduleManifest"):
            required.update(("module-manifest", "module-authority"))
        if config.get("windowsCheckout"):
            required.update(("windows-checkout", "source-revision"))
        if any(options["runner"] in ("windows-latest", "macos-latest") for options in configured.values()):
            if not required <= set(platform_fields):
                raise RenderError("selected Builds contract lacks matched CI outputs and prepare inputs for platform authority")
            if config["tests"].get("additional") and ("additional-test-projects" not in interfaces["ci_outputs"]
                                                       or "additional-test-projects" not in interfaces["prepare_inputs"]):
                raise RenderError("selected Builds contract lacks additional-test-projects platform preparation")
    green_manual, green_nightly = set(), False
    for name, options in sorted(configured.items()):
        private = isinstance(options["runner"], dict)
        platform = options["runner"] in ("windows-latest", "macos-latest")
        trigger = options.get("trigger", "ci")
        authority = private or (platform and trigger != "ci" and bool(config.get("moduleManifest") or config.get("windowsCheckout")))
        extended_platform = platform_fields or config.get("additionalSdkVersion") or config.get("tests", {}).get("additional")
        if set(options) == {"runner"} and platform and not extended_platform:
            legacy[name] = options
            continue
        dependencies = options.get("needs", [])
        job = {"runs-on": options["runner"], "permissions": {"contents": "read"},
               "timeout-minutes": options.get("timeoutMinutes", 30)}
        if trigger == "ci":
            job["needs"] = ["ci", *(identifiers[item] for item in dependencies)]
            if options.get("runAfterFailure"):
                job["if"] = "${{ !cancelled() && needs.ci.result == 'success' }}"
        else:
            if dependencies:
                job["needs"] = [identifiers[item] for item in dependencies]
            if trigger == "nightly":
                condition = "(github.event_name == 'schedule' || inputs.job == 'nightly')"
                green_nightly = green_nightly or authority
            else:
                selected = sorted(target for target, closure in closures.items() if name in closure)
                condition = "(github.event_name == 'workflow_dispatch' && contains(fromJSON('" + json.dumps(selected) + "'), inputs.job))"
                if authority:
                    green_manual.update(selected)
            if options.get("runAfterFailure"):
                condition = "!cancelled() && " + condition
            if authority:
                job["needs"] = ["qualification-ci", *job.get("needs", [])]
                condition = "needs.qualification-ci.result == 'success' && " + condition
            job["if"] = "${{ github.ref == 'refs/heads/main' && " + condition + " }}"
        if "environment" in options:
            job["environment"] = options["environment"]
        if "matrix" in options:
            job["strategy"] = {"fail-fast": False, "matrix": options["matrix"]}
            if "maxParallel" in options:
                job["strategy"]["max-parallel"] = options["maxParallel"]
        if "resourceProfile" in options:
            profile = schema.get("x-resource-profiles", {}).get(options["resourceProfile"])
            if (not isinstance(profile, dict) or set(profile) != {"container", "env"}
                    or not isinstance(profile["container"], dict) or set(profile["container"]) != {"image", "options"}
                    or re.fullmatch(r"[a-z0-9./-]+@sha256:[0-9a-f]{64}", profile["container"]["image"]) is None
                    or re.fullmatch(r"--cpus=[1-9][0-9]* --memory=[1-9][0-9]*g --memory-swap=[1-9][0-9]*g", profile["container"]["options"]) is None
                    or not isinstance(profile["env"], dict)
                    or any(not isinstance(key, str) or not isinstance(value, str)
                           or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) is None or "${{" in value
                           or any(ord(char) < 32 for char in value) for key, value in profile["env"].items())):
                raise RenderError(f"jobs/{name}: selected Builds contract has no valid resource profile")
            job["container"] = profile["container"]
            job["env"] = profile["env"]
            job["defaults"] = {"run": {"shell": "bash"}}
        prepare = {"uses": f"Hexalith/Hexalith.Builds/Github/prepare@{config['buildsTag']}"}
        linux = private or options["runner"].startswith("ubuntu-")
        if private:
            prepare["with"] = {"environment": "preserve", "authority-sha256": "${{ inputs.authority-sha256 }}",
                               "source-sha": "${{ needs.qualification-ci.outputs.source-sha }}"}
        elif linux:
            prepare["with"] = {"job-name": name}
            if "resourceProfile" in options:
                prepare["with"]["resource-profile"] = options["resourceProfile"]
            if options.get("setup", {}).get("registry", config["registry"]):
                prepare["env"] = {"REGISTRY_PULL_USERNAME": "${{ secrets.HEXALITH_REGISTRY_PULL_USERNAME }}",
                                  "REGISTRY_PULL_PASSWORD": "${{ secrets.HEXALITH_REGISTRY_PULL_PASSWORD }}"}
        elif trigger == "ci" or authority:
            producer = "ci" if trigger == "ci" else "qualification-ci"
            prepare["with"] = {key: "${{ needs." + producer + ".outputs." + key + " }}"
                               for key in ("solution", "submodules", "global-json", *platform_fields)}
        else:
            prepare["with"] = {"solution": config["solution"], "submodules": json.dumps(config["submodules"]),
                               "global-json": "global.json"}
        if platform and config.get("tests", {}).get("additional"):
            prepare["with"]["additional-test-projects"] = ("${{ needs.ci.outputs.additional-test-projects }}" if trigger == "ci"
                                                          else json.dumps(config["tests"]["additional"]))
        if "additionalSdkVersion" in config:
            prepare["with"]["additional-sdk-version"] = config["additionalSdkVersion"]
        if interfaces is not None:
            unsupported = prepare.get("with", {}).keys() - interfaces["prepare_inputs"].keys()
            if unsupported:
                raise RenderError(f"jobs/{name}: selected Builds prepare lacks inputs {sorted(unsupported)}")
        action_environment = {"HEXALITH_JOB_NAME": name,
                              "HEXALITH_JOB_PARAMETERS": "${{ toJSON(matrix) }}" if "matrix" in options else "{}",
                              "HEXALITH_JOB_NEEDS": "${{ toJSON(needs) }}",
                              "HEXALITH_QUALIFICATION_PARAMETERS": "${{ inputs.parameters || '{}' }}" if trigger == "manual" else "{}"}
        if private:
            action_environment.update(HEXALITH_AUTHORITY_SHA256="${{ inputs.authority-sha256 }}",
                                      HEXALITH_SOURCE_SHA="${{ needs.qualification-ci.outputs.source-sha }}")
        secrets = options.get("secrets", {})
        for variable, secret in (secrets.items() if isinstance(secrets, dict) else ((value, value) for value in secrets)):
            action_environment[variable] = "${{ secrets." + secret + " }}"
        action = {"uses": f"./.github/actions/{name}", "env": action_environment}
        bind = []
        if (published_builds_checkout and linux and not private and config.get("publishedBuilds")):
            bind = published_builds_bind_steps(published_builds_checkout)
        job["steps"] = [*bind, prepare, action]
        (ci if trigger == "ci" else qualification)[identifiers[name]] = job
    if green_manual or green_nightly:
        if interfaces is not None and "source-sha" not in interfaces["ci_outputs"]:
            raise RenderError("private qualification requires the selected Builds CI source-sha output")
        green = shared_ci_call(config, interfaces)
        conditions = []
        if green_manual:
            conditions.append("(github.event_name == 'workflow_dispatch' && contains(fromJSON('" + json.dumps(sorted(green_manual)) + "'), inputs.job))")
        if green_nightly:
            conditions.append("(github.event_name == 'schedule' || inputs.job == 'nightly')")
        green["if"] = "${{ github.ref == 'refs/heads/main' && (" + " || ".join(conditions) + ") }}"
        qualification = {"qualification-ci": green, **qualification}
    return legacy, ci, qualification


def desired_tree(project: Path, registrations: list[tuple[str, Path]],
                 environment: Environment, contract: Contract) -> dict[str, bytes]:
    result = {}
    source = f"Builds {contract.tag}/.github/workflows/ci.yml"
    ci_declaration = yaml_document((contract.root / ".github/workflows/ci.yml").read_bytes(), source)
    ci_permissions = permission_union(ci_declaration)
    prepare_declaration = yaml_document((contract.root / "Github/prepare/action.yml").read_bytes(), source)
    interfaces = {"ci_inputs": ci_declaration.get("on", {}).get("workflow_call", {}).get("inputs", {}),
                  "ci_outputs": ci_declaration.get("on", {}).get("workflow_call", {}).get("outputs", {}),
                  "prepare_inputs": prepare_declaration.get("inputs", {}), "ci_permissions": ci_permissions}
    for repository, path in registrations:
        setup = yaml_document(path.read_bytes(), str(path))
        if not isinstance(setup, dict):
            raise RenderError(f"{path}: $: expected an object")
        for forbidden in ("schema", "buildsTag"):
            if forbidden in setup:
                raise RenderError(f"{path}: $/{forbidden}: supplied by the renderer; forbidden in setup")
        try:
            config = defaults(setup, contract.schemas["ci"], contract.schemas["ci"])
        except (RenderError, Unresolvable) as error:
            raise RenderError(f"{path}: schema defaults: {error}") from error
        config["schema"] = contract.schemas["ci"]["properties"]["schema"]["const"]
        config["buildsTag"] = contract.tag
        context = {
            "config": config, "builds_tag": contract.tag,
            "perimeter_schema": contract.schemas["perimeter"]["properties"]["schema"]["const"],
            "ci_workflow": f"Hexalith/Hexalith.Builds/.github/workflows/ci.yml@{contract.tag}",
            "ci_permissions": ci_permissions,
            "release_workflow": f"Hexalith/Hexalith.Builds/.github/workflows/release.yml@{contract.tag}",
            "prepare_action": f"Hexalith/Hexalith.Builds/Github/prepare@{contract.tag}",
            "publish_action": f"Hexalith/Hexalith.Builds/Github/publish@{contract.tag}",
        }
        # First serialize and validate the actual CI JSON; only validated values
        # may participate in job structure or other templates.
        ci = rendered_bytes(environment, TEMPLATES[".github/hexalith-ci.json"], context)
        document = contract.validate("ci", ci, f"{path} -> .github/hexalith-ci.json", repository)
        if document["buildsTag"] != contract.tag:
            raise RenderError(f"{path} -> .github/hexalith-ci.json: buildsTag must equal builds-version")
        context["config"] = document
        checkout = None
        if document.get("publishedBuilds") and not linux_prepare_binds_published_builds(contract.root):
            checkout = prepare_checkout_pin(contract.root)
        legacy, custom, qualification = execution_jobs(
            document, contract.schemas["ci"], interfaces, published_builds_checkout=checkout)
        context.update(legacy_jobs=legacy, ci_custom_jobs=custom, qualification_jobs=qualification)
        context["ci_arguments"] = shared_ci_call(document, interfaces).get("with", {})
        context["qualification_choices"] = ["nightly", *sorted(name for name, options in document["jobs"].items()
                                                              if options.get("trigger", "ci") == "manual")]
        release_declaration = yaml_document((contract.root / ".github/workflows/release.yml").read_bytes(), source)
        context["release_timeouts"] = {}
        for field, argument in (("releaseTimeoutMinutes", "release-timeout-minutes"),
                                ("nightlyTimeoutMinutes", "nightly-timeout-minutes")):
            if field in document:
                inputs = release_declaration.get("on", {}).get("workflow_call", {}).get("inputs", {})
                if inputs.get(argument, {}).get("type") != "number":
                    raise RenderError(f"{source}: {field} requires the numeric {argument} input")
                context["release_timeouts"][argument] = document[field]
        # Only the selected release's complete contract may introduce this
        # knob. Older pins retain their original configuration and caller.
        # Preserve the explicit native override introduced by newer Builds
        # contracts while materializing the default-backed timeout knob.
        context["ci_timeout_minutes"] = document.get("job-timeout-minutes", document.get("ciTimeoutMinutes"))
        if context["ci_timeout_minutes"] is not None:
            inputs = ci_declaration.get("on", {}).get("workflow_call", {}).get("inputs", {})
            if inputs.get("job-timeout-minutes", {}).get("type") != "number":
                raise RenderError(f"{source}: ciTimeoutMinutes requires the numeric job-timeout-minutes input")
        context["ownership_block"] = rendered_bytes(environment, PARTIALS[0], context).decode("utf-8")
        context["deny_entries"] = json_document(rendered_bytes(environment, PARTIALS[1], context), PARTIALS[1])
        for output, template in TEMPLATES.items():
            data = ci if output.endswith(".json") else rendered_bytes(environment, template, context)
            if output.endswith(".yml"):
                document = yaml_document(data, f"{path} -> {output}")
                if not isinstance(document, dict):
                    raise RenderError(f"{path} -> {output}: expected a YAML object")
            result[f"{repository}/{output}"] = data
        if qualification:
            data = rendered_bytes(environment, QUALIFICATION, context)
            yaml_document(data, f"{path} -> qualification.yml")
            result[f"{repository}/.github/workflows/qualification.yml"] = data
        perimeter = rendered_bytes(environment, PERIMETER, context)
        contract.validate("perimeter", perimeter, f"{path} -> perimeter.json")
        result[f"{repository}.perimeter.json"] = perimeter
    validate_names(result)
    return result


def tree_directories(paths) -> set[str]:
    return {parent.as_posix() for path in paths for parent in PurePosixPath(path).parents
            if parent != PurePosixPath(".")}


def validate_names(files: dict[str, bytes]) -> None:
    seen = {".gitkeep": "reserved .gitkeep"}
    for name in sorted(set(files) | tree_directories(files)):
        key = name.casefold()
        if key in seen and seen[key] != name:
            raise RenderError(f"rendered/{name}: output-name collision with {seen[key]}")
        seen[key] = name
    overlap = set(files) & tree_directories(files)
    if overlap:
        raise RenderError(f"rendered/{sorted(overlap)[0]}: output file/directory collision")


def existing_tree(output: Path) -> tuple[dict[str, bytes], set[str]]:
    files, directories = {}, set()
    if not output.exists():
        return files, directories
    if not output.is_dir():
        raise RenderError(f"{output}: expected a directory")
    for directory, children, names in os.walk(output, followlinks=False):
        for name in sorted(children + names):
            path = Path(directory) / name
            mode = path.lstat().st_mode
            relative = path.relative_to(output).as_posix()
            if stat.S_ISLNK(mode):
                raise RenderError(f"{path}: symlink in generated output")
            if stat.S_ISDIR(mode):
                if relative == ".gitkeep":
                    raise RenderError(f"{path}: reserved .gitkeep must be a regular file")
                directories.add(relative)
            elif stat.S_ISREG(mode):
                files[relative] = path.read_bytes()
            else:
                raise RenderError(f"{path}: generated output must contain only regular files/directories")
    return files, directories


def publish(output: Path, files: dict[str, bytes]) -> None:
    """Stage a complete desired tree, then swap it in with rollback on failure."""
    with tempfile.TemporaryDirectory(prefix=".hexalith-render-", dir=output.parent) as directory:
        staging, backup = Path(directory) / "new", Path(directory) / "old"
        staging.mkdir()
        for relative, data in sorted(files.items()):
            path = staging / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        had_output = output.exists()
        try:
            if had_output:
                output.rename(backup)
            staging.rename(output)
        except BaseException:
            # A rename may finish before Python delivers KeyboardInterrupt.
            # Keep both boundaries inside rollback, including successful install.
            if backup.exists():
                if output.exists():
                    output.rename(staging)
                backup.rename(output)
            elif not had_output and output.exists() and not staging.exists():
                output.rename(staging)
            raise


def render(project: Path, *, check: bool) -> list[str]:
    project = project.resolve()
    output = safe_path(project, "rendered")
    current, directories = existing_tree(output)
    registrations = registry(project)
    environment = templates(project)
    with pinned_contract(project) as contract:
        desired = desired_tree(project, registrations, environment, contract)
    desired[".gitkeep"] = current.get(".gitkeep", b"")
    mismatches = {name for name in current.keys() | desired.keys() if current.get(name) != desired.get(name)}
    mismatches |= directories - tree_directories(desired)
    if mismatches and not check:
        publish(output, desired)
    return sorted(mismatches)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", help="Report sorted mismatches without writing")
    args = parser.parse_args()
    try:
        if sys.version_info < (3, 12):
            raise RenderError("Python 3.12 or later is required")
        mismatches = render(args.project_root, check=args.check)
        if args.check:
            for name in mismatches:
                print(diagnostic(f"rendered/{name}"))
            return int(bool(mismatches))
        print(f"Rendered setup registry ({len(mismatches)} changed paths).")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError, SchemaError,
            subprocess.SubprocessError) as error:
        print(f"Render failed: {diagnostic(error)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
