"""Configuration object used to build and reset a machine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MachineConfiguration:
    """Normalized machine specification."""

    name: str
    blank_symbol: str
    states: tuple[str, ...]
    alphabet: tuple[str, ...]
    start_state: str
    accept_states: tuple[str, ...]
    reject_states: tuple[str, ...]
    initial_tape: tuple[str, ...]
    initial_head: int
    missing_rule_policy: str = "halt"

