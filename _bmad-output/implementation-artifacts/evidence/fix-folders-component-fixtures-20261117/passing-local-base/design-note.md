# Restore content identity for signed packages

NuGet's restore `sha512` is a canonical package content identity. For signed
archives it differs from SHA-512 of the complete signed ZIP. The first complete
Server correction run retained 1,461 executed tests: all 10 negative security
cases passed, and the success case correctly refused the mistaken raw-archive
comparison. Cleanup observed zero containers and zero private paths.

The correction uses `NuGet.Packaging.PackageArchiveReader.GetContentHash` from
the repository's pinned .NET SDK, with its Common, Versioning and Frameworks
runtime dependencies. This recomputes SHA-512 from archive records, adjusting
signature records exactly as NuGet does; it does not trust
`.nupkg.metadata.contentHash`. Raw archive SHA-512 is separately compared with
the restored `.nupkg.sha512` sidecar and retained as `archiveSha512`. Restored
assets are SHA-256-bound into evaluated assembly metadata. Dependency identity,
manifest identity, runtime entry, loaded payload SHA-256 and MVID must also agree.
The genuine signed xUnit package control recomputes its restore identity and
rejects changed payload bytes. The real SDK success case covers signed EventStore
packages.

Primary implementation sources:

- [NuGet PackageArchiveReader](https://github.com/NuGet/NuGet.Client/blob/dev/src/NuGet.Core/NuGet.Packaging/PackageArchiveReader.cs)
- [NuGet canonical signed archive hashing](https://source.dot.net/NuGet.Packaging/Signing/Archive/SignedPackageArchiveUtility.cs.html)
- [NuGet extraction hash recording](https://github.com/NuGet/NuGet.Client/blob/dev/src/NuGet.Core/NuGet.Packaging/PackageExtractor.cs)

The API was inspected locally with the dotnet-inspect skill using:
`dnx dotnet-inspect -y -- member NuGet.Packaging.PackageArchiveReader --library /home/administrator/.dotnet/sdk/11.0.100/NuGet.Packaging.dll -S Methods --table -n 45`.
No frozen intent was changed.
