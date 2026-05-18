"""ant_self_model_accuracy — first ALERT-capable ant in the cohort.

Consciousness ant. Slice: the swarm's structural claims about
itself — `ALL_EYES` in `monsters.argos/eyes/__init__.py`,
`ALL_PHALANGES` in `monsters.argos/phalanxs/__init__.py`, and
`ALL_DEMES` in `monsters.argos/civitas/__init__.py`. Compares
the registry's claimed count against:

  - the number of `Eye`-subclass names imported into the same
    `__init__.py` (the imports are the source of truth for what
    exists; ALL_EYES is the registry CLAIM about what's loaded).
  - the number of `ant_*.py` files in the package.

Local rule: any mismatch = `alert` pheromone (intensity 8.0). This
is the FIRST ant in the E10 cohort that may fire an ALERT — the
100-year report observed 0 alerts in 100 years; the structurally
honest place for the first one is the swarm's self-model.

G18 (consciousness ants): reads SWARM SELF-STATE (registries,
package directories), not runtime pheromones.

Determinism: pure file-system + AST scan; no time, no randomness.

Authorized by `delphi/2026-05-13-arc-e-acceleration-consciousness-cohort-e10.md`.
"""

from __future__ import annotations

import re

from monsters.argos.base import Eye, EyeFinding, KIND_ALERT


# Pattern: capture imports from prefix-conforming modules ONLY
# (`ant_*`, `phalanx_*`, or any civitas module other than `base`).
# This deliberately ignores `from monsters.argos.<X>.base import ...`
# (base utilities) and any helper-only import lines — the question
# being answered is "how many module-files declare a registered class?"
_FROM_IMPORT_PREFIX_RE = {
    "ants":    re.compile(r"^from\s+monsters.argos\.ants\.(ant_\w+)\s+import\s+", re.MULTILINE),
    "phalanxs": re.compile(r"^from\s+monsters.argos\.phalanxs\.(phalanx_\w+)\s+import\s+", re.MULTILINE),
    "civitas": re.compile(r"^from\s+monsters.argos\.civitas\.(\w+)\s+import\s+", re.MULTILINE),
}
_ALL_LIST_RE = re.compile(
    r"^(ALL_EYES|ALL_PHALANGES|ALL_DEMES)\s*=\s*\[(.*?)\]",
    re.MULTILINE | re.DOTALL,
)
# A registered list entry is a Python identifier (Python class name)
# on its own physical line, optionally with trailing comma + comment.
_LIST_ENTRY_RE = re.compile(
    r"^\s*([A-Za-z_]\w*)\s*,?\s*(?:#.*)?$",
)


def _count_class_entries(list_body: str) -> int:
    """Count Python identifiers appearing as list entries, one per
    line. Robust against comment-only lines and trailing commas."""
    n = 0
    for raw_line in list_body.splitlines():
        # Strip pure comment lines and whitespace lines
        stripped = raw_line.split("#", 1)[0].strip()
        if not stripped:
            continue
        m = _LIST_ENTRY_RE.match(raw_line)
        if m:
            n += 1
    return n


# Helper modules per subdir that do NOT carry registered classes.
# These are shared utilities (base classes, computation helpers)
# loaded by the citizens/eyes/phalanxs but not themselves listed in
# ALL_*. Adjust here when new helper modules are added.
_SUBDIR_HELPERS = {
    "ants":    set(),                  # eyes/ holds only ant_*.py + __init__
    "phalanxs": set(),                  # phalanxs/ holds only phalanx_*.py + base + __init__
    "civitas": {"base", "treasury"},   # base.py + treasury.py are utilities
}


def _count_module_imports(init_text: str, subdir: str) -> int:
    """Count imports matching the per-subdir prefix convention,
    excluding helper modules per `_SUBDIR_HELPERS`."""
    pattern = _FROM_IMPORT_PREFIX_RE.get(subdir)
    if pattern is None:
        return 0
    modules = pattern.findall(init_text)
    helpers = _SUBDIR_HELPERS.get(subdir, set())
    modules = [m for m in modules if m not in helpers]
    return len(set(modules))


class AntSelfModelAccuracy(Eye):
    NAME = "ant_self_model_accuracy"
    DESCRIPTION = "Pheromones (ALERT) when swarm's self-registry diverges from reality."

    def scan(self) -> list[EyeFinding]:
        findings: list[EyeFinding] = []
        targets = (
            ("ants",     "ALL_EYES",     "ant_"),
            ("phalanxs",  "ALL_PHALANGES",  "phalanx_"),
            ("civitas",  "ALL_DEMES", None),  # citizens have varied filenames
        )
        for subdir, list_name, file_prefix in targets:
            init_text = self._read(
                "monsters.argos", subdir, "__init__.py",
            ) or ""
            if not init_text:
                continue
            # Count modules imported via prefix-conforming paths.
            import_count = _count_module_imports(init_text, subdir)
            # Find the registry list body
            m = None
            for cand in _ALL_LIST_RE.finditer(init_text):
                if cand.group(1) == list_name:
                    m = cand
                    break
            if m is None:
                continue
            registry_count = _count_class_entries(m.group(2))
            # Count source-of-truth files matching the convention.
            pkg_dir = self.root / "monsters.argos" / subdir
            if file_prefix is not None and pkg_dir.is_dir():
                file_count = sum(
                    1 for p in pkg_dir.glob(f"{file_prefix}*.py")
                    if p.is_file()
                )
            else:
                # citizens: filename-prefix varies; count from package
                # excluding __init__.py + helper modules.
                helpers = _SUBDIR_HELPERS.get(subdir, set())
                file_count = sum(
                    1 for p in pkg_dir.glob("*.py")
                    if p.is_file()
                    and p.name != "__init__.py"
                    and p.stem not in helpers
                )
            # Divergence check:
            #   registry_count == import_count == file_count  →  healthy
            if registry_count == import_count == file_count:
                continue
            findings.append(EyeFinding(
                node_id=f"swarm:self-model:{subdir}",
                intensity=8.0,
                kind=KIND_ALERT,
                evidence={
                    "message": (
                        f"{list_name} divergence — registry={registry_count}, "
                        f"imports={import_count}, files={file_count}"
                    ),
                    "subdir": subdir,
                    "registry_name": list_name,
                    "claim_registry": registry_count,
                    "claim_imports": import_count,
                    "reality_files": file_count,
                    "divergence": registry_count - file_count,
                    "fix_hint": (
                        "either add missing module to imports/registry, "
                        "or delete orphan file"
                    ),
                },
                half_life_hours=12.0,  # short half-life: transient alerts fade
            ))
        return findings
