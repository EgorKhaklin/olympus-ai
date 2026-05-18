"""The Charites — the three Graces, attendants of Aphrodite.

Aglaia (Splendor), Euphrosyne (Good Cheer), and Thalia (Festivity)
served Aphrodite, gracing every gathering with beauty, mirth, and
festivity. In Olympus they handle the small aesthetics that make
output bearable:

  Aglaia       splendor      — terminal banners + accent formatting
  Euphrosyne   good cheer    — friendly error messages
  Thalia       festivity     — docstring + doc-tone helpers
"""

from olympus.graces.aglaia import aglaia
from olympus.graces.euphrosyne import euphrosyne
from olympus.graces.thalia import thalia

__all__ = ["aglaia", "euphrosyne", "thalia"]
