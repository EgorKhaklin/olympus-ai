<div align="center">

# ⚡ DOMAIN.md TEMPLATE ⚡

**copy this file to `DOMAIN.md` at your project root and fill in**

</div>

---

The substrate (Olympus) names HOW an agent operates: with reconstructability, with audit-of-record, with bounded autonomy. Your DOMAIN.md names WHAT this specific agent does.

Substrate invariants (S1–S8 from `codex/COSMOGONY.md`) apply to every Olympus deployment. Domain invariants (C1–CN below) apply to **this** deployment.

---

# DOMAIN.md — < my-agent >

## What this agent is for

> *< one sentence — concrete, falsifiable, operator-readable >*

Examples:
- *"draft literature-review sections from a corpus of operator-supplied PDFs without hallucinating citations"*
- *"surface anomalies in production traffic that the on-call should know about within 5 minutes"*
- *"help the operator maintain a personal knowledge graph by suggesting links between newly-captured notes and existing ones"*

## What this agent refuses

State plainly what is OUT of scope. Refusals are constitutional — Hephaestus surfaces drift against them, Momus contests proposals that breach them.

- this agent will not < e.g., generate text claiming to cite a paper that is not in the corpus >
- this agent will not < e.g., act on behalf of the operator without `invoke action ratify` >
- this agent will not < e.g., retain user audio recordings beyond N hours >

## Domain invariants (C1–CN)

Falsifiable claims about this deployment that must always hold. Each one names how it's enforced.

### C1 — < short name >

> < the claim, in one sentence >

**Enforced by:** < which Eye / Head / test / runtime check verifies this >

### C2 — < short name >

> < the claim >

**Enforced by:** < ... >

*(add as many as the domain requires; a research-agent deployment might have 4; a personal-AI deployment might have 6; an identity-system deployment might have 10)*

## Risk classes — domain examples

The substrate defines LOW / MEDIUM / HIGH / COMPOSITE. Name what each looks like in YOUR domain:

| class | example for this domain |
|---|---|
| **LOW** | < e.g., "fixing a typo in a draft section" > |
| **MEDIUM** | < e.g., "adding a new corpus source" > |
| **HIGH** | < e.g., "changing the citation-hallucination definition" > |
| **COMPOSITE** | < e.g., "amending C1 — what counts as a citation" > |

## Operator

| field | value |
|---|---|
| Zeus's name | < e.g., "Egor Khaklin" — set via OLYMPUS_OPERATOR env var > |
| Authorization phrases | < e.g., "boil the ocean", "Zeus authorized", "ship now" > |
| Refusal trigger | < if Zeus says X, the agent does Y > |

## Cadences

| tier | how often |
|---|---|
| HYDRA `invoke session` | < e.g., every operator session start > |
| Argos auto-deploy | < e.g., on-demand only / hourly cron / never > |
| Apollo audit | < e.g., monthly review of predicate acceptance rate > |
| Delphi review | < e.g., weekly walk through `invoke action delphi` > |
| `invoke correlate` | < e.g., weekly > |

## Domain-specific anti-patterns

Momus's catalog (AP1–AP8 in `src/olympus/heroes/momus.py`) is substrate-level. Add domain-specific ones here:

- **AP-D1 — < name >**: < pattern description and why this domain refuses it >
- **AP-D2 — < name >**: < ... >

## What lives where (domain-specific quick-ref)

| question | file |
|---|---|
| What is this agent? | `DOMAIN.md` (you are here) |
| What is the cognitive substrate? | [`codex/COSMOGONY.md`](codex/COSMOGONY.md) |
| Domain-specific Eyes | `src/olympus/monsters/argos/eyes/eye_*.py` |
| Domain-specific Heads | `src/olympus/monsters/hydra/heads/head_*.py` |
| Domain-specific code | < `src/my_agent/`, etc. > |
| Domain-specific tests | `tests/test_my_domain*.py` |
| Recent decisions | `codex/oracles/delphi/` |

---

*Per the substrate constitution: this file is **required** before the agent does any real work. Write it; commit it; reference it from your code.*
