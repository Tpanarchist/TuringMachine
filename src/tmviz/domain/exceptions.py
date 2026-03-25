"""Domain-specific exceptions."""


class TmVizError(Exception):
    """Base exception for the application."""


class SpecValidationError(TmVizError):
    """Raised when a machine specification is invalid."""


class InvalidSymbolError(TmVizError):
    """Raised when an unknown symbol is used."""


class InvalidDirectionError(TmVizError):
    """Raised when an invalid move direction is encountered."""


class RuleNotFoundError(TmVizError):
    """Raised when no rule exists for the current configuration."""


class MachineHaltedError(TmVizError):
    """Raised when stepping a halted machine."""

