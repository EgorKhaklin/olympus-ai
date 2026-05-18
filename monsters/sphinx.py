"""The Sphinx — riddler at Thebes.

The Sphinx asked travellers a riddle; those who failed were devoured.
Oedipus answered correctly and the Sphinx threw herself from her cliff.
In Olympus, the Sphinx is the challenge-response primitive: a
question-answering gate that admits only the caller who knows the
answer.
"""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass


@dataclass
class Riddle:
    question: str
    answer_hash: str   # SHA-256 of the canonical answer + salt
    salt: str


class Sphinx:
    """Question-answer gate."""

    @staticmethod
    def _digest(answer: str, salt: str) -> str:
        return hashlib.sha256((salt + answer).encode("utf-8")).hexdigest()

    def pose(self, question: str, answer: str) -> Riddle:
        """Register a riddle. The plaintext answer is NOT stored;
        only the hash."""
        salt = secrets.token_hex(8)
        return Riddle(
            question=question,
            answer_hash=self._digest(answer, salt),
            salt=salt,
        )

    def solve(self, riddle: Riddle, attempt: str) -> bool:
        """True iff `attempt` matches the riddle's answer."""
        return self._digest(attempt, riddle.salt) == riddle.answer_hash


sphinx = Sphinx()
