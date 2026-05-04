from __future__ import annotations

from collections import defaultdict

from .models import FlowEvent


class FlowAggregator:
    def __init__(self) -> None:
        self.total_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.minute_buckets: dict[str, dict[str, dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )

    def add_event(self, event: FlowEvent) -> None:
        self.total_counts[event.rule_id][event.direction] += 1
        minute_key = str(event.timestamp_ms // 60000)
        self.minute_buckets[minute_key][event.rule_id][event.direction] += 1

    def snapshot(self) -> dict:
        return {
            "totals": _freeze_nested_dict(self.total_counts),
            "minutes": _freeze_nested_dict(self.minute_buckets),
        }


def _freeze_nested_dict(value):
    if isinstance(value, defaultdict):
        value = dict(value)
    if isinstance(value, dict):
        return {key: _freeze_nested_dict(item) for key, item in value.items()}
    return value

