## What

T003 — Artifact B (Tools Round-Trip Playground). Minimal CLI demonstrating
Claude's native `tools=` JSON schema round-trip from the protocol level,
no SDK abstractions hiding the mechanics. Closes Wk2 of the CCA-F
small-projects plan.

## Why

Hiring managers reading the small-projects portfolio see Artifact A
(`claude-mcp-server-minimal`) and wonder what changes when MCP is OUT
of the picture and you're talking to Claude's API directly. Artifact B
answers that: native `tools=` is its own protocol with its own
`stop_reason` semantics; understanding it is what lets you reason
about retry/escalation without the MCP envelope.

## How verified

- `make check` green: 223 tests passing (scaffold baseline 219 + 4 new
  playground tests).
- VCR cassette `tests/unit/cassettes/test_playground/test_round_trip_happy_path.yaml`
  committed; cassette redacts `authorization` and `x-api-key` headers
  (verified by grep — only `REDACTED` is recorded).
- Manual run: `ANTHROPIC_API_KEY=... uv run python -m claude_tools_roundtrip_playground "How far is Amsterdam from New York in kilometres?"`
  produces all 5 visible steps; `[step 3]` shows local `result: 5863.22`;
  final text references **5,863 kilometres**.
- CI green on this PR (push-time).
- (Post-merge): Smoke green on main.

## Implementation note

The `messages.append({"role": "assistant", "content": ...})` follow-up
turn passes `[block.model_dump() for block in resp.content]` rather
than the raw pydantic objects. Round-tripping pydantic objects back
into a fresh `messages.create(...)` call is fragile across SDK versions;
serializing once at the boundary keeps the loop robust.

## Out of scope

- MCP integration. Different artifact.
- Multi-tool round-trips. Single tool, single round-trip — the protocol
  story is the focus.
- Streaming responses. Synchronous `messages.create` is enough.
- Stripping inherited template scaffolding. Wk5 polish decision.
- Version bump / CHANGELOG.

## Closes

T003 of CCA-F small-projects plan v1; opens Artifact B for Wk5 polish.
