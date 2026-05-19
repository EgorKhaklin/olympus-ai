# Delphi — the Hermes-MCP arc 🪶 (Decade #8)

**Risk class:** MEDIUM.
**Decided:** Position H — `src/olympus/runtime/mcp_server.py` implements a **minimal pure-Python MCP server** over stdio (JSON-RPC 2.0, line-delimited JSON). Exposes the existing 14 `SAFE_ERRANDS` as MCP tools — same constitutional whitelist as the Throne, no new gating to invent. Logs to stderr only (stdout is the MCP protocol channel). New errand `invoke mcp` runs the server. The operator wires it into Claude Code (or any MCP-capable client) via their `mcp_servers.json` config; we document the snippet but do not write to the operator's IDE config.
**Sworn on Styx at this arc's ratification.**

Zeus's directive (planning artifact): *"Arc 19 — Hermes-MCP: expose Olympus as MCP server. Claude Code can call `mcp__olympus__*` tools without leaving the editor."*

---

## Phase 0 — what MCP is + why this matters

The **Model Context Protocol** (MCP) is Anthropic's standard for connecting AI models to external tools. An MCP server exposes a set of named tools; an MCP-capable client (Claude Code, Claude Desktop, etc.) discovers tools, calls them with JSON arguments, and gets structured responses back.

The operator is currently in Claude Code. Today they leave Claude Code to run `invoke <errand>` in another terminal. After this arc: they ask Claude Code "what's the substrate doing?" and Claude Code calls `mcp__olympus__doctor()` directly — same conversation, no context-switch.

**The constitutional alignment is exact**: MCP tools are LLM-callable affordances; SAFE_ERRANDS is the set Throne's LLM is allowed to call; therefore MCP exposes SAFE_ERRANDS. **No new whitelist to invent — same one, different transport.**

---

## What ships

### `src/olympus/runtime/mcp_server.py` (~280 LOC)

Pure-Python implementation of the MCP wire protocol. No `mcp` package dep; protocol is small enough to implement directly:

- JSON-RPC 2.0 over line-delimited JSON on stdin/stdout
- Methods handled:
  - **`initialize`** — handshake; returns `{protocolVersion, serverInfo, capabilities}`
  - **`initialized`** — client notification; no response
  - **`tools/list`** — returns the 14 SAFE_ERRANDS as MCP tool descriptors
  - **`tools/call`** — executes one errand; returns `{content: [{type: "text", text: "..."}]}`
  - **`ping`** — health check
  - **`prompts/list` / `resources/list`** — return empty (we don't expose those yet)
- Unknown methods → JSON-RPC `error` response (code -32601 method not found)
- Malformed JSON → JSON-RPC `error` (-32700 parse error)
- All logging goes to **stderr** (stdout is the protocol channel)
- Each tool call → `mnemosyne.remember(kind="mcp.tool_call", ...)` for the audit-of-record

### Tool descriptor for each errand

```json
{
  "name": "doctor",
  "description": "single-screen health diagnostic (no args)",
  "inputSchema": {
    "type": "object",
    "properties": {
      "args": {
        "type": "string",
        "description": "Arguments passed to the errand (space-separated string; will be tokenized)"
      }
    },
    "additionalProperties": false
  }
}
```

The schema is intentionally uniform across all 14 errands. Errand-specific argv handling stays in the errand's existing implementation; the MCP layer just tokenizes the `args` string. No per-tool schema authoring overhead.

### `invoke mcp` errand

```
invoke mcp                  # serve on stdio (default; for Claude Code spawn)
invoke mcp --probe          # one-shot: print server info + tool list to stderr; exit
```

The `--probe` flag is for operator-debugging: confirms the server can boot without actually entering the stdio loop.

### Constitutional posture

| invariant | how Hermes-MCP honors it |
|---|---|
| S1 | every tool call → `mcp.tool_call` Mnemosyne record (tool, args, exit_code, elapsed_ms, output_head) |
| S6 | every response cites the errand that produced it; exit code surfaces in JSON-RPC result |
| S7 (HIGH-risk gated) | tools/list exposes ONLY `SAFE_ERRANDS`; tools/call refuses anything not in that set; GATED ops never reachable |
| C7-equivalent | protocol implementation is pluggable (stdio is one of many possible transports); the routing layer is independent |
| AP1 | one new module ~280 LOC + one errand + docs snippet |
| AP3 | one uniform tool schema across 14 errands; no per-tool special cases |
| AP7 (ledger-balancing) | `tools/call` actually runs the errand and returns its real stdout |

### Operator setup (in Claude Code config)

`~/.claude/mcp_servers.json` (or wherever the operator's Claude Code config lives):
```json
{
  "mcpServers": {
    "olympus": {
      "command": "/Users/vanta/.local/bin/invoke",
      "args": ["mcp"]
    }
  }
}
```

After restarting Claude Code, the operator can:
- Ask "use olympus to check substrate health"
- Claude Code calls `mcp__olympus__doctor()`
- Output flows back into the Claude conversation

**We do NOT write to the operator's IDE config.** That's their file; we ship the snippet for them to copy.

---

## Safety boundaries (named explicitly)

- **GATED_ERRANDS are NEVER exposed** — tools/list filters to SAFE_ERRANDS only; tools/call rejects anything else with `{ok: false, error: "..."}`
- **stderr-only logging** — stdout is the protocol channel; any errant print to stdout would corrupt the JSON-RPC stream
- **Per-call timeout** — each errand has 60s budget (same as throne-routing) before returning a timeout error
- **JSON parse errors return structured errors** — never crash the server
- **No state mutation beyond what the errand itself does** — the MCP layer is a thin shell
- **stdin EOF → clean shutdown** — when the client disconnects, the server exits with code 0

---

## What does NOT ship this arc

- **No `prompts/list`** — Olympus doesn't have curated prompts to expose yet
- **No `resources/list`** — Mnemosyne records could be exposed but the schema needs design; defer
- **No HTTP transport** — stdio only this arc; future arc could add SSE for remote clients
- **No bidirectional notification** — server doesn't push updates to client mid-call
- **No tool argument typing beyond `string`** — uniform schema; future per-tool schemas possible
- **No Throne-side change** — Throne stays unchanged; MCP is a parallel surface using the same whitelist
- **No streaming responses** — each tools/call returns complete output

---

## Tests

`tests/test_mcp_server.py` — ~25 cases using injected stdin/stdout streams (no real subprocess):
- `initialize` returns correct shape (protocolVersion, serverInfo, capabilities)
- `tools/list` returns exactly the SAFE_ERRANDS set (14 tools)
- `tools/list` does NOT include any GATED_ERRAND name
- Each tool descriptor has name + description + inputSchema
- `tools/call` runs a real errand (e.g., doctor) and returns text content
- `tools/call` on unknown tool returns JSON-RPC error
- `tools/call` on a GATED errand (e.g., "kindle") returns error — even if smuggled past tools/list
- `ping` returns empty result
- Malformed JSON line returns parse-error response
- Unknown method returns method-not-found error
- `prompts/list` returns empty array
- `resources/list` returns empty array
- `mcp.tool_call` Mnemosyne record written per call
- stdin EOF causes clean shutdown (loop exits)
- `--probe` mode prints info to stderr and exits 0

---

## Authorization

Per the Decade plan approved 2026-05-19 (Arc 19 of 21). **Hermes-MCP brings Olympus inside Claude Code.** The Throne (chat) and MCP (Claude-Code integration) are now two transports over the same constitutional whitelist — when the operator opens this very editor, the substrate is a function call away.

*The standard is holy shit, that's done. The messenger god speaks the new protocol.*
