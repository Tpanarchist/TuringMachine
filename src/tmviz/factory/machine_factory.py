"""Builds machine instances from validated specifications."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tmviz.domain.machine import TuringMachine
from tmviz.domain.tape import Tape
from tmviz.infra.spec_loader import load_json_spec

from .spec_models import MachineSpec
from .validators import normalize_spec


class MachineSpecFactory:
    """Factory for creating Turing machines from various spec sources."""

    def from_mapping(self, raw_spec: dict[str, Any]) -> TuringMachine:
        spec = normalize_spec(raw_spec)
        return self.build_machine(spec)

    def from_path(self, path: Path) -> TuringMachine:
        raw_spec = load_json_spec(path)
        return self.from_mapping(raw_spec)

    def build_machine(self, spec: MachineSpec) -> TuringMachine:
        rules = {(rule.current_state, rule.read_symbol): rule for rule in spec.rules}
        tape = Tape.from_symbols(list(spec.config.initial_tape), spec.config.blank_symbol)
        return TuringMachine(config=spec.config, tape=tape, rules=rules)

