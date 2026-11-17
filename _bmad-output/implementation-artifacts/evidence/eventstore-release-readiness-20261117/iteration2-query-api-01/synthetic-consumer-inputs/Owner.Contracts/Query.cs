using Hexalith.EventStore.Contracts.Queries;
namespace Owner;
[QueryResultContract(typeof(Result), "owner", "Owner.Queries.Read.v1")]
public sealed record Query(string OpaqueId);
