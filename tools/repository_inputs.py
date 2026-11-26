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
from fnmatch import fnmatchcase
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
# These suites consume the live Builds pin or exercise the fixture that does.
PIN_SUITES = (
    "test_conversations_qualification.py",
    "test_delivery_workflow.py",
    "test_render.py",
    "test_render_legacy.py",
    "test_validate.py",
)
READS = {"read_text", "read_bytes", "open", "glob", "rglob", "iterdir", "exists", "is_file", "is_dir", "is_symlink", "stat", "lstat"}
# Standard-library calls whose path arguments are read, copied, executed or loaded.
SINKS = {"open", "io.open", "os.listdir", "os.scandir", "os.walk", "os.stat", "os.lstat",
         "os.path.exists", "os.path.isfile", "os.path.isdir", "shutil.copy", "shutil.copy2",
         "shutil.copyfile", "shutil.copytree", "shutil.move", "runpy.run_path"}
PROCESSES = {"subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_call", "subprocess.check_output"}
LOADERS = {"importlib.util.spec_from_file_location"}
STANDARD = {"pathlib", "io", "os", "os.path", "shutil", "runpy", "subprocess", "importlib", "importlib.util"}
# Helper calls nested deeper than this are not followed.
CALL_DEPTH = 12


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


class Scope(dict):
    """An environment that records the names written since it was copied.

    A copied branch still holds the enclosing value for every other name, and
    that value's union with itself is unchanged, so a merge visits only these.
    """
    __slots__ = ("written",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.written = set(self)

    def __setitem__(self, key, value):
        self.written.add(key)
        dict.__setitem__(self, key, value)

    def update(self, *args, **kwargs):
        changes = dict(*args, **kwargs)
        self.written.update(changes)
        dict.update(self, changes)

    def copy(self):
        branch = Scope.__new__(Scope)
        dict.update(branch, self)
        branch.written = set()
        return branch


def exact(value):
    """Return a memo key that keeps True and False apart from 1 and 0.

    They are equal members of a set, but an f-string formats them differently.
    """
    if value.__class__ is bool:
        return (bool, value)
    if isinstance(value, (frozenset, tuple)):
        return value.__class__(exact(item) for item in value)
    if isinstance(value, (Sequence, Mapping)):
        return (value.__class__, exact(value.items))
    return value


class Frame:
    """The calls one evaluation tried, including those of its nested calls."""
    __slots__ = ("depth", "epoch", "consulted", "deepest", "tainted")

    def __init__(self, depth, epoch):
        self.depth = depth
        self.epoch = epoch
        self.consulted = set()
        self.deepest = None
        self.tainted = False

    def observe(self, function, depth):
        self.consulted.add(function)
        self.reached(depth)

    def reached(self, depth):
        if self.deepest is None or depth > self.deepest:
            self.deepest = depth

    def absorb(self, entry, depth):
        self.consulted |= entry.consulted
        if entry.reach is not None:
            self.reached(depth + entry.reach)


class Entry:
    """A call evaluation and the stack conditions under which it repeats."""
    __slots__ = ("consulted", "outer", "depth", "reach", "epoch", "returned", "state")

    def __init__(self, frame, active, returned, state):
        self.consulted = frozenset(frame.consulted)
        self.outer = frozenset(function for function in active if function in self.consulted)
        self.depth = frame.depth
        self.reach = None if frame.deepest is None else frame.deepest - frame.depth
        self.epoch = frame.epoch
        self.returned = returned
        self.state = state

    def applies(self, active, depth, epoch):
        # Each tried call must again be skipped exactly when it was skipped:
        # for being on the stack, or for exceeding the depth limit.
        if epoch != self.epoch or frozenset(function for function in active if function in self.consulted) != self.outer:
            return False
        if self.reach is None:
            return True
        if self.depth + self.reach < CALL_DEPTH:
            return depth + self.reach < CALL_DEPTH
        return depth == self.depth


class PathReads:
    """Bounded Python path flow for evidence and suite input reads.

    Unknown fixture objects stay unknown. Known paths retain their identity
    through assignments, parameters, returned values and repository helpers.
    Both sides of conditionals are visited, so an unexecuted test branch cannot
    hide a dependency. This is a dependency guard, not a Python interpreter.
    """
    def __init__(self, root: Path, *, check_registry=True, pin_suite=None):
        self.root = root.resolve()
        self.check_registry = check_registry
        self.pin_suite = pin_suite
        self.modules = {}
        self.failures = set()
        self.active = set()
        self.imported_classes = set()
        # Reusable call evaluations, the evaluations in progress, and each
        # loading module with the number of evaluations begun before its load.
        self.memo = {}
        self.frames = []
        self.loading = {}
        self.sealed = set()
        self.epoch = 0

    def module(self, source):
        if source in self.modules:
            if source in self.loading:
                # Evaluations begun during this load see partial globals.
                for frame in self.frames[self.loading[source]:]:
                    frame.tainted = True
            return self.modules[source]
        path = self.root / source
        tree = ast.parse(path.read_text(), filename=source)
        env = Scope({"__file__": values(str(path))})
        functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                functions.update({node.name + "." + method.name: method for method in node.body
                                  if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))})
        self.modules[source] = (tree, env, functions)
        env.update({name: values(Function(source, name)) for name in functions})
        self.loading[source] = len(self.frames)
        self.statements(tree.body, env, source, top=True)
        del self.loading[source]
        # Loaded globals stay fixed unless a call merges self./cls. state into them.
        self.sealed.add(id(env))
        return self.modules[source]

    def local_module(self, name, source):
        parts = name.split(".")
        for directory in (Path(source).parent, Path("tools")):
            target = directory.joinpath(*parts)
            package = target / "__init__.py"
            module = target.with_suffix(".py") if name else directory / ".py"
            if self.pin_suite and name and (self.root / package).is_file():
                module = package
            if (self.root / module).is_file():
                if self.pin_suite:
                    for index in range(1, len(parts)):
                        initializer = directory.joinpath(*parts[:index], "__init__.py")
                        if (self.root / initializer).is_file():
                            self.module(initializer.as_posix())
                return module.as_posix()
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
        for key in branch.written if isinstance(branch, Scope) else branch:
            value = branch[key]
            if isinstance(value, frozenset):
                current = env.get(key, frozenset())
                if current is not value:
                    env[key] = current | value

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
                        target = Path(os.path.normpath(self.root / path.value)) if self.pin_suite else Path(path.value)
                        relative = target.relative_to(self.root).as_posix()
                    except ValueError:
                        continue
                    if (self.root / relative).is_file():
                        return values(Module(relative))
        return None

    def check(self, paths, source, line, *, pin=True):
        for path in paths:
            if isinstance(path, str):
                path = FilePath(path)
            if not isinstance(path, FilePath):
                continue
            normalized = Path(os.path.normpath(self.root / path.value))
            for directory in ("setup", "rendered") if self.check_registry else ():
                if normalized == self.root / directory or self.root / directory in normalized.parents:
                    self.failures.add(f"{source}:{line}: suite reads repository-root {directory}/")
            if pin and self.pin_suite and normalized == self.root / "builds-version":
                self.failures.add(f"{source}:{line}: {self.pin_suite} reads repository-root builds-version")
            if EVIDENCE_ROOT in normalized.parts:
                self.failures.add(f"{source}:{line}: active Python path reads evidence")

    def process_pin(self, commands, cwd, source, line):
        """Check explicit argv paths and Git's revision:path syntax."""
        for command in commands:
            if not isinstance(command, Sequence) or not command.items:
                continue
            argv = tuple(frozenset(item.value if isinstance(item, FilePath) else item
                                   for item in argument if isinstance(item, (str, FilePath)))
                         for argument in command.items)
            git = any(Path(executable).name == "git" for executable in argv[0])
            directory = cwd
            for index, argument in enumerate(argv[1:], 1):
                if git and "-C" in argument and index + 1 < len(argv):
                    directory = frozenset(os.path.normpath(Path(base) / value)
                                          for base in directory or ("",) for value in argv[index + 1]
                                          if base or os.path.isabs(value))
                for value in argument:
                    path = value.split(":", 1)[1] if git and ":" in value else value
                    if Path(path).name != "builds-version":
                        continue
                    candidates = values(path) if os.path.isabs(path) else values(*(str(Path(base) / path) for base in directory))
                    self.check(candidates, source, line)

    def expression(self, node, env, source):
        if node is None:
            return frozenset()
        if isinstance(node, ast.Constant):
            return values(node.value) if isinstance(node.value, (str, int)) else frozenset()
        if isinstance(node, ast.Name):
            return env.get(node.id, frozenset())
        if isinstance(node, (ast.List, ast.Tuple)):
            items = [()]
            for item in node.elts:
                if self.pin_suite and isinstance(item, ast.Starred):
                    spreads = [value.items for value in self.expression(item.value, env, source) if isinstance(value, Sequence)]
                    items = [prefix + spread for prefix in items for spread in spreads or [(frozenset(),)]]
                else:
                    value = self.expression(item, env, source)
                    items = [prefix + (value,) for prefix in items]
            return values(*(Sequence(item) for item in items))
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
        if self.pin_suite and name == "map" and len(node.args) == 2 and self.key(node.args[0]) in {"str", "os.fspath"}:
            return arguments[1]
        supplied = [*arguments, *keywords.values()]
        if names & SINKS:
            self.check(self.iterate(frozenset().union(*supplied)), source, node.lineno)
        if names & PROCESSES:
            # Relative strings are resolved by the child's cwd; constructed or absolute paths are known.
            self.check(frozenset(item for item in self.iterate(frozenset().union(*supplied))
                                 if isinstance(item, FilePath) or isinstance(item, str) and os.path.isabs(item)),
                       source, node.lineno, pin=False)
            if self.pin_suite:
                cwd = keywords.get("cwd", values(str(self.root)))
                directories = [item.value if isinstance(item, FilePath) else item for item in cwd
                               if isinstance(item, (str, FilePath))]
                self.process_pin(arguments[0] if arguments else keywords.get("args", ()),
                                 directories, source, node.lineno)
        if self.pin_suite and "runpy.run_path" in names:
            for module in self.loaded(arguments or [keywords.get("path_name", ())]) or ():
                self.module(module.source)
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
            if self.pin_suite and attr in {"with_suffix", "with_stem"} and arguments:
                result = set()
                for path, part in itertools.product(base, arguments[0]):
                    if isinstance(path, FilePath) and isinstance(part, str):
                        try:
                            result.add(FilePath(str(getattr(Path(path.value), attr)(part))))
                        except ValueError:
                            pass
                return frozenset(result)
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
                if self.pin_suite and attr in {"glob", "rglob"} and arguments:
                    for directory, pattern in itertools.product(base, arguments[0]):
                        if isinstance(directory, FilePath) and isinstance(pattern, str):
                            target = Path(os.path.normpath(self.root / directory.value / pattern))
                            if target.parent == self.root and fnmatchcase("builds-version", target.name):
                                self.check(values(FilePath(str(self.root / "builds-version"))), source, node.lineno)
                return paths
        results = set()
        for function in self.expression(node.func, env, source):
            if not isinstance(function, Function):
                continue
            if self.frames:
                self.frames[-1].observe(function, len(self.active))
            if function in self.active or len(self.active) >= CALL_DEPTH:
                continue
            _, globals_, functions = self.module(function.source)
            if function.name not in functions:
                continue
            shared = ({key: value for key, value in env.items() if key.startswith(("self.", "cls."))}
                      if function.bound else {})
            returned, state = self.invoke(function, functions[function.name], globals_, shared, arguments, keywords)
            results.update(returned)
            if function.bound:
                if id(env) in self.sealed:
                    # A default expression's bound call changed loaded globals: kept evaluations no longer apply.
                    self.epoch += 1
                self.merge(env, state)
        return frozenset(results)

    def invoke(self, function, definition, globals_, shared, arguments, keywords):
        """Evaluate a call body, reusing an earlier evaluation of identical inputs.

        The body sees only its module globals, the arguments and the caller's
        self./cls. state. Module globals are fixed once loaded, so calls into a
        loading module and evaluations that read its partial globals are not
        kept. Everything else an evaluation adds (failures, loaded modules,
        nested helpers, scanned classes) is idempotent. The active call stack is
        the remaining input: an entry keeps the functions its evaluation tried
        to call and how deep it went, and is reused only where each of those
        calls is allowed or skipped alike.
        """
        if function.source in self.loading:
            return self.evaluate(function, definition, globals_, shared, arguments, keywords)
        key = exact((function, tuple(arguments), frozenset(keywords.items()), frozenset(shared.items())))
        depth = len(self.active)
        for entry in self.memo.get(key, ()):
            if entry.applies(self.active, depth, self.epoch):
                if self.frames:
                    self.frames[-1].absorb(entry, depth)
                return entry.returned, entry.state
        frame = Frame(depth, self.epoch)
        self.frames.append(frame)
        returned, state = self.evaluate(function, definition, globals_, shared, arguments, keywords)
        self.frames.pop()
        entry = Entry(frame, self.active, returned, state)
        if not frame.tainted and frame.epoch == self.epoch:
            self.memo.setdefault(key, []).append(entry)
        if self.frames:
            self.frames[-1].absorb(entry, depth)
        return returned, state

    def evaluate(self, function, definition, globals_, shared, arguments, keywords):
        local = globals_.copy()
        if function.bound:
            local.update(shared)
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
        if self.pin_suite and definition.args.vararg:
            local[definition.args.vararg.arg] = values(Sequence(tuple(arguments[len(parameters):])))
        local.update(keywords)
        self.active.add(function)
        returned = self.statements(definition.body, local, function.source)
        self.active.remove(function)
        state = ({key: value for key, value in local.items() if key.startswith(("self.", "cls."))}
                 if function.bound else None)
        return returned, state

    def statements(self, body, env, source, top=False):
        returned = set()
        for node in body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = self.local_module(alias.name, source)
                    if local:
                        env[alias.asname or alias.name] = values(Module(local))
                        if self.pin_suite:
                            # Plain imports execute top-level reads even when
                            # the suite never accesses a module attribute.
                            self.module(local)
                    elif alias.name in STANDARD:
                        env[alias.asname or alias.name.split(".")[0]] = values(Symbol(alias.name if alias.asname else alias.name.split(".")[0]))
            elif isinstance(node, ast.ImportFrom):
                local = self.local_module(node.module or "", source)
                if local:
                    _, globals_, functions = self.module(local)
                    for alias in node.names:
                        env[alias.asname or alias.name] = (values(Function(local, alias.name)) if alias.name in functions
                                                         else globals_.get(alias.name, frozenset()))
                        imported = (local, alias.name)
                        if self.pin_suite and ("@class:" + alias.name) in globals_ and imported not in self.imported_classes:
                            self.imported_classes.add(imported)
                            self.scan(local, test_class=alias.name)
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

    def scan(self, source, *, test_class=None):
        tree, env, _ = self.module(source)
        classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

        def lineage(node, seen=()):
            # Same-module bases contribute class state, fixtures and inherited methods.
            for base in node.bases:
                name = self.key(base)
                if name in classes and name not in seen:
                    yield from lineage(classes[name], (*seen, name))
            yield node

        for node in tree.body if test_class is None else [classes[test_class]]:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.statements(node.body, env.copy(), source)
            elif isinstance(node, ast.ClassDef):
                chain = list(dict.fromkeys(lineage(node)))
                if test_class and not any(method.name.startswith("test_") for item in chain for method in item.body
                                          if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))):
                    continue
                state = Scope()
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


def pin_dependencies(root: Path, paths: list[str]) -> list[str]:
    selected = {f"tools/tests/{suite}" for suite in PIN_SUITES}
    failures = set()
    for relative in paths:
        path = root / relative
        if (relative.startswith("tools/") and path.match("test_*.py")
                and relative not in selected and path.is_file()):
            # Give each entry point its own analysis so imported reads keep
            # the consuming suite even when several suites share a helper.
            analysis = PathReads(root, check_registry=False, pin_suite=relative)
            analysis.scan(relative)
            failures.update(analysis.failures)
    return sorted(failures)
