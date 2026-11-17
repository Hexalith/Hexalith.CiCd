"""Compile the real product verifier against pinned public Aspire APIs and exercise its custody boundary."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
root=Path.cwd();module=root/'references/Hexalith.McpCli';scratch=Path(os.environ['TMPDIR']);repo=scratch/'module';repo.mkdir();fixture=scratch/'source-fixture';fixture.mkdir()
sys.path.insert(0,str(module/'tools/live-topology'));import native_sources
selection={'sources':{}}
for name in native_sources.MODULES:
 checkout=fixture/name;checkout.mkdir();subprocess.run(['git','init','--quiet',str(checkout)],check=True)
 (checkout/'source.cs').write_text('original source')
 (checkout/'.gitignore').write_text('bin/\nobj/\n')
 subprocess.run(['git','add','.'],cwd=checkout,check=True)
 subprocess.run(['git','-c','user.name=Fixture','-c','user.email=fixture@example.invalid','-c','commit.gpgsign=false','commit','--quiet','-m','test: fixture identity'],cwd=checkout,check=True)
 selection['sources'][name]={'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout).decode().strip()}
 out=checkout/'src'/name/'bin/Release/net11.0/host.dll';out.parent.mkdir(parents=True);out.write_bytes(b'prepared output')
 location=repo/'tools/live-topology/native-runtime-current.json';location.parent.mkdir(parents=True,exist_ok=True);location.write_text(json.dumps(selection))
proof={'schemaVersion':1,'result':'prepared','selection':{name:item['commit'] for name,item in selection['sources'].items()},'modules':{name:{'path':str(fixture/name),'commit':selection['sources'][name]['commit']} for name in native_sources.MODULES}}
native_sources.seal(proof);receipt=scratch/'fixtures.json';receipt.write_text(json.dumps(proof));digest=hashlib.sha256(receipt.read_bytes()).hexdigest()
harness=scratch/'verifier';harness.mkdir();(harness/'global.json').write_bytes((module/'global.json').read_bytes());(harness/'NativeSourceFixtures.cs').write_bytes((module/'tests/Hexalith.McpCli.AppHost/NativeSourceFixtures.cs').read_bytes())
(harness/'Verifier.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net11.0</TargetFramework><OutputType>Exe</OutputType><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><TreatWarningsAsErrors>true</TreatWarningsAsErrors></PropertyGroup><ItemGroup><PackageReference Include="Aspire.Hosting" Version="13.6.5"/><PackageReference Include="Hexalith.EventStore.Aspire" Version="5.1.0"/></ItemGroup></Project>')
(harness/'TopologyConfiguration.cs').write_text('namespace Hexalith.McpCli.AppHost; internal static class TopologyConfiguration { internal static string ResolveGatewayProject(string root,bool package,bool publish) => root; }')
(harness/'NuGet.Config').write_text('<configuration><packageSources><clear/><add key="nuget" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>')
(harness/'Program.cs').write_text(r'''
using Hexalith.McpCli.AppHost;
using System.Security.Cryptography;
string root=args[0],receipt=args[1],digest=args[2],fixture=args[3];
string selected=NativeSourceFixtures.RequireModule(root,"Hexalith.Tenants",receipt,digest);
if(selected!=Path.Combine(fixture,"Hexalith.Tenants")) throw new Exception("wrong source selected");
void Reject(Action mutation,Action restore,string label){mutation();try{NativeSourceFixtures.RequireModule(root,"Hexalith.Tenants",receipt,digest);throw new Exception("accepted "+label);}catch(System.IO.InvalidDataException){Console.WriteLine("Rejected "+label);}finally{restore();}}
string source=Path.Combine(selected,"source.cs");byte[] original=File.ReadAllBytes(source);
Reject(()=>File.WriteAllText(source,"changed"),()=>File.WriteAllBytes(source,original),"changed source");
string output=Path.Combine(selected,"src/Hexalith.Tenants/bin/Release/net11.0/host.dll");byte[] built=File.ReadAllBytes(output);
Reject(()=>File.WriteAllText(output,"changed"),()=>File.WriteAllBytes(output,built),"changed built output");
string unexpected=Path.Combine(selected,"unexpected.cs");
Reject(()=>File.WriteAllText(unexpected,"unexpected"),()=>File.Delete(unexpected),"untracked source");
string nested=Path.Combine(selected,"references/Hexalith.Builds/.git");
Reject(()=>Directory.CreateDirectory(nested),()=>Directory.Delete(Path.Combine(selected,"references"),true),"nested Builds initialization");
byte[] receiptBytes=File.ReadAllBytes(receipt);
Reject(()=>File.AppendAllText(receipt," "),()=>File.WriteAllBytes(receipt,receiptBytes),"receipt byte drift");
if(!new PreparedGatewayProject().SuppressBuild||!new PreparedTenantsProject().SuppressBuild||!new PreparedPartiesProject().SuppressBuild)throw new Exception("rebuild enabled");
Console.WriteLine("Exact private source selected; all resource metadata suppresses rebuilding.");
''')
env=dict(os.environ,NUGET_PACKAGES=str(scratch/'packages'),NUGET_HTTP_CACHE_PATH=str(scratch/'http'),DOTNET_NOLOGO='1',DOTNET_CLI_TELEMETRY_OPTOUT='1')
subprocess.run(['dotnet','restore','Verifier.csproj','--configfile','NuGet.Config','-p:NuGetAudit=true','-p:NuGetAuditMode=all','-p:NuGetAuditLevel=low','-warnaserror'],cwd=harness,env=env,check=True)
subprocess.run(['dotnet','build','Verifier.csproj','--no-restore','--configuration','Release','-warnaserror'],cwd=harness,env=env,check=True)
subprocess.run(['dotnet',str(harness/'bin/Release/net11.0/Verifier.dll'),str(repo),str(receipt),digest,str(fixture)],cwd=harness,env=env,check=True)
print('Verifier source SHA256:',hashlib.sha256((harness/'NativeSourceFixtures.cs').read_bytes()).hexdigest(),flush=True)
