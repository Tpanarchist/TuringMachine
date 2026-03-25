from pathlib import Path

import pytest

from tmviz.domain.exceptions import SpecValidationError
from tmviz.factory.machine_factory import MachineSpecFactory


def test_factory_loads_valid_spec() -> None:
    factory = MachineSpecFactory()
    path = Path(__file__).resolve().parents[1] / "specs" / "unary_increment.json"

    machine = factory.from_path(path)

    assert machine.name == "Unary Increment"
    assert machine.current_state == "q0"
    assert len(machine.rules) == 2


def test_factory_rejects_duplicate_rules() -> None:
    factory = MachineSpecFactory()
    invalid_spec = {
        "name": "Bad",
        "blank_symbol": "_",
        "states": ["q0"],
        "start_state": "q0",
        "accept_states": [],
        "reject_states": [],
        "alphabet": ["_"],
        "initial_tape": ["_"],
        "initial_head": 0,
        "rules": [
            ["q0", "_", "q0", "_", "S"],
            ["q0", "_", "q0", "_", "S"],
        ],
    }

    with pytest.raises(SpecValidationError):
        factory.from_mapping(invalid_spec)

