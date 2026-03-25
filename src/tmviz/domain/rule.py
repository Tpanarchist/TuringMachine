"""Transition rules for the Turing machine."""

from __future__ import annotations

from dataclasses import dataclass

from .moves import Direction


@dataclass(frozen=True, slots=True)
class Rule:
    """A single transition function entry."""

    current_state: str
    read_symbol: str
    next_state: str
    write_symbol: str
    move_direction: Direction

    def describe(self) -> str:
        return (
            f"({self.current_state}, {self.read_symbol}) -> "
            f"({self.next_state}, {self.write_symbol}, {self.move_direction.value})"
        )

