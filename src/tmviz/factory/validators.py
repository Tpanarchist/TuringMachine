"""Validation helpers for machine specs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from tmviz.domain.configuration import MachineConfiguration
from tmviz.domain.exceptions import SpecValidationError
from tmviz.domain.moves import Direction
from tmviz.domain.rule import Rule

from .spec_models import MachineSpec

REQUIRED_FIELDS = {
    "name",
    "blank_symbol",
    "states",
    "start_state",
    "accept_states",
    "alphabet",
    "initial_tape",
    "initial_head",
    "rules",
}

ALLOWED_MISSING_RULE_POLICIES = {"halt", "reject", "error"}


def normalize_spec(raw_spec: Mapping[str, Any]) -> MachineSpec:
    missing_fields = REQUIRED_FIELDS.difference(raw_spec)
    if missing_fields:
        raise SpecValidationError(f"Spec is missing required fields: {sorted(missing_fields)}")

    name = _require_non_empty_string(raw_spec["name"], "name")
    blank_symbol = _require_non_empty_string(raw_spec["blank_symbol"], "blank_symbol")
    states = tuple(_require_string_sequence(raw_spec["states"], "states"))
    alphabet = tuple(_require_string_sequence(raw_spec["alphabet"], "alphabet"))
    start_state = _require_non_empty_string(raw_spec["start_state"], "start_state")
    accept_states = tuple(_require_string_sequence(raw_spec["accept_states"], "accept_states"))
    reject_states = tuple(
        _require_string_sequence(raw_spec.get("reject_states", []), "reject_states")
    )
    initial_tape = tuple(_require_string_sequence(raw_spec["initial_tape"], "initial_tape"))
    initial_head = _require_int(raw_spec["initial_head"], "initial_head")
    missing_rule_policy = raw_spec.get("missing_rule_policy", "halt")

    if blank_symbol not in alphabet:
        raise SpecValidationError("blank_symbol must be present in the alphabet")
    if len(set(states)) != len(states):
        raise SpecValidationError("states must be unique")
    if len(set(alphabet)) != len(alphabet):
        raise SpecValidationError("alphabet must be unique")
    if start_state not in states:
        raise SpecValidationError("start_state must be in states")
    if any(state not in states for state in accept_states):
        raise SpecValidationError("accept_states must be a subset of states")
    if any(state not in states for state in reject_states):
        raise SpecValidationError("reject_states must be a subset of states")
    if any(symbol not in alphabet for symbol in initial_tape):
        raise SpecValidationError("initial_tape contains symbols outside the alphabet")
    if missing_rule_policy not in ALLOWED_MISSING_RULE_POLICIES:
        raise SpecValidationError(
            f"missing_rule_policy must be one of {sorted(ALLOWED_MISSING_RULE_POLICIES)}"
        )

    rules = _normalize_rules(raw_spec["rules"], states, alphabet)
    config = MachineConfiguration(
        name=name,
        blank_symbol=blank_symbol,
        states=states,
        alphabet=alphabet,
        start_state=start_state,
        accept_states=accept_states,
        reject_states=reject_states,
        initial_tape=initial_tape,
        initial_head=initial_head,
        missing_rule_policy=missing_rule_policy,
    )
    return MachineSpec(config=config, rules=rules)


def _normalize_rules(
    raw_rules: Any,
    states: tuple[str, ...],
    alphabet: tuple[str, ...],
) -> tuple[Rule, ...]:
    if not isinstance(raw_rules, Sequence) or isinstance(raw_rules, (str, bytes)):
        raise SpecValidationError("rules must be a sequence of 5-item rows")

    seen_keys: set[tuple[str, str]] = set()
    normalized_rules: list[Rule] = []
    for index, raw_rule in enumerate(raw_rules):
        if not isinstance(raw_rule, Sequence) or isinstance(raw_rule, (str, bytes)):
            raise SpecValidationError(f"Rule #{index} must be a 5-item sequence")
        if len(raw_rule) != 5:
            raise SpecValidationError(f"Rule #{index} must contain exactly 5 items")
        current_state, read_symbol, next_state, write_symbol, move_direction = raw_rule
        current_state = _require_non_empty_string(current_state, f"rules[{index}][0]")
        read_symbol = _require_non_empty_string(read_symbol, f"rules[{index}][1]")
        next_state = _require_non_empty_string(next_state, f"rules[{index}][2]")
        write_symbol = _require_non_empty_string(write_symbol, f"rules[{index}][3]")
        move_direction = _require_non_empty_string(move_direction, f"rules[{index}][4]")

        if current_state not in states or next_state not in states:
            raise SpecValidationError(f"Rule #{index} references an unknown state")
        if read_symbol not in alphabet or write_symbol not in alphabet:
            raise SpecValidationError(f"Rule #{index} references an unknown symbol")

        key = (current_state, read_symbol)
        if key in seen_keys:
            raise SpecValidationError(f"Duplicate rule for state/symbol pair: {key}")
        seen_keys.add(key)

        normalized_rules.append(
            Rule(
                current_state=current_state,
                read_symbol=read_symbol,
                next_state=next_state,
                write_symbol=write_symbol,
                move_direction=Direction.parse(move_direction),
            )
        )

    return tuple(normalized_rules)


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise SpecValidationError(f"{field_name} must be a non-empty string")
    return value


def _require_string_sequence(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise SpecValidationError(f"{field_name} must be a sequence of strings")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise SpecValidationError(f"{field_name} must contain only non-empty strings")
        normalized.append(item)
    return normalized


def _require_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int):
        raise SpecValidationError(f"{field_name} must be an integer")
    return value
