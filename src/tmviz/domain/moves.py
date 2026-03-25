"""Tape movement definitions."""

from __future__ import annotations

from enum import StrEnum

from .exceptions import InvalidDirectionError


class Direction(StrEnum):
    """Valid head movement directions."""

    LEFT = "L"
    RIGHT = "R"
    STAY = "S"

    @property
    def delta(self) -> int:
        if self is Direction.LEFT:
            return -1
        if self is Direction.RIGHT:
            return 1
        return 0

    @classmethod
    def parse(cls, value: str) -> Direction:
        try:
            return cls(value)
        except ValueError as exc:
            raise InvalidDirectionError(f"Unsupported direction: {value!r}") from exc
