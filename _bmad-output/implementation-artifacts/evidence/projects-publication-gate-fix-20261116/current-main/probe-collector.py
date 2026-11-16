from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

base=Path(os.environ['TMPDIR'])/'collector-probe'
root=Path('/home/administrator/projects/hexalith/cicd')
source=root/'references/Hexalith.Projects/tests/Hexalith.Projects.PackageFixtures'
results=root/'_bmad-output/implementation-artifacts/evidence/projects-publication-gate-fix-20261116/current-main'
for d in ('AppHost','Workload','Driver'): (base/d).mkdir(parents=True,exist_ok=True)
shutil.copyfile(root/'references/Hexalith.Projects/global.json',base/'global.json')
(base/'AppHost/Collector.AppHost.csproj').write_text('''<Project Sdk="Aspire.AppHost.Sdk/13.6.5"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net11.0</TargetFramework><AspireUseCliBundle>true</AspireUseCliBundle><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup><ItemGroup><PackageReference Include="Aspire.Hosting.AppHost" Version="13.6.5"/><ProjectReference Include="../Workload/Collector.Workload.csproj"/></ItemGroup></Project>''')
shutil.copyfile(source.parent/'Hexalith.Projects.PackageFixtures.AppHost/PrebuiltMetadata.cs',base/'AppHost/PrebuiltMetadata.cs')
(base/'AppHost/Program.cs').write_text('''using Aspire.Hosting;
using Hexalith.Projects.PackageFixtures.AppHost;
var builder=DistributedApplication.CreateBuilder(args);
builder.AddProject<PrebuiltMetadata<Projects.Collector_Workload>>("projects",options=>options.ExcludeLaunchProfile=true)
    .WithHttpEndpoint().WithHttpHealthCheck("/alive")
    .WithEnvironment("COLLECTOR_PROBE_DIRECTORY",Environment.GetEnvironmentVariable("COLLECTOR_PROBE_DIRECTORY")!);
await using var application=builder.Build();
await application.RunAsync();
''')
(base/'Workload/Collector.Workload.csproj').write_text('''<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup><TargetFramework>net11.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup><ItemGroup><PackageReference Include="OpenTelemetry.Extensions.Hosting" Version="1.21.0"/><PackageReference Include="OpenTelemetry.Exporter.OpenTelemetryProtocol" Version="1.21.0"/></ItemGroup></Project>''')
shutil.copyfile(source/'PackageProcessReceipt.cs',base/'Workload/PackageProcessReceipt.cs')
(base/'Workload/Program.cs').write_text('''using System.Diagnostics;
using System.Diagnostics.Metrics;
using OpenTelemetry;
using OpenTelemetry.Logs;
using OpenTelemetry.Metrics;
using OpenTelemetry.Trace;
using Hexalith.Projects.PackageFixtures;
if(!OperatingSystem.IsLinux())throw new PlatformNotSupportedException();
var builder=WebApplication.CreateBuilder(args);
builder.Logging.AddOpenTelemetry();
builder.Services.AddOpenTelemetry().WithTracing(value=>value.AddSource("OwnedCollectorProbe"))
    .WithMetrics(value=>value.AddMeter("OwnedCollectorProbe")).UseOtlpExporter();
using ActivitySource activity=new("OwnedCollectorProbe");
using Meter meter=new("OwnedCollectorProbe");
var counter=meter.CreateCounter<long>("owned_restart_requests");
var app=builder.Build();
app.MapGet("/alive",()=>Results.Ok());
app.MapGet("/warm",(ILoggerFactory logs)=>
{
    using var span=activity.StartActivity("OwnedWarmRequest");counter.Add(1);
    LoggerMessage.Define(LogLevel.Warning,new EventId(9011),"Owned collector probe warmup")(logs.CreateLogger("OwnedCollectorProbe"),null);
    return Results.Ok();
});
PackageProcessReceipt.Write(Environment.GetEnvironmentVariable("COLLECTOR_PROBE_DIRECTORY")!,"projects");
await app.RunAsync();
''')
(base/'Driver/Collector.Driver.csproj').write_text('''<Project Sdk="Microsoft.NET.Sdk.Web"><PropertyGroup><TargetFramework>net11.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable></PropertyGroup><ItemGroup><PackageReference Include="Aspire.Hosting.Testing" Version="13.6.5"/><ProjectReference Include="../AppHost/Collector.AppHost.csproj" ReferenceOutputAssembly="false"/></ItemGroup></Project>''')
for name in ('PackageApplicationFactory.cs','FixtureScratch.cs','FixtureProcess.cs'):shutil.copyfile(source/name,base/'Driver'/name)
(base/'Driver/FixtureInputs.cs').write_text('''namespace Hexalith.Projects.PackageFixtures;
using System.Security.Cryptography;
internal static class FixtureInputs { internal static string Secret()=>Convert.ToHexStringLower(RandomNumberGenerator.GetBytes(32)); }
''')
run=(source/'PackageFixtureRun.cs').read_text();start=run.index('    private static async Task VerifyTelemetryAsync(');end=run.index('    private static async Task BrowserAsync(',start)
method=run[start:end]
(base/'Driver/Verifier.cs').write_text('''namespace Hexalith.Projects.PackageFixtures;
using System.Security.Cryptography;
using System.Text.Json;
using Aspire.Hosting;
using Aspire.Hosting.Testing;
using Grpc.Core;
using Grpc.Net.Client;
using Microsoft.Extensions.DependencyInjection;
internal static class PackageFixtureRun {
internal static Task ProbeAsync(PackageApplicationFactory factory,DistributedApplication application,FixtureScratch scratch,CancellationToken token)=>VerifyTelemetryAsync(factory,application,scratch,token);
'''+method+'}\n')
(base/'Driver/Program.cs').write_text('''using System.Diagnostics;
using System.Reflection;
using System.Text.Json;
using Aspire.Hosting;
using Aspire.Hosting.ApplicationModel;
using Hexalith.Projects.PackageFixtures;
using var budget=new CancellationTokenSource(TimeSpan.FromMinutes(5));
await using var scratch=new FixtureScratch(false);
Environment.SetEnvironmentVariable("COLLECTOR_PROBE_DIRECTORY",scratch.Directory);
string host=Path.GetFullPath("../AppHost/bin/Release/net11.0/Collector.AppHost.dll");
Type entry=Assembly.LoadFrom(host).GetType("Program")!;
await using var factory=new PackageApplicationFactory(entry,["--environment","Development","--Logging:LogLevel:Default=Warning"],scratch.Directory);
await factory.StartAsync(budget.Token);
var app=factory.Application!;
try {
    await app.ResourceNotifications.WaitForResourceHealthyAsync("projects",budget.Token);
    await PackageFixtureRun.ProbeAsync(factory,app,scratch,budget.Token);
    using var client=new HttpClient();
    for(int index=0;index<40;index++) {using var response=await client.GetAsync(new Uri(factory.GetEndpoint("projects","http"),"warm"),budget.Token);response.EnsureSuccessStatusCode();}
    using JsonDocument before=JsonDocument.Parse(await File.ReadAllBytesAsync(scratch.File("projects-process.json"),budget.Token));
    var elapsed=Stopwatch.StartNew();
    var result=await app.ResourceCommands.ExecuteCommandAsync("projects",KnownResourceCommands.RestartCommand,budget.Token);
    if(!result.Success)throw new InvalidOperationException("Owned warm restart failed.");
    await app.ResourceNotifications.WaitForResourceHealthyAsync("projects",budget.Token);
    using JsonDocument after=JsonDocument.Parse(await File.ReadAllBytesAsync(scratch.File("projects-process.json"),budget.Token));
    if(before.RootElement.GetProperty("pid").GetInt32()==after.RootElement.GetProperty("pid").GetInt32()
        ||before.RootElement.GetProperty("assemblySha256").GetString()!=after.RootElement.GetProperty("assemblySha256").GetString())throw new InvalidOperationException("Actual process replacement proof failed.");
    File.Copy(scratch.File("telemetry-receiver.json"),Environment.GetEnvironmentVariable("COLLECTOR_PROBE_RESULT")!,true);
    Console.WriteLine("OWNED_COLLECTOR_PROBE_PASSED warm_restart_milliseconds="+elapsed.ElapsedMilliseconds);
} finally { using var stop=new CancellationTokenSource(TimeSpan.FromMinutes(2));await app.StopAsync(stop.Token); }
''')
manifest={'scope':'Exact factory, process receipt and extracted telemetry verifier against real Aspire13.6.5/OpenTelemetry1.21 service. This is an isolated runtime regression probe, not current Projects or Folders pre-push acceptance.',
          'sources':{name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in ('PackageApplicationFactory.cs','PackageProcessReceipt.cs','PackageFixtureRun.cs','FixtureScratch.cs','FixtureProcess.cs')}}
(results/'collector-probe-inputs.json').write_text(json.dumps(manifest,indent=2)+'\n')
with (results/'collector-probe-build.log').open('w') as output:
    code=subprocess.run(['dotnet','build','Driver/Collector.Driver.csproj','-c','Release','--disable-build-servers','-p:UseSharedCompilation=false','-p:EnableNETAnalyzers=true','-p:RunAnalyzers=true','-p:RunAnalyzersDuringBuild=true','-warnaserror','-m:1','-nr:false','-p:RestoreConfigFile='+str(root/'references/Hexalith.Builds/NuGet.ci.Config')],cwd=base,stdout=output,stderr=subprocess.STDOUT).returncode
print('COLLECTOR PROBE BUILD EXIT',code,flush=True)
if code:raise SystemExit(code)
environment=os.environ.copy();environment['COLLECTOR_PROBE_RESULT']=str(results/'collector-probe-receiver.json')
with (results/'collector-probe-runtime.log').open('w') as output:
    code=subprocess.run(['dotnet','bin/Release/net11.0/Collector.Driver.dll'],cwd=base/'Driver',env=environment,stdout=output,stderr=subprocess.STDOUT).returncode
print('COLLECTOR PROBE RUNTIME EXIT',code,flush=True)
raise SystemExit(code)
