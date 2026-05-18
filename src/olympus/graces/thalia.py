"""Thalia — Festivity (the Grace, not the Muse).

Thalia of the Graces governs the tone of gatherings — the lightness
that distinguishes celebration from mere meeting. In Olympus she
governs doc-tone: she pulls the first sentence of any module's
docstring and renders it as a short biography.
"""
from __future__ import annotations

import ast
import pathlib
from dataclasses import dataclass


@dataclass
class Biography:
    module: str
    first_sentence: str
    full_docstring: str


class Thalia:
    """Doc-tone helpers."""

    @staticmethod
    def biography(module_path: pathlib.Path) -> Biography | None:
        """Read a module's docstring and return its first-sentence biography."""
        if not module_path.exists():
            return None
        try:
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
        except SyntaxError:
            return None
        doc = ast.get_docstring(tree)
        if not doc:
            return Biography(
                module=module_path.stem,
                first_sentence="(no biography)",
                full_docstring="",
            )
        # First sentence — up to the first '.' followed by whitespace or newline
        first = doc.split("\n", 1)[0].strip()
        if not first.endswith("."):
            # Try harder: first '.' in the doc
            for i, ch in enumerate(doc):
                if ch == "." and (i + 1 == len(doc) or doc[i + 1] in (" ", "\n")):
                    first = doc[: i + 1]
                    break
        return Biography(
            module=module_path.stem,
            first_sentence=first.replace("\n", " "),
            full_docstring=doc,
        )


thalia = Thalia()
