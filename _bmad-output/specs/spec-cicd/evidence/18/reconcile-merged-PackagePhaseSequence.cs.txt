namespace Hexalith.Projects.PackageFixtures;

/// <summary>Continues after fully disposed assertion failures; cleanup/infrastructure exceptions halt allocation.</summary>
internal static class PackagePhaseSequence
{
    internal static async Task<IReadOnlyList<string>> RunAsync<T>(IEnumerable<T> selections, Func<T, Task<string?>> phase)
    {
        List<string> failures = [];
        foreach (T selection in selections)
        {
            // A result returns only after the phase has completely released its owned lifetime.
            // A fault has not established safe next allocation and must never be caught here.
            string? failure = await phase(selection).ConfigureAwait(false);
            if (failure is not null) failures.Add(failure);
        }
        return failures;
    }
}
