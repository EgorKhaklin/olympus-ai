"""olympians.apollo — minimum-viable foresight surface ().

Per [`delphi/2026-05-15-olympus-odyssey-debate.md`](../delphi/2026-05-15-olympus-odyssey-debate.md)
Position B (joint architect + momus recommendation).

This package is **deliberately small**. It ships the foresight
*function*, not the foresight *subsystem*. If the empirical-graduation
rule (50% acceptance over 6 monthly briefs) is met, a future Delphi
may extract this into a real subsystem. Until that threshold is met,
the function lives here as a single agent + small support modules.

**Sunset clause (operationally enforced):** if after 6 monthly briefs
the FS-XXXXXXXX acceptance rate is < 50%, every subsequent brief
prefaces with a "SUNSET TRIGGERED" warning recommending removal. The
script does not auto-remove (operator decides), but the dishonesty of
maintaining unused infrastructure becomes visible.

Module layout:
  - oracle.py: the Oracle (one type, not four)
  - brief.py: Brief dataclass + 5-section render
  - promotion.py: FS-XXXXXXXX auto-promotion to ROADMAP.md
  - external_categories.txt: operator-curated external-category list
  - _acceptance_log.json: empirical-graduation tracker

CLI: `bash scripts/oly-apollo.sh` (operator-installed; not cron-auto).

Vocation alignment is structural: §IV of every brief must surface
anti-coercion-aligned candidates. The agent enforces this; if the
brief contains zero anti-coercion-aligned candidates across two
consecutive briefs, the agent emits a corrective Delphi-recommendation.
"""

__version__ = "9.12"

from olympians.apollo.brief import Brief, BriefSection, render_brief
from olympians.apollo.oracle import Oracle
from olympians.apollo.promotion import (
    promote_foresight_candidates,
    stable_foresight_id,
    PromotionResult,
)

__all__ = [
    "Brief",
    "BriefSection",
    "Oracle",
    "promote_foresight_candidates",
    "stable_foresight_id",
    "PromotionResult",
    "render_brief",
]
