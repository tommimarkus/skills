# Extension — Blazor WebAssembly

**Applies to:** Blazor WebAssembly components and their host. The reference's principles, decisions, primitives, patterns, gotchas, and checklist all apply unchanged; this extension adds the stack-specific surface.

## Hosting models covered

Two hosting models ship WebAssembly components in 2026 and this extension covers both:

- **Standalone Blazor WebAssembly** — `blazorwasm` template, SDK `Microsoft.NET.Sdk.BlazorWebAssembly`, served as static files; no server and no prerendering; render mode is **not** used and `@rendermode` directives don't apply — every component runs on the client after the WASM runtime boots.
- **Blazor Web App (.NET 8+) with a `.Client` project** — `blazor` template, server project is `Microsoft.NET.Sdk.Web`; WebAssembly components live in a separate `.Client` project; render modes (`InteractiveWebAssembly`, `InteractiveServer`, `InteractiveAuto`, static SSR) **are** used and selected per component via `@rendermode`.

Rules in this extension are tagged `[Standalone]`, `[BWA]`, or `[Both]` where the distinction matters. When the distinction doesn't matter (CSS isolation, logical properties, focus management, form-control attributes), no tag is used.

**Detection signals:**

- Any `*.razor`, `*.razor.css`, or `*.razor.cs` file in the target.
- `*.csproj` with `<Project Sdk="Microsoft.NET.Sdk.BlazorWebAssembly">` → `[Standalone]`.
- `Program.cs` using `WebAssemblyHostBuilder.CreateDefault(args)` and `builder.RootComponents.Add<App>("#app")` → `[Standalone]`.
- `wwwroot/index.html` referencing `blazor.webassembly.js` → `[Standalone]`.
- A `.Client` project reference and a server project referencing `blazor.web.js` with `AddInteractiveWebAssemblyComponents()` / `AddInteractiveWebAssemblyRenderMode()` → `[BWA]`.
- `@rendermode` directives on components or `<Routes @rendermode="...">` on `App.razor` → `[BWA]`.

**Applies to reference sections:** §2.3 (component-scoped adaptation), §3.2 (container queries), §3.6 (touch/hover), §3.8 (sticky/focus), §3.9 (logical properties), §3.11–3.13 (loading, network), §3.14 (animation/INP), §3.16 (focus management), §4 (primitives), §4.5 (baseline boilerplate — as `wwwroot/index.html`), §5 (patterns — rewritten as Razor components), §6 (gotchas), §7 (checklist — particularly the Performance bucket, where WASM boot interacts with LCP).

**Complementary skills:** `devsecops-audit` dotnet extension owns C# security review of Blazor code; this extension owns the *responsive / a11y / i18n / perf* surface only.

## Project assimilation

The core SKILL.md runs a framework-agnostic discovery pass before this extension loads. This section covers the Blazor-specific detection the core pass delegates here.

**Direction follows the core rule: the Blazor project is assimilated to the reference, not vice versa.** Reuse of Blazor library primitives (MudBlazor / FluentUI Blazor / Radzen / Blazorise) is conditional on each primitive actually satisfying the reference rule it would replace — a library's "Dialog" component that lacks focus-trap, `Esc` handling, or focus restoration is not a substitute for §5.8, and gets flagged rather than reused.

### Blazor-specific discovery

- **`Program.cs`** — detect the host: `WebAssemblyHostBuilder.CreateDefault(args)` → `[Standalone]`; a server project calling `AddInteractiveWebAssemblyComponents()` / `AddInteractiveWebAssemblyRenderMode()` alongside a sibling `.Client` project → `[BWA]`. Record services added, `builder.RootComponents.Add<App>("#app")` call, and any `.Services` registrations that affect theming / navigation / JS interop.
- **`App.razor` / `Components/App.razor`** — detect the declared default `@rendermode` on `<Routes>` and any `<HeadOutlet>` render mode. This is the app-level default every page inherits unless overridden.
- **`MainLayout.razor`** and its `.razor.css` — detect the existing layout shell. Does it already have `<main id="main" tabindex="-1">`, a skip link, landmark structure (`<header>`, `<nav>`, `<aside>`, `<footer>`), a `NavigationManager.LocationChanged` subscription? If yes, extend it; don't introduce a parallel layout.
- **Isolated stylesheets (`*.razor.css`)** — grep for logical vs physical properties to assess the baseline. Leaked physical properties are a project-level `blazor.HC-1` count — flag in the assimilation footer.
- **Component libraries** via `.csproj` / `<PackageReference>`:

  | Package | Candidate primitives for | Reuse condition |
  |---|---|---|
  | `MudBlazor` | `MudDialog` (§5.8), `MudTooltip` (§5.11), `MudMenu`, `MudSnackbar`, `MudTextField` | Each instance verified: focus-trap + `Esc` + focus restore for dialog; `aria-describedby` wiring for tooltip; `AdditionalAttributes` splatting for form fields. Theme-aware and a11y-opinionated by default but theme overrides can break contrast — re-check SC 1.4.3 / 1.4.11 against the project's MudTheme. |
  | `Microsoft.FluentUI.AspNetCore.Components` | `FluentDialog`, `FluentTooltip`, `FluentMenu`, `FluentTextField` | Verify focus behaviour on the component version in use. |
  | `Radzen.Blazor` | `RadzenDialog`, `RadzenTooltip`, `RadzenDropDown` | **Verify keyboard flow** (focus-trap, `Esc`, focus restoration) before reusing — some versions historically shipped with gaps. If any fails, flag as legacy debt and fall back to the reference pattern. |
  | `Blazorise` | `Modal`, `Tooltip`, `Dropdown` | Verify per-instance. |
  | `AntDesign.Blazor` | `Modal`, `Tooltip`, `Dropdown` | Verify per-instance. |

- **Existing JS interop modules (`wwwroot/js/*.js` / `*.mjs`)** — grep for existing `matchMedia` / `visualViewport` / Web Vitals / dialog-open helpers. One module per *concern* is idiomatic; one per consumer is not. Extend existing modules; do not add `prefers.js`, `viewport.js`, `vitals.js`, `dialog.js` in parallel if any of them already exist.
- **Host HTML** — `wwwroot/index.html` (`[Standalone]`) or `App.razor` `<HeadContent>` (`[BWA]`). Check for the §4.5 baseline-boilerplate elements.
- **Trimming / AOT** — read the WASM `.csproj` for `PublishTrimmed`, `RunAOTCompilation`, `BlazorWebAssemblyLazyLoad` entries, and any `TrimmerRootAssembly` / `<DynamicallyAccessedMembers>`-style annotations. Records what the project has already committed to on bundle-size strategy.
- **CSS isolation bundle output location** — note whether the project relies on `{AssemblyName}.styles.css` (default) or has configured `DisableScopedCssBundling` / `CssScope` overrides; generated styles must match the chosen convention.

### Mapping reference rules to Blazor idioms

Every mapping here is **conditional on the target's compliance with the reference rule**. If the library primitive fails the rule, the mapping inverts — flag and fall back to the reference pattern, don't reuse.

- §5.8 `<dialog>` → reuse a compliant library dialog (per table). If the library's dialog fails focus-trap / `Esc` / focus-restore, flag as legacy debt and use `blazor.PAT-razor-dialog`.
- §5.11 `popover` → reuse a compliant library tooltip/menu. Otherwise use the native `popover` attribute via a JS-interop helper.
- §3.16 focus-on-navigate → extend `MainLayout.razor`'s existing `LocationChanged`/`OnAfterRenderAsync` if it already restores focus to `<main>`; if no focus restoration exists, add it per `blazor.PAT-focus-on-navigate` (don't quietly omit it because the project has never had it).
- §4 interop (`matchMedia` / `visualViewport` / Web Vitals) → extend any existing JS module that covers the concern, regardless of style. This is the one case where "match existing convention" is fair: interop modules are internal plumbing and adding parallel ones is pure debt.
- §3.17 theme → if the project uses `MudThemeProvider` / FluentUI `<FluentDesignTheme>` / `RadzenTheme` and both themes pass SC 1.4.3 / 1.4.11, follow that system. If contrast fails in either theme, the theme is legacy debt — flag it and emit `light-dark()`-based compliant styles in the isolated CSS for the new component (marked as deliberate deviation until the theme is fixed).
- §3.13 `Save-Data` server branching — in `[BWA]`, expose the `Save-Data` header to the Razor page via `IHttpContextAccessor` or a scoped `CascadingValue`; propagate to the `.Client` via `PersistentComponentState` so WebAssembly components receive the same signal after handoff. In `[Standalone]`, read the header server-side at the static-hosting layer (CDN rule, origin server) — the WASM client can't see its own request headers.

### Carve-outs

All carve-outs are conditional on the library's primitive *actually* satisfying the reference rule. Verify before relying on a carve-out; if verification fails, the core smell fires.

- **Do not flag `blazor.HC-5` (custom div-based modal)** when the project uses a UI library's dialog component that passes SC 2.4.11 (focus not obscured), SC 2.1.2 (no keyboard trap misuse), and provides `Esc` dismiss + focus restoration. Each library in the table qualifies *in principle* — verify per version and per theme override.
- **Do not flag missing native `<dialog>`** when the library's dialog delivers top-layer stacking, focus-trap, `Esc`, and focus restoration. Raw `<dialog>` is the fallback pattern, not the only compliant implementation.
- **Do not flag duplicated JS-interop modules** when the existing module lives in a separate package / RCL and the new component lives in the app project — cross-project reuse has its own friction that's out of scope for this skill.

## Stack-specific primitives

- **CSS isolation (`<Component>.razor.css`)** — per-component scoped CSS. Blazor's build rewrites selectors to match elements of the owning component, appending an attribute with the format `b-{STRING}` (a 10-character generated identifier, e.g. `b-3xxtam6d07`). The bundled file is referenced in `<head>` as `{PACKAGE ID/ASSEMBLY NAME}.styles.css` in standalone WASM, or as `@Assets["{PACKAGE ID/ASSEMBLY NAME}.styles.css"]` in Blazor Web App. Logical properties, `@container`, `@media`, `:has()`, `light-dark()` — everything in reference §4 — work inside `.razor.css`. Isolated CSS still inherits `dir` and `color-scheme` from ancestors, so RTL and theming propagate correctly. To style a child component's rendered elements, use the `::deep` pseudo-element. — MDN & Blazor CSS isolation docs.
- **Render modes (`@rendermode`)** `[BWA]` — applies only inside a Blazor Web App. Values come from `Microsoft.AspNetCore.Components.Web.RenderMode`: `InteractiveServer`, `InteractiveWebAssembly`, `InteractiveAuto` (SSR first, WASM on subsequent visits), plus static SSR (the default when no mode is specified). Apply via the `@rendermode` directive on the component file or the `@rendermode` attribute on the component tag. The choice governs when the UI becomes usable and therefore LCP and INP directly. **Components using `InteractiveWebAssembly` or `InteractiveAuto` must live in the `.Client` project** so their assemblies ship to the browser.
- **`ElementReference` + `FocusAsync()`** — set focus programmatically. `FocusAsync` is an extension method on `ElementReference` (`Microsoft.AspNetCore.Components.ElementReferenceExtensions.FocusAsync`). An `ElementReference` is a `struct` and is only valid after the component has rendered — capture it with `@ref` and call from `OnAfterRenderAsync` (`firstRender` gate) or from an event handler fired after first render.
- **`@attributes` splatting + `AdditionalAttributes`** — pass HTML attributes like `autocomplete`, `inputmode`, `enterkeyhint`, `aria-*` through to the underlying element. Built-in form components (`InputText`, `InputNumber`, `InputDate`, `InputSelect`, `InputTextArea`) inherit from `InputBase<T>` and expose an `AdditionalAttributes` dictionary which the template splats with `@attributes`. Setting mobile-keyboard hints requires this splat; the components don't infer them.
- **`@bind:event` and `@bind:after`** — default `@bind` binds on `onchange` (fires on blur). Switch to `@bind:event="oninput"` to bind per keystroke (INP hazard on complex render trees). `@bind:after="{delegate}"` runs an async handler after the synchronous value assignment completes — the canonical debounce/async-after-bind hook. `:get` / `:set` modifiers (`@bind:get="value" @bind:set="HandleChange"`) give separate read/write control, replacing the legacy `value`/`@onchange` pattern.
- **`PersistentComponentState` + `[PersistentState]`** `[BWA]` — preserves state across the SSR → interactive render handoff so components don't re-initialise and flicker. Blazor Web App only (standalone WASM does not prerender by default). Declarative form: annotate a `public` property with `[PersistentState]` and the framework serialises/deserialises it automatically. Imperative form: inject `PersistentComponentState` and call `RegisterOnPersisting(callback)`. Required `<persist-component-state />` tag helper in the layout when using hosted/embedded WASM prerendering; not needed in modern Blazor Web App layouts that already include it.
- **`LazyAssemblyLoader` + `BlazorWebAssemblyLazyLoad`** `[Both]` — lazy-load route-scoped assemblies. Namespace `Microsoft.AspNetCore.Components.WebAssembly.Services`. Declare assemblies for lazy loading in `.csproj` with `<BlazorWebAssemblyLazyLoad Include="Feature.wasm" />` (file extension is `.wasm` in .NET 8+ under the Webcil packaging format). Inject `LazyAssemblyLoader` in `App.razor`, hook into `Router.OnNavigateAsync`, and call `LoadAssembliesAsync(IEnumerable<string>)`. For routable components, pass the returned assemblies to `Router.AdditionalAssemblies`. Handle `NavigationContext.CancellationToken` so a superseded navigation doesn't keep loading. **Never lazy-load core runtime assemblies** — they may be trimmed and unavailable.
- **IL trimming + AOT (`PublishTrimmed=true`, `RunAOTCompilation=true`)** `[Both WASM contexts]` — trimming removes unreachable IL (reduces bundle size); AOT compiles to WebAssembly ahead of time (faster execution but larger bundle — trade-off). Configure in the WASM project's `.csproj`. Trimming interacts with reflection-based serialization; annotate types preserved by `[PersistentState]`, custom JSON converters, and DI resolution so they survive trimming.
- **`IJSObjectReference` module interop** — the idiomatic JS-interop pattern. Import a module: `_module = await js.InvokeAsync<IJSObjectReference>("import", "./js/prefers.js")` (the `"import"` identifier is magic and the path prefix `./` is required). Invoke exported functions on the returned reference. Always dispose via `DisposeAsync` — stored on `IAsyncDisposable` components — to avoid leaking JS memory.
- **`IJSInProcessRuntime` / `IJSInProcessObjectReference`** `[WASM only]` — synchronous JS interop for scenarios that know they only run client-side. Cast `IJSRuntime` to `IJSInProcessRuntime` and call `Invoke<T>(name, args)`. Avoids an async round-trip but won't work under Blazor Server or during SSR prerender — use only where you've confirmed WebAssembly execution.
- **`IJSRuntime` + `matchMedia` interop** — `matchMedia` is not exposed directly to C#. A small JS module bridges it for `prefers-reduced-motion`, `prefers-color-scheme`, `prefers-contrast`, `forced-colors`, `(hover: hover)`, `(pointer: coarse)`. Pattern in `blazor.PAT-prefers-interop` below.
- **`IJSRuntime` + `visualViewport` interop** — for keyboard-aware viewport handling (reference §3.7 and the interactive-widget gotcha). Blazor has no built-in equivalent.
- **`IJSRuntime` + Web Vitals** — emit LCP / CLS / INP to a RUM endpoint from `wwwroot/js/web-vitals-shim.js` calling the `web-vitals` npm lib. The runtime measurements the core reference §7 Performance bucket demands are unavailable without this bridge.

## Stack-specific patterns

### `blazor.PAT-interactive-auto-shell` — Blazor Web App, `InteractiveAuto` for LCP-sensitive pages `[BWA]`

```razor
@* Components/App.razor — default mode for routable pages *@
<Routes @rendermode="InteractiveAuto" />
```

```razor
@* .Client/Pages/Product.razor — WebAssembly-eligible; lives in the .Client project *@
@page "/product/{Id:int}"
@rendermode InteractiveAuto
@inject ProductService Products

<h1>@product.Name</h1>
<picture>
  <source type="image/avif" srcset="@product.AvifSrcset" sizes="(min-width: 40em) 50vw, 100vw">
  <source type="image/webp" srcset="@product.WebpSrcset" sizes="(min-width: 40em) 50vw, 100vw">
  <img src="@product.JpegSrc" alt="@product.Alt" width="1600" height="900" fetchpriority="high" decoding="async">
</picture>

@code {
    [Parameter] public int Id { get; set; }

    [PersistentState] public ProductDto? CachedProduct { get; set; }

    protected override async Task OnInitializedAsync()
    {
        CachedProduct ??= await Products.Get(Id);
    }

    private ProductDto product => CachedProduct!;
}
```

Server enables both interactive modes:

```csharp
// Program.cs (server project)
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents()
    .AddInteractiveWebAssemblyComponents();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode()
    .AddInteractiveWebAssemblyRenderMode();
```

Above-the-fold content renders via SSR immediately (LCP target reachable). WebAssembly takes over on subsequent visits once the bundle has downloaded, and `[PersistentState]` carries the data across so the component doesn't re-fetch. `InteractiveAuto` is **not available in standalone WASM** — the alternative there is to ship a smaller bundle (trimming, lazy-loading) and design for the WASM boot as part of LCP.

### `blazor.PAT-focus-on-navigate` — Restore focus after `NavigationManager.NavigateTo` `[Both]`

```razor
@* MainLayout.razor *@
@inject NavigationManager Nav
@implements IDisposable

<main id="main" tabindex="-1" @ref="mainRef">
  @Body
</main>

@code {
    private ElementReference mainRef;
    private bool navigated;

    protected override void OnInitialized() => Nav.LocationChanged += OnLocationChanged;

    private void OnLocationChanged(object? sender, LocationChangedEventArgs e) => navigated = true;

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        if (navigated)
        {
            navigated = false;
            await mainRef.FocusAsync();
        }
    }

    public void Dispose() => Nav.LocationChanged -= OnLocationChanged;
}
```

Focus is moved in `OnAfterRenderAsync` so the new view has rendered before focus lands on it. In Blazor Web App with enhanced navigation, `LocationChanged` fires for same-document navigations only when an interactive runtime is active — document the requirement.

### `blazor.PAT-prefers-interop` — Bridge `matchMedia` to C#

```javascript
// wwwroot/js/prefers.js
export function matches(query) { return globalThis.matchMedia(query).matches; }
export function watch(query, dotnetRef, methodName) {
  const mql = globalThis.matchMedia(query);
  const handler = (e) => dotnetRef.invokeMethodAsync(methodName, e.matches);
  mql.addEventListener("change", handler);
  handler(mql);
  return () => mql.removeEventListener("change", handler);
}
```

```csharp
// Services/PrefersService.cs
public sealed class PrefersService(IJSRuntime js) : IAsyncDisposable
{
    private IJSObjectReference? _module;

    public async ValueTask<bool> Matches(string query)
    {
        _module ??= await js.InvokeAsync<IJSObjectReference>("import", "./js/prefers.js");
        return await _module.InvokeAsync<bool>("matches", query);
    }

    public async ValueTask DisposeAsync()
    {
        if (_module is not null) await _module.DisposeAsync();
    }
}
```

Use it to gate autoplay, parallax, transitions, and reveal-on-hover logic that C# alone can't see.

### `blazor.PAT-razor-dialog` — Native `<dialog>` via a JS module `[Both]`

```javascript
// wwwroot/js/dialog.js
export function showModal(el) { el.showModal(); }
export function close(el) { el.close(); }
```

```razor
@* EditProfileDialog.razor *@
@inject IJSRuntime JS
@implements IAsyncDisposable

<button type="button" @onclick="Open">Edit profile</button>

<dialog @ref="dialogRef" aria-labelledby="profile-title">
  <header>
    <h2 id="profile-title">Edit profile</h2>
    <button type="button" @onclick="Close" aria-label="Close">×</button>
  </header>

  <EditForm EditContext="editContext" OnValidSubmit="Save">
    <DataAnnotationsValidator />
    <!-- InputText fields with AdditionalAttributes for autocomplete/inputmode -->
    <div class="actions">
      <button type="button" @onclick="Close">Cancel</button>
      <button type="submit" class="primary">Save</button>
    </div>
  </EditForm>
</dialog>

@code {
    private ElementReference dialogRef;
    private IJSObjectReference? _module;
    private EditContext editContext = null!;

    protected override void OnInitialized()
    {
        editContext = new EditContext(Model ?? new ProfileModel());
    }

    [Parameter] public ProfileModel? Model { get; set; }
    [Parameter] public EventCallback<ProfileModel> OnSave { get; set; }

    private async Task Open()
    {
        _module ??= await JS.InvokeAsync<IJSObjectReference>("import", "./js/dialog.js");
        await _module.InvokeVoidAsync("showModal", dialogRef);
    }

    private async Task Close()
    {
        if (_module is not null) await _module.InvokeVoidAsync("close", dialogRef);
    }

    private async Task Save()
    {
        await OnSave.InvokeAsync((ProfileModel)editContext.Model);
        await Close();
    }

    public async ValueTask DisposeAsync()
    {
        if (_module is not null) await _module.DisposeAsync();
    }
}
```

Native `<dialog>` handles focus trap, `Escape` to close, `inert` on the rest of the page, and focus restoration automatically (reference §5.8, SC 2.4.11). The JS module exists because `HTMLDialogElement.showModal()` can't be invoked via raw `IJSRuntime.InvokeVoidAsync("showModal", dialogRef)` — it needs a JS function wrapper. `EditForm` handles Blazor's validation cycle; dialog open/close is orthogonal to form submission and goes through the JS module.

### `blazor.PAT-isolated-responsive-card` — Container-aware card in isolated CSS

```razor
@* ProductCard.razor *@
<article class="card">
  <picture>…</picture>
  <div class="body">
    <h3>@Title</h3>
    <p class="price"><strong>@Price</strong></p>
  </div>
  <button class="buy" type="button" @onclick="AddToCart">Add to cart</button>
</article>

@code {
    [Parameter] public string Title { get; set; } = "";
    [Parameter] public string Price { get; set; } = "";
    [Parameter] public EventCallback OnAdd { get; set; }
    private Task AddToCart() => OnAdd.InvokeAsync();
}
```

```css
/* ProductCard.razor.css — scoped by Blazor build; selectors rewritten to append b-{STRING} */
.card {
  container-type: inline-size;
  container-name: card;
  display: grid;
  gap: 1rem;
  padding: clamp(0.75rem, 2cqi, 1.5rem);
  background: light-dark(#fff, #1a1a1a);
  color: light-dark(#111, #eee);
  border-radius: 1rem;
}
.card img { inline-size: 100%; block-size: auto; aspect-ratio: 4 / 3; }
.card .buy { min-block-size: 2.75rem; min-inline-size: fit-content; padding-inline: 1rem; }
.card .price strong { font-weight: 700; }

@container card (inline-size > 28rem) {
  .card { grid-template-columns: 40% 1fr; align-items: start; }
  .card img { aspect-ratio: 16 / 9; }
}
@media (hover: hover) {
  .card .buy:hover { background-color: color-mix(in oklch, currentColor, black 10%); }
}
@media (prefers-reduced-motion: no-preference) {
  .card { transition: transform 150ms ease; }
  .card:hover { transform: translateY(-2px); }
}
```

Logical properties throughout; container-aware layout; hover gated; motion gated; theme via `light-dark()`. Scoping happens at build, so the component is reusable in any layout.

### `blazor.PAT-lazy-route-module` — Lazy-load a feature assembly on route navigation `[Both]`

```xml
<!-- Client.csproj (or the WASM app csproj for standalone) -->
<ItemGroup>
  <BlazorWebAssemblyLazyLoad Include="MyApp.Admin.wasm" />
  <BlazorWebAssemblyLazyLoad Include="MyApp.Admin.Shared.wasm" />
</ItemGroup>
```

```razor
@* App.razor *@
@inject LazyAssemblyLoader Loader
@using System.Reflection
@using Microsoft.AspNetCore.Components.Routing
@using Microsoft.AspNetCore.Components.WebAssembly.Services

<Router AppAssembly="typeof(App).Assembly"
        AdditionalAssemblies="lazyAssemblies"
        OnNavigateAsync="OnNavigateAsync">
  <Navigating><p>Loading…</p></Navigating>
  <Found Context="routeData">…</Found>
  <NotFound>…</NotFound>
</Router>

@code {
    private readonly List<Assembly> lazyAssemblies = new();

    private async Task OnNavigateAsync(NavigationContext args)
    {
        if (args.Path.StartsWith("admin", StringComparison.OrdinalIgnoreCase))
        {
            try
            {
                var loaded = await Loader.LoadAssembliesAsync(
                    new[] { "MyApp.Admin.wasm", "MyApp.Admin.Shared.wasm" });
                lazyAssemblies.AddRange(loaded);
            }
            catch (OperationCanceledException) when (args.CancellationToken.IsCancellationRequested)
            {
                // Superseded navigation; let the new navigation continue.
                throw;
            }
        }
    }
}
```

File extension is `.wasm` under the Webcil packaging format (.NET 8+). Always observe `args.CancellationToken`. Show a `<Navigating>` block so users see a transition while assemblies download.

## Smell codes

### `blazor.HC-1` — Physical properties in `*.razor.css` `[Both]`

**Pattern:** any of `margin-left`, `margin-right`, `padding-top`, `padding-bottom`, `top:`, `right:`, `bottom:`, `left:` (for positioning), `text-align: left`, `text-align: right`, `float: left`, `float: right` in an isolated stylesheet.

**Detection:** `rg -n --glob '*.razor.css' -P '(margin|padding)-(left|right|top|bottom)\b|^\s*(top|right|bottom|left)\s*:|text-align:\s*(left|right)|float:\s*(left|right)'`

**Severity:** `warn` (`block` if the project declares RTL support in resources / config).

**Reference:** §3.9, §6 "RTL breaks because physical properties leaked".

**Action:** Replace with logical equivalents — `margin-inline-start` / `padding-block-end` / `inset-inline-start` / `text-align: start` / `float: inline-start`.

### `blazor.HC-2` — `@bind:event="oninput"` on expensive bindings `[Both]`

**Pattern:** `@bind:event="oninput"` on a field that triggers a parent re-render, JS interop, or server call on every keystroke.

**Detection:** `rg -n --glob '*.razor' '@bind:event="oninput"'` then inspect surrounding handlers (is `@bind:after` present? does the bound field drive an expensive child component?).

**Severity:** `warn`.

**Reference:** §3.14 Animation and interaction performance (INP budget).

**Action:** Default to `@bind` (onchange). If per-keystroke behaviour is required, pair with `@bind:after=` calling a debounced helper so expensive work runs every 200–300 ms at most. Consider `@bind:get` / `@bind:set` if you need to intercept and reshape the incoming value before it reaches the model.

### `blazor.HC-3` — `NavigationManager.NavigateTo` without focus restoration `[Both]`

**Pattern:** A component calls `NavigationManager.NavigateTo` (or a `<NavLink>` leads to a page change) without any subsequent `ElementReference.FocusAsync()` on a landmark of the new view.

**Detection:** `rg -n --glob '*.razor.cs' --glob '*.razor' 'NavigationManager\.NavigateTo|NavManager\.NavigateTo|Nav\.NavigateTo|@inject NavigationManager'` and cross-reference to a `FocusAsync` call in the layout or route component's `OnAfterRenderAsync` / `LocationChanged` handler.

**Severity:** `warn`.

**Reference:** §3.16 Focus management; SC 2.4.3 Focus Order; SC 2.4.11 Focus Not Obscured.

**Action:** Apply `blazor.PAT-focus-on-navigate` in `MainLayout.razor`. In Blazor Web App with enhanced navigation enabled, note that location-changing handlers only fire for programmatic navigation from an interactive runtime.

### `blazor.HC-4` — Above-the-fold content rendered with `InteractiveWebAssembly` without SSR fallback `[BWA]`

**Pattern:** In a Blazor Web App, a page's hero / LCP candidate lives in a component with `@rendermode InteractiveWebAssembly` and no `[PersistentState]` data carry or SSR fallback. LCP waits for the WASM runtime to boot and the assemblies to download before painting.

**Detection:** Grep the `.Client` project's pages for `@rendermode InteractiveWebAssembly` and check whether the first `<h1>` / hero image is inside it. If the page has no server-side component above the hero, flag it.

**Severity:** `block` for public / marketing pages; `warn` for authenticated app pages.

**Reference:** §2.8 Performance is responsiveness; §7 Performance bucket (LCP ≤ 2.5 s at mobile p75).

**Action:** Switch to `InteractiveAuto` (SSR first, WASM later) and annotate load-bearing data with `[PersistentState]` so the handoff doesn't re-fetch. See `blazor.PAT-interactive-auto-shell`. `[Standalone]` projects cannot use `InteractiveAuto` — reduce bundle size via trimming + lazy-loading instead, and accept that LCP is bounded by WASM boot.

### `blazor.HC-5` — Custom div-based modal in Razor `[Both]`

**Pattern:** A `<div class="modal">` (or any non-`<dialog>` element) with JS-toggled visibility instead of `<dialog>` + `showModal()`.

**Detection:** `rg -n --glob '*.razor' '(class|className)="[^"]*modal[^"]*"' | rg -v 'dialog'`

**Severity:** `block` (a11y failure: no focus trap, no `inert`, no `Escape`).

**Reference:** §5.8 Dialog / modal; SC 2.4.11 Focus Not Obscured; SC 2.1.2 No Keyboard Trap.

**Action:** Replace with `blazor.PAT-razor-dialog` using native `<dialog>` and a JS module exposing `showModal`/`close`.

### `blazor.HC-6` — `InputText` / `InputNumber` / `InputDate` without mobile-keyboard hints `[Both]`

**Pattern:** A `<InputText>` / `<InputNumber>` / `<InputDate>` / `<InputSelect>` / `<InputTextArea>` binding to user-facing data without an `@attributes` splat carrying `autocomplete`, `inputmode`, or `enterkeyhint`.

**Detection:** `rg -n --glob '*.razor' '<Input(Text|Number|Date|Select|TextArea)' | rg -v '@attributes|AdditionalAttributes|autocomplete|inputmode|enterkeyhint'`

**Severity:** `warn`.

**Reference:** §4 primitives (`autocomplete`, `inputmode`, `enterkeyhint`); SC 1.3.5 Identify Input Purpose; SC 3.3.8 Accessible Authentication.

**Action:** Provide an `AdditionalAttributes` dictionary (the base `InputBase<T>` exposes it) and splat via `@attributes`. Canonical tokens: email → `autocomplete="email" inputmode="email" enterkeyhint="next"`; OTP → `autocomplete="one-time-code" inputmode="numeric"`; card number → `autocomplete="cc-number" inputmode="numeric"`.

### `blazor.HC-7` — No `wwwroot/index.html` / `App.razor` baseline boilerplate `[Both]`

**Pattern:** The WASM host HTML (`wwwroot/index.html` for standalone; `App.razor` / `<HeadOutlet>` for Blazor Web App) is missing any of: `viewport-fit=cover`, `interactive-widget=resizes-content`, `color-scheme` meta, `theme-color` meta per scheme, `preload` for LCP asset / critical fonts, `preconnect` to API origin.

**Detection:** Read `wwwroot/index.html` (`[Standalone]`) or `App.razor` and `Components/App.razor` (`[BWA]`) and compare to reference §4.5.

**Severity:** `warn`.

**Reference:** §4.5 Baseline boilerplate.

**Action:** Port the §4.5 `<head>` block into the host file, adjusting theme colours and API origin. In `[BWA]`, use the `<HeadContent>` component for per-page overrides.

### `blazor.HC-8` — No assembly lazy-loading on non-trivial routes `[Both]`

**Pattern:** A WASM project with multiple feature areas but no `<BlazorWebAssemblyLazyLoad Include="…"/>` entries and no `Router.OnNavigateAsync` assembly-loading hook.

**Detection:** `rg -n --glob '*.csproj' 'BlazorWebAssemblyLazyLoad'` returning empty + more than ~3 feature areas / route modules + published bundle exceeds ~1 MB compressed.

**Severity:** `info` (bundle budget); `warn` if the initial bundle blocks LCP for the simplest route.

**Reference:** §3.13 Network and capability awareness; §2.8 Performance is responsiveness.

**Action:** Apply `blazor.PAT-lazy-route-module`. Keep shared framework assemblies in the initial bundle; split feature-specific ones. Never lazy-load core runtime assemblies that trimming may remove.

### `blazor.HC-9` — `IJSRuntime` call in `OnInitialized` (not `OnAfterRender`) `[BWA prerender]` `[SSR]`

**Pattern:** A component invokes `IJSRuntime.InvokeAsync*` in `OnInitialized` / `OnInitializedAsync` / `OnParametersSet`. Under prerender (`[BWA]` with SSR first) this throws because there's no browser JS context. Standalone WASM tolerates it because there is no prerender, but the smell still indicates a lifecycle misplacement.

**Detection:** `rg -n --glob '*.razor' --glob '*.razor.cs' -B 5 'InvokeAsync|InvokeVoidAsync' | rg 'OnInitialized|OnParametersSet'`

**Severity:** `warn` for standalone WASM; `block` for Blazor Web App.

**Action:** Move JS-interop calls into `OnAfterRenderAsync(bool firstRender)` and gate on `firstRender` where the call should only run once. If the component must initialise from JS-derived data, use `[PersistentState]` to carry it from SSR, or render a `"loading…"` state until interop returns.

### `blazor.HC-10` — Hardcoded `100vh` in a Razor component `[Both]`

**Pattern:** Any `100vh` in a `.razor.css` file on an element visible to the user on mobile.

**Detection:** `rg -n --glob '*.razor.css' '100vh\b'`

**Severity:** `block` (straightforward fix; no excuses in modern Blazor).

**Reference:** §3.7 `dvh` / `svh` / `lvh` vs `vh`.

**Action:** Replace with `100svh` for guaranteed-visible layouts, `100dvh` for edge-to-edge heroes, `100lvh` for URL-bar-hidden scrolling. Never bare `vh`.

### `blazor.HC-11` — Trimming without preserving types used by reflection or `[PersistentState]` `[Both]`

**Pattern:** `<PublishTrimmed>true</PublishTrimmed>` and/or `<RunAOTCompilation>true</RunAOTCompilation>` in the WASM project file, without `[DynamicallyAccessedMembers]` annotations or `<TrimmerRootAssembly>` entries for types that `[PersistentState]`, custom `JsonConverter`s, or reflection-based DI resolution depend on.

**Detection:** `rg -n --glob '*.csproj' 'PublishTrimmed|RunAOTCompilation'` and cross-reference with `[PersistentState]` usage and any `JsonSerializer.Serialize(...)` calls without a source-generated `JsonSerializerContext`.

**Severity:** `warn` (runtime errors at deserialization are easy to miss in dev).

**Reference:** N/A (stack-specific); relates to §3.13 (bundle budget) and §2.8 (performance).

**Action:** Prefer source-generated `JsonSerializerContext` over reflection-based serializers. Annotate preserved types. Test a trimmed + AOT build locally, not just a dev build.

### `blazor.LC-1` — `@media` queries inside `.razor.css` using `px` thresholds

**Pattern:** `@media (min-width: 768px)` or similar hard-coded `px` breakpoints in isolated CSS.

**Severity:** `info`.

**Reference:** §3.4 Breakpoints — derive from content, not device presets.

**Action:** Convert to `em`-based breakpoints that derive from the component's line measure, or — better — migrate to an `@container` query so the component responds to its own context.

### `blazor.LC-2` — `@rendermode` set on every page rather than at `App.razor` / `Routes` `[BWA]`

**Pattern:** Per-page `@rendermode` directives scattered across routes with no consistent convention.

**Severity:** `info`.

**Reference:** N/A (stack-specific organisational smell).

**Action:** Declare a default render mode at `App.razor` / `<Routes>`; override per page only when the default is wrong. Makes LCP characteristics of the app predictable.

### `blazor.LC-3` — Synchronous JS interop (`IJSInProcessRuntime`) used in a component that may also run under SSR `[BWA]`

**Pattern:** A component in the `.Client` project casts `IJSRuntime` to `IJSInProcessRuntime` without guarding on `OperatingSystem.IsBrowser()` or `RendererInfo.IsInteractive`.

**Severity:** `info`.

**Action:** Guard with `OperatingSystem.IsBrowser()` or keep the component `InteractiveWebAssembly`-only if sync interop is required. During SSR prerender the cast succeeds but calls fail.

## Positive signals

- **`blazor.POS-1`** — Isolated CSS (`*.razor.css`) uses only logical properties.
- **`blazor.POS-2`** `[BWA]` — `InteractiveAuto` render mode on LCP-sensitive pages, with `[PersistentState]` preserving data across the SSR → WASM handoff.
- **`blazor.POS-3`** `[Both]` — Route-module assemblies lazy-loaded; initial compressed bundle stays under ~1 MB.
- **`blazor.POS-4`** — `ElementReference.FocusAsync()` called in `LocationChanged`-driven `OnAfterRenderAsync` so focus lands on `<main>` after every navigation.
- **`blazor.POS-5`** — `matchMedia` interop service exists; components consult `prefers-reduced-motion` / `(hover: hover)` / `(pointer: coarse)` via C# rather than duplicating logic across CSS and code.
- **`blazor.POS-6`** — Web Vitals instrumented via `web-vitals` npm lib + JS interop, posting LCP / CLS / INP to a RUM endpoint. Closes the loop the core reference §7 Performance bucket asks for but cannot statically verify.
- **`blazor.POS-7`** — `<InputText>` / `<InputNumber>` / `<InputDate>` use `AdditionalAttributes` splat to pass `autocomplete`, `inputmode`, `enterkeyhint`.
- **`blazor.POS-8`** — Modal dialogs use `<dialog>` + `showModal()` via a JS module, not custom div overlays.
- **`blazor.POS-9`** — Host HTML (`wwwroot/index.html` / `App.razor`) mirrors reference §4.5 baseline boilerplate (`viewport-fit=cover`, `interactive-widget=resizes-content`, `color-scheme`, `theme-color` per scheme, `preload` for LCP asset + critical fonts, `preconnect` for API origin).
- **`blazor.POS-10`** — `PublishTrimmed=true` configured with explicit root annotations; AOT scoped to hot paths, not global.
- **`blazor.POS-11`** — Source-generated JSON serialization (`[JsonSerializable]` on a `JsonSerializerContext`) replacing reflection-based calls — trimming-safe.

## Carve-outs

- **Do not flag core "physical property" smells** when the physical property targets a *browser-fixed* axis with no writing-mode dependence — e.g., `scroll-padding-top` on a sticky-header scroll target, `top:` on a toast positioned visually at screen top regardless of direction. Require a one-line comment justifying the physical choice; otherwise `blazor.HC-1` still applies.
- **Do not flag "no `srcset`" smells** on developer-tool UI components (admin dashboards, IDE-like internal tools) where the image set is controlled and one resolution is sufficient. State the exception in the page-level comment.
- **Do not flag "missing `color-scheme`"** on components explicitly scoped to a single theme (branded embed widgets, chart containers that render on a known background). The exception must be stated in the component XML doc.
- **Do not flag `blazor.HC-9` (JS interop in `OnInitialized`)** on components marked `@rendermode InteractiveWebAssembly` in a Blazor Web App that also opts out of prerendering via `@rendermode @(new InteractiveWebAssemblyRenderMode(prerender: false))` — there's no SSR pass for interop to fail against. State the opt-out explicitly.

## Applies to which reference checklist items

| Reference §7 item | Blazor-specific check |
|---|---|
| Renders at 320 CSS px without horizontal scroll | Components compose cleanly under `container-type: inline-size` — verify at runtime via browser DevTools or Playwright viewport emulation. |
| Target ≥ 24×24 CSS px | Audit isolated CSS for buttons, chips, links; `blazor.HC-1` often correlates with bad sizing when physical-property leaks drive ad-hoc dimensions. |
| Focus visible and preserved through layout changes | `blazor.HC-3` (focus restoration) + `[BWA]` SSR→WASM handoff preserving focus via `[PersistentState]` + `ElementReference`. |
| All spacing / positioning uses logical properties | `blazor.HC-1` inside `.razor.css`. |
| `dir="rtl"` works | Root `<html dir="rtl">` in `wwwroot/index.html` (`[Standalone]`) or via `@attributes` on the root element in `App.razor` (`[BWA]`), typically driven by the request's `CultureInfo`. |
| LCP ≤ 2.5 s | `[BWA]` `blazor.HC-4` guards against WASM-bound above-the-fold; `blazor.POS-2` + `blazor.POS-3` + `blazor.POS-9` supply the fix. `[Standalone]` relies on `blazor.POS-3` (lazy-load) + `blazor.POS-10` (trim) — but cannot beat WASM boot time. **Runtime LCP still needs RUM.** |
| INP ≤ 200 ms | `blazor.HC-2` (`@bind:event="oninput"`), `blazor.HC-9` (JS interop in wrong lifecycle), `blazor.LC-3` (sync interop under SSR). |
| Fonts load with `font-display: swap` | Core — fonts served from `wwwroot/` or a CDN; configure at `@font-face` time. Same as core. |
| Resource hints in place | `blazor.HC-7` checks the host HTML for `preconnect` to API origin and `preload` for LCP asset + critical fonts. |
