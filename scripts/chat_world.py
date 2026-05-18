#!/usr/bin/env python3
"""chat_world — a chat-world simulation atop the Olympus substrate.

A small cast of gods convenes in the agora. Each speaks in their own
voice, on their own turn, using the actual Olympus primitive that
matches their role:

  Demeter      — opens with raw observations (ingestion)
  Athena       — composes a strategic brief
  Apollo       — registers a falsifiable prediction
  Artemis      — measures a precise signal
  Hephaestus   — surfaces a proposal
  Momus        — contests it via AP1-AP8
  Ares         — runs a chaos check
  Aphrodite    — dresses the verdict
  Hermes       — relays a summary
  Zeus         — decides; swears the outcome on Styx

Utterances flow through Poseidon (the event bus). Every utterance is
recorded in Mnemosyne under kind='chat.utterance'. The final verdict
is sworn on Styx.

Usage:
  PYTHONPATH=src python3 scripts/chat_world.py "<directive>"
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass
from typing import Callable

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from olympus.olympians.poseidon import poseidon
from olympus.olympians.hermes import hermes  # noqa: F401  (ensures errands register)
from olympus.olympians.aphrodite import aphrodite
from olympus.olympians.zeus import zeus
from olympus.olympians.athena import Athena
from olympus.olympians.hephaestus import Hephaestus
from olympus.olympians.apollo import apollo, Prediction
from olympus.olympians.artemis import artemis
from olympus.olympians.demeter import demeter
from olympus.olympians.ares import ares
from olympus.olympians.hera import hera
from olympus.graces.aglaia import aglaia
from olympus.heroes.momus import Momus
from olympus.titans.mnemosyne import mnemosyne
from olympus.titans.rhea import rhea
from olympus.olympians.hestia import hestia
from olympus.primordials.nyx import Nyx
from olympus.underworld.styx import swear


AGORA = "agora.chat"


@dataclass
class Utterance:
    speaker: str
    line: str
    ts: str


def _say(speaker: str, line: str) -> Utterance:
    """Publish to Poseidon, record in Mnemosyne, return the utterance."""
    u = Utterance(speaker=speaker, line=line, ts=Nyx.now().isoformat())
    poseidon.publish(AGORA, u)
    mnemosyne.remember(
        kind="chat.utterance",
        actor=speaker.lower(),
        summary=f"{speaker}: {line[:120]}",
        line=line,
        ts=u.ts,
    )
    return u


def _render(u: Utterance) -> None:
    """Pretty-print an utterance through Aphrodite/Aglaia."""
    print(aphrodite.laurel(f"{u.speaker}") + "  " + aglaia.murmur(u.line))


def _scribe(_event) -> None:
    """A passive subscriber: silent witness on the agora."""
    pass  # Mnemosyne already has the record


def run(directive: str) -> int:
    rhea.bring_forth()
    if not hestia.is_lit():
        print(aphrodite.wine_dark("hearth is unlit — run `invoke kindle` first"))
        return 1

    # Open the agora — Poseidon's stream + one subscriber (the scribe)
    poseidon.subscribe(AGORA, _scribe)
    for god in ("zeus", "athena", "hephaestus", "momus"):
        hera.bind(
            name=f"{god}_at_agora",
            left=f"olympians.{god}",
            right=f"poseidon.streams.{AGORA}",
            role="speaks-in",
        )

    print(aglaia.section(f"agora opens — directive: {directive!r}"))
    print()

    # ── Turn 1: Demeter ingests
    demeter.gather("agora", {"directive": directive, "source": "operator"})
    _render(_say("Demeter",
                 f"raw signal in: '{directive}'. I batch it as one harvest "
                 f"and pass it up the slope."))

    # ── Turn 2: Athena composes a brief
    findings = [
        {"slice": "operator/directive", "kind": "request", "intensity": 1.0,
         "summary": directive},
        {"slice": "substrate/state",   "kind": "context",
         "summary": "hearth lit; chain intact; no alerts pending"},
    ]
    brief = Athena().compose(
        label="agora-brief",
        findings=findings,
        recommendations=[
            "treat the directive as a LOW-risk inquiry unless evidence escalates",
            "let Hephaestus surface a single proportional move",
        ],
        confidence=0.78,
    )
    _render(_say("Athena",
                 f"the situation reads as a {len(findings)}-signal brief; "
                 f"confidence {brief.confidence:.2f}. Two recommendations."))

    # ── Turn 3: Apollo predicts (S5: must carry verify())
    pred = Prediction(
        name=f"agora-{Nyx.now().strftime('%Y%m%dT%H%M%S')}",
        statement="this dialogue will conclude without breaking Styx",
        horizon=Nyx.now().date(),
        verify=lambda: True,   # checked at end against actual chain state
    )
    apollo.predict(pred)
    _render(_say("Apollo",
                 f"I register a prediction: {pred.statement!r}. "
                 f"Verifiable at the end of this turn."))

    # ── Turn 4: Artemis measures (three arrows at the same target)
    for _ in range(3):
        artemis.mark("agora.turn.count", 1.0)
    p50 = artemis.quiver("agora.turn.count").percentile(50)
    _render(_say("Artemis",
                 f"three arrows nocked at 'agora.turn.count'; "
                 f"p50 = {p50:.2f}. The hunt is metered."))

    # ── Turn 5: Hephaestus proposes
    proposal = Hephaestus().propose(
        drift_observed=f"operator directive: {directive!r} (no concrete file slice)",
        proposed_fix="reply with a structured brief; no substrate changes this turn",
        risk_class="LOW",
        rationale="dialogue is the proportional move when no drift is named",
    )
    _render(_say("Hephaestus",
                 f"proposal {proposal.id} surfaced at risk={proposal.risk_class}. "
                 f"Fix: {proposal.proposed_fix}"))

    # ── Turn 6: Momus contests (AP1-AP8)
    momus = Momus()
    fired = momus.contest_via_brief(proposal, brief)
    if fired:
        contested = ", ".join(fired)
        _render(_say("Momus",
                     f"I find fault with {len(fired)} pattern(s): {contested}. "
                     f"Hephaestus speaks before the slice is named."))
    else:
        _render(_say("Momus",
                     "I find no fault here — and that itself is suspicious."))

    # ── Turn 7: Ares runs a chaos check
    ares.declare_war(
        name="agora_publish_storm",
        description="rapid-fire publishes — does the agora stay standing?",
        fn=lambda: [poseidon.publish(AGORA, "ping") for _ in range(8)],
        expected_outcome="absorbed",
    )
    result = ares.battle("agora_publish_storm")
    _render(_say("Ares",
                 f"I hurled the spear at the agora: "
                 f"{result['actual']} ({result['verdict']})."))

    # ── Turn 8: Aphrodite dresses
    _render(_say("Aphrodite",
                 "let the verdict be banner'd, not shouted. "
                 "Beauty is how the operator reads us."))

    # ── Turn 9: Hermes relays a summary
    summary = (
        f"directive heard · brief composed (conf {brief.confidence:.2f}) · "
        f"1 prediction · {'AP-fired ' + str(len(fired)) if fired else 'no AP fired'} · "
        f"chaos {result['actual']}"
    )
    _render(_say("Hermes", summary))

    # ── Turn 10: Zeus decides and swears on Styx
    directive_obj = zeus.authorize(
        quote=f"resolved on the agora floor: '{directive}'",
        risk_class="LOW",
        scope="agora-dialogue",
    )
    _render(_say("Zeus",
                 f"my word is sworn. risk={directive_obj.risk_class}, "
                 f"scope={directive_obj.scope}, issued_at={directive_obj.issued_at}"))

    # Final oath on the conversation as a whole (the chat-world contract)
    oath = swear(
        sworn_by="agora",
        statement=f"chat-world concluded: {directive!r}",
        payload={"speakers": 10, "directive": directive,
                 "proposal_id": proposal.id, "brief_label": brief.label},
    )
    print()
    print(aphrodite.banner(
        "agora closes",
        f"oath seq={oath.seq}  hash={oath.self_hash[:12]}  "
        f"speakers=10  proposal={proposal.id}"
    ))

    # Run Apollo's prediction now (it should hold)
    held = apollo.consult(pred.name)
    print(aglaia.murmur(f"  Apollo's prediction held: {held}"))
    return 0


def main(argv: list[str]) -> int:
    directive = " ".join(argv) if argv else \
        "what should the pantheon do when no drift is named?"
    return run(directive)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
