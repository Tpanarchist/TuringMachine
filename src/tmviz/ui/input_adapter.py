"""Maps pygame events to application commands."""

from __future__ import annotations

from pathlib import Path

import pygame

from tmviz.app.commands import (
    CenterHeadCommand,
    Command,
    LoadMachineCommand,
    QuitCommand,
    ResetCommand,
    RunCommand,
    SetSpeedCommand,
    StepCommand,
    ToggleGridCommand,
)


class InputAdapter:
    """Translate keyboard input into application commands."""

    def __init__(self, available_specs: list[Path]) -> None:
        self.available_specs = available_specs

    def translate(self, event: pygame.event.Event, current_spec: Path | None) -> list[Command]:
        if event.type == pygame.QUIT:
            return [QuitCommand()]
        if event.type != pygame.KEYDOWN:
            return []

        if event.key == pygame.K_ESCAPE:
            return [QuitCommand()]
        if event.key == pygame.K_SPACE:
            return [RunCommand()]
        if event.key == pygame.K_n:
            return [StepCommand()]
        if event.key == pygame.K_r:
            return [ResetCommand()]
        if event.key == pygame.K_g:
            return [ToggleGridCommand()]
        if event.key == pygame.K_c:
            return [CenterHeadCommand()]
        if event.key == pygame.K_1:
            return [SetSpeedCommand(1.0)]
        if event.key == pygame.K_2:
            return [SetSpeedCommand(2.0)]
        if event.key == pygame.K_3:
            return [SetSpeedCommand(5.0)]
        if event.key == pygame.K_l:
            next_spec = self._cycle_spec(current_spec)
            if next_spec is not None:
                return [LoadMachineCommand(next_spec)]
        return []

    def _cycle_spec(self, current_spec: Path | None) -> Path | None:
        if not self.available_specs:
            return None
        if current_spec is None:
            return self.available_specs[0]
        try:
            current_index = self.available_specs.index(current_spec)
        except ValueError:
            return self.available_specs[0]
        return self.available_specs[(current_index + 1) % len(self.available_specs)]

