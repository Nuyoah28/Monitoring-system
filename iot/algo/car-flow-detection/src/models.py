from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TrackedObject:
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox: tuple[float, float, float, float]
    anchor: tuple[float, float]


@dataclass(slots=True)
class FlowEvent:
    camera_id: str
    rule_type: str
    rule_id: str
    direction: str
    vehicle_class: str
    track_id: int
    frame_index: int
    timestamp_ms: int

