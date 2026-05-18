"""The Nine Muses — daughters of Mnemosyne and Zeus.

The Muses inspire the arts. In Olympus they govern the nine kinds of
recorded artifact — each Muse a specific kind of remembering.

  Calliope       epic poetry        — long-form narrative docs (codex/)
  Clio           history            — the chronicle / journal
  Erato          love poetry        — warm user-facing prose
  Euterpe        music              — pheromone rhythms / cadence
  Melpomene      tragedy            — post-mortems / failure analyses
  Polyhymnia     sacred hymns       — constitutional / oath records
  Terpsichore    dance              — choreography (cron schedules)
  Thalia         comedy             — casual notes / banter
  Urania         astronomy          — the brain-map (celestial chart)

Each Muse module knows how to read its own kind of artifact.
"""

from muses.calliope import calliope
from muses.clio import clio
from muses.erato import erato
from muses.euterpe import euterpe
from muses.melpomene import melpomene
from muses.polyhymnia import polyhymnia
from muses.terpsichore import terpsichore
from muses.thalia_muse import thalia_muse
from muses.urania import urania

__all__ = [
    "calliope", "clio", "erato", "euterpe", "melpomene",
    "polyhymnia", "terpsichore", "thalia_muse", "urania",
]
