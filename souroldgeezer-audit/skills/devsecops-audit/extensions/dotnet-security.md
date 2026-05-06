# .NET Security Extension

Load this routing card when audit targets include `*.csproj`, C# sources under
`api/`, `app/`, `shared/`, or `tests/`, or `appsettings*.json`.

Full rules: [../../../docs/security-reference/devsecops-extensions/dotnet-security.md](../../../docs/security-reference/devsecops-extensions/dotnet-security.md)

Adds `dns.*` findings and positives for ASP.NET Core security posture,
authentication/authorization, CORS, cookie policy, secret handling, logging,
dependency freshness, XML/SSRF/deserialization paths, and security tests. Apply
the full rule file before emitting .NET codes or carve-outs.
