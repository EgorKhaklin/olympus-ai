"""notekeeper CLI — `python -m notekeeper <command>`.

Commands:
  capture <text>        capture a note
  list                  list all notes
  topic <name>          list notes by topic
  recent [hours]        recent captures (default 24h)
  stale                 notes older than 30 days
  setup                 register notekeeper eyes + head + predictions with Olympus
  session               run an Olympus session (HYDRA + Argos + Athena + ...)
"""
from __future__ import annotations

import sys
from typing import Iterable


def _print_notes(notes: Iterable) -> None:
    for n in notes:
        topics = ", ".join(n.topics) if n.topics else "(no topics)"
        first_line = n.text.split("\n", 1)[0][:80]
        print(f"  {n.id[:18]}  [{n.captured_at[:19]}]  [{topics}]")
        print(f"    {first_line}")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    if not argv:
        print(__doc__)
        return 0
    cmd = argv[0]

    if cmd == "setup":
        from notekeeper.eyes import register_with_colony
        from notekeeper.heads import attach_to_hydra
        from notekeeper.predictions import register_with_apollo
        register_with_colony()
        attach_to_hydra()
        register_with_apollo()
        print("notekeeper: 3 eyes + 1 head + 2 predictions registered with Olympus")
        return 0

    if cmd == "capture":
        from notekeeper.notes import capture
        text = " ".join(argv[1:])
        if not text:
            print("usage: notekeeper capture <text>"); return 2
        try:
            n = capture(text)
        except ValueError as exc:
            print(f"refused: {exc}"); return 1
        topics = ", ".join(n.topics) if n.topics else "(none)"
        print(f"captured: {n.id[:18]}  topics: {topics}")
        return 0

    if cmd == "list":
        from notekeeper.notes import all_notes
        notes = all_notes()
        if not notes:
            print("no notes yet"); return 0
        _print_notes(notes)
        return 0

    if cmd == "topic" and len(argv) >= 2:
        from notekeeper.notes import by_topic
        notes = by_topic(argv[1])
        if not notes:
            print(f"no notes on topic {argv[1]!r}"); return 0
        _print_notes(notes)
        return 0

    if cmd == "recent":
        from notekeeper.notes import notes_in_window
        hours = float(argv[1]) if len(argv) > 1 else 24.0
        notes = notes_in_window(max_age_hours=hours)
        if not notes:
            print(f"no notes in the last {hours}h"); return 0
        _print_notes(notes)
        return 0

    if cmd == "stale":
        from notekeeper.notes import all_notes
        from olympus.titans.cronus import Cronus
        stale = [n for n in all_notes()
                 if Cronus.age_seconds(n.captured_at) / 86400.0 > 30]
        if not stale:
            print("no stale notes"); return 0
        _print_notes(stale)
        return 0

    if cmd == "session":
        # Registrations don't persist across processes; ensure they're
        # present for THIS process before running the loop.
        from notekeeper.eyes import register_with_colony
        from notekeeper.heads import attach_to_hydra
        from notekeeper.predictions import register_with_apollo
        register_with_colony()
        attach_to_hydra()
        register_with_apollo()

        from olympus.session import Session
        s = Session(directive="notekeeper session")
        r = s.run()
        print(r.render(verbose=True))
        return 1 if r.error else 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
