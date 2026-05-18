"""Property tests for Styx — chain invariants under random append sequences.

The Styx chain must satisfy:
  P1  Append-only: writing a new oath never modifies any prior oath.
  P2  Chain-hashed: each oath.prev_hash == prior oath's self_hash.
  P3  Tamper-detectable: re-computing any oath's self_hash from its
      fields + the prior hash must match the recorded self_hash.

We exercise these with random sequences of oaths against a fresh
ledger and verify the invariants hold for arbitrary append patterns.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / 'src'
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import json
import pathlib
import secrets
import tempfile
import unittest

from olympus.underworld.styx import Styx, Oath


class TestStyxProperties(unittest.TestCase):

    def _fresh_styx(self) -> tuple[Styx, pathlib.Path]:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
        tmp.close()
        path = pathlib.Path(tmp.name)
        path.unlink()  # remove file so Styx creates it
        return Styx(ledger_path=path), path

    def test_P1_append_only_under_random_oaths(self):
        """After N random appends, no prior oath's row has been modified."""
        styx, path = self._fresh_styx()
        snapshots: list[list[dict]] = []
        for i in range(20):
            styx.swear(
                sworn_by=f"actor-{i % 3}",
                statement=secrets.token_hex(8),
                payload={"i": i, "noise": secrets.token_hex(4)},
            )
            with path.open("r", encoding="utf-8") as f:
                snapshots.append([json.loads(line) for line in f if line.strip()])
        # Every snapshot must be a prefix of the final snapshot
        final = snapshots[-1]
        for i, snap in enumerate(snapshots):
            self.assertEqual(snap, final[: i + 1],
                f"P1 violation — snapshot at step {i} is not a prefix of final")

    def test_P2_chain_links_under_random_oaths(self):
        """prev_hash of each oath == self_hash of its predecessor."""
        styx, path = self._fresh_styx()
        for _ in range(15):
            styx.swear(
                sworn_by=f"a-{secrets.token_hex(2)}",
                statement=secrets.token_hex(8),
            )
        rows = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
        for i, row in enumerate(rows):
            if i == 0:
                self.assertEqual(row["prev_hash"], "GENESIS")
            else:
                self.assertEqual(row["prev_hash"], rows[i - 1]["self_hash"],
                    f"P2 violation at seq={i}: prev_hash mismatch")

    def test_P3_tampering_detected_by_verify(self):
        """If we corrupt a single byte in any oath's statement, verify()
        must return (False, <seq>)."""
        styx, path = self._fresh_styx()
        for _ in range(10):
            styx.swear(sworn_by="random", statement=secrets.token_hex(8))

        # Sanity: chain verifies clean
        intact, bad = styx.verify()
        self.assertTrue(intact)
        self.assertIsNone(bad)

        # Tamper with the middle row's statement
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        target = json.loads(lines[5])
        target["statement"] = target["statement"] + "!"
        lines[5] = json.dumps(target) + "\n"
        with path.open("w", encoding="utf-8") as f:
            f.writelines(lines)

        intact, bad = styx.verify()
        self.assertFalse(intact, "P3 violation — tamper undetected")
        self.assertEqual(bad, 5, f"first_bad_seq should be 5; got {bad}")

    def test_verify_passes_on_empty_chain(self):
        styx, _ = self._fresh_styx()
        intact, bad = styx.verify()
        self.assertTrue(intact)
        self.assertIsNone(bad)


if __name__ == "__main__":
    unittest.main()
