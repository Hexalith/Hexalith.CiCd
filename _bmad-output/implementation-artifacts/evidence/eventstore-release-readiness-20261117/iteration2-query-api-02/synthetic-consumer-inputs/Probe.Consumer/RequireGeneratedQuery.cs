using Hexalith.EventStore.Client.Gateway;
using Probe.Consumer.Generated;
namespace Probe.Consumer;
public static class RequireGeneratedQuery
{
    public static Task<EventStoreQueryResult<Owner.Result>> Compile(IEventStoreGatewayClient gateway)
        => gateway.QueryAsync("tenant", "opaque-target", new Owner.Query("opaque-query"));
}
