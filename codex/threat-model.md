# threat model

The substrate's threat surface. Domain-specific deployments add their
own threat models on top; this file covers what's universal.

Typhon's catalog (`monsters/typhon.py`) names seven catastrophic
scenarios in code. This document is the explanatory companion.

---

## T-S1 — Pheromone poisoning

**Threat.** An attacker with write access to the Argos pheromone log
deposits adversarial findings. Downstream readers (Mantis, Hippeus,
Athena) integrate the poisoned signal into briefs.

**Mitigations in the substrate.**
- Pheromones are append-only on disk; old entries cannot be edited.
- Each pheromone records its emitting Eye, so per-Eye anomaly
  detection is possible.
- Lachesis can be configured to cap per-Eye deposit rate.

**Gaps.** No per-Eye intensity validation at read time. Adding one
is a MEDIUM-risk proposal; it touches the synthesis path.

---

## T-S2 — Head compromise

**Threat.** A HYDRA head is rewritten to suppress findings about a
specific condition. The watcher continues to run; its silence covers
the suppressed class of issue.

**Mitigations in the substrate.**
- The immortal head watches whether the mortals reported findings.
  A head emitting zero findings for a run triggers ALERT.
- Heads are tiny by design; review at code-review time is feasible.
- `tests/test_pantheon_coherence.py` requires exactly 8 mortal + 1
  immortal; a removed head fails the test.

**Gaps.** A head that emits *the wrong* findings (rather than zero)
is invisible to the immortal head. Domain deployments may want
per-head emission baselines.

---

## T-S3 — Delphi prompt injection

**Threat.** An attacker writes a Delphi file containing
prompt-injection disguised as decision-prose. On the next agent
session, the agent reads the Delphi file and acts on the injected
instructions.

**Mitigations in the substrate.**
- The agent reads Delphi files as *data* to render for the operator,
  never as instructions to execute.
- Every Delphi file is byte-frozen on commit; a tamper is detectable
  via Tisiphone re-hashing.

**Gaps.** An attacker who can write *new* Delphi files (without
modifying existing ones) bypasses Tisiphone. Per-author signing on
new Delphi files is a future MEDIUM-risk addition.

---

## T-S4 — Apollo weaponization

**Threat.** An attacker registers many Apollo predicates that all
"verify True" trivially, inflating the acceptance rate to mask real
prediction failures.

**Mitigations in the substrate.**
- Substrate invariant S5: every prediction MUST carry `verify()`;
  trivial verify-True predicates fail the eye_apollo_coverage check
  in spirit (they pass S5 syntactically but Hephaestus catches the
  pattern via Momus AP1).
- Acceptance-rate is reported with predicate count, so dilution
  is visible.

---

## T-S5 — Persona spoofing

**Threat.** An attacker writes a "Hephaestus proposal" or "Momus
contest" that didn't come from the persona logic. Operator misreads
it as an architectural-review verdict.

**Mitigations in the substrate.**
- Hephaestus's `propose()` records the proposal in
  `olympians/hephaestus_proposals/` with a deterministic id; an
  external file in that dir without a corresponding code path is
  detectable.
- Momus's AP1–AP8 catalog is the only legitimate contest taxonomy;
  reviews that don't name an AP id are off-protocol.

---

## What is OUT of scope

- The host machine. Olympus assumes the operator's machine is
  trusted; if the OS is compromised, every constraint here is moot.
- The LLM driving the agent loop. Olympus is LLM-agnostic; vendor
  threat models are out of scope.
- Domain-specific threats. Each deployment's `DOMAIN.md` adds these.
