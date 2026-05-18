<div align="center">

# 🜂 PLUGINS 🜂

**extending Olympus from outside the repo**

</div>

---

Olympus discovers third-party extensions at startup via Python's
standard `importlib.metadata` entry-point mechanism. Plugins are
pip-installable packages — no Olympus fork required.

If you are reading this to author a plugin, the recipe is at the
bottom. If you are reading this to understand what plugins can do,
the table below is your map.

---

## Entry-point groups

| group | what plugins register | how it's wired |
|---|---|---|
| `olympus.prometheus_handlers` | functions `(action) -> (before, after)` | `Prometheus.register(name, fn)` |
| `olympus.asclepius_healers`   | functions `() -> (succeeded, changed, detail)` | `Asclepius.register(name, fn)` |
| `olympus.argos_eyes`          | Eye class or instance | added to the colony |
| `olympus.apollo_predictions`  | a `Prediction` or factory returning one | `apollo.predict(prediction)` |
| `olympus.cli_errands`         | a callable (or `(summary, callable)` tuple) | `hermes.register(name, summary)(fn)` |

---

## The discipline plugins must follow

Plugins are first-class participants in the substrate. The same
invariants apply:

- **S1 (Mnemosyne)** — every load-bearing action a plugin takes must
  write to Mnemosyne via `mnemosyne.remember(...)`. Silent side effects
  are AP6 (understanding-obscuring).
- **S3 (read-only observation)** — eyes and HYDRA-style watchers do
  not mutate state. Plugin-registered eyes that write fail Furies
  invariants and get caught.
- **S7 (bounded autonomy)** — plugin handlers run with the same risk-
  class semantics as built-ins. A handler that wants to perform a
  HIGH-risk action must route through Hephaestus → Momus → Delphi →
  Zeus, not just do it.
- **S8 (continuity)** — every recorded plugin action must be
  reconstructable from substrate records alone. No "trust me bro"
  derivations.

Plugin failures (import-time or registration-time) are captured per-
plugin and never abort the load pass. The `plugins.loaded` Mnemosyne
record names what loaded and what failed.

---

## Recipe — authoring a plugin

Create a normal Python package. In your `pyproject.toml`:

```toml
[project]
name = "olympus-my-plugin"
version = "0.1.0"

[project.entry-points."olympus.prometheus_handlers"]
my_rotation = "olympus_my_plugin.handlers:rotate_my_logs"

[project.entry-points."olympus.asclepius_healers"]
my_recovery = "olympus_my_plugin.healers:repair_my_cache"

[project.entry-points."olympus.cli_errands"]
mything = "olympus_my_plugin.cli:my_errand"
```

Your `olympus_my_plugin/handlers.py`:

```python
def rotate_my_logs(action):
    """Rotate domain-specific log files. Returns (before, after) state."""
    from olympus.titans.mnemosyne import mnemosyne
    before = {"my_log_lines": _count_lines()}
    _rotate()
    after = {"my_log_lines": _count_lines()}
    return before, after
```

Install:

```bash
pip install -e .
```

Verify:

```bash
invoke plugins
```

You should see your handler listed under `loaded`.

---

## Inspecting plugin discovery

`invoke plugins` (no flags) discovers and reports without auto-loading.
The CLI's bootstrap auto-loads on every `invoke` invocation. To disable
auto-load (e.g., for diagnosis), set `OLYMPUS_DISABLE_PLUGINS=1`.

Every load pass writes one `plugins.loaded` record to Mnemosyne with:

- `loaded` — list of `{group, name, target}`
- `failed` — list of `{group, name, target, detail}` with the import
  or registration error

---

## What plugins should NOT do

- **Mutate `state/` or `codex/` directly** outside their registered surface.
  Use the substrate's APIs.
- **Replace built-in handlers** by re-registering the same name. The
  built-ins are the constitutional minimum; plugins augment, they don't
  override.
- **Phone home.** External calls go through `pythia` so they are
  recorded in Mnemosyne with the same audit-of-record discipline as
  every other event.
- **Bypass Pan.** If your plugin wants to ratify actions, it goes
  through `action_queue.ratify` — which consults Pan — like anything
  else.

---

## Examples of legitimate plugin work

- **Domain handlers** — your deployment archives domain-specific JSONL,
  rebuilds domain caches, runs domain integrity checks.
- **Domain eyes** — observation specialists watching slices unique to
  your domain (an `eye_my_service_health`, an `eye_my_data_freshness`).
- **Domain predictions** — Apollo claims about your domain ("the
  customer queue depth will drop below 100 by tomorrow noon").
- **CLI extensions** — `invoke mydomain report` that aggregates your
  domain's recent records into a summary.

---

*Per Delphi 2026-05-18-recursion-arc.md. Plugins are how Olympus
becomes genuinely useful in a specific operator's context — domain
expertise lives in the plugin, the substrate stays generic.*
