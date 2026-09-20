from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Color:
    """One named color, ready to be defined in a TikZ preamble."""

    name: str
    hex: str

    @property
    def rgb(self) -> tuple[float, float, float]:
        """The hex triple as the fractions TikZ's `rgb` model expects."""
        r, g, b = (int(self.hex[i : i + 2], 16) / 255 for i in (1, 3, 5))
        return r, g, b

    def definition(self) -> str:
        r, g, b = self.rgb
        return f"\\definecolor{{{self.name}}}{{rgb}}{{{r},{g},{b}}}"


FIRST = 2


class Palette:
    """The colors bricks are filled with, cycling once they run out."""

    def __init__(self, hexes: Sequence[str]) -> None:
        self.colors = tuple(
            Color(f"palettecolor{index + FIRST}", code)
            for index, code in enumerate(hexes)
        )

    def __getitem__(self, width: int) -> Color:
        """The color a brick of `width` is filled with."""
        return self.colors[(width - 1) % len(self.colors)]

    def preamble(self) -> str:
        """Every `\\definecolor` this palette needs, one per line."""
        return "\n".join(color.definition() for color in self.colors)


PALETTE = Palette(
    [
        "#ff0000",
        "#00ff00",
        "#0000ff",
        "#ffff00",
        "#00ffff",
        "#ff00ff",
        "#aa0000",
        "#00aa00",
        "#0000aa",
        "#ffaa00",
        "#aa00ff",
        "#aaaaff",
        "#00ffaa",
        "#ff00aa",
        "#00aaff",
        "#aaff00",
        "#aa00aa",
        "#00aaaa",
        "#aaaa00",
    ]
)
