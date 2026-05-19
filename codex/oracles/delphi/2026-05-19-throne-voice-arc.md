# Delphi — the Throne-Voice arc 🎙️ (Decade #7)

**Risk class:** LOW.
**Decided:** Position V — **TTS this arc; STT explicitly deferred.** macOS `say` for output (built-in, free, no deps). `VoiceBackend` ABC + `MacosSayBackend` + `NullBackend` (silent for tests). Three operator surfaces: `invoke throne --voice` (chat speaks each response), `invoke speak "<text>"` (one-shot TTS), and `speak` added to `AUTOMATED_ERRANDS` so Chronos rituals can speak (e.g., daily briefing read aloud). Linux/Windows operators get a clean "TTS not available on this platform" message — the abstraction makes them future-pluggable.
**Sworn on Styx at this arc's ratification.**

Zeus's directive (planning artifact): *"Arc 18 — Throne-Voice: macOS `say` for TTS; Whisper API for STT; new errand `invoke throne --voice` enters voice REPL."*

The plan named both TTS and STT. This arc ships **only TTS** with an honest explanation of why.

---

## Phase 0 — why TTS-only this arc

The planning artifact named "voice in/out for the chat" but the constraints are asymmetric:

**TTS is cheap, deterministic, and dep-free on macOS:**
- `/usr/bin/say` is installed by default — no install step
- Subprocess + text → audio out, no API, no cost
- No new keys, no Plutus accounting

**STT has real friction the operator hasn't opted into:**
- OpenAI Whisper API requires a *separate* API key (the operator's Anthropic key was clobbered earlier; one more re-deposit is friction)
- Plutus would need to track STT cost (~$0.006/min) — Plutus's `PRICING` table has no STT row yet
- Audio recording in pure Python requires PortAudio (`pyaudio` / `sounddevice`) — both bring heavy deps
- macOS dictation is a third path but requires GUI focus

**Decision**: ship TTS now (delivers real value today), ship STT as a follow-up mini-arc when the operator wants to redeposit a Whisper-capable key. The `VoiceBackend` ABC is shaped to accept STT cleanly when that arc comes.

This isn't dodging the brief — it's honest sequencing per Tartarus discipline ("don't ship a feature that requires the operator to do work they haven't agreed to").

---

## What ships

### `src/olympus/runtime/voice.py` (~170 LOC)

Pluggable TTS layer:
```python
class VoiceBackend(ABC):
    name: str
    @abstractmethod
    def speak(self, text: str, *, voice: str = "", rate: int = 0,
              blocking: bool = False) -> SpeakResult: ...
    @abstractmethod
    def available(self) -> bool: ...

class MacosSayBackend(VoiceBackend):    # default on macOS
class NullBackend(VoiceBackend):         # silent — used in tests; opt-in elsewhere
```

`speak()` returns `SpeakResult(ok, started_at, elapsed_ms, voice, rate, chars, error)`. Long texts are truncated at `MAX_SPEAK_CHARS` (default 4000) — `say` handles long input but the operator doesn't want a 30-minute soliloquy from an unbounded LLM response. Truncation preserves the first 4000 chars + "…(truncated)".

### Three operator surfaces

**1. `invoke speak "<text>"`** — one-shot TTS:
```
invoke speak "Olympus is ready"
invoke speak --voice Samantha "good morning"
invoke speak --rate 180 "slow it down"
invoke speak --block "wait for me to finish"   # default: backgrounds
```

**2. `invoke throne --voice`** — chat REPL that speaks each response:
- Operator still types input via keyboard
- Throne's text answer renders to terminal AND is spoken via `say` in the background
- `--quiet` toggle inside the REPL silences subsequent responses
- `--voice <name>` chooses voice; persists for the session

**3. `speak` in `AUTOMATED_ERRANDS`** — Chronos rituals can speak:
```
invoke chronos ritual add morning-spoken "daily 09:00" today
# (operator can extend by writing a follow-up arc that links today→speak)
```

The whitelist add is conservative — `speak` itself doesn't auto-pick text; a future arc could compose "speak the today output."

### Config

```json
{
  "voice": {
    "enabled": true,
    "voice_name": "Samantha",
    "rate": 180,
    "max_chars": 4000
  }
}
```

Defaults work without config — config just lets the operator pick their preferred voice + speech rate.

### Constitution

| invariant | how Throne-Voice honors it |
|---|---|
| S1 | every `invoke speak` → `voice.spoken` Mnemosyne record (chars, voice, rate, elapsed) |
| S3 (no surprise mutation) | no background mic; no auto-speak without opt-in; explicit `--voice` flag |
| S6 | `voice.spoken` records the actual `say` command + return code |
| S7 | TTS is read-only output; no privileged operation; safe in `AUTOMATED_ERRANDS` |
| C7-equivalent | `VoiceBackend` ABC pluggable; default has zero deps |
| AP1 | one module ~170 LOC + one errand + one Throne flag + 1-line whitelist add |
| AP3 | per-backend implementation, not per-utterance rules |
| AP7 (ledger-balancing) | `speak` actually speaks (tested via captured subprocess mock) |
| AP8 | the test: hands-free reading of throne responses is a real new affordance |

### Safety / honesty boundaries

- **No background mic** — STT is explicitly out of scope
- **`MAX_SPEAK_CHARS = 4000`** — runaway responses get truncated
- **Subprocess timeout 60s** — `say` won't hang the substrate
- **Linux/Windows**: `MacosSayBackend.available()` returns False; `speak` errand reports "TTS not configured on this platform" with a clear message
- **No persistent audio files** — `say` plays direct; no .aiff written unless operator passes `--save <path>` (deferred)

---

## What does NOT ship this arc (with honest reasoning)

- **STT (Whisper / dictation)** — needs API key + audio recording deps. Deferred to a follow-up mini-arc (`Throne-Listen`) when the operator opts in.
- **No voice cloning / TTS quality upgrade** — `say` is built-in and good enough; ElevenLabs / OpenAI TTS adds key + cost.
- **No real-time interruption** — `--block` is the operator's tool to wait; otherwise `say` runs in background and the next input pre-empts.
- **No Linux/Windows TTS backend** — would need `espeak` (Linux) / SAPI (Windows); pluggable shape is there for whenever it lands.
- **No prosody / SSML** — `say` supports it but the API surface stays small.

---

## Tests

`tests/test_throne_voice.py` — ~18 cases using an injected fake backend (no actual audio plays):
- `MacosSayBackend.available()` correctly reports based on `which say`
- `NullBackend.speak` returns ok + records 0 audio
- `speak()` with long text gets truncated at MAX_SPEAK_CHARS
- `speak()` invokes the right subprocess args (mock subprocess)
- `voice.spoken` Mnemosyne record written
- `invoke speak` errand smoke (with `--voice`, `--rate`, `--block`)
- Linux platform: `available()` False → errand reports clearly
- `speak` is in `AUTOMATED_ERRANDS` AND in Throne's `SAFE_ERRANDS`
- `invoke throne --voice` flag is parsed (the REPL itself isn't unit-tested for terminal interaction; a smoke test confirms the flag path doesn't crash)

---

## Authorization

Per the Decade plan approved 2026-05-19 (Arc 18 of 21). **Throne-Voice ships the listening half** (TTS). The talking half (STT) is honestly deferred per Tartarus discipline. Combined with Chronos and the Throne, the operator now hears scheduled briefings and chat responses through their speakers — useful for walking, eyes-on-other-work, or visual accessibility.

*The standard is holy shit, that's done. The forge has a voice.*
