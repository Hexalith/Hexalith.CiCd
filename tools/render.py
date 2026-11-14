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
    for name in (*TEMPLATES.values(), PERIMETER, *PARTIALS):
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


def desired_tree(project: Path, registrations: list[tuple[str, Path]],
                 environment: Environment, contract: Contract) -> dict[str, bytes]:
    result = {}
    source = f"Builds {contract.tag}/.github/workflows/ci.yml"
    ci_declaration = yaml_document((contract.root / ".github/workflows/ci.yml").read_bytes(), source)
    ci_permissions = permission_union(ci_declaration)
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
        context["ownership_block"] = rendered_bytes(environment, PARTIALS[0], context).decode("utf-8")
        context["deny_entries"] = json_document(rendered_bytes(environment, PARTIALS[1], context), PARTIALS[1])
        for output, template in TEMPLATES.items():
            data = ci if output.endswith(".json") else rendered_bytes(environment, template, context)
            if output.endswith(".yml"):
                document = yaml_document(data, f"{path} -> {output}")
                if not isinstance(document, dict):
                    raise RenderError(f"{path} -> {output}: expected a YAML object")
            result[f"{repository}/{output}"] = data
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
