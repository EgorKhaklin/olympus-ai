# Security

Olympus's security model lives at two layers — the substrate
(this file) and the deployment (each deployment's own SECURITY.md).

## Substrate threat model

See `bestiary/threats.md` for the substrate's threat model. Typhon's
catalog (`monsters/typhon.py`) enumerates the catastrophic scenarios
every deployment should prepare for.

## Reporting a substrate vulnerability

If you find a way to bypass the substrate invariants S1–S8
(see COSMOGONY.md), email Egor Khaklin privately rather than opening
a public issue.

## Constitutional anchors

These cannot be amended without a HIGH-risk Delphi:

- The pantheon hierarchy
- Substrate invariants S1–S8
- Substrate invariant S8 (Continuity of Understanding)
- The risk-class definitions (LOW / MEDIUM / HIGH / COMPOSITE)

A pull request that tries to amend any of these without an
accompanying Delphi will be refused.
