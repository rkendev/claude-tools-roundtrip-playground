"""CLI entrypoint: ``python -m claude_tools_roundtrip_playground "<question>"``.

Reads ``ANTHROPIC_API_KEY`` from the environment at call time. Exits 1
with a clear message if the key is missing.
"""

from __future__ import annotations

import argparse
import os
import sys

from .playground import MODEL_DEFAULT, run_roundtrip


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m claude_tools_roundtrip_playground",
        description=(
            "Run a single Claude tools= round-trip against the haversine tool "
            "and print every protocol step."
        ),
    )
    parser.add_argument(
        "question",
        help='Natural-language question, e.g. "How far is Amsterdam from New York?"',
    )
    parser.add_argument(
        "--model",
        default=MODEL_DEFAULT,
        help=f"Anthropic model id (default: {MODEL_DEFAULT}).",
    )
    args = parser.parse_args(argv)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "error: ANTHROPIC_API_KEY is not set; export it before running.",
            file=sys.stderr,
        )
        return 1

    run_roundtrip(args.question, model=args.model)
    return 0


if __name__ == "__main__":
    sys.exit(main())
