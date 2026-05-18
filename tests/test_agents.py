"""olympus.runtime.agents — agent role registry + run + propose-figure.

All tests use EchoBridge (or an injected stub) for determinism.
They verify:
  - Every canonical role renders a non-empty system prompt
  - run() returns an AgentResult with parsed output
  - Each role's parser handles canned JSON correctly
  - Pan circuit-breaker gates agent invocations
  - propose_figure writes a HIGH-risk proposal file
  - Calibration aggregates across recent invocations
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import json
import unittest


class TestAgentRoles(unittest.TestCase):

    def test_five_canonical_roles_present(self):
        from olympus.runtime.agents import known_roles
        roles = set(known_roles())
        for expected in ("hephaestus", "momus", "cassandra",
                          "athena", "figure_proposer"):
            self.assertIn(expected, roles)

    def test_every_role_renders_system_prompt(self):
        from olympus.runtime.agents import role, known_roles
        for name in known_roles():
            r = role(name)
            sys_prompt = r.render_system()
            self.assertGreater(len(sys_prompt), 200,
                f"role {name!r} system prompt too short")
            # Every role must surface the constitution
            self.assertIn("S1", sys_prompt)
            self.assertIn("S8", sys_prompt)
            # Every role must require a JSON output
            self.assertIn("JSON", sys_prompt)

    def test_unknown_role_raises(self):
        from olympus.runtime.agents import role
        with self.assertRaises(KeyError):
            role("not_a_role")


class TestAgentRun(unittest.TestCase):

    def setUp(self) -> None:
        # Force EchoBridge + clear Pan so the agent invocation isn't
        # blocked by lingering test seeds.
        from olympus.runtime.llm_bridge import EchoBridge, set_bridge
        from olympus.olympians.pan import pan
        set_bridge(EchoBridge())
        pan.clear(by="test", reason="agents-test setUp")

    def test_run_returns_agent_result(self):
        from olympus.runtime.agents import run, AgentResult
        result = run("hephaestus", "test prompt for hephaestus")
        self.assertIsInstance(result, AgentResult)
        self.assertEqual(result.role, "hephaestus")
        self.assertEqual(result.bridge, "echo")
        self.assertEqual(result.error, "")

    def test_run_records_invocation(self):
        from olympus.runtime.agents import run
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("agent.invocation"))
        run("momus", "test prompt for momus")
        after = len(mnemosyne.recall("agent.invocation"))
        self.assertGreater(after, before)

    def test_pan_panic_blocks_invocation(self):
        from olympus.runtime.agents import run
        from olympus.olympians.pan import pan, PanicState
        import datetime
        # Force Pan into panic
        pan._write_state(PanicState(
            panicked=True,
            entered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            last_transition_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            detail="forced for agents test",
        ))
        try:
            result = run("hephaestus", "test")
            self.assertIn("Pan refused", result.error)
        finally:
            pan.clear(by="test", reason="agents-test cleanup")

    def test_unknown_role_returns_structured_error(self):
        from olympus.runtime.agents import run
        result = run("not_a_role", "x")
        self.assertIn("unknown role", result.error)


class TestParsers(unittest.TestCase):

    def test_parse_hephaestus(self):
        from olympus.runtime.agents import parse_hephaestus
        text = """
        {
          "summary": "rotate state file X",
          "drift_observed": "slice 'state/x.jsonl' approaches 10k lines",
          "proposed_fix": "rotate when above 10k",
          "rationale": "disk-fill risk",
          "risk_class": "LOW",
          "confidence": 0.75
        }
        """
        d = parse_hephaestus(text)
        self.assertEqual(d["summary"], "rotate state file X")
        self.assertEqual(d["risk_class"], "LOW")
        self.assertAlmostEqual(d["confidence"], 0.75)

    def test_parse_momus_with_fence(self):
        from olympus.runtime.agents import parse_momus
        text = """```json
        {"ap_ids": ["AP1", "ap8"], "reasoning": "x", "confidence": 0.6}
        ```"""
        d = parse_momus(text)
        self.assertEqual(d["ap_ids"], ["AP1", "AP8"])
        self.assertAlmostEqual(d["confidence"], 0.6)

    def test_parse_cassandra(self):
        from olympus.runtime.agents import parse_cassandra
        d = parse_cassandra(
            '{"vindicated_slices": ["a", "b"], '
            '"still_safe_to_dismiss": ["c"], '
            '"reasoning": "x", "confidence": 0.7}'
        )
        self.assertEqual(d["vindicated_slices"], ["a", "b"])
        self.assertEqual(d["still_safe_to_dismiss"], ["c"])

    def test_parse_athena(self):
        from olympus.runtime.agents import parse_athena
        d = parse_athena('{"insights": ["i1", "i2"], "themes": ["t1"], '
                          '"reasoning": "r", "confidence": 0.55}')
        self.assertEqual(len(d["insights"]), 2)
        self.assertEqual(d["themes"], ["t1"])

    def test_parse_figure_proposer(self):
        from olympus.runtime.agents import parse_figure_proposer
        d = parse_figure_proposer(
            '{"figure_name": "Triton", "tier": "olympians", '
            '"mythological_grounding": "sea messenger", '
            '"cognitive_role": "x", "ap_self_check": "y", '
            '"skeleton": "class Triton: pass", "confidence": 0.4}'
        )
        self.assertEqual(d["figure_name"], "Triton")
        self.assertEqual(d["tier"], "olympians")

    def test_parse_handles_malformed(self):
        from olympus.runtime.agents import parse_hephaestus
        d = parse_hephaestus("definitely not json at all")
        # Returns empty / parse-error marker; never raises
        self.assertTrue(d.get("_empty") or d.get("_parse_error")
                         or d == {})


class TestProposeFigure(unittest.TestCase):

    def setUp(self) -> None:
        from olympus.runtime.llm_bridge import EchoBridge, set_bridge
        from olympus.olympians.pan import pan
        # Install a stub that returns a well-formed figure proposal
        canned = json.dumps({
            "figure_name": "TestBellerophon",
            "tier": "heroes",
            "mythological_grounding": "tamer of Pegasus",
            "cognitive_role": "test role",
            "ap_self_check": "passes AP1-AP8",
            "skeleton": "class TestBellerophon: pass",
            "confidence": 0.6,
        })
        set_bridge(EchoBridge(response_template=canned))
        pan.clear(by="test", reason="propose-figure test setUp")

    def test_writes_high_risk_proposal(self):
        from olympus.runtime.agents import propose_figure
        from olympus.primordials.gaia import root
        proposals_dir = root.child("state", "hephaestus", "proposals")
        before = (len(list(proposals_dir.glob("figure-*.json")))
                  if proposals_dir.exists() else 0)
        result = propose_figure()
        self.assertTrue(result["ok"], f"propose-figure failed: {result}")
        self.assertEqual(result["tier"], "heroes")
        after = len(list(proposals_dir.glob("figure-*.json")))
        self.assertEqual(after, before + 1)
        # Verify the written proposal is well-formed
        with open(result["proposal_path"]) as f:
            written = json.load(f)
        self.assertEqual(written["risk_class"], "HIGH")
        self.assertTrue(written["requires_delphi"])
        self.assertIn("suggested_skeleton", written)
        self.assertIn("agent_confidence", written)

    def test_duplicate_figure_refused(self):
        """If the agent proposes a figure already in the pantheon,
        the proposal is refused (not written)."""
        from olympus.runtime.agents import propose_figure
        from olympus.runtime.llm_bridge import EchoBridge, set_bridge
        canned = json.dumps({
            "figure_name": "athena",  # already exists
            "tier": "olympians",
            "mythological_grounding": "x",
            "cognitive_role": "y",
            "ap_self_check": "z",
            "skeleton": "pass",
            "confidence": 0.5,
        })
        set_bridge(EchoBridge(response_template=canned))
        result = propose_figure()
        self.assertFalse(result["ok"])
        self.assertIn("already present", result["error"])

    def test_records_to_mnemosyne(self):
        from olympus.runtime.agents import propose_figure
        from olympus.titans.mnemosyne import mnemosyne
        from olympus.runtime.llm_bridge import EchoBridge, set_bridge
        # Use a unique name so the test is idempotent
        import uuid
        canned = json.dumps({
            "figure_name": f"TestUnique{uuid.uuid4().hex[:8]}",
            "tier": "heroes",
            "mythological_grounding": "x",
            "cognitive_role": "y",
            "ap_self_check": "z",
            "skeleton": "pass",
            "confidence": 0.5,
        })
        set_bridge(EchoBridge(response_template=canned))
        before = len(mnemosyne.recall("agent.figure-proposal"))
        propose_figure()
        after = len(mnemosyne.recall("agent.figure-proposal"))
        self.assertGreater(after, before)


class TestCalibration(unittest.TestCase):

    def test_returns_baseline_for_each_role(self):
        from olympus.runtime.agents import calibration, known_roles
        for r in known_roles():
            c = calibration(r)
            self.assertEqual(c["role"], r)
            self.assertIn("total_invocations", c)
            self.assertIn("avg_confidence", c)
            self.assertIn("parse_failure_rate", c)
            self.assertIn("error_rate", c)

    def test_aggregate(self):
        from olympus.runtime.agents import calibration
        c = calibration()
        self.assertEqual(c["role"], "all")
        # After test runs there should be many invocations
        self.assertGreater(c["total_invocations"], 0)


if __name__ == "__main__":
    unittest.main()
