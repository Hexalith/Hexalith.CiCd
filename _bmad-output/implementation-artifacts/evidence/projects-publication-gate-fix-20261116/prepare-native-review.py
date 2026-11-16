from pathlib import Path
import difflib
root=Path('/home/administrator/projects/hexalith/cicd')
source=root/'references/Hexalith.Projects/tests'
patch=''
def add(p,before,after):
    global patch
    label='references/Hexalith.Projects/tests/'+p
    patch+=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+label,tofile='b/'+label))
p='Hexalith.Projects.PackageFixtures/FixtureInputs.cs';after=(source/p).read_text();before=after
before=before.replace('        using RSA folderScan = RSA.Create(2048), folderWorker = RSA.Create(2048), folderWorkerScan = RSA.Create(2048);\n','',1)
a=before.index('            FolderScanPrivateKey = ');b=before.index('            CertificatePath = ',a);before=before[:a]+before[b:];add(p,before,after)
p='Hexalith.Projects.PackageFixtures.AppHost/PackageActualOwnerComposition.cs';after=(source/p).read_text();before=after
before=before.replace(', "FolderScanPrivateKey", "FolderScanPublicKey", "FolderWorkersSecret", "FolderWorkerPrivateKey", "FolderWorkerPublicKey", "FolderWorkerScanPrivateKey", "FolderWorkerScanPublicKey"','',1)
a=before.index('        foreach (var source in new[]');b=before.index('        _ = eventStore.WaitFor(authority);',a)
before=before[:a]+'''        IResourceBuilder<ParameterResource> foldersSecret = Secret("folders-secret", "FoldersSecret");
        IResourceBuilder<ParameterResource> folderOwnerKey = Secret("folders-owner-key", "FolderOwnerPrivateKey");
        ConfigureClient(folders, "folders", foldersSecret);
        int folderGrant = ordinal;
        AddGrant("folders-owner-head", "folders", "FoldersSecret", "eventstore", ["eventstore:stream-read"], false);
        string grant = "Authentication__WorkloadAuthority__Grants__" + folderGrant + "__";
        _ = authority.WithEnvironment(grant + "AllowUnbound", "false")
            .WithEnvironment(grant + "Bindings__eventstore:bound-tenant__0", Required(configuration, Prefix + "Tenant"))
            .WithEnvironment(grant + "Bindings__eventstore:bound-tenant__1", Required(configuration, Prefix + "ForeignTenant"))
            .WithEnvironment(grant + "Bindings__eventstore:bound-domain__0", "folders");
        _ = folders.WithEnvironment("Authentication__BoundStreamRead__PrivateKey", folderOwnerKey);
        _ = eventStore.WithEnvironment("Authentication__DaprInternal__AllowedCallers__2", "folders")
            .WithEnvironment("Authentication__BoundStreamRead__PublicKeys__folders", Required(configuration, Prefix + "FolderOwnerPublicKey"))
            .WithEnvironment("Authentication__BoundStreamRead__AllowedDomains__folders", "folders");
'''+before[b:];add(p,before,after)
p='Hexalith.Projects.PackageFixtures.AppHost/PackageActualOwnerInfrastructure.cs';after=(source/p).read_text();before=after
for line in ('new(folders, "api/v1/streams/scan/workload", ["POST"]),','new(foldersWorkers, "api/v1/streams/read/workload", ["POST"]),','new(foldersWorkers, "api/v1/streams/scan/workload", ["POST"]),'):
    before=before.replace('                '+line+'\n','',1)
add(p,before,after)
p='Hexalith.Projects.Integration.Tests/PackageCredentialMatrixTests.cs';after=(source/p).read_text();before=after
before=before.replace('extern alias PackageFixtureHost;\n\n','',1).replace('using Microsoft.Extensions.Configuration;\n','',1).replace('using PackageHost = PackageFixtureHost::Hexalith.Projects.PackageFixtures.AppHost;\n','',1)
a=before.index('            HashSet<string> proofKeys = ');b=before.index('            Dictionary<string, string> browser = ',a);before=before[:a]+before[b:];add(p,before,after)
result=root/'_bmad-output/implementation-artifacts/evidence/projects-publication-gate-fix-20261116/native-scan-review.diff';result.write_text(patch);print(result.stat().st_size)
