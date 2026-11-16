namespace Hexalith.Projects.Integration.Tests;

using System.Net;

using Hexalith.Projects.Contracts.Models;
using Hexalith.Projects.Contracts.Queries;
using Hexalith.Projects.Contracts.Ui;

using Shouldly;
using Xunit;

/// <summary>Keeps eventual setup observations separate from every unchanged product assertion and baseline.</summary>
public sealed class PackageReadSetupReadinessTests
{
    /// <summary>A known cold dependency must reach the exact Complete seeded view.</summary>
    [Fact]
    public async Task KnownUnavailableRequiresExactCompleteRows()
    {
        int calls = 0;
        await PackageReadSetupReadiness.WaitAsync(_ => Task.FromResult((HttpStatusCode.OK, (ProjectListPage?)(++calls == 1 ? Unavailable() : Complete()))),
            ["project-a", "project-b"], TimeSpan.FromSeconds(2), TimeSpan.Zero, TestContext.Current.CancellationToken);
        calls.ShouldBe(2);
    }

    /// <summary>A wrong Complete result is a product error and cannot be retried into acceptance.</summary>
    [Fact]
    public async Task WrongCompleteRowsAreNeverRetried()
    {
        int calls = 0;
        InvalidOperationException failure = await Should.ThrowAsync<InvalidOperationException>(() => PackageReadSetupReadiness.WaitAsync(_ =>
        {
            calls++;
            return Task.FromResult((HttpStatusCode.OK, (ProjectListPage?)(Complete() with { Items = [] })));
        }, ["project-a", "project-b"], TimeSpan.FromSeconds(2), TimeSpan.Zero, TestContext.Current.CancellationToken));
        calls.ShouldBe(1);
        failure.Message.ShouldContain("exact expected rows");
    }

    /// <summary>Unexpected unavailable evidence is a hard failure with safe last-response diagnostics.</summary>
    [Fact]
    public async Task UnexpectedUnavailableIsNeverRetried()
    {
        int calls = 0;
        InvalidOperationException failure = await Should.ThrowAsync<InvalidOperationException>(() => PackageReadSetupReadiness.WaitAsync(_ =>
        {
            calls++;
            return Task.FromResult((HttpStatusCode.OK, (ProjectListPage?)Unavailable("private-component", "private-reason")));
        }, ["project-a", "project-b"], TimeSpan.FromSeconds(2), TimeSpan.Zero, TestContext.Current.CancellationToken));
        calls.ShouldBe(1);
        failure.Message.ShouldContain("unexpected unavailable");
        failure.Message.ShouldNotContain("private-component");
        failure.Message.ShouldNotContain("private-reason");
    }

    /// <summary>Persistent known Unavailable remains red and retains the safe final reason and snapshot component.</summary>
    [Fact]
    public async Task PersistentUnavailableTimesOutWithLastSafeObservation()
    {
        int calls = 0;
        InvalidOperationException failure = await Should.ThrowAsync<InvalidOperationException>(() => PackageReadSetupReadiness.WaitAsync(_ =>
        {
            calls++;
            return Task.FromResult((HttpStatusCode.OK, (ProjectListPage?)Unavailable()));
        }, ["project-a", "project-b"], TimeSpan.FromMilliseconds(50), TimeSpan.FromMilliseconds(1), TestContext.Current.CancellationToken));
        calls.ShouldBeGreaterThan(1);
        failure.Message.ShouldContain("setup budget");
        failure.Message.ShouldContain("FolderVisibility");
        failure.Message.ShouldContain("FolderUnavailable");
    }

    /// <summary>Authentication failure is not a readiness race.</summary>
    [Fact]
    public async Task AuthenticationRefusalIsNeverRetried()
    {
        int calls = 0;
        await Should.ThrowAsync<InvalidOperationException>(() => PackageReadSetupReadiness.WaitAsync(_ =>
        {
            calls++;
            return Task.FromResult((HttpStatusCode.Unauthorized, (ProjectListPage?)null));
        }, ["project-a", "project-b"], TimeSpan.FromSeconds(2), TimeSpan.Zero, TestContext.Current.CancellationToken));
        calls.ShouldBe(1);
    }

    /// <summary>A child that ignores cancellation cannot publish a late Complete result past setup's complete deadline.</summary>
    [Fact]
    public async Task LateCompleteCannotOutliveSetupBudget()
    {
        var reply = new TaskCompletionSource<(HttpStatusCode, ProjectListPage?)>();
        try
        {
            await Should.ThrowAsync<InvalidOperationException>(() => PackageReadSetupReadiness.WaitAsync(_ => reply.Task,
                ["project-a", "project-b"], TimeSpan.FromMilliseconds(10), TimeSpan.Zero, TestContext.Current.CancellationToken));
        }
        finally { reply.SetResult((HttpStatusCode.OK, Complete())); }
    }

    private static ProjectListPage Complete()
    {
        AdmissionSnapshot snapshot = new(AdmissionResponseState.Complete, DateTimeOffset.UtcNow, 2,
            [new("Project", true, EvidenceFreshnessState.Current, "Current")], []);
        return new([new("project-a", null, ProjectLifecycle.Active, ReferenceState.Included, snapshot),
            new("project-b", null, ProjectLifecycle.Active, ReferenceState.Included, snapshot)], null, false, snapshot);
    }

    private static ProjectListPage Unavailable(string component = "FolderVisibility", string reason = "FolderUnavailable")
        => new([], null, false, new(AdmissionResponseState.Unavailable, DateTimeOffset.UtcNow, 0,
            [new(component, false, EvidenceFreshnessState.Unavailable, reason)], []));
}
