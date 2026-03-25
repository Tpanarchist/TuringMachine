# Contribution and Testing Guide

[Back to README](../README.md) | [User Guide](user-guide.md) | [Spec Reference](spec-reference.md) | [Architecture Guide](architecture.md)

## Prerequisites

- Python `3.12`
- a local virtual environment at `.venv`

The project currently targets:

- `pygame-ce`
- `transitions`
- `pytest`
- `ruff`

## Local Setup

### Windows

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[dev]
```

### Linux / macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .[dev]
```

## Day-To-Day Commands

Run the simulator:

```bash
python -m tmviz
```

Run tests:

```bash
pytest -q
```

Run lint:

```bash
ruff check
```

## Where To Change Things

| Area | Place to start |
| --- | --- |
| Machine semantics | `src/tmviz/domain/` |
| App state machine and commands | `src/tmviz/app/` |
| JSON spec validation and loading | `src/tmviz/factory/` |
| Event bus and logging | `src/tmviz/infra/` |
| Rendering, layout, and input | `src/tmviz/ui/` |
| Example machines | `specs/` |
| Automated coverage | `tests/` |

## Adding A New Bundled Spec

1. Add a JSON file under `specs/`.
2. Follow the schema described in [Spec Reference](spec-reference.md).
3. Keep the machine small enough to understand visually unless complexity is the point.
4. Run `pytest -q` to confirm it loads with the existing spec tests.
5. Update docs if the new machine should be surfaced as a recommended example.

## Testing Expectations

At a minimum, changes should preserve:

- domain correctness
- controller lifecycle behavior
- spec loading and validation
- UI layout and renderer smoke coverage

Useful existing test areas:

- domain engine tests
- controller tests
- spec loading tests
- UI layout tests
- renderer smoke tests

## Documentation Expectations

Documentation is part of the product surface.

If you change any of the following, update the docs in the same change:

- keyboard controls
- bundled machines
- machine-spec schema or validation rules
- architecture or package boundaries
- install, test, or lint commands
- visible UI structure or terminology

## Suggested Contribution Checklist

- code matches the current architecture
- tests pass locally
- lint passes locally
- spec examples are valid
- README and `docs/` still reflect the real behavior
- screenshots are refreshed if the visible UI changed materially

