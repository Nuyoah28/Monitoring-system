from __future__ import annotations

import math

import cv2
import numpy as np

from .geometry import polygon_bounds


LINE_COLOR = (0, 255, 255)
REGION_COLOR = (255, 200, 0)
TRACK_COLOR = (0, 255, 0)
ANCHOR_COLOR = (0, 0, 255)
IN_COLOR = (60, 220, 60)
OUT_COLOR = (80, 80, 255)


def draw_overlay(
    frame,
    rules: dict,
    tracked_objects,
    track_history: dict[int, list[tuple[float, float]]],
    snapshot: dict,
    occupancy: dict[str, int] | None = None,
    events=None,
):
    occupancy = occupancy or {}
    events = events or []

    for line in rules.get("lines", []):
        _draw_line_rule(frame, line)

    for region in rules.get("regions", []):
        points = [tuple(int(v) for v in point) for point in region["points"]]
        cv2.polylines(frame, [_as_contour(points)], isClosed=True, color=REGION_COLOR, thickness=2)
        x1, y1, _, _ = polygon_bounds(region["points"])
        region_text = region["id"]
        if region["id"] in occupancy:
            region_text = f"{region['id']} now:{occupancy[region['id']]}"
        cv2.putText(
            frame,
            region_text,
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            REGION_COLOR,
            2,
            cv2.LINE_AA,
        )

    for tracked in tracked_objects:
        x1, y1, x2, y2 = [int(value) for value in tracked.bbox]
        cv2.rectangle(frame, (x1, y1), (x2, y2), TRACK_COLOR, 2)

        label = f"ID {tracked.track_id} {tracked.class_name} {tracked.confidence:.2f}"
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 2)
        label_y1 = max(0, y1 - label_h - 10)
        label_y2 = label_y1 + label_h + 8
        label_x2 = min(frame.shape[1] - 1, x1 + label_w + 12)
        cv2.rectangle(frame, (x1, label_y1), (label_x2, label_y2), TRACK_COLOR, -1)
        cv2.putText(
            frame,
            label,
            (x1 + 6, label_y2 - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )

        ax, ay = int(tracked.anchor[0]), int(tracked.anchor[1])
        cv2.circle(frame, (ax, ay), 4, ANCHOR_COLOR, -1)

        history = track_history.get(tracked.track_id, [])
        if len(history) >= 2:
            cv2.polylines(frame, [_as_contour(history)], isClosed=False, color=(240, 240, 240), thickness=2)

    _draw_stats(frame, tracked_objects, snapshot.get("totals", {}), occupancy, events)
    return frame


def _draw_line_rule(frame, line_rule: dict) -> None:
    p1 = tuple(int(v) for v in line_rule["points"][0])
    p2 = tuple(int(v) for v in line_rule["points"][1])
    cv2.line(frame, p1, p2, LINE_COLOR, 2)

    midpoint = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
    in_vec = _in_vector(line_rule)
    out_vec = (-in_vec[0], -in_vec[1])
    arrow_len = 36

    in_end = (int(midpoint[0] + in_vec[0] * arrow_len), int(midpoint[1] + in_vec[1] * arrow_len))
    out_end = (int(midpoint[0] + out_vec[0] * arrow_len), int(midpoint[1] + out_vec[1] * arrow_len))
    cv2.arrowedLine(frame, midpoint, in_end, IN_COLOR, 2, tipLength=0.35)
    cv2.arrowedLine(frame, midpoint, out_end, OUT_COLOR, 2, tipLength=0.35)

    label = f"{line_rule['id']}  IN:{_direction_label(line_rule.get('direction_hint', 'positive_is_in'))}"
    (label_w, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.58, 2)
    label_x = max(10, min(frame.shape[1] - label_w - 10, midpoint[0] - label_w // 2))
    label_pos = (label_x, max(24, midpoint[1] - 12))
    cv2.putText(frame, label, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.58, LINE_COLOR, 2, cv2.LINE_AA)

    cv2.putText(
        frame,
        "IN",
        (in_end[0] + 4, in_end[1] - 4),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        IN_COLOR,
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "OUT",
        (out_end[0] + 4, out_end[1] - 4),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        OUT_COLOR,
        2,
        cv2.LINE_AA,
    )


def _direction_label(hint: str) -> str:
    mapping = {
        "down_is_in": "down",
        "up_is_in": "up",
        "right_is_in": "right",
        "left_is_in": "left",
        "positive_is_in": "positive-side",
        "negative_is_in": "negative-side",
    }
    return mapping.get(hint, hint)


def _in_vector(line_rule: dict) -> tuple[float, float]:
    hint = line_rule.get("direction_hint", "positive_is_in")
    if hint == "down_is_in":
        return (0.0, 1.0)
    if hint == "up_is_in":
        return (0.0, -1.0)
    if hint == "right_is_in":
        return (1.0, 0.0)
    if hint == "left_is_in":
        return (-1.0, 0.0)

    (x1, y1), (x2, y2) = line_rule["points"]
    dx = float(x2 - x1)
    dy = float(y2 - y1)
    normal = (-dy, dx)
    length = math.hypot(normal[0], normal[1]) or 1.0
    normal = (normal[0] / length, normal[1] / length)
    if hint == "negative_is_in":
        return (-normal[0], -normal[1])
    return normal


def _draw_stats(frame, tracked_objects, totals: dict, occupancy: dict[str, int], events) -> None:
    frame_events = _summarize_events(events)
    lines = [
        "Car Flow Monitor",
        f"Tracked now: {len(tracked_objects)}",
        f"This frame IN:{frame_events['IN']} OUT:{frame_events['OUT']}",
    ]

    if totals:
        lines.append("Total flow:")
        for rule_id, directions in totals.items():
            lines.append(f"{rule_id}  IN:{directions.get('IN', 0)}  OUT:{directions.get('OUT', 0)}")

    if occupancy:
        lines.append("Region occupancy:")
        for region_id, count in occupancy.items():
            lines.append(f"{region_id}: {count}")

    x = 14
    y = 14
    line_height = 24
    width = _panel_width(lines)
    height = 14 + len(lines) * line_height

    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + width, y + height), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    text_y = y + 26
    for index, text in enumerate(lines):
        color = (255, 255, 255)
        thickness = 2 if index == 0 else 1
        if text.startswith("This frame IN:"):
            color = (180, 255, 180)
        elif text in ("Total flow:", "Region occupancy:"):
            color = (255, 255, 0)
            thickness = 2
        cv2.putText(frame, text, (x + 10, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, thickness, cv2.LINE_AA)
        text_y += line_height


def _summarize_events(events) -> dict[str, int]:
    summary = {"IN": 0, "OUT": 0}
    for event in events:
        if getattr(event, "direction", None) in summary:
            summary[event.direction] += 1
    return summary


def _panel_width(lines: list[str]) -> int:
    max_width = 280
    for text in lines:
        (text_width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        max_width = max(max_width, text_width + 20)
    return max_width


def _as_contour(points: list[tuple[float, float]]):
    return np.array(points, dtype=np.int32).reshape((-1, 1, 2))
