# meta/delphi-index.md — chronological index of Delphi sessions

Maintained by `scripts/oly-delphi.sh close`. Newest first.

A **Delphi** (the strategic-decision protocol) is the strategic-decision
protocol. Hephaestus drafts the position; Momus contests it; Zeus
decides; the decision is byte-frozen as an audit-of-record entry.

See [`meta/delphi-protocol.md`](delphi-protocol.md) for the full
protocol spec.

---

## Active decisions

*(empty at v0.1 fork-time — see CHANGELOG.md v0.1 for the
fork-authorization decision, which was pre-authorized in chat and
not routed through Delphi)*

---

## How to add an entry

When closing a Delphi:

```bash
./scripts/oly-delphi.sh close <topic> --position <A|B|C|...> \
    --decision "<one-sentence summary of what was decided>"
```

The script appends a row at the top of this file in the format:

```markdown
- **YYYY-MM-DD** — [topic-name](../delphi/YYYY-MM-DD-topic-name.md) —
  **DECIDED + SHIPPED** (vX.Y), <risk-class>. Position <X> chosen
  because <one-sentence rationale>. Authorized by Zeus
  ("<authorization-quote-if-any>").
```

---

## Decisions held in reserve (no Delphi opened yet)

- *(empty at v0.1; Olympus had multiple deferred-arc entries here,
  but those were Olympus-domain. Add your deployment's deferred
  decisions as they're declined)*

---

*Per Olympus v0.1: the decision archive starts empty. The first
Delphi a deployment opens should be `initial-vocation-naming` —
naming what THIS Olympus is FOR (which then becomes the seed for
`DOMAIN.md`).*
