namespace Hexalith.Projects.Contracts.Queries;

using System.ComponentModel;
using System.Text.Json.Serialization;

using Hexalith.McpCli.Abstractions;

/// <summary>Opens one Project bound to the envelope target, without paging.</summary>
/// <param name="InspectDescriptiveMetadata">Requests separately authorized descriptive metadata.</param>
/// <param name="InspectQuarantined">Requests the narrowly scoped Administrator inspection of an unbound Active Project.</param>
[method: JsonConstructor]
[HexalithQuery("Read Project detail, lifecycle and reference health. Supply the Project identifier through --aggregate-id. Safe metadata is the default; descriptive metadata requires separate permission and a durable audit.",
    Name = "describe", Domain = "projects", WireType = QueryType,
    Example = """{}""")]
[Hexalith.EventStore.Contracts.Queries.QueryResultContract(typeof(GetProjectResponse), "projects", "Hexalith.Projects.Queries.GetProject.v1")]
public sealed record GetProjectQuery(
    [property: Description("Request descriptive fields; permission and durable inspection audit are required."), JsonPropertyName("inspectDescriptiveMetadata")]
    bool InspectDescriptiveMetadata = false,
    [property: Description("Request separately authorized Administrator inspection of an unbound Active Project."), JsonPropertyName("inspectQuarantined")]
    bool InspectQuarantined = false)
{
    /// <summary>Preserves the original constructor signature for existing consumers.</summary>
    /// <param name="InspectDescriptiveMetadata">Requests separately authorized descriptive metadata.</param>
    public GetProjectQuery(bool InspectDescriptiveMetadata) : this(InspectDescriptiveMetadata, false) { }

    /// <summary>Preserves the original positional deconstruction signature.</summary>
    /// <param name="InspectDescriptiveMetadata">The descriptive inspection selection.</param>
    public void Deconstruct(out bool InspectDescriptiveMetadata) => InspectDescriptiveMetadata = this.InspectDescriptiveMetadata;

    /// <summary>The supported query discriminator.</summary>
    public const string QueryType = "Hexalith.Projects.Queries.GetProject.v1";
}
