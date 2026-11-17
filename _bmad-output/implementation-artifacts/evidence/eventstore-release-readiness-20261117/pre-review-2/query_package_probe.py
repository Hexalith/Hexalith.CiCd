"""Compile the requested query API using three real, unpublished archives."""

import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import zipfile

from verification_core import digest, require


def probe(owner, work, output, env, run, source):
    version = "5.2.1-local-readiness." + source[:8]
    feed = work / "query-api-feed"
    feed.mkdir()
    identities = ("Contracts", "Client", "RestApi.Generators")
    archives = []
    for identity in identities:
        package = "Hexalith.EventStore." + identity
        project = f"src/{package}/{package}.csproj"
        run("query-pack-" + identity, ["dotnet", "pack", project, "--configuration", "Release",
            "--output", str(feed), "-warnaserror", "-m:1", f"-p:Version={version}",
            "-p:GeneratePackageOnBuild=false", "-p:UseHexalithProjectReferences=false",
            "-p:UseNuGetDeps=true"], cwd=owner, required=True)
        archive = feed / f"{package}.{version}.nupkg"
        require(archive.exists(), f"Missing actual archive {archive.name}")
        with zipfile.ZipFile(archive) as opened:
            nuspec_name = next(name for name in opened.namelist() if name.endswith(".nuspec"))
            nuspec = opened.read(nuspec_name)
            root = ET.fromstring(nuspec)
            values = {node.tag.rsplit("}", 1)[-1]: node.text for node in root.iter()}
            require(values.get("id") == package and values.get("version") == version,
                    "Archive metadata does not match candidate identity")
            analyzer = f"analyzers/dotnet/cs/{package}.dll"
            if identity == "RestApi.Generators":
                require(analyzer in opened.namelist(), "Real generator archive lacks its packaged analyzer")
            metadata = output / "package-metadata" / nuspec_name
            metadata.parent.mkdir(exist_ok=True)
            metadata.write_bytes(nuspec)
        archives.append({"name": archive.name, "sha256": digest(archive),
                         "id": package, "version": version, "published": False})
    root = work / "synthetic-query-api"
    root.mkdir()
    shutil.copy2(owner / "global.json", root / "global.json")
    (root / "NuGet.Config").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<configuration><packageSources><clear />
<add key="candidate" value="{feed}" />
<add key="nuget.org" value="https://api.nuget.org/v3/index.json" />
</packageSources></configuration>
''')
    properties = '''<PropertyGroup><TargetFramework>net11.0</TargetFramework>
<Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings>
<TreatWarningsAsErrors>true</TreatWarningsAsErrors><EnableNETAnalyzers>true</EnableNETAnalyzers>
<NuGetAudit>true</NuGetAudit><NuGetAuditMode>all</NuGetAuditMode><NuGetAuditLevel>low</NuGetAuditLevel>
<EmitCompilerGeneratedFiles>true</EmitCompilerGeneratedFiles>
<CompilerGeneratedFilesOutputPath>$(BaseIntermediateOutputPath)generated</CompilerGeneratedFilesOutputPath>
</PropertyGroup>'''
    contracts = root / "Owner.Contracts"
    consumer = root / "Probe.Consumer"
    contracts.mkdir()
    consumer.mkdir()
    (contracts / "Owner.Contracts.csproj").write_text(f'''<Project Sdk="Microsoft.NET.Sdk">{properties}
<ItemGroup><PackageReference Include="Hexalith.EventStore.Contracts" Version="[{version}]" /></ItemGroup>
</Project>''')
    (contracts / "Query.cs").write_text('''using Hexalith.EventStore.Contracts.Queries;
namespace Owner;
[QueryResultContract(typeof(Result), "owner", "Owner.Queries.Read.v1")]
public sealed record Query(string OpaqueId);
''')
    (contracts / "Result.cs").write_text('''namespace Owner;
public sealed record Result(string OpaqueId);
''')
    (consumer / "Probe.Consumer.csproj").write_text(f'''<Project Sdk="Microsoft.NET.Sdk">{properties}
<ItemGroup>
<ProjectReference Include="../Owner.Contracts/Owner.Contracts.csproj" />
<PackageReference Include="Hexalith.EventStore.Contracts" Version="[{version}]" />
<PackageReference Include="Hexalith.EventStore.Client" Version="[{version}]" />
<PackageReference Include="Hexalith.EventStore.RestApi.Generators" Version="[{version}]" PrivateAssets="all" />
</ItemGroup></Project>''')
    (consumer / "RequireGeneratedQuery.cs").write_text('''using Hexalith.EventStore.Client.Gateway;
using Probe.Consumer.Generated;
namespace Probe.Consumer;
public static class RequireGeneratedQuery
{
    public static Task<EventStoreQueryResult<Owner.Result>> Compile(IEventStoreGatewayClient gateway)
        => gateway.QueryAsync("tenant", "opaque-target", new Owner.Query("opaque-query"));
}
''')
    for path in root.rglob("*"):
        if path.is_file():
            target = output / "synthetic-consumer-inputs" / path.relative_to(root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    project = consumer / "Probe.Consumer.csproj"
    run("query-consumer-restore", ["dotnet", "restore", str(project),
        "--configfile", str(root / "NuGet.Config"), "-p:Configuration=Release"], cwd=root, required=True)
    run("query-consumer-build", ["dotnet", "build", str(project), "--no-restore",
        "--configuration", "Release", "-warnaserror", "-m:1"], cwd=root, required=True)
    generated = list(consumer.rglob("TypedGatewayQueries.g.cs"))
    require(len(generated) == 1, "Expected exactly one real packaged-generator typed binding")
    text = generated[0].read_text()
    require("SubmitQueryAsync<global::Owner.Result>" in text and '"Owner.Queries.Read.v1"' in text,
            "Generated binding does not use the owner result and existing wire query")
    require(all(value not in text for value in ("HttpGet", "Controller", "catch")),
            "Typed binding unexpectedly creates REST route or exception behavior")
    target = output / "TypedGatewayQueries.g.cs"
    shutil.copy2(generated[0], target)
    resolved = {}
    for project_dir in (contracts, consumer):
        assets = json.loads((project_dir / "obj/project.assets.json").read_text())
        libraries = assets["libraries"]
        expected = identities if project_dir == consumer else ("Contracts",)
        for identity in expected:
            key = f"Hexalith.EventStore.{identity}/{version}"
            require(key in libraries and libraries[key]["type"] == "package", f"Not a real package: {key}")
        resolved[project_dir.name] = sorted(libraries)
    return {"passed": True, "source": source, "version": version, "published": False,
            "archives": archives, "resolved_libraries": resolved,
            "generated_binding": {"path": target.name, "sha256": digest(target)},
            "boundary": "synthetic attributed owner assembly plus consumer compiled with packaged analyzer",
            "projects_consumer_retested": False, "producer_source_changed": False}
