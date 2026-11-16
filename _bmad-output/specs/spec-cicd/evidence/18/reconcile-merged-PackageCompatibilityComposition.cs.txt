namespace Hexalith.Projects.PackageFixtures.AppHost;

using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

using global::Aspire.Hosting;
using global::Aspire.Hosting.ApplicationModel;
using CommunityToolkit.Aspire.Hosting.Dapr;
using Hexalith.EventStore.Aspire;
using Hexalith.Projects.Aspire;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;

/// <summary>Composes an owned compatibility lane without enrolling or modifying a shared backend.</summary>
public static class PackageCompatibilityComposition
{
    /// <summary>The isolated compatibility profile's explicit opt-in key.</summary>
    public const string EnabledConfigurationKey = "Projects:PackageFixtures:Enabled";
    private const string Prefix = "Projects:PackageFixtures:";

    /// <summary>Returns whether the runner explicitly selected the isolated compatibility profile.</summary>
    public static bool IsEnabled(IConfiguration configuration)
    {
        ArgumentNullException.ThrowIfNull(configuration);
        return configuration.GetValue<bool>(EnabledConfigurationKey);
    }

    /// <summary>Loads private runner inputs before security and sibling resources are selected.</summary>
    public static void Configure(IDistributedApplicationBuilder builder)
    {
        ArgumentNullException.ThrowIfNull(builder);
        if (!IsEnabled(builder.Configuration)) return;
        if (!builder.Environment.IsDevelopment())
            throw new InvalidOperationException("Package fixtures require their private Development environment.");
        string path = Path.GetFullPath(Required(builder.Configuration, Prefix + "ConfigurationFile"));
        EnsurePrivate(path);
        builder.Configuration.AddJsonFile(path, optional: false, reloadOnChange: false);
        Validate(builder.Configuration);
    }

    /// <summary>Rejects shared dependencies, mixed fixture profiles and incomplete private trust.</summary>
    public static void Validate(IConfiguration configuration)
    {
        ArgumentNullException.ThrowIfNull(configuration);
        if (!string.Equals(configuration["EnableKeycloak"], "false", StringComparison.OrdinalIgnoreCase)
            || configuration.GetValue<bool>("KeycloakPersistent"))
            throw new InvalidOperationException("The isolated compatibility profile cannot adopt another security or owner profile.");
        string isolation = Required(configuration, Prefix + "IsolationId");
        if (!System.Text.RegularExpressions.Regex.IsMatch(isolation, configuration[Prefix + "Mode"] == "actual-owner"
            ? "^reads-[a-z0-9]{24}$" : "^fixtures-[a-z0-9]{24}$"))
            throw new InvalidOperationException("An owned compatibility namespace is required.");
        string directory = Path.GetDirectoryName(Required(configuration, Prefix + "CertificatePath"))!;
        foreach (string key in new[] { "CertificatePath", "TrustBundle", "DiscoveryConfiguration" })
        {
            string path = Required(configuration, Prefix + key);
            if (!Path.IsPathFullyQualified(path) || Path.GetDirectoryName(path) != directory)
                throw new InvalidOperationException("Trust and discovery inputs must belong to the private runner directory.");
            EnsurePrivate(path);
        }
        if (!Uri.TryCreate(Required(configuration, Prefix + "UserIssuer"), UriKind.Absolute, out Uri? issuer)
            || issuer.Scheme != "https" || !issuer.IsLoopback)
            throw new InvalidOperationException("Isolated compatibility fixtures require an owned HTTPS OIDC issuer.");
        if (!System.Net.IPEndPoint.TryParse(Required(configuration, "Dapr:RedisHost"), out var redis)
            || !System.Net.IPAddress.IsLoopback(redis.Address) || redis.Port is 0 or 6379)
            throw new InvalidOperationException("Compatibility storage must use an owned loopback backend.");
        using JsonDocument discovery = JsonDocument.Parse(File.ReadAllBytes(Required(configuration, Prefix + "DiscoveryConfiguration")));
        JsonElement resolver = discovery.RootElement.GetProperty("spec").GetProperty("nameResolution");
        string registry = resolver.GetProperty("configuration").GetProperty("connectionString").GetString()!;
        if (resolver.GetProperty("component").GetString() != "sqlite" || resolver.GetProperty("version").GetString() != "v1"
            || registry != Path.Combine(directory, "discovery.sqlite") || File.Exists(registry))
            throw new InvalidOperationException("Compatibility discovery requires a fresh private registry.");
        foreach (string key in new[] { "CertificatePassword", "CatalogDigestKey", "EventStoreSecret", "ProjectsSecret", "TenantsSecret",
            "OwnerPrivateKey", "OwnerPublicKey", "TenantOwnerPrivateKey", "TenantOwnerPublicKey", "ReceiptKey", "BootstrapPassword",
            "Tenant", "ForeignTenant", "Root", "Browser:PrimaryActor", "Browser:ClientSecret" })
            _ = Required(configuration, Prefix + key);
    }

    /// <summary>Uses generic SDK catalog composition, Platform mTLS and a private workload authority.</summary>
    public static DevelopmentRouteCatalogComposition AddResources(IDistributedApplicationBuilder builder,
        IResourceBuilder<ProjectResource> gateway, IResourceBuilder<ProjectResource> tenants,
        IResourceBuilder<ProjectResource> projects, IResourceBuilder<ProjectResource> workers,
        IResourceBuilder<ProjectResource> ui, string resourcesPath)
    {
        ArgumentNullException.ThrowIfNull(builder);
        ArgumentNullException.ThrowIfNull(gateway);
        ArgumentNullException.ThrowIfNull(tenants);
        ArgumentNullException.ThrowIfNull(projects);
        ArgumentNullException.ThrowIfNull(workers);
        ArgumentNullException.ThrowIfNull(ui);
        ArgumentException.ThrowIfNullOrWhiteSpace(resourcesPath);
        IConfiguration configuration = builder.Configuration;
        string Value(string key) => Required(configuration, Prefix + key);
        string isolation = Value("IsolationId"), directory = Path.GetDirectoryName(Value("CertificatePath"))!;
        string root = Value("Root");
        IResourceBuilder<ParameterResource> Secret(string name, string key)
            => builder.AddParameter("isolated-fixture-" + name, () => Value(key), secret: true);
        var certificatePassword = Secret("certificate-password", "CertificatePassword");
        var receipt = Secret("receipt", "ReceiptKey");
        var authority = builder.AddProject<PrebuiltMetadata<global::Projects.Hexalith_Projects_PackageFixtures>>("live-fixture-authority", options => options.ExcludeLaunchProfile = true)
            .WithArgs("--authority")
            .WithHttpsEndpoint(name: "https").WithHttpEndpoint(name: "http")
            .WithEnvironment("Kestrel__Certificates__Default__Path", Value("CertificatePath"))
            .WithEnvironment("Kestrel__Certificates__Default__Password", certificatePassword);
        _ = authority.WithHttpHealthCheck(() => authority.GetEndpoint("http"), path: "/alive");
        ReferenceExpression issuer = ReferenceExpression.Create($"{authority.GetEndpoint("https")}/workload-authority");
        _ = authority.WithEnvironment("ASPNETCORE_ENVIRONMENT", "Development")
                .WithEnvironment("Logging__Console__FormatterName", "json")
            .WithEnvironment("Authentication__WorkloadAuthority__Enabled", "true")
            .WithEnvironment("Authentication__WorkloadAuthority__NonconformingDevelopmentFixture", "true")
            .WithEnvironment("Authentication__WorkloadAuthority__Issuer", issuer)
            .WithEnvironment("Authentication__WorkloadAuthority__KeyId", isolation)
            .WithEnvironment("Authentication__WorkloadAuthority__SigningCertificatePath", Value("CertificatePath"))
            .WithEnvironment("Authentication__WorkloadAuthority__SigningCertificatePassword", certificatePassword);
        var (state, pubsub) = builder.AddProjectsSharedDaprComponents(Required(configuration, "Dapr:RedisHost"));
        foreach (var resource in new[] { gateway, tenants, projects, workers })
        {
            string name = resource.Resource.Name;
            _ = resource.WithEnvironment("ASPNETCORE_ENVIRONMENT", "Development")
                .WithEnvironment("Logging__Console__FormatterName", "json")
                .WithEnvironment("EventStore__DomainService__AppId", name)
                .WithEnvironment("Authentication__Workload__Audience", name)
                .WithEnvironment("Authentication__Workload__AllowedCallers__0", "eventstore")
                .WithEnvironment("XDG_DATA_HOME", Path.Combine(directory, "data-" + name))
                .WithEnvironment("SSL_CERT_FILE", Value("TrustBundle")).WithEnvironment("NAMESPACE", isolation)
                .WithEnvironment("Authentication__JwtBearer__Authority", Value("UserIssuer"))
                .WithEnvironment("Authentication__JwtBearer__Issuer", Value("UserIssuer"))
                .WithEnvironment("Authentication__JwtBearer__Audience", "supported-read-users")
                .WithEnvironment("Authentication__JwtBearer__SigningKey", string.Empty)
                .WithEnvironment("Authentication__JwtBearer__AllowedAlgorithms__0", "RS256")
                .WithEnvironment("Authentication__JwtBearer__RequireHttpsMetadata", "true")
                .WithEnvironment("Authentication__JwtBearer__AllowAnonymousDevelopment", "false")
                .WithEnvironment("Authentication__WorkloadJwtBearer__Authority", issuer)
                .WithEnvironment("Authentication__WorkloadJwtBearer__Issuer", issuer)
                .WithEnvironment("Authentication__WorkloadJwtBearer__Audience", name)
                .WithEnvironment("Authentication__WorkloadJwtBearer__RequireHttpsMetadata", "true")
                .WithEnvironment("Authentication__WorkloadJwtBearer__SigningKey", string.Empty)
                .WithEnvironment("Authentication__WorkloadJwtBearer__AllowedAlgorithms__0", "RS256")
                .WithEnvironment("Authentication__HumanAuthorityReceipt__SigningKey", receipt)
                .WithDaprSidecar(sidecar =>
                {
                    _ = sidecar.WithOptions(new DaprSidecarOptions
                    {
                        AppId = name, Config = Value("DiscoveryConfiguration"), ResourcesPaths = [resourcesPath],
                        // The legacy tenant journal's initial save predates conditional-create
                        // semantics. Serialize only this private callback host; browser work stays parallel.
                        AppMaxConcurrency = name == "projects-workers" ? 1 : null,
                        AppHealthCheckPath = "/alive", EnableAppHealthCheck = true,
                        PlacementHostAddress = Required(configuration, "Dapr:PlacementHostAddress"),
                        SchedulerHostAddress = Required(configuration, "Dapr:SchedulerHostAddress"),
                    }).WithReference(state).WithReference(pubsub);
                    sidecar.Resource.Annotations.Add(new EnvironmentCallbackAnnotation(context => context.EnvironmentVariables["NAMESPACE"] = isolation));
                });
        }
        builder.Configuration["Dapr:Mtls:CertificateDirectory"] = Path.Combine(directory, "mtls");
        var infrastructure = DaprSelfHostedMtls.AddLocalApplicationInfrastructure(builder, root,
            Path.Combine(resourcesPath, "sentry.yaml"), isolation);
        Write(directory, "mtls-plane.json", new { isolationId = isolation, runDirectory = infrastructure.RunDirectory,
            certificateDirectory = infrastructure.CertificateDirectory });
        foreach (ContainerResource resource in builder.Resources.OfType<ContainerResource>()
            .Where(resource => resource.Name is "dapr-sentry" or "dapr-placement-mtls" or "dapr-scheduler-mtls"))
            _ = builder.CreateResourceBuilder(resource).WithContainerRuntimeArgs("--label", "hexalith.supported-reads=" + isolation);
        int ordinal = 0;
        void Client(IResourceBuilder<ProjectResource> resource, string key)
        {
            string name = resource.Resource.Name;
            _ = resource.WithEnvironment("Authentication__WorkloadIssuer__Workload", name)
                .WithEnvironment("Authentication__WorkloadIssuer__ClientId", name + "-fixture")
                .WithEnvironment("Authentication__WorkloadIssuer__ClientSecret", Secret(name, key))
                .WithEnvironment("Authentication__WorkloadIssuer__EnableResourceBindingRequests", "true")
                .WithEnvironment("Authentication__WorkloadIssuer__TokenEndpoint", ReferenceExpression.Create($"{issuer}/token"));
        }
        string Grant(string workload, string key, string audience, params string[] operations)
        {
            string prefix = "Authentication__WorkloadAuthority__Grants__" + ordinal++ + "__";
            _ = authority.WithEnvironment(prefix + "GrantId", isolation + "-" + ordinal)
                .WithEnvironment(prefix + "Revision", "1").WithEnvironment(prefix + "ClientId", workload + "-fixture")
                .WithEnvironment(prefix + "Workload", workload).WithEnvironment(prefix + "Audience", audience)
                .WithEnvironment(prefix + "Surface", "service")
                .WithEnvironment(prefix + "ClientSecretSha256", Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(Value(key)))))
                .WithEnvironment(prefix + "AllowUnbound", "true")
                .WithEnvironment(prefix + "NotBefore", DateTimeOffset.UtcNow.AddMinutes(-1).ToString("O"))
                .WithEnvironment(prefix + "ExpiresAt", DateTimeOffset.UtcNow.AddHours(2).ToString("O"));
            for (int i = 0; i < operations.Length; i++) _ = authority.WithEnvironment(prefix + "Operations__" + i, operations[i]);
            return prefix;
        }
        Client(gateway, "EventStoreSecret"); Client(projects, "ProjectsSecret"); Client(tenants, "TenantsSecret");
        foreach (string domain in new[] { "projects", "tenants" })
            Grant("eventstore", "EventStoreSecret", domain, "domain-service:query", "domain-service:process",
                "domain-service:project", "domain-service:metadata", "domain-service:replay-state");
        Grant("projects", "ProjectsSecret", "eventstore", "eventstore:owner-authority-query");
        Grant("tenants", "TenantsSecret", "eventstore", "eventstore:command-submit", "eventstore:stream-read");
        string bootstrapSource = Grant("tenants", "TenantsSecret", "eventstore", "eventstore:stream-read");
        _ = authority.WithEnvironment(bootstrapSource + "AllowUnbound", "false")
            .WithEnvironment(bootstrapSource + "Bindings__eventstore:bound-tenant__0", "platform:global-administrators")
            .WithEnvironment(bootstrapSource + "Bindings__eventstore:bound-domain__0", "global-administrators");
        // Fresh writer activation requires a genuinely quiescent delivery inventory. The ordinary
        // compatibility profile's background workers can reacquire lifecycle leases after inline
        // delivery, including the completed bootstrap scope. This private lane uses the supported
        // recovery switch to retain request-path delivery while suppressing those background effects.
        _ = gateway.WithEnvironment("EventStore__Projections__Domains__projects__RefreshIntervalMs", "0")
            .WithEnvironment("EventStore__Projections__Domains__global-administrators__RefreshIntervalMs", "0")
            .WithEnvironment("EventStore__Projections__Domains__tenants__RefreshIntervalMs", "0")
            .WithEnvironment("EventStore__Projections__DefaultRefreshIntervalMs", "0")
            .WithEnvironment("EventStore__Projections__WorkersEnabled", "false")
            .WithEnvironment("Authentication__DaprInternal__AllowedCallers__0", "projects")
            .WithEnvironment("Authentication__DaprInternal__AllowedCallers__1", "tenants")
            .WithEnvironment("Authentication__BoundStreamRead__PublicKeys__projects", Value("OwnerPublicKey"))
            .WithEnvironment("Authentication__BoundStreamRead__AllowedDomains__projects", "projects")
            .WithEnvironment("Authentication__BoundStreamRead__PublicKeys__tenants", Value("TenantOwnerPublicKey"))
            .WithEnvironment("Authentication__BoundStreamRead__AllowedDomains__tenants", "tenants,global-administrators")
            .WithEnvironment("Authentication__BoundCommand__AllowedDomains__tenants", "global-administrators")
            .WithEnvironment("EventStore__DomainServices__Registrations__system|global-administrators|v1__AppId", "tenants")
            .WithEnvironment("EventStore__DomainServices__Registrations__system|global-administrators|v1__Domain", "global-administrators")
            .WaitFor(authority);
        _ = projects.WithEnvironment("Authentication__BoundStreamRead__PrivateKey", Secret("owner-key", "OwnerPrivateKey"));
        _ = tenants.WithEnvironment("Authentication__BoundStreamRead__PrivateKey", Secret("tenant-owner-key", "TenantOwnerPrivateKey"))
            .WithEnvironment("Tenants__BootstrapGlobalAdminEnabled", "true")
            .WithEnvironment("Tenants__BootstrapGlobalAdminUserId", Value("Browser:PrimaryActor"))
            .WithEnvironment("Tenants__BootstrapBoundWorkloadEnabled", "true")
            .WithEnvironment("EventStore__Authentication__Authority", Value("UserIssuer"))
            .WithEnvironment("EventStore__Authentication__TokenEndpoint", Value("Browser:TokenEndpoint"))
            .WithEnvironment("EventStore__Authentication__ClientId", "supported-read-bootstrap")
            .WithEnvironment("EventStore__Authentication__Username", "actor-1")
            .WithEnvironment("EventStore__Authentication__Password", Secret("bootstrap-password", "BootstrapPassword"));
        _ = ui.WithEnvironment("Authentication__OpenIdConnect__Authority", Value("UserIssuer"))
            .WithEnvironment("Authentication__OpenIdConnect__ClientId", "hexalith-projects-ui")
            .WithEnvironment("Authentication__OpenIdConnect__ClientSecret", Secret("ui", "Browser:ClientSecret"))
            .WithEnvironment("SSL_CERT_FILE", Value("TrustBundle"))
            .WithEnvironment("Logging__LogLevel__Microsoft.AspNetCore.Components.Server.Circuits", "Debug");
        _ = projects.WithReference(gateway).WithReference(tenants).WaitFor(authority);
        _ = workers.WithReference(gateway).WithReference(tenants);
        _ = projects.WithEnvironment("Projects__IsolatedLiveFixtures__Enabled", "true");
        _ = workers.WithEnvironment("Projects__IsolatedLiveFixtures__Enabled", "true");
        DevelopmentRouteCatalogInvocation[] Calls(params string[] methods) => methods.Select(method =>
            new DevelopmentRouteCatalogInvocation(gateway, method, ["POST"])).ToArray();
        DevelopmentRouteCatalogReceiver[] receivers =
        [
            new(gateway, [new(tenants, "api/v1/commands/bound/workload", ["POST"]),
                new(tenants, "api/v1/streams/read/workload", ["POST"]),
                new(projects, "api/v1/queries/owner-authority/workload", ["POST"]),
                new(projects, "api/v1/streams/read/workload", ["POST"]), new(projects, "api/v1/commands", ["POST"])]) { TechnicalHttp = true },
            new(tenants, Calls("process", "replay-state", "query", "project", "admin/operational-index-metadata")),
            new(projects, Calls("process", "query", "project", "project/v2", "project/rebuild/v1", "admin/operational-index-metadata")),
            new(workers, []),
        ];
        Dictionary<string, PackageOwnerLoadContext> ownerContexts = [];
        Assembly Load(string project, string assembly)
        {
            string path = project == "Hexalith.Projects.Server"
                ? new PrebuiltMetadata<global::Projects.Hexalith_Projects_Server>().ProjectPath
                : new PrebuiltMetadata<global::Projects.Hexalith_Tenants>().ProjectPath;
            string release = Path.Combine(Path.GetDirectoryName(path)!, "bin", "Release");
            if (!ownerContexts.TryGetValue(project, out PackageOwnerLoadContext? context))
            {
                context = new(Directory.GetFiles(release, Path.GetFileNameWithoutExtension(path) + ".dll", SearchOption.AllDirectories).Single());
                ownerContexts.Add(project, context);
            }
            return context.LoadOwner(Directory.GetFiles(release, assembly, SearchOption.AllDirectories).Single());
        }
        Assembly projectOwner = Load("Hexalith.Projects.Server", "Hexalith.Projects.Server.dll");
        Assembly tenantOwner = Load("Hexalith.Tenants", "Hexalith.Tenants.Contracts.dll");
        Assembly tenantAdapters = Load("Hexalith.Tenants", "Hexalith.Tenants.Server.dll");
        string statePath = Path.Combine(directory, "catalog-statestore.json");
        Write(directory, "catalog-statestore.json", new { apiVersion = "dapr.io/v1alpha1", kind = "Component", metadata = new { name = "statestore" },
            spec = new { type = "state.redis", version = "v1", metadata = new[] { new { name = "redisHost", value = Required(configuration, "Dapr:RedisHost") },
                new { name = "actorStateStore", value = "true" }, new { name = "keyPrefix", value = "none" } } } });
        var options = new DevelopmentRouteCatalogCompositionOptions(Path.Combine(directory, "catalog-custody"), "fixturecatalog",
            isolation, "fixture-v1", new Dictionary<string, string> { ["fixture-v1"] = Value("CatalogDigestKey") }, "fixture-v1");
        var catalog = builder.AddEventStoreDevelopmentRouteCatalog(gateway,
            [new(projects, projectOwner, projectOwner), new(tenants, tenantOwner, tenantAdapters)], receivers, statePath, options, isolation);
        builder.AddEventStoreDevelopmentSqliteStartupOrdering(tenants, gateway, projects, workers);
        _ = tenants.WithEnvironment("Tenants__BootstrapBoundWorkloadReceiptPath", Path.Combine(catalog.Directory, "tenants.bootstrap.json"));
        Write(directory, "catalog-plane.json", new { isolationId = isolation, directory = catalog.Directory, rootDigest = catalog.RootDigest,
            custodyDirectory = options.CustodyDirectory });
        return catalog;
    }

    private static string Required(IConfiguration configuration, string key)
        => !string.IsNullOrWhiteSpace(configuration[key]) ? configuration[key]! : throw new InvalidOperationException("Missing isolated fixture input: " + key);

    private static void EnsurePrivate(string path)
    {
        if (!File.Exists(path) || new FileInfo(path).LinkTarget is not null || (!OperatingSystem.IsWindows()
            && (File.GetUnixFileMode(path) & (UnixFileMode.GroupRead | UnixFileMode.GroupWrite | UnixFileMode.OtherRead | UnixFileMode.OtherWrite)) != 0))
            throw new InvalidOperationException("Isolated fixture inputs must be private regular files.");
    }

    private static void Write(string directory, string file, object value)
    {
        var options = new FileStreamOptions { Mode = FileMode.CreateNew, Access = FileAccess.Write, Share = FileShare.None };
        if (!OperatingSystem.IsWindows()) options.UnixCreateMode = UnixFileMode.UserRead | UnixFileMode.UserWrite;
        using var output = new FileStream(Path.Combine(directory, file), options);
        JsonSerializer.Serialize(output, value, JsonSerializerOptions.Web);
    }
}
