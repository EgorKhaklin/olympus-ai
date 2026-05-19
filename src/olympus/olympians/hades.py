"""olympus.olympians.hades — the secrets vault.

Per Delphi 2026-05-19-hades-arc.md.

Hades (Greek: ᾍδης) ruled the underworld and kept the riches of the
earth in his strongbox. In Olympus, **Hades is the secrets vault**:
deposit a secret, retrieve it back, forget it when done. He uses the
`keyring` library, which dispatches to:

  - macOS  → Keychain (encrypted at rest, GUI-prompted)
  - Linux  → Secret Service (GNOME Keyring, KWallet)
  - Win    → Credential Manager
  - Headless / no backend → `available()` returns False; callers
    must fall back to plaintext config OR refuse.

Constitutional posture:
  - S1: every deposit/forget is recorded to Mnemosyne under
    `hades.event` — **the value is NEVER logged**, only metadata
    (length, sha256-prefix, location).
  - S3: reading never mutates; migration is explicit.
  - S6: `hades.where(name)` reports the verifiable resolved location.
  - S7: deposit/forget stay CLI-only (Throne can read, not write).
  - AP1: ~150 LOC; reuses `keyring`; no parallel secrets system.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any, Literal

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


# Service name — groups all Olympus secrets together in the OS UI
SERVICE = "olympus"


Location = Literal["env", "keychain", "plaintext", "unset"]


@dataclass
class VaultStatus:
    """What the operator should know about one secret name."""
    name: str
    location: Location
    backend: str = ""
    env_var: str = ""
    bytes_known: int = 0   # length of secret (NEVER the secret itself)
    sha256_prefix: str = ""  # 12-char prefix of sha256(secret) for ID


# ─────────────────────────────────────────────────────────────────────
# Backend access — keyring import + functionality probe
# ─────────────────────────────────────────────────────────────────────


def _try_import_keyring() -> Any:
    """Return the keyring module if importable AND a real backend is
    configured. Returns None on either failure (graceful fallback)."""
    try:
        import keyring  # type: ignore
        backend = keyring.get_keyring()
        backend_name = type(backend).__name__
        # The fail-backend reports as "fail.Keyring"; treat as unavailable
        if "fail" in backend_name.lower():
            return None
        return keyring
    except Exception:  # noqa: BLE001
        return None


# ─────────────────────────────────────────────────────────────────────
# The Hades singleton
# ─────────────────────────────────────────────────────────────────────


# Mapping of secret-name → env-var that, if set, takes precedence
ENV_OVERRIDES: dict[str, str] = {
    "anthropic_api_key": "ANTHROPIC_API_KEY",
}


# Sentinel value written into config.json when a secret has moved to Hades
PLAINTEXT_SENTINEL = "(in-hades)"


class Hades:
    """The secrets vault. Reads/writes via OS keychain."""

    def __init__(self, *, service: str = SERVICE,
                  keyring_module: Any | None = None) -> None:
        self.service = service
        # Lazy resolution: re-probe on each call so tests can inject
        self._injected_keyring = keyring_module

    # ─────────────────────────────────────────────────────────────
    # Backend probe
    # ─────────────────────────────────────────────────────────────

    def _kr(self) -> Any:
        if self._injected_keyring is not None:
            return self._injected_keyring
        return _try_import_keyring()

    def available(self) -> bool:
        return self._kr() is not None

    def backend_name(self) -> str:
        kr = self._kr()
        if kr is None:
            return "(unavailable)"
        try:
            return type(kr.get_keyring()).__name__
        except Exception:  # noqa: BLE001
            return "(error)"

    # ─────────────────────────────────────────────────────────────
    # Core operations
    # ─────────────────────────────────────────────────────────────

    def deposit(self, name: str, secret: str) -> None:
        """Store `secret` under `name` in the keychain. Raises
        RuntimeError if no backend available — callers must check
        `available()` first OR catch and fall back."""
        if not name or not isinstance(name, str):
            raise ValueError("name must be a non-empty string")
        if not isinstance(secret, str):
            raise ValueError("secret must be a string")
        kr = self._kr()
        if kr is None:
            raise RuntimeError(
                "no keyring backend available; cannot deposit")
        kr.set_password(self.service, name, secret)
        self._record_event("deposit", name, secret)

    def retrieve(self, name: str) -> str | None:
        """Return the secret or None. Never raises (callers shouldn't
        need to wrap every call)."""
        kr = self._kr()
        if kr is None:
            return None
        try:
            return kr.get_password(self.service, name)
        except Exception:  # noqa: BLE001
            return None

    def forget(self, name: str) -> bool:
        """Remove the secret from the keychain. Returns True if a
        value was actually removed."""
        kr = self._kr()
        if kr is None:
            return False
        try:
            existed = kr.get_password(self.service, name) is not None
            if existed:
                kr.delete_password(self.service, name)
                self._record_event("forget", name, None)
            return existed
        except Exception:  # noqa: BLE001
            return False

    # ─────────────────────────────────────────────────────────────
    # Location reporting (verifies S6)
    # ─────────────────────────────────────────────────────────────

    def where(self, name: str) -> Location:
        """Where is `name` actually being read from RIGHT NOW?
        Resolution order: env → keychain → plaintext-config → unset."""
        env_var = ENV_OVERRIDES.get(name)
        if env_var and os.environ.get(env_var):
            return "env"
        if self.retrieve(name) is not None:
            return "keychain"
        # Check legacy plaintext in config.json
        try:
            from olympus.runtime.config import load as _load_config
            cfg = _load_config()
            legacy = getattr(cfg.llm, name, None)
            if legacy and legacy != PLAINTEXT_SENTINEL:
                return "plaintext"
        except Exception:  # noqa: BLE001
            pass
        return "unset"

    def status(self, name: str) -> VaultStatus:
        """Full status for one secret name."""
        loc = self.where(name)
        env_var = ENV_OVERRIDES.get(name, "")
        # Compute non-value metadata if we can find a value
        value: str | None = None
        if loc == "env":
            value = os.environ.get(env_var) if env_var else None
        elif loc == "keychain":
            value = self.retrieve(name)
        elif loc == "plaintext":
            try:
                from olympus.runtime.config import load as _load_config
                value = getattr(_load_config().llm, name, None)
            except Exception:  # noqa: BLE001
                pass
        bytes_known = len(value) if isinstance(value, str) else 0
        sha_prefix = ""
        if value:
            sha_prefix = hashlib.sha256(
                value.encode("utf-8")).hexdigest()[:12]
        return VaultStatus(
            name=name, location=loc,
            backend=self.backend_name() if loc == "keychain" else "",
            env_var=env_var,
            bytes_known=bytes_known,
            sha256_prefix=sha_prefix,
        )

    # ─────────────────────────────────────────────────────────────
    # Audit-of-record — value is NEVER recorded
    # ─────────────────────────────────────────────────────────────

    def _record_event(self, action: str, name: str,
                       secret: str | None) -> None:
        """Persist deposit/forget to Mnemosyne. value → hash + length."""
        body: dict[str, Any] = {
            "name": name,
            "action": action,
            "service": self.service,
            "backend": self.backend_name(),
        }
        if secret is not None:
            body["bytes_stored"] = len(secret)
            body["sha256_prefix"] = hashlib.sha256(
                secret.encode("utf-8")).hexdigest()[:12]
        mnemosyne.remember(
            kind="hades.event",
            actor="hades",
            summary=f"{action} '{name}' ({self.backend_name()})",
            **body,
        )


# ─────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────


hades = Hades()


__all__ = [
    "Hades", "hades",
    "VaultStatus", "Location",
    "SERVICE", "ENV_OVERRIDES", "PLAINTEXT_SENTINEL",
]
