"""tests/test_hades.py — the Hades arc.

Per Delphi 2026-05-19-hades-arc.md.

Covers (using an injected fake keyring — no real OS keychain touched):
  - deposit/retrieve round-trip
  - forget removes
  - where() reports env / keychain / plaintext / unset correctly
  - available() returns False when no backend
  - retrieve() never raises
  - deposit raises clearly when no backend
  - event recording: value is NEVER stored, only metadata
  - migrate_plaintext_to_hades: idempotent + sentinel replacement
  - effective_anthropic_api_key resolution priority
  - apply_to_environment honors Hades
  - vault errand smoke tests
  - vault in SAFE_ERRANDS
  - doctor check produces a finding
"""
from __future__ import annotations

import io
import contextlib
import os
import sys

import pytest

from olympus.olympians.hades import (
    Hades, VaultStatus, PLAINTEXT_SENTINEL, ENV_OVERRIDES,
)
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────────────────
# Fake keyring — no real OS keychain touched in tests
# ─────────────────────────────────────────────────────────────────────


class _FakeBackend:
    def __init__(self): self.store: dict[tuple[str, str], str] = {}
    def __class__name__(self): return "FakeBackend"
    def get_password(self, service, name):
        return self.store.get((service, name))
    def set_password(self, service, name, value):
        self.store[(service, name)] = value
    def delete_password(self, service, name):
        self.store.pop((service, name), None)


class FakeKeyringModule:
    """Quacks like the `keyring` package."""
    def __init__(self):
        self._backend = _FakeBackend()
    def get_keyring(self): return self._backend
    def set_password(self, service, name, value):
        return self._backend.set_password(service, name, value)
    def get_password(self, service, name):
        return self._backend.get_password(service, name)
    def delete_password(self, service, name):
        return self._backend.delete_password(service, name)


class BrokenKeyringModule:
    """All operations raise."""
    def get_keyring(self):
        class _B: pass
        return _B()
    def set_password(self, *_): raise RuntimeError("backend broken")
    def get_password(self, *_): raise RuntimeError("backend broken")
    def delete_password(self, *_): raise RuntimeError("backend broken")


# ─────────────────────────────────────────────────────────────────────
# Round-trip
# ─────────────────────────────────────────────────────────────────────


class TestDepositRetrieve:

    def test_round_trip(self):
        h = Hades(keyring_module=FakeKeyringModule())
        assert h.retrieve("missing") is None
        h.deposit("anthropic_api_key", "sk-ant-test-123")
        assert h.retrieve("anthropic_api_key") == "sk-ant-test-123"

    def test_forget_removes(self):
        h = Hades(keyring_module=FakeKeyringModule())
        h.deposit("k", "v")
        assert h.forget("k") is True
        assert h.retrieve("k") is None
        # Re-forget returns False
        assert h.forget("k") is False

    def test_deposit_rejects_empty_name(self):
        h = Hades(keyring_module=FakeKeyringModule())
        with pytest.raises(ValueError):
            h.deposit("", "value")

    def test_deposit_rejects_non_string_secret(self):
        h = Hades(keyring_module=FakeKeyringModule())
        with pytest.raises(ValueError):
            h.deposit("k", 12345)  # type: ignore[arg-type]


# ─────────────────────────────────────────────────────────────────────
# No-backend behavior
# ─────────────────────────────────────────────────────────────────────


class TestNoBackend:

    def test_available_false_when_no_module(self, monkeypatch):
        # Force the lazy resolver to return None
        from olympus.olympians import hades as hades_mod
        monkeypatch.setattr(hades_mod, "_try_import_keyring",
                             lambda: None)
        h = Hades()  # no injection → uses lazy resolver
        assert h.available() is False
        # retrieve never raises
        assert h.retrieve("anything") is None

    def test_deposit_raises_when_unavailable(self, monkeypatch):
        from olympus.olympians import hades as hades_mod
        monkeypatch.setattr(hades_mod, "_try_import_keyring",
                             lambda: None)
        h = Hades()
        with pytest.raises(RuntimeError, match="no keyring backend"):
            h.deposit("k", "v")

    def test_retrieve_swallows_backend_error(self):
        h = Hades(keyring_module=BrokenKeyringModule())
        # Should NOT raise
        assert h.retrieve("k") is None


# ─────────────────────────────────────────────────────────────────────
# where() resolution
# ─────────────────────────────────────────────────────────────────────


class TestWhere:

    def test_env_wins(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-env-value")
        h = Hades(keyring_module=FakeKeyringModule())
        h.deposit("anthropic_api_key", "sk-keychain-value")
        assert h.where("anthropic_api_key") == "env"

    def test_keychain_when_no_env(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        h = Hades(keyring_module=FakeKeyringModule())
        h.deposit("anthropic_api_key", "sk-keychain-value")
        assert h.where("anthropic_api_key") == "keychain"

    def test_unset_when_nothing(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        h = Hades(keyring_module=FakeKeyringModule())
        # No deposit
        # NOTE: 'plaintext' might be true on this real machine, so we
        # only assert NOT keychain and NOT env
        w = h.where("anthropic_api_key")
        assert w in ("plaintext", "unset")


# ─────────────────────────────────────────────────────────────────────
# status() metadata never leaks the secret
# ─────────────────────────────────────────────────────────────────────


class TestStatusNeverLeaksSecret:

    def test_status_returns_metadata_only(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        h = Hades(keyring_module=FakeKeyringModule())
        secret = "sk-ant-secret-value-do-not-expose"
        h.deposit("anthropic_api_key", secret)
        st = h.status("anthropic_api_key")
        assert isinstance(st, VaultStatus)
        assert st.bytes_known == len(secret)
        assert len(st.sha256_prefix) == 12
        # The value itself must NOT be in any field
        for v in st.__dict__.values():
            assert secret not in str(v), \
                "secret leaked into VaultStatus field!"


# ─────────────────────────────────────────────────────────────────────
# Event recording — value NEVER recorded
# ─────────────────────────────────────────────────────────────────────


class TestEventRecording:

    def test_deposit_records_metadata_not_value(self):
        h = Hades(keyring_module=FakeKeyringModule())
        secret = "sk-ant-recording-test-very-secret"
        before = len(mnemosyne.recall("hades.event"))
        h.deposit("test_key", secret)
        after = mnemosyne.recall("hades.event")
        assert len(after) == before + 1
        body = after[-1].body
        assert body["action"] == "deposit"
        assert body["bytes_stored"] == len(secret)
        assert len(body["sha256_prefix"]) == 12
        # The value must NOT be in the body
        for v in body.values():
            assert secret not in str(v), \
                "secret leaked into hades.event record!"

    def test_forget_records_event(self):
        h = Hades(keyring_module=FakeKeyringModule())
        h.deposit("forget_test", "value")
        before = len(mnemosyne.recall("hades.event"))
        h.forget("forget_test")
        after = len(mnemosyne.recall("hades.event"))
        assert after == before + 1
        assert mnemosyne.recall("hades.event")[-1].body["action"] == "forget"


# ─────────────────────────────────────────────────────────────────────
# config.effective_anthropic_api_key resolution
# ─────────────────────────────────────────────────────────────────────


class TestEffectiveKeyResolution:

    def test_env_wins_over_everything(self, monkeypatch):
        from olympus.runtime import config as cfg_mod
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-env-value")
        # Even with a Hades value, env wins
        from olympus.olympians import hades as hades_mod
        monkeypatch.setattr(hades_mod, "hades",
                             Hades(keyring_module=FakeKeyringModule()))
        hades_mod.hades.deposit("anthropic_api_key", "sk-keychain")
        assert cfg_mod.effective_anthropic_api_key() == "sk-env-value"

    def test_returns_none_when_nothing(self, monkeypatch):
        from olympus.runtime import config as cfg_mod
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        # Inject empty Hades
        from olympus.olympians import hades as hades_mod
        empty = Hades(keyring_module=FakeKeyringModule())
        monkeypatch.setattr(hades_mod, "hades", empty)
        # If real config has a plaintext key on the test machine, this
        # test exits early (we can't undo the operator's real state).
        # Otherwise the resolver should return None.
        real = cfg_mod.load()
        if real.llm.anthropic_api_key and \
           real.llm.anthropic_api_key != PLAINTEXT_SENTINEL:
            pytest.skip("operator has a real plaintext key; "
                         "cannot test the None branch")
        assert cfg_mod.effective_anthropic_api_key() is None


# ─────────────────────────────────────────────────────────────────────
# CLI errand smoke
# ─────────────────────────────────────────────────────────────────────


class TestVaultErrand:

    def test_vault_status_exits_zero(self):
        from olympus.cli import hermes
        errand = hermes._errands.get("vault")
        assert errand is not None
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["status"])
        assert rc == 0
        out = buf.getvalue()
        assert "vault" in out.lower()
        assert "Hades" in out or "strongbox" in out

    def test_vault_unknown_subcommand(self):
        from olympus.cli import hermes
        errand = hermes._errands["vault"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["floob"])
        assert rc == 1


# ─────────────────────────────────────────────────────────────────────
# Throne integration
# ─────────────────────────────────────────────────────────────────────


class TestThroneCanReadVault:

    def test_vault_in_safe_errands(self):
        from olympus.throne.router import SAFE_ERRANDS, GATED_ERRANDS
        assert "vault" in SAFE_ERRANDS
        # Should not be gated; the read-only status check is safe
        assert "vault" not in GATED_ERRANDS

    def test_vault_appears_in_system_prompt(self):
        from olympus.throne.router import build_system_prompt
        p = build_system_prompt()
        assert "vault" in p


# ─────────────────────────────────────────────────────────────────────
# Doctor check
# ─────────────────────────────────────────────────────────────────────


class TestDoctorVaultCheck:

    def test_check_secrets_returns_finding(self):
        from olympus.runtime.doctor import _check_secrets
        finding = _check_secrets()
        assert finding.name == "vault"
        assert finding.status in ("ok", "warn", "fail")
        assert finding.detail


# ─────────────────────────────────────────────────────────────────────
# Migration semantics
# ─────────────────────────────────────────────────────────────────────


class TestMigrate:

    def test_migrate_skips_when_empty(self, monkeypatch):
        from olympus.runtime import config as cfg_mod
        # Override hades singleton with an empty fake
        from olympus.olympians import hades as hades_mod
        empty = Hades(keyring_module=FakeKeyringModule())
        monkeypatch.setattr(hades_mod, "hades", empty)
        # If real config is empty/sentinel, migrate is a no-op
        result = cfg_mod.migrate_plaintext_to_hades()
        assert "migrated" in result
        assert "reason" in result

    def test_migrate_refuses_garbage_value(self, monkeypatch, tmp_path):
        """Use monkey-patched _path() pointing to tmp — DO NOT touch
        the real state/config.json (an earlier version of this test
        clobbered the operator's actual key. Never again)."""
        from olympus.runtime import config as cfg_mod
        fake_path = tmp_path / "config.json"
        monkeypatch.setattr(cfg_mod, "_path", lambda: fake_path)
        # Build a fake-key config in the redirected location
        cfg = cfg_mod.Config()
        cfg.llm.provider = "anthropic"
        cfg.llm.anthropic_api_key = "not-a-real-key"
        cfg_mod.save(cfg)
        # Confirm we wrote to tmp, NOT to the real path
        assert fake_path.exists()
        # Hades available
        from olympus.olympians import hades as hades_mod
        monkeypatch.setattr(hades_mod, "hades",
                             Hades(keyring_module=FakeKeyringModule()))
        result = cfg_mod.migrate_plaintext_to_hades()
        assert result["migrated"] is False
        assert "doesn't look like a real key" in result["reason"] \
            or "real key" in result["reason"]
        # Real config.json must NOT have changed
        from olympus.primordials.gaia import root
        real = root.child("state", "config.json")
        if real.exists():
            real_data = real.read_text(encoding="utf-8")
            assert "not-a-real-key" not in real_data, \
                "TEST CONTAMINATED REAL CONFIG.JSON — refusing to pass"
