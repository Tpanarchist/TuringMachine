from tmviz.domain.configuration import MachineConfiguration
from tmviz.domain.exceptions import RuleNotFoundError
from tmviz.domain.machine import TuringMachine
from tmviz.domain.moves import Direction
from tmviz.domain.rule import Rule
from tmviz.domain.tape import Tape


def build_machine(missing_rule_policy: str = "halt") -> TuringMachine:
    config = MachineConfiguration(
        name="Unary Increment",
        blank_symbol="_",
        states=("q0", "halt"),
        alphabet=("1", "_"),
        start_state="q0",
        accept_states=("halt",),
        reject_states=(),
        initial_tape=("1", "1", "1", "_"),
        initial_head=0,
        missing_rule_policy=missing_rule_policy,
    )
    rules = {
        ("q0", "1"): Rule("q0", "1", "q0", "1", Direction.RIGHT),
        ("q0", "_"): Rule("q0", "_", "halt", "1", Direction.STAY),
    }
    return TuringMachine(
        config=config,
        tape=Tape.from_symbols(list(config.initial_tape), "_"),
        rules=rules,
    )


def test_unary_increment_halts_with_incremented_tape() -> None:
    machine = build_machine()

    results = [machine.step() for _ in range(4)]

    assert results[-1].halted is True
    assert machine.current_state == "halt"
    assert machine.halt_reason == "accept"
    assert machine.head_position == 3
    assert [machine.tape.read(index) for index in range(5)] == ["1", "1", "1", "1", "_"]


def test_missing_rule_halts_without_advancing_step_count() -> None:
    config = MachineConfiguration(
        name="No Rule",
        blank_symbol="_",
        states=("q0",),
        alphabet=("_",),
        start_state="q0",
        accept_states=(),
        reject_states=(),
        initial_tape=("_",),
        initial_head=0,
        missing_rule_policy="halt",
    )
    machine = TuringMachine(config=config, tape=Tape.from_symbols(["_"], "_"), rules={})

    result = machine.step()

    assert result.halted is True
    assert result.halt_reason == "no_rule"
    assert result.step_count == 0
    assert machine.halted is True


def test_missing_rule_error_policy_raises() -> None:
    config = MachineConfiguration(
        name="No Rule Error",
        blank_symbol="_",
        states=("q0",),
        alphabet=("_",),
        start_state="q0",
        accept_states=(),
        reject_states=(),
        initial_tape=("_",),
        initial_head=0,
        missing_rule_policy="error",
    )
    machine = TuringMachine(config=config, tape=Tape.from_symbols(["_"], "_"), rules={})

    try:
        machine.step()
    except RuleNotFoundError:
        pass
    else:
        raise AssertionError("Expected a RuleNotFoundError")


def test_machine_can_start_in_accept_state() -> None:
    config = MachineConfiguration(
        name="Accepted",
        blank_symbol="_",
        states=("halt",),
        alphabet=("_",),
        start_state="halt",
        accept_states=("halt",),
        reject_states=(),
        initial_tape=("_",),
        initial_head=0,
    )
    machine = TuringMachine(config=config, tape=Tape.from_symbols(["_"], "_"), rules={})

    assert machine.halted is True
    assert machine.halt_reason == "accept"
