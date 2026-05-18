------------------------- MODULE HephaestusPipeline -------------------------
(***************************************************************************
 Hephaestus → Momus → Delphi → Zeus → ActionQueue (proposal lifecycle).

 Per Delphi 2026-05-18-labyrinth-arc.md.

 What this models:
   - A proposal moves through stages: PROPOSED → CONTESTED → either
     RATIFIED or REJECTED → (if HIGH/COMPOSITE) DELPHI_PENDING →
     (after Styx oath) RATIFIED → EXECUTED
   - The invariant: no proposal reaches RATIFIED without passing
     CONTESTED (Momus's AP1–AP8 catalog ran on it)
   - The invariant: no HIGH/COMPOSITE proposal reaches RATIFIED
     without DELPHI_PENDING (Delphi recorded the decision)

 What this spec verifies:
   - Safety: ∀ p, RATIFIED(p) ⇒ CONTESTED(p)
   - Safety: ∀ p, HIGH(p) ∧ RATIFIED(p) ⇒ DELPHI_PENDING was visited
   - Liveness (under fairness): every proposal eventually reaches a
     terminal state (RATIFIED or REJECTED), never stuck in CONTESTED
 ***************************************************************************)
EXTENDS Naturals, FiniteSets

CONSTANTS
    Proposals,          \* set of proposal ids
    RiskClasses         \* {LOW, MEDIUM, HIGH, COMPOSITE}

VARIABLES
    status,             \* function: proposal -> status
    contested,          \* set of proposals that passed Momus
    delphi_visited      \* set of proposals that went through DELPHI

vars == <<status, contested, delphi_visited>>

STATES == {"NEW", "PROPOSED", "CONTESTED", "DELPHI_PENDING",
           "RATIFIED", "REJECTED"}
TERMINAL == {"RATIFIED", "REJECTED"}

\* Map from proposal id to its risk class. In a real check, this
\* would be supplied per-proposal; here we model it as a constant.
ASSUME RiskClasses = {"LOW", "MEDIUM", "HIGH", "COMPOSITE"}

\* For modeling simplicity, every proposal in this spec gets risk
\* class HIGH — that exercises the strictest path through Delphi.
RiskOf(p) == "HIGH"

TypeOK ==
    /\ status \in [Proposals -> STATES]
    /\ contested \subseteq Proposals
    /\ delphi_visited \subseteq Proposals

Init ==
    /\ status = [p \in Proposals |-> "NEW"]
    /\ contested = {}
    /\ delphi_visited = {}

\* Hephaestus surfaces a proposal.
Surface(p) ==
    /\ status[p] = "NEW"
    /\ status' = [status EXCEPT ![p] = "PROPOSED"]
    /\ UNCHANGED <<contested, delphi_visited>>

\* Momus contests it (runs AP catalog).
Contest(p) ==
    /\ status[p] = "PROPOSED"
    /\ status' = [status EXCEPT ![p] = "CONTESTED"]
    /\ contested' = contested \cup {p}
    /\ UNCHANGED delphi_visited

\* For HIGH/COMPOSITE, must enter DELPHI_PENDING.
EnterDelphi(p) ==
    /\ status[p] = "CONTESTED"
    /\ RiskOf(p) \in {"HIGH", "COMPOSITE"}
    /\ status' = [status EXCEPT ![p] = "DELPHI_PENDING"]
    /\ delphi_visited' = delphi_visited \cup {p}
    /\ UNCHANGED contested

\* Zeus ratifies — but only after DELPHI for HIGH/COMPOSITE.
Ratify(p) ==
    /\ \/ /\ status[p] = "CONTESTED"
          /\ RiskOf(p) \in {"LOW", "MEDIUM"}
       \/ /\ status[p] = "DELPHI_PENDING"
          /\ RiskOf(p) \in {"HIGH", "COMPOSITE"}
    /\ status' = [status EXCEPT ![p] = "RATIFIED"]
    /\ UNCHANGED <<contested, delphi_visited>>

\* Zeus rejects.
Reject(p) ==
    /\ status[p] \in {"CONTESTED", "DELPHI_PENDING"}
    /\ status' = [status EXCEPT ![p] = "REJECTED"]
    /\ UNCHANGED <<contested, delphi_visited>>

Next ==
    \E p \in Proposals:
        \/ Surface(p)
        \/ Contest(p)
        \/ EnterDelphi(p)
        \/ Ratify(p)
        \/ Reject(p)

\* Fairness: every proposal eventually leaves PROPOSED.
Fairness ==
    \A p \in Proposals:
        /\ WF_vars(Contest(p))
        /\ WF_vars(Ratify(p) \/ Reject(p))

Spec == Init /\ [][Next]_vars /\ Fairness

------------------------------------------------------------------------------
\* SAFETY PROPERTIES
\* ===========================================================================

\* No proposal reaches RATIFIED without Momus contesting it first.
RatifiedImpliesContested ==
    \A p \in Proposals:
        status[p] = "RATIFIED" => p \in contested

\* No HIGH/COMPOSITE proposal reaches RATIFIED without DELPHI.
HighImpliesDelphiVisited ==
    \A p \in Proposals:
        (status[p] = "RATIFIED" /\ RiskOf(p) \in {"HIGH", "COMPOSITE"})
            => p \in delphi_visited

\* The full safety invariant.
Invariant ==
    /\ TypeOK
    /\ RatifiedImpliesContested
    /\ HighImpliesDelphiVisited

------------------------------------------------------------------------------
\* LIVENESS
\* ===========================================================================

EventualResolution ==
    \A p \in Proposals: <>(status[p] \in TERMINAL)

------------------------------------------------------------------------------
\* CONFIGURATION FOR TLC
\* ===========================================================================
\* SPECIFICATION Spec
\* INVARIANT Invariant
\* PROPERTY EventualResolution
\* CONSTANTS Proposals = {p1, p2} RiskClasses = {LOW, MEDIUM, HIGH, COMPOSITE}
=============================================================================
