namespace Hexalith.Projects.Integration.Tests;

using Hexalith.Projects.PackageFixtures;
using Shouldly;
using Xunit;

/// <summary>Requires Docker's actual single loopback binding rather than an earlier free-port observation.</summary>
public sealed class PackagePublishedBindingTests
{
    /// <summary>Only the requested owned container port supplies the selected origin.</summary>
    [Fact]
    public void AssignedLoopbackPortIsSelectedExactly()
    {
        FixtureScratch.PublishedPort("{\"8443/tcp\":[{\"HostIp\":\"127.0.0.1\",\"HostPort\":\"43190\"}],\"6379/tcp\":null}", "8443/tcp").ShouldBe(43190);
    }

    /// <summary>Absent, ambiguous, public or nonassigned bindings cannot establish fixture trust.</summary>
    [Theory]
    [InlineData("{}")]
    [InlineData("{\"8443/tcp\":null}")]
    [InlineData("{\"8443/tcp\":[]}")]
    [InlineData("{\"8443/tcp\":[{\"HostIp\":\"0.0.0.0\",\"HostPort\":\"43190\"}]}")]
    [InlineData("{\"8443/tcp\":[{\"HostIp\":\"127.0.0.1\",\"HostPort\":\"0\"}]}")]
    [InlineData("{\"8443/tcp\":[{\"HostIp\":\"127.0.0.1\",\"HostPort\":\"65536\"}]}")]
    [InlineData("{\"8443/tcp\":[{\"HostIp\":\"127.0.0.1\",\"HostPort\":\"43190\"},{\"HostIp\":\"127.0.0.1\",\"HostPort\":\"43191\"}]}")]
    public void UnsafeOrUnassignedBindingIsRefused(string binding)
    {
        Should.Throw<InvalidOperationException>(() => FixtureScratch.PublishedPort(binding, "8443/tcp"));
    }

    /// <summary>An unowned identity is refused before Docker inspection, independent of any apparent port.</summary>
    [Fact]
    public async Task UnownedContainerCannotSupplyAnIssuerBinding()
    {
        FixtureScratch scratch = new(true, (_, _) => throw new InvalidOperationException("Unexpected Docker access"));
        await using var cleanup = scratch.ConfigureAwait(true);
        await Should.ThrowAsync<InvalidOperationException>(() => scratch.OwnedPublishedPortAsync(new string('a', 64), "8443/tcp", TestContext.Current.CancellationToken));
    }
}
