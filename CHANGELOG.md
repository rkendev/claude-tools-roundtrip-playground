# Changelog

> Scaffolded from [`roy-ai-template@v0.5.0`](https://github.com/rkendev/roy-ai-template/releases/tag/v0.5.0).
> The template's inherited CHANGELOG history (v0.1.0 → v0.5.0) is preserved
> in git history at scaffold-commit `c00c9fb`; the entries below cover only
> this artifact's own releases.

All notable changes to this project are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
`[Unreleased]` collects changes landing on `main` ahead of the next tagged
release; each tagged version carries its release date and a stable anchor.

## [Unreleased]

## [0.1.0] — 2026-05-12

First stable release of `claude-tools-roundtrip-playground`: a single-file
CLI demo of Claude's native `tools=` round-trip protocol, with a
`compute_haversine_distance_km` example tool and an offline VCR-recorded
end-to-end test.

### Added

- **T003 — `tools=` round-trip playground** (PR #1, commit `130ee52`).
  Scaffolded from `roy-ai-template@v0.5.0`. Ships:
  - `src/claude_tools_roundtrip_playground/playground.py` —
    `run_roundtrip(question, *, model, client)` orchestrates the
    tool_use → tool_result → end_turn loop, capped at `MAX_ITERATIONS`,
    raises `RoundTripIterationError` on stuck loops, prints every
    protocol step.
  - `src/claude_tools_roundtrip_playground/tools.py` — `HAVERSINE_TOOL`
    JSON schema + `compute_haversine_distance_km(lat1, lon1, lat2, lon2)`
    pure-Python implementation.
  - `src/claude_tools_roundtrip_playground/__main__.py` — `python -m`
    entrypoint: `argparse` over `question` + `--model`, fail-fast on
    missing `ANTHROPIC_API_KEY`, dispatch into `run_roundtrip`.
  - `tests/unit/test_playground.py` — schema, haversine arithmetic,
    VCR-recorded happy-path round-trip, iteration-cap error.
  - VCR cassette with redacted `authorization` / `x-api-key` headers
    under `tests/unit/cassettes/`.
- **T006 — `test_cli.py` retrofit** (PR #2, commit `5c1bd64`). Adds
  `tests/unit/test_cli.py` (4 tests) covering argparse usage error,
  missing `ANTHROPIC_API_KEY`, default-model dispatch, and `--model`
  override against `__main__:main`. Closes the post-T003 audit coverage
  gap on `__main__.py`. Total: **228 tests passing**.

### Inherited from `roy-ai-template@v0.5.0` (preserved unchanged)

The full hexagonal scaffold (`src/.../{domain,application,infrastructure}/`
with three LLM adapters + `FallbackModel` orchestrator, 32-case contract
suite, `.claude/` rules + skills + commands, `make check` gate, CI +
smoke workflows, Docker compose) ships intact from the template. Wk3
polish — pruning the unused adapter stack down to just the Anthropic
path this playground uses — is deferred pending a follow-up task.

[Unreleased]: https://github.com/rkendev/claude-tools-roundtrip-playground/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/rkendev/claude-tools-roundtrip-playground/releases/tag/v0.1.0
