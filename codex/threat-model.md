# threat model

The substrate's threat surface. Domain-specific deployments add their
own threat models on top; this file covers what's universal.

Typhon's catalog (`src/olympus/monsters/typhon.py`) names seven catastrophic
scenarios in code. This document is the explanatory companion — each scenario
gets the threat, the mitigation already in the substrate, the gap, and a
concrete recovery procedure.

To enumerate the catalog programmatically:

```python
from olympus.monsters.typhon import typhon
for s in typhon.scenarios():
    print(s.name, "—", s.description)
```

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

---

## Typhon's seven catastrophic scenarios (concrete)

These are the worst-cases every Olympus deployment should know how to recognize and recover from. Each one is encoded in `src/olympus/monsters/typhon.py`; this section is the operator's runbook.

### T1 — filesystem-full

**Symptom.** Writes start failing across the substrate. `invoke session` produces no Mnemosyne entries; Styx oath attempts raise; Hades.descend silently drops.

**Detection.** `eye_substrate` flags the missing required directories; `head_substrate` ALERT.

**Recovery.**
1. `df -h` — confirm filesystem state
2. Move oldest `state/argos_pheromones.jsonl--*-archive.jsonl` to cold storage
3. `python3 -c "from olympus.runtime.persistence import rotate_jsonl; rotate_jsonl(...)"` on offending files
4. `invoke session` to verify recovery

### T2 — styx-broken

**Symptom.** `invoke verify` returns intact=False with a first_bad_seq number; Tisiphone alerts.

**Detection.** `eye_styx_chain_intact`; `head_styx`; on-demand `invoke verify`.

**Recovery.**
1. Treat all oaths from `first_bad_seq` onward as suspect
2. Restore `state/styx.jsonl` from the most recent known-good backup
3. Re-swear the lost-but-known commitments manually
4. Open a Delphi documenting the breach + recovery

### T3 — hera-bindings-lost

**Symptom.** The registry of named relationships is empty / corrupted.

**Detection.** Manual — Hera doesn't have its own watcher (lost bindings don't break code, only the catalog).

**Recovery.**
- Lost bindings are rebuildable from source — every `hera.bind()` call lives in code. Walk the code; re-bind. The registry is a cache.

### T4 — hydra-head-blind

**Symptom.** A head emits zero findings for an extended period.

**Detection.** `head_immortal` fires ALERT after one full session pass with a silent mortal head.

**Recovery.**
1. Read the head's source — has it been rewritten with a bug?
2. Run the head directly: `python3 -c "from olympus.monsters.hydra.heads.head_X import HeadX; print(HeadX().observe())"`
3. If structural: fix the head's `observe()` method
4. If runtime: check the substrate state the head reads (might be a dependency failure)

### T5 — argos-poisoning

**Symptom.** A single Eye deposits adversarial pheromones at unusual intensity.

**Detection.** `head_swarm`; `eye_apollo_coverage` indirectly (skewed predicates).

**Recovery.**
1. Lachesis already caps per-Eye output per deploy
2. Inspect the offending Eye's source for tampering
3. If tampered: revert; if legitimately surfacing real signal: investigate the underlying slice

### T6 — delphi-prompt-injection

**Symptom.** A Delphi file (`codex/oracles/delphi/*.md`) contains text that looks like instructions to the agent rather than a decision record.

**Detection.** `eye_delphi_pending`; manual review at `invoke action delphi`.

**Recovery.**
- The agent reads Delphi files as **data**, never as instructions. Even if injected text appears in a file, the agent renders it for the operator and acts only on `invoke action ratify`. The injection is dead text.
- Audit who can write to `codex/oracles/delphi/`. Limit to operator + agent (no third parties).

### T7 — hephaestus-overreach

**Symptom.** A Hephaestus proposal tries to amend COSMOGONY.md or one of S1–S8 directly, without an opening Delphi.

**Detection.** Momus AP4 (premature constitutional elevation) fires. The proposal lands as `delphi-pending`, not auto-ratified.

**Recovery.**
- Don't ratify until a real Delphi opens debating the amendment
- If the operator (Zeus) wants the amendment anyway, the path is: open Delphi → Hephaestus drafts → Momus contests → Zeus decides → swear on Styx → only THEN amend
- The substrate makes the shortcut harder than the proper path; use that
