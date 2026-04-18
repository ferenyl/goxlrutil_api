"""Colour helper for GoXLR lighting commands.

Colours are represented as 6-character uppercase hex strings (``RRGGBB``)
in the GoXLR protocol.  The :class:`Colour` dataclass provides a
type-safe way to build them from RGB components or hex strings, and
pre-defines a set of named colours for convenience.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Colour:
    """An RGB colour for GoXLR lighting.

    Examples::

        Colour(255, 0, 0)            # red
        Colour.from_hex("#FF8800")   # orange
        Colour.RED                   # named constant
    """

    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        for name, val in (("r", self.r), ("g", self.g), ("b", self.b)):
            if not 0 <= val <= 255:
                msg = f"Colour.{name} must be 0–255, got {val}"
                raise ValueError(msg)

    def __str__(self) -> str:
        """Return the 6-character uppercase hex string expected by the daemon."""
        return f"{self.r:02X}{self.g:02X}{self.b:02X}"

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_hex(cls, hex_str: str) -> Colour:
        """Create a :class:`Colour` from a hex string (``#RRGGBB`` or ``RRGGBB``)."""
        s = hex_str.lstrip("#")
        if len(s) != 6:
            msg = f"Expected 6-character hex string, got {hex_str!r}"
            raise ValueError(msg)
        return cls(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))

    @classmethod
    def from_int(cls, value: int) -> Colour:
        """Create a :class:`Colour` from a packed 24-bit integer (``0xRRGGBB``)."""
        return cls((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF)

    def dimmed(self, factor: float = 0.3) -> Colour:
        """Return a dimmed version of this colour (``factor`` in 0–1)."""
        f = max(0.0, min(1.0, factor))
        return Colour(int(self.r * f), int(self.g * f), int(self.b * f))

    # ------------------------------------------------------------------
    # Named colours (class-level constants set after class definition)
    # ------------------------------------------------------------------

    BLACK: ClassVar[Colour]
    WHITE: ClassVar[Colour]
    RED: ClassVar[Colour]
    GREEN: ClassVar[Colour]
    BLUE: ClassVar[Colour]
    YELLOW: ClassVar[Colour]
    CYAN: ClassVar[Colour]
    MAGENTA: ClassVar[Colour]
    ORANGE: ClassVar[Colour]
    PURPLE: ClassVar[Colour]
    PINK: ClassVar[Colour]


# Assign class-level named constants after class definition.
Colour.BLACK = Colour(0, 0, 0)
Colour.WHITE = Colour(255, 255, 255)
Colour.RED = Colour(255, 0, 0)
Colour.GREEN = Colour(0, 255, 0)
Colour.BLUE = Colour(0, 0, 255)
Colour.YELLOW = Colour(255, 255, 0)
Colour.CYAN = Colour(0, 255, 255)
Colour.MAGENTA = Colour(255, 0, 255)
Colour.ORANGE = Colour(255, 128, 0)
Colour.PURPLE = Colour(128, 0, 255)
Colour.PINK = Colour(255, 105, 180)


ColourLike = Colour | str
"""A colour value accepted by GoXLR commands.

Either a :class:`Colour` instance or a 6-character hex string (``RRGGBB``
or ``#RRGGBB``).
"""


def _as_hex(c: ColourLike) -> str:
    """Normalise a :data:`ColourLike` to a 6-char uppercase hex string."""
    if isinstance(c, Colour):
        return str(c)
    return str(Colour.from_hex(c))
