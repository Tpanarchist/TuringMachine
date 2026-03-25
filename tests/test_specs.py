import json
from pathlib import Path

from tmviz.factory.machine_factory import MachineSpecFactory


def test_all_specs_load() -> None:
    factory = MachineSpecFactory()
    spec_dir = Path(__file__).resolve().parents[1] / "specs"

    for spec_path in spec_dir.glob("*.json"):
        machine = factory.from_path(spec_path)
        assert machine.name


def test_all_specs_are_valid_json() -> None:
    spec_dir = Path(__file__).resolve().parents[1] / "specs"

    for spec_path in spec_dir.glob("*.json"):
        with spec_path.open("r", encoding="utf-8") as handle:
            parsed = json.load(handle)
        assert isinstance(parsed, dict)

