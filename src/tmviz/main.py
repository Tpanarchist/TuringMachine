"""Application entry point."""

from __future__ import annotations

from pathlib import Path

import pygame

from tmviz.app.commands import PauseCommand, QuitCommand, RunCommand
from tmviz.app.controller import AppController
from tmviz.factory.machine_factory import MachineSpecFactory
from tmviz.infra.event_bus import EventBus
from tmviz.infra.logging_config import configure_logging
from tmviz.ui.input_adapter import InputAdapter
from tmviz.ui.layout import clamp_window_size
from tmviz.ui.renderer import Renderer
from tmviz.ui.theme import WINDOW_SIZE


def main() -> None:
    configure_logging()
    pygame.init()
    pygame.display.set_caption("Turing Machine Visualizer")
    window = pygame.display.set_mode(clamp_window_size(WINDOW_SIZE), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    project_root = Path(__file__).resolve().parents[2]
    spec_paths = sorted((project_root / "specs").glob("*.json"))

    event_bus = EventBus()
    controller = AppController(factory=MachineSpecFactory(), event_bus=event_bus)
    input_adapter = InputAdapter(spec_paths)
    renderer = Renderer()

    controller.boot_complete()
    if spec_paths:
        controller.load_machine(spec_paths[0])

    running = True
    while running:
        delta_seconds = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                resized = clamp_window_size((event.w, event.h))
                window = pygame.display.set_mode(resized, pygame.RESIZABLE)
                continue
            for command in input_adapter.translate(event, controller.current_spec_path):
                if isinstance(command, QuitCommand):
                    running = False
                    break
                if isinstance(command, RunCommand) and controller.state in {"loaded", "paused"}:
                    controller.execute(command)
                    continue
                if isinstance(command, RunCommand) and controller.state.startswith("running"):
                    controller.execute(PauseCommand())
                    continue
                controller.execute(command)
            if not running:
                break

        controller.update(delta_seconds)
        renderer.render(window, controller.snapshot())
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
