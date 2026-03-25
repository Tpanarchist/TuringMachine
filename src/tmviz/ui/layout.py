"""Layout calculations for the modern terminal scene."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from . import theme


@dataclass(frozen=True, slots=True)
class SceneMetrics:
    compact: bool
    padding: int
    section_gap: int
    title_line_height: int
    body_line_height: int
    small_line_height: int
    cell_width: int
    cell_height: int
    inspector_width: int
    desired_log_rows: int
    desired_rule_lines: int


@dataclass(frozen=True, slots=True)
class SceneLayout:
    compact: bool
    hud: pygame.Rect
    tape: pygame.Rect
    inspector: pygame.Rect
    inspector_metrics: pygame.Rect
    inspector_current_rule: pygame.Rect
    inspector_last_rule: pygame.Rect
    inspector_status: pygame.Rect
    log: pygame.Rect
    log_content: pygame.Rect
    visible_log_rows: int
    rule_line_limit: int
    hint_text: str


def clamp_window_size(size: tuple[int, int]) -> tuple[int, int]:
    return (
        max(size[0], theme.MIN_WINDOW_SIZE[0]),
        max(size[1], theme.MIN_WINDOW_SIZE[1]),
    )


def is_compact_size(size: tuple[int, int]) -> bool:
    return size[0] < theme.COMPACT_BREAKPOINT[0] or size[1] < theme.COMPACT_BREAKPOINT[1]


def build_scene_layout(window_rect: pygame.Rect, metrics: SceneMetrics) -> SceneLayout:
    bounds = pygame.Rect((0, 0), clamp_window_size((window_rect.width, window_rect.height)))
    padding = metrics.padding
    section_gap = metrics.section_gap

    hud_height = (
        padding
        + metrics.title_line_height
        + 8
        + metrics.small_line_height
        + (padding // 2)
    )
    log_rows = metrics.desired_log_rows
    rule_lines = metrics.desired_rule_lines
    min_metric_row_height = metrics.body_line_height + 2

    while True:
        log_height = _log_height(metrics, log_rows)
        hud = pygame.Rect(padding, padding, bounds.width - (padding * 2), hud_height)
        log = pygame.Rect(
            padding,
            bounds.height - padding - log_height,
            bounds.width - (padding * 2),
            log_height,
        )
        main_top = hud.bottom + section_gap
        main_bottom = log.top - section_gap
        main_height = max(main_bottom - main_top, metrics.cell_height + (padding * 2))
        inspector_width = min(metrics.inspector_width, max(250, bounds.width // 3))
        inspector = pygame.Rect(
            bounds.width - padding - inspector_width,
            main_top,
            inspector_width,
            main_height,
        )

        tape = pygame.Rect(
            padding,
            main_top,
            max(inspector.left - section_gap - padding, 280),
            main_height,
        )

        inspector_content = inspector.inflate(-(padding + 4), -(padding + 4))
        status_height = metrics.small_line_height + metrics.body_line_height + 14
        rule_block_height = metrics.small_line_height + (metrics.body_line_height * rule_lines) + 18
        min_metrics_height = metrics.small_line_height + (min_metric_row_height * 4) + 10
        available_metrics_height = (
            inspector_content.height
            - status_height
            - (section_gap * 2)
            - (rule_block_height * 2)
        )
        if available_metrics_height >= min_metrics_height or (log_rows == 2 and rule_lines == 1):
            break
        if log_rows > 2:
            log_rows -= 1
            continue
        if rule_lines > 1:
            rule_lines -= 1
            continue
        break

    inspector_content = inspector.inflate(-(padding + 4), -(padding + 4))
    status_height = metrics.small_line_height + metrics.body_line_height + 14
    rule_block_height = metrics.small_line_height + (metrics.body_line_height * rule_lines) + 18
    status_rect = pygame.Rect(
        inspector_content.x,
        inspector_content.bottom - status_height,
        inspector_content.width,
        status_height,
    )
    last_rule_rect = pygame.Rect(
        inspector_content.x,
        status_rect.top - section_gap - rule_block_height,
        inspector_content.width,
        rule_block_height,
    )
    current_rule_rect = pygame.Rect(
        inspector_content.x,
        last_rule_rect.top - section_gap - rule_block_height,
        inspector_content.width,
        rule_block_height,
    )
    metrics_rect = pygame.Rect(
        inspector_content.x,
        inspector_content.y,
        inspector_content.width,
        max(current_rule_rect.top - section_gap - inspector_content.y, min_metrics_height),
    )
    log_content = pygame.Rect(
        log.x + padding,
        log.y + (padding // 2),
        log.width - (padding * 2),
        log.height - padding,
    )
    hint_text = (
        "SPACE pause/run  N step  R reset  L spec"
        if metrics.compact
        else "SPACE pause/run  N step  R reset  L cycle spec  C center  G grid  1/2/3 speed"
    )

    return SceneLayout(
        compact=metrics.compact,
        hud=hud,
        tape=tape,
        inspector=inspector,
        inspector_metrics=metrics_rect,
        inspector_current_rule=current_rule_rect,
        inspector_last_rule=last_rule_rect,
        inspector_status=status_rect,
        log=log,
        log_content=log_content,
        visible_log_rows=log_rows,
        rule_line_limit=rule_lines,
        hint_text=hint_text,
    )


def _log_height(metrics: SceneMetrics, log_rows: int) -> int:
    row_gap = max(4, metrics.small_line_height // 3)
    return (
        metrics.small_line_height
        + (metrics.small_line_height * log_rows)
        + (row_gap * max(log_rows - 1, 0))
        + (metrics.padding + 18)
    )
