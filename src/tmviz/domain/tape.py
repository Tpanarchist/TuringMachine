"""Tape model backed by sparse storage."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Tape:
    """Sparse tape with an implicit blank symbol."""

    blank_symbol: str
    cells: dict[int, str] = field(default_factory=dict)

    @classmethod
    def from_symbols(cls, symbols: list[str], blank_symbol: str) -> Tape:
        cells = {index: symbol for index, symbol in enumerate(symbols) if symbol != blank_symbol}
        return cls(blank_symbol=blank_symbol, cells=cells)

    def read(self, position: int) -> str:
        return self.cells.get(position, self.blank_symbol)

    def write(self, position: int, symbol: str) -> None:
        if symbol == self.blank_symbol:
            self.cells.pop(position, None)
            return
        self.cells[position] = symbol

    def snapshot(self, min_index: int, max_index: int) -> list[tuple[int, str]]:
        return [(index, self.read(index)) for index in range(min_index, max_index + 1)]

    def populated_bounds(self) -> tuple[int, int]:
        if not self.cells:
            return (0, 0)
        return (min(self.cells), max(self.cells))

    def clone(self) -> Tape:
        return Tape(blank_symbol=self.blank_symbol, cells=dict(self.cells))

