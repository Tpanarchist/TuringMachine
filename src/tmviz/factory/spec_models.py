"""Normalized specification models."""

from __future__ import annotations

from dataclasses import dataclass

from tmviz.domain.configuration import MachineConfiguration
from tmviz.domain.rule import Rule


@dataclass(frozen=True, slots=True)
class MachineSpec:
    """Validated machine specification."""

    config: MachineConfiguration
    rules: tuple[Rule, ...]

