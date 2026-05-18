# Delphi — the substance arc

**Risk class:** COMPOSITE
**Opened + closed:** 2026-05-18
**Decided:** Position A — history-aware reasoning across all gods
**Sworn on Styx at seq=37.**

---

## Question

Zeus's critique, verbatim:

> *"Right now it reads as a very well-designed constitutional framework more than a running cognitive engine. The scaffolding, naming, and philosophical grounding are strong. The actual execution of the gods (how Athena synthesizes in practice, how HYDRA/Argos create useful emergence, how prophecy becomes operational) will determine whether this becomes substance or stays beautiful architecture.*
>
> *The risk with this style of project is that the mapping itself becomes the product. The mythology has to justify its overhead by producing clearer thinking and better behavior than simpler named components would."*

How does Olympus prove its mythology earns the overhead — not by adding more components, not by hiring an LLM to look smart, but by producing thinking a flat naming convention wouldn't?

## Three candidates

| id | shape | Momus dings |
|---|---|---|
| `arch-2026-05-18-6573` | **History-aware reasoning** — Athena reads Mnemosyne; Apollo consults due predictions; Hephaestus reads rejections; Furies fire in the loop; sessions surface deltas; new `invoke wisdom` | **(none)** |
| `arch-2026-05-18-3967` | LLM-injected synthesis — call an LLM from Athena | AP6 (understanding-obscuring) + AP1 (no ground-touch) |
| `arch-2026-05-18-6493` | More eyes + heads — scale solves it | AP8 (decorative) + AP3 (instance-vs-class) |

History-aware is the only zero-ding answer.

## Decision

**Position A.** The substrate earns its overhead by READING ITS OWN RECORD as a first-class operation.

### What lands

1. **Athena.compose_from** now pulls the last N `session.completed` memories. Surfaces:
   - **recurring** slices — alerted in ≥3 of last 7 sessions
   - **newly alerted** slices — alerted this session but not in the prior 5
   - **resolved** slices — alerted in the prior session, not this one
   - **stable** slices — INFO for ≥5 sessions
   - A new `insights` field on `Brief` carrying concrete cross-session claims

2. **Apollo.consult_due()** auto-verifies predictions whose horizon has passed; records outcomes in Mnemosyne; updates `acceptance_rate`. Sessions call this at start. Apollo predictions become operational, not just declarative.

3. **Hephaestus.surface_from** reads recent `action.rejected` memories. Refuses to re-propose a drift Zeus rejected in the last 7 days. After 3 rejections of the same drift, emits a "proposal-fatigue" signal — the agent stops nagging.

4. **The Furies fire in the loop.** Tisiphone verifies Styx at session start; if broken, Alecto raises ALERT immediately. Megaera reports per-session lock contention. The Furies are no longer decorative — they are part of every pass.

5. **SessionReport.deltas** — every session compares to the prior session:
   - new alerts that weren't there
   - resolved alerts
   - intensity-trend per slice
   - new vs repeated proposals
   The verbose render surfaces deltas above the static phase output.

6. **`invoke wisdom`** — new CLI command. Reads Mnemosyne and surfaces concrete patterns:
   - "slice X alerted in N of last M sessions; no proposal stuck"
   - "Apollo prediction Y verified true in 4/5 horizons; acceptance rising"
   - "Hephaestus has proposed Z three times; Zeus rejected each time"
   The substrate explains what it has learned.

### Why this proves the mythology earns its overhead

A flat naming convention (`ObservationCorrelator → DecisionAuditEngine → PredicateRegistry`) could implement the same logic. But:

- **Mnemosyne is named** as "memory" — so when we say "Athena reads Mnemosyne," we mean exactly the right thing: synthesis reaches into the agent's memory, the way reasoning reaches into recollection. The name does work the abstraction wouldn't.
- **Hephaestus reads rejections** is exactly the right idiom for "the architect learns what Zeus killed." A "RejectionMemoryLogger" wouldn't make the loop legible.
- **The Furies fire** when oaths break — the catalog (Alecto/Megaera/Tisiphone) covers three distinct violation types each with a separate persona. A flat `InvariantViolationHandler` would either be a single handler (less specific) or three subclasses (the same shape, less memorable).

The mythology compresses the API. The API would exist anyway; the names make it legible across sessions and contributors.

### Refused

- **LLM in synthesis** — would obscure decision-making (AP6) and break the deterministic-substrate claim (S2). Olympus is LLM-agnostic by design.
- **More observers** — doesn't address the class-level problem.

---

*Sworn on Styx at seq=37. The mythology proves itself by reading its own record.*
