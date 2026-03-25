"""Application controller and state machine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from transitions.extensions import HierarchicalMachine

from tmviz.domain.machine import StepResult, TuringMachine
from tmviz.domain.rule import Rule
from tmviz.factory.machine_factory import MachineSpecFactory
from tmviz.infra.event_bus import EventBus

from .commands import (
    CenterHeadCommand,
    Command,
    LoadMachineCommand,
    PauseCommand,
    ReloadMachineCommand,
    ResetCommand,
    RunCommand,
    SetSpeedCommand,
    StepCommand,
    ToggleGridCommand,
)
from .events import (
    CenterHeadEvent,
    GridToggledEvent,
    MachineErrorEvent,
    MachineLoadedEvent,
    MachineResetEvent,
    SpeedChangedEvent,
    StateChangedEvent,
)
from .services import StepService
from .statechart import APP_STATES, RUNNING_PHASES

RUNNING_STATES = [f"running_{phase}" for phase in RUNNING_PHASES]


@dataclass(frozen=True, slots=True)
class ControllerSnapshot:
    """State exposed to the renderer."""

    app_state: str
    phase: str | None
    machine_name: str
    control_state: str
    head_position: int
    current_symbol: str
    current_rule: Rule | None
    last_rule: Rule | None
    step_count: int
    halted: bool
    halt_reason: str | None
    error_message: str | None
    tape_window: list[tuple[int, str]]
    steps_per_second: float
    grid_enabled: bool
    event_log: list[str]


class AppController:
    """Owns app lifecycle, command handling, and phased stepping."""

    state: str

    if TYPE_CHECKING:
        def boot_complete(self) -> bool: ...
        def set_loaded(self) -> bool: ...
        def start_running(self) -> bool: ...
        def advance_lookup(self) -> bool: ...
        def advance_write(self) -> bool: ...
        def advance_move(self) -> bool: ...
        def advance_commit(self) -> bool: ...
        def complete_step(self) -> bool: ...
        def continue_running(self) -> bool: ...
        def pause_running(self) -> bool: ...
        def halt_running(self) -> bool: ...
        def fail(self) -> bool: ...
        def reset_to_loaded(self) -> bool: ...

    def __init__(self, factory: MachineSpecFactory, event_bus: EventBus) -> None:
        self.factory = factory
        self.event_bus = event_bus
        self.step_service = StepService(event_bus=event_bus)
        self.machine: TuringMachine | None = None
        self.current_spec_path: Path | None = None
        self.steps_per_second = 2.0
        self.grid_enabled = True
        self.error_message: str | None = None
        self.last_step_result: StepResult | None = None
        self.current_read_symbol: str | None = None
        self.current_rule: Rule | None = None
        self._phase_accumulator = 0.0
        self._run_mode: Literal["idle", "continuous", "single"] = "idle"

        self._machine = HierarchicalMachine(
            model=self,
            states=APP_STATES,
            initial="boot",
            auto_transitions=False,
            ignore_invalid_triggers=True,
            after_state_change="_publish_state_change",
        )
        self._machine.add_transition("boot_complete", "boot", "idle")
        self._machine.add_transition("set_loaded", "*", "loaded")
        self._machine.add_transition("start_running", ["loaded", "paused"], "running_fetch")
        self._machine.add_transition("advance_lookup", "running_fetch", "running_lookup")
        self._machine.add_transition("advance_write", "running_lookup", "running_write")
        self._machine.add_transition("advance_move", "running_write", "running_move")
        self._machine.add_transition("advance_commit", "running_move", "running_commit")
        self._machine.add_transition("complete_step", "running_commit", "loaded")
        self._machine.add_transition("continue_running", "running_commit", "running_fetch")
        self._machine.add_transition("pause_running", RUNNING_STATES, "paused")
        self._machine.add_transition("halt_running", RUNNING_STATES, "halted")
        self._machine.add_transition("fail", "*", "error")
        self._machine.add_transition(
            "reset_to_loaded",
            ["loaded", "paused", "halted", "error", *RUNNING_STATES],
            "loaded",
        )

    def execute(self, command: Command) -> None:
        if isinstance(command, LoadMachineCommand):
            self.load_machine(command.spec_path)
            return
        if isinstance(command, StepCommand):
            self.single_step()
            return
        if isinstance(command, RunCommand):
            self.run()
            return
        if isinstance(command, PauseCommand):
            self.pause()
            return
        if isinstance(command, ResetCommand):
            self.reset_machine()
            return
        if isinstance(command, SetSpeedCommand):
            self.set_speed(command.steps_per_second)
            return
        if isinstance(command, ToggleGridCommand):
            self.toggle_grid()
            return
        if isinstance(command, CenterHeadCommand):
            self.center_head()
            return
        if isinstance(command, ReloadMachineCommand):
            if self.current_spec_path is not None:
                self.load_machine(self.current_spec_path)
            return
        raise TypeError(f"Unsupported command: {command!r}")

    def load_machine(self, path: Path) -> None:
        try:
            machine = self.factory.from_path(path)
        except Exception as exc:
            self.error_message = str(exc)
            self.event_bus.publish(MachineErrorEvent(self.error_message))
            self.fail()
            return

        self.machine = machine
        self.current_spec_path = path
        self.step_service.attach_machine(machine)
        self.last_step_result = None
        self.current_read_symbol = machine.read_symbol()
        self.current_rule = None
        self.error_message = None
        self._phase_accumulator = 0.0
        self._run_mode = "idle"
        self.set_loaded()
        self.event_bus.publish(MachineLoadedEvent(name=machine.name, source=str(path)))

    def run(self) -> None:
        if self.machine is None or self.machine.halted:
            return
        if self.state in {"loaded", "paused"}:
            self._run_mode = "continuous"
            self.start_running()

    def pause(self) -> None:
        if self.state in RUNNING_STATES:
            self._run_mode = "idle"
            self.pause_running()

    def reset_machine(self) -> None:
        if self.machine is None:
            return
        self.machine.reset()
        self.step_service.reset()
        self.last_step_result = None
        self.current_read_symbol = self.machine.read_symbol()
        self.current_rule = None
        self.error_message = None
        self._phase_accumulator = 0.0
        self._run_mode = "idle"
        if self.state != "loaded":
            self.reset_to_loaded()
        self.event_bus.publish(MachineResetEvent(name=self.machine.name))

    def set_speed(self, steps_per_second: float) -> None:
        self.steps_per_second = max(0.25, steps_per_second)
        self.event_bus.publish(SpeedChangedEvent(steps_per_second=self.steps_per_second))

    def toggle_grid(self) -> None:
        self.grid_enabled = not self.grid_enabled
        self.event_bus.publish(GridToggledEvent(enabled=self.grid_enabled))

    def center_head(self) -> None:
        if self.machine is None:
            return
        self.event_bus.publish(CenterHeadEvent(head_position=self.machine.head_position))

    def single_step(self) -> None:
        if self.machine is None or self.machine.halted:
            return
        if self.state not in {"loaded", "paused"}:
            return
        self._run_mode = "single"
        self.start_running()
        while self.state in RUNNING_STATES:
            self._advance_phase()

    def update(self, delta_seconds: float) -> None:
        if self.state not in RUNNING_STATES or self._run_mode != "continuous":
            return
        self._phase_accumulator += delta_seconds
        interval = max(0.02, 1.0 / (self.steps_per_second * 5.0))
        while self._phase_accumulator >= interval and self.state in RUNNING_STATES:
            self._phase_accumulator -= interval
            self._advance_phase()

    def snapshot(self) -> ControllerSnapshot:
        if self.machine is None:
            return ControllerSnapshot(
                app_state=self.state,
                phase=None,
                machine_name="No machine loaded",
                control_state="-",
                head_position=0,
                current_symbol="-",
                current_rule=None,
                last_rule=None,
                step_count=0,
                halted=False,
                halt_reason=None,
                error_message=self.error_message,
                tape_window=[(index, "_") for index in range(-6, 7)],
                steps_per_second=self.steps_per_second,
                grid_enabled=self.grid_enabled,
                event_log=[record.summary for record in self.event_bus.history],
            )

        phase = self.state.split("_", 1)[1] if self.state.startswith("running_") else None
        return ControllerSnapshot(
            app_state=self.state,
            phase=phase,
            machine_name=self.machine.name,
            control_state=self.machine.current_state,
            head_position=self.machine.head_position,
            current_symbol=self.machine.read_symbol(),
            current_rule=self.current_rule,
            last_rule=self.machine.last_rule,
            step_count=self.machine.step_count,
            halted=self.machine.halted,
            halt_reason=self.machine.halt_reason,
            error_message=self.error_message,
            tape_window=self.machine.preview_window(radius=6),
            steps_per_second=self.steps_per_second,
            grid_enabled=self.grid_enabled,
            event_log=[record.summary for record in self.event_bus.history],
        )

    def _advance_phase(self) -> None:
        if self.machine is None:
            return
        try:
            if self.state == "running_fetch":
                self.current_read_symbol = self.step_service.fetch()
                self.advance_lookup()
                return
            if self.state == "running_lookup":
                prepared = self.step_service.lookup()
                if prepared is None:
                    self.current_rule = None
                    self._run_mode = "idle"
                    self.halt_running()
                    return
                self.current_rule = prepared.rule
                self.advance_write()
                return
            if self.state == "running_write":
                self.step_service.write()
                self.advance_move()
                return
            if self.state == "running_move":
                self.step_service.move()
                self.advance_commit()
                return
            if self.state == "running_commit":
                self.last_step_result = self.step_service.commit()
                self.current_rule = self.last_step_result.rule
                self.current_read_symbol = self.machine.read_symbol()
                if self.last_step_result.halted:
                    self._run_mode = "idle"
                    self.halt_running()
                    return
                if self._run_mode == "continuous":
                    self.continue_running()
                    return
                self._run_mode = "idle"
                self.complete_step()
        except Exception as exc:
            self.error_message = str(exc)
            self._run_mode = "idle"
            self.event_bus.publish(MachineErrorEvent(self.error_message))
            self.fail()

    def _publish_state_change(self) -> None:
        self.event_bus.publish(StateChangedEvent(state=self.state))
