# Turing Machine Visualizer

A desktop Turing machine simulator and visualizer built with Python 3.12,
`transitions`, and `pygame-ce`.

## Quick start

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[dev]
python -m tmviz
```

## Controls

- `Space`: run or pause
- `N`: single step
- `R`: reset machine
- `L`: reload current spec
- `C`: center head
- `G`: toggle tape grid
- `1`, `2`, `3`: speed presets
- `Esc`: quit

