from __future__ import annotations

import cv2
import numpy as np

from .geometry import polygon_bounds


def draw_overlay(frame, rules: dict, tracked_objects, track_history: dict[int, list[tuple[float, float]]], snapshot: dict):
    for line in rules.get("lines", []):
        points = [tuple(int(v) for v in point) for point in line["points"]]
        cv2.line(frame, points[0], points[1], (0, 255, 255), 2)
        cv2.putText(
            frame,
            line["id"],
            points[0],
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

    for region in rules.get("regions", []):
        points = [tuple(int(v) for v in point) for point in region["points"]]
        cv2.polylines(frame, [_as_contour(points)], isClosed=True, color=(255, 200, 0), thickness=2)
        x1, y1, _, _ = polygon_bounds(region["points"])
        cv2.putText(
            frame,
            region["id"],
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 200, 0),
            2,
            cv2.LINE_AA,
        )

    for tracked in tracked_objects:
        x1, y1, x2, y2 = [int(value) for value in tracked.bbox]
        color = (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame,
            f"{tracked.class_name}#{tracked.track_id} {tracked.confidence:.2f}",
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
            cv2.LINE_AA,
        )
        ax, ay = int(tracked.anchor[0]), int(tracked.anchor[1])
        cv2.circle(frame, (ax, ay), 4, (0, 0, 255), -1)

        history = track_history.get(tracked.track_id, [])
        if len(history) >= 2:
            cv2.polylines(frame, [_as_contour(history)], isClosed=False, color=(240, 240, 240), thickness=2)

    _draw_stats(frame, snapshot.get("totals", {}))
    return frame


def _draw_stats(frame, totals: dict) -> None:
    x = 15
    y = 25
    cv2.putText(frame, "Flow Totals", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    y += 26
    for rule_id, directions in totals.items():
        cv2.putText(frame, rule_id, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 2, cv2.LINE_AA)
        y += 22
        for direction, classes in directions.items():
            parts = [f"{vehicle_class}:{count}" for vehicle_class, count in classes.items()]
            text = f"{direction} " + ", ".join(parts)
            cv2.putText(frame, text, (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1, cv2.LINE_AA)
            y += 20
        y += 6


def _as_contour(points: list[tuple[float, float]]):
    return np.array(points, dtype=np.int32).reshape((-1, 1, 2))
