#!/usr/bin/env python3
"""Reproduce story 19 package-mode checks using disposable exact-gitlink sources.

Run from any directory:
  run-with-temp python3 PATH/verify-product.py --phase build
No fetch, nested submodule initialization, credentials, or sibling edits occur.
Logs and the sanitized result remain alongside this script after TMPDIR cleanup.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import tarfile
import time
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--phase", choices=["build", "architecture", "units", "units-release", "tests", "integration", "release", "evaluate", "packages", "all"], default="all")
parser.add_argument("--timeout", type=int, default=900)
parser.add_argument("--live", action="store_true", help="Require live Docker/Dapr/browser prerequisites before stage 4")
args = parser.parse_args()
evidence = Path(__file__).resolve().parent
repo = evidence.parents[4]
product = repo / "references/Hexalith.ChatBot"
objects = repo.parent / "cicd/references"
scratch = Path(os.environ["TMPDIR"]) / "story19"
scratch.mkdir()
root = scratch / "references"
root.mkdir()
chatbot = scratch / "ChatBot"
log_path = evidence / f"product-{args.phase}-verification.log"
result_path = evidence / f"product-{args.phase}-verification.json"
result_path.unlink(missing_ok=True)
results = {"phase": args.phase, "product_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=product, text=True).strip(), "snapshots": {}, "commands": []}
results["product_diff_sha256"] = hashlib.sha256(subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=product)).hexdigest()
results["product_untracked_sha256"] = {name: hashlib.sha256((product / name).read_bytes()).hexdigest() for name in subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=product).decode().split("\0") if name}
results["live_required"] = args.live
log = log_path.open("w", buffering=1)
env = dict(os.environ, CI="true", DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1")
owned_process_groups = set()


def current_input_hashes():
    return {"product_diff_sha256": hashlib.sha256(subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=product)).hexdigest(),
        "product_untracked_sha256": {name: hashlib.sha256((product / name).read_bytes()).hexdigest() for name in subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=product).decode().split("\0") if name}}


def verify_built_source():
    checked = 0
    for entry in subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=product).decode().split("\0"):
        if not entry:
            continue
        metadata, name = entry.split("\t", 1)
        mode = metadata.split()[0]
        if mode == "160000":
            continue  # Exact foreign archives are independently bound by snapshots.
        original, copied = product / name, chatbot / name
        if not original.exists():
            assert not copied.exists(), name
        elif mode == "120000":
            assert original.readlink() == copied.readlink(), name
        else:
            assert original.read_bytes() == copied.read_bytes(), name
            checked += 1
    for name, expected in results["product_untracked_sha256"].items():
        assert hashlib.sha256((chatbot / name).read_bytes()).hexdigest() == expected, name
        checked += 1
    return {"regular_files_checked": checked, "matches_original_product_inputs": True}


def capture_json_loader_metadata():
    data = {"scope": "Actual normal child output metadata; this capture does not claim child-runtime execution",
        "installed_runtimes": subprocess.check_output(["dotnet", "--list-runtimes"], text=True).splitlines(),
        "projects": {}}
    for name, directory in [
        ("required_test_host", chatbot / "tests/Hexalith.ChatBot.Live.IntegrationTests"),
        ("release_test_host", chatbot / "tests/Hexalith.ChatBot.Release.Tests"),
        ("normal_tenants_child", root / "Hexalith.Tenants/src/Hexalith.Tenants"),
    ]:
        output = directory / "bin/Release/net10.0"
        deps_path = output / (directory.name + ".deps.json")
        runtime_path = output / (directory.name + ".runtimeconfig.json")
        assets = json.loads((directory / "obj/project.assets.json").read_text())
        deps = json.loads(deps_path.read_text())
        local_json = output / "System.Text.Json.dll"
        entry = {"deps_path": str(deps_path), "deps_sha256": hashlib.sha256(deps_path.read_bytes()).hexdigest(),
            "deps_runtime_target": deps["runtimeTarget"],
            "deps_json_entries": {target: {key: value for key, value in libraries.items() if key.startswith("System.Text.Json/")}
                for target, libraries in deps["targets"].items()},
            "runtimeconfig_path": str(runtime_path), "runtimeconfig": json.loads(runtime_path.read_text()),
            "assets_json_libraries": {key: value for key, value in assets["libraries"].items() if key.startswith("System.Text.Json/")},
            "app_local_json_present": local_json.is_file()}
        if local_json.is_file():
            identity = subprocess.check_output(["pwsh", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command",
                "[System.Reflection.AssemblyName]::GetAssemblyName($env:CHATBOT_METADATA_ASSEMBLY_PATH).FullName"],
                env=dict(env, CHATBOT_METADATA_ASSEMBLY_PATH=str(local_json)), text=True, timeout=30).strip()
            entry["app_local_json"] = {"path": str(local_json), "assembly_identity": identity,
                "sha256": hashlib.sha256(local_json.read_bytes()).hexdigest()}
        data["projects"][name] = entry
    return data


def capture_runtime_metadata():
    """Retain observed storage/SDK identity and modes without reading custody contents."""
    prefix = Path(os.environ["TMPDIR"]).resolve()
    identities = subprocess.check_output(["docker", "ps", "--all", "--filter",
        f"label=io.hexalith.chatbot-live.scope={prefix}", "--format", "{{.ID}}"], text=True, timeout=5).split()
    observed = results.setdefault("owned_backend_observations", {})
    for identity in identities:
        try:
            data = json.loads(subprocess.check_output(["docker", "inspect", "--format",
                '{"id":{{json .Id}},"labels":{{json .Config.Labels}},"mounts":{{json .Mounts}},"tmpfs":{{json .HostConfig.Tmpfs}}}',
                identity], text=True, stderr=subprocess.DEVNULL, timeout=5))
        except subprocess.CalledProcessError:
            continue  # Normal fixture disposal can win this observation race.
        labels = data["labels"]
        custody = Path(labels["io.hexalith.chatbot-live.custody"]).resolve()
        if not custody.is_relative_to(prefix):
            raise RuntimeError("Observed fixture custody is outside the private job directory")
        entry = {"container_id": data["id"], "run_id": labels["io.hexalith.chatbot-live.run"],
            "storage_mounts": [{key: mount.get(key) for key in ("Type", "Destination")} for mount in data["mounts"]],
            "tmpfs": data["tmpfs"]}
        if custody.is_dir():
            try:
                entry["private_modes"] = {str(path.relative_to(custody)): oct(path.stat().st_mode & 0o777)
                    for path in [custody, *custody.rglob("*")] if path.is_dir() or path.is_file()}
            except FileNotFoundError:
                pass
        observed[data["id"]] = entry
    receipts = results.setdefault("compiled_owner_observations", {})
    for receipt in prefix.glob("hexalith-selected-owner-*/preparation.json"):
        try:
            data = json.loads(receipt.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            continue
        selected = {key: data[key] for key in ("project", "projectPath", "configuration", "targetFramework", "sdk",
            "targetPath", "metadataPath", "targetSha256", "moduleVersionId", "declarations", "operations", "dependencies", "loadedSdk")}
        if "ownerArtifacts" in data:
            selected["ownerArtifacts"] = data["ownerArtifacts"]
        receipts[data["project"] + ":" + data["targetSha256"]] = selected
    comparisons = results.setdefault("selected_owner_sdk_comparisons", {})
    for selected in prefix.glob("hexalith-selected-owner-*/metadata/Hexalith.EventStore.*.dll"):
        loaded = chatbot / "tests/Hexalith.ChatBot.IntegrationTests/bin/Release/net10.0" / selected.name
        if loaded.is_file():
            child_hash = hashlib.sha256(selected.read_bytes()).hexdigest()
            loaded_hash = hashlib.sha256(loaded.read_bytes()).hexdigest()
            comparisons[str(selected.relative_to(prefix))] = {"assembly": selected.name,
                "selected_owner_sha256": child_hash, "actual_apphost_sdk_sha256": loaded_hash,
                "identical": child_hash == loaded_hash}


def run(command, cwd, timeout=args.timeout):
    log.write("\n$ " + shlex.join(map(str, command)) + "\n")
    output_start = log.tell()
    start = time.monotonic()
    child = subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    owned_process_groups.add(child.pid)
    try:
        if args.live and command[:2] == ["dotnet", "test"]:
            while True:
                remaining = timeout - (time.monotonic() - start)
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(command, timeout)
                try:
                    code = child.wait(timeout=min(2, remaining))
                    break
                except subprocess.TimeoutExpired:
                    capture_runtime_metadata()
        else:
            code = child.wait(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as interruption:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
        code = 124 if isinstance(interruption, subprocess.TimeoutExpired) else 130
    except Exception:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        raise
    if args.live and command[:2] == ["dotnet", "test"]:
        capture_runtime_metadata()
    reason = None
    if code == 0 and command[:2] == ["dotnet", "test"]:
        log.flush()
        with log_path.open() as reader:
            reader.seek(output_start)
            output = reader.read()
        if "Test run summary: Passed!" not in output or not re.search(r"total:\s*[1-9]", output):
            code, reason = 125, "The test runner returned zero without a completed passing summary"
        else:
            skipped = [line.removeprefix("skipped ") for line in output.splitlines() if line.startswith("skipped ")]
            ordinary_project = any(str(value).endswith("/Hexalith.ChatBot.IntegrationTests.csproj") for value in command)
            manual = "Hexalith.ChatBot.IntegrationTests.PolicyIsolation.PolicyRefusalPreflightTests.MissingProofMustRefuseBothRealPrincipalsWithoutNativeMutation"
            skipped_summary = re.search(r"^\s*skipped:\s*(\d+)\s*$", output, re.MULTILINE)
            if skipped_summary is None:
                code, reason = 126, "Completed test summary lacks its skipped count"
            elif int(skipped_summary.group(1)) or skipped:
                if ordinary_project and skipped == [manual] and int(skipped_summary.group(1)) == 1:
                    results["unexecuted_legacy_manual_observer_producer"] = manual
                else:
                    code, reason = 126, "Unexpected skipped tests or skips in a required live project"
    entry = {"command": list(map(str, command)), "exit": code, "seconds": round(time.monotonic() - start, 2)}
    if reason:
        entry["reason"] = reason
    results["commands"].append(entry)
    log.write(f"exit={code}; seconds={entry['seconds']}\n")
    print(f"exit={code}; seconds={entry['seconds']}: {shlex.join(map(str, command[:4]))}", flush=True)
    return code


def snapshot(source, revision, target):
    target.mkdir()
    archive = subprocess.Popen(["git", "archive", revision], cwd=source, stdout=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=archive.stdout, mode="r|*") as stream:
            stream.extractall(target, filter="data")
    finally:
        archive.stdout.close()
        if archive.wait() != 0:
            raise RuntimeError(f"git archive failed: {source} {revision}")


def cleanup_owned_runtime():
    """Wait for scoped child work and verify only this job's fresh backends are gone."""
    prefix = str(Path(os.environ["TMPDIR"]).resolve())

    def scoped_processes():
        selected = []
        for process in Path("/proc").iterdir():
            if not process.name.isdigit() or int(process.name) in {os.getpid(), os.getppid()}:
                continue
            try:
                command = (process / "cmdline").read_bytes().replace(b"\0", b" ")
                status = (process / "stat").read_text().rsplit(")", 1)[1].split()
                process_group = int(status[2])
            except (OSError, PermissionError):
                continue
            if status[0] == "Z":
                continue  # Exited child work has finished; its parent owns reaping.
            executable = Path(command.decode(errors="replace").split(" ", 1)[0]).name
            runtime_command = executable not in {"bash", "sh", "python", "python3"}
            if process_group in owned_process_groups or runtime_command and (prefix + "/").encode() in command:
                selected.append(int(process.name))
        return selected

    deadline = time.monotonic() + 15
    while scoped_processes() and time.monotonic() < deadline:
        time.sleep(0.1)
    for number in scoped_processes():
        try:
            os.kill(number, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 10
    while scoped_processes() and time.monotonic() < deadline:
        time.sleep(0.1)
    for number in scoped_processes():
        try:
            os.kill(number, signal.SIGKILL)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 5
    while scoped_processes() and time.monotonic() < deadline:
        time.sleep(0.1)
    if scoped_processes():
        raise RuntimeError("Scoped runtime children did not exit before workspace cleanup")
    if args.phase not in {"all", "integration", "release", "units-release", "tests"}:
        return {"remaining_scoped_processes": [], "owned_backends_removed": []}
    query = ["docker", "ps", "--all", "--filter", f"label=io.hexalith.chatbot-live.scope={prefix}", "--format", "{{.ID}}"]
    containers = subprocess.check_output(query, text=True, timeout=30).split()
    removed, removal_failures = [], []
    for identity in containers:
        inspected = json.loads(subprocess.check_output(["docker", "inspect", "--format", "{{json .Config.Labels}}", identity], text=True, timeout=30))
        if inspected.get("io.hexalith.chatbot-live.scope") != prefix or not inspected.get("io.hexalith.chatbot-live.run"):
            raise RuntimeError("Refusing ambiguous backend cleanup")
        try:
            subprocess.run(["docker", "rm", "--force", "--volumes", identity], check=True, capture_output=True, text=True, timeout=30)
        except Exception:
            # Keep authentic custody private if its backend cannot be removed.
            custody = Path(inspected["io.hexalith.chatbot-live.custody"]).resolve()
            if custody.is_dir() and custody.is_relative_to(Path(prefix)):
                retained = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "hexalith/chatbot-live-retained" / inspected["io.hexalith.chatbot-live.run"]
                retained.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                shutil.copytree(custody, retained, dirs_exist_ok=True)
                retained.chmod(0o700)
                results.setdefault("private_custody_retained_at", []).append(str(retained))
            removal_failures.append(identity)
            continue
        removed.append(identity)
    if removal_failures or subprocess.check_output(query, text=True, timeout=30).strip():
        raise RuntimeError("Owned fresh backends remain before workspace cleanup")
    return {"remaining_scoped_processes": [], "owned_backends_removed": removed}


try:
    if run(["git", "clone", "--shared", str(product), str(chatbot)], repo, timeout=30):
        raise RuntimeError("Product clone failed")
    patch = subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=product)
    if patch:
        subprocess.run(["git", "apply", "--binary"], cwd=chatbot, input=patch, check=True)
    for name in subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=product).decode().split("\0"):
        if name:
            destination = chatbot / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(product / name, destination)
    for entry in subprocess.check_output(["git", "ls-tree", "HEAD:references"], cwd=product, text=True).splitlines():
        mode, kind, revision, name = entry.split()
        if mode != "160000":
            continue
        if args.phase == "packages" and name != "Hexalith.Builds":
            continue
        if args.phase == "evaluate" and name not in {"Hexalith.Builds", "Hexalith.Platform"}:
            continue
        results["snapshots"][name] = revision
        snapshot(objects / name, revision, root / name)
    # One canonical source path per project prevents duplicate MSBuild instances
    # from restoring incompatible assets into the same obj directory.
    for owner in [chatbot, *root.iterdir()]:
        references = owner / "references"
        references.mkdir(exist_ok=True)
        # Foreign source compilation uses canonical global root mappings. Only
        # its catalog import needs a nested alias. Linking every sibling to every
        # other sibling creates cycles in genuine recursive product scans.
        names = results["snapshots"] if owner == chatbot else (["Hexalith.Builds"] if owner.name != "Hexalith.Builds" else [])
        for name in names:
            path = references / name
            if path.is_dir() and not path.is_symlink():
                path.rmdir()  # gitlink placeholders must contain no real checkout.
            if not path.exists():
                path.symlink_to(root / name, target_is_directory=True)
    properties = ["-p:UseHexalithProjectReferences=false"]
    for name in results["snapshots"]:
        if name not in {"Hexalith.AI.Tools", "Hexalith.PolymorphicSerializations"}:
            properties.append(f"-p:{name.replace('.', '')}Root={root / name}")
    common = ["--configuration", "Release", "-warnaserror", "-m:1", "/nr:false", "-noAutoResponse", *properties]
    if args.phase == "architecture":
        project = "tests/Hexalith.ChatBot.Architecture.Tests/Hexalith.ChatBot.Architecture.Tests.csproj"
        if run(["dotnet", "build", project, *common], chatbot):
            raise RuntimeError("Architecture-only package-mode build failed")
        results["built_source_verification"] = verify_built_source()
        if run(["dotnet", "test", "--project", project, "--configuration", "Release", "--no-build", "--no-restore", *properties], chatbot):
            raise RuntimeError("Whole Architecture project failed")
        results["built_source_after_tests"] = verify_built_source()
        assert not (chatbot / "src/Hexalith.ChatBot.AppHost/bin").exists(), "Architecture qualification unexpectedly built AppHost"
        results["apphost_graph_built"] = False
    if args.phase == "evaluate":
        def capture(command, environment=None):
            log.write("\n$ " + shlex.join(command) + "\n")
            completed = subprocess.run(command, cwd=chatbot, env=environment or env, capture_output=True, text=True, timeout=60)
            log.write(completed.stdout + completed.stderr)
            if completed.returncode:
                raise RuntimeError(f"Evaluation failed: {completed.returncode}")
            return completed.stdout

        version = json.loads((chatbot / ".config/dotnet-tools.json").read_text())["tools"]["hexalith.builds.module.cli"]["version"]
        package_relative = Path("hexalith.builds.module.cli") / version / "tools/net10.0/any"
        default_cache = Path.home() / ".nuget/packages"
        caches = {name: scratch / name for name in ["env-cache", "restore-cache", "explicit-cache"]}
        for cache in caches.values():
            target = cache / package_relative
            target.mkdir(parents=True)
            shutil.copy2(default_cache / package_relative / "Hexalith.Builds.Tooling.dll", target)
        cases = [
            ("default", default_cache, {}, []),
            ("environment cache", caches["env-cache"], {"NUGET_PACKAGES": str(caches["env-cache"])}, []),
            ("restore overrides environment", caches["restore-cache"], {"NUGET_PACKAGES": str(caches["env-cache"])}, [f'-p:RestorePackagesPath={caches["restore-cache"]}']),
            ("explicit NuGet root", caches["explicit-cache"], {"NUGET_PACKAGES": str(caches["env-cache"])}, [f'-p:RestorePackagesPath={caches["restore-cache"]}', f'-p:NuGetPackageRoot={caches["explicit-cache"]}']),
        ]
        results["cold_cache_checks"] = []
        for name, expected_cache, additions, flags in cases:
            environment = dict(env, **additions)
            if not additions:
                environment.pop("NUGET_PACKAGES", None)
            published = capture(["dotnet", "msbuild", "src/Hexalith.ChatBot.AppHost/Hexalith.ChatBot.AppHost.csproj", "-noAutoResponse", "-p:Configuration=Release", *properties, *flags, "-getProperty:_ChatBotPublishedToolRoot"], environment).strip()
            assert Path(published) == expected_cache / package_relative, (name, published)
            assert (Path(published) / "Hexalith.Builds.Tooling.dll").is_file()
            platform = json.loads(capture(["dotnet", "msbuild", str(root / "Hexalith.Platform/src/Hexalith.Platform.Composition/Hexalith.Platform.Composition.csproj"), "-noAutoResponse", "-p:Configuration=Release", *properties, f"-p:HexalithBuildsPublishedToolRoot={published}", "-getProperty:BuildsToolingAssemblyPath", "-getItem:ProjectReference"]))
            assert platform["Properties"]["BuildsToolingAssemblyPath"] == str(Path(published) / "Hexalith.Builds.Tooling.dll")
            assert not any(item["Identity"].endswith("Hexalith.Builds.Tooling.csproj") for item in platform["Items"]["ProjectReference"])
            results["cold_cache_checks"].append({"case": name, "published_root": published, "assembly_exists": True, "platform_source_tooling_reference": False})
        assert not list(chatbot.glob("**/obj")), "Cold evaluation unexpectedly generated obj"
        solution_targets = chatbot / "Directory.Solution.targets"
        solution_targets.write_text(solution_targets.read_text().replace("</Project>", '''  <Target Name="ProbeChatBotMode" DependsOnTargets="BindChatBotRestoreCompositionInputs">
    <Message Importance="high" Text="PROBE_MODE=$(UseHexalithProjectReferences)" />
    <Message Importance="high" Text="PROBE_RESTORE=$(_GenerateRestoreGraphProjectEntryInputProperties)" />
  </Target>
</Project>'''))
        results["mode_checks"] = []
        for name, configuration, ci, explicit, expected in [("local Debug default", "Debug", "false", None, "true"), ("local Release default", "Release", "false", None, "false"), ("CI Debug default", "Debug", "true", None, "false"), ("explicit Debug packages", "Debug", "false", "false", "false")]:
            flags = [f"-p:Configuration={configuration}", f"-p:CI={ci}"]
            if explicit:
                flags.append(f"-p:UseHexalithProjectReferences={explicit}")
            project_mode = capture(["dotnet", "msbuild", "src/Hexalith.ChatBot.AppHost/Hexalith.ChatBot.AppHost.csproj", "-noAutoResponse", *flags, "-getProperty:UseHexalithProjectReferences"]).strip()
            solution = capture(["dotnet", "msbuild", "Hexalith.ChatBot.slnx", "-noAutoResponse", *flags, "-target:ProbeChatBotMode"])
            assert project_mode == expected and f"PROBE_MODE={expected}" in solution, (name, project_mode, solution)
            binding = "HexalithBuildsPublishedToolRoot=" in solution
            assert binding == (expected == "false"), (name, solution)
            results["mode_checks"].append({"case": name, "project_mode": project_mode, "solution_mode": expected, "restore_forwards_published_tool": binding})
    if args.phase in {"build", "units", "units-release", "all", "tests", "integration", "release"}:
        if run(["dotnet", "build", "Hexalith.ChatBot.slnx", *common], chatbot):
            raise RuntimeError("Package-mode solution build failed")
        assets = json.loads((chatbot / "src/Hexalith.ChatBot.AppHost/obj/project.assets.json").read_text())
        sdk_closure = {}
        for name in ["Hexalith.EventStore.Aspire", "Hexalith.EventStore.Contracts", "Hexalith.EventStore.Client", "Hexalith.EventStore.ServiceDefaults"]:
            library_name = next(key for key in assets["libraries"] if key.startswith(name + "/"))
            library = assets["libraries"][library_name]
            assert library["type"] == "package", (library_name, library)
            package_file = next(Path(folder) / library["path"] / "lib/net10.0" / (name + ".dll") for folder in assets["packageFolders"]
                if (Path(folder) / library["path"] / "lib/net10.0" / (name + ".dll")).is_file())
            selected = chatbot / "src/Hexalith.ChatBot.AppHost/bin/Release/net10.0" / (name + ".dll")
            assert selected.read_bytes() == package_file.read_bytes(), name
            sdk_closure[library_name] = {"actual_apphost_sha256": hashlib.sha256(selected.read_bytes()).hexdigest(), "matches_published_package": True}
        assert not any(key.startswith("Hexalith.Builds.Tooling/") and value["type"] == "project" for key, value in assets["libraries"].items())
        results["composition_sdk_package_closure"] = sdk_closure
        configuration = (chatbot / "tests/required-live.xunit.runner.json").read_bytes()
        results["required_runner_configuration_sha256"] = hashlib.sha256(configuration).hexdigest()
        for project in ["Hexalith.ChatBot.Live.IntegrationTests", "Hexalith.ChatBot.Release.Tests", "Hexalith.ChatBot.Recovery.Tests"]:
            assert (chatbot / "tests" / project / "bin/Release/net10.0/xunit.runner.json").read_bytes() == configuration, project
        results["built_source_verification"] = verify_built_source()
        results["json_loader_metadata_before_tests"] = capture_json_loader_metadata()
    if args.phase == "packages":
        feed = scratch / "feed"
        feed.mkdir()
        version = f"0.0.0-story19.c{results['product_diff_sha256'][:12]}"
        inventory = json.loads((chatbot / "release-metadata.json").read_text())["inventory"]["packages"]
        for package in inventory:
            if run(["dotnet", "pack", package["project"], "--output", str(feed), f"-p:Version={version}", f"-p:PackageVersion={version}", *common], chatbot):
                raise RuntimeError(f"Pack failed: {package['id']}")
        consumer = scratch / "consumer"
        consumer.mkdir()
        shutil.copy2(chatbot / "global.json", consumer / "global.json")
        references = "".join(f'<PackageReference Include="{package["id"]}" Version="{version}" />' for package in inventory)
        (consumer / "Consumer.csproj").write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><TreatWarningsAsErrors>true</TreatWarningsAsErrors><NuGetAudit>true</NuGetAudit><NuGetAuditMode>all</NuGetAuditMode></PropertyGroup><ItemGroup>' + references + '</ItemGroup></Project>\n')
        (consumer / "NuGet.Config").write_text(f'<configuration><packageSources><clear/><add key="local" value="{feed}"/><add key="nuget.org" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>\n')
        (consumer / "Program.cs").write_text('''using Hexalith.ChatBot.Client;
using Hexalith.ChatBot.Contracts;
using Hexalith.ChatBot.Contracts.Identities;
using Hexalith.ChatBot.Testing;

ChatBotCommandId command = ChatBotCommandId.New();
if (!ChatBotCommandId.TryParse(command.Value, out ChatBotCommandId parsed) || parsed != command)
    throw new InvalidOperationException("The packaged contract identity did not round-trip.");
if (ChatBotTestConstants.ModuleName != ChatBotModuleInfo.ModuleName || ChatBotTestConstants.DaprAppId != ChatBotModuleInfo.DaprAppId)
    throw new InvalidOperationException("The packaged testing facade disagrees with Contracts.");
using HttpClient http = new();
IChatBotClient client = new ChatBotClient(new Hexalith.ChatBot.Client.Generated.Client(http));
if (client is null) throw new InvalidOperationException("The packaged client did not initialize.");
Console.WriteLine("Contracts, Client and Testing packages loaded; contract identity and testing facade passed.");
''')
        if run(["dotnet", "run", "--project", "Consumer.csproj", "--configuration", "Release"], consumer):
            raise RuntimeError("Isolated NuGet consumer failed")
    if args.phase in {"units", "units-release", "tests", "all", "integration", "release"}:
        suite_failures = []
        ordinary_discovery_start = log.tell()
        if run(["dotnet", str(chatbot / "tests/Hexalith.ChatBot.IntegrationTests/bin/Release/net10.0/Hexalith.ChatBot.IntegrationTests.dll"), "-list", "tests"], chatbot):
            raise RuntimeError("Ordinary integration discovery failed")
        log.flush()
        with log_path.open() as reader:
            reader.seek(ordinary_discovery_start)
            ordinary_inventory = [line for line in reader.read().splitlines() if line.startswith("Hexalith.ChatBot.")]
        required_ordinary = [
            "Hexalith.ChatBot.IntegrationTests.PolicyIsolation.PolicyRefusalPreflightTests.MissingProofMustRefuseBothRealPrincipalsWithoutNativeMutation",
        ]
        assert all(name in ordinary_inventory for name in required_ordinary)
        assert not any("RunCommittedGovernedStateM2GateAsync" in name or "RunGovernedNoteOriginParityAsync" in name
            or "CommittedGovernedStateShouldPassM2StopShipSweeps" in name
            or "GovernedNoteShouldProjectIdenticalDurableEndState" in name for name in ordinary_inventory)
        results["ordinary_integration_discovery"] = ordinary_inventory
        live_discovery_start = log.tell()
        if run(["dotnet", str(chatbot / "tests/Hexalith.ChatBot.Live.IntegrationTests/bin/Release/net10.0/Hexalith.ChatBot.Live.IntegrationTests.dll"), "-list", "tests"], chatbot):
            raise RuntimeError("Required live discovery failed")
        log.flush()
        with log_path.open() as reader:
            reader.seek(live_discovery_start)
            live_inventory = [line for line in reader.read().splitlines() if line.startswith("Hexalith.ChatBot.")]
        expected_live = sorted("Hexalith.ChatBot.Live.IntegrationTests.RequiredTopologyTests." + method for method in [
            "GovernedCommandsShouldFailClosedWithoutAtomicParticipationInRealDaprTopology",
            "CorrectionPropagationWorkflowRuntimeShouldBeHealthyInRealDaprTopology",
            "AuthenticatedProductionClientShouldFailClosedWithoutPersistingAcrossRequiredChromeMatrix",
        ])
        assert sorted(live_inventory) == expected_live
        assert not any(name.rsplit(".", 1)[-1] in {test.rsplit(".", 1)[-1] for test in expected_live} for name in ordinary_inventory)
        results["required_live_discovery"] = live_inventory
        projects = sorted(chatbot / node.attrib["Path"] for node in ET.parse(chatbot / "Hexalith.ChatBot.slnx").iter("Project") if node.attrib["Path"].startswith("tests/"))
        unit, integration = [], []
        for project in projects:
            if project.parent.name in {"Hexalith.ChatBot.RecoverySandbox", "Hexalith.ChatBot.Recovery.Tests", "Hexalith.ChatBot.Release.Tests"}:
                continue
            target = integration if project.stem.endswith(("IntegrationTests", "AppHost.Tests")) or "E2E" in project.stem else unit
            target.append(project)
        for project in unit if args.phase in {"units", "units-release", "tests", "all"} else []:
            if run(["dotnet", "test", "--project", str(project), "--no-build", "--configuration", "Release", *properties], chatbot):
                suite_failures.append(project.parent.name)
        if args.live:
            environment_file = scratch / "github-env"
            env["GITHUB_ENV"] = str(environment_file)
            if run(["python3", ".github/actions/after-unit-tests/require-runtime.py"], chatbot):
                raise RuntimeError("Live product prerequisites failed")
            for line in environment_file.read_text().splitlines():
                key, value = line.split("=", 1)
                env[key] = value
        for project in integration if args.phase not in {"units", "units-release", "release"} else []:
            if run(["dotnet", "test", "--project", str(project), "--no-build", "--configuration", "Release", *properties], chatbot):
                suite_failures.append(project.parent.name)
        discovery_start = log.tell()
        if run(["dotnet", str(chatbot / "tests/Hexalith.ChatBot.Recovery.Tests/bin/Release/net10.0/Hexalith.ChatBot.Recovery.Tests.dll"), "-list", "tests"], chatbot):
            raise RuntimeError("Recovery discovery failed")
        log.flush()
        with log_path.open() as reader:
            reader.seek(discovery_start)
            discovered = reader.read()
        expected_recovery_test = "Hexalith.ChatBot.Recovery.Tests.LiveContinuityAspireE2eTests.LiveRecoveryValidationRunsAllThreeCoordinatorsAndPassesEvidenceGate"
        if expected_recovery_test not in discovered.splitlines():
            raise RuntimeError("Recovery discovery did not list the complete destructive sweep")
        results["recovery_test_discovered"] = expected_recovery_test
        release_discovery_start = log.tell()
        if run(["dotnet", str(chatbot / "tests/Hexalith.ChatBot.Release.Tests/bin/Release/net10.0/Hexalith.ChatBot.Release.Tests.dll"), "-list", "tests"], chatbot):
            raise RuntimeError("Release discovery failed")
        log.flush()
        with log_path.open() as reader:
            reader.seek(release_discovery_start)
            released = [line for line in reader.read().splitlines() if line.startswith("Hexalith.ChatBot.")]
        expected_release = sorted([
            "Hexalith.ChatBot.Release.Tests.GovernedStateReleaseGateTests.CommittedGovernedStateShouldPassM2StopShipSweepsInRealDaprTopology",
            "Hexalith.ChatBot.Release.Tests.GovernedStateReleaseGateTests.GovernedNoteShouldProjectIdenticalDurableEndStateRegardlessOfDeclaredOrigin",
        ])
        if sorted(released) != expected_release:
            raise RuntimeError(f"Release discovery changed the preserved positive inventory: {released}")
        results["release_tests_discovered"] = expected_release
        if args.phase in {"release", "units-release"}:
            if run(["dotnet", "test", "--project", "tests/Hexalith.ChatBot.Release.Tests/Hexalith.ChatBot.Release.Tests.csproj", "--no-build", "--configuration", "Release", *properties], chatbot):
                suite_failures.append("Hexalith.ChatBot.Release.Tests")
        if suite_failures:
            results["failed_suites"] = suite_failures
            raise RuntimeError("Product suites failed: " + ", ".join(suite_failures))
    results["passed"] = True
except Exception as error:
    results["passed"] = False
    results["error"] = str(error)
    print(str(error), flush=True)
finally:
    results["product_inputs_after"] = current_input_hashes()
    if results["product_inputs_after"] != {key: results[key] for key in ("product_diff_sha256", "product_untracked_sha256")}:
        results["passed"] = False
        results["input_mutation_error"] = "Original product inputs changed during verification"
    if args.phase == "units-release" and (chatbot / "src/Hexalith.ChatBot.AppHost/bin/Release/net10.0").is_dir():
        try:
            results["json_loader_metadata_after_tests"] = capture_json_loader_metadata()
            results["built_source_after_tests"] = verify_built_source()
        except Exception as metadata_error:
            results["passed"] = False
            results["final_metadata_error"] = str(metadata_error)
    try:
        results["runtime_cleanup"] = cleanup_owned_runtime()
    except Exception as cleanup_error:
        results["passed"] = False
        results["runtime_cleanup_error"] = str(cleanup_error)
    result_path.write_text(json.dumps(results, indent=2) + "\n")
    log.close()
raise SystemExit(0 if results["passed"] else 1)
