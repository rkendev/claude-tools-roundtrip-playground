# claude-tools-roundtrip-playground

[![CI](https://github.com/rkendev/claude-tools-roundtrip-playground/actions/workflows/ci.yml/badge.svg)](https://github.com/rkendev/claude-tools-roundtrip-playground/actions/workflows/ci.yml)

Minimal CLI showing Claude's native `tools=` JSON schema round-trip from
the API protocol level. Send a tool definition, watch Claude emit a
`tool_use`, execute the tool, send the `tool_result` back, see Claude's
final text. No SDK magic, no agent framework — just the protocol.

Built as Artifact B of a Claude Certified Architect Foundations
small-projects portfolio. Companion to
[claude-mcp-server-minimal](https://github.com/rkendev/claude-mcp-server-minimal)
(Artifact A).

> Repo bootstrapped from my own `roy-ai-template@v0.5.0` starter; the
> round-trip CLI is original.

## Round-trip walkthrough

```bash
ANTHROPIC_API_KEY=sk-ant-... \
  uv run python -m claude_tools_roundtrip_playground \
    "How far is Amsterdam from New York in kilometres?"
```

Example output (trimmed for brevity):

```
[step 1] tool schema sent to Claude:
{
  "name": "compute_haversine_distance_km",
  "description": "Great-circle distance between two lat/lon points...",
  "input_schema": {
    "type": "object",
    "properties": {
      "lat1": {"type": "number"}, ...
    },
    "required": ["lat1", "lon1", "lat2", "lon2"],
    "additionalProperties": false
  }
}

[step 2] Claude's first response: stop_reason=tool_use, ...
[step 3] executing tool locally: result=5863.32
[step 4] tool_result sent back to Claude...
[step 5] Claude's final response: stop_reason=end_turn
  "Amsterdam is approximately 5,863 kilometres from New York..."
```

Why this matters: most "tool use" tutorials hide the protocol behind an
SDK convenience method. This CLI makes every step of the round-trip
visible so you can see (a) the JSON schema Claude actually receives,
(b) what `stop_reason` controls the loop, (c) how `tool_result` plumbs
back into the next request. The exam quizzes on these mechanics; the
hiring conversations want to see you've worked through them.

`make check` runs the round-trip test offline against the committed
[VCR cassette](tests/unit/cassettes/test_playground/test_round_trip_happy_path.yaml) — no API key required for CI.

## Inherited template scaffolding (background)

The sections below describe the upstream template's three-tier LLM
adapter, contract suite, and quality gate. They aren't load-bearing for
the round-trip artifact — kept for transparency and so `make check`
remains the canonical local gate.

## Quick start

```bash
# Copy .env.example and fill in any keys you want to exercise.
cp .env.example .env
$EDITOR .env

# Install dependencies (including dev extras — ruff, mypy, pytest, etc.).
uv sync --all-extras

# Install pre-commit's git hook so trailing-whitespace / EOF / line-ending
# auto-fixes fire at commit time. Skipping this means CI catches drift
# (auto-fix hooks aren't part of `make check`).
uv run pre-commit install

# Run the full quality gate: lint + type + security + 219 tests + auto-fix hooks.
make check
```

Need offline Ollama backing? `./scripts/smoke.sh` brings up a
digest-pinned Ollama container and verifies it's healthy.

## What this gives you

A shaped starting point, not a framework. Three layers with a strict
dependency rule (see [`ARCHITECTURE.md`](ARCHITECTURE.md)):

- **`domain/`** — types, invariants, errors. Pure Python; Pydantic is
  the only third-party import allowed.
- **`application/`** — ports (`LLMPort`, `ConfigPort`, `LoggerPort`)
  and the `FallbackModel` orchestrator. Depends on `domain/` only.
- **`infrastructure/`** — SDK adapters (Anthropic, OpenAI, Ollama) and
  the `pydantic-settings` loader. Only layer that imports vendor SDKs
  or reads the environment.
- **`main.py`** — the single composition root. `build_llm(settings)`
  wires a single adapter or a `FallbackModel` stack depending on
  `LLM_TIER`.

The 32-case contract suite in `tests/contract/` is the architectural
drift detector: any new adapter registered with
`tests/contract/conftest.py::LLM_ADAPTERS` inherits eight behavioural
assertions automatically — vendor-tagged failures
(`test_returns_response[anthropic]`) pinpoint which implementation
drifted, not which test broke.

## Make targets

Run `make help` for the full list. The core surface:

| Target | What it does |
| --- | --- |
| `check` | ruff + ruff-format + mypy + bandit + 219 unit/contract tests. The default quality gate. |
| `fmt` | Auto-fix formatting with ruff. |
| `lint` | ruff lint only (no format pass). |
| `typecheck` | mypy strict on `src/` + `tests/`. |
| `security` | bandit -ll on `src/`. |
| `test` | pytest unit + contract, with coverage. |
| `integration` | pytest -m integration (requires docker-compose; skips if empty). |
| `smoke` | `./scripts/smoke.sh` — docker compose up + healthcheck for Ollama. |
| `build` | `uv build` — sdist + wheel. |
| `parity` | `scripts/check_version_parity.py` — asserts ruff/mypy/bandit pins match between `pyproject.toml` and `.pre-commit-config.yaml`. |
| `example-all-tiers` | Run all three examples back-to-back (needs API keys for cloud tiers). |

## Example usage

Three runnable scripts in `examples/` show the composition root from the
outside:

```bash
# Single adapter (Claude Haiku) — needs ANTHROPIC_API_KEY.
uv run python examples/01_single_adapter.py

# Fallback stack — uses whichever tier's credentials are present.
uv run python examples/02_fallback_demo.py

# Custom stack — secondary (OpenAI) only; demonstrates how to wire a
# subset of tiers manually.
uv run python examples/03_custom_stack.py
```

Each script prints the completion on stdout and a `[tier=... model=... ]`
metadata line on stderr so pipelines can consume `.text` cleanly.

Offline-only? Force the tertiary tier:

```bash
LLM_TIER=tertiary uv run python -m claude_tools_roundtrip_playground.main \
  "Say hi in one sentence."
```

No API key required; runs entirely against local Ollama.

## Configuration

All runtime configuration lives in `.env` (loaded by
`infrastructure/settings.py`). Variables:

| Var | Default | Purpose |
| --- | --- | --- |
| `LLM_TIER` | `fallback` | `primary` / `secondary` / `tertiary` / `fallback`. |
| `ANTHROPIC_API_KEY` | (unset) | Enables primary tier. |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5-20251001` | Override model. |
| `OPENAI_API_KEY` | (unset) | Enables secondary tier. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Override model. |
| `OLLAMA_HOST` | `http://localhost:11434` | Where to find Ollama. |
| `OLLAMA_MODEL` | `llama3.2:3b` | Override model. |

Empty strings coerce to `None` so a `.env` placeholder doesn't silently
become a zero-length API key.

## Verification

Every architectural claim is paired with a runnable command in
[`VERIFICATION.md`](VERIFICATION.md). OT-2 (`LLMPort` contract
conformance), OT-3 (pre-commit parity), OT-4 (Docker healthcheck), OT-7
(offline Ollama), OT-8 (all three tiers end-to-end), OT-9 (wheel build),
and OT-10 (bandit clean) each take one line to re-verify.

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the Mermaid dependency
graph and the extension recipes (adding a tier, adding an unrelated
port). The short version: `domain/` knows nothing; `application/` knows
`domain/`; `infrastructure/` knows both; `main.py` knows all three and
is the only place allowed to wire them together.

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) — Keep-a-Changelog 1.1.0 format. The
template's own release notes (`v0.1.0`, `v0.2.0`) are trimmed from the
fork's changelog so `[Unreleased]` is what you edit.

## License

MIT — see [`LICENSE`](LICENSE).
