"""Application events emitted to the UI and logs."""

from __future__ import annotations

from dataclasses import dataclass

from tmviz.domain.rule import Rule


@dataclass(frozen=True, slots=True)
class StateChangedEvent:
    state: str

    def summary(self) -> str:
        return f"App state -> {self.state}"


@dataclass(frozen=True, slots=True)
class MachineLoadedEvent:
    name: str
    source: str

    def summary(self) -> str:
        return f"Loaded machine: {self.name}"


@dataclass(frozen=True, slots=True)
class MachineResetEvent:
    name: str

    def summary(self) -> str:
        return f"Reset machine: {self.name}"


@dataclass(frozen=True, slots=True)
class StepStartedEvent:
    step_count: int
    state: str
    head_position: int

    def summary(self) -> str:
        return f"Step {self.step_count + 1} started at {self.state}"


@dataclass(frozen=True, slots=True)
class SymbolReadEvent:
    symbol: str
    position: int

    def summary(self) -> str:
        return f"Read {self.symbol!r} at {self.position}"


@dataclass(frozen=True, slots=True)
class RuleSelectedEvent:
    rule: Rule

    def summary(self) -> str:
        return f"Rule {self.rule.describe()}"


@dataclass(frozen=True, slots=True)
class SymbolWrittenEvent:
    symbol: str
    position: int

    def summary(self) -> str:
        return f"Wrote {self.symbol!r} at {self.position}"


@dataclass(frozen=True, slots=True)
class HeadMovedEvent:
    previous_position: int
    position: int

    def summary(self) -> str:
        return f"Head {self.previous_position} -> {self.position}"


@dataclass(frozen=True, slots=True)
class StepCommittedEvent:
    step_count: int
    state: str

    def summary(self) -> str:
        return f"Committed step {self.step_count} in {self.state}"


@dataclass(frozen=True, slots=True)
class MachineHaltedEvent:
    reason: str
    state: str

    def summary(self) -> str:
        return f"Halted ({self.reason}) in {self.state}"


@dataclass(frozen=True, slots=True)
class MachineErrorEvent:
    message: str

    def summary(self) -> str:
        return f"Error: {self.message}"


@dataclass(frozen=True, slots=True)
class SpeedChangedEvent:
    steps_per_second: float

    def summary(self) -> str:
        return f"Speed {self.steps_per_second:.1f} step/s"


@dataclass(frozen=True, slots=True)
class GridToggledEvent:
    enabled: bool

    def summary(self) -> str:
        return "Grid enabled" if self.enabled else "Grid disabled"


@dataclass(frozen=True, slots=True)
class CenterHeadEvent:
    head_position: int

    def summary(self) -> str:
        return f"Centered head on {self.head_position}"

