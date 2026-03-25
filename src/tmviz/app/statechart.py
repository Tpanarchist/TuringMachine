"""Hierarchical app state definitions."""

RUNNING_PHASES = ["fetch", "lookup", "write", "move", "commit"]

APP_STATES = [
    "boot",
    "idle",
    "loaded",
    {"name": "running", "children": RUNNING_PHASES, "initial": "fetch"},
    "paused",
    "halted",
    "error",
]

