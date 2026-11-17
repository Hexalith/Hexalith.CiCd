using System.Reflection;
using System.Text.Json;

using Hexalith.EventStore.Client.Aggregates;
using Hexalith.EventStore.Client.Handlers;
using Hexalith.EventStore.DomainService;
using Hexalith.EventStore.Server.Configuration;
using Hexalith.Tenants.Server.Aggregates;

using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;

// Scratch-only capability observation. These assertions establish missing capabilities,
// never a snapshot qualification, parity pass, registry entry, or product acceptance.
WebApplicationBuilder domainBuilder = WebApplication.CreateBuilder(new WebApplicationOptions { Args = [] });
domainBuilder.AddEventStoreDomainService(typeof(TenantAggregate).Assembly);
using ServiceProvider domain = domainBuilder.Services.BuildServiceProvider();
IAsyncDomainProcessor processor = domain.GetRequiredKeyedService<IAsyncDomainProcessor>("tenants");
var actorServices = new ServiceCollection();
actorServices.AddLogging();
actorServices.AddDaprClient();
actorServices.AddEventStoreServer(domainBuilder.Configuration);
using ServiceProvider actor = actorServices.BuildServiceProvider();

var facts = new Dictionary<string, bool>
{
    ["actualTenantAggregateSelected"] = processor.GetType() == typeof(TenantAggregate),
    ["aggregateSupportsOrdinaryAsyncCommands"] = processor is IAsyncDomainProcessor,
    ["aggregateSupportsExistingReplay"] = processor is IAggregateReplay && processor is IAsyncAggregateReplay,
    ["domainAsyncReplayRegistered"] = domain.GetKeyedServices<IAsyncAggregateReplay>("tenants").Any(),
    ["aggregateLacksFoldedSnapshotProcessor"] = processor is not IAsyncFoldedSnapshotProcessor,
    ["domainRegistryAbsent"] = domain.GetService<FoldedSnapshotQualificationRegistry>() is null,
    ["boundedDomainProducerAbsent"] = domain.GetKeyedService<BoundedV1DomainResultProducer>("tenants") is null
        && domain.GetService<BoundedV1DomainResultProducer>() is null,
    ["actorRegistryAbsent"] = actor.GetService<FoldedSnapshotQualificationRegistry>() is null,
    ["actualActorOptionsRemain100"] = actor.GetRequiredService<IOptions<SnapshotOptions>>().Value.DefaultInterval == 100,
    ["typedProcessorBaseHasFoldedContract"] = typeof(IAsyncFoldedSnapshotProcessor).IsAssignableFrom(typeof(DomainProcessorBase<TenantState>)),
    ["typedProcessorBaseLacksAggregateReplayContract"] = !typeof(IAggregateReplay).IsAssignableFrom(typeof(DomainProcessorBase<TenantState>)),
};
Console.WriteLine(JsonSerializer.Serialize(new
{
    purpose = "in-process compatibility-gap observation; not parity or performance qualification",
    facts,
    observed = facts.Count,
    matched = facts.Count(fact => fact.Value),
    failed = facts.Count(fact => !fact.Value),
    skipped = 0,
    qualified = false,
    productModified = false,
    nativeRuntimeStarted = false,
    stateProperties = typeof(TenantState).GetProperties().Select(property => property.Name).Order().ToArray(),
    applyEventTypes = typeof(TenantState).GetMethods().Where(method => method.Name == "Apply")
        .Select(method => method.GetParameters().Single().ParameterType.FullName).Order().ToArray(),
    assemblies = new[] { typeof(TenantAggregate).Assembly, typeof(IAsyncDomainProcessor).Assembly,
            typeof(FoldedSnapshotQualification).Assembly, typeof(SnapshotOptions).Assembly }
        .Select(assembly => new { name = assembly.GetName().Name,
            version = assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>()?.InformationalVersion }).ToArray(),
}));
return facts.Values.All(value => value) ? 0 : 1;
