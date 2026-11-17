using Hexalith.EventStore.Contracts.Queries;
namespace Owner;
public sealed record Result(string OpaqueId);
[QueryResultContract(typeof(Result), "owner", "Owner.Queries.Read.v1")]
public sealed record Query(string OpaqueId);
