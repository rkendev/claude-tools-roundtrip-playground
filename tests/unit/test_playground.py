"""Tests for the tools= round-trip playground.

Four tests, no live network on `make check`:

1. Tool JSON-schema is well-formed.
2. The local haversine function returns a sensible distance.
3. End-to-end round-trip replays from a committed VCR cassette.
4. The iteration cap raises ``RoundTripIterationError`` on a stuck loop.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from anthropic import Anthropic

from claude_tools_roundtrip_playground.playground import (
    MAX_ITERATIONS,
    RoundTripIterationError,
    run_roundtrip,
)
from claude_tools_roundtrip_playground.tools import (
    HAVERSINE_TOOL,
    compute_haversine_distance_km,
)


def test_tool_schema_is_well_formed() -> None:
    schema = HAVERSINE_TOOL["input_schema"]
    assert schema["type"] == "object"
    assert set(schema["properties"]) == {"lat1", "lon1", "lat2", "lon2"}
    for key in ("lat1", "lon1", "lat2", "lon2"):
        assert schema["properties"][key]["type"] == "number"
    assert set(schema["required"]) == {"lat1", "lon1", "lat2", "lon2"}
    assert schema["additionalProperties"] is False
    assert HAVERSINE_TOOL["name"] == "compute_haversine_distance_km"


def test_haversine_known_distance() -> None:
    """Amsterdam → New York great-circle ≈ 5863 km for these rounded coords.

    The exact value depends on coordinate precision; using the spec's
    rounded coords (52.37, 4.90, 40.71, -74.01) the formula yields
    5863.32 km. ±10 km tolerance covers float-rounding wobble without
    masking arithmetic regressions.
    """
    distance = compute_haversine_distance_km(52.37, 4.90, 40.71, -74.01)
    assert distance == pytest.approx(5863, abs=10)


@pytest.mark.vcr
def test_round_trip_happy_path(capsys: pytest.CaptureFixture[str]) -> None:
    """End-to-end round-trip replayed from a committed VCR cassette.

    First run records a real API call (set ``ANTHROPIC_API_KEY`` and run:
    ``uv run pytest tests/unit/test_playground.py::test_round_trip_happy_path
    --record-mode=once``). Subsequent runs replay from the committed
    cassette — no key needed. To re-record: delete the cassette YAML
    and re-run with ``--record-mode=once``. The conftest's VCR config
    redacts the ``authorization`` and ``x-api-key`` headers so the
    cassette never embeds a real key.
    """
    # Pass an explicit dummy-keyed client so cassette replay works in CI
    # (no ANTHROPIC_API_KEY set). VCR intercepts the HTTP layer, but the
    # SDK still validates auth at construction time.
    offline_client = Anthropic(api_key="cassette-replay-dummy-key")
    text = run_roundtrip(
        "How far is Amsterdam from New York in kilometres?",
        model="claude-haiku-4-5-20251001",
        client=offline_client,
    )
    captured = capsys.readouterr().out
    assert "stop_reason: tool_use" in captured
    assert "stop_reason: end_turn" in captured
    assert "[step 3] executing tool locally:" in captured
    # Literal substring match against the recorded cassette text. Claude
    # phrases the haversine result as "5,863 kilometers" in this take;
    # if the cassette is re-recorded and the wording shifts, update both
    # together.
    assert "5,863" in text or "5863" in text


def test_iteration_cap_raises() -> None:
    """A stuck tool_use loop raises after MAX_ITERATIONS rounds."""
    fake_client = MagicMock()
    stuck = MagicMock()
    stuck.stop_reason = "tool_use"
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "compute_haversine_distance_km"
    tool_block.id = "stub_id"
    tool_block.input = {"lat1": 0.0, "lon1": 0.0, "lat2": 0.0, "lon2": 0.0}
    tool_block.model_dump.return_value = {"type": "tool_use"}
    stuck.content = [tool_block]
    fake_client.messages.create.return_value = stuck

    with pytest.raises(RoundTripIterationError, match=r"iteration cap"):
        run_roundtrip("stuck loop test", client=fake_client)

    # Sanity: we hit the cap exactly MAX_ITERATIONS times.
    assert fake_client.messages.create.call_count == MAX_ITERATIONS


def test_unexpected_stop_reason_raises() -> None:
    """A non-{tool_use, end_turn} stop_reason aborts the loop."""
    fake_client = MagicMock()
    weird = MagicMock()
    weird.stop_reason = "max_tokens"
    weird.content = []
    fake_client.messages.create.return_value = weird

    with pytest.raises(RoundTripIterationError, match=r"unexpected stop_reason"):
        run_roundtrip("weird stop_reason", client=fake_client)


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, Any]:
    """Redact auth headers from any VCR cassette this module records."""
    return {
        "filter_headers": [
            ("authorization", "REDACTED"),
            ("x-api-key", "REDACTED"),
        ],
    }
