"""Round-trip CLI demonstrating Claude's native ``tools=`` API.

Visibility is the feature. Every protocol step prints to stdout — the
tool schema we send, Claude's tool_use response, the local execution,
the tool_result we send back, and Claude's final text — so a reader can
follow the round-trip without an SDK abstraction in the way.
"""

from __future__ import annotations

import json
from typing import Any, cast

from anthropic import Anthropic

from .tools import HAVERSINE_TOOL, compute_haversine_distance_km

MODEL_DEFAULT = "claude-haiku-4-5-20251001"
MAX_ITERATIONS = 5
MAX_TOKENS = 1024


class RoundTripIterationError(RuntimeError):
    """Raised when the tool-use loop exceeds ``MAX_ITERATIONS`` rounds."""


def run_roundtrip(
    question: str,
    *,
    model: str = MODEL_DEFAULT,
    client: Anthropic | None = None,
) -> str:
    """Run a single tools= round-trip against Claude and return the final text.

    The loop is gated by ``stop_reason``, which is the canonical D2 signal
    — never parse text for completion. ``tool_use`` triggers a local call
    to the haversine tool and a follow-up turn carrying the ``tool_result``.
    ``end_turn`` ends the round-trip and returns the model's final text.
    Any other stop_reason aborts.
    """
    if client is None:
        client = Anthropic()

    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]

    print("[step 1] tool schema sent to Claude:")
    print(json.dumps(HAVERSINE_TOOL, indent=2))

    for iteration in range(MAX_ITERATIONS):
        resp = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            tools=[HAVERSINE_TOOL],  # type: ignore[list-item]
            messages=messages,  # type: ignore[arg-type]
        )

        if resp.stop_reason == "tool_use":
            tool_block = next(b for b in resp.content if b.type == "tool_use")
            raw_input = cast("dict[str, Any]", tool_block.input)
            print("[step 2] Claude's first response:")
            print("  stop_reason: tool_use")
            print("  tool_use:")
            print(f"    name: {tool_block.name}")
            print(f"    input: {json.dumps(raw_input)}")

            result = compute_haversine_distance_km(
                lat1=float(raw_input["lat1"]),
                lon1=float(raw_input["lon1"]),
                lat2=float(raw_input["lat2"]),
                lon2=float(raw_input["lon2"]),
            )
            print("[step 3] executing tool locally:")
            print(f"  result: {result:.2f}")

            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_block.id,
                "content": f"{result:.2f}",
            }
            print("[step 4] tool_result sent back to Claude:")
            print(f"  {json.dumps(tool_result_block, indent=2)}")

            messages.append(
                {
                    "role": "assistant",
                    "content": [b.model_dump() for b in resp.content],
                }
            )
            messages.append({"role": "user", "content": [tool_result_block]})
            continue

        if resp.stop_reason == "end_turn":
            text = "".join(block.text for block in resp.content if block.type == "text")
            print("[step 5] Claude's final response:")
            print("  stop_reason: end_turn")
            print(f"  text: {text!r}")
            return text

        raise RoundTripIterationError(
            f"unexpected stop_reason at iteration {iteration}: {resp.stop_reason!r}"
        )

    raise RoundTripIterationError(f"iteration cap ({MAX_ITERATIONS}) reached without end_turn")
