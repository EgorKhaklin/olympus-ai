"""olympus.action — the action queue.

Proposals surfaced by Hephaestus + contested by Momus get promoted to
Actions. Actions move through a lifecycle:

  proposed   → promote() →   queued          (MEDIUM, awaiting Zeus)
                          or auto-ratified   (LOW, no Momus contests)
                          or delphi-pending  (HIGH / COMPOSITE)
                          or rejected        (Momus issued blocking contests)

  queued     → ratify(quote) → ratified   (Zeus oaths it)
  ratified   → execute(fn)   → executed   (the action ran)
                            or failed     (the action raised; recorded in Hades)

The queue itself is append-only JSONL. State transitions are recorded
as separate Mnemosyne entries.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field, asdict
from typing import Callable, Any

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class Action:
    id: str
    proposal_id: str
    risk_class: str
    summary: str            # one-line description of what would happen
    status: str             # see lifecycle above
    contests: list[str] = field(default_factory=list)
    queued_at: str = ""
    ratified_at: str = ""
    executed_at: str = ""
    ratified_by: str = ""
    execution_result: str = ""

    def __post_init__(self) -> None:
        if not self.queued_at:
            self.queued_at = Nyx.now().isoformat()


@dataclass
class ExecutionResult:
    action_id: str
    success: bool
    detail: str


class ActionQueue:
    """Append-only queue. Reads return the full history; promotion +
    state transitions append new rows rather than mutating."""

    LOG = "state/action_queue.jsonl"

    def __init__(self, log_path: pathlib.Path | None = None) -> None:
        self.log_path = log_path or root.child(self.LOG)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    # ─────────────────────────────────────────────────────────
    # Read-side
    # ─────────────────────────────────────────────────────────

    def _read_all(self) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        out: list[dict[str, Any]] = []
        with self.log_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    out.append(json.loads(line))
        return out

    def _append(self, row: dict[str, Any]) -> None:
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")

    def _latest_per_action(self) -> dict[str, dict[str, Any]]:
        """Roll up the append-only log to current state per action."""
        out: dict[str, dict[str, Any]] = {}
        for row in self._read_all():
            out[row["id"]] = row
        return out

    def all(self) -> list[Action]:
        return [Action(**row) for row in self._latest_per_action().values()]

    def pending(self) -> list[Action]:
        """Actions awaiting Zeus's ratification."""
        return [a for a in self.all() if a.status == "queued"]

    def delphi_pending(self) -> list[Action]:
        return [a for a in self.all() if a.status == "delphi-pending"]

    def ratified(self) -> list[Action]:
        return [a for a in self.all() if a.status == "ratified"]

    def by_id(self, action_id: str) -> Action | None:
        rows = self._latest_per_action()
        if action_id in rows:
            return Action(**rows[action_id])
        return None

    # ─────────────────────────────────────────────────────────
    # Write-side — every state transition appends, never mutates
    # ─────────────────────────────────────────────────────────

    def promote(self, proposal: Any, *, contests: list[str] | None = None) -> Action:
        """Promote a proposal to an action with status set by risk class
        and Momus contest count."""
        contests = contests or []
        risk = proposal.risk_class.upper()

        if contests and any(c.startswith("AP") for c in contests):
            # Any Momus contest blocks auto-ratification regardless of risk.
            status = "queued" if risk != "LOW" else "queued"
        elif risk == "LOW":
            status = "auto-ratified"
        elif risk == "MEDIUM":
            status = "queued"
        else:  # HIGH or COMPOSITE
            status = "delphi-pending"

        action = Action(
            id=f"act-{proposal.id}",
            proposal_id=proposal.id,
            risk_class=risk,
            summary=proposal.proposed_fix[:140],
            status=status,
            contests=list(contests),
        )
        self._append(asdict(action))

        mnemosyne.remember(
            kind="action.promoted",
            actor="action-queue",
            summary=f"{action.id} promoted ({status}) — {action.summary[:80]}",
            action_id=action.id, risk_class=risk, status=status,
        )

        # Auto-ratified LOW actions get the ratification entry immediately.
        if status == "auto-ratified":
            self._append({**asdict(action),
                          "status": "ratified",
                          "ratified_at": Nyx.now().isoformat(),
                          "ratified_by": "auto:LOW-no-contests"})

        return action

    def ratify(self, action_id: str, *, quote: str,
               by: str = "zeus:operator") -> Action:
        """Move an action from 'queued' or 'delphi-pending' to 'ratified'.
        Zeus is the only authority that can promote out of delphi-pending.
        """
        action = self.by_id(action_id)
        if action is None:
            raise KeyError(f"no action {action_id!r}")
        if action.status not in {"queued", "delphi-pending"}:
            raise RuntimeError(
                f"cannot ratify action in status {action.status!r} "
                f"(must be 'queued' or 'delphi-pending')"
            )

        # HIGH/COMPOSITE require Zeus's explicit Styx-sworn authority.
        if action.status == "delphi-pending":
            from olympus.underworld.styx import swear
            swear(
                sworn_by=by,
                statement=f"RATIFY action={action_id} (delphi-pending)",
                payload={"quote": quote, "action_id": action_id},
            )

        ratified = Action(**{
            **asdict(action),
            "status": "ratified",
            "ratified_at": Nyx.now().isoformat(),
            "ratified_by": by,
        })
        self._append(asdict(ratified))

        mnemosyne.remember(
            kind="action.ratified",
            actor=by,
            summary=f"{action_id} ratified",
            action_id=action_id, quote=quote,
        )
        return ratified

    def reject(self, action_id: str, *, reason: str,
               by: str = "zeus:operator") -> Action:
        """Move an action to 'rejected' — final state."""
        action = self.by_id(action_id)
        if action is None:
            raise KeyError(f"no action {action_id!r}")
        rejected = Action(**{
            **asdict(action),
            "status": "rejected",
            "execution_result": f"rejected: {reason}",
        })
        self._append(asdict(rejected))
        mnemosyne.remember(
            kind="action.rejected",
            actor=by,
            summary=f"{action_id} rejected: {reason}",
            action_id=action_id,
        )
        return rejected

    def execute(self, action_id: str, fn: Callable[[Action], Any]) -> ExecutionResult:
        """Run `fn(action)` for a ratified action; record success or failure.
        Returns an ExecutionResult; never raises out of this method."""
        action = self.by_id(action_id)
        if action is None:
            return ExecutionResult(action_id, False, "no-such-action")
        if action.status != "ratified":
            return ExecutionResult(
                action_id, False,
                f"refused: status is {action.status!r}, not 'ratified'"
            )
        try:
            outcome = fn(action)
            detail = str(outcome)[:200] if outcome is not None else "completed"
            self._append({
                **asdict(action),
                "status": "executed",
                "executed_at": Nyx.now().isoformat(),
                "execution_result": detail,
            })
            mnemosyne.remember(
                kind="action.executed",
                actor="action-executor",
                summary=f"{action_id} executed: {detail[:80]}",
                action_id=action_id,
            )
            return ExecutionResult(action_id, True, detail)
        except Exception as exc:  # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"
            from olympus.underworld.hades import descend
            descend(f"action-failure--{action_id}", {
                "action": asdict(action),
                "error": err,
            })
            self._append({
                **asdict(action),
                "status": "failed",
                "executed_at": Nyx.now().isoformat(),
                "execution_result": err,
            })
            mnemosyne.remember(
                kind="action.failed",
                actor="action-executor",
                summary=f"{action_id} failed: {err}",
                action_id=action_id,
            )
            return ExecutionResult(action_id, False, err)


action_queue = ActionQueue()
