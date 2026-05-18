#!/usr/bin/env bash
# loop.sh — Olympus self-improvement cron loop.
#
# Per Delphi 2026-05-18-self-improvement-arc.md: bash is pure orchestration
# here. No logic. Cron triggers this script; the script calls `invoke
# session` (one cognitive pass) and `invoke improve` (one Prometheus pass);
# logs to state/loop.log. Safe to install in crontab.
#
# Usage:
#   ./scripts/loop.sh                    # one pass
#   ./scripts/loop.sh --loop             # continuous, default 600s interval
#   ./scripts/loop.sh --loop --interval 300
#   ./scripts/loop.sh --dry-run          # show what would run, don't run
#
# Crontab example (every 10 minutes):
#   */10 * * * * /Users/vanta/Desktop/Olympus/scripts/loop.sh >> /tmp/olympus-cron.log 2>&1
#
# Environment:
#   OLYMPUS_HOME       repo root (default: derived from this script's path)
#   OLYMPUS_LOG        log file (default: $OLYMPUS_HOME/state/loop.log)
#   OLYMPUS_INTERVAL   seconds between iterations (default: 600)
#   OLYMPUS_DIRECTIVE  directive passed to invoke session (default: empty)

set -euo pipefail

# ─────────────────────────────────────────────────────────
# Locate the repo so cron's blank cwd doesn't break us
# ─────────────────────────────────────────────────────────

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
OLYMPUS_HOME="${OLYMPUS_HOME:-$(dirname "$SCRIPT_PATH")}"
OLYMPUS_LOG="${OLYMPUS_LOG:-$OLYMPUS_HOME/state/loop.log}"
OLYMPUS_INTERVAL="${OLYMPUS_INTERVAL:-600}"
OLYMPUS_DIRECTIVE="${OLYMPUS_DIRECTIVE:-}"
INVOKE="$OLYMPUS_HOME/scripts/invoke"

# ─────────────────────────────────────────────────────────
# Parse flags
# ─────────────────────────────────────────────────────────

CONTINUOUS=0
DRY_RUN=0
MAX_ITERATIONS=-1

while [[ $# -gt 0 ]]; do
    case "$1" in
        --loop)        CONTINUOUS=1; shift ;;
        --interval)    OLYMPUS_INTERVAL="$2"; shift 2 ;;
        --count)       MAX_ITERATIONS="$2"; shift 2 ;;
        --dry-run)     DRY_RUN=1; shift ;;
        --directive)   OLYMPUS_DIRECTIVE="$2"; shift 2 ;;
        -h|--help)
            sed -n '1,30p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)  echo "loop.sh: unknown flag: $1" >&2; exit 2 ;;
    esac
done

# ─────────────────────────────────────────────────────────
# Pre-flight: substrate exists, invoke is callable
# ─────────────────────────────────────────────────────────

if [[ ! -d "$OLYMPUS_HOME/src/olympus" ]]; then
    echo "loop.sh: cannot find Olympus at $OLYMPUS_HOME" >&2
    exit 1
fi
if [[ ! -x "$INVOKE" ]]; then
    echo "loop.sh: invoke script not executable: $INVOKE" >&2
    exit 1
fi
mkdir -p "$(dirname "$OLYMPUS_LOG")"

# ─────────────────────────────────────────────────────────
# Logging helpers
# ─────────────────────────────────────────────────────────

ts() { date -u "+%Y-%m-%dT%H:%M:%SZ"; }
log() { echo "[$(ts)] $*" | tee -a "$OLYMPUS_LOG"; }

# ─────────────────────────────────────────────────────────
# One pass = one session + one improvement
# ─────────────────────────────────────────────────────────

run_pass() {
    local i="$1"
    log "pass $i — beginning"

    local session_cmd=("$INVOKE" --quiet session)
    if [[ -n "$OLYMPUS_DIRECTIVE" ]]; then
        session_cmd+=("$OLYMPUS_DIRECTIVE")
    fi

    if [[ $DRY_RUN -eq 1 ]]; then
        log "  DRY-RUN would run: ${session_cmd[*]}"
        log "  DRY-RUN would run: $INVOKE --quiet improve"
        log "pass $i — dry-run complete"
        return 0
    fi

    # Session phase
    if "${session_cmd[@]}" >> "$OLYMPUS_LOG" 2>&1; then
        log "  session — succeeded"
    else
        log "  session — FAILED (exit $?)"
        # Don't bail; improve may still produce value.
    fi

    # Improvement phase — Prometheus
    if "$INVOKE" --quiet improve >> "$OLYMPUS_LOG" 2>&1; then
        log "  improve — succeeded"
    else
        log "  improve — FAILED (exit $?)"
    fi

    log "pass $i — complete"
}

# ─────────────────────────────────────────────────────────
# Main: single-shot (cron's job) or continuous (foreground)
# ─────────────────────────────────────────────────────────

if [[ $CONTINUOUS -eq 0 ]]; then
    run_pass 1
    exit 0
fi

log "loop — starting; interval=${OLYMPUS_INTERVAL}s; max=${MAX_ITERATIONS}"
i=0
trap 'log "loop — caught SIGINT; exiting after pass $i"; exit 0' INT TERM

while :; do
    i=$((i + 1))
    run_pass "$i"
    if [[ $MAX_ITERATIONS -gt 0 && $i -ge $MAX_ITERATIONS ]]; then
        log "loop — reached max iterations ($MAX_ITERATIONS); exiting"
        break
    fi
    sleep "$OLYMPUS_INTERVAL"
done
