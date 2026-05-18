# style

Olympus's written voice — the constitutional tone for code, docs,
commit messages, and Delphi entries.

## Prose

- **Declarative.** State what is. Do not hedge.
- **No em-dashes** in human-readable prose. Use commas, semicolons,
  or periods.
- **No filler.** "It should be noted that…" is filler. Say the thing.
- **The mythology earns its presence.** Don't name a god in prose
  unless that god's role is what the sentence is about. Random
  mythological flavor reads as larping.

## Comments

- **Default to no comments.** Code with good names doesn't need them.
- **Comment when the WHY is non-obvious.** A hidden invariant, a
  subtle constraint, a non-obvious tradeoff.
- **Do not comment what the code does.** Identifiers already say that.

## Docstrings

- **Open with the mythological role** for any deity module. One
  sentence on what the god / hero / monster IS in Greek myth.
- **Then name the cognitive concern.** One sentence on what role
  in the substrate the mythology maps to.
- **Then the API.** Specifics belong here, not in long-form docs.

## Commits

- Imperative mood for the subject.
- One line, under 70 chars when possible.
- Body explains *why*, not *what*. The diff says what.
- Reference the Delphi if one was opened.

## Refusing larp

When prose starts describing routine work in cosmic-significance
terms ("the hearth was lit," "the oaths bound"), name the pattern
(Momus AP1: self-observation without ground-touch) and edit it back
down. The mythology is the architecture, not a costume.
