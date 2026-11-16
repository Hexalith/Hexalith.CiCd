from pathlib import Path
import os
import subprocess

root=Path(os.environ['TMPDIR'])/'Hexalith.Projects'
results=Path('/home/administrator/projects/hexalith/cicd/_bmad-output/implementation-artifacts/evidence/projects-publication-gate-fix-20261116')
source=root/'tests/Hexalith.Projects.Integration.Tests/PackageReadFixture.cs'
original=source.read_bytes()
text=original.decode()
needle='''        Dictionary<string, PackageReadStateSnapshot> before = await AwaitFreshCutoverQuiescenceAsync('''
helper='''        static object Facts(KeyValuePair<string, PackageReadStateSnapshot> pair)
        {
            using JsonDocument document = JsonDocument.Parse(pair.Value.Bytes);
            var body = document.RootElement;
            bool hasItems = body.ValueKind == JsonValueKind.Object && body.TryGetProperty("items", out _);
            int? count = hasItems && body.GetProperty("items").ValueKind == JsonValueKind.Array ? body.GetProperty("items").GetArrayLength() : null;
            long? Number(string name) => body.ValueKind == JsonValueKind.Object && body.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.Number ? value.GetInt64() : null;
            string category = pair.Key.StartsWith("projection-activation:", StringComparison.Ordinal) ? "activation"
                : pair.Key.EndsWith("||projection-lifecycle", StringComparison.Ordinal) ? "lifecycle"
                : pair.Key.EndsWith("||projection-lifecycle-epoch", StringComparison.Ordinal) ? "epoch"
                : pair.Key.StartsWith("projection-checkpoints", StringComparison.Ordinal) ? "checkpoint" : "other";
            return new { category, keySha256 = Digest(pair.Key), etagSha256 = Digest(pair.Value.ETag), bytesSha256 = Digest(Convert.ToHexString(pair.Value.Bytes)),
                itemCount = count, lastRevision = Number("lastRevision"), lastDeliveredSequence = Number("lastDeliveredSequence"),
                properties = body.ValueKind == JsonValueKind.Object ? body.EnumerateObject().Select(property => property.Name).ToArray() : [] };
        }
        int observation = 0;
'''
assert text.count(needle)==1
text=text.replace(needle,helper+needle,1)
needle='''            return ProjectionDeliveryCutoverObserver.IsQuiescentWithCompletedSource(inventory.ToDictionary(pair => pair.Key,
                pair => (ReadOnlyMemory<byte>)pair.Value.Bytes, StringComparer.Ordinal), bootstrap, "global-administrators", PrimaryActor,
                allowLegacy: true, dapr.JsonSerializerOptions);'''
replacement='''            bool quiescent = ProjectionDeliveryCutoverObserver.IsQuiescentWithCompletedSource(inventory.ToDictionary(pair => pair.Key,
                pair => (ReadOnlyMemory<byte>)pair.Value.Bytes, StringComparer.Ordinal), bootstrap, "global-administrators", PrimaryActor,
                allowLegacy: true, dapr.JsonSerializerOptions);
            if (observation++ % 5 == 0) Console.WriteLine("[cutover-observation] " + JsonSerializer.Serialize(new { quiescent, states = inventory.Select(Facts) }, Json));
            return quiescent;'''
assert text.count(needle)==1
text=text.replace(needle,replacement,1)
source.write_text(text)
try:
    flags=['--configuration','Release','--no-restore','--disable-build-servers','-noAutoResponse','-p:UseHexalithProjectReferences=false','-p:ShouldUnsetParentConfigurationAndPlatform=false','-p:RestoreConfigFile='+str(root/'references/Hexalith.Builds/NuGet.ci.Config'),'-p:EnableNETAnalyzers=true','-p:RunAnalyzers=true','-p:RunAnalyzersDuringBuild=true','-p:UseSharedCompilation=false','-warnaserror','-m:1','-nr:false']
    with (results/'cutover-diagnostic-build.log').open('w') as output:
        code=subprocess.run(['dotnet','build','tests/Hexalith.Projects.Integration.Tests/Hexalith.Projects.Integration.Tests.csproj',*flags],cwd=root,stdout=output,stderr=subprocess.STDOUT).returncode
    print('CUTOVER DIAGNOSTIC BUILD EXIT',code,flush=True)
    if code: raise SystemExit(code)
    with (results/'cutover-diagnostic-fixture.log').open('w') as output:
        code=subprocess.run(['dotnet','tests/Hexalith.Projects.PackageFixtures/bin/Release/net11.0/Hexalith.Projects.PackageFixtures.dll','--root',str(root)],cwd=root,stdout=output,stderr=subprocess.STDOUT).returncode
    print('CUTOVER DIAGNOSTIC FIXTURE EXIT',code,flush=True)
finally:
    source.write_bytes(original)
raise SystemExit(code)
