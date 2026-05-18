"""The Erinyes — the three Furies, punishers of broken oaths.

Alecto, Megaera, and Tisiphone hunt down those who break sacred oaths
or commit unnatural crimes. They are older than the Olympians and
answer to no one. In Olympus they enforce specific kinds of violation:

  Alecto      unceasing anger      — CI / invariant-failure alerter
  Megaera     jealousy / envy      — concurrency-violation detector
  Tisiphone   avenger of murder    — data-integrity enforcer

A Fury that fires cannot be ignored. They report to Themis.
"""

from furies.alecto import alecto
from furies.megaera import megaera
from furies.tisiphone import tisiphone

__all__ = ["alecto", "megaera", "tisiphone"]
