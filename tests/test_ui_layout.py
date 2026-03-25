import pygame

from tmviz.ui.layout import SceneMetrics, build_scene_layout


def make_metrics(compact: bool) -> SceneMetrics:
    return SceneMetrics(
        compact=compact,
        padding=18 if compact else 24,
        section_gap=10 if compact else 16,
        title_line_height=32 if compact else 36,
        body_line_height=22 if compact else 24,
        small_line_height=18 if compact else 20,
        cell_width=48 if compact else 58,
        cell_height=76 if compact else 92,
        inspector_width=320,
        desired_log_rows=3 if compact else 4,
        desired_rule_lines=2 if compact else 3,
    )


def assert_no_overlap(a: pygame.Rect, b: pygame.Rect) -> None:
    assert not a.colliderect(b)


def test_scene_layout_regions_do_not_overlap_at_target_sizes() -> None:
    for size in ((1280, 720), (1024, 640), (1600, 900)):
        compact = size[0] < 1180 or size[1] < 680
        layout = build_scene_layout(pygame.Rect((0, 0), size), make_metrics(compact))

        assert layout.hud.width > 0
        assert layout.tape.width > 0
        assert layout.inspector.width > 0
        assert layout.log.width > 0
        assert layout.visible_log_rows >= 2
        assert layout.rule_line_limit >= 1

        assert_no_overlap(layout.hud, layout.tape)
        assert_no_overlap(layout.hud, layout.inspector)
        assert_no_overlap(layout.log, layout.tape)
        assert_no_overlap(layout.log, layout.inspector)
        assert_no_overlap(layout.tape, layout.inspector)


def test_scene_layout_subregions_stay_within_inspector() -> None:
    layout = build_scene_layout(pygame.Rect(0, 0, 1024, 640), make_metrics(compact=True))

    assert layout.inspector.contains(layout.inspector_metrics)
    assert layout.inspector.contains(layout.inspector_current_rule)
    assert layout.inspector.contains(layout.inspector_last_rule)
    assert layout.inspector.contains(layout.inspector_status)
    assert layout.inspector_metrics.bottom <= layout.inspector_current_rule.top
    assert layout.inspector_current_rule.bottom <= layout.inspector_last_rule.top
    assert layout.inspector_last_rule.bottom <= layout.inspector_status.top

