# Gold standard example

Source type: security advisory (CVE remediation on a Windows/IIS hosted .NET API).
Use this for tone, density, and structure. Do not copy its content into unrelated tickets.

```
Summary
Upgrade .NET 8 ASP.NET Core Hosting Bundle on Staging & Production - remediate CVE-2025-55315

Description
Background
Microsoft published ASP.NET Core / .NET security advisories including CVE-2025-55315 (HTTP request smuggling / security feature bypass in Kestrel, Critical). RadicalHealth API targets .NET 8 (`net8.0`) and runs as a framework-dependent IIS app, so the Windows Server Hosting runtime on each server determines exposure.

Current versions (before)
* Staging: `Microsoft.AspNetCore.App` / `Microsoft.NETCore.App` 8.0.19 -> Affected (CVE-2025-55315 fixed in 8.0.21+)
* Production: 8.0.27 -> Not affected by CVE-2025-55315; still below later servicing patches

Other CVEs reviewed
* CVE-2026-40372 - Not applicable (.NET 10 only)
* CVE-2026-114148 - Not applicable (Linux tarball ownership; we use Windows Hosting Bundle)
* CVE-2026-45591 - SignalR/Blazor DoS; we do not use SignalR/Blazor; cleared by 8.0.28+ / 8.0.33

Action taken
1. Install Microsoft .NET 8.0.33 - Windows Server Hosting on Staging and Production
2. Run `iisreset`
3. Verify with `dotnet --list-runtimes`

After
* Staging & Production: AspNetCore / NETCore App 8.0.33

Out of scope
* Application code changes
* CI/CD pipeline changes (deploy is framework-dependent; fix is server runtime only)
* NuGet package bump in `Directory.Packages.props` (optional follow-up)

Acceptance criteria
* [ ] Staging shows `Microsoft.AspNetCore.App 8.0.33` (or higher 8.0.x) via `dotnet --list-runtimes`
* [ ] Production shows `Microsoft.AspNetCore.App 8.0.33` (or higher 8.0.x)
* [ ] IIS restarted successfully on both environments
* [ ] API smoke test passes (login / basic endpoint) on Staging and Production
* [ ] No application redeploy required for this CVE fix
```

## Why this works

- Summary has verb, target, environments, and driver in one line.
- "Current versions" and "After" are parallel, so the delta is obvious.
- "Other CVEs reviewed" shows what was ruled out, which prevents repeat investigation.
- "Out of scope" pre-empts scope creep.
- Each acceptance criterion is verifiable, and each environment has its own.
- Negative criterion (no redeploy) closes a common assumption.
