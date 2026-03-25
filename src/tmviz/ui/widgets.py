"""Lightweight reusable drawing helpers."""

from __future__ import annotations

import pygame

from . import theme


def draw_panel(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, theme.PANEL, rect, border_radius=18)
    pygame.draw.rect(surface, theme.GRID, rect, width=1, border_radius=18)

