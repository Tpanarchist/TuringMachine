"""User intent commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class Command:
    """Marker base class for commands."""


@dataclass(frozen=True, slots=True)
class LoadMachineCommand(Command):
    spec_path: Path


@dataclass(frozen=True, slots=True)
class StepCommand(Command):
    pass


@dataclass(frozen=True, slots=True)
class RunCommand(Command):
    pass


@dataclass(frozen=True, slots=True)
class PauseCommand(Command):
    pass


@dataclass(frozen=True, slots=True)
class ResetCommand(Command):
    pass


@dataclass(frozen=True, slots=True)
class SetSpeedCommand(Command):
    steps_per_second: float


@dataclass(frozen=True, slots=True)
class ToggleGridCommand(Command):
    pass


@dataclass(frozen=True, slots=True)
class CenterHeadCommand(Command):
    pass


@dataclass(frozen=True, slots=True)
class ReloadMachineCommand(Command):
    pass


@dataclass(frozen=True, slots=True)
class QuitCommand(Command):
    pass

