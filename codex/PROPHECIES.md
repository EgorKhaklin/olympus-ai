<div align="center">

# ⚡ PROPHECIES ⚡

**what Apollo has foreseen — the backlog**

</div>

---

Apollo is god of prophecy. Each item here is a *prediction* about a change Olympus will eventually want: a foreseen direction, with a risk class and a trigger that would make it real.

A prophecy is not a commitment. It is a structured guess. Hephaestus may propose any of these at any time; Momus will contest; Zeus will decide.

---

## ⚡ Imminent prophecies — Phase 1

Foreseen for the first cycles of operation.

| | prophecy | risk | trigger |
|-:|----------|:----:|---------|
| **P1** | `DOMAIN.md` is written, naming the deployment's vocation and C-class invariants | LOW | first session |
| **P2** | First Delphi opens (`initial-vocation-naming`) | MEDIUM | when DOMAIN.md exceeds 30 lines |
| **P3** | At least one domain-specific Eye registers in `monsters/argos/eyes/` | LOW | first observable signal in the domain |
| **P4** | At least one domain-specific HYDRA Head registers in `monsters/hydra/heads/` | LOW | first structural drift signal |
| **P5** | First Apollo predicate (`olympians/apollo/`) is composed with a `verify()` callable | MEDIUM | first claim worth checking |

---

## ⚡ Middle prophecies — Phase 2

Foreseen after the substrate has been exercised against a real domain for several cycles.

| | prophecy | risk | trigger |
|-:|----------|:----:|---------|
| **P6** | Heracles's twelve labors are filled in for the deployment | MEDIUM | first kill-test run; current labors are placeholders |
| **P7** | Atalanta benchmarks the hot path | LOW | first observed latency complaint |
| **P8** | Persephone cycles register at least one rotating resource | MEDIUM | first secret / token / session subject to rotation |
| **P9** | Cerberus posts at least one gate (auth + authz + integrity) | MEDIUM | first cross-boundary call needs gating |
| **P10** | Typhon scenarios are exercised by Ares quarterly | MEDIUM | quarterly cadence |

---

## ⚡ Distant prophecies — Phase 3

Foreseen for advanced deployments that scale Olympus beyond a single agent.

| | prophecy | risk | trigger |
|-:|----------|:----:|---------|
| **P11** | Multi-deployment federation — Hera tracks bindings across Olympus instances | HIGH | second deployment goes live |
| **P12** | Apollo predicates achieve empirical graduation (50% accepted over six distinct months, or sunset) | HIGH | first six-month evaluation window closes |
| **P13** | The brain-map (Urania) renders as an interactive D3 force graph | LOW | operator requests visual nav |
| **P14** | The Sphinx posts riddles for high-stakes ops (challenge-response auth) | MEDIUM | first deployment needs human-in-the-loop confirmation |
| **P15** | Hecate's at-crossroads is used everywhere with retry-able operations | LOW | as operations are added |

---

## Held in reserve — refused for now

These prophecies have been considered and explicitly declined. They are named here so that future agents do not waste cycles re-proposing them.

| prophecy | why refused | trigger that would unfreeze it |
|----------|-------------|--------------------------------|
| Pan-Olympus message bus across machines | premature; Poseidon's in-memory pub/sub suffices for now | when a second machine actually needs to subscribe |
| Vendor-specific LLM bindings in the substrate | violates the LLM-agnostic constraint | never — domain deployments add their own |
| Persistent state replacing per-deployment storage | violates S4 decentralization | only after a Delphi explicitly amends S4 |
| Olympus-as-a-service hosted offering | violates the operator-served clause | never under the current vocation |

---

## How a prophecy becomes real

```
prophecy → Hephaestus proposal → Momus contest → Zeus decision → Delphi closed → shipped
```

The Delphi closure swears the change on Styx; the CHRONICLE entry records what shipped; the journal records the human side of it.

---

<div align="center">

*"Prophecies do not bind the future. They name it, so the future cannot pretend to be a surprise."*

</div>
