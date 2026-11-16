namespace Hexalith.Projects.Integration.Tests;

using Hexalith.Projects.PackageFixtures;
using Shouldly;
using Xunit;

/// <summary>Distinguishes a retained assertion result from failure to release the preceding runtime.</summary>
public sealed class PackagePhaseSequenceTests
{
    /// <summary>The next allocation follows successful disposal while the original assertion remains red.</summary>
    [Fact]
    public async Task DisposedAssertionFailureContinuesAndIsRetained()
    {
        List<string> events = [];
        IReadOnlyList<string> failures = await PackagePhaseSequence.RunAsync(new[] { 1, 2 }, async phase =>
        {
            events.Add("allocate:" + phase);
            await using var cleanup = new ControlledCleanup(events, phase, fail: false).ConfigureAwait(true);
            await Task.Yield();
            return phase == 1 ? "main:AssertionFailure" : null;
        });
        failures.ShouldBe(["main:AssertionFailure"]);
        events.ShouldBe(["allocate:1", "cleanup:1", "allocate:2", "cleanup:2"]);
    }

    /// <summary>A failed disposal prevents a phase from returning its assertion result or allocating a later runtime.</summary>
    [Fact]
    public async Task CleanupFailureHaltsLaterAllocation()
    {
        List<string> events = [];
        IOException failure = await Should.ThrowAsync<IOException>(() => PackagePhaseSequence.RunAsync(new[] { 1, 2 }, async phase =>
        {
            events.Add("allocate:" + phase);
            await using var cleanup = new ControlledCleanup(events, phase, fail: true).ConfigureAwait(true);
            await Task.Yield();
            return "main:AssertionFailure";
        }));
        failure.Message.ShouldBe("owned cleanup failed");
        events.ShouldBe(["allocate:1", "cleanup:1"]);
    }

    private sealed class ControlledCleanup(List<string> events, int phase, bool fail) : IAsyncDisposable
    {
        public ValueTask DisposeAsync()
        {
            events.Add("cleanup:" + phase);
            return fail ? ValueTask.FromException(new IOException("owned cleanup failed")) : ValueTask.CompletedTask;
        }
    }
}
