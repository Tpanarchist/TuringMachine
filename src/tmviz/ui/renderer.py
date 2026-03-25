"""Pygame renderer for the simulator."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from tmviz.app.controller import ControllerSnapshot

from . import theme
from .layout import SceneMetrics, build_scene_layout, is_compact_size


@dataclass(frozen=True, slots=True)
class FontPack:
    title: pygame.font.Font
    body: pygame.font.Font
    small: pygame.font.Font


class Renderer:
    """Draws the main simulator view."""

    def __init__(self) -> None:
        self._font_cache: dict[bool, FontPack] = {}
        self._background_cache: dict[tuple[int, int], pygame.Surface] = {}

    def render(self, surface: pygame.Surface, snapshot: ControllerSnapshot) -> None:
        size = surface.get_size()
        compact = is_compact_size(size)
        fonts = self._get_fonts(compact)
        metrics = self._measure_metrics(size, fonts, compact)
        layout = build_scene_layout(surface.get_rect(), metrics)

        surface.blit(self._get_background(size), (0, 0))
        self._draw_hud(surface, layout.hud, fonts, snapshot, layout.hint_text)
        self._draw_tape(surface, layout.tape, fonts, metrics, snapshot)
        self._draw_inspector(surface, layout, fonts, snapshot)
        self._draw_log(surface, layout, fonts, snapshot)

    def _draw_hud(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        fonts: FontPack,
        snapshot: ControllerSnapshot,
        hint_text: str,
    ) -> None:
        self._draw_separator(surface, rect.bottom, rect.left, rect.right, theme.SURFACE_EDGE)
        clip_before = surface.get_clip()
        surface.set_clip(rect)

        meta_items = [
            ("APP", snapshot.app_state.upper()),
            ("PHASE", (snapshot.phase or "IDLE").upper()),
            ("SPD", f"{snapshot.steps_per_second:.1f}/S"),
        ]
        meta_right = rect.right
        cursor_x = meta_right
        for label, value in reversed(meta_items):
            text = f"{label} {value}"
            rendered = fonts.small.render(
                text,
                True,
                theme.CYAN if label == "PHASE" else theme.MUTED_TEXT,
            )
            chip = rendered.get_rect()
            chip.width += 18
            chip.height += 10
            chip.top = rect.y + 4
            chip.right = cursor_x
            fill = theme.CYAN_SOFT if label == "PHASE" else None
            if fill is not None:
                self._fill_rect(surface, chip, (*fill, 160), border_radius=12)
                pygame.draw.rect(surface, theme.CYAN, chip, width=1, border_radius=12)
            surface.blit(rendered, rendered.get_rect(center=chip.center))
            cursor_x = chip.left - 10

        title_width = max(cursor_x - rect.x - 24, 60)
        machine_name = self._ellipsize(fonts.title, snapshot.machine_name.upper(), title_width)
        self._blit_text(
            surface,
            fonts.title,
            machine_name,
            theme.TEXT,
            (rect.x, rect.y + 2),
        )

        self._blit_text(
            surface,
            fonts.small,
            hint_text,
            theme.MUTED_TEXT,
            (rect.x, rect.bottom - fonts.small.get_linesize() - 2),
        )
        surface.set_clip(clip_before)

    def _draw_tape(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        fonts: FontPack,
        metrics: SceneMetrics,
        snapshot: ControllerSnapshot,
    ) -> None:
        clip_before = surface.get_clip()
        surface.set_clip(rect)

        self._blit_text(surface, fonts.small, "TAPE FIELD", theme.MUTED_TEXT, (rect.x, rect.y))
        band_top = rect.y + fonts.small.get_linesize() + 28
        band_bottom = rect.bottom - 46
        band_height = max(band_bottom - band_top, metrics.cell_height + 24)
        band_rect = pygame.Rect(rect.x, band_top, rect.width, band_height)
        self._draw_separator(
            surface,
            band_rect.centery,
            band_rect.left,
            band_rect.right,
            theme.GRID,
        )
        self._draw_separator(
            surface,
            band_rect.top + 20,
            band_rect.left,
            band_rect.right,
            theme.TRACK,
        )
        self._draw_separator(
            surface,
            band_rect.bottom - 20,
            band_rect.left,
            band_rect.right,
            theme.TRACK,
        )

        cells = snapshot.tape_window
        cell_count = max(len(cells), 1)
        available_width = band_rect.width - 32
        cell_width = max(36, min(metrics.cell_width + 18, available_width // cell_count))
        cell_height = max(54, min(metrics.cell_height + 10, band_rect.height - 70))
        start_x = band_rect.x + ((band_rect.width - (cell_width * cell_count)) // 2)
        cell_top = band_rect.centery - (cell_height // 2)

        for offset, (index, symbol) in enumerate(cells):
            cell_rect = pygame.Rect(
                start_x + (offset * cell_width),
                cell_top,
                cell_width - 4,
                cell_height,
            )
            is_head = index == snapshot.head_position
            if is_head:
                pulse = (math.sin(pygame.time.get_ticks() / 260) + 1.0) / 2.0
                glow_alpha = 44 if snapshot.app_state.startswith("running") else 70
                glow_alpha = int(glow_alpha + (pulse * 36))
                glow_rect = cell_rect.inflate(20, 16)
                self._fill_rect(
                    surface,
                    glow_rect,
                    (*theme.ACTIVE_GLOW[:3], glow_alpha),
                    border_radius=18,
                )
                self._fill_rect(surface, cell_rect, (*theme.HEAD_FILL, 220), border_radius=10)
                pygame.draw.rect(surface, theme.HEAD_OUTLINE, cell_rect, width=2, border_radius=10)
            else:
                self._fill_rect(surface, cell_rect, (*theme.TRACK, 160), border_radius=10)
                if snapshot.grid_enabled:
                    pygame.draw.rect(surface, theme.GRID, cell_rect, width=1, border_radius=10)

            symbol_surface = fonts.body.render(symbol, True, theme.CYAN if is_head else theme.TEXT)
            symbol_rect = symbol_surface.get_rect(center=cell_rect.center)
            surface.blit(symbol_surface, symbol_rect)

            index_text = f"{index:+d}" if index != 0 else "0"
            index_surface = fonts.small.render(index_text, True, theme.DIM_TEXT)
            surface.blit(
                index_surface,
                index_surface.get_rect(center=(cell_rect.centerx, cell_rect.bottom + 14)),
            )
            if is_head:
                self._blit_text(
                    surface,
                    fonts.small,
                    "HEAD",
                    theme.CYAN,
                    (cell_rect.centerx - (fonts.small.size("HEAD")[0] // 2), cell_rect.y - 24),
                )

        surface.set_clip(clip_before)

    def _draw_inspector(
        self,
        surface: pygame.Surface,
        layout,
        fonts: FontPack,
        snapshot: ControllerSnapshot,
    ) -> None:
        self._fill_rect(surface, layout.inspector, theme.SURFACE_TINT, border_radius=18)
        pygame.draw.rect(surface, theme.SURFACE_EDGE, layout.inspector, width=1, border_radius=18)
        self._draw_separator(
            surface,
            layout.inspector.y + 1,
            layout.inspector.x + 10,
            layout.inspector.right - 10,
            theme.GRID,
        )

        metrics_items = [
            ("APP", snapshot.app_state.upper()),
            ("PHASE", (snapshot.phase or "IDLE").upper()),
            ("SPD", f"{snapshot.steps_per_second:.1f}/S"),
            ("CTRL", snapshot.control_state),
            ("HEAD", str(snapshot.head_position)),
            ("READ", snapshot.current_symbol),
            ("STEPS", str(snapshot.step_count)),
            ("GRID", "ON" if snapshot.grid_enabled else "OFF"),
        ]
        self._draw_metric_grid(surface, layout.inspector_metrics, fonts, metrics_items)

        current_rule = (
            snapshot.current_rule.describe() if snapshot.current_rule else "No active rule."
        )
        last_rule = snapshot.last_rule.describe() if snapshot.last_rule else "No prior rule."
        self._draw_text_block(
            surface,
            layout.inspector_current_rule,
            fonts,
            "CURRENT RULE",
            current_rule,
            layout.rule_line_limit,
            theme.CYAN,
        )
        self._draw_text_block(
            surface,
            layout.inspector_last_rule,
            fonts,
            "LAST RULE",
            last_rule,
            layout.rule_line_limit,
            theme.TEXT,
        )
        self._draw_status_block(surface, layout.inspector_status, fonts, snapshot)

    def _draw_log(
        self,
        surface: pygame.Surface,
        layout,
        fonts: FontPack,
        snapshot: ControllerSnapshot,
    ) -> None:
        self._fill_rect(surface, layout.log, theme.SURFACE_TINT, border_radius=14)
        pygame.draw.rect(surface, theme.SURFACE_EDGE, layout.log, width=1, border_radius=14)
        clip_before = surface.get_clip()
        surface.set_clip(layout.log_content)

        self._blit_text(
            surface,
            fonts.small,
            "EVENT RAIL",
            theme.MUTED_TEXT,
            layout.log_content.topleft,
        )
        row_y = layout.log_content.y + fonts.small.get_linesize() + 10
        row_gap = max(4, fonts.small.get_linesize() // 3)
        entries = snapshot.event_log[-layout.visible_log_rows :]
        for entry in entries:
            line = self._ellipsize(fonts.small, entry, layout.log_content.width)
            self._blit_text(surface, fonts.small, line, theme.TEXT, (layout.log_content.x, row_y))
            row_y += fonts.small.get_linesize() + row_gap

        surface.set_clip(clip_before)

    def _draw_metric_grid(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        fonts: FontPack,
        items: list[tuple[str, str]],
    ) -> None:
        clip_before = surface.get_clip()
        surface.set_clip(rect)
        self._blit_text(surface, fonts.small, "STATE VECTOR", theme.MUTED_TEXT, rect.topleft)

        grid_top = rect.y + fonts.small.get_linesize() + 8
        gap = 10
        cols = 2
        rows = 4
        col_width = (rect.width - gap) // cols
        row_height = max((rect.bottom - grid_top) // rows, fonts.body.get_linesize() + 4)

        for index, (label, value) in enumerate(items):
            row = index // cols
            col = index % cols
            cell = pygame.Rect(
                rect.x + (col * (col_width + gap)),
                grid_top + (row * row_height),
                col_width,
                row_height - 4,
            )
            self._draw_separator(surface, cell.bottom, cell.left, cell.right, theme.TRACK)
            self._blit_text(surface, fonts.small, label, theme.MUTED_TEXT, (cell.x, cell.y + 2))
            value_text = self._ellipsize(fonts.body, value, max(cell.width - 72, 24))
            value_surface = fonts.body.render(value_text, True, theme.TEXT)
            value_rect = value_surface.get_rect(
                midright=(cell.right, cell.y + (fonts.body.get_linesize() // 2) + 2)
            )
            surface.blit(value_surface, value_rect)

        surface.set_clip(clip_before)

    def _draw_text_block(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        fonts: FontPack,
        label: str,
        value: str,
        max_lines: int,
        accent: tuple[int, int, int],
    ) -> None:
        self._draw_separator(surface, rect.top - 4, rect.left, rect.right, theme.TRACK)
        clip_before = surface.get_clip()
        surface.set_clip(rect)

        self._blit_text(surface, fonts.small, label, accent, rect.topleft)
        lines = self._wrap_text(
            fonts.body,
            value.upper(),
            rect.width,
            max_lines=max_lines,
        )
        y = rect.y + fonts.small.get_linesize() + 6
        for line in lines:
            self._blit_text(surface, fonts.body, line, theme.TEXT, (rect.x, y))
            y += fonts.body.get_linesize()

        surface.set_clip(clip_before)

    def _draw_status_block(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        fonts: FontPack,
        snapshot: ControllerSnapshot,
    ) -> None:
        if snapshot.error_message:
            value = snapshot.error_message
            color = theme.RED
        elif snapshot.halted:
            value = f"HALTED // {snapshot.halt_reason or 'STOP'}"
            color = theme.AMBER
        elif snapshot.app_state.startswith("running"):
            value = "RUNNING // CLOCK ADVANCING"
            color = theme.CYAN
        else:
            value = "READY // AWAITING INPUT"
            color = theme.TEXT

        self._draw_separator(surface, rect.top - 4, rect.left, rect.right, theme.TRACK)
        clip_before = surface.get_clip()
        surface.set_clip(rect)
        self._blit_text(surface, fonts.small, "STATUS", theme.MUTED_TEXT, rect.topleft)
        lines = self._wrap_text(fonts.body, value.upper(), rect.width, max_lines=2)
        y = rect.y + fonts.small.get_linesize() + 6
        for line in lines:
            self._blit_text(surface, fonts.body, line, color, (rect.x, y))
            y += fonts.body.get_linesize()
        surface.set_clip(clip_before)

    def _get_fonts(self, compact: bool) -> FontPack:
        cached = self._font_cache.get(compact)
        if cached is not None:
            return cached

        title_size = 26 if compact else 30
        body_size = 18 if compact else 20
        small_size = 15 if compact else 16
        fonts = FontPack(
            title=pygame.font.SysFont(theme.FONT_STACK, title_size, bold=True),
            body=pygame.font.SysFont(theme.FONT_STACK, body_size),
            small=pygame.font.SysFont(theme.FONT_STACK, small_size),
        )
        self._font_cache[compact] = fonts
        return fonts

    def _measure_metrics(
        self,
        size: tuple[int, int],
        fonts: FontPack,
        compact: bool,
    ) -> SceneMetrics:
        return SceneMetrics(
            compact=compact,
            padding=18 if compact else 24,
            section_gap=10 if compact else 16,
            title_line_height=fonts.title.get_linesize(),
            body_line_height=fonts.body.get_linesize(),
            small_line_height=fonts.small.get_linesize(),
            cell_width=48 if compact else 58,
            cell_height=76 if compact else 92,
            inspector_width=min(max(int(size[0] * (0.33 if compact else 0.29)), 286), 390),
            desired_log_rows=5 if size[1] >= 820 else (3 if compact else 4),
            desired_rule_lines=2 if compact else 3,
        )

    def _get_background(self, size: tuple[int, int]) -> pygame.Surface:
        cached = self._background_cache.get(size)
        if cached is not None:
            return cached

        background = pygame.Surface(size)
        background.fill(theme.BACKGROUND)
        overlay = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.circle(
            overlay,
            (*theme.BACKGROUND_GLOW, 70),
            (int(size[0] * 0.22), int(size[1] * 0.35)),
            int(min(size) * 0.52),
        )
        pygame.draw.circle(
            overlay,
            (*theme.BACKGROUND_GLOW, 35),
            (int(size[0] * 0.72), int(size[1] * 0.55)),
            int(min(size) * 0.42),
        )
        for y in range(0, size[1], 4):
            pygame.draw.line(overlay, theme.SCANLINE, (0, y), (size[0], y))
        for x in range(0, size[0], 96):
            pygame.draw.line(overlay, theme.NOISE, (x, 0), (x, size[1]))
        background.blit(overlay, (0, 0))
        self._background_cache[size] = background
        return background

    def _fill_rect(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: tuple[int, int, int] | tuple[int, int, int, int],
        border_radius: int = 0,
    ) -> None:
        if len(color) == 3:
            pygame.draw.rect(surface, color, rect, border_radius=border_radius)
            return
        overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(overlay, color, overlay.get_rect(), border_radius=border_radius)
        surface.blit(overlay, rect.topleft)

    def _draw_separator(
        self,
        surface: pygame.Surface,
        y: int,
        x_start: int,
        x_end: int,
        color: tuple[int, int, int],
    ) -> None:
        pygame.draw.line(surface, color, (x_start, y), (x_end, y))

    def _blit_text(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        text: str,
        color: tuple[int, int, int],
        position: tuple[int, int],
    ) -> None:
        surface.blit(font.render(text, True, color), position)

    def _ellipsize(self, font: pygame.font.Font, text: str, max_width: int) -> str:
        if max_width <= 0:
            return ""
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        trimmed = text
        while trimmed and font.size(f"{trimmed}{ellipsis}")[0] > max_width:
            trimmed = trimmed[:-1]
        return f"{trimmed}{ellipsis}" if trimmed else ellipsis

    def _wrap_text(
        self,
        font: pygame.font.Font,
        text: str,
        max_width: int,
        max_lines: int,
    ) -> list[str]:
        text = " ".join(text.split())
        if not text or max_lines <= 0:
            return []
        words = text.split(" ")
        lines: list[str] = []
        current = words.pop(0)
        while words:
            candidate = f"{current} {words[0]}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
                words.pop(0)
                continue
            lines.append(self._ellipsize(font, current, max_width))
            current = words.pop(0)
            if len(lines) == max_lines - 1:
                remainder = " ".join([current, *words])
                lines.append(self._ellipsize(font, remainder, max_width))
                return lines
        lines.append(self._ellipsize(font, current, max_width))
        return lines[:max_lines]
