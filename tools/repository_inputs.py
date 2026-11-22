"""Check active inputs without importing or executing the code being checked.

Historical proof strings are permitted only at the exact identities below.
They are inert receipt/module-source names, never permission to follow a path.
The Python path analysis follows aliases, nested, inherited, imported and
spec-loaded helpers, and standard-library read, copy, load and process sinks; it
does not execute qualification suites or their external tools.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import itertools
import os
from pathlib import Path
import re
import subprocess


PROVENANCE = {
    "docs/contracts-prerequisites/approval.json": "186e462c2aa47fc135e736e7eeca76f39f0308efd198083f0ca1e6fec383bb6d",
    "docs/contracts-prerequisites/eventstore-tests.json": "1e7fb6935883085d5911a78be6f0a5246a9fe35fc24df158a60c72d4f0a592f0",
    "docs/contracts-prerequisites/mcp.json": "1491876dae82477dbeeed198b9eb708e38c3418f3566de8f6cdea7a1662fbf43",
    "docs/contracts-prerequisites/projects-source.json": "7ae10b92899a91201635cdd4ea3f72d7256e46cbcae749419f55d2fa29c0023b",
    "docs/contracts-prerequisites/projects-tests.json": "9faf1a358faafa37283559db53703e01982e104deb56ae4e4b7773d7940f2dba",
    "docs/proposals/contracts-prerequisites/projects-prerequisite-policy.patch": "a911c9eda24ba7099ea0940375d9a0390f9428fd287433e80510c1f775e620bf",
    "docs/proposals/works-builds-resync-20261117.json": "1580e044d3986c28eff3175437b47b0ab1b2cb46a3293a8b4053bf7aa8b1a30b",
    "tools/qualification/pre-adoption/parties/fixtures/current-preparation.patch": "376fe76acb58d3f03428be884c55c999e3559786da67ed628fbc49c784cb7370",
}
EVIDENCE_ROOT = "_bmad-" + "output"
EVIDENCE_PATH = re.compile(re.escape(EVIDENCE_ROOT) + r"(?:[/\\]|\b)")
PROSE_FILES = {"README.md", "AGENTS.md", "limits.md", "LICENSE", "setup/README.md"}
PROSE_DIRECTORIES = (".claude/", ".agents/", ".agent/", ".codex/", ".cursor/",
                     ".github/agents/", "_bmad/", ".bmad-loop/")
READS = {"read_text", "read_bytes", "open", "glob", "rglob", "iterdir", "exists", "is_file", "is_dir", "is_symlink", "stat", "lstat"}
# Standard-library calls whose path arguments are read, copied, executed or loaded.
SINKS = {"open", "io.open", "os.listdir", "os.scandir", "os.walk", "os.stat", "os.lstat",
         "os.path.exists", "os.path.isfile", "os.path.isdir", "shutil.copy", "shutil.copy2",
         "shutil.copyfile", "shutil.copytree", "shutil.move", "runpy.run_path"}
PROCESSES = {"subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_call", "subprocess.check_output"}
LOADERS = {"importlib.util.spec_from_file_location"}
STANDARD = {"pathlib", "io", "os", "os.path", "shutil", "runpy", "subprocess", "importlib", "importlib.util"}


def tracked_paths(root: Path) -> list[str]:
    return subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"], text=True).split("\0")[:-1]


def evidence_dependencies(root: Path, paths: list[str]) -> list[str]:
    failures = []
    analysis = PathReads(root, check_registry=False)
    for relative in paths:
        path = root / relative
        if relative.startswith(EVIDENCE_ROOT + "/") or not path.is_file():
            continue
        data = path.read_bytes()
        # A named immutable input is checked even if an edit removes its old
        # strings. A changed or copied receipt cannot inherit this exception.
        if relative in PROVENANCE:
            if hashlib.sha256(data).hexdigest() != PROVENANCE[relative]:
                failures.append(f"{relative}:1: historical provenance identity changed")
            continue
        prose = (relative in PROSE_FILES or relative.startswith(PROSE_DIRECTORIES)
                 or Path(relative).parent == Path("docs") and path.suffix == ".md")
        if prose and not data.startswith(b"#!") and not path.stat().st_mode & 0o111:
            continue
        for number, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
            if (path.suffix in {".py", ".sh", ".ps1", ".yaml", ".yml", ".toml"}
                    and line.lstrip().startswith("#")) or (
                    path.suffix in {".js", ".mjs", ".ts"} and line.lstrip().startswith("//")):
                continue
            if EVIDENCE_PATH.search(line):
                failures.append(f"{relative}:{number}: active input references evidence")
        if path.suffix == ".py":
            analysis.scan(relative)
    return sorted(set(failures) | analysis.failures)


@dataclass(frozen=True)
class FilePath:
    value: str


@dataclass(frozen=True)
class Function:
    source: str
    name: str
    bound: bool = False


@dataclass(frozen=True)
class Module:
    source: str


@dataclass(frozen=True)
class Symbol:
    name: str


@dataclass(frozen=True)
class Sequence:
    items: tuple


@dataclass(frozen=True)
class Mapping:
    items: tuple


def values(*items):
    return frozenset(item for item in items if item is not None)


class PathReads:
    """Bounded Python path flow for evidence and suite registry reads.

    Unknown fixture objects stay unknown. Known paths retain their identity
    through assignments, parameters, returned values and repository helpers.
    Both sides of conditionals are visited, so an unexecuted test branch cannot
    hide a dependency. This is a dependency guard, not a Python interpreter.
    """
    def __init__(self, root: Path, *, check_registry=True):
        self.root = root.resolve()
        self.check_registry = check_registry
        self.modules = {}
        self.failures = set()
        self.active = set()

    def module(self, source):
        if source in self.modules:
            return self.modules[source]
        path = self.root / source
        tree = ast.parse(path.read_text(), filename=source)
        env = {"__file__": values(str(path))}
        functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                functions.update({node.name + "." + method.name: method for method in node.body
                                  if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))})
        self.modules[source] = (tree, env, functions)
        env.update({name: values(Function(source, name)) for name in functions})
        self.statements(tree.body, env, source, top=True)
        return self.modules[source]

    def local_module(self, name, source):
        suffix = name.replace(".", "/") + ".py"
        for relative in ((Path(source).parent / suffix).as_posix(), "tools/" + suffix):
            if (self.root / relative).is_file():
                return relative
        return None

    @staticmethod
    def key(node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = PathReads.key(node.value)
            return parent + "." + node.attr if parent else None
        return None

    def assign(self, target, result, env):
        key = self.key(target)
        if key:
            env[key] = env.get(key, frozenset()) | result
        elif isinstance(target, (ast.Tuple, ast.List)):
            for sequence in result:
                if isinstance(sequence, Sequence):
                    for item, value in zip(target.elts, sequence.items):
                        self.assign(item, value, env)

    @staticmethod
    def iterate(result):
        return frozenset().union(*(frozenset().union(*item.items) if isinstance(item, Sequence)
                                   else values(item) for item in result))

    @staticmethod
    def merge(env, branch):
        for key, value in branch.items():
            if isinstance(value, frozenset):
                env[key] = env.get(key, frozenset()) | value

    @staticmethod
    def join(arguments):
        paths = arguments[0] if arguments else values(FilePath("."))
        for argument in arguments[1:]:
            argument = frozenset(item for item in argument if isinstance(item, (str, FilePath))) or values("*")
            paths = frozenset(FilePath(str(Path(left.value if isinstance(left, FilePath) else left)
                                           / (right.value if isinstance(right, FilePath) else right)))
                              for left, right in itertools.product(paths, argument)
                              if isinstance(left, (FilePath, str)) and isinstance(right, (FilePath, str)))
        return frozenset(FilePath(item) if isinstance(item, str) else item
                         for item in paths if isinstance(item, (str, FilePath)))

    def loaded(self, arguments):
        for argument in arguments:
            for path in argument:
                path = FilePath(path) if isinstance(path, str) else path
                if isinstance(path, FilePath) and path.value.endswith(".py"):
                    try:
                        relative = Path(path.value).relative_to(self.root).as_posix()
                    except ValueError:
                        continue
                    if (self.root / relative).is_file():
                        return values(Module(relative))
        return None

    def check(self, paths, source, line):
        for path in paths:
            if isinstance(path, str):
                path = FilePath(path)
            if not isinstance(path, FilePath):
                continue
            normalized = Path(os.path.normpath(self.root / path.value))
            for directory in ("setup", "rendered") if self.check_registry else ():
                if normalized == self.root / directory or self.root / directory in normalized.parents:
                    self.failures.add(f"{source}:{line}: suite reads repository-root {directory}/")
            if EVIDENCE_ROOT in normalized.parts:
                self.failures.add(f"{source}:{line}: active Python path reads evidence")

    def expression(self, node, env, source):
        if node is None:
            return frozenset()
        if isinstance(node, ast.Constant):
            return values(node.value) if isinstance(node.value, (str, int)) else frozenset()
        if isinstance(node, ast.Name):
            return env.get(node.id, frozenset())
        if isinstance(node, (ast.List, ast.Tuple)):
            return values(Sequence(tuple(self.expression(item, env, source) for item in node.elts)))
        if isinstance(node, ast.Set):
            return frozenset().union(*(self.expression(item, env, source) for item in node.elts))
        if isinstance(node, ast.Dict):
            return values(Mapping(tuple((self.expression(key, env, source), self.expression(value, env, source))
                                        for key, value in zip(node.keys, node.values))))
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            local = env.copy()
            for generator in node.generators:
                self.assign(generator.target, self.iterate(self.expression(generator.iter, local, source)), local)
                for condition in generator.ifs:
                    self.expression(condition, local, source)
            if isinstance(node, ast.DictComp):
                return values(Mapping(((self.expression(node.key, local, source), self.expression(node.value, local, source)),)))
            return values(Sequence((self.expression(node.elt, local, source),)))
        if isinstance(node, ast.Attribute):
            key = self.key(node)
            if key in env:
                return env[key]
            result = set()
            for value in self.expression(node.value, env, source):
                if isinstance(value, FilePath) and node.attr == "parent":
                    result.add(FilePath(str(Path(value.value).parent)))
                elif isinstance(value, FilePath) and node.attr == "parts":
                    result.update(Path(value.value).parts)
                elif isinstance(value, Module):
                    _, globals_, functions = self.module(value.source)
                    result.update(values(Function(value.source, node.attr)) if node.attr in functions else globals_.get(node.attr, ()))
                elif isinstance(value, Symbol):
                    result.add(Symbol(value.name + "." + node.attr))
            return frozenset(result)
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "parents":
            result = set()
            for path, index in itertools.product(self.expression(node.value.value, env, source), self.expression(node.slice, env, source)):
                if isinstance(path, FilePath) and isinstance(index, int) and index < len(Path(path.value).parents):
                    result.add(FilePath(str(Path(path.value).parents[index])))
            return frozenset(result)
        if isinstance(node, ast.Subscript):
            result = set()
            indices = self.expression(node.slice, env, source)
            for container in self.expression(node.value, env, source):
                if isinstance(container, Mapping):
                    for keys, items in container.items:
                        if keys & indices:
                            result.update(items)
                elif isinstance(container, Sequence):
                    for index in indices:
                        if isinstance(index, int) and -len(container.items) <= index < len(container.items):
                            result.update(container.items[index])
            return frozenset(result)
        if isinstance(node, ast.BinOp):
            result = set()
            # An unknown component stays a wildcard, so the known prefix keeps its identity.
            rights = frozenset(item for item in self.expression(node.right, env, source)
                               if isinstance(item, (str, FilePath))) or values("*")
            for left, right in itertools.product(self.expression(node.left, env, source), rights):
                if isinstance(node.op, ast.Div) and isinstance(left, FilePath):
                    result.add(FilePath(str(Path(left.value) / (right.value if isinstance(right, FilePath) else right))))
                elif isinstance(node.op, ast.Add) and isinstance(left, str) and isinstance(right, str):
                    result.add(left + right)
            return frozenset(result)
        if isinstance(node, ast.IfExp):
            return self.expression(node.body, env, source) | self.expression(node.orelse, env, source)
        if isinstance(node, ast.JoinedStr):
            strings = {""}
            for part in node.values:
                parts = self.expression(part.value if isinstance(part, ast.FormattedValue) else part, env, source)
                strings = {prefix + (item.value if isinstance(item, FilePath) else str(item))
                           for prefix, item in itertools.product(strings, parts or values("*"))}
            return frozenset(strings)
        if isinstance(node, ast.Call):
            return self.call(node, env, source)
        # Visit nested calls in comparisons, comprehensions and other containers.
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                self.expression(child, env, source)
        return frozenset()

    def call(self, node, env, source):
        arguments = [self.expression(arg, env, source) for arg in node.args]
        keywords = {}
        for argument in node.keywords:
            result = self.expression(argument.value, env, source)
            if argument.arg is not None:
                keywords[argument.arg] = result
        name = self.key(node.func) or ""
        names = {name} | {symbol.name for symbol in self.expression(node.func, env, source) if isinstance(symbol, Symbol)}
        if names & {"Path", "PurePath", "PurePosixPath", "pathlib.Path", "pathlib.PurePath", "pathlib.PurePosixPath"}:
            return self.join(arguments)
        if names & {"Path.cwd", "pathlib.Path.cwd"}:
            return values(FilePath(str(self.root)))
        if "os.path.join" in names and arguments:
            return self.join(arguments)
        if names & {"str", "os.fspath"} and arguments:
            return frozenset(item.value if isinstance(item, FilePath) else item for item in arguments[0])
        supplied = [*arguments, *keywords.values()]
        if names & SINKS:
            self.check(self.iterate(frozenset().union(*supplied)), source, node.lineno)
        if names & PROCESSES:
            # Relative strings are resolved by the child's cwd; constructed or absolute paths are known.
            self.check(frozenset(item for item in self.iterate(frozenset().union(*supplied))
                                 if isinstance(item, FilePath) or isinstance(item, str) and os.path.isabs(item)),
                       source, node.lineno)
        if any(value.startswith(("Path.", "pathlib.Path.")) and value.rsplit(".", 1)[-1] in READS for value in names) and arguments:
            self.check(arguments[0], source, node.lineno)
        if names & LOADERS and len(arguments) > 1:
            self.check(arguments[1], source, node.lineno)
            module = self.loaded(arguments[1:2])
            if module:
                return module
        if "importlib.util.module_from_spec" in names and arguments:
            return frozenset(value for value in arguments[0] if isinstance(value, Module))
        if name in {"load_module", "load"}:
            module = self.loaded(arguments)
            if module:
                return module
        if isinstance(node.func, ast.Attribute):
            base = self.expression(node.func.value, env, source)
            attr = node.func.attr
            if attr in READS:
                self.check(base, source, node.lineno)
            if attr in {"resolve", "absolute", "expanduser", "with_suffix", "with_stem"}:
                return base
            if attr in {"joinpath", "with_name"} and arguments:
                if attr == "joinpath":
                    return self.join([base, *arguments])
                result = set()
                for path, item in itertools.product(base, arguments[0]):
                    if isinstance(path, FilePath) and isinstance(item, str):
                        result.add(FilePath(str(Path(path.value) / item) if attr == "joinpath" else str(Path(path.value).with_name(item))))
                return frozenset(result)
            if attr in {"glob", "rglob", "iterdir"}:
                paths = self.join([base, arguments[0]]) if arguments else base
                self.check(paths, source, node.lineno)
                return paths
        results = set()
        for function in self.expression(node.func, env, source):
            if not isinstance(function, Function):
                continue
            signature = (function, tuple(arguments), tuple(keywords.items()))
            if any(active[0] == function for active in self.active) or len(self.active) >= 12:
                continue
            _, globals_, functions = self.module(function.source)
            if function.name not in functions:
                continue
            definition = functions[function.name]
            local = globals_.copy()
            if function.bound:
                local.update({key: value for key, value in env.items() if key.startswith(("self.", "cls."))})
            positional = [*definition.args.posonlyargs, *definition.args.args]
            parameters = positional[1:] if function.bound else positional
            for parameter in (*parameters, *definition.args.kwonlyargs):
                local[parameter.arg] = frozenset()
            for parameter, default in zip(positional[-len(definition.args.defaults):], definition.args.defaults):
                local[parameter.arg] = self.expression(default, globals_, function.source)
            for parameter, default in zip(definition.args.kwonlyargs, definition.args.kw_defaults):
                local[parameter.arg] = self.expression(default, globals_, function.source)
            for parameter, argument in zip(parameters, arguments):
                local[parameter.arg] = argument
            local.update(keywords)
            self.active.add(signature)
            results.update(self.statements(definition.body, local, function.source))
            self.active.remove(signature)
            if function.bound:
                self.merge(env, {key: value for key, value in local.items() if key.startswith(("self.", "cls."))})
        return frozenset(results)

    def statements(self, body, env, source, top=False):
        returned = set()
        for node in body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = self.local_module(alias.name, source)
                    if local:
                        env[alias.asname or alias.name] = values(Module(local))
                    elif alias.name in STANDARD:
                        env[alias.asname or alias.name.split(".")[0]] = values(Symbol(alias.name if alias.asname else alias.name.split(".")[0]))
            elif isinstance(node, ast.ImportFrom):
                local = self.local_module(node.module or "", source)
                if local:
                    _, globals_, functions = self.module(local)
                    for alias in node.names:
                        env[alias.asname or alias.name] = (values(Function(local, alias.name)) if alias.name in functions
                                                         else globals_.get(alias.name, frozenset()))
                elif node.module in STANDARD:
                    for alias in node.names:
                        env[alias.asname or alias.name] = values(Symbol(node.module + "." + alias.name))
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                result = self.expression(node.value, env, source)
                for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
                    self.assign(target, result, env)
            elif isinstance(node, ast.AugAssign):
                result = self.expression(ast.BinOp(left=node.target, op=node.op, right=node.value), env, source)
                self.assign(node.target, result, env)
            elif isinstance(node, ast.Return):
                returned.update(self.expression(node.value, env, source))
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                self.assign(node.target, self.iterate(self.expression(node.iter, env, source)), env)
                returned.update(self.statements(node.body + node.orelse, env, source))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not top:
                    # A nested helper is callable by name and its body sees the enclosing paths.
                    key = node.name + "@" + str(node.lineno)
                    self.modules[source][2][key] = node
                    env[node.name] = values(Function(source, key))
                    nested = env.copy()
                    signature = node.args
                    for parameter in (*signature.posonlyargs, *signature.args, *signature.kwonlyargs,
                                      signature.vararg, signature.kwarg):
                        if parameter is not None:
                            nested[parameter.arg] = frozenset()
                    self.statements(node.body, nested, source)
                continue
            elif isinstance(node, ast.ClassDef):
                methods = env.copy()
                self.statements([item for item in node.body if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))], methods, source)
                for item in node.body:
                    if isinstance(item, (ast.Assign, ast.AnnAssign)):
                        for target in item.targets if isinstance(item, ast.Assign) else [item.target]:
                            if isinstance(target, ast.Name):
                                for prefix in ("self.", "cls.", node.name + "."):
                                    methods[prefix + target.id] = methods.get(target.id, frozenset())
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods["self." + method.name] = values(Function(source, node.name + "." + method.name, True))
                env["@class:" + node.name] = methods
                continue
            else:
                for field in ("test", "value", "exc"):
                    self.expression(getattr(node, field, None), env, source)
                for field in ("body", "orelse", "finalbody"):
                    branch = env.copy()
                    returned.update(self.statements(getattr(node, field, []), branch, source))
                    self.merge(env, branch)
                if isinstance(node, (ast.With, ast.AsyncWith)):
                    for item in node.items:
                        self.expression(item.context_expr, env, source)
                for handler in getattr(node, "handlers", []):
                    branch = env.copy()
                    returned.update(self.statements(handler.body, branch, source))
                    self.merge(env, branch)
        return frozenset(returned)

    def scan(self, source):
        tree, env, _ = self.module(source)
        classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

        def lineage(node, seen=()):
            # Same-module bases contribute class state, fixtures and inherited methods.
            for base in node.bases:
                name = self.key(base)
                if name in classes and name not in seen:
                    yield from lineage(classes[name], (*seen, name))
            yield node

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.statements(node.body, env.copy(), source)
            elif isinstance(node, ast.ClassDef):
                chain = list(dict.fromkeys(lineage(node)))
                state = {}
                for item in chain:
                    state.update(env.get("@class:" + item.name, env))
                for setup in ("setUpClass", "setUp"):
                    for item in chain:
                        for method in item.body:
                            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and method.name == setup:
                                self.statements(method.body, state, source)
                                self.merge(state, {"self." + key[4:]: value for key, value in state.items() if key.startswith("cls.")})
                for item in chain:
                    for method in item.body:
                        if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            self.statements(method.body, state.copy(), source)


def registry_dependencies(root: Path, paths: list[str]) -> list[str]:
    analysis = PathReads(root)
    for relative in paths:
        if (relative.startswith("tools/") and relative.endswith(".py")
                and (Path(relative).name.startswith("test_") or "/tests/" in relative)
                and (root / relative).is_file()):
            analysis.scan(relative)
    return sorted(analysis.failures)
