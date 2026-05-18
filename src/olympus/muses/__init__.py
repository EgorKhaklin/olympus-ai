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

from olympus.muses.calliope import calliope
from olympus.muses.clio import clio
from olympus.muses.erato import erato
from olympus.muses.euterpe import euterpe
from olympus.muses.melpomene import melpomene
from olympus.muses.polyhymnia import polyhymnia
from olympus.muses.terpsichore import terpsichore
from olympus.muses.thalia_muse import thalia_muse
from olympus.muses.urania import urania

__all__ = [
    "calliope", "clio", "erato", "euterpe", "melpomene",
    "polyhymnia", "terpsichore", "thalia_muse", "urania",
]
