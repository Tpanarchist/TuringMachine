"""Deterministic Turing machine engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from .configuration import MachineConfiguration
from .exceptions import InvalidSymbolError, MachineHaltedError, RuleNotFoundError
from .moves import Direction
from .rule import Rule
from .tape import Tape


@dataclass(frozen=True, slots=True)
class StepResult:
    """Result of a completed transition."""

    previous_state: str
    read_symbol: str
    rule: Rule | None
    previous_head_position: int
    head_position: int
    current_state: str
    step_count: int
    halted: bool
    halt_reason: str | None


@dataclass(frozen=True, slots=True)
class PreparedStep:
    """Intermediate data used for animated sub-phases."""

    previous_state: str
    read_symbol: str
    rule: Rule
    head_position: int


@dataclass(slots=True)
class TuringMachine:
    """Turing machine state and deterministic step logic."""

    config: MachineConfiguration
    tape: Tape
    rules: dict[tuple[str, str], Rule]
    current_state: str = field(init=False)
    head_position: int = field(init=False)
    step_count: int = field(default=0, init=False)
    halted: bool = field(default=False, init=False)
    halt_reason: str | None = field(default=None, init=False)
    last_rule: Rule | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.reset()

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def accept_states(self) -> tuple[str, ...]:
        return self.config.accept_states

    @property
    def reject_states(self) -> tuple[str, ...]:
        return self.config.reject_states

    @property
    def blank_symbol(self) -> str:
        return self.config.blank_symbol

    def reset(self) -> None:
        self.tape = Tape.from_symbols(list(self.config.initial_tape), self.config.blank_symbol)
        self.current_state = self.config.start_state
        self.head_position = self.config.initial_head
        self.step_count = 0
        self.halted = False
        self.halt_reason = None
        self.last_rule = None
        self._update_halt_status()

    def read_symbol(self) -> str:
        return self.tape.read(self.head_position)

    def lookup_rule(self, read_symbol: str | None = None) -> Rule:
        symbol = read_symbol if read_symbol is not None else self.read_symbol()
        key = (self.current_state, symbol)
        try:
            return self.rules[key]
        except KeyError as exc:
            raise RuleNotFoundError(
                f"No rule for state={self.current_state!r}, symbol={symbol!r}"
            ) from exc

    def write_symbol(self, symbol: str) -> None:
        self._validate_symbol(symbol)
        self.tape.write(self.head_position, symbol)

    def move_head(self, direction: Direction) -> tuple[int, int]:
        previous_position = self.head_position
        self.head_position += direction.delta
        return previous_position, self.head_position

    def update_control_state(self, next_state: str) -> None:
        self.current_state = next_state

    def prepare_step(self) -> PreparedStep:
        self._ensure_runnable()
        previous_state = self.current_state
        read_symbol = self.read_symbol()
        rule = self.lookup_rule(read_symbol)
        return PreparedStep(
            previous_state=previous_state,
            read_symbol=read_symbol,
            rule=rule,
            head_position=self.head_position,
        )

    def apply_prepared_step(self, prepared: PreparedStep) -> StepResult:
        self._ensure_runnable()
        self.apply_write_phase(prepared)
        previous_head, current_head = self.apply_move_phase(prepared)
        return self.commit_prepared_step(prepared, previous_head, current_head)

    def step(self) -> StepResult:
        try:
            prepared = self.prepare_step()
        except RuleNotFoundError:
            previous_state = self.current_state
            read_symbol = self.read_symbol()
            previous_head = self.head_position
            self.handle_missing_rule()
            return StepResult(
                previous_state=previous_state,
                read_symbol=read_symbol,
                rule=None,
                previous_head_position=previous_head,
                head_position=previous_head,
                current_state=self.current_state,
                step_count=self.step_count,
                halted=self.halted,
                halt_reason=self.halt_reason,
            )
        return self.apply_prepared_step(prepared)

    def preview_window(self, radius: int = 8) -> list[tuple[int, str]]:
        minimum, maximum = self.tape.populated_bounds()
        minimum = min(minimum, self.head_position - radius)
        maximum = max(maximum, self.head_position + radius)
        return self.tape.snapshot(minimum, maximum)

    def _validate_symbol(self, symbol: str) -> None:
        if symbol not in self.config.alphabet:
            raise InvalidSymbolError(f"Symbol {symbol!r} is not in the machine alphabet")

    def apply_write_phase(self, prepared: PreparedStep) -> None:
        self.write_symbol(prepared.rule.write_symbol)

    def apply_move_phase(self, prepared: PreparedStep) -> tuple[int, int]:
        return self.move_head(prepared.rule.move_direction)

    def commit_prepared_step(
        self,
        prepared: PreparedStep,
        previous_head_position: int,
        head_position: int,
    ) -> StepResult:
        self.update_control_state(prepared.rule.next_state)
        self.last_rule = prepared.rule
        self.step_count += 1
        self._update_halt_status()
        return StepResult(
            previous_state=prepared.previous_state,
            read_symbol=prepared.read_symbol,
            rule=prepared.rule,
            previous_head_position=previous_head_position,
            head_position=head_position,
            current_state=self.current_state,
            step_count=self.step_count,
            halted=self.halted,
            halt_reason=self.halt_reason,
        )

    def _ensure_runnable(self) -> None:
        self._update_halt_status()
        if self.halted:
            raise MachineHaltedError(f"Machine is halted ({self.halt_reason})")

    def _update_halt_status(self) -> None:
        if self.current_state in self.accept_states:
            self.halted = True
            self.halt_reason = "accept"
            return
        if self.current_state in self.reject_states:
            self.halted = True
            self.halt_reason = "reject"
            return
        self.halted = False
        self.halt_reason = None

    def handle_missing_rule(self) -> None:
        policy = self.config.missing_rule_policy
        if policy == "halt":
            self.halted = True
            self.halt_reason = "no_rule"
            return
        if policy == "reject":
            if self.reject_states:
                self.current_state = self.reject_states[0]
            self.halted = True
            self.halt_reason = "reject"
            return
        raise RuleNotFoundError(
            f"No rule for state={self.current_state!r}, symbol={self.read_symbol()!r}"
        )
