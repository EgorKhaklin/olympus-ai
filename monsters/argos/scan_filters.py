"""scan_filters — canonical "is this a Olympus source file" predicate.

 / (legacy wave) / B1+B2 — Delphi referenced:
`meta/olympus-self-roadmap-2026-05-14.md` items B1 + B2.

Pre-, every ant walker decided independently what to skip.
The conventions matched on `__pycache__` + `__init__.py` +
`conftest.py` but `venv/` and `site-packages/` were systematically
forgotten. The macro-to-micro scan caught the impact:

  - ant_test_gap:    708 venv-noise / 17 real-signal (97.7% pollution)
  - ant_todo_debt:   96 venv-noise / 6 real-signal (94% pollution)
  - ant_recent_churn: 28 venv / 23 real (55%)
  - ant_changelog_gap: 9 venv / 22 real (29%)
  - + 7 other eyes/phalanxs with the same blind spot

The whole substrate was ~800+ noise pheromones a day from venv
walks. Correlations and brief-archive accumulated noise. ActionQueue
ranked noise.

This module is the single source of truth for "what counts as
Olympus source code". Every ant walker that does `rglob("*.py")` or
`os.walk()` over `olympus_*` dirs MUST import + use these helpers.

The structural invariant `test_no_ant_scans_venv_files` reads live
Pheromone deposits + asserts none have node_id matching `*venv*` or
`*site-packages*`.

Constitutional contract:
  - G1 (deterministic): pure function on the path string
  - G3 (read-only): no side effects
  - G16 (pure-function): same input → same output
"""

from __future__ import annotations

import pathlib
from typing import Iterable


# Directory names that, when present anywhere in a path's parts, mean
# "skip this entire subtree". Includes:
#
#   - venv               — Python virtual environments at the repo root
#                          (olympus_web/venv/) or anywhere else
#   - .venv              — alternate venv naming convention
#   - site-packages      — pip-installed dependency code
#   - __pycache__        — Python bytecode cache
#   - .git               — git internals
#   - .github/workflows  — CI definitions, scanned separately
#   - target             — Rust build artifacts (olympus_zk/target/)
#   - node_modules       — npm dependencies (none today, but defensive)
#   - .DS_Store          — macOS finder noise
#   - .pytest_cache      — pytest cache
#   - .mypy_cache        — mypy cache
#   - .ruff_cache        — ruff cache
#   - dist, build        — Python packaging artifacts
#   - coverage_html      — coverage report output
#   - htmlcov            — alternate coverage output dir
SKIP_DIR_NAMES: frozenset[str] = frozenset({
    "venv",
    ".venv",
    "site-packages",
    "__pycache__",
    ".git",
    "target",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "coverage_html",
    "htmlcov",
})


# File names to skip even within Olympus directories. These are
# legitimate parts of the project structure but not "modules" in the
# sense the test_gap / todo_debt / changelog_gap ants care about.
SKIP_FILE_NAMES: frozenset[str] = frozenset({
    "__init__.py",
    "conftest.py",
    ".DS_Store",
})


def is_olympus_source(path: pathlib.Path) -> bool:
    """True iff `path` is real Olympus source code that ant walkers
    should consider.

    Returns False for:
      - Any path under venv/ / .venv/ / site-packages/ / __pycache__/
        / .git/ / target/ / node_modules/ / build artifacts
      - __init__.py / conftest.py / .DS_Store at any level
      - Anything where SKIP_DIR_NAMES intersects path.parts

    The check is conservative: if the path looks like it MIGHT be
    venv (e.g., a vendored copy of a library at `vendor/foo/`), it's
    NOT skipped. The skip is keyed on exact directory-name match.

    Args:
        path: pathlib.Path to test. Can be absolute or relative.

    Returns:
        True if walker should consider the file; False to skip.
    """
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)
    parts = set(path.parts)
    if parts & SKIP_DIR_NAMES:
        return False
    if path.name in SKIP_FILE_NAMES:
        return False
    return True


def filter_paths(paths: Iterable[pathlib.Path]) -> list[pathlib.Path]:
    """Apply is_olympus_source to a sequence; return the kept paths.

    Convenience for `for path in filter_paths(base.rglob('*.py')): ...`.
    """
    return [p for p in paths if is_olympus_source(p)]


def is_olympus_module(path: pathlib.Path) -> bool:
    """Stricter than is_olympus_source: also requires .py extension
    and not a test file.

    Used by ants that specifically care about "modules to test" or
    "modules to scan for symbol references".
    """
    if not is_olympus_source(path):
        return False
    if path.suffix != ".py":
        return False
    name = path.name
    if name.startswith("test_"):
        return False
    return True
