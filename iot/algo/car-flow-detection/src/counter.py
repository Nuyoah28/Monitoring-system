from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .geometry import line_side, point_in_polygon, segments_intersect
from .models import FlowEvent, TrackedObject


@dataclass(slots=True)
class TrackState:
    class_name: str
    history: list[tuple[float, float]] = field(default_factory=list)
    counted_lines: set[str] = field(default_factory=set)
    region_inside: dict[str, bool] = field(default_factory=dict)
    region_entered: set[str] = field(default_factory=set)
    region_exited: set[str] = field(default_factory=set)
    last_frame_index: int = -1


class FlowCounter:
    def __init__(self, camera_id: str, rules: dict) -> None:
        self.camera_id = camera_id
        self.rules = rules
        self.track_states: dict[int, TrackState] = {}
        self.track_history: dict[int, list[tuple[float, float]]] = defaultdict(list)
        self.max_history = int(rules.get("max_track_history", 30))

    def update(self, tracked_objects: list[TrackedObject], frame_index: int, timestamp_ms: int) -> list[FlowEvent]:
        events: list[FlowEvent] = []
        active_ids = set()

        for tracked in tracked_objects:
            active_ids.add(tracked.track_id)
            state = self.track_states.setdefault(tracked.track_id, TrackState(class_name=tracked.class_name))
            state.class_name = tracked.class_name
            state.last_frame_index = frame_index
            state.history.append(tracked.anchor)
            if len(state.history) > self.max_history:
                state.history.pop(0)
            self.track_history[tracked.track_id] = list(state.history)

            if len(state.history) >= 2:
                prev_point = state.history[-2]
                curr_point = state.history[-1]
                events.extend(self._check_lines(tracked, state, prev_point, curr_point, frame_index, timestamp_ms))
                events.extend(self._check_regions(tracked, state, prev_point, curr_point, frame_index, timestamp_ms))

        self._cleanup_stale_tracks(frame_index)
        return events

    def _check_lines(
        self,
        tracked: TrackedObject,
        state: TrackState,
        prev_point: tuple[float, float],
        curr_point: tuple[float, float],
        frame_index: int,
        timestamp_ms: int,
    ) -> list[FlowEvent]:
        events: list[FlowEvent] = []
        for line_rule in self.rules.get("lines", []):
            line_id = line_rule["id"]
            if line_id in state.counted_lines:
                continue

            line_points = [tuple(point) for point in line_rule["points"]]
            crossed = segments_intersect(prev_point, curr_point, line_points[0], line_points[1])
            if not crossed:
                continue

            direction = self._line_direction(prev_point, curr_point, line_points, line_rule.get("direction_hint", "positive_is_in"))
            if direction is None:
                continue

            state.counted_lines.add(line_id)
            events.append(
                FlowEvent(
                    camera_id=self.camera_id,
                    rule_type="line",
                    rule_id=line_id,
                    direction=direction,
                    vehicle_class=tracked.class_name,
                    track_id=tracked.track_id,
                    frame_index=frame_index,
                    timestamp_ms=timestamp_ms,
                )
            )
        return events

    def _check_regions(
        self,
        tracked: TrackedObject,
        state: TrackState,
        prev_point: tuple[float, float],
        curr_point: tuple[float, float],
        frame_index: int,
        timestamp_ms: int,
    ) -> list[FlowEvent]:
        del prev_point  # The region logic only needs current state changes for now.
        events: list[FlowEvent] = []
        for region_rule in self.rules.get("regions", []):
            region_id = region_rule["id"]
            polygon = [tuple(point) for point in region_rule["points"]]
            curr_inside = point_in_polygon(curr_point, polygon)
            prev_inside = state.region_inside.get(region_id, False)
            state.region_inside[region_id] = curr_inside

            mode = region_rule.get("mode", "occupancy")
            if mode == "occupancy":
                continue

            if not prev_inside and curr_inside:
                state.region_entered.add(region_id)
                events.append(
                    FlowEvent(
                        camera_id=self.camera_id,
                        rule_type="region",
                        rule_id=region_id,
                        direction="IN",
                        vehicle_class=tracked.class_name,
                        track_id=tracked.track_id,
                        frame_index=frame_index,
                        timestamp_ms=timestamp_ms,
                    )
                )
            elif prev_inside and not curr_inside:
                state.region_exited.add(region_id)
                events.append(
                    FlowEvent(
                        camera_id=self.camera_id,
                        rule_type="region",
                        rule_id=region_id,
                        direction="OUT",
                        vehicle_class=tracked.class_name,
                        track_id=tracked.track_id,
                        frame_index=frame_index,
                        timestamp_ms=timestamp_ms,
                    )
                )
        return events

    def occupancy_snapshot(self) -> dict[str, dict[str, int]]:
        occupancy: dict[str, dict[str, int]] = {}
        for region_rule in self.rules.get("regions", []):
            if region_rule.get("mode", "occupancy") != "occupancy":
                continue
            region_id = region_rule["id"]
            class_counts: dict[str, int] = defaultdict(int)
            for state in self.track_states.values():
                if state.region_inside.get(region_id, False):
                    class_counts[state.class_name] += 1
            occupancy[region_id] = dict(class_counts)
        return occupancy

    def _line_direction(
        self,
        prev_point: tuple[float, float],
        curr_point: tuple[float, float],
        line: list[tuple[float, float]],
        hint: str,
    ) -> str | None:
        dx = curr_point[0] - prev_point[0]
        dy = curr_point[1] - prev_point[1]

        if hint == "down_is_in":
            return "IN" if dy > 0 else "OUT"
        if hint == "up_is_in":
            return "IN" if dy < 0 else "OUT"
        if hint == "right_is_in":
            return "IN" if dx > 0 else "OUT"
        if hint == "left_is_in":
            return "IN" if dx < 0 else "OUT"

        prev_side = line_side(prev_point, line)
        curr_side = line_side(curr_point, line)
        if prev_side == curr_side == 0:
            return None

        if hint == "negative_is_in":
            return "IN" if prev_side > 0 and curr_side <= 0 else "OUT"
        return "IN" if prev_side < 0 and curr_side >= 0 else "OUT"

    def _cleanup_stale_tracks(self, frame_index: int) -> None:
        stale_after = int(self.rules.get("stale_frames", 90))
        stale_ids = [
            track_id
            for track_id, state in self.track_states.items()
            if frame_index - state.last_frame_index > stale_after
        ]
        for track_id in stale_ids:
            self.track_states.pop(track_id, None)
            self.track_history.pop(track_id, None)

