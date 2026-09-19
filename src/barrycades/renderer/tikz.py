from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import ClassVar, get_args, get_origin

from ..barrycade import Barrycade
from ..corral import Corral
from ..exceptions import RenderError
from ..stack import Stack
from .palette import PALETTE, Palette


@dataclass(frozen=True)
class Brick:
    """One rectangle of a stack, `width` wide, on row `y` at `x`."""

    x: float
    y: int
    width: int

    @property
    def corners(self) -> tuple[float, int, float, int]:
        return self.x, self.y, self.x + self.width, self.y + 1

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.width / 2, self.y + 0.5


class TikzRenderer[F: Stack](ABC):
    """Draws a stack as a TikZ picture, one brick at a time."""

    block_style: ClassVar[str]
    grid_style: ClassVar[str]
    palette: ClassVar[Palette] = PALETTE

    def __init__(self, stack: F) -> None:
        self.stack = stack

    @classmethod
    def renderers(cls) -> dict[type[Stack], type["TikzRenderer"]]:
        """Every renderer there is, keyed by the stack it draws.

        A renderer claims a stack by subscripting `TikzRenderer` with it.
        """
        found: dict[type[Stack], type[TikzRenderer]] = {}
        pending = TikzRenderer.__subclasses__()
        while pending:
            renderer = pending.pop()
            pending += renderer.__subclasses__()
            for base in getattr(renderer, "__orig_bases__", ()):
                if get_origin(base) is TikzRenderer:
                    found[get_args(base)[0]] = renderer
        return found

    @classmethod
    def for_stack(cls, stack: Stack) -> "TikzRenderer":
        """The renderer that draws `stack`, ready to render it."""
        renderers = cls.renderers()
        renderer = renderers.get(type(stack))
        if renderer is None:
            raise RenderError(
                f"no TikZ renderer for `{type(stack).__name__}`, expected one "
                f"of {sorted(klass.__name__ for klass in renderers)}"
            )
        return renderer(stack)

    def render(self) -> str:
        """The body of a TikZ picture drawing this stack."""
        return "\n".join(self.draw())

    def draw(self) -> Iterator[str]:
        yield "\\begin{scope}"
        yield from self.draw_grid()
        for y in range(self.stack.height):
            yield from self.draw_labels(y)
        yield from self.draw_bricks()
        yield "\\end{scope}"

    def draw_grid(self) -> Iterator[str]:
        top = self.stack.height + 0.25
        for x in self.grid_positions():
            yield f"\\draw[{self.grid_style}] ({x},{top}) -- ({x},-0.25);"
            yield (
                f"\\node[align=center, anchor=north] at ({x},-0.25) "
                f"{{${self.grid_label(x)}$}};"
            )

    def draw_labels(self, y: int) -> Iterator[str]:
        """The names of row `y`, drawn outside the stack itself."""
        yield (
            f"\\node[align=center, anchor=east] at (-0.25, {y + 0.5}) "
            f"{{$\\varrho_{{{y + 1}}}:$}};"
        )

    def draw_bricks(self) -> Iterator[str]:
        for y, perm in enumerate(self.stack.permutations):
            for brick in self.row_bricks(y, perm):
                yield from self.draw_brick(brick)

    def draw_brick(self, brick: Brick) -> Iterator[str]:
        """Draw one brick, labelled above and below the translucent fill."""
        color = self.palette[brick.width].name
        x1, y1, x2, y2 = brick.corners
        cx, cy = brick.center
        yield f"\\node[align=center, fill=white] at ({cx}, {cy}) {{${brick.width}$}};"
        yield (
            f"\\draw[{self.block_style.format(color=color)}] "
            f"({x1}, {y1}) rectangle ({x2}, {y2});"
        )
        yield f"\\node[align=center] at ({cx}, {cy}) {{${brick.width}$}};"

    @abstractmethod
    def grid_positions(self) -> range:
        """Where the dotted vertical rules go."""

    @abstractmethod
    def grid_label(self, x: int) -> int:
        """The number written under the rule at `x`."""

    @abstractmethod
    def row_bricks(self, y: int, perm: tuple[int, ...]) -> Iterator[Brick]:
        """Every rectangle needed to draw row `y`, in drawing order."""


class CorralRenderer(TikzRenderer[Corral]):
    block_style: ClassVar[str] = "fill={color}, fill opacity=0.5, draw=black, thick"
    grid_style: ClassVar[str] = "dotted, draw=black"

    def grid_positions(self) -> range:
        return range(self.stack.width + 1)

    def grid_label(self, x: int) -> int:
        return x % self.stack.width

    def draw_labels(self, y: int) -> Iterator[str]:
        yield from super().draw_labels(y)
        yield (
            f"\\node[align=center, anchor=south] at "
            f"({self.stack.shifts[y]},{self.stack.height + 0.25}) "
            f"{{$\\tau_{{{y + 1}}}$}};"
        )

    def draw_bricks(self) -> Iterator[str]:
        """Draw the rows clipped, so the copies past either edge are cut off."""
        stack = self.stack
        yield "\\begin{scope}"
        yield (
            f"\\clip (-0.25,-0.25) rectangle "
            f"({stack.width + 0.25},{stack.height + 1.25});"
        )
        yield from super().draw_bricks()
        yield "\\end{scope}"

    def row_bricks(self, y: int, perm: tuple[int, ...]) -> Iterator[Brick]:
        total = self.stack.width
        x = self.stack.shifts[y] % total
        for elem in perm:
            start = x
            yield Brick(x=start, y=y, width=elem)
            x = (start + elem) % total
            if x < start:
                # The brick ran off the right edge; draw the part that
                # reappears on the left.
                start = x - elem
                yield Brick(x=start, y=y, width=elem)
            if start == 0:
                # A brick starting at the origin also belongs past the right
                # edge, inside the clip.
                yield Brick(x=total, y=y, width=elem)


class BarrycadeRenderer(TikzRenderer[Barrycade]):
    block_style: ClassVar[str] = (
        "fill={color},fill opacity=0.5, draw=black, draw opacity=1, thick"
    )
    grid_style: ClassVar[str] = "dotted, draw=black, draw opacity=0.5"

    def grid_positions(self) -> range:
        return range(1, self.stack.width)

    def grid_label(self, x: int) -> int:
        return x

    def row_bricks(self, y: int, perm: tuple[int, ...]) -> Iterator[Brick]:
        x = 0
        for elem in perm:
            yield Brick(x=x, y=y, width=elem)
            x += elem
