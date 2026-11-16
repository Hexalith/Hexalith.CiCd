"""Run the real package fixture after building its full integration dependency graph.

This is a focused diagnostic, not a complete publication qualification.
"""
from pathlib import Path
import ast
import hashlib
import json
import sys

root = Path(__file__).resolve().parents[3]
driver = root / "_bmad-output/specs/spec-cicd/evidence/18/local-package-build.py"
source = driver.read_text()
parsed = ast.parse(source)
targets = [node for node in parsed.body if isinstance(node, ast.Assign)
           and any(isinstance(target, ast.Name) and target.id == "target" for target in node.targets)]
assert len(targets) == 1
target = targets[0]
lines = source.splitlines(keepends=True)
lines[target.lineno - 1:target.end_lineno] = ["target = 'tests/Hexalith.Projects.Integration.Tests/Hexalith.Projects.Integration.Tests.csproj'\n"]
source = "".join(lines)
needle = "    digest = hashlib.sha256()\n"
assert source.count(needle) == 1
if "--frozen-fix-inputs" in sys.argv:
    heads = {name.removeprefix("Hexalith."): revision for name, revision in
             json.loads((Path(__file__).parent / "result.json").read_text())["tested_source_revisions"].items()}
    trees = {"Projects": "7f45e5a3fde607e64a3648ed77f96f6367bdd490", "Folders": "8bad72c4296f96a6fa6c0da7572ec5dcefd8c720"}
    fixes = [
        "tests/Hexalith.Projects.PackageFixtures.AppHost/PackageOwnerLoadContext.cs",
        "tests/Hexalith.Projects.PackageFixtures.AppHost/PackageActualOwnerInfrastructure.cs",
        "tests/Hexalith.Projects.PackageFixtures.AppHost/Hexalith.Projects.PackageFixtures.AppHost.csproj",
        "tests/Hexalith.Projects.Integration.Tests/PackageOwnerLoadContextTests.cs",
        "tests/Hexalith.Projects.Integration.Tests/PackageOwnerMetadataTests.cs",
        "tests/Hexalith.Projects.Integration.Tests/Hexalith.Projects.Integration.Tests.csproj",
        "tests/Hexalith.Projects.Integration.Tests/PackageReadFixture.cs",
        "tests/Hexalith.Projects.PackageFixtures/PackageCatalogWorker.cs",
        "tests/Hexalith.Projects.PackageFixtures/PackageOwnerWorker.cs",
        "tests/Hexalith.Projects.PackageFixtures/PackageHostingStartup.cs",
    ]
    loop = next(node for node in ast.parse(source).body if isinstance(node, ast.For)
                and isinstance(node.target, ast.Name) and node.target.id == "module")
    names = next(node for node in loop.body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == "names" for target in node.targets))
    lines = source.splitlines(keepends=True)
    lines[names.lineno - 1:names.end_lineno] = ["    names = []\n"]
    source = "".join(lines)
    preparation = (
        "    frozen_head = " + repr(heads) + "[module]\n"
        "    subprocess.run(['git', '-c', 'submodule.recurse=false', '-C', str(target), 'checkout', '--detach', frozen_head], check=True, capture_output=True)\n"
        "    frozen_tree = " + repr(trees) + ".get(module)\n"
        "    if frozen_tree:\n"
        "        subprocess.run(['git', '-c', 'submodule.recurse=false', '-C', str(target), 'read-tree', '--reset', '-u', frozen_tree], check=True, capture_output=True)\n"
        "    if module == 'Projects':\n"
        "        for fix_path in " + repr(fixes) + ":\n"
        "            output = target / fix_path\n"
        "            output.parent.mkdir(parents=True, exist_ok=True)\n"
        "            shutil.copyfile(repository / fix_path, output)\n"
        "            print('FIX OVERLAY', fix_path, hashlib.sha256(output.read_bytes()).hexdigest(), flush=True)\n"
        "    print('FROZEN SOURCE', name, frozen_head, frozen_tree, flush=True)\n"
    )
    source = source.replace(needle, preparation + needle)
    print("FOCUSED FROZEN INPUTS: original audited source trees plus listed fixture fixes; newer concurrent changes are preserved and excluded from this diagnostic only", flush=True)
elif "--freeze-original-queries" in sys.argv:
    # Newer concurrent metadata annotations require an unpublished SDK API.
    # This focused diagnostic retains the original query sources only in scratch;
    # it is explicitly not qualification of that newer complete working tree.
    paths = ["src/Hexalith.Projects.Contracts/Queries/" + name + ".cs" for name in
             ("GetProjectQuery", "ListProjectsQuery", "ResolveProjectFromAttachmentsQuery", "ResolveProjectFromConversationQuery")]
    preparation = (
        "    if module == 'Projects':\n"
        "        for original_query in " + repr(paths) + ":\n"
        "            frozen = subprocess.check_output(['git', '-C', str(repository), 'show', '7f45e5a3fde607e64a3648ed77f96f6367bdd490:' + original_query])\n"
        "            (target / original_query).write_bytes(frozen)\n"
        "            print('FOCUSED ORIGINAL QUERY', original_query, hashlib.sha256(frozen).hexdigest(), flush=True)\n"
    )
    source = source.replace(needle, preparation + needle)
    print("FOCUSED SOURCE: four original query files retained in scratch; newer SDK annotations preserved in the user's workspace and excluded from this diagnostic only", flush=True)
print("DIAGNOSTIC ONLY: existing driver with integration build target; actual full native/browser scenario loop unchanged", flush=True)
print("SOURCE DRIVER SHA256", hashlib.sha256(driver.read_bytes()).hexdigest(), flush=True)
sys.argv = [str(driver), "--nightly"]
exec(compile(source, str(driver), "exec"), {"__file__": str(driver), "__name__": "__main__"})
