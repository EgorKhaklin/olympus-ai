--------------------------- MODULE StyxAppendOnly ---------------------------
(***************************************************************************
 Styx — append-only cryptographic oath chain (S1 in formal form).

 Per Delphi 2026-05-18-labyrinth-arc.md. Demonstrator artifact, not
 maintained verification infrastructure. The value of writing this
 spec is in stating, in mathematics, what the implementation must
 guarantee under concurrent writers.

 What this models:
   - A monotonically-increasing sequence of oaths, each carrying a
     cryptographic hash that chains back to the previous oath
   - Multiple "swearers" attempting to swear concurrently
   - The invariant: the chain remains valid (each oath's prev_hash
     matches the previous oath's self_hash; seq strictly increases)

 What this spec verifies (under TLC):
   - Safety: ∀ i > 0, chain[i].prev_hash = chain[i-1].self_hash
   - Safety: ∀ i > 0, chain[i].seq = chain[i-1].seq + 1
   - Safety: under any interleaving of N concurrent swears, both
     properties continue to hold (concurrency is serialized in the
     implementation via an exclusive file lock — modeled here as an
     atomic Swear action)

 What this spec does NOT verify:
   - The Python implementation of the file lock
   - SHA-256 collision resistance (assumed)
   - Disk durability (assumed)
 ***************************************************************************)
EXTENDS Naturals, Sequences

CONSTANTS
    Swearers,           \* set of identities able to swear oaths
    MaxOaths            \* bound on chain length for finite checking

VARIABLES
    chain,              \* sequence of oath records
    pending             \* set of in-flight swear attempts

vars == <<chain, pending>>

\* A type-correctness invariant.
TypeOK ==
    /\ chain \in Seq([seq: Nat, prev_hash: STRING, self_hash: STRING,
                       sworn_by: Swearers])
    /\ pending \subseteq Swearers

\* Initial state: empty chain, no pending swears.
Init ==
    /\ chain = <<>>
    /\ pending = {}

\* A swearer attempts a swear. (Models the call entering the lock.)
AttemptSwear(s) ==
    /\ s \notin pending
    /\ Len(chain) < MaxOaths
    /\ pending' = pending \cup {s}
    /\ UNCHANGED chain

\* The actual append. Atomic — the file lock serializes this.
\* prev_hash = "GENESIS" if first; otherwise the prior self_hash.
\* self_hash is modeled symbolically as <seq, sworn_by> for the spec.
Swear(s) ==
    /\ s \in pending
    /\ LET prevHash == IF Len(chain) = 0 THEN "GENESIS"
                       ELSE chain[Len(chain)].self_hash
           selfHash == ToString(Len(chain)) \o "-" \o s
       IN chain' = Append(chain, [seq |-> Len(chain),
                                   prev_hash |-> prevHash,
                                   self_hash |-> selfHash,
                                   sworn_by |-> s])
    /\ pending' = pending \ {s}

\* (Helper — TLA+ has no built-in stringify; this is a placeholder.)
ToString(n) == "n"

Next ==
    \E s \in Swearers:
        \/ AttemptSwear(s)
        \/ Swear(s)

Spec == Init /\ [][Next]_vars

------------------------------------------------------------------------------
\* SAFETY PROPERTIES
\* ===========================================================================

\* The chain links are always valid.
ChainLinksValid ==
    \A i \in 2..Len(chain):
        chain[i].prev_hash = chain[i-1].self_hash

\* The sequence numbers are strictly monotonic and dense.
SeqMonotonic ==
    \A i \in 1..Len(chain):
        chain[i].seq = i - 1

\* The full invariant.
Invariant == TypeOK /\ ChainLinksValid /\ SeqMonotonic

------------------------------------------------------------------------------
\* CONFIGURATION FOR TLC
\* ===========================================================================
\* To check:
\*   tlc StyxAppendOnly -config StyxAppendOnly.cfg
\* with config:
\*   SPECIFICATION Spec
\*   INVARIANT Invariant
\*   CONSTANTS Swearers = {s1, s2, s3}  MaxOaths = 4
=============================================================================
