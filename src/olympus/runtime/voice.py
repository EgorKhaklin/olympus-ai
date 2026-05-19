"""olympus.runtime.voice — pluggable TTS layer.

Per Delphi 2026-05-19-throne-voice-arc.md.

This arc ships TTS only; STT is deferred (needs a Whisper-capable API
key the operator hasn't set up + audio-recording dependencies). The
`VoiceBackend` ABC is shaped to accept STT cleanly when that follow-up
arc lands.

Default backend on macOS is `MacosSayBackend` — uses the built-in
`/usr/bin/say` subprocess. No new deps. On Linux/Windows the operator
gets a clean "TTS not configured" message.
"""
from __future__ import annotations

import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────────────────
# Bounds
# ─────────────────────────────────────────────────────────────────────


MAX_SPEAK_CHARS = 4000
DEFAULT_RATE = 180        # words-per-minute; `say` default is ~180
SUBPROCESS_TIMEOUT_S = 60


# ─────────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────────


@dataclass
class SpeakResult:
    ok: bool
    backend: str
    started_at: str
    elapsed_ms: float = 0.0
    voice: str = ""
    rate: int = 0
    chars: int = 0
    truncated: bool = False
    error: str = ""


# ─────────────────────────────────────────────────────────────────────
# Backend ABC
# ─────────────────────────────────────────────────────────────────────


class VoiceBackend(ABC):
    name: str = "abstract"

    @abstractmethod
    def available(self) -> bool:
        """True iff this backend can actually produce speech."""

    @abstractmethod
    def speak(self, text: str, *,
               voice: str = "",
               rate: int = 0,
               blocking: bool = False) -> SpeakResult:
        """Speak `text`. Returns SpeakResult. Truncates text at
        MAX_SPEAK_CHARS. `blocking=False` runs in background."""


# ─────────────────────────────────────────────────────────────────────
# NullBackend — silent (default in tests + on unsupported platforms)
# ─────────────────────────────────────────────────────────────────────


class NullBackend(VoiceBackend):
    """Silent backend. Records the speak() call but produces no audio.
    Used as the fallback when no real TTS is available."""

    name = "null"

    def available(self) -> bool:
        return True   # always callable, just doesn't make noise

    def speak(self, text: str, *,
               voice: str = "", rate: int = 0,
               blocking: bool = False) -> SpeakResult:
        return SpeakResult(
            ok=True, backend=self.name,
            started_at=Nyx.now().isoformat(),
            elapsed_ms=0.0, voice=voice, rate=rate,
            chars=len(text or ""),
            truncated=False,
        )


# ─────────────────────────────────────────────────────────────────────
# MacosSayBackend — /usr/bin/say
# ─────────────────────────────────────────────────────────────────────


class MacosSayBackend(VoiceBackend):
    """Wraps the macOS `say` command. Zero new deps; preinstalled on
    every modern macOS."""

    name = "macos-say"

    def __init__(self, *, executable: str = "say",
                  subprocess_module=subprocess) -> None:
        self._executable = executable
        self._sp = subprocess_module   # injectable for tests

    def available(self) -> bool:
        return shutil.which(self._executable) is not None

    def speak(self, text: str, *,
               voice: str = "", rate: int = 0,
               blocking: bool = False) -> SpeakResult:
        started = time.perf_counter()
        result = SpeakResult(
            ok=False, backend=self.name,
            started_at=Nyx.now().isoformat(),
            voice=voice, rate=rate,
        )
        if not text or not text.strip():
            result.error = "empty text"
            return result
        # Truncate
        if len(text) > MAX_SPEAK_CHARS:
            text = text[:MAX_SPEAK_CHARS] + "…(truncated)"
            result.truncated = True
        result.chars = len(text)
        if not self.available():
            result.error = "`say` not available on this system"
            return result
        cmd: list[str] = [self._executable]
        if voice:
            cmd += ["-v", voice]
        if rate and rate > 0:
            cmd += ["-r", str(int(rate))]
        try:
            if blocking:
                proc = self._sp.run(
                    cmd, input=text, text=True,
                    timeout=SUBPROCESS_TIMEOUT_S,
                    capture_output=True)
                if proc.returncode != 0:
                    result.error = (proc.stderr or
                                     f"exit={proc.returncode}")[:200]
                else:
                    result.ok = True
            else:
                # True non-blocking: spawn, write to stdin, close.
                # The `say` process runs in the background; we do not
                # wait for it. The operator hears audio play out while
                # the REPL continues.
                proc = self._sp.Popen(
                    cmd, stdin=self._sp.PIPE,
                    stdout=self._sp.DEVNULL,
                    stderr=self._sp.DEVNULL)
                if proc.stdin is not None:
                    try:
                        proc.stdin.write(text.encode("utf-8"))
                    finally:
                        proc.stdin.close()
                result.ok = True
        except subprocess.TimeoutExpired:
            result.error = (f"timeout after "
                             f"{SUBPROCESS_TIMEOUT_S}s "
                             "(blocking path)")
        except FileNotFoundError:
            result.error = f"executable not found: {self._executable}"
        except Exception as exc:  # noqa: BLE001
            result.error = f"{type(exc).__name__}: {exc}"
        result.elapsed_ms = (time.perf_counter() - started) * 1000.0
        return result


# ─────────────────────────────────────────────────────────────────────
# Default backend resolution
# ─────────────────────────────────────────────────────────────────────


def default_backend() -> VoiceBackend:
    """Pick the right backend for this platform. macOS → MacosSayBackend
    if `say` is on PATH; else NullBackend."""
    mac = MacosSayBackend()
    if mac.available():
        return mac
    return NullBackend()


_BACKEND: VoiceBackend | None = None


def get_backend() -> VoiceBackend:
    """Module-level singleton (memoized)."""
    global _BACKEND
    if _BACKEND is None:
        _BACKEND = default_backend()
    return _BACKEND


def set_backend(b: VoiceBackend) -> None:
    """For tests + config overrides."""
    global _BACKEND
    _BACKEND = b


# ─────────────────────────────────────────────────────────────────────
# Public convenience — speak + record to Mnemosyne
# ─────────────────────────────────────────────────────────────────────


def speak(text: str, *,
           voice: str = "",
           rate: int = 0,
           blocking: bool = False,
           record: bool = True) -> SpeakResult:
    """Speak `text` via the active backend. Records `voice.spoken` to
    Mnemosyne unless `record=False` (rare, for tests)."""
    backend = get_backend()
    result = backend.speak(text, voice=voice, rate=rate,
                            blocking=blocking)
    if record:
        mnemosyne.remember(
            kind="voice.spoken",
            actor="voice",
            summary=(f"{backend.name} spoke "
                     f"{result.chars}c voice={voice or '(default)'} "
                     f"rate={rate or '(default)'} "
                     f"{result.elapsed_ms:.0f}ms"
                     + (" TRUNCATED" if result.truncated else "")
                     + (f" ERROR={result.error[:60]}"
                        if result.error else "")),
            backend=backend.name,
            voice=voice, rate=rate,
            chars=result.chars,
            truncated=result.truncated,
            elapsed_ms=result.elapsed_ms,
            error=result.error,
            blocking=blocking,
        )
    return result


__all__ = [
    "VoiceBackend", "NullBackend", "MacosSayBackend",
    "SpeakResult",
    "default_backend", "get_backend", "set_backend", "speak",
    "MAX_SPEAK_CHARS", "DEFAULT_RATE",
]
