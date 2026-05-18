"""Apollo — god of prophecy.

The foresight surface: falsifiable predicates about the future state
of the substrate or its domain. Each predicate carries a `verify()`
callable that can be checked when the predicted moment arrives.

This module is deliberately small. Apollo predicts; he does not
fetch external data and does not call any LLM. Predictions are
deterministic over the substrate's own state plus an explicit input.
"""

from olympians.apollo.oracle import Apollo, apollo, Prediction
from olympians.apollo.brief import Brief, render_brief

__all__ = ["Apollo", "apollo", "Prediction", "Brief", "render_brief"]
