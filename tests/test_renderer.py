import os
from dataclasses import replace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from tmviz.app.controller import ControllerSnapshot
from tmviz.domain.moves import Direction
from tmviz.domain.rule import Rule
from tmviz.ui.renderer import Renderer


def build_snapshot() -> ControllerSnapshot:
    current_rule = Rule(
        "scan_and_validate_input_stream",
        "very_long_symbol_marker",
        "transition_to_commit_after_extended_validation",
        "1",
        Direction.RIGHT,
    )
    last_rule = Rule(
        "carry_and_rewrite_previous_cells",
        "_",
        "halt_after_commit_when_no_more_rules_exist",
        "_",
        Direction.STAY,
    )
    return ControllerSnapshot(
        app_state="running_commit",
        phase="commit",
        machine_name="Busy Beaver Diagnostic Console With Extended Instrumentation",
        control_state="carry_and_validate_extended_state",
        head_position=14,
        current_symbol="_",
        current_rule=current_rule,
        last_rule=last_rule,
        step_count=512,
        halted=False,
        halt_reason=None,
        error_message=None,
        tape_window=[(index, "1" if index % 2 == 0 else "_") for index in range(8, 21)],
        steps_per_second=5.0,
        grid_enabled=True,
        event_log=[
            "Loaded machine and normalized specification for dense UI rendering.",
            "Read '_' at 14 and selected a long-form rule description for clipping.",
            "Moved head into the commit phase without losing inspector alignment.",
            "Committed step 512 while preserving event rail boundaries.",
            "Prepared another long log line to verify ellipsis behavior in the rail.",
        ],
    )


def test_renderer_smoke_renders_target_sizes() -> None:
    pygame.init()
    try:
        renderer = Renderer()
        snapshot = build_snapshot()
        for size in ((1280, 720), (1024, 640), (1600, 900)):
            surface = pygame.Surface(size)
            renderer.render(surface, snapshot)
            assert surface.get_width() == size[0]
            assert surface.get_height() == size[1]
    finally:
        pygame.quit()


def test_renderer_smoke_renders_error_and_halt_states() -> None:
    pygame.init()
    try:
        renderer = Renderer()
        halted = build_snapshot()
        errored = build_snapshot()
        halted = replace(halted, halted=True, halt_reason="accept")
        errored = replace(errored, app_state="error", error_message="No rule for state='q9'")

        for snapshot in (halted, errored):
            renderer.render(pygame.Surface((1280, 720)), snapshot)
    finally:
        pygame.quit()
