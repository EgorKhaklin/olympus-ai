# Delphi — restructure to namespaced src/olympus/ layout

**Risk class:** HIGH (filesystem restructure — every import touched)
**Opened:** 2026-05-18
**Closed:** 2026-05-18
**Decided:** Position B (namespaced `src/olympus/`)
**Authorized by Zeus** (proposed exactly this layout in-chat).
**Sworn on Styx** at this commit.

---

## Question

The repository root currently shows 14+ top-level directories. On GitHub's
landing page this reads as scattered. Most of the directories are
mythological-tier source dirs that could live together under a single
parent.

## Hephaestus's three structures (recorded in Mnemosyne)

| id | name | shape |
|---|---|---|
| `arch-2026-05-18-9270` | **Flat src/** | All tiers directly under `src/`; imports stay `from titans.X import Y` |
| `arch-2026-05-18-2126` | **Namespaced src/olympus/** | All tiers under `src/olympus/`; imports become `from olympus.titans.X import Y`; pip-installable |
| `arch-2026-05-18-3798` | **Namespaced + codex→docs rename** | #2 plus rename `codex/` → `docs/` per Python convention |

## Momus contest

| candidate | dings | passes |
|---|---|---|
| Flat src/ | AP3 — cosmetic shuffle; no single package identity | AP1, AP6 |
| **Namespaced src/olympus/** | **(none)** | AP1, AP3, AP4, AP6, AP8 |
| Namespaced + docs/ rename | AP2 — bundles structural move with debatable rename | AP1, AP3 |

## Decision

**Position B — Namespaced `src/olympus/`.**

Final layout:

```
Olympus/
├── README.md, LICENSE, NOTICE, SECURITY.md, pyproject.toml, .gitignore
├── codex/             prose: COSMOGONY, PANTHEON, RITES, CHRONICLE, PROPHECIES,
│   ├── ...            BESTIARY, style, threat-model, journal/, postmortems/, oracles/
│   └── oracles/delphi/  decision records (moved from /oracles/)
├── src/
│   └── olympus/       single importable package
│       ├── primordials/, titans/, olympians/, underworld/,
│       ├── fates/, furies/, graces/, muses/, heroes/, monsters/
│       └── cli.py     pip-install entry point
├── scripts/invoke     thin wrapper for ./scripts/invoke
└── tests/
```

Plus runtime state under `state/` (gitignored — not visible on GitHub).

## Knock-on changes this Delphi authorizes

1. All 10 tier directories move to `src/olympus/<tier>/`.
2. `src/olympus/__init__.py` created (package marker).
3. All `from <tier>.X import Y` rewritten to `from olympus.<tier>.X import Y` across
   every Python file: tier modules, `scripts/invoke`, all tests.
4. `oracles/` folded into `codex/oracles/` (decision records are prose).
5. Dynamic state moved from inside-package paths to root `state/`:
   - `monsters/argos/pheromones.jsonl` → `state/argos/pheromones.jsonl`
   - `underworld/styx.jsonl` → `state/styx.jsonl`
   - `underworld/hades/` → `state/hades/`
   - `underworld/tartarus.jsonl` → `state/tartarus.jsonl`
   - `titans/mnemosyne/` → `state/mnemosyne/`
   - `olympians/athena_briefs/` → `state/athena/`
   - `olympians/hephaestus_proposals/` → `state/hephaestus/`
   - `olympians/hera_bindings.jsonl` → `state/hera_bindings.jsonl`
   - `olympians/dionysus_transitions.jsonl` → `state/dionysus.jsonl`
   - `olympians/hestia_hearth.json` → `state/hestia_hearth.json`
6. `pyproject.toml` added: `name=olympus`, hatchling build, `[project.scripts] invoke = olympus.cli:main`.
7. `src/olympus/cli.py` created (moved Hermes-dispatch logic from `scripts/invoke`).
8. `scripts/invoke` becomes a thin wrapper invoking `olympus.cli:main`.
9. Gaia's root-discovery updated to walk up from `src/olympus/primordials/gaia.py`
   to the dir containing `codex/COSMOGONY.md` (same algorithm, deeper start).
10. `tests/conftest.py` (or per-file sys.path) updated to add `src/` to sys.path.
11. README + PANTHEON + CHRONICLE updated with new paths.
12. `.gitignore` extended with `state/`.

## What is preserved

- All mythological tier names and structure.
- Every named module (no gods deleted, no concepts renamed).
- The cosmogonic hierarchy (primordials → titans → olympians → ...).
- The Hephaestus + Momus + Delphi debate protocol.
- All eight substrate invariants (S1–S8).
- Hestia's vocation slot.

## What's gained

- **Root cleanliness**: GitHub shows ~5 files + 4 dirs (down from 14+ dirs).
- **Pip-installable**: `pip install -e .` and `import olympus` work.
- **State separation**: code in `src/`, runtime data in `state/` (gitignored).
- **Modern Python convention**: `src/` layout is current best practice.

---

*Sworn on Styx at this commit. Future structural moves require a new Delphi.*
