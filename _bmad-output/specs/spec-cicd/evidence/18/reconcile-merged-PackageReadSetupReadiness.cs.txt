namespace Hexalith.Projects.Integration.Tests;

using System.Net;
using System.Text.Json;

using Hexalith.Projects.Contracts.Queries;
using Hexalith.Projects.Contracts.Ui;
using Hexalith.Projects.Contracts.Models;

/// <summary>Establishes exact seeded admission before any product state, audit or cursor baseline is captured.</summary>
internal static class PackageReadSetupReadiness
{
    internal static async Task WaitAsync(Func<CancellationToken, Task<(HttpStatusCode Status, ProjectListPage? Page)>> query,
        string[] expected, TimeSpan timeout, TimeSpan interval, CancellationToken cancellation)
    {
        using CancellationTokenSource budget = CancellationTokenSource.CreateLinkedTokenSource(cancellation);
        budget.CancelAfter(timeout);
        string last = "no-response";
        try
        {
            while (true)
            {
                var (status, page) = await query(budget.Token).WaitAsync(budget.Token).ConfigureAwait(false);
                budget.Token.ThrowIfCancellationRequested();
                last = page is null ? "httpStatus=" + (int)status
                    : PackageReadFixture.CreateCursorControlEvidence(page).GetRawText();
                if (status != HttpStatusCode.OK || page is null)
                    throw new InvalidOperationException("Seed read admission was unexpectedly refused: " + last);
                if (page.Snapshot.ResponseState == AdmissionResponseState.Complete)
                {
                    if (!page.Items.Select(item => item.ProjectId).SequenceEqual(expected, StringComparer.Ordinal)
                        || page.HasMore || page.Cursor is not null || page.Snapshot.AsOf == default)
                        throw new InvalidOperationException("Seed read admission differed from the exact expected rows: " + last);
                    Console.WriteLine("[package-native] setup-readiness=" + last);
                    return;
                }
                if (page.Snapshot.ResponseState != AdmissionResponseState.Unavailable || page.Items.Count != 0
                    || page.HasMore || page.Cursor is not null || page.Snapshot.AsOf == default || page.Snapshot.ProjectVersion != 0
                    || page.Snapshot.Components.Count != 1 || !ExpectedUnavailable(page.Snapshot.Components[0]))
                    throw new InvalidOperationException("Seed read admission returned an unexpected unavailable shape: " + last);
                await Task.Delay(interval, budget.Token).ConfigureAwait(false);
            }
        }
        catch (OperationCanceledException) when (!cancellation.IsCancellationRequested)
        {
            Console.Error.WriteLine("[package-native] setup-readiness-timeout last=" + last);
            throw new InvalidOperationException("Seed read admission did not become Complete within its setup budget; last=" + last);
        }
    }

    private static bool ExpectedUnavailable(AdmissionComponent component)
        => !component.Included && component.Freshness is EvidenceFreshnessState.Stale or EvidenceFreshnessState.Unavailable
            && (component.Name, component.Reason) is ("Enumeration", "ProjectionUnavailable")
                or ("Authorization", "AuthorizationUnavailable") or ("FolderVisibility", "FolderUnavailable");
}
