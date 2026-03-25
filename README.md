# Turing Machine Visualizer

A desktop Turing machine simulator and visualizer built with Python 3.12,
[`pygame-ce`](https://pyga.me/), and [`transitions`](https://github.com/pytransitions/transitions).
It separates the mathematical Turing machine from the simulator shell, so the
core execution model stays deterministic while the app remains interactive and
teachable.

![Turing Machine Visualizer overview](docs/assets/screenshots/overview.png)

## Why this project

- Run bundled Turing machine demos such as unary increment, binary increment,
  and the 2-state busy beaver.
- Step one transition at a time or run continuously at adjustable speed.
- Watch machine state, active rule, tape head, and event history update live.
- Explore an architecture that keeps domain semantics, controller logic, and UI
  rendering cleanly separated.

## Quick Start

### Windows

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[dev]
python -m tmviz
```

### Linux / macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .[dev]
python -m tmviz
```

The app starts with the first bundled spec, opens a resizable terminal-style
window, and enforces a minimum size of `960x600`.

## Developer Commands

```bash
python -m tmviz
pytest -q
ruff check
```

After an editable install you can also launch the simulator with:

```bash
tmviz
```

## Controls

| Key | Action |
| --- | --- |
| `Space` | Toggle run / pause |
| `N` | Execute one full transition |
| `R` | Reset the loaded machine |
| `L` | Cycle to the next bundled machine spec |
| `C` | Publish and log a center-head event |
| `G` | Toggle tape grid rendering |
| `1` | Set speed to `1.0` steps/sec |
| `2` | Set speed to `2.0` steps/sec |
| `3` | Set speed to `5.0` steps/sec |
| `Esc` | Quit |

## Bundled Machines

| Spec | What it demonstrates |
| --- | --- |
| `specs/unary_increment.json` | A minimal machine that appends one unary mark and halts. |
| `specs/binary_increment.json` | Carry logic, left/right movement, and a more interesting transition table. |
| `specs/busy_beaver_2state.json` | A classic small busy beaver configuration with compact rules and obvious tape growth. |

## What You See On Screen

The UI is intentionally dense but structured around one dominant idea: the tape
is the primary workspace.

- **HUD**: machine name, app state, current phase, speed, and compact key hints
- **Tape field**: the active tape window with the current head highlighted
- **Inspector**: state vector, current rule, last rule, and status block
- **Event rail**: the most recent published simulator events

Additional screenshots:

- ![Running phase view](docs/assets/screenshots/running-phase.png)
- ![Halted state view](docs/assets/screenshots/halted-state.png)

## How The Simulator Works

At runtime the project keeps two layers separate:

1. The **domain engine** holds tape contents, head position, control state, and
   the transition table.
2. The **application shell** handles commands, phases, timing, rendering, and
   event publication.

```mermaid
flowchart LR
    P[pygame-ce window and loop] --> I[InputAdapter]
    I --> C[AppController]
    C --> S[StepService]
    S --> D[TuringMachine domain]
    D --> E[EventBus]
    E --> R[Renderer]
    C --> R
```

One machine transition can be shown as a micro-pipeline:

`fetch -> lookup -> write -> move -> commit`

The controller uses a hierarchical `transitions` state machine to move between
boot, idle, loaded, running sub-phases, paused, halted, and error states.

## Machine Spec At A Glance

Machine definitions live in JSON and are validated before they become runtime
objects.

```json
{
  "name": "Unary Increment",
  "blank_symbol": "_",
  "states": ["q0", "halt"],
  "start_state": "q0",
  "accept_states": ["halt"],
  "reject_states": [],
  "alphabet": ["1", "_"],
  "initial_tape": ["1", "1", "1", "_"],
  "initial_head": 0,
  "rules": [
    ["q0", "1", "q0", "1", "R"],
    ["q0", "_", "halt", "1", "S"]
  ]
}
```

Each rule row follows:

```text
[current_state, read_symbol, next_state, write_symbol, move_direction]
```

Supported directions are `L`, `R`, and `S`. The full schema, defaults, and
validation rules are documented in [docs/spec-reference.md](docs/spec-reference.md).

## Project Layout

```text
src/tmviz/
├── app/       # controller, commands, app events, step orchestration
├── domain/    # tape, rules, movements, machine semantics
├── factory/   # spec normalization, validation, machine construction
├── infra/     # event bus, spec loading, logging
└── ui/        # pygame rendering, layout, input mapping, theme

specs/         # bundled example machines
tests/         # domain, controller, layout, renderer, and spec tests
```

## Documentation Map

- [User Guide](docs/user-guide.md)
- [Machine Spec Reference](docs/spec-reference.md)
- [Architecture Guide](docs/architecture.md)
- [Contribution and Testing Guide](docs/contributing.md)

## Current Status

This repository currently focuses on:

- a correct, tested domain engine
- a `transitions`-driven simulator controller
- a dense terminal-style `pygame-ce` UI
- machine specs loaded from JSON
- pytest and Ruff coverage for the implemented surface

If you want to add new machines, UI refinements, or new simulator behaviors,
start with the docs linked above and then inspect the corresponding package in
`src/tmviz/`.
