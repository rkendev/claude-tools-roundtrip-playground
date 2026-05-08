# T003 — Artifact B: Tools Round-Trip Playground (new repo)

## Goal

Build the second small-projects-portfolio artifact: a minimal CLI demonstrating Claude's native `tools=` API round-trip. JSON schema in, tool_use back, tool_result, final text. Every step printed visibly so a reader can follow the protocol mechanics without an SDK abstraction in the way.

This is **a new public repo**, NOT a directory inside `claude-mcp-server-minimal`. Per the locked plan: "3–4 separate GitHub repos as a SERIES PATTERN, NOT a monorepo." Each artifact stands alone with its own README + Medium post + LinkedIn hook.

Repo name: `claude-tools-roundtrip-playground`
Local location on VPS: `/root/projects/AI-Engineering/short_projects_exam_prep/claude-tools-roundtrip-playground/`

## Workflow

This task has TWO phases. Treat as one PR — phases are organizational, not sequential branches.

**Phase A (scaffold):** new repo from `roy-ai-template@v0.5.0`, all 5 known post-scaffold fixes, GitHub repo public, CI + Smoke green on initial commit, scaffold-disclosure note in README.

**Phase B (artifact):** native `tools=` round-trip CLI, one demo tool, VCR-recorded test, README with the Medium hook framing.

Single feature branch: `feat/t003-tools-roundtrip`. PR-based merge, squash-and-delete.

## Phase A — Scaffold

### A.1 Create the repo locally

```bash
cd /root/projects/AI-Engineering/short_projects_exam_prep
copier copy --vcs-ref v0.5.0 \
  /root/projects/AI-Engineering/roy-ai-template \
  ./claude-tools-roundtrip-playground \
  --trust --defaults \
  --data project_name=claude-tools-roundtrip-playground \
  --data package_name=claude_tools_roundtrip_playground \
  --data project_description="Minimal CLI demonstrating Claude's native tools= JSON schema round-trip."
```

### A.2 Apply the 5 known post-scaffold fixes

```bash
cd claude-tools-roundtrip-playground

# Bug #1 — defensive sed for any "my-ai-project" residue
grep -rl "my-ai-project" --include="*.toml" --include="*.md" --include="Makefile" --include="*.yaml" --include="*.yml" --include="*.example" . 2>/dev/null \
  | xargs -r sed -i 's/my-ai-project/claude-tools-roundtrip-playground/g'

# Bug #2 — git init + main branch
git init && git checkout -b main

# Bug #4 — top-level pre-commit exclude for jinja-placeholder skill template
sed -i '1i exclude: ^\\.claude/skills/add-adapter/_adapter_template\\.py$\n' .pre-commit-config.yaml

# Bug #3 — install dev extras
uv sync --all-extras

# Bug #5 — smoke.sh executable bit
chmod +x scripts/smoke.sh
git update-index --chmod=+x scripts/smoke.sh

# First commit + verify
git add -A
git commit -m "chore: scaffold from roy-ai-template@v0.5.0 + post-scaffold fixes"
make check
```

If any pre-commit auto-fixers (end-of-file-fixer, ruff-format) modify files on first run, re-stage and amend:

```bash
git add -A && git commit --amend --no-edit
make check   # second pass — must be all-green, both inline and pre-commit hooks
```

### A.3 Push to GitHub + secrets + topics

```bash
gh repo create claude-tools-roundtrip-playground \
  --public \
  --source=. \
  --description "Minimal CLI demonstrating Claude's native tools= JSON schema round-trip." \
  --push

# Set the API key (smoke.yml will need it)
gh secret set ANTHROPIC_API_KEY     # paste when prompted
gh secret set OPENAI_API_KEY        # smoke.yml inherits the template's three-tier expectation; set this too even if unused

# Topic tags
gh repo edit rkendev/claude-tools-roundtrip-playground \
  --add-topic mcp,claude,anthropic,tool-use,json-schema,cca-f
```

### A.4 README scaffold disclosure (Phase A)

Replace the inherited template README's lead paragraph with:

```markdown
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
```

The "What this gives you" template-era paragraphs and the inherited LLM-adapter `Example usage` H2 stay for now — group them under a "Inherited template scaffolding (background)" H2 right after the artifact-specific content (same pattern T001b applied to Artifact A).

### A.5 Phase A acceptance gates

- `make check` green locally — note the test count baseline (likely 219, same as Artifact A's pre-customization baseline since it's the same template).
- Public repo created, first commit pushed, `gh repo view` shows the topics.
- Both `CI` and `Smoke` workflows green on the initial commit. **Note:** Smoke runs only on push-to-main (template default); the initial scaffold push IS to main, so it should fire automatically.
- README badge resolves green.

If Phase A fails the gate, fix scaffolding before starting Phase B.

## Phase B — Artifact

### B.1 The demo tool

Pick one tool that is multi-parameter (rich enough to exercise a non-trivial JSON schema), deterministic (so VCR tests are stable), and explainable in one sentence. Recommended:

```python
def compute_haversine_distance_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Great-circle distance between two lat/lon points, in kilometres."""
```

Reasons: 4 typed params force a richer JSON schema than a single-string tool would; output is one number; the implementation is ~10 lines of stdlib `math`; the demo question Claude asks ("how far is Amsterdam from New York?") is human-relatable.

If you prefer a different tool that meets the same three criteria (multi-param, deterministic, one-sentence explainable), propose it in plan mode.

### B.2 The round-trip CLI

Module path: `src/claude_tools_roundtrip_playground/playground.py` (or similar — the package was renamed by copier).

Public entrypoint: `python -m claude_tools_roundtrip_playground "<question>"` — e.g. `python -m claude_tools_roundtrip_playground "How far is Amsterdam from New York in kilometres?"`.

Behavior, made deliberately verbose so a reader following along sees every protocol step:

```
[step 1] tool schema sent to Claude:
  {<print the full JSON schema here, indent 2>}

[step 2] Claude's first response:
  stop_reason: tool_use
  tool_use:
    name: compute_haversine_distance_km
    input: {"lat1": 52.37, "lon1": 4.90, "lat2": 40.71, "lon2": -74.01}

[step 3] executing tool locally:
  result: 5847.83

[step 4] tool_result sent back to Claude:
  {<the structured tool_result content>}

[step 5] Claude's final response:
  stop_reason: end_turn
  text: "Amsterdam and New York are about 5,847 kilometres apart..."
```

Each `[step N]` block prints to stdout. Use `print()`, not `logging` — the point is observability, not production logging.

Implementation notes:

- Use the Anthropic Python SDK (`anthropic`) which is already in the inherited template's dependencies.
- Loop until `stop_reason == "end_turn"`. Cap iterations at 5 (single round-trip should be 2 iterations: initial → tool_use, then post-tool_result → end_turn). If iteration cap is hit, raise.
- Use the **canonical D2 stop_reason check** — never parse text for completion signals. The `stop_reason` field is the protocol's truth.
- Read `ANTHROPIC_API_KEY` from env at call time. If missing, exit 1 with a clear message.
- Default model: `claude-haiku-4-5-20251001` (matches the inherited template's `ANTHROPIC_MODEL` default — cheap for this demo).

### B.3 Tests

Add `tests/unit/test_playground.py` with at minimum:

1. **`test_tool_schema_is_well_formed`** — call your tool's JSON-schema generator, assert it's a valid JSON Schema dict (has `type: "object"`, `properties` with all 4 lat/lon keys, `required` lists all 4, all 4 have `type: "number"`).

2. **`test_haversine_known_distance`** — pure Python unit test of the `compute_haversine_distance_km` function itself, asserting the Amsterdam–New York pair returns ~5847 km ± 5 km tolerance.

3. **`test_round_trip_happy_path`** — uses `pytest-recording` (already in template deps) to record a live round-trip on first run, replay from cassette on subsequent runs. The cassette file lands at `tests/unit/cassettes/test_round_trip_happy_path.yaml` and is committed. The test asserts:
   - The CLI runs end-to-end without raising.
   - `stop_reason: tool_use` was observed at step 2.
   - `stop_reason: end_turn` was observed at step 5.
   - The final text contains the substring `"5,8"` or `"5847"` (allowing for thousands-separator variation).

4. **`test_iteration_cap_raises`** — synthetic test where you craft a mocked response sequence that never returns `end_turn`, verify the loop raises `RoundTripIterationError` (or whatever you name the exception) at iteration 5.

Live-API tests must be marked `@pytest.mark.live` so `make check` (which excludes `live` and `integration` markers) doesn't try to run them. The VCR-recorded test does NOT need the marker because cassette replay is offline.

### B.4 README artifact section

Add an H2 `## Round-trip walkthrough` between the lead paragraph and the inherited-scaffolding section. Body:

```markdown
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
[step 3] executing tool locally: result=5847.83
[step 4] tool_result sent back to Claude...
[step 5] Claude's final response: stop_reason=end_turn
  "Amsterdam and New York are about 5,847 kilometres apart..."
```

Why this matters: most "tool use" tutorials hide the protocol behind an
SDK convenience method. This CLI makes every step of the round-trip
visible so you can see (a) the JSON schema Claude actually receives,
(b) what `stop_reason` controls the loop, (c) how `tool_result` plumbs
back into the next request. The exam quizzes on these mechanics; the
hiring conversations want to see you've worked through them.
```

### B.5 Phase B acceptance gates

- `make check` green. Test count = scaffold baseline + 4 (new playground tests). Report new total in PR body.
- VCR cassette committed at `tests/unit/cassettes/test_round_trip_happy_path.yaml`. Verify it doesn't leak the API key (cassette filter should redact `Authorization` header — check the recorded YAML before commit).
- Manual end-to-end run: `ANTHROPIC_API_KEY=... uv run python -m claude_tools_roundtrip_playground "..."` returns coherent output, all 5 steps visible.
- CI green on the PR.
- Post-merge: Smoke green on main (push-to-main only by design).

## Anti-patterns to avoid

- Do NOT use the `mcp` SDK. This artifact is about Claude's native `tools=` API, not MCP. Don't conflate the two — the whole point of B is to show what `tools=` looks like *without* the MCP layer.
- Do NOT add an MCP server, `.mcp.json`, or echo the structure from Artifact A. Different artifact, different lesson.
- Do NOT use a tool-use abstraction (e.g. `anthropic.tools.run` or any high-level convenience). Use the raw `client.messages.create(...)` loop with explicit `stop_reason` checks. Visibility is the feature.
- Do NOT validate or process Claude's text output beyond the iteration cap. The point is showcasing the protocol, not building a production agent.
- Do NOT bump version, do NOT touch CHANGELOG. Wk5 ships v0.1.0 of this repo (after Medium #1 publishes per the locked plan).
- Do NOT touch any file in `src/claude_tools_roundtrip_playground/{domain,application,infrastructure}/`. Inherited template scaffolding stays unchanged for Wk5 polish decision.

## Protocols (inlined)

- **API verification:** Inspect the actually-installed `anthropic` SDK (`uv run python -c "from anthropic import Anthropic; help(Anthropic.messages.create)"` or read the type stubs) before quoting parameter names. The `tools=` API has shifted across SDK versions; verify against what's installed in the new repo's venv.
- **Test-count reporting:** Read totals from `make check` pytest summary line. Never `grep -c "def test_"`.
- **Pre-commit:** Always `uv run pre-commit run --all-files` or `make check`. Bare `pre-commit` errors.
- **Branch protocol:** New work on `feat/t003-tools-roundtrip` per `.claude/rules/commit.md`. PR-based; squash-merge on acceptance.
- **Task close:** local `make check` green + CI green on PR + acceptance-specific verification (manual run with real key) → squash-merge → Smoke green on main post-merge.
- **Smoke note:** `smoke.yml` is configured `on: push: branches: [main]` only by design. Do NOT block on Smoke-on-PR; it can't be satisfied.
- **Mypy gotchas:** if the SDK has untyped decorator surface (similar to `mcp` SDK), apply `# type: ignore[misc, unused-ignore]` (multi-code) — same pattern as Artifact A's `server.py:24`. Don't waste cycles re-discovering this.

## Plan mode requirements

Begin in plan mode. Walk through:

1. The exact `copier` invocation + the post-scaffold fixes (verify the 5-bug list against the current state of `roy-ai-template@v0.5.0`).
2. The demo tool choice — confirm `compute_haversine_distance_km` or propose an alternative meeting the three criteria (multi-param, deterministic, one-sentence explainable).
3. The exact entrypoint structure (CLI arg parsing, env-var read, the iteration loop, the per-step print blocks).
4. Tool schema verification — show what `inputSchema` Anthropic SDK generates for the chosen tool. Inspect the live SDK before declaring the expected shape.
5. The 4 tests with exact assertions.
6. README diff — what stays from the template, what's replaced.
7. PR body draft (in `tasks/pr_body.md`).
8. Expected new test count (scaffold baseline + 4) and the file list.

Wait for explicit approval before any code changes. Do not execute the `copier copy` until the plan is approved.

## PR body template (write to `tasks/pr_body.md`)

```markdown
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

- `make check` green: <N> tests passing on initial scaffold baseline + 4.
- VCR cassette `test_round_trip_happy_path.yaml` committed; cassette
  redacts `Authorization` header.
- Manual run: `ANTHROPIC_API_KEY=... uv run python -m claude_tools_roundtrip_playground "How far is Amsterdam from New York in kilometres?"` produces all 5 visible steps, final text references ~5847 km.
- CI green on this PR.
- (Post-merge): Smoke green on main.

## Out of scope

- MCP integration. Different artifact.
- Multi-tool round-trips. Single tool, single round-trip — the protocol
  story is the focus.
- Streaming responses. Synchronous `messages.create` is enough.
- Stripping inherited template scaffolding. Wk5 polish decision.
- Version bump / CHANGELOG.

## Closes

T003 of CCA-F small-projects plan v1; opens Artifact B for Wk5 polish.
```

End of PR body template.

## Out of scope (later in Wk2/Wk3)

- Wk5 (per locked plan): Artifact B README polish + Medium #1 publish: "Native Tools in Claude: JSON Schema Round-Trip" + tag `v0.1.0` of this repo.
- Wk6 onward: T004 — Artifact C (Tool Choice Modes Showcase, new repo).
