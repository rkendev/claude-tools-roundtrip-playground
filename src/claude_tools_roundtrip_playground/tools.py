"""Demo tool used by the round-trip CLI: a great-circle distance calculator.

Kept deliberately tiny so the artifact's focus stays on the protocol
mechanics, not on the tool's implementation. Pure stdlib `math`, no
side effects, fully deterministic — which is why the VCR cassette in
the round-trip happy-path test stays stable across re-records.
"""

from __future__ import annotations

import math
from typing import Any

EARTH_RADIUS_KM = 6371.0


def compute_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in kilometres."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


HAVERSINE_TOOL: dict[str, Any] = {
    "name": "compute_haversine_distance_km",
    "description": (
        "Great-circle distance between two lat/lon points, in kilometres. "
        "Use this when the user asks how far one location is from another."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "lat1": {
                "type": "number",
                "description": "Latitude of point 1, in decimal degrees.",
            },
            "lon1": {
                "type": "number",
                "description": "Longitude of point 1, in decimal degrees.",
            },
            "lat2": {
                "type": "number",
                "description": "Latitude of point 2, in decimal degrees.",
            },
            "lon2": {
                "type": "number",
                "description": "Longitude of point 2, in decimal degrees.",
            },
        },
        "required": ["lat1", "lon1", "lat2", "lon2"],
        "additionalProperties": False,
    },
}
