"""Application services."""

from __future__ import annotations

from dataclasses import dataclass

from tmviz.domain.exceptions import RuleNotFoundError
from tmviz.domain.machine import PreparedStep, StepResult, TuringMachine
from tmviz.infra.event_bus import EventBus

from .events import (
    HeadMovedEvent,
    MachineErrorEvent,
    MachineHaltedEvent,
    RuleSelectedEvent,
    StepCommittedEvent,
    StepStartedEvent,
    SymbolReadEvent,
    SymbolWrittenEvent,
)


@dataclass(slots=True)
class StepService:
    """Coordinates the step pipeline and emits phase-level events."""

    event_bus: EventBus
    machine: TuringMachine | None = None
    prepared_step: PreparedStep | None = None
    previous_head_position: int | None = None
    current_head_position: int | None = None
    last_result: StepResult | None = None

    def attach_machine(self, machine: TuringMachine) -> None:
        self.machine = machine
        self.reset()

    def reset(self) -> None:
        self.prepared_step = None
        self.previous_head_position = None
        self.current_head_position = None
        self.last_result = None

    def fetch(self) -> str:
        machine = self._require_machine()
        self.event_bus.publish(
            StepStartedEvent(
                step_count=machine.step_count,
                state=machine.current_state,
                head_position=machine.head_position,
            )
        )
        symbol = machine.read_symbol()
        self.event_bus.publish(SymbolReadEvent(symbol=symbol, position=machine.head_position))
        return symbol

    def lookup(self) -> PreparedStep | None:
        machine = self._require_machine()
        try:
            self.prepared_step = machine.prepare_step()
        except RuleNotFoundError as exc:
            try:
                machine.handle_missing_rule()
            except RuleNotFoundError:
                self.event_bus.publish(MachineErrorEvent(str(exc)))
                raise
            self.event_bus.publish(
                MachineHaltedEvent(
                    reason=machine.halt_reason or "no_rule",
                    state=machine.current_state,
                )
            )
            return None

        self.event_bus.publish(RuleSelectedEvent(rule=self.prepared_step.rule))
        return self.prepared_step

    def write(self) -> None:
        machine = self._require_machine()
        prepared = self._require_prepared_step()
        machine.apply_write_phase(prepared)
        self.event_bus.publish(
            SymbolWrittenEvent(symbol=prepared.rule.write_symbol, position=machine.head_position)
        )

    def move(self) -> tuple[int, int]:
        machine = self._require_machine()
        prepared = self._require_prepared_step()
        self.previous_head_position, self.current_head_position = machine.apply_move_phase(prepared)
        self.event_bus.publish(
            HeadMovedEvent(
                previous_position=self.previous_head_position,
                position=self.current_head_position,
            )
        )
        return self.previous_head_position, self.current_head_position

    def commit(self) -> StepResult:
        machine = self._require_machine()
        prepared = self._require_prepared_step()
        if self.previous_head_position is None or self.current_head_position is None:
            raise RuntimeError("move must be executed before commit")

        result = machine.commit_prepared_step(
            prepared,
            previous_head_position=self.previous_head_position,
            head_position=self.current_head_position,
        )
        self.event_bus.publish(
            StepCommittedEvent(step_count=result.step_count, state=result.current_state)
        )
        if result.halted:
            self.event_bus.publish(
                MachineHaltedEvent(
                    reason=result.halt_reason or "halted",
                    state=result.current_state,
                )
            )
        self.last_result = result
        self.prepared_step = None
        self.previous_head_position = None
        self.current_head_position = None
        return result

    def _require_machine(self) -> TuringMachine:
        if self.machine is None:
            raise RuntimeError("No machine is attached")
        return self.machine

    def _require_prepared_step(self) -> PreparedStep:
        if self.prepared_step is None:
            raise RuntimeError("No prepared step is available")
        return self.prepared_step

