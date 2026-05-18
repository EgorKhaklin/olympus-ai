"""olympus.runtime.boundaries — error-boundary decorator.

Wraps a callable so exceptions become structured BoundaryResults that
Hecate can route to retry / abandon / escalate. Inside the cognitive
loop, every observation phase (HYDRA head, Argos Eye, Hephaestus
proposal, etc.) is wrapped — one bad watcher cannot crash the loop.
"""
from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from olympus.primordials.tartarus import quarantine
from olympus.titans.mnemosyne import mnemosyne


T = TypeVar("T")


@dataclass
class BoundaryResult:
    ok: bool
    value: Any = None
    error: str | None = None
    callable_name: str | None = None


def bounded(*, name: str | None = None,
            quarantine_on_error: bool = True,
            record_in_mnemosyne: bool = True):
    """Decorator: catch any exception and return a BoundaryResult.

    Usage:
        @bounded(name="head_cosmogony.observe")
        def observe(): ...
    """
    def decorator(fn: Callable[..., T]) -> Callable[..., BoundaryResult]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> BoundaryResult:
            label = name or getattr(fn, "__qualname__", fn.__name__)
            try:
                value = fn(*args, **kwargs)
                return BoundaryResult(ok=True, value=value, callable_name=label)
            except Exception as exc:  # noqa: BLE001
                err = f"{type(exc).__name__}: {exc}"
                if quarantine_on_error:
                    quarantine(
                        {"args": repr(args)[:300], "kwargs": repr(kwargs)[:300]},
                        reason=f"bounded:{label}: {err}",
                        witness=label,
                    )
                if record_in_mnemosyne:
                    mnemosyne.remember(
                        kind="boundary.caught",
                        actor=label,
                        summary=f"caught {err[:100]}",
                        callable=label, error=err,
                    )
                return BoundaryResult(
                    ok=False, error=err, callable_name=label
                )
        return wrapper
    return decorator
