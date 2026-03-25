"""A tiny synchronous event bus."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class EventRecord:
    """Captured event and its display summary."""

    event: object
    summary: str


class EventBus:
    """Simple in-process pub/sub with a short event history for the UI."""

    def __init__(self, history_limit: int = 10) -> None:
        self._subscribers: dict[type[Any], list[Callable[[object], None]]] = defaultdict(list)
        self._history: deque[EventRecord] = deque(maxlen=history_limit)

    def subscribe(self, event_type: type[Any], callback: Callable[[object], None]) -> None:
        self._subscribers[event_type].append(callback)

    def publish(self, event: object) -> None:
        summary_method = getattr(event, "summary", None)
        summary = summary_method() if callable(summary_method) else repr(event)
        record = EventRecord(event=event, summary=summary)
        self._history.append(record)
        for subscriber in self._subscribers.get(type(event), []):
            subscriber(event)

    @property
    def history(self) -> list[EventRecord]:
        return list(self._history)

