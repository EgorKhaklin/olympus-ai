# Delphi — replace S8 with Continuity of Understanding

**Risk class:** HIGH (constitutional amendment — substrate invariant change)
**Opened:** 2026-05-18
**Closed:** 2026-05-18
**Decided:** Position A (Continuity of Understanding)
**Authorized by Zeus:**
> _"The current S8 is philosophically strong (Anti-coercion vocation) but it
> is also the single biggest thing preventing Olympus from being a true blank
> slate. … A well-designed replacement (like Operator Optionality or
> Continuity of Understanding) still gives S8 real weight and gives
> Hephaestus/Momus something meaningful to argue about. It just removes the
> hard ideological line."_

---

## Question

The current S8 reads:

> **S8 — Anti-coercion vocation.** Olympus refuses changes that strengthen
> surveillance, centralization, or unbounded retention. Changes that
> strengthen the operator's leverage against coerced behavior are welcomed.

This is the only substrate invariant that takes an ideological stance. A
surveillance-monitoring deployment, an enterprise-compliance agent, or a
corporate-analytics tool cannot honestly adopt Olympus with S8 as written —
they would be claiming a vocation they don't hold.

Replace S8 with a domain-neutral substrate invariant that still has real
structural weight.

---

## Hephaestus's three proposals (recorded in Mnemosyne)

| id | name | statement |
|---|---|---|
| `arch-2026-05-18-2933` | **Continuity of Understanding** | Every load-bearing action must be reconstructible — what was done, why, on whose authority — from the substrate's own records alone. |
| `arch-2026-05-18-1746` | **Operator Optionality** | Every action must preserve the operator's ability to take a different action next. No state is one-way without explicit Zeus authorization. |
| `arch-2026-05-18-4418` | **Vocational Fidelity** | The substrate is bound by whatever vocation the deployment names in DOMAIN.md. Each deployment writes its own line. |

---

## Momus contest

| candidate | Momus dings | Momus passes |
|---|---|---|
| Continuity of Understanding | **(none)** | AP1, AP4, AP6 |
| Operator Optionality | **AP3** (instance-level rule for class-level drift — would refuse legitimate one-way ops like trade execution, file delete, key rotation) | AP1, AP4 |
| Vocational Fidelity | **AP5** (decline-and-surface violation — a vacuous DOMAIN.md leaves S8 vacuous; the substrate has nothing to refuse) | AP4, AP6 |

Continuity of Understanding is the only candidate with zero AP-violations.

---

## Decision

**Position A — Continuity of Understanding.**

### Why this position

- Zero Momus dings — the only candidate that passes the full AP1–AP8 catalog.
- Universal — every operator wants to reconstruct why their agent did what it did.
- Already half-implemented — Mnemosyne (S1) and Styx (S6) provide the substrate;
  S8 makes the meta-claim explicit.
- Domain-neutral — applies to a surveillance tool, a research agent, a
  personal AI, or any deployment without contradiction.
- Generative — Hephaestus has a fresh question for every proposal:
  _"after this change, will the operator be able to reconstruct why?"_
- Composable — does not conflict with any DOMAIN.md vocation.

### New S8 wording (sworn on Styx at commit time)

> **S8 — Continuity of Understanding.** Every load-bearing action the agent
> takes must be reconstructible — what was done, why, and on whose authority —
> from the substrate's own records alone. The substrate refuses changes that
> obscure its own decision-making from the operator.
>
> Enforced by: Mnemosyne discipline (S1) + Styx oath chain (S6) + the
> structural eye `eye_understanding_gap` which surfaces any load-bearing
> decision without a recorded rationale. Hephaestus contests proposals
> that would reduce reconstructability; Momus's new AP6 fires when a
> proposal makes the agent's reasoning harder to follow.

### Knock-on changes (this Delphi authorizes)

1. **`titans/themis.py`** — S8 entry rewritten.
2. **`heroes/momus.py`** — AP6 reframed from "vocation-adjacent silent
   strengthening" to "understanding-obscuring."
3. **`codex/COSMOGONY.md`** — §III S8 rewritten; §V "Vocation"
   reframed: Hestia's vocation slot is preserved as a per-deployment
   commitment, but the substrate no longer prescribes its content.
4. **`README.md`** — S8 row updated; "anti-coercion" mentions removed.
5. **`codex/BESTIARY.md`**, **`codex/RITES.md`**, **`codex/threat-model.md`**,
   **`monsters/typhon.py`** — anti-coercion residue audited and replaced
   with neutral framing where present.
6. **New `monsters/argos/eyes/eye_understanding_gap.py`** — structural
   enforcement of S8 (an Eye that fires when load-bearing Mnemosyne
   memories lack a rationale field).
7. **`tests/test_substrate_invariants.py`** — `test_S8_anticoercion_AP6_exists`
   renamed to `test_S8_continuity_AP6_exists` and updated.

### What is preserved

- The vocation **slot** in Hestia (deployments still name what they're for).
- The full Hephaestus + Momus debate protocol.
- All seven other substrate invariants (S1 through S7).
- The Delphi protocol itself.

### What is removed

- The substrate's stance on surveillance, centralization, and retention.
  Those become **deployment-level** choices in DOMAIN.md, not
  substrate-level constraints.
- The "anti-coercion" framing as an architectural property of Olympus.

---

*Sworn on Styx at this commit. Future amendments to S8 require a new Delphi.*
