<!--
Olympus PR template. See CONTRIBUTING.md for the shape of a change.
Per S6: every MEDIUM/HIGH-risk change names its Delphi note here.
-->

## Arc / change

<!-- One-line description of what this change is. -->

**Risk class:** LOW / MEDIUM / HIGH / COMPOSITE
**Delphi note:** `codex/oracles/delphi/YYYY-MM-DD-<name>-arc.md`
**Sworn on Styx:** seq=N (or N/A for LOW autonomous)

---

## What ships

<!-- The concrete deliverables. New modules, errands, endpoints, pages, tests.
     Be specific: "src/olympus/runtime/foo.py — does X". -->

## Constitution

| invariant | how this change honors it |
|---|---|
| S1 | … |
| S6 | … |
| S7 | … |

## What does NOT ship this arc

<!-- Explicit deferrals. Operator should not be surprised by what's missing. -->

## Tests

- `tests/test_<arc>.py` — N cases
- Full suite still green: `python3 -m pytest tests/`

## Live demonstration

<!-- A real run — terminal output or a screenshot — that proves the change works.
     Theoretical "should work" is AP7. The substrate is built to refuse it. -->

```
$ invoke <errand>
...
```

## Authorization

<!-- For HIGH-risk: the operator's authorization quote.
     For LOW autonomous: name the proposal id ratified by Zeus. -->
