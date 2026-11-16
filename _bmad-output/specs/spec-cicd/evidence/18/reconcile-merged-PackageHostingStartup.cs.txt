using Hexalith.Projects.PackageFixtures;

using Microsoft.AspNetCore.Hosting;

[assembly: HostingStartup(typeof(PackageHostingStartup))]

namespace Hexalith.Projects.PackageFixtures;

using Hexalith.EventStore.DomainService;
using Hexalith.Folders.Authorization;
using Microsoft.Extensions.DependencyInjection.Extensions;

using Hexalith.EventStore.ServiceDefaults.Authentication;
using Hexalith.EventStore.ServiceDefaults.Routing;
using Hexalith.EventStore.Testing.CatalogInvocation;
using Hexalith.EventStore.Testing.OwnerSourceRead;

using Microsoft.Extensions.Options;
using Microsoft.Extensions.Logging;

/// <summary>Fixture-only adapters using the actual prebuilt gateway/owner services, never producer Debug helper activation.</summary>
public sealed class PackageHostingStartup : IHostingStartup
{
    /// <inheritdoc/>
    public void Configure(IWebHostBuilder builder)
    {
        ArgumentNullException.ThrowIfNull(builder);
        builder.ConfigureServices((context, services) =>
        {
            if (!context.HostingEnvironment.IsDevelopment() || context.Configuration["HEXALITH_PACKAGE_STARTUP"] != "1")
                throw new InvalidOperationException("Package adapters require explicit private Development activation.");
            string role = context.Configuration["HEXALITH_PACKAGE_ROLE"] ?? throw new InvalidOperationException("Missing fixture role.");
            string directory = context.Configuration["HEXALITH_PACKAGE_DIRECTORY"] ?? throw new InvalidOperationException("Missing private fixture directory.");
            if (!OperatingSystem.IsLinux() || !Path.IsPathFullyQualified(directory) || new DirectoryInfo(directory).LinkTarget is not null
                || (File.GetUnixFileMode(directory) & (UnixFileMode.GroupRead | UnixFileMode.GroupWrite | UnixFileMode.GroupExecute
                    | UnixFileMode.OtherRead | UnixFileMode.OtherWrite | UnixFileMode.OtherExecute)) != 0)
                throw new InvalidOperationException("Package adapters require an owned private directory.");
            _ = new PackageIpcFiles(directory);
            string endpoint = context.Configuration["DAPR_HTTP_ENDPOINT"] ?? "http://127.0.0.1:" + context.Configuration["DAPR_HTTP_PORT"];
            if (!Uri.TryCreate(endpoint, UriKind.Absolute, out Uri? dapr) || !dapr.IsLoopback || dapr.Scheme != "http"
                || dapr.Port <= 0 || dapr.AbsolutePath != "/") throw new InvalidOperationException("Package adapter requires the actual local sidecar.");
            if (role == "eventstore")
                services.AddSingleton<IHostedService>(provider => new PackageCatalogWorker(new CatalogInvocationOptions
                {
                    Directory = Path.Combine(directory, "invocation"), MetadataAppIds = ["projects", "folders"], ProjectionAppId = "projects",
                }, provider.GetRequiredService<IRouteCatalogAuthority>(), provider.GetRequiredService<IOptions<RouteCatalogHostOptions>>(),
                    provider.GetRequiredService<IWorkloadAssertionIssuer>(), dapr,
                    provider.GetRequiredService<ILogger<PackageCatalogWorker>>()));
            else if (role == "tenants")
                services.AddSingleton<IHostedService>(provider =>
                {
                    HttpClient http = new(new RouteCatalogInvocationHandler(provider.GetRequiredService<IRouteCatalogAuthority>(),
                        new SocketsHttpHandler { AllowAutoRedirect = false }, provider.GetRequiredService<IOptions<RouteCatalogHostOptions>>()))
                    { BaseAddress = new Uri(dapr, "/v1.0/invoke/eventstore/method/") };
                    PackageOwnerGateway gateway = new(http, provider.GetRequiredService<IWorkloadAssertionIssuer>(), context.Configuration, TimeProvider.System);
                    return new PackageOwnerWorker(new OwnerSourceReadOptions { Directory = Path.Combine(directory, "owner-source") },
                        gateway.ReadAsync, provider.GetRequiredService<ILogger<PackageOwnerWorker>>());
                });
            else if (role == "folders")
            {
                if (context.Configuration["Authentication:WorkloadIssuer:Workload"] != "folders"
                    || string.IsNullOrWhiteSpace(context.Configuration["Authentication:BoundStreamRead:PrivateKey"]))
                    throw new InvalidOperationException("Package Folder source reads require the actual owner identity and proof key.");
                services.AddEventStoreGatewayAuthoritativeEventStreamReader("folders");
                services.Replace(ServiceDescriptor.Singleton<IOrganizationStreamSequenceReader, GatewayOrganizationStreamSequenceReader>());
            }
            else if (role != "projects") throw new InvalidOperationException("Unknown private package adapter role.");
            // DCP's finite stop window must exceed the selected host's graceful drain.
            // This private profile still requires the original process to exit before restart.
            if (role is "projects" or "folders")
                services.Configure<HostOptions>(options => options.ShutdownTimeout = TimeSpan.FromSeconds(5));
            PackageProcessReceipt.Write(directory, role);
        });
    }
}
