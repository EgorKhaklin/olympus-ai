"""Gaia — the Earth, foundation of all that grows.

Gaia is the personification of the Earth in Greek myth, mother of the
Titans and the substrate on which all life stands. Olympus's Gaia is
the filesystem foundation — the resolved path of the project root.

Every other deity locates itself relative to Gaia.
"""
from __future__ import annotations

import os
import pathlib


class Gaia:
    """The earth beneath Olympus — the project root."""

    def __init__(self, root_path: pathlib.Path | str | None = None) -> None:
        if root_path is None:
            root_path = self._discover_root()
        self.root: pathlib.Path = pathlib.Path(root_path).resolve()

    @staticmethod
    def _discover_root() -> pathlib.Path:
        """Walk up from this file to find the Olympus root (the dir
        containing codex/COSMOGONY.md).

        Honors the OLYMPUS_ROOT env var — when set, that path is used
        directly (validated). Castor uses this to spawn shadow sessions
        rooted at a tempdir without touching production state."""
        env_root = os.environ.get("OLYMPUS_ROOT")
        if env_root:
            candidate = pathlib.Path(env_root).resolve()
            if (candidate / "codex" / "COSMOGONY.md").exists():
                return candidate
            # Fall back to discovery if the env var points somewhere
            # without the marker — silent fallback would be S6
            # ('strategic discipline') failure, so we emit a warning.
            import sys
            sys.stderr.write(
                f"[olympus.gaia] OLYMPUS_ROOT={env_root!r} set but "
                f"missing codex/COSMOGONY.md; falling back to "
                f"file-based discovery\n"
            )
        here = pathlib.Path(__file__).resolve()
        for parent in [here, *here.parents]:
            if (parent / "codex" / "COSMOGONY.md").exists():
                return parent
        # Fallback — assume two levels up from this file
        return here.parent.parent

    def child(self, *parts: str) -> pathlib.Path:
        """Path joined under Gaia (the root)."""
        return self.root.joinpath(*parts)

    def exists(self, *parts: str) -> bool:
        return self.child(*parts).exists()

    def __repr__(self) -> str:
        return f"<Gaia root={self.root}>"


root = Gaia()
