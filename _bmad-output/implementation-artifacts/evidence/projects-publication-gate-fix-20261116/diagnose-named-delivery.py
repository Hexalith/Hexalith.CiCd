from pathlib import Path
import json
import os
import subprocess

root=Path(os.environ['TMPDIR'])/'Hexalith.Projects'
results=Path('/home/administrator/projects/hexalith/cicd/_bmad-output/implementation-artifacts/evidence/projects-publication-gate-fix-20261116')
source=root/'tests/Hexalith.Projects.Integration.Tests/PackageReadFixture.cs'
original=source.read_bytes()
text=original.decode()
start=text.index('    private async Task WaitForSeedNamedDeliveryAsync(')
first=text[:start]
method=text[start:]
needle='''        while (true)
        {
            cancellation.ThrowIfCancellationRequested();
            var before = await ReadSeedDeliveryStatesAsync(keys, cancellation).ConfigureAwait(false);'''
replacement='''        int observation = 0;
        while (true)
        {
            cancellation.ThrowIfCancellationRequested();
            var before = await ReadSeedDeliveryStatesAsync(keys, cancellation).ConfigureAwait(false);
            if (observation++ % 10 == 0)
                Console.WriteLine("[package-seed-observation] " + JsonSerializer.Serialize(new
                {
                    domain, source.Metadata.LatestSequence, source.Metadata.FromSequence, source.Metadata.EventCount,
                    projections = scopes.Select(scope => new
                    {
                        projection = scope.Projection,
                        checkpoint = CheckpointFacts(before[scope.Checkpoint]),
                        epochPresent = before[scope.Actor + "||projection-lifecycle-epoch"] is not null,
                        lifecyclePresent = before[scope.Actor + "||projection-lifecycle"] is not null,
                    }),
                }, Json));'''
assert needle in method
method=method.replace(needle,replacement,1)
needle='''        int observation = 0;'''
helper='''        static object CheckpointFacts(PackageReadStateSnapshot? value)
        {
            if (value is null) return new { present = false };
            using JsonDocument document = JsonDocument.Parse(value.Bytes);
            long? Number(string name) => document.RootElement.TryGetProperty(name, out var field) && field.ValueKind == JsonValueKind.Number ? field.GetInt64() : null;
            bool NonNull(string name) => document.RootElement.TryGetProperty(name, out var field) && field.ValueKind != JsonValueKind.Null;
            return new { present = true, schemaVersion = Number("schemaVersion"), writerProtocolVersion = Number("writerProtocolVersion"),
                lastDeliveredSequence = Number("lastDeliveredSequence"), firstRetainedSequence = Number("firstRetainedSequence"),
                activeReservation = NonNull("activeReservation"), idleBindingPending = NonNull("idleBindingPending"), guardEvidence = NonNull("guardEvidence") };
        }
        int observation = 0;'''
method=method.replace(needle,helper,1)
source.write_text(first+method)
try:
    flags=['--configuration','Release','--no-restore','--disable-build-servers','-noAutoResponse','-p:UseHexalithProjectReferences=false','-p:ShouldUnsetParentConfigurationAndPlatform=false','-p:RestoreConfigFile='+str(root/'references/Hexalith.Builds/NuGet.ci.Config'),'-p:EnableNETAnalyzers=true','-p:RunAnalyzers=true','-p:RunAnalyzersDuringBuild=true','-p:UseSharedCompilation=false','-warnaserror','-m:1','-nr:false']
    with (results/'named-delivery-diagnostic-build.log').open('w') as output:
        code=subprocess.run(['dotnet','build','tests/Hexalith.Projects.Integration.Tests/Hexalith.Projects.Integration.Tests.csproj',*flags],cwd=root,stdout=output,stderr=subprocess.STDOUT).returncode
    print('NAMED DELIVERY DIAGNOSTIC BUILD EXIT',code,flush=True)
    if code: raise SystemExit(code)
    with (results/'named-delivery-diagnostic-fixture.log').open('w') as output:
        code=subprocess.run(['dotnet','tests/Hexalith.Projects.PackageFixtures/bin/Release/net11.0/Hexalith.Projects.PackageFixtures.dll','--root',str(root)],cwd=root,stdout=output,stderr=subprocess.STDOUT).returncode
    print('NAMED DELIVERY DIAGNOSTIC FIXTURE EXIT',code,flush=True)
finally:
    source.write_bytes(original)
raise SystemExit(code)
