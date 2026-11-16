namespace Hexalith.Projects.Integration.Tests;

using System.Diagnostics;

using Shouldly;

using Xunit;

/// <summary>Requires genuine pre-backup quiescence without retrying unrelated failures.</summary>
public sealed class PackageFreshCutoverTests
{
    /// <summary>A transient inventory turnover restarts observation and still requires stable actual state.</summary>
    [Fact]
    public async Task InventoryTurnoverWaitsForStableState()
    {
        int reads = 0;
        Dictionary<string, PackageReadStateSnapshot> expected = State("1");
        Task<Dictionary<string, PackageReadStateSnapshot>> Read(CancellationToken _)
        {
            reads++;
            if (reads == 1) throw new PackageReadFixture.FreshCutoverInventoryChangedException();
            return Task.FromResult(expected);
        }
        using CancellationTokenSource timeout = new(TimeSpan.FromSeconds(10));
        Stopwatch elapsed = Stopwatch.StartNew();
        Dictionary<string, PackageReadStateSnapshot> result = await PackageReadFixture.AwaitFreshCutoverQuiescenceAsync(
            Read, _ => true, timeout.Token).ConfigureAwait(true);
        result.ShouldBeSameAs(expected);
        reads.ShouldBeGreaterThan(2);
        elapsed.Elapsed.ShouldBeGreaterThanOrEqualTo(TimeSpan.FromSeconds(2));
    }

    /// <summary>An ETag change restarts the complete stability interval.</summary>
    [Fact]
    public async Task ChangedStateRestartsStabilityWindow()
    {
        Stopwatch changed = new();
        int reads = 0;
        Task<Dictionary<string, PackageReadStateSnapshot>> Read(CancellationToken _)
        {
            reads++;
            if (reads == 4) changed.Start();
            return Task.FromResult(State(reads < 4 ? "1" : "2"));
        }
        using CancellationTokenSource timeout = new(TimeSpan.FromSeconds(10));
        Dictionary<string, PackageReadStateSnapshot> result = await PackageReadFixture.AwaitFreshCutoverQuiescenceAsync(
            Read, _ => true, timeout.Token).ConfigureAwait(true);
        result["key"].ETag.ShouldBe("2");
        changed.Elapsed.ShouldBeGreaterThanOrEqualTo(TimeSpan.FromSeconds(2));
    }

    /// <summary>Interrupted quiescence cannot count an earlier interval toward readiness.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task InterruptedStableInventoryRequiresANewWindow(bool turnover)
    {
        int reads = 0;
        Stopwatch resumed = new();
        Task<Dictionary<string, PackageReadStateSnapshot>> Read(CancellationToken _)
        {
            reads++;
            if (reads == 4 && turnover) throw new PackageReadFixture.FreshCutoverInventoryChangedException();
            if (reads == 5) resumed.Start();
            return Task.FromResult(State("1"));
        }
        using CancellationTokenSource timeout = new(TimeSpan.FromSeconds(10));
        await PackageReadFixture.AwaitFreshCutoverQuiescenceAsync(Read, _ => reads != 4, timeout.Token).ConfigureAwait(true);
        resumed.Elapsed.ShouldBeGreaterThanOrEqualTo(TimeSpan.FromSeconds(2));
    }

    /// <summary>Persistent work or turnover cannot escape the inherited startup deadline.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task UnsettledInventoryHonorsCancellation(bool turnover)
    {
        Task<Dictionary<string, PackageReadStateSnapshot>> Read(CancellationToken _)
            => turnover ? throw new PackageReadFixture.FreshCutoverInventoryChangedException() : Task.FromResult(State("1"));
        using CancellationTokenSource timeout = new(TimeSpan.FromMilliseconds(150));
        await Should.ThrowAsync<OperationCanceledException>(() => PackageReadFixture.AwaitFreshCutoverQuiescenceAsync(
            Read, _ => false, timeout.Token));
    }

    /// <summary>Malformed inventory and failed source assertions must fail on their first observation.</summary>
    [Fact]
    public async Task OtherFailuresPropagateWithoutRetry()
    {
        int reads = 0;
        InvalidOperationException expected = new("Malformed inventory");
        Task<Dictionary<string, PackageReadStateSnapshot>> Read(CancellationToken _)
        {
            reads++;
            throw expected;
        }
        Exception actual = await Should.ThrowAsync<InvalidOperationException>(() => PackageReadFixture.AwaitFreshCutoverQuiescenceAsync(
            Read, _ => true, CancellationToken.None));
        actual.ShouldBeSameAs(expected);
        reads.ShouldBe(1);
    }

    private static Dictionary<string, PackageReadStateSnapshot> State(string etag)
        => new(StringComparer.Ordinal) { ["key"] = new("key", [1, 2, 3], etag) };
}
