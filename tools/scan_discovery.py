"""Static action/script reachability. No module text is ever evaluated."""
from __future__ import annotations

import ast
from collections import deque
from pathlib import PurePosixPath
import posixpath
import re
import shlex

import yaml

from delivery_runtime import DeliveryError, clean

FORMATS = {".yml": "yaml", ".yaml": "yaml", ".sh": "bash", ".bash": "bash",
           ".ps1": "powershell", ".psm1": "powershell", ".py": "python"}
MAX_FILES = 2000
MAX_BYTES = 32 * 1024 * 1024
# Environment variables that change which local Python sources are imported.
RESOLUTION = {"PYTHONPATH", "PYTHONHOME", "PYTHONSAFEPATH"}
# Commands that execute their operand after this many fixed positional values.
WRAPPERS = {"env": 0, "exec": 0, "command": 0, "time": 0, "nohup": 0, "nice": 0, "sudo": 0, "doas": 0,
            "setsid": 0, "stdbuf": 0, "ionice": 0, "unbuffer": 0, "xargs": 0, "timeout": 1, "flock": 1, "chrt": 1}
OTHER_LANGUAGES = {".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".rb", ".pl", ".pm", ".php"}
COMMAND_APIS = {"subprocess.run", "subprocess.call", "subprocess.Popen", "subprocess.check_call",
                "subprocess.check_output", "subprocess.getoutput", "subprocess.getstatusoutput",
                "os.system", "os.popen", "runpy.run_path", "runpy.run_module"}
UNSUPPORTED_PREFIXES = ("os.exec", "os.spawn", "os.posix_spawn", "asyncio.create_subprocess_", "pty.spawn")
UNSUPPORTED_CALLS = {"importlib.util.spec_from_file_location", "importlib.machinery.SourceFileLoader",
                     "importlib.machinery.SourcelessFileLoader", "exec", "compile"}
PROCESS_MODULES = {"subprocess", "os", "runpy", "importlib", "importlib.util", "importlib.machinery",
                   "asyncio", "pty", "contextlib", "functools"}


def assignment(word):
    """Return whether a shell word is NAME=value; import-path overrides fail."""
    match = re.match(r"([A-Za-z_]\w*)=", word)
    if match and match[1].upper() in RESOLUTION:
        raise DeliveryError("unsupported environment assignment affecting script resolution")
    return match is not None


def executes(name):
    return (name in COMMAND_APIS or name in UNSUPPORTED_CALLS or name.startswith(UNSUPPORTED_PREFIXES)
            or name in {"importlib.import_module", "__import__"})


def literal_key(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.upper() not in RESOLUTION


class ActionLoader(yaml.SafeLoader):
    """Ambiguous YAML keys cannot silently replace a script invocation."""


class ActionMap(dict):
    pass


def mapping(loader, node):
    value = ActionMap()
    value.locations = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str) or key in value:
            raise DeliveryError("invalid or duplicate action mapping key")
        value[key] = loader.construct_object(value_node, deep=True)
        value.locations[key] = value_node.start_mark.line + 1 + int(getattr(value_node, "style", None) in {"|", ">"})
    return value


ActionLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def safe_path(value):
    if (not isinstance(value, str) or not value or value.startswith("/") or "\\" in value
            or any(ord(c) < 32 or ord(c) == 127 for c in value)
            or any(p in {"", ".", "..", ".git"} for p in value.split("/"))):
        raise DeliveryError("unsafe source path: " + clean(value))
    return value


class Discovery:
    def __init__(self, git, revision):
        self.git, self.revision = git, revision
        self.items = git.items(revision)
        self.files, self.errors, self.queue, self.visited = {}, [], deque(), set()
        self.total = 0

    def error(self, path, line, message):
        self.errors.append(f"{clean(path)}:{line}: {clean(message)}")

    def add(self, path, fmt=None, cwd=".", action=None, *, python_roots=None, sourced=False):
        path = safe_path(path)
        item = self.items.get(path)
        if item is None or item[:2] not in (("100644", "blob"), ("100755", "blob")):
            raise DeliveryError("missing or unsafe regular script/action: " + clean(path))
        fmt = fmt or FORMATS.get(PurePosixPath(path).suffix.lower())
        raw = None
        if fmt is None:
            raw = self.git.blob(self.revision, path)
            first = raw.split(b"\n", 1)[0]
            if first.startswith(b"#!"):
                fmt = "python" if b"python" in first else "powershell" if b"pwsh" in first else (
                    "bash" if re.search(rb"\b(?:ba)?sh\b", first) else None)
        if fmt not in {"yaml", "bash", "powershell", "python"}:
            raise DeliveryError("unsupported local-script language: " + clean(path))
        if path not in self.files:
            if len(self.files) >= MAX_FILES:
                raise DeliveryError("module selected-file limit exceeded")
            raw = raw if raw is not None else self.git.blob(self.revision, path)
            self.total += len(raw)
            if self.total > MAX_BYTES:
                raise DeliveryError("module selected-source byte limit exceeded")
            try:
                text = raw.decode("utf-8")
            except UnicodeError:
                raise DeliveryError("source is not UTF-8: " + clean(path)) from None
            if "\0" in text:
                raise DeliveryError("source contains NUL: " + clean(path))
            self.files[path] = {"format": fmt, "text": text}
        elif self.files[path]["format"] != fmt:
            raise DeliveryError("ambiguous script language: " + clean(path))
        key = (path, cwd, action, python_roots, sourced)
        if key not in self.visited:
            self.visited.add(key)
            if len(self.visited) > 4 * MAX_FILES:
                raise DeliveryError("script traversal limit exceeded")
            self.queue.append(key)

    def resolve(self, value, *, path, cwd, action, allow_root=False):
        if not isinstance(value, str):
            raise DeliveryError("unresolved local-script target")
        value = value.replace("\\", "/")
        replacements = {
            "${{ github.workspace }}": ".", "${GITHUB_WORKSPACE}": ".", "$GITHUB_WORKSPACE": ".",
            "$env:GITHUB_WORKSPACE": ".", "${env:GITHUB_WORKSPACE}": ".",
            "$PSScriptRoot": str(PurePosixPath(path).parent),
            "${PSScriptRoot}": str(PurePosixPath(path).parent),
        }
        if action:
            for marker in ("${{ github.action_path }}", "${GITHUB_ACTION_PATH}", "$GITHUB_ACTION_PATH",
                           "$env:GITHUB_ACTION_PATH", "${env:GITHUB_ACTION_PATH}"):
                replacements[marker] = action
        anchored = any(value.startswith(marker) for marker in replacements)
        for marker in sorted(replacements, key=len, reverse=True):
            value = value.replace(marker, replacements[marker])
        if any(c in value for c in ("$", "`", "*", "?", "{", "}", "~")):
            raise DeliveryError("unresolved local-script target: " + clean(value))
        joined = posixpath.join("." if anchored else cwd, value)
        components, traversed = joined.split("/"), []
        for index, component in enumerate(components):
            if component in {"", "."}:
                continue
            if component == "..":
                if not traversed:
                    raise DeliveryError("source path escapes module")
                traversed.pop()
            else:
                traversed.append(component)
                prefix = "/".join(traversed)
                if index < len(components) - 1 and prefix in self.items:
                    raise DeliveryError("unsafe non-directory source path component: " + clean(prefix))
        value = posixpath.normpath(joined)
        if allow_root and value == ".":
            return value
        return safe_path(value)

    def action(self, path, text):
        try:
            value = yaml.load(text, Loader=ActionLoader)
            if (not isinstance(value, dict) or not isinstance(value.get("runs"), dict)
                    or value["runs"].get("using") != "composite"
                    or not isinstance(value["runs"].get("steps"), list)):
                raise DeliveryError("invalid composite action")
            if len(value["runs"]["steps"]) > 1000:
                raise DeliveryError("action step limit exceeded")
            parent = str(PurePosixPath(path).parent)
            for step in value["runs"]["steps"]:
                if not isinstance(step, dict):
                    raise DeliveryError("invalid action step")
                if "uses" in step:
                    target = step["uses"]
                    if not isinstance(target, str):
                        raise DeliveryError("invalid action target")
                    if target.startswith("./"):
                        directory = self.resolve(target, path=path, cwd=".", action=parent)
                        candidates = [directory + "/" + name for name in ("action.yml", "action.yaml")
                                      if directory + "/" + name in self.items]
                        if not directory.startswith(".github/actions/") or len(candidates) != 1:
                            raise DeliveryError("missing/ambiguous local action: " + clean(target))
                        self.add(candidates[0], "yaml", action=directory)
                    elif not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[0-9a-fA-F]{40}", target):
                        raise DeliveryError("unresolved or unpinned action target: " + clean(target))
                elif "run" in step:
                    command, shell = step["run"], step.get("shell")
                    if not isinstance(command, str) or not isinstance(shell, str):
                        raise DeliveryError("action run requires literal command and shell")
                    if isinstance(step.get("env"), dict) and any(str(key).upper() in RESOLUTION for key in step["env"]):
                        raise DeliveryError("unsupported step environment affecting script resolution")
                    cwd = "."
                    if "working-directory" in step:
                        cwd = self.resolve(step["working-directory"], path=path, cwd=".", action=parent, allow_root=True)
                    line = step.locations.get("run", 1)
                    if shell.split()[0] in {"python", "python3"}:
                        self.python(path, command, cwd, parent, roots=(cwd,), offset=line - 1)
                    elif shell.split()[0] in {"bash", "sh", "pwsh", "powershell"}:
                        self.commands(path, command, cwd, parent, offset=line - 1,
                                      powershell=shell.split()[0] in {"pwsh", "powershell"})
                    else:
                        raise DeliveryError("unsupported action shell: " + clean(shell))
                else:
                    raise DeliveryError("action step has no run/uses")
        except (yaml.YAMLError, RecursionError, TypeError, ValueError) as error:
            self.error(path, 1, "invalid action/discovery: " + clean(error))

    def commands(self, path, text, cwd, action, *, offset=0, powershell=False, sourced=False):
        # Shell state is intentionally limited to literal cd/working-directory.
        # Computed executable/script targets fail; ordinary data arguments do not
        # become reachability edges merely because their name ends in .py/.sh.
        text = text.removeprefix("﻿")
        if powershell:
            # Comment-based help is data; blanking it keeps diagnostic line numbers.
            text = re.sub(r"(?ms)^[ \t]*<#.*?#>", lambda match: "\n" * match[0].count("\n"), text)
        text = re.sub(r"[\\`]\r?\n", " ", text)
        for number, line in enumerate(text.splitlines(), 1 + offset):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                # Replace spaced Actions expressions before shell tokenization.
                line = re.sub(r"\$\{\{\s*github\.(workspace|action_path)\s*\}\}",
                              lambda m: "$GITHUB_WORKSPACE" if m[1] == "workspace" else "$GITHUB_ACTION_PATH", line)
                # Reject execution syntax outside literal quotes before shlex
                # can discard its structure and certify the wrong scope.
                single, double, escaped, syntax, cut = False, False, False, [], len(line)
                for index, char in enumerate(line):
                    if escaped:
                        escaped = False
                        syntax.append(" ")
                        continue
                    # A comment starts only at a word boundary: $#, ${#x} and a#b are words.
                    if char == "#" and not single and not double and (index == 0 or line[index - 1] in " \t;&|()<>"):
                        cut = index
                        break
                    if char == ("`" if powershell else "\\") and not single:
                        escaped = True
                        syntax.append(" ")
                        continue
                    if char == "'" and not double:
                        single = not single
                    elif char == '"' and not single:
                        double = not double
                    elif not single and (line[index:index + 2] == "$(" or (char == "`" and not powershell)):
                        raise DeliveryError("unsupported shell command substitution")
                    syntax.append(char if not single and not double and char not in "'\"" else " ")
                structure = "".join(syntax)
                if ("(" in structure or ")" in structure
                        or re.search(r"(?:^|[;&|])\s*\{|^\s*function\b", structure)):
                    raise DeliveryError("unsupported shell compound/subshell execution")
                lex = shlex.shlex(line[:cut], posix=True, punctuation_chars=";&|()")
                if powershell:
                    lex.escape = ""
                lex.whitespace_split, lex.commenters = True, ""
                segments, words = [], []
                for word in lex:
                    if word and set(word) <= set(";&|()"):
                        if words:
                            segments.append(words)
                            words = []
                    else:
                        words.append(word)
                if words:
                    segments.append(words)
                for words in segments:
                    while words and (words[0] in {"then", "do", "else", "if", "elif", "while", "until", "!", "&"}
                                     or assignment(words[0])):
                        words = words[1:]
                    if not words:
                        continue
                    while words and words[0] in WRAPPERS:
                        positional = WRAPPERS[words[0]]
                        words = words[1:]
                        if words and words[0].startswith("-"):
                            raise DeliveryError("unsupported shell wrapper options")
                        words = words[positional:]
                        while words and assignment(words[0]):
                            words = words[1:]
                    if words[:2] == ["uv", "run"]:
                        words = words[2:]
                        while words and words[0].startswith("-"):
                            if words[0] in {"--directory", "-C"} or words[0].startswith("--directory="):
                                raise DeliveryError("unsupported uv working-directory option")
                            if words[0] in {"--python", "--project", "--with", "--with-requirements"}:
                                words = words[2:]
                            else:
                                words = words[1:]
                    if not words:
                        raise DeliveryError("unresolved wrapped script invocation")
                    cmd, args = words[0], words[1:]
                    builtin = cmd.lower()
                    if (builtin in {"pushd", "popd", "push-location", "pop-location", "set-location", "sl", "chdir"}
                            or (powershell and builtin == "cd")):
                        raise DeliveryError("unsupported shell working-directory command")
                    if builtin == "start-process":
                        raise DeliveryError("unsupported PowerShell process invocation")
                    if builtin in {"invoke-command", "icm"}:
                        raise DeliveryError("unsupported PowerShell Invoke-Command execution")
                    if builtin in {"export", "declare", "typeset", "readonly", "local"}:
                        if any(argument.split("=", 1)[0].upper() in RESOLUTION for argument in args):
                            raise DeliveryError("unsupported environment assignment affecting script resolution")
                        continue
                    if builtin in {"eval", "invoke-expression", "iex"}:
                        if args[:1] and args[0].lower() == "-command":
                            args = args[1:]
                        # Evaluated text runs in this shell, so a directory change
                        # inside it fails rather than leaving a stale caller cwd.
                        self.commands(path, " ".join(args), cwd, action, offset=number - 1,
                                      powershell=powershell, sourced=True)
                        continue
                    if builtin == "trap" and not powershell:
                        if args and args[0] != "-" and not args[0].startswith("-"):
                            self.commands(path, args[0], cwd, action, offset=number - 1, sourced=True)
                        continue
                    if builtin == "find":
                        for index, argument in enumerate(args):
                            if argument in {"-execdir", "-okdir"}:
                                raise DeliveryError("unsupported find -execdir working directory")
                            if argument in {"-exec", "-ok"}:
                                inner = []
                                for word in args[index + 1:]:
                                    if word in {"-exec", "-ok", "-execdir", "-okdir"}:
                                        break
                                    inner.append(word)
                                if not inner or inner[0] == "{}":
                                    raise DeliveryError("unresolved computed find -exec command")
                                self.commands(path, shlex.join(inner), cwd, action, offset=number - 1)
                        continue
                    if cmd == "cd":
                        if sourced:
                            raise DeliveryError("sourced script changes caller working directory; coverage unsupported")
                        if len(args) != 1:
                            raise DeliveryError("unresolved local working directory")
                        cwd = self.resolve(args[0], path=path, cwd=cwd, action=action, allow_root=True)
                        continue
                    base = PurePosixPath(cmd).name.lower().removesuffix(".exe")
                    fmt, target = None, None
                    if re.fullmatch(r"(?:python|pypy)(?:\d+(?:\.\d+)*)?|py", base):
                        fmt = "python"
                        mode, value, remaining = self.python_options(args)
                        if mode == "m":
                            self.import_module(value, path, cwd, action, roots=(cwd,), required=True, execute=True)
                            continue
                        if mode == "c":
                            self.python(path, value, cwd, action, roots=(cwd,), offset=number - 1)
                            continue
                        target = remaining[0] if remaining else None
                        if target is None or target in {"-", "<<"} or target.startswith("<<"):
                            raise DeliveryError("unresolved Python script target")
                    elif base in {"bash", "sh", "pwsh", "powershell"}:
                        fmt = "powershell" if base in {"pwsh", "powershell"} else "bash"
                        inline, remaining = self.shell_options(args, fmt == "powershell")
                        if inline:
                            if not remaining:
                                raise DeliveryError("unresolved shell command")
                            self.commands(path, remaining[0], cwd, action, offset=number - 1,
                                          powershell=fmt == "powershell")
                            continue
                        target = remaining[0] if remaining else None
                        if target is None:
                            raise DeliveryError("unresolved shell script target")
                    elif base in {"node", "nodejs", "deno", "bun", "ruby", "perl", "php"}:
                        for argument in args:
                            if PurePosixPath(argument).suffix.lower() in OTHER_LANGUAGES:
                                try:
                                    resolved = self.resolve(argument, path=path, cwd=cwd, action=action)
                                except DeliveryError:
                                    continue
                                if resolved in self.items:
                                    raise DeliveryError("unsupported local-script language: " + clean(resolved))
                    elif powershell and builtin == "using":
                        if len(args) >= 2 and args[0].lower() == "module" and (
                                args[1].lower().endswith(".psm1") or any(c in args[1] for c in "/\\$")):
                            target, fmt = args[1], "powershell"
                    elif cmd in {".", "source"}:
                        target = args[0] if args else None
                        fmt = FORMATS.get(PurePosixPath(target or "").suffix.lower(), "bash")
                    elif cmd.lower() == "import-module":
                        if args and args[0].lower() == "-name":
                            args = args[1:]
                        if not args or args[0].startswith("-"):
                            raise DeliveryError("unresolved PowerShell module parameter form")
                        if args[0].lower().endswith(".psm1") or any(c in args[0] for c in "/\\$"):
                            target, fmt = args[0], "powershell"
                    elif FORMATS.get(PurePosixPath(cmd).suffix.lower()) in {"bash", "powershell", "python"}:
                        target = cmd
                    elif cmd.startswith(("./", "../", ".\\", "..\\")) or (
                            "/" in cmd and not cmd.startswith("/")):
                        target = cmd
                    elif "$" in cmd or "`" in cmd:
                        raise DeliveryError("unresolved computed command: " + clean(cmd))
                    if target is not None:
                        resolved = self.resolve(target, path=path, cwd=cwd, action=action)
                        self.add(resolved, fmt, cwd=cwd, action=action, sourced=cmd in {".", "source"})
                    elif cmd in {".", "source"}:
                        raise DeliveryError("unresolved sourced script")
            except (ValueError, RecursionError) as error:
                self.error(path, number, "local-script discovery: " + clean(error))

    @staticmethod
    def python_options(args):
        """Parse interpreter options before the script; later words are its arguments."""
        remaining = list(args)
        while remaining and remaining[0].startswith("-") and remaining[0] != "-":
            option = remaining.pop(0)
            if option == "--":
                break
            if option.startswith("--") or re.fullmatch(r"-\d+(?:\.\d+)*(?:-\d+)?", option):
                if option == "--check-hash-based-pycs" and remaining:
                    remaining.pop(0)
                continue
            if option[1] in "WX":
                if len(option) == 2 and remaining:
                    remaining.pop(0)
                continue
            short = re.fullmatch(r"-[bBdEhiIOPqRsSuvVx]*([cm]?)(.*)", option, re.S)
            if not short or (short[2] and not short[1]):
                raise DeliveryError("unsupported Python interpreter option")
            if short[1]:
                value = short[2] or (remaining.pop(0) if remaining else None)
                if value is None:
                    raise DeliveryError("unresolved python -m target" if short[1] == "m" else "unresolved inline Python")
                return short[1], value, remaining
        return None, None, remaining

    @staticmethod
    def shell_options(args, powershell):
        """Parse shell options before the script or inline command operand."""
        remaining = list(args)
        while remaining and remaining[0][:1] in {"-", "+"} and remaining[0] not in {"-", "+"}:
            option = remaining.pop(0)
            lower = option.lower()
            if not powershell:
                if option == "--":
                    break
                if option in {"-o", "+o", "-O", "+O"}:
                    remaining = remaining[1:]
                elif option[0] == "-" and not option.startswith("--") and "c" in option[1:]:
                    return True, remaining
                continue
            # PowerShell parameters are case-insensitive unambiguous prefixes.
            if lower == "-c" or (len(lower) > 4 and "-command".startswith(lower)):
                return True, remaining
            if lower in {"-e", "-ec", "-cwa", "-commandwithargs"} or (len(lower) > 2 and "-encodedcommand".startswith(lower)):
                raise DeliveryError("unsupported PowerShell encoded or argument command")
            if lower == "-wd" or (len(lower) > 2 and "-workingdirectory".startswith(lower)):
                raise DeliveryError("unsupported PowerShell working-directory option")
            if lower == "-f" or (len(lower) > 2 and "-file".startswith(lower)):
                break
            if (lower in {"-ep", "-if", "-inputformat", "-of", "-o", "-outputformat", "-v", "-version", "-config",
                          "-configurationname", "-settingsfile", "-w", "-windowstyle"}
                    or (len(lower) > 2 and "-executionpolicy".startswith(lower))):
                remaining = remaining[1:]
        return False, remaining

    def import_module(self, module, path, cwd, action, *, roots=None, required=False, relative=0, execute=False):
        if not isinstance(module, str) or not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", module):
            raise DeliveryError("unresolved local Python module")
        parent = str(PurePosixPath(path).parent)
        import_roots = roots if roots is not None else (parent,)
        if relative:
            for _ in range(relative - 1):
                parent = str(PurePosixPath(parent).parent)
            search_roots = (parent,)
        else:
            search_roots = import_roots
        selected = []
        for root in search_roots:
            stem = posixpath.normpath(posixpath.join(root, module.replace(".", "/")))
            candidates = [p for p in (stem + ".py", stem + "/__init__.py") if p in self.items]
            namespace = not candidates and stem not in self.items and any(source.startswith(stem + "/") for source in self.items)
            if not candidates and not namespace:
                continue
            selected.append(stem)
            for target in candidates:
                self.add(target, "python", cwd=cwd, action=action, python_roots=import_roots)
                # Importing a submodule executes every package initializer.
                for parent_path in PurePosixPath(target).parents:
                    init = str(parent_path / "__init__.py")
                    if init in self.items and init != target:
                        self.add(init, "python", cwd=cwd, action=action, python_roots=import_roots)
            if execute and (namespace or stem + "/__init__.py" in candidates):
                self.add(stem + "/__main__.py", "python", cwd=cwd, action=action, python_roots=import_roots)
        if selected:
            return selected
        if relative:
            raise DeliveryError("missing local Python module: " + clean(module))
        if required:
            # A missing child of a local package is a missing local call; a
            # name without a local top-level package is an installed tool.
            top = module.split(".", 1)[0]
            for root in search_roots:
                stem = posixpath.normpath(posixpath.join(root, top))
                if stem + ".py" in self.items or any(source.startswith(stem + "/") for source in self.items):
                    raise DeliveryError("missing local Python module: " + clean(module))
        return None

    def python(self, path, text, cwd, action, *, roots=None, offset=0):
        roots = roots if roots is not None else (str(PurePosixPath(path).parent),)
        try:
            tree = ast.parse(text.removeprefix("﻿"))
        except (SyntaxError, ValueError, RecursionError) as error:
            self.error(path, getattr(error, "lineno", 1) + offset, "invalid Python source")
            return
        nodes = []
        for index, node in enumerate(ast.walk(tree)):
            if index > 100000:
                self.error(path, 1, "Python discovery node limit exceeded")
                return
            nodes.append(node)
        # Imports can occur in functions, classes, conditionals and exception
        # handlers. Retain every static binding rather than letting another
        # scope's reused alias erase an invocation edge. Ambiguous bindings are
        # deliberately conservative: all recognized possibilities are examined.
        aliases = {}
        for node in nodes:
            if isinstance(node, ast.Import):
                for item in node.names:
                    aliases.setdefault(item.asname or item.name, set()).add(item.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                for item in node.names:
                    aliases.setdefault(item.asname or item.name, set()).add(node.module + "." + item.name)

        def names(expression):
            head, dot, tail = expression.partition(".")
            # Subscript writes such as sys.path[:] and an alias[:] have no dot
            # after an aliased list name, so preserve that suffix separately.
            if "[" in head:
                head, bracket, subscript = head.partition("[")
                suffix = bracket + subscript + (dot + tail if dot else "")
            else:
                suffix = dot + tail if dot else ""
            return {target + suffix for target in aliases.get(head, {head})}

        assignments = [node for node in nodes if isinstance(node, (ast.Assign, ast.AnnAssign))]
        for _ in range(8):
            changed = False
            for node in assignments:
                if node.value is None or not isinstance(node.value, (ast.Name, ast.Attribute)):
                    continue
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                resolved = {candidate for candidate in names(ast.unparse(node.value))
                            if candidate.split(".", 1)[0] in {"subprocess", "importlib", "runpy", "sys", "site", "os",
                                                              "asyncio", "pty", "contextlib", "functools"}}
                if not resolved:
                    continue
                for target in targets:
                    if isinstance(target, ast.Name):
                        binding = aliases.setdefault(target.id, set())
                        previous = len(binding)
                        binding.update(resolved)
                        changed |= len(binding) != previous
                        if len(binding) > 100:
                            self.error(path, node.lineno + offset, "Python alias-resolution limit exceeded")
                            return
            if not changed:
                break
        else:
            self.error(path, 1, "Python alias-resolution depth limit exceeded")
            return

        def search_path(expression):
            return any(expression == root or expression.startswith(root + "[")
                       for root in ("sys.path", "sys.meta_path", "sys.path_hooks"))

        for node in nodes:
            try:
                if isinstance(node, ast.Import):
                    for item in node.names:
                        self.import_module(item.name, path, cwd, action, roots=roots)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if not node.level and module in PROCESS_MODULES and any(item.name == "*" for item in node.names):
                        raise DeliveryError("unsupported star import of a process/import API")
                    resolved = None
                    if module:
                        resolved = self.import_module(module, path, cwd, action, roots=roots, relative=node.level)
                    for item in node.names:
                        if item.name != "*":
                            if resolved:
                                # A from-import can name a package's attribute;
                                # add its submodule only when that file exists.
                                for location in resolved:
                                    stem = location + "/" + item.name
                                    for candidate in (stem + ".py", stem + "/__init__.py"):
                                        if candidate in self.items:
                                            self.add(candidate, "python", cwd, action, python_roots=roots)
                            elif not module:
                                # Only "from . import name" imports a module by that
                                # name; names from a non-local module are its own.
                                self.import_module(item.name, path, cwd, action, roots=roots, relative=node.level)
                elif (isinstance(node, (ast.Attribute, ast.Subscript))
                      and isinstance(node.ctx, (ast.Store, ast.Del))
                      and any(search_path(candidate) for candidate in names(ast.unparse(node)))):
                    raise DeliveryError("unsupported Python search-path mutation")
                elif (isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del))
                      and "os.environ" in names(ast.unparse(node.value)) and not literal_key(node.slice)):
                    raise DeliveryError("unsupported Python environment mutation affecting resolution")
                elif isinstance(node, ast.Call):
                    calls = names(ast.unparse(node.func))
                    mutators = {"append", "insert", "extend", "remove", "pop", "clear", "reverse", "sort",
                                "__setitem__", "__delitem__", "__iadd__", "__imul__"}
                    if any(candidate.rsplit(".", 1)[-1] in mutators and search_path(candidate.rsplit(".", 1)[0])
                           for candidate in calls) or "site.addsitedir" in calls:
                        raise DeliveryError("unsupported Python search-path mutation")
                    if calls & {"os.chdir", "os.fchdir", "contextlib.chdir"}:
                        raise DeliveryError("unsupported Python working-directory mutation")
                    environment = calls & {"os.putenv", "os.environ.setdefault", "os.environ.__setitem__",
                                           "os.environ.update"}
                    if environment:
                        if "os.environ.update" in environment:
                            source = node.args[0] if node.args else ast.Dict(keys=[], values=[])
                            keys = [*source.keys] if isinstance(source, ast.Dict) else [None]
                            keys += [ast.Constant(keyword.arg) if keyword.arg else None for keyword in node.keywords]
                        else:
                            keys = node.args[:1] or [None]
                        if not all(literal_key(key) for key in keys):
                            raise DeliveryError("unsupported Python environment mutation affecting resolution")
                    if "functools.partial" in calls and node.args and any(
                            executes(candidate) for candidate in names(ast.unparse(node.args[0]))):
                        raise DeliveryError("unsupported partial application of a process/import API")
                    for call in sorted(calls):
                        self.python_call(call, node, path, cwd, action, roots, offset)
            except (ValueError, RecursionError) as error:
                self.error(path, node.lineno + offset, "local-script discovery: " + clean(error))

    def python_call(self, call, node, path, cwd, action, roots, offset):
        if call.startswith(UNSUPPORTED_PREFIXES) or call in UNSUPPORTED_CALLS:
            raise DeliveryError("unsupported Python process/import API: " + clean(call))
        if call in {"importlib.import_module", "__import__"}:
            if not node.args or not isinstance(node.args[0], ast.Constant):
                raise DeliveryError("unresolved computed Python import")
            self.import_module(node.args[0].value, path, cwd, action, roots=roots)
        if call in COMMAND_APIS:
            target_cwd = cwd
            if call.startswith("subprocess."):
                if len(node.args) > 1 or any(keyword.arg is None for keyword in node.keywords):
                    raise DeliveryError("unresolved subprocess positional/options expansion")
                for keyword in node.keywords:
                    if keyword.arg not in {"cwd", "executable", "shell", "env"}:
                        continue
                    try:
                        option = ast.literal_eval(keyword.value)
                    except (ValueError, TypeError):
                        raise DeliveryError("unresolved computed subprocess " + keyword.arg) from None
                    if keyword.arg == "cwd" and option is not None:
                        if not isinstance(option, str):
                            raise DeliveryError("unresolved subprocess cwd")
                        try:
                            target_cwd = self.resolve(option, path=path, cwd=cwd, action=action, allow_root=True)
                        except DeliveryError as error:
                            raise DeliveryError("unsafe subprocess cwd: " + clean(error)) from None
                        for component in (PurePosixPath(target_cwd), *PurePosixPath(target_cwd).parents):
                            if str(component) in self.items:
                                raise DeliveryError("unsafe subprocess working directory: " + clean(option))
                        if target_cwd != "." and not any(
                                source.startswith(target_cwd + "/") for source in self.items):
                            raise DeliveryError("missing committed subprocess working directory: " + clean(option))
                    elif keyword.arg == "executable" and option is not None:
                        raise DeliveryError("unsupported alternate subprocess executable")
                    elif keyword.arg == "env" and option is not None:
                        if (not isinstance(option, dict) or any(not isinstance(key, str) or not isinstance(value, str)
                                                              for key, value in option.items())
                                or any(key.upper() in {"PYTHONPATH", "PYTHONHOME", "PYTHONSAFEPATH", "PATH"} for key in option)):
                            raise DeliveryError("unsupported subprocess environment affecting resolution")
                    elif keyword.arg == "shell" and option not in (None, False, True):
                        raise DeliveryError("unresolved subprocess shell option")
            if not node.args:
                raise DeliveryError("unresolved Python script invocation")
            try:
                value = ast.literal_eval(node.args[0])
            except (ValueError, TypeError):
                raise DeliveryError("unresolved computed Python script invocation") from None
            if call == "runpy.run_module":
                self.import_module(value, path, cwd, action, roots=roots, required=True, execute=True)
            elif call == "runpy.run_path":
                self.add(self.resolve(value, path=path, cwd=cwd, action=action), "python", cwd, action, python_roots=roots)
            elif isinstance(value, str):
                self.commands(path, value, target_cwd, action, offset=node.lineno - 1 + offset)
            elif isinstance(value, (list, tuple)) and all(isinstance(v, str) for v in value):
                self.commands(path, shlex.join(value), target_cwd, action, offset=node.lineno - 1 + offset)
            else:
                raise DeliveryError("unresolved Python subprocess target")

    def discover(self):
        for root in (".github", ".github/actions"):
            # ls-tree -r returns this exact name only for a blob or gitlink,
            # never a directory. A substituted scope root is not empty scope.
            if root in self.items:
                self.error(root, 1, "unsafe action directory (blob/symlink/gitlink)")
        for path in sorted(self.items):
            if path.startswith(".github/actions/"):
                try:
                    safe_path(path)
                    if self.items[path][:2] not in (("100644", "blob"), ("100755", "blob")):
                        raise DeliveryError("unsafe action source (symlink/gitlink)")
                    fmt = FORMATS.get(PurePosixPath(path).suffix.lower())
                    if fmt:
                        self.add(path, fmt, action=str(PurePosixPath(path).parent))
                    else:
                        header = self.git.blob(self.revision, path).split(b"\n", 1)[0]
                        if header.startswith(b"#!"):
                            self.add(path, action=str(PurePosixPath(path).parent))
                except (ValueError, UnicodeError) as error:
                    self.error(path, 1, str(error))
        while self.queue:
            path, cwd, action, python_roots, sourced = self.queue.popleft()
            try:
                item = self.files[path]
                if PurePosixPath(path).name in {"action.yml", "action.yaml"}:
                    self.action(path, item["text"])
                elif item["format"] == "python":
                    self.python(path, item["text"], cwd, action, roots=python_roots)
                elif item["format"] in {"bash", "powershell"}:
                    self.commands(path, item["text"], cwd, action, powershell=item["format"] == "powershell", sourced=sourced)
            except (ValueError, UnicodeError, RecursionError) as error:
                self.error(path, 1, "discovery failed: " + clean(error))
        return self.files, sorted(set(self.errors))
