"""tests/test_throne_voice.py — the Throne-Voice arc (TTS only).

Per Delphi 2026-05-19-throne-voice-arc.md.

STT is explicitly deferred; tests cover the TTS surface only.
No actual audio plays — tests inject a FakeSubprocess.
"""
from __future__ import annotations

import contextlib
import io
import shutil

import pytest

from olympus.runtime.voice import (
    VoiceBackend, NullBackend, MacosSayBackend,
    SpeakResult, default_backend, get_backend, set_backend, speak,
    MAX_SPEAK_CHARS,
)
from olympus.runtime.errand_whitelist import AUTOMATED_ERRANDS
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────────────────
# Fake subprocess module for MacosSayBackend injection
# ─────────────────────────────────────────────────────────────────────


class _FakeProc:
    def __init__(self, *, returncode=0, stderr=""):
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = ""

    def communicate(self, input=None, timeout=None):
        return (b"", b"")


class _FakeStdin:
    def __init__(self):
        self.written: bytes = b""
        self.closed = False
    def write(self, data):
        self.written += data
    def close(self):
        self.closed = True


class _FakePopen(_FakeProc):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.communicate_called_with = None
        self.stdin = _FakeStdin()

    def communicate(self, input=None, timeout=None):
        self.communicate_called_with = input
        return (b"", b"")


class FakeSubprocess:
    """Quacks like the subprocess module for `say` invocations."""
    PIPE = -1
    DEVNULL = -3

    def __init__(self):
        self.run_calls: list[dict] = []
        self.popen_calls: list[dict] = []

    def run(self, cmd, **kwargs):
        self.run_calls.append({"cmd": cmd, **kwargs})
        return _FakeProc(returncode=0)

    def Popen(self, cmd, **kwargs):
        self.popen_calls.append({"cmd": cmd, **kwargs})
        return _FakePopen()


# ─────────────────────────────────────────────────────────────────────
# Backend availability
# ─────────────────────────────────────────────────────────────────────


class TestBackendAvailability:

    def test_null_always_available(self):
        assert NullBackend().available() is True

    def test_macos_say_availability_matches_path(self):
        b = MacosSayBackend()
        expected = shutil.which("say") is not None
        assert b.available() is expected

    def test_default_backend_picks_macos_on_mac(self):
        # On the test machine, `say` exists → MacosSayBackend
        b = default_backend()
        if shutil.which("say"):
            assert isinstance(b, MacosSayBackend)
        else:
            assert isinstance(b, NullBackend)


# ─────────────────────────────────────────────────────────────────────
# NullBackend behavior
# ─────────────────────────────────────────────────────────────────────


class TestNullBackend:

    def test_speak_succeeds_silently(self):
        r = NullBackend().speak("hello world", voice="Samantha", rate=200)
        assert isinstance(r, SpeakResult)
        assert r.ok
        assert r.backend == "null"
        assert r.chars == len("hello world")
        assert r.voice == "Samantha"
        assert r.rate == 200


# ─────────────────────────────────────────────────────────────────────
# MacosSayBackend with injected subprocess
# ─────────────────────────────────────────────────────────────────────


class TestMacosSayBackend:

    def test_speak_blocking_invokes_subprocess_run(self):
        fake = FakeSubprocess()
        b = MacosSayBackend(subprocess_module=fake)
        r = b.speak("hello", blocking=True)
        assert r.ok, f"got error: {r.error}"
        assert len(fake.run_calls) == 1
        call = fake.run_calls[0]
        assert call["cmd"][0] == "say"
        assert call["input"] == "hello"

    def test_speak_passes_voice_and_rate(self):
        fake = FakeSubprocess()
        b = MacosSayBackend(subprocess_module=fake)
        b.speak("hi", voice="Samantha", rate=200, blocking=True)
        cmd = fake.run_calls[0]["cmd"]
        assert "-v" in cmd
        assert cmd[cmd.index("-v") + 1] == "Samantha"
        assert "-r" in cmd
        assert cmd[cmd.index("-r") + 1] == "200"

    def test_speak_nonblocking_uses_popen(self):
        fake = FakeSubprocess()
        b = MacosSayBackend(subprocess_module=fake)
        r = b.speak("hello", blocking=False)
        assert r.ok
        assert len(fake.popen_calls) == 1
        assert fake.run_calls == []

    def test_empty_text_errors_cleanly(self):
        fake = FakeSubprocess()
        b = MacosSayBackend(subprocess_module=fake)
        r = b.speak("")
        assert not r.ok
        assert "empty" in r.error.lower()
        assert fake.run_calls == []
        assert fake.popen_calls == []

    def test_truncates_long_text(self):
        fake = FakeSubprocess()
        b = MacosSayBackend(subprocess_module=fake)
        long = "X" * (MAX_SPEAK_CHARS + 100)
        r = b.speak(long, blocking=True)
        assert r.truncated
        assert r.chars <= MAX_SPEAK_CHARS + 20  # +len("…(truncated)")
        # And the input passed to subprocess is also truncated
        passed = fake.run_calls[0]["input"]
        assert "…(truncated)" in passed


# ─────────────────────────────────────────────────────────────────────
# speak() module-level convenience + Mnemosyne recording
# ─────────────────────────────────────────────────────────────────────


class TestSpeakRecording:

    def test_speak_records_to_mnemosyne(self):
        # Use NullBackend so no audio plays
        set_backend(NullBackend())
        before = len(mnemosyne.recall("voice.spoken"))
        speak("test phrase for recording")
        after = len(mnemosyne.recall("voice.spoken"))
        assert after == before + 1

    def test_recorded_payload_has_backend_and_chars(self):
        set_backend(NullBackend())
        speak("phrase X")
        latest = mnemosyne.recall("voice.spoken")[-1]
        assert latest.body["backend"] == "null"
        assert latest.body["chars"] == len("phrase X")

    def test_speak_no_record_when_record_false(self):
        set_backend(NullBackend())
        before = len(mnemosyne.recall("voice.spoken"))
        speak("ignored", record=False)
        after = len(mnemosyne.recall("voice.spoken"))
        assert after == before


# ─────────────────────────────────────────────────────────────────────
# CLI errand smoke
# ─────────────────────────────────────────────────────────────────────


class TestSpeakErrand:

    def test_registered(self):
        from olympus.cli import hermes
        assert "speak" in hermes._errands

    def test_speak_runs_with_text(self):
        # Ensure backend is null so no audio
        set_backend(NullBackend())
        from olympus.cli import hermes
        errand = hermes._errands["speak"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["hello", "world"])
        assert rc == 0
        assert "spoke" in buf.getvalue().lower()

    def test_speak_usage_on_empty(self):
        from olympus.cli import hermes
        errand = hermes._errands["speak"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn([])
        assert rc == 2

    def test_speak_parses_voice_rate(self):
        set_backend(NullBackend())
        from olympus.cli import hermes
        errand = hermes._errands["speak"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["--voice", "Alex", "--rate", "200",
                              "hello"])
        assert rc == 0


# ─────────────────────────────────────────────────────────────────────
# Whitelist + Throne integration
# ─────────────────────────────────────────────────────────────────────


class TestWhitelistAndThrone:

    def test_speak_in_automated_errands(self):
        assert "speak" in AUTOMATED_ERRANDS

    def test_speak_can_be_used_by_chronos(self):
        """Chronos's whitelist matches AUTOMATED_ERRANDS — speak is
        therefore a valid `do` value for a ritual."""
        from olympus.primordials.chronos import RitualSpec
        spec = RitualSpec(id="r", when="daily 09:00", do="speak")
        ok, err = spec.validate()
        assert ok, err

    def test_throne_repl_accepts_voice_flag(self):
        """Smoke: run() must accept speak_responses kwarg without error.
        We can't drive the interactive loop here; just confirm the
        parameter exists."""
        import inspect
        from olympus.throne.repl import run
        sig = inspect.signature(run)
        assert "speak_responses" in sig.parameters


# ─────────────────────────────────────────────────────────────────────
# Backend swap
# ─────────────────────────────────────────────────────────────────────


class TestBackendSwap:

    def test_set_backend_overrides_default(self):
        custom = NullBackend()
        set_backend(custom)
        assert get_backend() is custom
